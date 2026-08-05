/** The instrument bank for the title music.
 *
 * Everything here is generated: there is not one audio file in the project.
 * Every timbre is oscillators, filters and shaped noise scheduled on the Web
 * Audio graph, and the noise itself comes from a seeded PRNG so a given note
 * sounds identical on every visit.
 *
 * There is one voice per band member in the reference - lead, backing
 * harmony, bass, organ, two guitars each printed twice (driven and clean),
 * and a full kit - because the score plays every one of the reference's
 * tracks. The palette is the one the show's theme grew up next to: late
 * nineties, early two-thousands, detuned and filtered.
 *
 * Signal flow:
 *
 *   lead/harmony ─┐                     ┌─→ delay (dotted 8th, ping-pong) ─┐
 *   organ ────────┼─→ chorus ───────────┤                                  │
 *   guitar clean ─┘                     └─→ plate (generated impulse) ─────┤
 *   guitar drive ──→ amp drive ──────────────────────────────────────────┐ │
 *   bass ──────────→ bass drive ───────────────────────────────────────┐ │ │
 *   drums ───────────────────────────────────────────────────────────┐ │ │ │
 *                                                                    ▼ ▼ ▼ ▼
 *                                            glue compressor → master → out
 */

/* ---------------------------------------------------------------- noise --- */

/** Small, fast, well-distributed PRNG - the same one the scene code uses for
 * reproducible procedural detail, here so the noise beds never change. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function noiseBuffer(ctx: BaseAudioContext, seconds: number, seed: number): AudioBuffer {
  const buffer = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * seconds), ctx.sampleRate)
  const data = buffer.getChannelData(0)
  const rand = mulberry32(seed)
  for (let i = 0; i < data.length; i++) data[i] = rand() * 2 - 1
  return buffer
}

/** A plate-ish impulse response: decorrelated stereo noise under an
 * exponential envelope, with the first few milliseconds swept in so the tail
 * blooms instead of cracking. */
function plateImpulse(ctx: BaseAudioContext, seconds: number, decay: number, seed: number): AudioBuffer {
  const length = Math.ceil(ctx.sampleRate * seconds)
  const buffer = ctx.createBuffer(2, length, ctx.sampleRate)
  const rand = mulberry32(seed)
  const bloom = Math.ceil(ctx.sampleRate * 0.012)
  for (let channel = 0; channel < 2; channel++) {
    const data = buffer.getChannelData(channel)
    for (let i = 0; i < length; i++) {
      const t = i / length
      const swell = i < bloom ? i / bloom : 1
      data[i] = (rand() * 2 - 1) * swell * Math.pow(1 - t, decay)
    }
  }
  return buffer
}

/** tanh soft clip, normalised so the curve still spans ±1 at full drive. */
function driveCurve(amount: number): Float32Array<ArrayBuffer> {
  const curve = new Float32Array(1024)
  const norm = Math.tanh(amount)
  for (let i = 0; i < curve.length; i++) {
    const x = (i / (curve.length - 1)) * 2 - 1
    curve[i] = Math.tanh(x * amount) / norm
  }
  return curve
}

/* ------------------------------------------------------------ envelopes --- */

/** Exponential ramps cannot reach zero, so every decay lands on this floor
 * and is then pinned to silence. */
const SILENCE = 1e-4

function decayTo(param: AudioParam, value: number, at: number): void {
  param.exponentialRampToValueAtTime(Math.max(SILENCE, value), at)
}

/** Percussive amplitude shape: instant rise, exponential fall. */
function hit(gain: GainNode, at: number, peak: number, fall: number): void {
  const g = gain.gain
  g.setValueAtTime(SILENCE, at)
  g.exponentialRampToValueAtTime(Math.max(SILENCE, peak), at + 0.002)
  g.exponentialRampToValueAtTime(SILENCE, at + fall)
  g.setValueAtTime(0, at + fall + 0.005)
}

/** Sustained shape: attack, decay to sustain, hold for `dur`, then release.
 * Returns the time the voice can be torn down. */
function adsr(
  gain: GainNode,
  at: number,
  dur: number,
  peak: number,
  attack: number,
  decay: number,
  sustain: number,
  release: number,
): number {
  const g = gain.gain
  const end = at + Math.max(dur, attack + 0.02)
  g.setValueAtTime(SILENCE, at)
  g.exponentialRampToValueAtTime(Math.max(SILENCE, peak), at + attack)
  decayTo(g, peak * sustain, at + attack + decay)
  g.setValueAtTime(Math.max(SILENCE, peak * sustain), end)
  decayTo(g, SILENCE, end + release)
  g.setValueAtTime(0, end + release + 0.005)
  return end + release + 0.02
}

/* ---------------------------------------------------------------- Synth --- */

/** Metallic partials of the classic analogue hat - squares at inharmonic
 * ratios over a 40 Hz fundamental. */
const HAT_RATIOS = [2, 3, 4.16, 5.43]
const HAT_BASE = 40

/** Drawbar levels for the organ: 8', 4', 2 2/3' and 2'. */
const DRAWBARS: [number, number][] = [[1, 1], [2, 0.58], [3, 0.32], [4, 0.22]]

/** CC1 vibrato, the GM reading: a sine LFO into pitch, depth scaled by the
 * wheel. Full wheel is ±40 cents at 5.5 Hz. */
const VIBRATO_HZ = 5.5
const VIBRATO_CENTS = 40

/** Plate depth at cc91 = 127; each bus's send is this times its cc91/127. */
const PLATE_DEPTH = 0.28

export type BusName = 'lead' | 'harmony' | 'bass' | 'organ' | 'drive' | 'clean' | 'drums'

export interface SynthOptions {
  /** Seconds per beat - the delay time is locked to a dotted eighth. */
  secondsPerBeat: number
  /** Per-bus reverb depth 0..1, derived from the reference's cc91 values. */
  reverb: Record<BusName, number>
}

export class Synth {
  readonly ctx: AudioContext
  readonly master: GainNode

  private noise: AudioBuffer
  private leadBus: GainNode
  private harmonyBus: GainNode
  private organBus: GainNode
  private bassBus: GainNode
  private driveBus: GainNode
  private cleanBus: GainNode
  private drumBus: GainNode
  private reverbSend: GainNode
  private delaySend: GainNode
  /** One panner per guitar seat, reused by every note on that track. */
  private seats = new Map<string, GainNode>()

  constructor(ctx: AudioContext, options: SynthOptions) {
    this.ctx = ctx
    this.noise = noiseBuffer(ctx, 2, 0x5eed)

    // ---- master: one glue compressor so the chorus never pumps the mix ----
    this.master = ctx.createGain()
    this.master.gain.value = 0
    // Glue, not limiting: the bus gains below are set so the summed programme
    // sits near -10 dBFS and only transients cross the threshold.
    const glue = ctx.createDynamicsCompressor()
    glue.threshold.value = -12
    glue.knee.value = 20
    glue.ratio.value = 2.5
    glue.attack.value = 0.006
    glue.release.value = 0.22
    glue.connect(this.master)
    this.master.connect(ctx.destination)

    // ---- sends ----
    const plate = ctx.createConvolver()
    plate.buffer = plateImpulse(ctx, 1.9, 2.4, 0x1f0e)
    const plateTone = ctx.createBiquadFilter()
    plateTone.type = 'highpass'
    plateTone.frequency.value = 320
    this.reverbSend = ctx.createGain()
    this.reverbSend.gain.value = 1
    this.reverbSend.connect(plate)
    plate.connect(plateTone)
    plateTone.connect(glue)

    // Dotted-eighth ping-pong: the delay that dates this music precisely.
    const time = options.secondsPerBeat * 0.75
    const left = ctx.createDelay(1)
    const right = ctx.createDelay(1)
    left.delayTime.value = time
    right.delayTime.value = time
    const feedback = ctx.createGain()
    feedback.gain.value = 0.3
    const damp = ctx.createBiquadFilter()
    damp.type = 'lowpass'
    damp.frequency.value = 3200
    const panL = ctx.createStereoPanner()
    const panR = ctx.createStereoPanner()
    panL.pan.value = -0.75
    panR.pan.value = 0.75
    this.delaySend = ctx.createGain()
    this.delaySend.gain.value = 1
    this.delaySend.connect(left)
    left.connect(panL)
    left.connect(damp)
    damp.connect(feedback)
    feedback.connect(right)
    right.connect(panR)
    right.connect(left)
    panL.connect(glue)
    panR.connect(glue)

    // ---- chorus: two modulated taps, hard left and right of the dry line ----
    // Dry and wet are set so the chorus widens at roughly unity gain rather
    // than adding level on top of the buses feeding it.
    const chorusIn = ctx.createGain()
    const chorusOut = ctx.createGain()
    const chorusDry = ctx.createGain()
    chorusDry.gain.value = 0.75
    chorusIn.connect(chorusDry)
    chorusDry.connect(chorusOut)
    for (const [delayTime, rate, depth, pan] of [
      [0.0142, 0.18, 0.0028, -0.85],
      [0.0211, 0.27, 0.0021, 0.85],
    ]) {
      const tap = ctx.createDelay(0.1)
      tap.delayTime.value = delayTime
      const lfo = ctx.createOscillator()
      lfo.type = 'sine'
      lfo.frequency.value = rate
      const swing = ctx.createGain()
      swing.gain.value = depth
      lfo.connect(swing)
      swing.connect(tap.delayTime)
      lfo.start()
      const spread = ctx.createStereoPanner()
      spread.pan.value = pan
      const level = ctx.createGain()
      level.gain.value = 0.4
      chorusIn.connect(tap)
      tap.connect(spread)
      spread.connect(level)
      level.connect(chorusOut)
    }
    chorusOut.connect(glue)

    const bus = (gain: number, dest: AudioNode): GainNode => {
      const node = ctx.createGain()
      node.gain.value = gain
      node.connect(dest)
      return node
    }

    // ---- amp stages ----
    // A WaveShaper clamps its input to ±1, so each drive stage is bracketed:
    // a gain that lands the summed bus just under 1, the curve, then a trim
    // that sets the level. Driving into the curve rather than after it is
    // what makes these saturate like an amp instead of scaling like a fader.
    // The driven guitars share one overdrive, as two channels of one amp
    // would; the bass keeps its own so the low end never smears into it.
    const ampShaper = ctx.createWaveShaper()
    ampShaper.curve = driveCurve(3.2)
    ampShaper.oversample = '4x'
    const ampTone = ctx.createBiquadFilter()
    ampTone.type = 'lowpass'
    ampTone.frequency.value = 3000
    ampTone.Q.value = 0.7
    const ampBody = ctx.createBiquadFilter()
    ampBody.type = 'highpass'
    ampBody.frequency.value = 110
    const ampTrim = bus(0.2, glue)
    ampShaper.connect(ampTone)
    ampTone.connect(ampBody)
    ampBody.connect(ampTrim)
    this.driveBus = bus(0.45, ampShaper)

    const bassShaper = ctx.createWaveShaper()
    bassShaper.curve = driveCurve(2.2)
    bassShaper.oversample = '2x'
    const bassTone = ctx.createBiquadFilter()
    bassTone.type = 'lowpass'
    bassTone.frequency.value = 3400
    const bassTrim = bus(0.26, glue)
    bassShaper.connect(bassTone)
    bassTone.connect(bassTrim)
    this.bassBus = bus(0.5, bassShaper)

    // ---- instrument buses ----
    // Balanced by measurement, not by ear: see dev_docs/audio.md. The lead's
    // FM sidebands sit mid/treble, so it reads louder than its RMS suggests.
    this.leadBus = bus(0.16, chorusIn)
    this.harmonyBus = bus(0.05, chorusIn)
    this.organBus = bus(0.08, chorusIn)
    this.cleanBus = bus(0.07, chorusIn)
    this.drumBus = bus(0.36, glue)

    // Delay sends are a rendering flavour; the plate sends are the file's own
    // cc91 depths. Driven and bass sends tap after their amps, not before -
    // the reverb should hear the guitar everyone hears.
    this.leadBus.connect(this.tap(0.22, this.delaySend))
    this.cleanBus.connect(this.tap(0.16, this.delaySend))
    const wet = (from: AudioNode, depth: number): void => {
      if (depth > 0) from.connect(this.tap(PLATE_DEPTH * depth, this.reverbSend))
    }
    wet(this.leadBus, options.reverb.lead)
    wet(this.harmonyBus, options.reverb.harmony)
    wet(this.organBus, options.reverb.organ)
    wet(this.cleanBus, options.reverb.clean)
    wet(ampTrim, options.reverb.drive)
    wet(bassTrim, options.reverb.bass)
    wet(this.drumBus, options.reverb.drums)
  }

  /* --------------------------------------------------------------- pitch --- */

  /** Per-part pitch automation, in cents, summed into every oscillator the
   * part plays: the wheel (a constant source stepped by `scheduleBend`) plus
   * CC1 vibrato (a fixed-rate LFO whose depth `scheduleMod` sets). One bus a
   * part, made on first use, alive until the synth is torn down - exactly a
   * MIDI channel's pitch state. */
  private pitch = new Map<string, GainNode>()
  private wheels = new Map<string, ConstantSourceNode>()
  private vibratos = new Map<string, GainNode>()

  private pitchBus(key: string): GainNode {
    let node = this.pitch.get(key)
    if (!node) {
      node = this.ctx.createGain()
      node.gain.value = 1
      this.pitch.set(key, node)
    }
    return node
  }

  /** Step the part's wheel to `cents` at `at` - steps, not ramps, because a
   * stepped stream is exactly how the reference's player renders the wheel,
   * and the file's gestures are dense enough (a few ms apart) to be smooth. */
  scheduleBend(key: string, at: number, cents: number): void {
    let wheel = this.wheels.get(key)
    if (!wheel) {
      wheel = this.ctx.createConstantSource()
      wheel.offset.value = 0
      wheel.connect(this.pitchBus(key))
      wheel.start()
      this.wheels.set(key, wheel)
    }
    wheel.offset.setValueAtTime(cents, at)
  }

  /** Set the part's CC1 vibrato depth (raw 0-127) at `at`. */
  scheduleMod(key: string, at: number, depth: number): void {
    let vibrato = this.vibratos.get(key)
    if (!vibrato) {
      const lfo = this.ctx.createOscillator()
      lfo.type = 'sine'
      lfo.frequency.value = VIBRATO_HZ
      vibrato = this.ctx.createGain()
      vibrato.gain.value = 0
      lfo.connect(vibrato)
      vibrato.connect(this.pitchBus(key))
      lfo.start()
      this.vibratos.set(key, vibrato)
    }
    vibrato.gain.setValueAtTime((depth / 127) * VIBRATO_CENTS, at)
  }

  /** Hang one oscillator off its part's pitch automation. */
  private tune(key: string | undefined, osc: OscillatorNode): void {
    if (key) this.pitchBus(key).connect(osc.detune)
  }

  private tap(gain: number, dest: AudioNode): GainNode {
    const node = this.ctx.createGain()
    node.gain.value = gain
    node.connect(dest)
    return node
  }

  /** A fixed stereo position on one of the tone buses. Guitars are
   * double-tracked hard-ish left and right, so their panners are made once
   * and shared rather than rebuilt per note. */
  private seat(key: string, pan: number, dest: GainNode): GainNode {
    let node = this.seats.get(key)
    if (!node) {
      const panner = this.ctx.createStereoPanner()
      panner.pan.value = pan
      panner.connect(dest)
      node = this.ctx.createGain()
      node.gain.value = 1
      node.connect(panner)
      this.seats.set(key, node)
    }
    return node
  }

  private source(at: number, stop: number): AudioBufferSourceNode {
    const node = this.ctx.createBufferSource()
    node.buffer = this.noise
    node.loop = true
    // Different slices of the bed per hit, so repeated drums never phase.
    node.loopStart = (at * 7.13) % 1.5
    node.loopEnd = node.loopStart + 0.4
    node.start(at, node.loopStart)
    node.stop(stop)
    return node
  }

  /* -------------------------------------------------------------- voices --- */

  /** The tune rides this: a two-operator FM lead, the DX-era electric-piano
   * family - none of the subtractive recipes tried before it. Each of two
   * slightly detuned carrier sines is frequency-modulated by its own 2:1
   * modulator; the modulation index opens with the attack and settles, so
   * every note speaks with a glassy front and warms as it holds, and harder
   * notes ring brighter (index scales with velocity - FM's own expression).
   * All sidebands, no filters to muffle: clear, mid-and-treble forward, and
   * the wheel's scoops and CC1 vibrato ride carriers and modulators together
   * so the ratio - the timbre - never drifts. A faint plain octave sine adds
   * air. */
  playLead(at: number, freq: number, dur: number, vel: number, key?: string): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    amp.connect(this.leadBus)
    const stop = adsr(amp, at, dur, vel, 0.008, 0.12, 0.8, 0.16)
    // Peak frequency deviation in Hz: index ~1.6 into the attack, ~0.55
    // held, scaled by how hard the note was played.
    const brightness = 0.55 + 0.45 * Math.min(1, vel * 2.4)
    let first: OscillatorNode | null = null
    for (const detune of [-3, 3]) {
      const carrier = ctx.createOscillator()
      carrier.type = 'sine'
      carrier.frequency.value = freq
      carrier.detune.value = detune
      this.tune(key, carrier)
      const modulator = ctx.createOscillator()
      modulator.type = 'sine'
      modulator.frequency.value = freq * 2
      modulator.detune.value = detune
      this.tune(key, modulator)
      const index = ctx.createGain()
      index.gain.setValueAtTime(freq * 3.2 * brightness, at)
      decayTo(index.gain, freq * 1.1 * brightness, at + 0.24)
      modulator.connect(index)
      index.connect(carrier.frequency)
      carrier.connect(amp)
      carrier.start(at)
      carrier.stop(stop)
      modulator.start(at)
      modulator.stop(stop)
      first ??= carrier
    }
    const air = ctx.createOscillator()
    air.type = 'sine'
    air.frequency.value = freq * 2
    air.detune.value = 4
    this.tune(key, air)
    const airMix = ctx.createGain()
    airMix.gain.value = 0.12
    air.connect(airMix)
    airMix.connect(amp)
    air.start(at)
    air.stop(stop)
    if (first) first.onended = () => amp.disconnect()
  }

  /** The backing vocal: the same family as the lead but softer, darker and
   * a little to one side, so it thickens the tune instead of competing. */
  playHarmony(at: number, freq: number, dur: number, vel: number, key?: string): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.Q.value = 2.5
    filter.frequency.setValueAtTime(Math.min(8000, 700 + freq * 4), at)
    decayTo(filter.frequency, Math.min(5200, 400 + freq * 2), at + 0.2)
    filter.connect(amp)
    amp.connect(this.seat('harmony', 0.3, this.harmonyBus))
    const stop = adsr(amp, at, dur, vel, 0.03, 0.12, 0.8, 0.2)
    let first: OscillatorNode | null = null
    for (const detune of [-11, 0, 11]) {
      const osc = ctx.createOscillator()
      osc.type = 'sawtooth'
      osc.frequency.value = freq
      osc.detune.value = detune
      this.tune(key, osc)
      osc.connect(filter)
      osc.start(at)
      osc.stop(stop)
      first ??= osc
    }
    if (first) first.onended = () => amp.disconnect()
  }

  /** Drawbar organ: four sine partials and the key click, straight into the
   * chorus for its Leslie-ish wobble. */
  playOrgan(at: number, freq: number, dur: number, vel: number, key?: string): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    amp.connect(this.organBus)
    const stop = adsr(amp, at, dur, vel, 0.012, 0.05, 0.92, 0.07)
    let first: OscillatorNode | null = null
    for (const [ratio, level] of DRAWBARS) {
      const osc = ctx.createOscillator()
      osc.type = 'sine'
      osc.frequency.value = freq * ratio
      this.tune(key, osc)
      const mix = ctx.createGain()
      mix.gain.value = level
      osc.connect(mix)
      mix.connect(amp)
      osc.start(at)
      osc.stop(stop)
      first ??= osc
    }
    if (first) first.onended = () => amp.disconnect()

    // Percussion click on the attack - the drawbar organ's signature.
    const click = ctx.createGain()
    hit(click, at, vel * 0.2, 0.03)
    const ping = ctx.createOscillator()
    ping.type = 'sine'
    ping.frequency.value = freq * 4
    this.tune(key, ping)
    ping.connect(click)
    click.connect(this.organBus)
    ping.start(at)
    ping.stop(at + 0.05)
    ping.onended = () => click.disconnect()
  }

  /** Rhythm guitar. `drive` picks the amp: the driven channel is two saws
   * pushed into the shared overdrive, the clean one a brighter, shorter pair
   * that keeps its pick attack. */
  playGuitar(at: number, freq: number, dur: number, vel: number, drive: boolean, seat: string, pan: number, key?: string): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.Q.value = drive ? 1.6 : 3
    filter.frequency.setValueAtTime(Math.min(11000, freq * (drive ? 7 : 10)), at)
    decayTo(filter.frequency, Math.min(6000, 500 + freq * (drive ? 3 : 2)), at + (drive ? 0.14 : 0.08))
    filter.connect(amp)
    amp.connect(this.seat(seat, pan, drive ? this.driveBus : this.cleanBus))
    const stop = drive
      ? adsr(amp, at, dur, vel, 0.006, 0.13, 0.72, 0.12)
      : adsr(amp, at, dur, vel, 0.004, 0.1, 0.5, 0.1)
    let first: OscillatorNode | null = null
    for (const [type, detune] of (drive
      ? [['sawtooth', -7], ['sawtooth', 7]]
      : [['sawtooth', -4], ['triangle', 4]]) as [OscillatorType, number][]) {
      const osc = ctx.createOscillator()
      osc.type = type
      osc.frequency.value = freq
      osc.detune.value = detune
      this.tune(key, osc)
      osc.connect(filter)
      osc.start(at)
      osc.stop(stop)
      first ??= osc
    }
    if (first) first.onended = () => amp.disconnect()
  }

  /** Saw + square over a sine sub, through the bass overdrive. */
  playBass(at: number, freq: number, dur: number, vel: number, key?: string): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    const filter = ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.Q.value = 4.5
    filter.frequency.setValueAtTime(Math.min(6000, 260 + freq * 9), at)
    decayTo(filter.frequency, Math.min(2200, 130 + freq * 2.2), at + 0.11)
    filter.connect(amp)
    amp.connect(this.bassBus)
    const stop = adsr(amp, at, dur, vel, 0.006, 0.1, 0.72, 0.07)
    let first: OscillatorNode | null = null
    for (const [type, mul, level] of [
      ['sawtooth', 1, 1],
      ['square', 1, 0.35],
      ['sine', 0.5, 0.85],
    ] as const) {
      const osc = ctx.createOscillator()
      osc.type = type
      osc.frequency.value = freq * mul
      this.tune(key, osc)
      const mix = ctx.createGain()
      mix.gain.value = level
      osc.connect(mix)
      // The sub bypasses the resonant sweep - it only has to be round.
      mix.connect(type === 'sine' ? amp : filter)
      osc.start(at)
      osc.stop(stop)
      first ??= osc
    }
    if (first) first.onended = () => amp.disconnect()
  }

  /* --------------------------------------------------------------- drums --- */

  /** Sine with a fast pitch drop, plus a noise click for the beater. */
  playKick(at: number, vel: number): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    amp.connect(this.drumBus)
    hit(amp, at, vel, 0.34)
    const osc = ctx.createOscillator()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(132, at)
    decayTo(osc.frequency, 46, at + 0.07)
    osc.connect(amp)
    osc.start(at)
    osc.stop(at + 0.36)
    osc.onended = () => amp.disconnect()

    const click = ctx.createGain()
    const edge = ctx.createBiquadFilter()
    edge.type = 'highpass'
    edge.frequency.value = 1400
    hit(click, at, vel * 0.18, 0.012)
    this.source(at, at + 0.02).connect(edge)
    edge.connect(click)
    click.connect(this.drumBus)
  }

  /** Noise body over two tuned shells. `tight` is the reference's electric
   * snare (GM 40) against its acoustic one (GM 38): brighter and shorter. */
  playSnare(at: number, vel: number, tight: boolean): void {
    const ctx = this.ctx
    const fall = tight ? 0.12 : 0.19
    const amp = ctx.createGain()
    const body = ctx.createBiquadFilter()
    body.type = 'bandpass'
    body.frequency.value = tight ? 2300 : 1750
    body.Q.value = 0.85
    hit(amp, at, vel, fall)
    body.connect(amp)
    amp.connect(this.drumBus)
    this.source(at, at + fall + 0.04).connect(body)

    for (const [freq, level, shell] of [
      [tight ? 220 : 188, 0.5, 0.1],
      [tight ? 288 : 242, 0.32, 0.075],
    ] as const) {
      const tone = ctx.createGain()
      hit(tone, at, vel * level, shell)
      const osc = ctx.createOscillator()
      osc.type = 'triangle'
      osc.frequency.value = freq
      osc.connect(tone)
      tone.connect(this.drumBus)
      osc.start(at)
      osc.stop(at + shell + 0.02)
      osc.onended = () => tone.disconnect()
    }
  }

  /** Pitched tom: a falling sine skin over a short noise stick attack. The
   * reference's fills run four of these, floor to timbale. */
  playTom(at: number, freq: number, vel: number): void {
    const ctx = this.ctx
    const fall = Math.min(0.5, 26 / freq)
    const amp = ctx.createGain()
    amp.connect(this.drumBus)
    hit(amp, at, vel, fall)
    let first: OscillatorNode | null = null
    for (const [type, mul, level] of [
      ['sine', 1, 1],
      ['triangle', 1.5, 0.22],
    ] as const) {
      const osc = ctx.createOscillator()
      osc.type = type
      osc.frequency.setValueAtTime(freq * mul * 1.9, at)
      decayTo(osc.frequency, freq * mul, at + 0.09)
      const mix = ctx.createGain()
      mix.gain.value = level
      osc.connect(mix)
      mix.connect(amp)
      osc.start(at)
      osc.stop(at + fall + 0.02)
      first ??= osc
    }
    if (first) first.onended = () => amp.disconnect()

    const stick = ctx.createGain()
    const edge = ctx.createBiquadFilter()
    edge.type = 'bandpass'
    edge.frequency.value = 2600
    hit(stick, at, vel * 0.3, 0.016)
    this.source(at, at + 0.03).connect(edge)
    edge.connect(stick)
    stick.connect(this.drumBus)
  }

  /** The claps. Three tight noise slaps a few milliseconds apart, then the
   * room tail - the reason the whole arrangement exists. */
  playClap(at: number, vel: number): void {
    const ctx = this.ctx
    const shape = ctx.createBiquadFilter()
    shape.type = 'bandpass'
    shape.frequency.value = 1080
    shape.Q.value = 0.72
    const edge = ctx.createBiquadFilter()
    edge.type = 'highpass'
    edge.frequency.value = 620
    shape.connect(edge)
    edge.connect(this.drumBus)

    for (const [offset, level, fall] of [
      [0, 0.9, 0.014],
      [0.011, 0.95, 0.014],
      [0.023, 1, 0.016],
    ] as const) {
      const slap = ctx.createGain()
      hit(slap, at + offset, vel * level, fall)
      slap.connect(shape)
      this.source(at + offset, at + offset + fall + 0.01).connect(slap)
    }
    const tail = ctx.createGain()
    hit(tail, at + 0.033, vel * 0.62, 0.17)
    tail.connect(shape)
    this.source(at + 0.033, at + 0.21).connect(tail)
  }

  /** Filtered noise plus inharmonic squares - the analogue hat recipe. */
  playHat(at: number, vel: number, open: boolean): void {
    const ctx = this.ctx
    const fall = open ? 0.3 : 0.055
    const amp = ctx.createGain()
    const bright = ctx.createBiquadFilter()
    bright.type = 'highpass'
    bright.frequency.value = open ? 6800 : 7800
    hit(amp, at, vel, fall)
    bright.connect(amp)
    amp.connect(this.drumBus)
    this.source(at, at + fall + 0.02).connect(bright)

    const metal = ctx.createGain()
    const ring = ctx.createBiquadFilter()
    ring.type = 'bandpass'
    ring.frequency.value = 9200
    ring.Q.value = 1.1
    hit(metal, at, vel * 0.35, fall * 0.8)
    ring.connect(metal)
    metal.connect(this.drumBus)
    let first: OscillatorNode | null = null
    // Closed hats are short enough that half the partials carry the character.
    for (const ratio of open ? HAT_RATIOS : HAT_RATIOS.slice(0, 2)) {
      const osc = ctx.createOscillator()
      osc.type = 'square'
      osc.frequency.value = HAT_BASE * ratio
      osc.connect(ring)
      osc.start(at)
      osc.stop(at + fall + 0.02)
      first ??= osc
    }
    if (first) first.onended = () => metal.disconnect()
  }

  /** Two overlapping noise transients - jingles, not a single hit. */
  playTamb(at: number, vel: number): void {
    const ctx = this.ctx
    const shape = ctx.createBiquadFilter()
    shape.type = 'bandpass'
    shape.frequency.value = 6400
    shape.Q.value = 1.4
    shape.connect(this.drumBus)
    for (const [offset, level, fall] of [
      [0, 1, 0.03],
      [0.006, 0.7, 0.085],
    ] as const) {
      const amp = ctx.createGain()
      hit(amp, at + offset, vel * level, fall)
      amp.connect(shape)
      this.source(at + offset, at + offset + fall + 0.02).connect(amp)
    }
  }

  /** Long noise wash swept down by a closing lowpass. */
  playCrash(at: number, vel: number): void {
    const ctx = this.ctx
    const amp = ctx.createGain()
    const bright = ctx.createBiquadFilter()
    bright.type = 'highpass'
    bright.frequency.value = 3200
    const close = ctx.createBiquadFilter()
    close.type = 'lowpass'
    close.frequency.setValueAtTime(14000, at)
    decayTo(close.frequency, 4200, at + 1.5)
    hit(amp, at, vel, 1.5)
    bright.connect(close)
    close.connect(amp)
    amp.connect(this.drumBus)
    this.source(at, at + 1.6).connect(bright)
  }
}
