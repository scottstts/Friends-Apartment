# Audio

One 48-second loop of theme music, generated. There is no audio file in the
project and none is fetched: every note, drum, bend and effect is oscillators,
filters and seeded noise scheduled onto the Web Audio graph at runtime. The
whole soundtrack costs ~5 kB gzipped.

| File | Covers |
| --- | --- |
| `src/audio/synth.ts` | The instrument bank, pitch automation and effect chain — pure DSP |
| `src/audio/score.ts` | **Generated.** The arrangement as data: notes, bends, mods, mix |
| `src/audio/music.ts` | Casting table, scheduler, and the scene-scoped play state |
| `tools/midi-to-score.mjs` | Writes `score.ts` from the reference (`npm run score`) |
| `tools/verify-parity.mjs` | Proves the result is the reference (`npm run verify:score`) |

## The reference, and what "reference" means

`assets/I_will_be_there_for_you.mid` is a 21-track performance capture. It is
read **at authoring time only** — never shipped, never fetched, never parsed
at runtime. What ships is `score.ts`, plain data written out of it.

Every musical track is ported, and so is every audible channel stream:

- **1299 notes** across all 20 musical tracks (lead, backing harmony, bass,
  organ, four guitar prints, and a 12-piece kit), each with the file's own
  integer-tick onset and length and its raw 0–127 velocity.
- **790 pitch-bend points.** The wheel streams of the lead (508), Drive
  GTR 1 (172), Drive GTR 2 (55) and Clean GTR 2 (55). The file sets no RPN,
  so the range is GM's ±2 semitones; values ship as integer cents. These are
  the whole-step scoops and the riff's G-bent-up-to-A — without them,
  two-note transitions collapse into single notes, which is exactly how the
  gap was found.
- **710 CC1 modulation points.** On a GM player CC1 is vibrato depth; the
  lead carries 564 points of it. Rendered as a 5.5 Hz LFO at ±40 cents full
  wheel.
- **MIX**: each track's static CC7 volume / CC10 pan / CC11 expression /
  CC91 reverb state at the window start.

Things worth knowing about the source:

- The **drive and clean guitar pairs** (5/7 and 6/8) share every onset and
  pitch but differ in note lengths, velocities *and bends* — Drive GTR 1
  bends through the intro riff while Clean GTR 1 plays it straight, which is
  what the file says and what plays. All four prints are kept.
- **Bend and mod streams carry a synthetic anchor** at the top of every bar —
  the stream's value at that instant — unless a real event already sits
  there. Any bar is then correct in isolation: the loop seam resets the
  wheel, and a catch-up rejoin lands on correct state. The verifier applies
  the same rule independently.
- The reference is a **human performance**: onsets, bends and velocities
  land where they were played, unquantised and unrounded.

## Layout

The loop is reference bars 2–39 — the intro riff through the turnaround, the
section on the sheet. Loop bar N is reference bar N+1: the file opens with a
count-in in 1/4 and the 4/4 downbeat is tick 1080.

38 bars, A major, 190 BPM, 4/4 — 48.00 s exactly. Intro riff (1–8), verse
(9–16, the four claps in bar 12), bridge (17–24), chorus (25–36, claps on 2
and 4), turnaround (37–38).

## Verifying parity

`npm run verify:score` re-parses the MIDI with its **own** reader — not the
generator's — and checks the *compiled* `score.ts`, so the score's runtime
decoder is exercised too and a generator bug cannot hide behind itself. It
exits non-zero on any mismatch. Two layers, because data parity alone is not
enough — a part nothing plays would still be silent:

1. **Data** — every note appears with identical onset, pitch, length and
   velocity (integer ticks); every bend and mod point appears in its part's
   stream with identical tick and value under the same anchor rule; MIX
   matches the recomputed window-start controller state; the score invents
   nothing; no track and no stream is left unported.
2. **Playback** — the real `Music` scheduler runs against a stubbed Web Audio
   API and a fake clock. Every note must arrive at a synth voice with onset,
   pitch, length, **gain** (the velocity curve times the part's MIX scale)
   and stereo seat intact; every bend and mod point must arrive at
   `scheduleBend`/`scheduleMod` with part, tick and value intact.

## Timbres and pitch automation

Late-nineties dance-rock, built from scratch: the lead is a two-operator FM
voice, the DX-era electric-piano family - two slightly detuned carrier sines
each frequency-modulated by its own 2:1 modulator, the modulation index
opening with the attack and settling as the note holds, scaled by velocity so
harder notes ring brighter (FM's own expression). All sidebands, no filters
to muffle; carriers and modulators ride the pitch bus together so bends never
shift the ratio, and a faint plain octave sine adds air. Around it: a softer
supersaw backing harmony, four-drawbar organ with key click, two amp channels
(a shared `tanh` overdrive for the driven prints, a brighter clean pair),
saw/square/sub bass through its own drive, and a synthesised kit whose clap
is three noise slaps 11 ms apart plus a room tail. Sends are a tempo-locked
dotted-eighth ping-pong delay and a plate reverb whose impulse response is
generated seeded noise. The lead's FM sidebands sit mid/treble, so it reads
louder than its measured RMS suggests.

Pitch automation is a per-part **pitch bus** in cents, summed into the
`detune` of every oscillator that part plays — the wheel as a
`ConstantSourceNode` stepped by `scheduleBend` (steps, not ramps: a stepped
stream is exactly how the reference's player renders the wheel, and the
gestures are a few milliseconds apart), and CC1 vibrato as a fixed-rate LFO
whose depth `scheduleMod` sets. One bus per part, alive until the synth is
torn down — exactly a MIDI channel's pitch state.

## The mix is the file's, then measured

Per-part levels come from the reference: CC7 volume and CC11 expression on
the GM 40·log10 curve, normalised so the loudest part sits at unity. Per-bus
plate depth comes from each track's CC91 (organ and clean guitars wet,
harmony and bass dry, at `PLATE_DEPTH` × cc91/127). The file pans every track
centre; the stereo seats (double-tracked guitars left/right, harmony right of
centre) are this port's reading of a double-tracked band, not the file's —
the one deliberate rendering liberty, documented here.

Under those scales, the bus staging keeps the measured balance from the
20-track load model: ~0.6 peak into a −12 dB / 2.5:1 glue compressor, so it
glues transients rather than limiting the programme. `MASTER` in music.ts is
a clean output trim.

## Lifecycle: the music belongs to the scenes

Silent on the landing; no in-game UI. `main.ts` drives four transport calls:

| Moment | Call | Effect |
| --- | --- | --- |
| Scene entered (`tryEnter`) | `begin()` | loop starts from the top |
| Esc (pause veil up) | `pause()` | fade out, context suspends, position holds |
| Pointer lock re-acquired | `resume()` | picks up exactly where pause left it |
| Walked out to the hallway | `reset()` | silence, rewind; next scene starts over |

The one sound surface is the pause veil's row (`src/ui/sound.ts`, the
`MusicUi` interface): a horizontal slider - recessed groove, gold fill,
brass bead thumb - and the brass speaker that mutes, on one line. The slider
is **master volume**: it scales the single master gain (`MASTER × volume`),
never a per-track level. Mute rides the same suspend machinery as pause
(position freezes; unmute picks it back up), and both settings are the
visitor's, surviving scene resets. The slider answers a press-or-drag
anywhere along its length, the scroll wheel, and arrow keys; the row
contains its own events so the veil's whole-surface Resume never fires from
it.

Pausing suspends the `AudioContext`: `currentTime` freezes, the scheduler
stalls on its own, and every note in flight resumes mid-ring. `reset()` also
marks the graph **stale** — the next `begin()` rebuilds the synth, so the
dead scene's already-scheduled tail (the lookahead runs ~1.5 s deep) can
never leak into the next scene's fresh start.

`begin()` always runs downstream of a door click, so the autoplay gate is
already satisfied; the one-shot gesture fallback stays for the day it is not.

## Transport

The usual two-clock arrangement: a 100 ms `setInterval` that only ever hands
work to the audio clock. Each tick pushes whole bars — notes, bends, mods —
into the graph until the schedule runs 1.5 s past the present, so timer
jitter cannot reach the notes. Bar times accumulate arithmetically; the loop
does not drift however long it runs. Parts are bucketed per bar at
construction, so a tick is a lookup.
