/** The transport: turns `score.ts` into scheduled Web Audio events and owns
 * the scene-scoped play state.
 *
 * The score is every track of the reference, so this file is mostly a casting
 * table - which synth voice stands in for which member of the band, plus the
 * per-part gain scale and per-bus reverb depths read out of the file's own
 * channel state - and the scheduler that feeds them.
 *
 * Lifecycle: the music belongs to the scenes, not the landing. `begin()` on
 * scene entry starts the loop from the top; Esc pauses it (`pause()`), and
 * pausing suspends the context so `currentTime` freezes, the scheduler
 * stalls on its own, and every note in flight resumes exactly where it
 * stopped (`resume()`). Leaving a scene calls `reset()`: position rewinds,
 * and the synth graph is marked stale so the next `begin()` starts on a
 * fresh graph with no tail of the old scene's notes waiting in it.
 *
 * Scheduling is the usual two-clock arrangement: a coarse `setInterval` that
 * only ever hands work to the audio clock, never plays anything itself. Each
 * tick pushes whole bars into the graph until the schedule runs `AHEAD`
 * seconds past the present, so timer jitter (or a throttled tab) can never
 * reach the notes. Bar times accumulate arithmetically, so the loop cannot
 * drift no matter how long it runs. Bends and CC1 vibrato are scheduled the
 * same way, straight off the score's per-bar streams.
 */

import { Synth, type BusName } from './synth'
import {
  BARS, BASS, BEATS_PER_BAR, BENDS, BPM, CLAP, CRASH, GUITAR_CLEAN_A,
  GUITAR_CLEAN_B, GUITAR_DRIVE_A, GUITAR_DRIVE_B, HARMONY, HAT_CLOSED,
  HAT_MID, HAT_OPEN, hz, KICK, LEAD, MIX, MODS, ORGAN, SNARE, TAMB, TIMBALE,
  TOM_FLOOR, TOM_LOW, TOM_MID,
  type Bend, type Hit, type Mod, type Note,
} from './score'

/** Background level - the scene is the point, the music sits under it. The
 * bus balance below this lands the programme near -12 dBFS, so this is a
 * clean output trim rather than something the compressor has to absorb.
 * The pause veil's dial scales it: effective master is MASTER × volume. */
const MASTER = 0.9

/** What the pause veil's sound row is allowed to touch. */
export interface MusicUi {
  readonly muted: boolean
  readonly volume: number
  toggleMute(): void
  setVolume(volume: number): void
  watch(listener: (muted: boolean, volume: number) => void): void
}
const FADE_OUT = 0.14
const FADE_IN = 0.28
/** How far past the present the schedule is kept, and how often it is topped
 * up. A bar is ~1.26s here, so this is always a bar or two of runway. */
const AHEAD = 1.5
const TICK = 100

const SECONDS_PER_BEAT = 60 / BPM
const BAR_SECONDS = SECONDS_PER_BEAT * BEATS_PER_BAR

/* ----------------------------------------------------------------- mix --- */

/** Each part's static gain scale from the file's CC7 volume and CC11
 * expression, on the GM 40·log10 curve (amplitude ∝ (v/127)² per
 * controller), normalised so the loudest part sits at unity and the measured
 * bus staging in synth.ts keeps its meaning. */
const SCALE: Record<string, number> = (() => {
  const raw: Record<string, number> = {}
  let loudest = 0
  for (const [name, mix] of Object.entries(MIX)) {
    raw[name] = (mix.volume / 127) ** 2 * (mix.expression / 127) ** 2
    loudest = Math.max(loudest, raw[name])
  }
  for (const name of Object.keys(raw)) raw[name] /= loudest
  return raw
})()

/** MIDI velocity times the part scale -> gain. The reference plays between
 * 38 and 127, and this is the only place that range is interpreted. */
function gain(part: string, velocity: number): number {
  return (velocity / 127) ** 1.5 * SCALE[part]
}

/** Which parts sit on which synth bus - used to turn the file's per-track
 * cc91 reverb depths into the per-bus sends the graph actually has. */
const BUS_PARTS: Record<BusName, string[]> = {
  lead: ['LEAD'],
  harmony: ['HARMONY'],
  bass: ['BASS'],
  organ: ['ORGAN'],
  drive: ['GUITAR_DRIVE_A', 'GUITAR_DRIVE_B'],
  clean: ['GUITAR_CLEAN_A', 'GUITAR_CLEAN_B'],
  drums: [
    'KICK', 'SNARE', 'CLAP', 'TOM_LOW', 'HAT_CLOSED', 'TOM_FLOOR', 'HAT_MID',
    'HAT_OPEN', 'TOM_MID', 'CRASH', 'TAMB', 'TIMBALE',
  ],
}

function reverbDepths(): Record<BusName, number> {
  const out = {} as Record<BusName, number>
  for (const [bus, parts] of Object.entries(BUS_PARTS) as [BusName, string[]][]) {
    const sum = parts.reduce((acc, part) => acc + (MIX[part]?.reverb ?? 0), 0)
    out[bus] = sum / parts.length / 127
  }
  return out
}

/* ------------------------------------------------------------- casting --- */

type Pitched = (synth: Synth, at: number, note: Note, seconds: number) => void
type Struck = (synth: Synth, at: number, hit: Hit) => void

/** A part's pitch-automation key: its own name when the score carries a bend
 * or mod stream for it, else nothing - an unused pitch bus never exists. */
const keyOf = (name: string): string | undefined =>
  name in BENDS || name in MODS ? name : undefined

/** Rhythm guitars sit double-tracked: the two parts hard-ish left and right,
 * each with its clean print pushed a little wider than its driven one. The
 * file itself pans every track centre; the seats are this port's stereo
 * reading of a double-tracked band, not the file's. */
function guitar(name: string, drive: boolean, seat: string, pan: number): Pitched {
  const key = keyOf(name)
  return (synth, at, note, seconds) =>
    synth.playGuitar(at, note.hz, seconds, gain(name, note.velocity), drive, seat, pan, key)
}

function voice(
  name: string,
  play: (synth: Synth, at: number, hz: number, seconds: number, level: number, key?: string) => void,
): Pitched {
  const key = keyOf(name)
  return (synth, at, note, seconds) => play(synth, at, note.hz, seconds, gain(name, note.velocity), key)
}

const PITCHED_PARTS: [string, Note[], Pitched][] = [
  ['LEAD', LEAD, voice('LEAD', (s, at, hz, d, v, k) => s.playLead(at, hz, d, v, k))],
  ['HARMONY', HARMONY, voice('HARMONY', (s, at, hz, d, v, k) => s.playHarmony(at, hz, d, v, k))],
  ['BASS', BASS, voice('BASS', (s, at, hz, d, v, k) => s.playBass(at, hz, d, v, k))],
  ['ORGAN', ORGAN, voice('ORGAN', (s, at, hz, d, v, k) => s.playOrgan(at, hz, d, v, k))],
  ['GUITAR_DRIVE_A', GUITAR_DRIVE_A, guitar('GUITAR_DRIVE_A', true, 'driveA', -0.42)],
  ['GUITAR_DRIVE_B', GUITAR_DRIVE_B, guitar('GUITAR_DRIVE_B', true, 'driveB', 0.42)],
  ['GUITAR_CLEAN_A', GUITAR_CLEAN_A, guitar('GUITAR_CLEAN_A', false, 'cleanA', -0.72)],
  ['GUITAR_CLEAN_B', GUITAR_CLEAN_B, guitar('GUITAR_CLEAN_B', false, 'cleanB', 0.72)],
]

/** The kit reads General MIDI percussion numbers, so the note is an
 * articulation rather than a pitch - except on the toms, where treating it as
 * a pitch lands the fills on sensible drum fundamentals (GM 41 floor tom is
 * F2 at 87 Hz, GM 65 timbale is F4). */
const tom = (name: string): Struck => (s, at, h) => s.playTom(at, hz(h.midi), gain(name, h.velocity))
const hat = (name: string, open: boolean): Struck => (s, at, h) => s.playHat(at, gain(name, h.velocity), open)

const STRUCK_PARTS: [string, Hit[], Struck][] = [
  ['KICK', KICK, (s, at, h) => s.playKick(at, gain('KICK', h.velocity))],
  // GM 40 is the electric snare against GM 38's acoustic one.
  ['SNARE', SNARE, (s, at, h) => s.playSnare(at, gain('SNARE', h.velocity), h.midi === 40)],
  ['CLAP', CLAP, (s, at, h) => s.playClap(at, gain('CLAP', h.velocity))],
  ['TOM_LOW', TOM_LOW, tom('TOM_LOW')],
  ['TOM_FLOOR', TOM_FLOOR, tom('TOM_FLOOR')],
  ['TOM_MID', TOM_MID, tom('TOM_MID')],
  ['TIMBALE', TIMBALE, tom('TIMBALE')],
  ['HAT_CLOSED', HAT_CLOSED, hat('HAT_CLOSED', false)],
  ['HAT_MID', HAT_MID, hat('HAT_MID', false)],
  ['HAT_OPEN', HAT_OPEN, hat('HAT_OPEN', true)],
  ['TAMB', TAMB, (s, at, h) => s.playTamb(at, gain('TAMB', h.velocity))],
  ['CRASH', CRASH, (s, at, h) => s.playCrash(at, gain('CRASH', h.velocity))],
]

/* ----------------------------------------------------------- scheduling --- */

/** Split a part into per-bar buckets so a scheduler tick is a lookup, not a
 * scan. Index 0 is bar 1. */
function byBar<T extends { at: number }>(items: T[]): T[][] {
  const bars: T[][] = Array.from({ length: BARS }, () => [])
  for (const item of items) {
    const bar = Math.floor(item.at / BEATS_PER_BAR)
    if (bar >= 0 && bar < BARS) bars[bar].push(item)
  }
  return bars
}

export class Music implements MusicUi {
  muted = false
  /** Half by default - the slider opens at its midpoint. */
  volume = 0.5

  private ctx: AudioContext
  private synth: Synth
  private synthOptions = { secondsPerBeat: SECONDS_PER_BEAT, reverb: reverbDepths() }
  /** The graph holds a dead scene's scheduled tail; rebuild before reuse. */
  private stale = false
  private paused = false
  /** True from `begin()` until `reset()` - the player is inside a scene. */
  private wanted = false
  private listeners = new Set<(muted: boolean, volume: number) => void>()
  private timer = 0
  private suspendTimer = 0
  private armed: (() => void) | null = null

  /** Next bar to schedule (0-based) and the audio-clock time of its downbeat. */
  private bar = 0
  private barTime = 0

  private pitched: [Note[][], Pitched][]
  private struck: [Hit[][], Struck][]
  private bendBars: [string, Bend[][]][]
  private modBars: [string, Mod[][]][]

  constructor() {
    this.ctx = new AudioContext({ latencyHint: 'playback' })
    this.ctx.addEventListener('statechange', () => this.onRunning())
    this.synth = new Synth(this.ctx, this.synthOptions)
    this.pitched = PITCHED_PARTS.map(([, part, play]) => [byBar(part), play])
    this.struck = STRUCK_PARTS.map(([, part, play]) => [byBar(part), play])
    this.bendBars = Object.entries(BENDS).map(([name, events]) => [name, byBar(events)])
    this.modBars = Object.entries(MODS).map(([name, events]) => [name, byBar(events)])
  }

  /* ------------------------------------------------------------- state --- */

  /** True when the graph should be running and audible. Mute rides the same
   * suspend machinery as pause: position freezes, unmute picks it back up. */
  private get live(): boolean {
    return this.wanted && !this.paused && !this.muted
  }

  /** Scene entered: the loop starts over from the top. Always downstream of
   * a door click, so the context's autoplay gate is already satisfied - but
   * the gesture fallback stays for the day it is not. */
  begin(): void {
    if (this.wanted) return
    this.wanted = true
    this.paused = false
    this.bar = 0
    this.barTime = 0
    this.apply()
  }

  /** Esc: hold the loop where it stands. */
  pause(): void {
    if (!this.wanted || this.paused) return
    this.paused = true
    this.apply()
  }

  /** Back into the same scene: pick up exactly where pause left it. */
  resume(): void {
    if (!this.wanted || !this.paused) return
    this.paused = false
    this.apply()
  }

  /** Scene left: silence, rewind, and mark the graph for a fresh start so
   * the old scene's already-scheduled tail can never leak into the next.
   * Mute and volume are the visitor's settings, not transport state, and
   * survive it. */
  reset(): void {
    if (!this.wanted) return
    this.wanted = false
    this.paused = false
    this.bar = 0
    this.barTime = 0
    this.stale = true
    this.apply()
  }

  toggleMute(): void {
    this.muted = !this.muted
    this.apply()
    this.notify()
  }

  setVolume(volume: number): void {
    this.volume = Math.min(1, Math.max(0, volume))
    // Usually turned while the pause veil holds the context suspended, so
    // the new level simply applies on resume; if the graph is live, follow
    // the dial right away.
    if (this.live && this.ctx.state === 'running') this.fade(MASTER * this.volume, 0.05)
    this.notify()
  }

  watch(listener: (muted: boolean, volume: number) => void): void {
    this.listeners.add(listener)
    listener(this.muted, this.volume)
  }

  private notify(): void {
    for (const listener of this.listeners) listener(this.muted, this.volume)
  }

  /** Drive the graph to match `live`. Every transition runs through here, so
   * the states can overlap in any order without fighting. */
  private apply(): void {
    window.clearTimeout(this.suspendTimer)
    this.suspendTimer = 0
    if (!this.live) {
      this.stopScheduler()
      if (this.ctx.state !== 'running') return
      this.fade(0, FADE_OUT)
      this.suspendTimer = window.setTimeout(() => {
        void this.ctx.suspend()
      }, (FADE_OUT + 0.02) * 1000)
      return
    }
    // A blocked context leaves `resume()` pending rather than rejecting, so
    // the state change - not the promise - is what starts the transport.
    void this.ctx.resume().catch(() => undefined)
    if (this.ctx.state === 'running') this.onRunning()
    else this.waitForGesture()
  }

  private onRunning(): void {
    if (this.ctx.state !== 'running' || !this.live) return
    this.armed?.()
    if (this.stale) {
      // The old graph still holds the dead scene's scheduled notes; cut it
      // loose whole and start over. Sources ring out into a disconnected
      // master and are collected.
      this.stale = false
      this.synth.master.disconnect()
      this.synth = new Synth(this.ctx, this.synthOptions)
    }
    // Fresh start: put the top of the loop just past the fade-in.
    if (this.barTime === 0) this.barTime = this.ctx.currentTime + 0.12
    this.fade(MASTER * this.volume, FADE_IN)
    this.startScheduler()
  }

  private fade(to: number, seconds: number): void {
    const gainParam = this.synth.master.gain
    const now = this.ctx.currentTime
    gainParam.cancelScheduledValues(now)
    gainParam.setValueAtTime(gainParam.value, now)
    gainParam.linearRampToValueAtTime(to, now + seconds)
  }

  /** Autoplay was refused; the next interaction with the page releases it. */
  private waitForGesture(): void {
    if (this.armed) return
    const go = (): void => {
      this.armed?.()
      this.apply()
    }
    const off = (): void => {
      this.armed = null
      window.removeEventListener('pointerdown', go, true)
      window.removeEventListener('keydown', go, true)
    }
    this.armed = off
    window.addEventListener('pointerdown', go, true)
    window.addEventListener('keydown', go, true)
  }

  /* --------------------------------------------------------- scheduler --- */

  private startScheduler(): void {
    if (this.timer) return
    this.pump()
    this.timer = window.setInterval(() => this.pump(), TICK)
  }

  private stopScheduler(): void {
    if (!this.timer) return
    window.clearInterval(this.timer)
    this.timer = 0
  }

  private pump(): void {
    const horizon = this.ctx.currentTime + AHEAD
    // A tab that was throttled hard enough to fall behind rejoins at the
    // present rather than replaying bars nobody heard.
    if (this.barTime < this.ctx.currentTime - BAR_SECONDS) this.barTime = this.ctx.currentTime
    while (this.barTime < horizon) {
      this.scheduleBar(this.bar, this.barTime)
      this.barTime += BAR_SECONDS
      this.bar = (this.bar + 1) % BARS
    }
  }

  private scheduleBar(bar: number, at: number): void {
    const base = bar * BEATS_PER_BAR
    const when = (beat: number): number => at + (beat - base) * SECONDS_PER_BEAT
    for (const [bars, play] of this.pitched) {
      for (const note of bars[bar]) {
        play(this.synth, when(note.at), note, note.beats * SECONDS_PER_BEAT)
      }
    }
    for (const [bars, play] of this.struck) {
      for (const beat of bars[bar]) play(this.synth, when(beat.at), beat)
    }
    // Pitch automation rides the same clock as the notes it belongs to; the
    // per-bar anchors in the score make each bar self-contained, so the loop
    // seam and any catch-up rejoin land on correct wheel state.
    for (const [key, bars] of this.bendBars) {
      for (const bend of bars[bar]) this.synth.scheduleBend(key, when(bend.at), bend.cents)
    }
    for (const [key, bars] of this.modBars) {
      for (const mod of bars[bar]) this.synth.scheduleMod(key, when(mod.at), mod.depth)
    }
  }
}
