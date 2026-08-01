/** Seat interactions: the window armchair, the slipper chair (its ottoman as
 * the foot rest), the three-cushion sofa, and the foot of either bed.
 *
 * Walking near a seat offers "Press E to sit"; E sits, E stands, and on the
 * sofa A/D slide one cushion at a time.  While seated the walker stands down
 * entirely and only the mouse pans.  All camera choreography lives here and is
 * hand-keyed to read as human: turn first, settle the hips, a cushion catch at
 * the bottom, a lean-forward push-up on rising, and a seated breathing sway.
 *
 * Seat geometry is derived from the same layout constants the furniture is
 * built from (src/lib/L.ts, ports of build_scripts/L.py), so the eye comes to
 * rest exactly over each authored seating area. */
import type * as THREE from 'three/webgpu'
import * as L from '../lib/L'
import { EYE, applyPose, type PlayerControls } from './controls'
import { SeatHint } from './hint'

const rad = (d: number): number => (d * Math.PI) / 180
const clamp01 = (v: number): number => (v < 0 ? 0 : v > 1 ? 1 : v)
/** C2 smootherstep: zero velocity and acceleration at both ends. */
const smooth = (v: number): number => {
  const t = clamp01(v)
  return t * t * t * (t * (t * 6 - 15) + 10)
}
/** Shortest signed equivalent of an angle. */
const wrap = (a: number): number => Math.atan2(Math.sin(a), Math.cos(a))

const SIT_T = 1.3
const STAND_T = 1.05
const SCOOT_T = 0.62
/** Eyes settle just short of level, the way a sitter actually rests. */
const SEAT_PITCH = -0.02

interface Spot {
  /** where the eyes rest, straight above the seating area */
  x: number
  y: number
  eyeZ: number
  /** seat facing, in the walker's yaw convention (0 looks +Y) */
  yaw: number
  /** a guaranteed-standable spot to rise onto when the entry spot is far */
  standX: number
  standY: number
  /** unit facing on the floor plane */
  fwdX: number
  fwdY: number
}

interface SeatTarget {
  kind: 'chair' | 'couch' | 'bed'
  /** south-to-north for the sofa; single entry otherwise */
  spots: Spot[]
  radius: number
  /** distance from a player position to this seat's approach zone */
  zoneDist(px: number, py: number): number
  /** which spot an entry from y lands on (sofa: its two halves) */
  entrySpot(py: number): number
}

function chairTarget(
  kind: 'chair' | 'bed',
  cx: number,
  cy: number,
  facing: number,
  fwdOff: number,
  eyeZ: number,
  stand: [number, number],
  radius: number,
  anchor?: [number, number],
): SeatTarget {
  const fx = Math.cos(facing)
  const fy = Math.sin(facing)
  const [ax, ay] = anchor ?? stand
  const spot: Spot = {
    x: cx + fx * fwdOff,
    y: cy + fy * fwdOff,
    eyeZ,
    yaw: wrap(facing - Math.PI / 2),
    standX: stand[0],
    standY: stand[1],
    fwdX: fx,
    fwdY: fy,
  }
  return {
    kind,
    spots: [spot],
    radius,
    zoneDist: (px, py) => Math.hypot(px - ax, py - ay),
    entrySpot: () => 0,
  }
}

function buildTargets(): SeatTarget[] {
  const targets: SeatTarget[] = []

  // --- sofa: three cushions, faces +X down the flat's axis ------------------
  {
    const [cx, cy] = L.SOFA_C
    const aw = 0.185 // arm width, as the sofa is built in scene/living.ts
    const pitch = (L.SOFA_L - 2 * aw) / 3
    // cushion top 0.575, sunk under weight, plus a seated torso
    const eyeZ = 1.245
    // The coffee table leaves only a 0.36 m slot along the sofa's front - too
    // narrow to walk - so each end seat rises onto the open pocket past its
    // own end of the table instead of straight ahead.
    const stands: [number, number][] = [
      [cx + 0.78, cy - pitch - 0.57],
      [cx + 0.78, cy], // unused: the middle seat is only reached by sliding
      [cx + 0.82, cy + pitch + 0.38],
    ]
    const spots: Spot[] = [-1, 0, 1].map((k, i) => ({
      x: cx + 0.1,
      y: cy + k * pitch,
      eyeZ,
      yaw: -Math.PI / 2,
      standX: stands[i][0],
      standY: stands[i][1],
      fwdX: 1,
      fwdY: 0,
    }))
    const y0 = spots[0].y
    const y1 = spots[2].y
    const frontX = cx + 0.9
    targets.push({
      kind: 'couch',
      spots,
      radius: 0.85,
      zoneDist: (px, py) =>
        // never from behind the back rail
        px < cx + 0.5 ? Infinity : Math.hypot(px - frontX, py - Math.max(y0, Math.min(y1, py))),
      entrySpot: (py) => (py >= cy ? 2 : 0),
    })
  }

  // --- armchair at the window, facing south over the coffee table -----------
  targets.push(
    chairTarget('chair', L.CHAIR_ARM_WIN[0], L.CHAIR_ARM_WIN[1], -Math.PI / 2, 0.09, 1.245, [L.CHAIR_ARM_WIN[0], 2.34], 0.8),
  )

  // --- slipper chair, its ottoman parked 0.74 ahead as the foot rest --------
  {
    const a = rad(L.SLIPPER_ROT)
    const [cx, cy] = L.CHAIR_SLIPPER
    // rise forward-left of the ottoman, out onto the open rug
    const sa = a + rad(45)
    targets.push(
      chairTarget(
        'chair',
        cx,
        cy,
        a,
        0.045,
        1.22,
        [cx + Math.cos(sa), cy + Math.sin(sa)],
        0.85,
        [cx + Math.cos(a) * 0.45, cy + Math.sin(a) * 0.45],
      ),
    )
  }

  // --- beds: the seat is the foot end, nearest each bedroom's door ----------
  {
    const footX = L.EXT_E - 0.03 - L.BED_L
    for (const cy of [L.RB_WIN_Y, L.MB_WIN_Y]) {
      // duvet top 0.665 sunk under weight, plus an upright seated torso
      targets.push(chairTarget('bed', footX + 0.07, cy, Math.PI, 0, 1.33, [footX - 0.35, cy], 0.78, [footX - 0.15, cy]))
    }
  }

  return targets
}

const K = (c: string): string => `<span class="k">${c}</span>`
const HINT_SIT = `Press ${K('E')} to sit`
const HINT_STAND = `Press ${K('E')} to stand`
const HINT_LEFT = `Press ${K('A')} to move left`
const HINT_RIGHT = `Press ${K('D')} to move right`
const HINT_BOTH = `${HINT_LEFT}<span class="sep">·</span>${HINT_RIGHT}`

interface Pose {
  x: number
  y: number
  z: number
  yaw: number
  pitch: number
  roll: number
}

type Mode =
  | { k: 'walk' }
  | { k: 'sit'; tgt: SeatTarget; idx: number; t: number; from: Pose; entryX: number; entryY: number }
  | { k: 'seated'; tgt: SeatTarget; idx: number; entryX: number; entryY: number }
  | { k: 'scoot'; tgt: SeatTarget; idx: number; to: number; t: number; entryX: number; entryY: number }
  | { k: 'stand'; t: number; from: Pose; spot: Spot; toX: number; toY: number }

export class SeatingSystem {
  private controls: PlayerControls
  private camera: THREE.PerspectiveCamera
  private hint = new SeatHint()
  private targets = buildTargets()
  private mode: Mode = { k: 'walk' }
  /** runs through seated and scoot states, driving breath and sway */
  private seatedTime = 0
  private last: Pose = { x: 0, y: 0, z: EYE, yaw: 0, pitch: 0, roll: 0 }

  constructor(controls: PlayerControls, camera: THREE.PerspectiveCamera) {
    this.controls = controls
    this.camera = camera
    window.addEventListener('keydown', (e) => this.onKey(e))
  }

  private onKey(e: KeyboardEvent): void {
    if (!this.controls.enabled || e.repeat) return
    const m = this.mode
    if (e.code === 'KeyE') {
      if (m.k === 'walk') this.trySit()
      else if (m.k === 'seated') this.beginStand(m)
    } else if (m.k === 'seated' && m.tgt.kind === 'couch') {
      // A slides towards the sitter's left (north, +Y), D towards the right
      if (e.code === 'KeyA' && m.idx < m.tgt.spots.length - 1) this.beginScoot(m, m.idx + 1)
      else if (e.code === 'KeyD' && m.idx > 0) this.beginScoot(m, m.idx - 1)
    }
  }

  private nearest(px: number, py: number): SeatTarget | null {
    let best: SeatTarget | null = null
    let bd = Infinity
    for (const t of this.targets) {
      const d = t.zoneDist(px, py)
      if (d <= t.radius && d < bd) {
        bd = d
        best = t
      }
    }
    return best
  }

  private trySit(): void {
    const p = this.controls.getPose()
    const tgt = this.nearest(p.x, p.y)
    if (!tgt) return
    const idx = tgt.entrySpot(p.y)
    this.controls.external = true
    this.controls.lookLocked = true
    const c = this.camera.position
    this.mode = {
      k: 'sit',
      tgt,
      idx,
      t: 0,
      from: { x: c.x, y: c.y, z: c.z, yaw: p.yaw, pitch: p.pitch, roll: 0 },
      entryX: p.x,
      entryY: p.y,
    }
    this.hint.hide()
  }

  private beginStand(m: Extract<Mode, { k: 'seated' }>): void {
    const s = m.tgt.spots[m.idx]
    // Rise back onto the spot the sit started from while it is still by this
    // seat; after sliding along the sofa, use the nearest authored pocket.
    let toX: number
    let toY: number
    if (Math.hypot(m.entryX - s.x, m.entryY - s.y) <= 1.25) {
      toX = m.entryX
      toY = m.entryY
    } else if (m.tgt.kind === 'couch') {
      const ends = [m.tgt.spots[0], m.tgt.spots[m.tgt.spots.length - 1]]
      const pick = ends.reduce((a, b) =>
        Math.hypot(a.standX - s.x, a.standY - s.y) <= Math.hypot(b.standX - s.x, b.standY - s.y) ? a : b,
      )
      toX = pick.standX
      toY = pick.standY
    } else {
      toX = s.standX
      toY = s.standY
    }
    this.controls.lookLocked = true
    this.mode = { k: 'stand', t: 0, from: { ...this.last }, spot: s, toX, toY }
    this.hint.hide()
  }

  private beginScoot(m: Extract<Mode, { k: 'seated' }>, to: number): void {
    this.mode = { k: 'scoot', tgt: m.tgt, idx: m.idx, to, t: 0, entryX: m.entryX, entryY: m.entryY }
    this.hint.hide()
  }

  update(dt: number): void {
    dt = Math.min(dt, 0.05)
    const m = this.mode
    if (!this.controls.enabled) {
      // paused: hold the frame exactly as it is
      this.hint.hide()
      return
    }
    if (m.k === 'walk') {
      const p = this.controls.getPose()
      if (this.nearest(p.x, p.y)) this.hint.show(HINT_SIT)
      else this.hint.hide()
      return
    }
    if (m.k === 'sit') {
      m.t += dt
      const u = clamp01(m.t / SIT_T)
      const p = this.sitPose(m, u)
      this.apply(p)
      if (u >= 1) {
        this.controls.setLook(p.yaw, p.pitch)
        this.controls.lookLocked = false
        this.seatedTime = 0
        this.mode = { k: 'seated', tgt: m.tgt, idx: m.idx, entryX: m.entryX, entryY: m.entryY }
      }
      return
    }
    if (m.k === 'seated') {
      this.seatedTime += dt
      const look = this.controls.getPose()
      this.apply(this.seatedPose(m.tgt.spots[m.idx], look.yaw, look.pitch))
      if (m.tgt.kind === 'couch') {
        const last = m.tgt.spots.length - 1
        const sub = m.idx === 0 ? HINT_LEFT : m.idx === last ? HINT_RIGHT : HINT_BOTH
        this.hint.show(HINT_STAND, sub)
      } else {
        this.hint.show(HINT_STAND)
      }
      return
    }
    if (m.k === 'scoot') {
      m.t += dt
      this.seatedTime += dt
      const u = clamp01(m.t / SCOOT_T)
      const look = this.controls.getPose()
      this.apply(this.scootPose(m, u, look.yaw, look.pitch))
      if (u >= 1) this.mode = { k: 'seated', tgt: m.tgt, idx: m.to, entryX: m.entryX, entryY: m.entryY }
      return
    }
    m.t += dt
    const u = clamp01(m.t / STAND_T)
    const p = this.standPose(m, u)
    this.apply(p)
    if (u >= 1) {
      this.controls.place(m.toX, m.toY, p.yaw, p.pitch)
      this.controls.external = false
      this.controls.lookLocked = false
      this.mode = { k: 'walk' }
    }
  }

  private apply(p: Pose): void {
    applyPose(this.camera, p.x, p.y, p.z, p.yaw, p.pitch, p.roll)
    this.last = p
  }

  /** Quadratic bezier through a control point pulled out in front of the
   * seat, so every sit and stand sweeps over the seat's front edge. */
  private static bez(a: number, c: number, b: number, t: number): number {
    const s = 1 - t
    return s * s * a + 2 * s * t * c + t * t * b
  }

  private sitPose(m: Extract<Mode, { k: 'sit' }>, u: number): Pose {
    const s = m.tgt.spots[m.idx]
    const from = m.from
    const pu = smooth(u)
    let x = SeatingSystem.bez(from.x, s.x + s.fwdX * 0.3, s.x, pu)
    let y = SeatingSystem.bez(from.y, s.y + s.fwdY * 0.3, s.y, pu)
    // hips hold walking height while the body turns, then settle
    let z = from.z + (s.eyeZ - from.z) * smooth((u - 0.3) / 0.62)
    if (u > 0.78) z -= 0.026 * Math.sin((Math.PI * (u - 0.78)) / 0.22) // cushion catch
    const yaw = from.yaw + wrap(s.yaw - from.yaw) * smooth((u - 0.04) / 0.66)
    let pitch = from.pitch + (SEAT_PITCH - from.pitch) * smooth((u - 0.15) / 0.75)
    if (u > 0.28 && u < 0.86) pitch -= 0.085 * Math.sin((Math.PI * (u - 0.28)) / 0.58) // glance down at the seat
    const env = Math.sin(Math.PI * u)
    const t = m.t
    x += Math.sin(t * 8.9) * 0.005 * env
    y += Math.sin(t * 11.3 + 2.1) * 0.005 * env
    z += Math.sin(t * 7.1 + 0.6) * 0.004 * env
    const roll = Math.sin(t * 6.3 + 0.9) * 0.01 * env
    return { x, y, z, yaw, pitch, roll }
  }

  private standPose(m: Extract<Mode, { k: 'stand' }>, u: number): Pose {
    const from = m.from
    const s = m.spot
    const pu = smooth(u)
    let x = SeatingSystem.bez(from.x, from.x + s.fwdX * 0.32, m.toX, pu)
    let y = SeatingSystem.bez(from.y, from.y + s.fwdY * 0.32, m.toY, pu)
    let z = from.z + (EYE - from.z) * smooth((u - 0.12) / 0.73)
    if (u < 0.24) z -= 0.018 * Math.sin((Math.PI * u) / 0.24) // weight shifts forward first
    if (u > 0.74) z += 0.01 * Math.sin((Math.PI * (u - 0.74)) / 0.26) // and settles at the top
    let pitch = from.pitch
    if (u < 0.55) pitch -= 0.07 * Math.sin((Math.PI * u) / 0.55)
    const env = Math.sin(Math.PI * u)
    const t = m.t
    x += Math.sin(t * 9.7 + 0.8) * 0.004 * env
    y += Math.sin(t * 12.1 + 1.9) * 0.004 * env
    z += Math.sin(t * 7.7 + 2.6) * 0.004 * env
    const roll = Math.sin(t * 5.9 + 1.4) * 0.008 * env
    return { x, y, z, yaw: from.yaw, pitch, roll }
  }

  private scootPose(m: Extract<Mode, { k: 'scoot' }>, u: number, yaw: number, pitch: number): Pose {
    const a = m.tgt.spots[m.idx]
    const b = m.tgt.spots[m.to]
    const sw = this.breathOffsets(a)
    const lift = Math.sin(Math.PI * u)
    const e = smooth(u)
    // hips lift a little, lean forward, and settle onto the next cushion
    const x = a.x + (b.x - a.x) * e + a.fwdX * 0.035 * lift + sw.dx
    const y = a.y + (b.y - a.y) * e + a.fwdY * 0.035 * lift + sw.dy
    const z = a.eyeZ + (b.eyeZ - a.eyeZ) * e + 0.065 * lift + sw.dz
    const roll = -Math.sign(b.y - a.y) * 0.022 * lift // shoulders tip into the push
    return { x, y, z, yaw, pitch, roll }
  }

  private breathOffsets(s: Spot): { dx: number; dy: number; dz: number } {
    const t = this.seatedTime
    const breath = 0.0035 * Math.sin(t * 1.35) + 0.0011 * Math.sin(t * 0.31 + 1.0)
    const sway = 0.0016 * Math.sin(t * 0.52 + 0.4)
    return { dx: Math.cos(s.yaw) * sway, dy: Math.sin(s.yaw) * sway, dz: breath }
  }

  private seatedPose(s: Spot, yaw: number, pitch: number): Pose {
    const o = this.breathOffsets(s)
    return { x: s.x + o.dx, y: s.y + o.dy, z: s.eyeZ + o.dz, yaw, pitch, roll: 0 }
  }
}
