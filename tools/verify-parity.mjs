#!/usr/bin/env node
/** Proves the shipped soundtrack is the reference MIDI, stream for stream.
 *
 * Run with `npm run verify:score`. Exits non-zero on any mismatch.
 *
 * This is deliberately not the generator's code path. It re-parses
 * `assets/I_will_be_there_for_you.mid` with its own reader, and it checks the
 * *compiled* `src/audio/score.ts` - so the score's own runtime decoder is
 * exercised too, and a bug in `midi-to-score.mjs` cannot hide behind itself.
 *
 * Two layers, because data parity alone is not enough - a part that nothing
 * plays would still be silent:
 *
 *   1. DATA     every note in the reference's loop window appears in the
 *               score with identical onset, pitch, length and velocity
 *               (integer ticks); every pitch-bend and CC1 event appears in
 *               its part's stream with identical tick and value, under the
 *               same anchor rule; MIX carries each track's exact CC7/10/11/91
 *               state at the window start; and the score invents nothing.
 *   2. PLAYBACK the real `Music` scheduler, run against a stubbed Web Audio
 *               API, delivers every one of those events - notes to their
 *               voices with onset, pitch, length, velocity, gain and stereo
 *               seat intact, bends and mods to the synth's pitch buses with
 *               tick and value intact.
 */

import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { tmpdir } from 'node:os'
import * as esbuild from 'esbuild'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const failures = []
const fail = (msg) => failures.push(msg)

/* ------------------------------------------------- 0. read the reference --- */

/** An independent SMF reader: notes, pitch bends and controllers per track. */
function readMidi(path) {
  const b = readFileSync(path)
  let i = 0
  const be = (n) => { let v = 0; for (let k = 0; k < n; k++) v = (v << 8) | b[i++]; return v >>> 0 }
  const str = (n) => { const s = b.toString('ascii', i, i + n); i += n; return s }
  const varlen = () => { let v = 0, c; do { c = b[i++]; v = (v << 7) | (c & 0x7f) } while (c & 0x80); return v }

  if (str(4) !== 'MThd') throw new Error('not a MIDI file')
  const headerLen = be(4)
  const afterHeader = i + headerLen
  be(2) // format
  const ntrks = be(2)
  const division = be(2)
  i = afterHeader

  const tracks = []
  const names = []
  const bends = []
  const controls = []
  for (let t = 0; t < ntrks; t++) {
    if (str(4) !== 'MTrk') throw new Error(`track ${t}: missing MTrk`)
    const size = be(4)
    const stop = i + size
    const events = []
    bends[t] = []
    controls[t] = []
    const sounding = new Map()
    let clock = 0
    let last = 0
    while (i < stop) {
      clock += varlen()
      let status = b[i]
      if (status >= 0x80) { i += 1; last = status } else { status = last }
      const high = status & 0xf0
      if (status === 0xff) {
        const kind = b[i++]
        const len = varlen()
        if (kind === 0x03) names[t] = b.toString('utf8', i, i + len).trim()
        i += len
      } else if (status === 0xf0 || status === 0xf7) {
        i += varlen()
      } else if (high === 0x90 || high === 0x80) {
        const pitch = b[i++]
        const velocity = b[i++]
        if (high === 0x90 && velocity > 0) {
          const queue = sounding.get(pitch) ?? []
          queue.push({ clock, velocity })
          sounding.set(pitch, queue)
        } else {
          const queue = sounding.get(pitch)
          if (queue?.length) {
            const on = queue.shift()
            events.push({ tick: on.clock, midi: pitch, length: Math.max(1, clock - on.clock), velocity: on.velocity })
          }
        }
      } else if (high === 0xe0) {
        const lsb = b[i++]
        const msb = b[i++]
        bends[t].push({ tick: clock, value: lsb | (msb << 7) })
      } else if (high === 0xb0) {
        controls[t].push({ tick: clock, cc: b[i++], value: b[i++] })
      } else if (high === 0xc0 || high === 0xd0) {
        i += 1
      } else {
        i += 2
      }
    }
    i = stop
    tracks.push(events)
  }
  return { division, ntrks, names, tracks, bends, controls }
}

const midi = readMidi(join(ROOT, 'assets/I_will_be_there_for_you.mid'))
const TPB = midi.division
const TPBAR = TPB * 4
const DOWNBEAT = 1080
const FIRST_BAR = 2
const BARS = 38
const WINDOW_START = DOWNBEAT + (FIRST_BAR - 1) * TPBAR
const WINDOW_END = WINDOW_START + BARS * TPBAR

/** The reference's note events for one track, rebased on the loop. */
function reference(track) {
  return midi.tracks[track]
    .filter((e) => e.tick >= WINDOW_START && e.tick < WINDOW_END)
    .map((e) => ({ tick: e.tick - WINDOW_START, midi: e.midi, length: e.length, velocity: e.velocity }))
}

/** Pitch-bend sensitivity: RPN 0 data entry if the track sets it, else GM's
 * 2 semitones. */
function bendRange(track) {
  let rpn = -1
  let semis = 2
  for (const e of midi.controls[track]) {
    if (e.cc === 101) rpn = ((rpn === -1 ? 0 : rpn) & 0x7f) | (e.value << 7)
    else if (e.cc === 100) rpn = ((rpn === -1 ? 0 : rpn) & 0x3f80) | e.value
    else if (e.cc === 6 && rpn === 0) semis = e.value
  }
  return semis
}

/** Expected automation stream for one track under the score's contract:
 * windowed events plus a synthetic bar-top anchor wherever no real event
 * sits, null when the stream is silent throughout. Mirrors the generator's
 * rule, implemented against this file's own parse. */
function expectedStream(events, map, neutral) {
  const sorted = [...events].sort((a, b) => a.tick - b.tick)
  const windowed = sorted
    .filter((e) => e.tick >= WINDOW_START && e.tick < WINDOW_END)
    .map((e) => ({ tick: e.tick - WINDOW_START, value: map(e.value) }))
  const anchors = []
  for (let bar = 0; bar < BARS; bar++) {
    const barTick = bar * TPBAR
    if (windowed.some((e) => e.tick === barTick)) continue
    let value = neutral
    for (const e of sorted) {
      if (e.tick > WINDOW_START + barTick) break
      value = e.value
    }
    anchors.push({ tick: barTick, value: map(value) })
  }
  const all = [...windowed, ...anchors].sort((a, b) => a.tick - b.tick)
  const silent = windowed.length === 0 && all.every((e) => e.value === map(neutral))
  return silent ? null : all
}

/** The state of one controller at the window start. */
function controlAt(track, cc, neutral) {
  let value = neutral
  for (const e of [...midi.controls[track]].sort((a, b) => a.tick - b.tick)) {
    if (e.cc !== cc || e.tick > WINDOW_START) continue
    value = e.value
  }
  return value
}

/* --------------------------------------------------- 1. compile the score --- */

const scratch = mkdtempSync(join(tmpdir(), 'friends-parity-'))
async function compile(entry, name) {
  const out = join(scratch, name)
  const result = await esbuild.build({
    entryPoints: [entry], bundle: true, format: 'esm', write: false, platform: 'neutral',
  })
  writeFileSync(out, result.outputFiles[0].text)
  return import(`file://${out}`)
}
const score = await compile(join(ROOT, 'src/audio/score.ts'), 'score.mjs')

/** Which score export carries which reference track. Declared here rather
 * than imported, so a casting change in the app has to be mirrored here
 * consciously instead of agreeing with itself by construction. */
const MAP = [
  ['LEAD', 1], ['HARMONY', 2], ['BASS', 3], ['ORGAN', 4],
  ['GUITAR_DRIVE_A', 5], ['GUITAR_DRIVE_B', 6], ['GUITAR_CLEAN_A', 7], ['GUITAR_CLEAN_B', 8],
  ['KICK', 9], ['SNARE', 10], ['CLAP', 11], ['TOM_LOW', 12], ['HAT_CLOSED', 13],
  ['TOM_FLOOR', 14], ['HAT_MID', 15], ['HAT_OPEN', 16], ['TOM_MID', 17],
  ['CRASH', 18], ['TAMB', 19], ['TIMBALE', 20],
]

const toTicks = (beats) => {
  const exact = beats * TPB
  const rounded = Math.round(exact)
  if (Math.abs(exact - rounded) > 1e-6) fail(`non-integer tick from beats ${beats}`)
  return rounded
}

/** The score's note events for one part, back in reference ticks. Percussion
 * parts carry no length, so they compare on onset/pitch/velocity only. */
function scored(name) {
  const part = score[name]
  if (!part) { fail(`score has no export ${name}`); return [] }
  return part.map((e) => ({
    tick: toTicks(e.at),
    midi: e.midi,
    length: e.beats === undefined ? undefined : toTicks(e.beats),
    velocity: e.velocity,
  }))
}

const key = (e) => `${e.tick}:${e.midi}:${e.length ?? '-'}:${e.velocity}`

console.log('  LAYER 1 - data parity against the reference\n')
console.log('  part             track  ref  score  onsets  pitches  lengths  velocities')
let refTotal = 0
let scoreTotal = 0
for (const [name, track] of MAP) {
  const ref = reference(track).sort((a, b) => a.tick - b.tick || a.midi - b.midi)
  const got = scored(name).sort((a, b) => a.tick - b.tick || a.midi - b.midi)
  refTotal += ref.length
  scoreTotal += got.length

  // Percussion parts do not carry length; blank the reference's to match.
  const drums = got.length > 0 && got[0].length === undefined
  const refCmp = drums ? ref.map((e) => ({ ...e, length: undefined })) : ref

  const counts = ref.length === got.length
  const onsets = counts && refCmp.every((e, n) => e.tick === got[n].tick)
  const pitches = counts && refCmp.every((e, n) => e.midi === got[n].midi)
  const lengths = counts && refCmp.every((e, n) => e.length === got[n].length)
  const vels = counts && refCmp.every((e, n) => e.velocity === got[n].velocity)
  const ok = (b) => (b ? '  ok  ' : ' FAIL ')

  console.log(
    `  ${name.padEnd(15)}${String(track).padStart(4)}${String(ref.length).padStart(6)}` +
    `${String(got.length).padStart(6)}  ${ok(onsets)}  ${ok(pitches)}  ${ok(lengths)}  ${ok(vels)}`,
  )
  if (!counts) fail(`${name}: ${ref.length} reference events, ${got.length} in score`)
  if (!onsets || !pitches || !lengths || !vels) {
    const a = new Set(refCmp.map(key))
    const b = new Set(got.map(key))
    for (const k of [...a].filter((x) => !b.has(x)).slice(0, 3)) fail(`${name}: missing ${k}`)
    for (const k of [...b].filter((x) => !a.has(x)).slice(0, 3)) fail(`${name}: invented ${k}`)
  }
}

// Nothing in the window may be unaccounted for by any part.
const mapped = new Set(MAP.map(([, t]) => t))
for (let t = 0; t < midi.ntrks; t++) {
  if (mapped.has(t)) continue
  const stray = reference(t)
  if (stray.length) fail(`reference track ${t} (${midi.names[t]}) has ${stray.length} unported events`)
}
if (refTotal !== scoreTotal) fail(`total ${refTotal} reference vs ${scoreTotal} score`)
console.log(`\n  ${refTotal} reference events, ${scoreTotal} in score`)

/* ---- bends and modulation ---- */

console.log('\n  stream           part             ref points  score  match')
let bendTotal = 0
let modTotal = 0
for (const [label, pick, mapOf, neutral, store, count] of [
  ['bend', (t) => midi.bends[t], (t) => { const r = bendRange(t); return (v) => Math.round(((v - 8192) / 8192) * r * 100) }, 8192, score.BENDS, (n) => { bendTotal += n }],
  ['mod', (t) => midi.controls[t].filter((e) => e.cc === 1), () => (v) => v, 0, score.MODS, (n) => { modTotal += n }],
]) {
  for (const [name, track] of MAP) {
    const expected = expectedStream(pick(track), mapOf(track), neutral)
    const entry = store?.[name]
    if (!expected) {
      if (entry) fail(`${name}: score carries a ${label} stream the reference does not`)
      continue
    }
    if (!entry) {
      console.log(`  ${label.padEnd(15)}${name.padEnd(18)}${String(expected.length).padStart(9)}      -   FAIL`)
      fail(`${name}: reference has a ${label} stream (${expected.length} points); score has none`)
      continue
    }
    const got = entry.map((e) => ({ tick: toTicks(e.at), value: label === 'bend' ? e.cents : e.depth }))
    const same = expected.length === got.length &&
      expected.every((e, n) => e.tick === got[n].tick && e.value === got[n].value)
    count(entry.length)
    console.log(
      `  ${label.padEnd(15)}${name.padEnd(18)}${String(expected.length).padStart(9)}` +
      `${String(got.length).padStart(7)}   ${same ? 'ok' : 'FAIL'}`,
    )
    if (!same) {
      for (let n = 0; n < Math.max(expected.length, got.length); n++) {
        const a = expected[n], b = got[n]
        if (!a || !b || a.tick !== b.tick || a.value !== b.value) {
          fail(`${name} ${label}[${n}]: expected ${a?.tick}:${a?.value}, score ${b?.tick}:${b?.value}`)
          break
        }
      }
    }
  }
  const extras = Object.keys(store ?? {}).filter((k) => !MAP.some(([n]) => n === k))
  for (const k of extras) fail(`${label} stream for unknown part ${k}`)
}

/* ---- static mix ---- */

for (const [name, track] of MAP) {
  const expected = {
    volume: controlAt(track, 7, 100),
    pan: controlAt(track, 10, 64),
    expression: controlAt(track, 11, 127),
    reverb: controlAt(track, 91, 0),
  }
  const got = score.MIX?.[name]
  if (!got) { fail(`MIX missing ${name}`); continue }
  for (const field of ['volume', 'pan', 'expression', 'reverb']) {
    if (got[field] !== expected[field]) {
      fail(`MIX.${name}.${field}: reference ${expected[field]}, score ${got[field]}`)
    }
  }
}
console.log(`\n  ${bendTotal} bend points, ${modTotal} mod points, MIX checked for all ${MAP.length} parts\n`)

/* ------------------------------------------------ 2. drive the scheduler --- */

console.log('  LAYER 2 - the scheduler plays every one of them\n')

let clock = 0
const timers = { interval: [], timeout: [] }
globalThis.window = {
  setInterval: (fn, ms) => timers.interval.push({ fn, ms, next: clock * 1000 + ms }),
  clearInterval: () => {},
  setTimeout: (fn, ms) => timers.timeout.push({ fn, at: clock * 1000 + ms }),
  clearTimeout: () => {},
  addEventListener: () => {}, removeEventListener: () => {},
}
const audioParam = () => ({
  value: 0,
  setValueAtTime() { return this }, exponentialRampToValueAtTime() { return this },
  linearRampToValueAtTime() { return this }, cancelScheduledValues() { return this },
})
const audioNode = (extra = {}) => ({ connect: () => audioNode(), disconnect() {}, ...extra })
globalThis.AudioContext = class {
  constructor() { this.state = 'suspended'; this.sampleRate = 48000; this.destination = audioNode(); this.hooks = [] }
  get currentTime() { return clock }
  addEventListener(_, fn) { this.hooks.push(fn) }
  async resume() { this.state = 'running'; this.hooks.forEach((f) => f()) }
  async suspend() { this.state = 'suspended'; this.hooks.forEach((f) => f()) }
  createGain() { return audioNode({ gain: audioParam() }) }
  createBiquadFilter() { return audioNode({ frequency: audioParam(), Q: audioParam(), type: '' }) }
  createOscillator() { return audioNode({ frequency: audioParam(), detune: audioParam(), type: '', start() {}, stop() {} }) }
  createConstantSource() { return audioNode({ offset: audioParam(), start() {}, stop() {} }) }
  createBufferSource() { return audioNode({ buffer: null, loop: false, loopStart: 0, loopEnd: 0, start() {}, stop() {} }) }
  createConvolver() { return audioNode({ buffer: null }) }
  createDelay() { return audioNode({ delayTime: audioParam() }) }
  createStereoPanner() { return audioNode({ pan: audioParam() }) }
  createDynamicsCompressor() {
    return audioNode({ threshold: audioParam(), knee: audioParam(), ratio: audioParam(), attack: audioParam(), release: audioParam() })
  }
  createWaveShaper() { return audioNode({ curve: null, oversample: '' }) }
  createBuffer(_, len) { return { getChannelData: () => new Float32Array(len), length: len } }
}

const entry = join(scratch, 'entry.ts')
writeFileSync(entry,
  `export { Music } from '${ROOT}/src/audio/music'\nexport { Synth } from '${ROOT}/src/audio/synth'\n`)
const app = await compile(entry, 'music.mjs')

const played = []
const automated = []
const VOICES = {
  playLead: (at, hz, dur, vel) => ({ at, hz, dur, vel }),
  playHarmony: (at, hz, dur, vel) => ({ at, hz, dur, vel }),
  playBass: (at, hz, dur, vel) => ({ at, hz, dur, vel }),
  playOrgan: (at, hz, dur, vel) => ({ at, hz, dur, vel }),
  playGuitar: (at, hz, dur, vel, drive, seat) => ({ at, hz, dur, vel, seat }),
  playKick: (at, vel) => ({ at, vel }),
  playSnare: (at, vel, tight) => ({ at, vel, midi: tight ? 40 : 38 }),
  playClap: (at, vel) => ({ at, vel, midi: 39 }),
  playTom: (at, hz, vel) => ({ at, hz, vel }),
  playHat: (at, vel, open) => ({ at, vel, open }),
  playTamb: (at, vel) => ({ at, vel, midi: 54 }),
  playCrash: (at, vel) => ({ at, vel, midi: 49 }),
}
for (const [name, shape] of Object.entries(VOICES)) {
  app.Synth.prototype[name] = function (...args) { played.push({ voice: name, ...shape(...args) }) }
}
app.Synth.prototype.scheduleBend = function (part, at, cents) {
  automated.push({ stream: 'bend', part, at, value: cents })
}
app.Synth.prototype.scheduleMod = function (part, at, depth) {
  automated.push({ stream: 'mod', part, at, value: depth })
}

const music = new app.Music()
music.begin()
const LOOP = BARS * 4 * 60 / score.BPM
const ORIGIN = 0.12
// Advance a little past one loop so the whole cycle is scheduled.
const horizon = ORIGIN + LOOP + 0.5
while (clock < horizon) {
  clock = Math.min(horizon, clock + 0.02)
  const ms = clock * 1000
  for (const t of timers.timeout) if (!t.done && t.at <= ms) { t.done = true; t.fn() }
  for (const t of timers.interval) while (t.next <= ms) { t.next += t.ms; t.fn() }
}

const SPB = 60 / score.BPM
const midiOf = (hz) => Math.round(69 + 12 * Math.log2(hz / 440))
const tickOf = (at) => Math.round((at - ORIGIN) / SPB * TPB)

/** The gain each part's velocity becomes - the same GM 40·log10 volume and
 * expression curve music.ts applies, duplicated consciously so the app
 * cannot agree with itself by construction. */
const SCALE = (() => {
  const raw = {}
  let loudest = 0
  for (const [name, mix] of Object.entries(score.MIX)) {
    raw[name] = (mix.volume / 127) ** 2 * (mix.expression / 127) ** 2
    loudest = Math.max(loudest, raw[name])
  }
  for (const name of Object.keys(raw)) raw[name] /= loudest
  return raw
})()
const gainOf = (part, velocity) => ((velocity / 127) ** 1.5 * SCALE[part]).toFixed(12)

/** Which voice each part is expected to reach, and how the drum voices
 * disambiguate the GM articulations that share one voice. */
const EXPECT = {
  LEAD: 'playLead', HARMONY: 'playHarmony', BASS: 'playBass', ORGAN: 'playOrgan',
  GUITAR_DRIVE_A: 'playGuitar', GUITAR_DRIVE_B: 'playGuitar',
  GUITAR_CLEAN_A: 'playGuitar', GUITAR_CLEAN_B: 'playGuitar',
  KICK: 'playKick', SNARE: 'playSnare', CLAP: 'playClap',
  TOM_LOW: 'playTom', TOM_FLOOR: 'playTom', TOM_MID: 'playTom', TIMBALE: 'playTom',
  HAT_CLOSED: 'playHat', HAT_MID: 'playHat', HAT_OPEN: 'playHat',
  TAMB: 'playTamb', CRASH: 'playCrash',
}

const inLoop = played.filter((p) => p.at >= ORIGIN - 1e-9 && p.at < ORIGIN + LOOP - 1e-9)
const byVoice = {}
for (const p of inLoop) (byVoice[p.voice] ??= []).push(p)

console.log('  voice          calls  expected  from')
let callTotal = 0
for (const voice of Object.keys(VOICES)) {
  const parts = Object.entries(EXPECT).filter(([, v]) => v === voice).map(([p]) => p)
  const expected = parts.reduce((n, p) => n + (score[p]?.length ?? 0), 0)
  const actual = (byVoice[voice] ?? []).length
  callTotal += actual
  console.log(
    `  ${voice.padEnd(13)}${String(actual).padStart(6)}${String(expected).padStart(10)}` +
    `  ${parts.join(', ')}${actual === expected ? '' : '   <-- MISMATCH'}`,
  )
  if (actual !== expected) fail(`${voice}: scheduler made ${actual} calls, score holds ${expected} events`)
}
if (callTotal !== scoreTotal) fail(`scheduler played ${callTotal} of ${scoreTotal} score events`)

// Onset, pitch, length, gain and seat must survive the whole chain, not just
// the counts. The four guitar tracks share a voice and mostly share their
// onsets and pitches, so their stereo seat goes into the key - otherwise
// playing one of them twice would look the same as playing each once.
const SEATS = {
  GUITAR_DRIVE_A: 'driveA', GUITAR_DRIVE_B: 'driveB',
  GUITAR_CLEAN_A: 'cleanA', GUITAR_CLEAN_B: 'cleanB',
}
// GM 42 (closed) and GM 44 (pedal) both reach playHat as "closed", so the two
// would be indistinguishable downstream. Track 13 is empty in this section,
// which is what keeps that from mattering - assert it rather than assume it.
if ((score.HAT_CLOSED ?? []).length !== 0) {
  fail('HAT_CLOSED (GM 42) now has notes; playHat cannot distinguish it from HAT_MID (GM 44)')
}

const wanted = new Map()
for (const [name] of MAP) {
  for (const e of score[name] ?? []) {
    const k = [
      EXPECT[name], SEATS[name] ?? '', toTicks(e.at), e.midi,
      e.beats === undefined ? '-' : toTicks(e.beats), gainOf(name, e.velocity),
    ].join('|')
    wanted.set(k, (wanted.get(k) ?? 0) + 1)
  }
}
const seen = new Map()
for (const p of inLoop) {
  const midiNote = p.hz !== undefined ? midiOf(p.hz)
    : p.open !== undefined ? (p.open ? 46 : 44)
      : p.midi ?? 36
  const len = p.dur === undefined ? '-' : Math.round(p.dur / SPB * TPB)
  const k = [p.voice, p.seat ?? '', tickOf(p.at), midiNote, len, p.vel.toFixed(12)].join('|')
  seen.set(k, (seen.get(k) ?? 0) + 1)
}
let drift = 0
let covered = 0
for (const [k, n] of wanted) {
  if (seen.get(k) === n) { covered += n; continue }
  drift++
  if (drift <= 5) fail(`chain: ${k} expected ${n}, scheduler produced ${seen.get(k) ?? 0}`)
}
for (const [k, n] of seen) if (!wanted.has(k)) fail(`chain: scheduler invented ${n}x ${k}`)
console.log(`\n  ${inLoop.length} voice calls in one loop; ` +
  `${covered}/${scoreTotal} events matched exactly on voice, seat, onset, pitch, length and gain`)

/* ---- the automation reaches the pitch buses ---- */

const autoLoop = automated.filter((a) => a.at >= ORIGIN - 1e-9 && a.at < ORIGIN + LOOP - 1e-9)
const wantAuto = new Map()
for (const [stream, store] of [['bend', score.BENDS], ['mod', score.MODS]]) {
  for (const [part, events] of Object.entries(store)) {
    for (const e of events) {
      const k = [stream, part, toTicks(e.at), stream === 'bend' ? e.cents : e.depth].join('|')
      wantAuto.set(k, (wantAuto.get(k) ?? 0) + 1)
    }
  }
}
const seenAuto = new Map()
for (const a of autoLoop) {
  const k = [a.stream, a.part, tickOf(a.at), a.value].join('|')
  seenAuto.set(k, (seenAuto.get(k) ?? 0) + 1)
}
let autoCovered = 0
let autoWanted = 0
for (const [k, n] of wantAuto) {
  autoWanted += n
  if (seenAuto.get(k) === n) { autoCovered += n; continue }
  fail(`automation: ${k} expected ${n}, scheduler produced ${seenAuto.get(k) ?? 0}`)
}
for (const [k, n] of seenAuto) if (!wantAuto.has(k)) fail(`automation: scheduler invented ${n}x ${k}`)
console.log(`  ${autoLoop.length} automation calls in one loop; ` +
  `${autoCovered}/${autoWanted} bend/mod points matched exactly on part, tick and value\n`)

/* --------------------------------------------------------------- verdict --- */

if (failures.length) {
  console.error(`PARITY FAILED (${failures.length}):`)
  for (const f of failures.slice(0, 40)) console.error(`  - ${f}`)
  process.exit(1)
}
console.log(`PARITY CONFIRMED: all ${MAP.length} reference tracks - ${refTotal} notes,`)
console.log(`${bendTotal} bend points, ${modTotal} mod points, and the window's mix state -`)
console.log('identical from the MIDI through the score to the scheduler.')
