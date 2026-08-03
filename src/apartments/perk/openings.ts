/** Central Perk joinery from build_openings.py: storefront glazing, entrance
 * doors, interior openings and back-of-house doors, each built in the wall's
 * own frame (u along the wall, v up, w into the thickness).  Closed leaves
 * register their own collision bodies over the wall gaps they fill. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'

class Wallf {
  private ax: number
  private ay: number
  private dx: number
  private dy: number
  private nx: number
  private ny: number
  readonly t: number

  constructor(p0: Vec2, p1: Vec2, t: number, side = 1) {
    const dx = p1[0] - p0[0]
    const dy = p1[1] - p0[1]
    const len = Math.hypot(dx, dy)
    this.ax = p0[0]
    this.ay = p0[1]
    this.dx = dx / len
    this.dy = dy / len
    this.nx = -this.dy * side
    this.ny = this.dx * side
    this.t = t
  }

  P(u: number, v: number, w = 0): Vec3 {
    return [this.ax + this.dx * u + this.nx * w, this.ay + this.dy * u + this.ny * w, v]
  }

  angle(): number {
    return Math.atan2(this.dy, this.dx)
  }

  /** Extrude a (u, v) polygon through the wall's thickness. */
  prism(quad: Vec2[], w0: number, w1: number): MeshData {
    const pts = quad.map(([u, v]) => this.P(u, v, w0))
    const pts2 = quad.map(([u, v]) => this.P(u, v, w1))
    const n = quad.length
    const faces: number[][] = [
      Array.from({ length: n }, (_, i) => n - 1 - i),
      Array.from({ length: n }, (_, i) => n + i),
    ]
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n
      faces.push([i, j, j + n, i + n])
    }
    const md = MeshData.from([...pts, ...pts2], faces)
    mlib.recalcNormals(md)
    return md
  }

  board(u0: number, v0: number, u1: number, v1: number, w0: number, w1: number): MeshData {
    return this.prism(
      [
        [u0, v0],
        [u1, v0],
        [u1, v1],
        [u0, v1],
      ],
      w0,
      w1,
    )
  }

  /** OBB collider covering u0..u1 at depth w0..w1, z0..z1. */
  collide(world: World, u0: number, u1: number, w0: number, w1: number, z0: number, z1: number): void {
    const um = (u0 + u1) / 2
    const wm = (w0 + w1) / 2
    const c = this.P(um, 0, wm)
    world.obb(c[0], c[1], (u1 - u0) / 2, (w1 - w0) / 2, this.angle(), z0, z1)
  }
}

/** The four boards that line a reveal; head and sill run full width. */
function lining(F: Wallf, u0: number, z0: number, u1: number, z1: number, d = 0.03, sill = false): MeshData[] {
  const out: MeshData[] = []
  const w0 = d
  const w1 = F.t - d
  const jz0 = z0 + (sill ? 0.032 : 0)
  const jz1 = z1 - 0.028
  out.push(F.board(u0, jz0, u0 + 0.028, jz1, w0, w1))
  out.push(F.board(u1 - 0.028, jz0, u1, jz1, w0, w1))
  out.push(F.board(u0, jz1, u1, z1, w0, w1))
  if (sill) out.push(F.board(u0, z0, u1, z0 + 0.032, w0, w1))
  return out
}

/** A mitred casing standing proud of the wall face at w. */
function architrave(
  F: Wallf,
  u0: number,
  u1: number,
  z0: number,
  z1: number,
  wide = 0.075,
  proj = 0.022,
  w = 0,
  foot = true,
): MeshData[] {
  const a = u0 - wide
  const b = u1 + wide
  const c = z0 - (foot ? wide : 0)
  const e = z1 + wide
  const out: MeshData[] = []
  const segs: (Vec2[] | null)[] = [
    foot
      ? [
          [a, c],
          [b, c],
          [u1, z0],
          [u0, z0],
        ]
      : null,
    [
      [a, c],
      [u0, z0],
      [u0, z1],
      [a, e],
    ],
    [
      [a, e],
      [u0, z1],
      [u1, z1],
      [b, e],
    ],
    [
      [b, c],
      [b, e],
      [u1, z1],
      [u1, z0],
    ],
  ]
  for (const s of segs) {
    if (!s) continue
    out.push(F.prism(s, w - proj, w))
  }
  return out
}

/** A glazed sash: stiles, rails, glazing bars, one pane per light. */
function sash(
  world: World,
  F: Wallf,
  u0: number,
  u1: number,
  z0: number,
  z1: number,
  cols: number,
  rows: number,
  w: number,
  glassMat: THREE.Material,
  frameMat: THREE.Material,
  rail = 0.052,
  bar = 0.022,
  depth = 0.048,
): void {
  const wf0 = w
  const wf1 = w + depth
  const frame: MeshData[] = []
  frame.push(F.board(u0, z0, u0 + rail, z1, wf0, wf1))
  frame.push(F.board(u1 - rail, z0, u1, z1, wf0, wf1))
  frame.push(F.board(u0 + rail, z0, u1 - rail, z0 + rail, wf0, wf1))
  frame.push(F.board(u0 + rail, z1 - rail, u1 - rail, z1, wf0, wf1))
  const iu0 = u0 + rail
  const iu1 = u1 - rail
  const iz0 = z0 + rail
  const iz1 = z1 - rail
  for (let i = 1; i < cols; i++) {
    const u = iu0 + ((iu1 - iu0) * i) / cols
    frame.push(F.board(u - bar / 2, iz0, u + bar / 2, iz1, wf0 + 0.006, wf1))
  }
  for (let j = 1; j < rows; j++) {
    const z = iz0 + ((iz1 - iz0) * j) / rows
    frame.push(F.board(iu0, z - bar / 2, iu1, z + bar / 2, wf0 + 0.006, wf1))
  }
  world.add(mlib.join(frame), frameMat)
  world.add(F.board(iu0 + 0.004, iz0 + 0.004, iu1 - 0.004, iz1 - 0.004, wf0 + 0.014, wf0 + 0.02), glassMat)
}

interface DoorMats {
  wood: THREE.Material
  glass: THREE.Material
  brass: THREE.Material
}

/** A shop door: big single light over a raised bottom panel, brass pulls. */
function panelDoor(
  world: World,
  F: Wallf,
  u0: number,
  u1: number,
  z0: number,
  z1: number,
  w: number,
  mats: DoorMats,
  glazed = true,
  hingeLeft = true,
  th = 0.045,
): void {
  const st = 0.11
  const br = 0.24
  const lr = 0.09
  const wood: MeshData[] = []
  wood.push(F.board(u0, z0, u0 + st, z1, w, w + th))
  wood.push(F.board(u1 - st, z0, u1, z1, w, w + th))
  wood.push(F.board(u0 + st, z0, u1 - st, z0 + br, w, w + th))
  wood.push(F.board(u0 + st, z0 + br + 0.86, u1 - st, z0 + br + 0.86 + lr, w, w + th))
  wood.push(F.board(u0 + st, z1 - lr, u1 - st, z1, w, w + th))
  wood.push(F.board(u0 + st - 0.012, z0 + 0.05, u1 - st + 0.012, z0 + br + 0.86, w + 0.012, w + th - 0.012))
  if (glazed) {
    world.add(
      F.board(u0 + st - 0.006, z0 + br + 0.86 + lr - 0.006, u1 - st + 0.006, z1 - lr + 0.006, w + 0.016, w + 0.022),
      mats.glass,
    )
  } else {
    // a blank door needs a panel where the light would have been
    wood.push(F.board(u0 + st - 0.012, z0 + br + 0.86 + lr, u1 - st + 0.012, z1 - lr, w + 0.012, w + th - 0.012))
  }
  world.add(mlib.join(wood), mats.wood)
  // handle: a long brass pull on the leading stile, both faces
  const hu = hingeLeft ? u1 - st * 0.5 : u0 + st * 0.5
  const brassParts: MeshData[] = []
  for (const k of [0, 1]) {
    const ww = k === 0 ? w - 0.028 : w + th + 0.028
    const barMd = mlib.tubeAlong([F.P(hu, z0 + 0.86, ww), F.P(hu, z0 + 1.24, ww)], mlib.circle(0.011, 12))
    mlib.smoothShade(barMd, 40)
    brassParts.push(barMd)
    for (const zz of [z0 + 0.86, z0 + 1.24]) {
      const stub = mlib.tubeAlong([F.P(hu, zz, k === 0 ? w : w + th), F.P(hu, zz, ww)], mlib.circle(0.009, 10))
      mlib.smoothShade(stub, 40)
      brassParts.push(stub)
    }
  }
  world.add(mlib.join(brassParts), mats.brass)
  // the closed leaf blocks its opening
  F.collide(world, u0 - 0.02, u1 + 0.02, w - 0.035, w + th + 0.035, 0, z1)
}

export function build(world: World): void {
  const green = M.get('paint_joinery')
  const gl = M.get('glass_window')
  const wd = M.get('wood_dark')
  const brass = M.paint('metal_brass', 'BE9A4A', { rough: 0.24, coat: 0.35 })
  const doorMats: DoorMats = { wood: wd, glass: gl, brass }

  // ---------------------------------------------------------- window bay
  const F = new Wallf([L.BAY_E, L.BAY_S], [L.BAY_E, L.BAY_DIAG_E], L.TW, -1)
  const z0 = L.STEP + L.STORE_SILL
  const z1 = L.STORE_HEAD
  for (const [a, b] of L.BAY_WIN) {
    const u0 = a - L.BAY_S
    const u1 = b - L.BAY_S
    for (const o of lining(F, u0, z0, u1, z1, 0.03, true)) world.add(o, green)
    for (const o of architrave(F, u0, u1, z0, z1, 0.062, 0.02, 0, false)) world.add(o, green)
    const sill = F.board(u0, z0 - 0.055, u1, z0 + 0.032, -0.075, -0.001)
    world.add(sill, green)
    sash(world, F, u0 + 0.03, u1 - 0.03, z0 + 0.03, z1 - 0.03, 2, 1, L.TW * 0.42, gl, green)
  }
  for (const o of lining(F, L.TRAN_U[0], L.TRAN_BOT, L.TRAN_U[1], L.TRAN_TOP)) world.add(o, green)
  sash(world, F, L.TRAN_U[0] + 0.02, L.TRAN_U[1] - 0.02, L.TRAN_BOT + 0.02, L.TRAN_TOP - 0.02, 5, 1, L.TW * 0.42, gl, green)

  // ---------------------------------------------------------- the entrance
  const D = new Wallf(L.DIAG_A, L.DIAG_B, L.TW, 1)
  const [eu0, eu1] = L.ENTRY_U
  for (const o of lining(D, eu0, L.STEP, eu1, L.ENTRY_H)) world.add(o, green)
  for (const o of architrave(D, eu0, eu1, L.STEP, L.ENTRY_H, 0.085, 0.026, 0, false)) world.add(o, green)
  const mid = (eu0 + eu1) * 0.5
  panelDoor(world, D, eu0 + 0.03, mid - 0.005, L.STEP + 0.01, L.ENTRY_H - 0.03, L.TW * 0.5, doorMats, true, true)
  panelDoor(world, D, mid + 0.005, eu1 - 0.03, L.STEP + 0.01, L.ENTRY_H - 0.03, L.TW * 0.5, doorMats, true, false)
  for (const o of lining(D, eu0, L.TRAN_BOT, eu1, L.TRAN_TOP)) world.add(o, green)
  sash(world, D, eu0 + 0.02, eu1 - 0.02, L.TRAN_BOT + 0.02, L.TRAN_TOP - 0.02, 3, 1, L.TW * 0.42, gl, green)
  const [su0, su1] = L.DIAG_WIN
  for (const o of lining(D, su0, L.STEP + L.STORE_SILL, su1, L.STORE_HEAD)) world.add(o, green)
  sash(world, D, su0 + 0.03, su1 - 0.03, L.STEP + L.STORE_SILL + 0.03, L.STORE_HEAD - 0.03, 1, 1, L.TW * 0.42, gl, green)

  // ------------------------------------------- street windows, main room
  const E = new Wallf([L.EX, -L.TW], [L.EX, L.BAY_S], L.TW, -1)
  {
    const u0 = L.TW + L.E_WIN_S[0]
    const u1 = L.TW + L.E_WIN_S[1]
    for (const o of lining(E, u0, L.STORE_SILL, u1, L.STORE_HEAD, 0.03, true)) world.add(o, green)
    for (const o of architrave(E, u0, u1, L.STORE_SILL, L.STORE_HEAD, 0.062, 0.02, 0, false)) world.add(o, green)
    sash(world, E, u0 + 0.03, u1 - 0.03, L.STORE_SILL + 0.03, L.STORE_HEAD - 0.03, 2, 2, L.TW * 0.42, gl, green)
  }
  const E2 = new Wallf([L.EX, L.PIER[1]], [L.EX, L.NY + L.TP], L.TW, -1)
  {
    const u0 = L.E_WIN_N[0] - L.PIER[1]
    const u1 = L.E_WIN_N[1] - L.PIER[1]
    for (const o of lining(E2, u0, L.STORE_SILL, u1, L.STORE_HEAD, 0.03, true)) world.add(o, green)
    for (const o of architrave(E2, u0, u1, L.STORE_SILL, L.STORE_HEAD, 0.062, 0.02, 0, false)) world.add(o, green)
    sash(world, E2, u0 + 0.03, u1 - 0.03, L.STORE_SILL + 0.03, L.STORE_HEAD - 0.03, 2, 2, L.TW * 0.42, gl, green)
  }

  // ------------------------------------ the doorway through to the lobby
  const N = new Wallf([0, L.NY], [L.EX + L.TW, L.NY], L.TP, 1)
  const [la, lb] = L.LOBBY_DR
  for (const o of lining(N, la, 0, lb, L.LOBBY_H)) world.add(o, green)
  for (const o of architrave(N, la, lb, 0, L.LOBBY_H, 0.085, 0.026, 0, false)) world.add(o, green)

  // ---------------------------------------------------------- back of house
  const K = new Wallf([L.KIT_CH[1][0], L.KIT_N], [-L.TW, L.KIT_N], L.TP, -1)
  {
    const a = L.KIT_CH[1][0] - L.KIT_DR[1]
    const b = L.KIT_CH[1][0] - L.KIT_DR[0]
    for (const o of lining(K, a, 0, b, L.DOOR_H)) world.add(o, green)
    for (const o of architrave(K, a, b, 0, L.DOOR_H, 0.07, 0.02, L.TP + 0.02, false)) world.add(o, green)
    panelDoor(world, K, a + 0.03, b - 0.03, 0.012, L.DOOR_H - 0.03, L.TP * 0.5, doorMats, false)
  }

  const KS = new Wallf([L.EX + 0.22, 0], [0, 0], L.TW, 1)
  {
    const a = L.EX + 0.22 - L.KIT_WIN[1]
    const b = L.EX + 0.22 - L.KIT_WIN[0]
    for (const o of lining(KS, a, 1.05, b, 2.3, 0.03, true)) world.add(o, green)
    sash(world, KS, a + 0.03, b - 0.03, 1.08, 2.27, 2, 2, L.TW * 0.42, gl, green)
  }

  // both lavatory doors come off the hallway's north side
  const H = new Wallf([0, L.HALL_N], [L.WC_E, L.HALL_N], L.TP, 1)
  for (const [a, b] of L.WC_DOORS) {
    for (const o of lining(H, a, 0, b, L.DOOR_H)) world.add(o, green)
    for (const o of architrave(H, a, b, 0, L.DOOR_H, 0.07, 0.02, 0, false)) world.add(o, green)
    panelDoor(world, H, a + 0.03, b - 0.03, 0.012, L.DOOR_H - 0.03, L.TP * 0.5, doorMats, false)
  }

  const NW = new Wallf([L.WC_E, L.WC_N], [0, L.WC_N], L.TW, -1)
  for (const [w0, w1] of L.WC_WIN) {
    const a = L.WC_E - w1
    const b = L.WC_E - w0
    for (const o of lining(NW, a, 1.35, b, 2.35, 0.03, true)) world.add(o, green)
    sash(world, NW, a + 0.025, b - 0.025, 1.375, 2.325, 1, 2, L.TW * 0.42, gl, green)
  }
}
