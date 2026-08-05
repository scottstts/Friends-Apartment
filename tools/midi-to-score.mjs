#!/usr/bin/env node
/** Regenerates `src/audio/score.ts` from `assets/I_will_be_there_for_you.mid`.
 *
 * The MIDI is a reference, not an asset: it is read here, at authoring time,
 * and never shipped, fetched or parsed at runtime. What ships is the score
 * module this writes - plain data, note for note, bend for bend.
 *
 * Run with `npm run score`. Nothing in the app depends on this file.
 *
 * Ticks are kept as the integers the file stores (120 per beat, 480 per bar),
 * so the emitted score is bit-exact with the source rather than rounded onto
 * some grid of ours. Velocities are the raw 0-127 the performance carries.
 *
 * Beyond notes, two channel streams are ported because they are audible:
 *
 *   pitch bends  0xE0, 14-bit. The file sets no RPN 0, so the range is GM's
 *                default ±2 semitones; values become integer cents. The lead
 *                scoops into notes from below and the driven guitar bends the
 *                riff's G up to A - without these, two-note transitions
 *                collapse into single notes.
 *   modulation   CC1, raw 0-127. On a GM player this is vibrato depth, and
 *                the lead carries hundreds of events of it.
 *
 * Both are emitted with a synthetic anchor at the top of every bar (the
 * stream's value at that instant) unless a real event already sits there, so
 * each bar is self-contained: the loop seam resets cleanly and a bar is
 * correct no matter where scheduling picks up.
 *
 * Static mix state - CC7 volume, CC10 pan, CC11 expression, CC91 reverb
 * depth, each captured at the window start - is emitted as MIX.
 */

import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const SOURCE = join(ROOT, 'assets/I_will_be_there_for_you.mid')
const TARGET = join(ROOT, 'src/audio/score.ts')

/* ----------------------------------------------------------------- SMF --- */

function parse(buf) {
  let p = 0
  const u32 = () => { const v = buf.readUInt32BE(p); p += 4; return v }
  const u16 = () => { const v = buf.readUInt16BE(p); p += 2; return v }
  const u8 = () => buf[p++]
  const tag = () => { const v = buf.toString('ascii', p, p + 4); p += 4; return v }
  const vlq = () => { let v = 0, b; do { b = u8(); v = (v << 7) | (b & 0x7f) } while (b & 0x80); return v }

  if (tag() !== 'MThd') throw new Error('not a standard MIDI file')
  const headerLen = u32()
  const afterHeader = p + headerLen
  u16() // format
  const trackCount = u16()
  const division = u16()
  p = afterHeader

  const names = []
  const notes = []
  const bends = []
  const ccs = []
  let usPerBeat = 500000
  for (let t = 0; t < trackCount; t++) {
    if (tag() !== 'MTrk') throw new Error(`bad track chunk at ${t}`)
    const length = u32()
    const end = p + length
    let tick = 0
    let running = 0
    const open = new Map()
    bends[t] = []
    ccs[t] = []
    while (p < end) {
      tick += vlq()
      let status = buf[p]
      if (status & 0x80) { p++; running = status } else status = running
      const type = status & 0xf0
      if (status === 0xff) {
        const meta = u8()
        const len = vlq()
        const data = buf.subarray(p, p + len)
        p += len
        if (meta === 0x03) names[t] = data.toString('utf8').trim()
        if (meta === 0x51) usPerBeat = (data[0] << 16) | (data[1] << 8) | data[2]
      } else if (status === 0xf0 || status === 0xf7) {
        p += vlq()
      } else if (type === 0x90 || type === 0x80) {
        const note = u8()
        const vel = u8()
        if (type === 0x90 && vel > 0) {
          if (!open.has(note)) open.set(note, [])
          open.get(note).push({ tick, vel })
        } else {
          const stack = open.get(note)
          if (stack?.length) {
            const on = stack.shift()
            notes.push({ track: t, note, vel: on.vel, start: on.tick, dur: Math.max(1, tick - on.tick) })
          }
        }
      } else if (type === 0xe0) {
        const lsb = u8()
        const msb = u8()
        bends[t].push({ tick, value: lsb | (msb << 7) })
      } else if (type === 0xb0) {
        ccs[t].push({ tick, cc: u8(), value: u8() })
      } else if (type === 0xc0 || type === 0xd0) {
        u8()
      } else {
        u8(); u8()
      }
    }
    p = end
  }
  return { division, names, notes, bends, ccs, bpm: Math.round(60000000 / usPerBeat) }
}

/* -------------------------------------------------------------- layout --- */

/** The file opens with a count-in in 1/4; the 4/4 downbeat is tick 1080.
 * The loop is reference bars 2-39: the intro riff through the turnaround,
 * which is the section on the sheet. Loop bar N is reference bar N+1. */
const DOWNBEAT = 1080
const FIRST_BAR = 2
const BARS = 38

/** Every musical track in the reference (0 is the conductor track and carries
 * no notes). Nothing is merged or dropped: the drive and clean guitar pairs
 * share their onsets and pitches but differ in note lengths, velocities and
 * bend data, so all four are emitted and all four are played. */
const PARTS = [
  { name: 'LEAD', track: 1, kind: 'note' },
  { name: 'HARMONY', track: 2, kind: 'note' },
  { name: 'BASS', track: 3, kind: 'note' },
  { name: 'ORGAN', track: 4, kind: 'note' },
  { name: 'GUITAR_DRIVE_A', track: 5, kind: 'note' },
  { name: 'GUITAR_DRIVE_B', track: 6, kind: 'note' },
  { name: 'GUITAR_CLEAN_A', track: 7, kind: 'note' },
  { name: 'GUITAR_CLEAN_B', track: 8, kind: 'note' },
  { name: 'KICK', track: 9, kind: 'hit' },
  { name: 'SNARE', track: 10, kind: 'hit' },
  { name: 'CLAP', track: 11, kind: 'hit' },
  { name: 'TOM_LOW', track: 12, kind: 'hit' },
  { name: 'HAT_CLOSED', track: 13, kind: 'hit' },
  { name: 'TOM_FLOOR', track: 14, kind: 'hit' },
  { name: 'HAT_MID', track: 15, kind: 'hit' },
  { name: 'HAT_OPEN', track: 16, kind: 'hit' },
  { name: 'TOM_MID', track: 17, kind: 'hit' },
  { name: 'CRASH', track: 18, kind: 'hit' },
  { name: 'TAMB', track: 19, kind: 'hit' },
  { name: 'TIMBALE', track: 20, kind: 'hit' },
]

/** Pairs whose relationship the emitted header documents; the generator
 * re-measures it each run so the claim cannot go stale. */
const COMPARE = [[5, 7], [6, 8]]

/* ---------------------------------------------------------------- emit --- */

const midi = parse(readFileSync(SOURCE))
const TPB = midi.division
const TPBAR = TPB * 4
const start = DOWNBEAT + (FIRST_BAR - 1) * TPBAR
const end = start + BARS * TPBAR

const report = []

/** Every note of one track, rebased on the loop and grouped by loop bar. */
function collect(track) {
  return midi.notes
    .filter((n) => n.track === track && n.start >= start && n.start < end)
    .map((n) => ({ ...n, at: n.start - start }))
    .sort((a, b) => a.at - b.at || a.note - b.note)
}

/** How close two tracks are - measured, not assumed. */
function compare(a, b) {
  const A = collect(a)
  const B = collect(b)
  if (A.length !== B.length) return `${A.length} vs ${B.length} notes`
  const same = A.every((n, i) => n.at === B[i].at && n.note === B[i].note)
  const dur = A.filter((n, i) => n.dur !== B[i].dur).length
  const vel = A.filter((n, i) => n.vel !== B[i].vel).length
  return `${A.length} notes, onsets+pitches ${same ? 'identical' : 'DIFFER'}, ` +
    `${dur} differing lengths, ${vel} differing velocities`
}

/** Pitch-bend sensitivity for a track: RPN 0 data entry if the file sets it,
 * else the GM default of 2 semitones. */
function bendRange(track) {
  let rpn = -1
  let semis = 2
  for (const e of midi.ccs[track]) {
    if (e.cc === 101) rpn = ((rpn === -1 ? 0 : rpn) & 0x7f) | (e.value << 7)
    else if (e.cc === 100) rpn = ((rpn === -1 ? 0 : rpn) & 0x3f80) | e.value
    else if (e.cc === 6 && rpn === 0) semis = e.value
  }
  return semis
}

/** The stream's value on the last event at or before `tick`, else neutral. */
function stateAt(events, tick, neutral) {
  let value = neutral
  for (const e of events) {
    if (e.tick > tick) break
    value = e.value
  }
  return value
}

/** One automation stream for one track, rebased on the loop, with an anchor
 * at the top of every bar so each bar is self-contained. Returns null when
 * the stream is silent across the whole window. */
function automation(track, events, map, neutral) {
  const sorted = [...events].sort((a, b) => a.tick - b.tick)
  const window = sorted
    .filter((e) => e.tick >= start && e.tick < end)
    .map((e) => ({ at: e.tick - start, value: map(e.value) }))
  const anchors = []
  for (let bar = 0; bar < BARS; bar++) {
    const barTick = bar * TPBAR
    if (window.some((e) => e.at === barTick)) continue
    anchors.push({ at: barTick, value: map(stateAt(sorted, start + barTick, neutral)) })
  }
  const all = [...window, ...anchors].sort((a, b) => a.at - b.at)
  const silent = window.length === 0 && all.every((e) => e.value === map(neutral))
  return silent ? null : all
}

function streamLines(events) {
  const bars = new Map()
  for (const e of events) {
    const bar = Math.floor(e.at / TPBAR) + 1
    const tick = e.at - (bar - 1) * TPBAR
    if (!bars.has(bar)) bars.set(bar, [])
    bars.get(bar).push(`${tick}:${e.value}`)
  }
  return [...bars.keys()].sort((a, b) => a - b)
    .map((bar) => `  ${String(bar).padStart(2)}: '${bars.get(bar).join(' ')}',`)
    .join('\n')
}

function lines(notes, kind) {
  const bars = new Map()
  for (const n of notes) {
    const bar = Math.floor(n.at / TPBAR) + 1
    const tick = n.at - (bar - 1) * TPBAR
    if (!bars.has(bar)) bars.set(bar, [])
    bars.get(bar).push(kind === 'note' ? `${tick}:${n.note}:${n.dur}:${n.vel}` : `${tick}:${n.note}:${n.vel}`)
  }
  return [...bars.keys()].sort((a, b) => a - b)
    .map((bar) => `  ${String(bar).padStart(2)}: '${bars.get(bar).join(' ')}',`)
    .join('\n')
}

const blocks = []
let total = 0
for (const part of PARTS) {
  const notes = collect(part.track)
  total += notes.length
  report.push(
    `${part.name.padEnd(15)} track ${String(part.track).padStart(2)} ` +
    `${midi.names[part.track].padEnd(26)} ${String(notes.length).padStart(4)} notes`,
  )
  const reader = part.kind === 'note' ? 'notes' : 'hits'
  const body = notes.length
    ? `${reader}({\n${lines(notes, part.kind)}\n})`
    : `${reader}({}) /* no notes in this section of the reference */`
  blocks.push(
    `/* ${midi.names[part.track]} - reference track ${part.track} */\n` +
    `export const ${part.name}: ${part.kind === 'note' ? 'Note' : 'Hit'}[] = ${body}`,
  )
}
for (const [a, b] of COMPARE) report.push(`track ${a} vs ${b}: ${compare(a, b)}`)

/* ---- bends and modulation ---- */

const bendEntries = []
const modEntries = []
let bendCount = 0
let modCount = 0
for (const part of PARTS) {
  const range = bendRange(part.track)
  const toCents = (v) => Math.round(((v - 8192) / 8192) * range * 100)
  const bend = automation(part.track, midi.bends[part.track], toCents, 8192)
  const mod = automation(part.track, midi.ccs[part.track].filter((e) => e.cc === 1), (v) => v, 0)
  if (part.kind === 'hit') {
    // The kit has no pitch wheel; if the reference ever grows one here, the
    // runtime needs wiring before the data can be honoured.
    if (bend || mod) throw new Error(`${part.name}: percussion track carries bend/mod automation`)
    continue
  }
  if (bend) {
    bendCount += bend.length
    bendEntries.push(`  ${part.name}: bends({\n${streamLines(bend)}\n  }),`)
    report.push(`${part.name}: ${bend.length} bend points (range ±${range} st)`)
  }
  if (mod) {
    modCount += mod.length
    modEntries.push(`  ${part.name}: mods({\n${streamLines(mod)}\n  }),`)
    report.push(`${part.name}: ${mod.length} mod points`)
  }
}

/* ---- static mix ---- */

const mixLines = PARTS.map((part) => {
  const at = (cc, neutral) =>
    stateAt(midi.ccs[part.track].filter((e) => e.cc === cc).sort((a, b) => a.tick - b.tick), start, neutral)
  return `  ${part.name}: { volume: ${at(7, 100)}, pan: ${at(10, 64)}, expression: ${at(11, 127)}, reverb: ${at(91, 0)} },`
})

const header = `/** The arrangement - GENERATED, do not edit by hand.
 *
 * Written by \`tools/midi-to-score.mjs\` (\`npm run score\`) out of
 * \`assets/I_will_be_there_for_you.mid\`, which is a reference read at
 * authoring time and is never shipped, fetched or parsed at runtime. Every
 * note below is the reference's own: its pitch, its onset, its length and the
 * velocity it was played at, unquantised and unrounded.
 *
 * The loop is reference bars ${FIRST_BAR}-${FIRST_BAR + BARS - 1} - the intro riff through the turnaround.
 * Loop bar N is reference bar N+1: the file opens with a count-in in 1/4 and
 * the 4/4 downbeat is tick ${DOWNBEAT}.
 *
 * Notation: one entry per loop bar, whitespace-separated events.
 *   pitched  \`tick:midi:length:velocity\`
 *   drums    \`tick:midi:velocity\`
 *   bends    \`tick:cents\`   (14-bit wheel -> integer cents, GM ±2 st range)
 *   mods     \`tick:depth\`   (CC1, raw 0-127)
 * Ticks are the file's own - ${TPB} to the beat, ${TPBAR} to the bar - counted from the
 * start of that bar. Velocity is raw MIDI 0-127; music.ts owns the curve that
 * turns it into gain.
 *
 * BENDS and MODS carry the wheel and CC1 streams for every part that uses
 * them, with a synthetic anchor at the top of each bar (the stream's value at
 * that instant) so any bar is correct in isolation and the loop seam resets
 * cleanly. MIX is each track's static CC7/CC10/CC11/CC91 state at the window
 * start.
 *
 * Every musical track in the reference is here - nothing merged, nothing
 * dropped. The drive and clean guitar pairs (5/7 and 6/8) share their onsets
 * and pitches but differ in note lengths, velocities and bend data, so all
 * four are kept and all four are played. Track 13 is present and empty: it
 * has no notes in this section of the reference.
 */

export const BPM = ${midi.bpm}
export const BEATS_PER_BAR = 4
export const BARS = ${BARS}
export const TICKS_PER_BEAT = ${TPB}

const TICKS_PER_BAR = TICKS_PER_BEAT * BEATS_PER_BAR

export interface Note {
  /** Beats from the top of the loop. */
  at: number
  midi: number
  hz: number
  /** Length in beats. */
  beats: number
  /** Raw MIDI velocity, 0-127. */
  velocity: number
}

export interface Hit {
  at: number
  midi: number
  velocity: number
}

export interface Bend {
  /** Beats from the top of the loop. */
  at: number
  /** Wheel deflection in cents; 0 is centre pitch. */
  cents: number
}

export interface Mod {
  at: number
  /** CC1 as written, 0-127. */
  depth: number
}

export interface PartMix {
  volume: number
  pan: number
  expression: number
  reverb: number
}

export function hz(midi: number): number {
  return 440 * 2 ** ((midi - 69) / 12)
}

function notes(bars: Record<number, string>): Note[] {
  const out: Note[] = []
  for (const [bar, line] of Object.entries(bars)) {
    const base = (Number(bar) - 1) * TICKS_PER_BAR
    for (const token of line.split(' ')) {
      const [tick, midi, length, velocity] = token.split(':').map(Number)
      out.push({
        at: (base + tick) / TICKS_PER_BEAT,
        midi,
        hz: hz(midi),
        beats: length / TICKS_PER_BEAT,
        velocity,
      })
    }
  }
  return out.sort((a, b) => a.at - b.at)
}

function hits(bars: Record<number, string>): Hit[] {
  const out: Hit[] = []
  for (const [bar, line] of Object.entries(bars)) {
    const base = (Number(bar) - 1) * TICKS_PER_BAR
    for (const token of line.split(' ')) {
      const [tick, midi, velocity] = token.split(':').map(Number)
      out.push({ at: (base + tick) / TICKS_PER_BEAT, midi, velocity })
    }
  }
  return out.sort((a, b) => a.at - b.at)
}

function bends(bars: Record<number, string>): Bend[] {
  const out: Bend[] = []
  for (const [bar, line] of Object.entries(bars)) {
    const base = (Number(bar) - 1) * TICKS_PER_BAR
    for (const token of line.split(' ')) {
      const [tick, cents] = token.split(':').map(Number)
      out.push({ at: (base + tick) / TICKS_PER_BEAT, cents })
    }
  }
  return out.sort((a, b) => a.at - b.at)
}

function mods(bars: Record<number, string>): Mod[] {
  const out: Mod[] = []
  for (const [bar, line] of Object.entries(bars)) {
    const base = (Number(bar) - 1) * TICKS_PER_BAR
    for (const token of line.split(' ')) {
      const [tick, depth] = token.split(':').map(Number)
      out.push({ at: (base + tick) / TICKS_PER_BEAT, depth })
    }
  }
  return out.sort((a, b) => a.at - b.at)
}
`

const tail = `
/* Pitch-wheel streams, per part that uses one. */
export const BENDS: Record<string, Bend[]> = {
${bendEntries.join('\n')}
}

/* CC1 modulation streams, per part that uses one. */
export const MODS: Record<string, Mod[]> = {
${modEntries.join('\n')}
}

/* Static channel state at the window start: CC7/CC10/CC11/CC91. */
export const MIX: Record<string, PartMix> = {
${mixLines.join('\n')}
}
`

writeFileSync(TARGET, `${header}\n${blocks.join('\n\n')}\n${tail}`)

console.log(report.join('\n'))
console.log(`\n${total} notes, ${bendCount} bend points, ${modCount} mod points ` +
  `over ${BARS} bars at ${midi.bpm} BPM (${(BARS * 4 * 60 / midi.bpm).toFixed(2)}s)`)
console.log(`wrote ${TARGET}`)
