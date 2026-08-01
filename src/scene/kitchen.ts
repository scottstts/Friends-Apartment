/** Monica's kitchen - port of build_scripts/f_kitchen.py: turquoise casework,
 * butcher-block counters, pro range, double sink, retro fridge, open shelving,
 * hanging pot rack, rattan pendant, ceiling dome. */
import type * as THREE from 'three/webgpu'
import * as L from '../lib/L'
import * as mlib from '../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../lib/mesh'
import { PyRandom } from '../lib/rng'
import * as mats from '../mats/mats'
import * as P from './props'
import type { MatSet } from './shell'
import type { World } from './world'

const CTR_H = L.CTR_H
const CTR_D = L.CTR_D
const TOE = L.TOE
const TOP_T = 0.042
const SHELF_BAYS = 4
const SHELF_TIERS = [3, 4, 4, 3]

function rad(d: number): number {
  return (d * Math.PI) / 180
}

// ------------------------------------------------------------------ materials
export function mkMats(): MatSet {
  const M: MatSet = {}
  M.turq = mats.get('paint_turquoise') ?? mats.paint('paint_turquoise', L.TURQ)
  M.turq2 = mats.paint('paint_turq_dark', '2A8E9C', { rough: 0.32, coat: 0.2 })
  M.block = mats.wood('wood_butcher', ['D6B078', 'B98C4E', '8E6430'], {
    ring: 14.0,
    warp: 0.08,
    bump: 0.16,
    rough: [0.2, 0.36],
    axis: 'Y',
  })
  M.block_n = mats.wood('wood_butcher_n', ['D6B078', 'B98C4E', '8E6430'], {
    ring: 14.0,
    warp: 0.08,
    bump: 0.16,
    rough: [0.2, 0.36],
    axis: 'X',
  })
  M.ovenglass = mats.paint('oven_glass', '17161A', { rough: 0.1, coat: 0.85 })
  M.steel = mats.metal('metal_range', 'A28C6C', { rough: 0.42, bump: 0.02, brush: [1, 40, 1] })
  M.steel_d = mats.metal('metal_range_dark', '35312B', { rough: 0.44, bump: 0.08 })
  M.chrome = mats.get('metal_chrome') ?? mats.metal('metal_chrome', 'D8DCE0', { rough: 0.1 })
  M.chrome_s = mats.metal('metal_chrome_satin', 'DEE2E5', { rough: 0.25, bump: 0.02 })
  M.sink = mats.metal('metal_sink', 'C4C8CB', { rough: 0.31, bump: 0.03, brush: [1, 30, 1] })
  M.castiron = mats.paint('cast_iron', '1B1A19', { rough: 0.55, bump: 0.14, noise: 260 })
  M.enamel = mats.paint('enamel_fridge', 'EFEDE2', { rough: 0.13, coat: 0.55, variation: 0.012 })
  M.celadon = mats.paint('paint_celadon', 'C4D49A', { rough: 0.32, coat: 0.18 })
  M.copper = mats.metal('metal_copper', 'B87333', { rough: 0.33, bump: 0.06 })
  M.tin = mats.metal('metal_tinned', 'BFAD8E', { rough: 0.5, bump: 0.02, scale: 620.0 })
  M.panhandle = mats.metal('metal_panhandle', 'A9A69F', { rough: 0.31, bump: 0.04, brush: [1, 1, 26] })
  M.perf = mats.perforated('metal_perf', { hexcol: 'A7ACB0', rough: 0.34, around: 48, rows: 12, hole: 0.2, vmin: 0.4 })
  M.iron = mats.metal('metal_wrought', '35322E', { rough: 0.48, bump: 0.16 })
  M.glass = mats.get('glass_clear') ?? mats.pane('glass_clear')
  M.towel_r = mats.gingham('towel_rust', { band: 0.0055, light: 'E9DDCB', dark: 'B4502C', rough: 0.86, sheen: 0.35, weave: 1400.0, bump: 0.28 })
  M.towel_b = mats.gingham('towel_navy', { band: 0.0055, light: 'E4E6E4', dark: '2F4C7A', rough: 0.86, sheen: 0.35, weave: 1400.0, bump: 0.28 })
  return M
}

// ------------------------------------------------------------------- casework
function slabDoor(w: number, h: number, t = 0.019, rail = 0.062): MeshData {
  const fr = mlib.panelWithHoles(w, h, t, [[rail, rail, w - rail, h - rail]])
  mlib.translate(fr, [-w / 2, 0, 0])
  const pan = mlib.box(-w / 2 + rail - 0.006, t * 0.42, rail - 0.006, w / 2 - rail + 0.006, t * 0.42 + 0.01, h - rail + 0.006)
  const ob = mlib.join([fr, pan])
  mlib.bevel(ob, 0.0025, 2)
  return ob
}

function barPull(ln = 0.135): MeshData {
  const parts: MeshData[] = []
  parts.push(
    mlib.revolve(
      [
        [0.0, 0.0],
        [0.0065, 0.0],
        [0.0065, ln],
        [0.0, ln],
      ],
      14,
    ),
  )
  for (const z of [0.012, ln - 0.012]) {
    const p = mlib.revolve(
      [
        [0.0, 0.0],
        [0.0055, 0.0],
        [0.0055, 0.026],
        [0.0, 0.026],
      ],
      12,
    )
    mlib.rotX(p, Math.PI / 2)
    mlib.translate(p, [0, 0, z])
    parts.push(p)
  }
  const ob = mlib.join(parts)
  mlib.translate(ob, [0, 0, -ln / 2])
  mlib.smoothShade(ob, 34)
  return ob
}

function baseRun(
  w: World,
  p0: Vec2,
  p1: Vec2,
  M: MatSet,
  doors = 2,
  drawers = 0,
  drH = 0.16,
  depth = CTR_D,
  top = true,
  topMat?: THREE.Material,
): void {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const ln = Math.hypot(dx, dy)
  const ux = dx / ln
  const uy = dy / ln
  const nx = uy
  const ny = -ux // into the room
  const M4 = [
    [ux, nx, 0, p0[0]],
    [uy, ny, 0, p0[1]],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ]
  const placed: [MeshData, THREE.Material][] = []
  const car = mlib.box(0.0, TOE, TOE, ln, depth - 0.021, CTR_H - TOP_T)
  placed.push([car, M.turq])
  const kick = mlib.box(0.0, TOE + 0.055, 0.0, ln, depth - 0.03, TOE)
  placed.push([kick, M.turq2])
  // fronts
  const z0 = TOE
  const fh = CTR_H - TOP_T - TOE
  const rows: [string, number][] = []
  for (let i = 0; i < drawers; i++) rows.push(['dr', drH])
  rows.push(['dr_or_door', fh - drawers * drH])
  let zz = z0
  for (const [kind, hh] of rows) {
    const n = kind !== 'dr' ? doors : 1
    for (let i = 0; i < n; i++) {
      const dw = (ln - 0.012 * (n + 1)) / n
      const cx = 0.006 + i * (dw + 0.012) + dw / 2
      const d = slabDoor(dw, hh - 0.01, 0.019, kind !== 'dr' ? 0.055 : 0.038)
      mlib.translate(d, [cx, depth - 0.019, zz + 0.005])
      placed.push([d, M.turq])
      const pl = barPull(kind === 'dr' ? 0.125 : 0.115)
      if (kind === 'dr') {
        mlib.rotY(pl, Math.PI / 2)
        mlib.translate(pl, [cx, depth + 0.028, zz + hh * 0.55])
      } else {
        mlib.translate(pl, [cx + dw / 2 - 0.058, depth + 0.028, zz + hh - 0.14])
      }
      placed.push([pl, M.chrome])
    }
    zz += hh
  }
  for (const [ob, mm] of placed) {
    mlib.transform4(ob, M4)
    mlib.recalcNormals(ob)
    w.add(ob, mm)
  }
  if (top) {
    const tp = mlib.box(-0.002, -0.012, CTR_H - TOP_T, ln + 0.002, depth + 0.022, CTR_H)
    mlib.bevel(tp, 0.005, 3)
    mlib.transform4(tp, M4)
    mlib.recalcNormals(tp)
    w.add(tp, topMat ?? M.block)
  }
  // counter footprint collider
  const c0: Vec2 = [p0[0] + (nx * depth) / 2 + (ux * ln) / 2, p0[1] + (ny * depth) / 2 + (uy * ln) / 2]
  w.obb(c0[0], c0[1], ln / 2, depth / 2, Math.atan2(uy, ux))
}

// --------------------------------------------------------------- open shelving
function shelfUnit(
  w: World,
  p0: Vec2,
  p1: Vec2,
  z0: number,
  z1: number,
  depth: number,
  tiers: number,
  M: MatSet,
  bays = 0,
  stagger: number[] = [],
): void {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const ln = Math.hypot(dx, dy)
  const ux = dx / ln
  const uy = dy / ln
  const nx = uy
  const ny = -ux
  const t = 0.024
  const parts: MeshData[] = []
  parts.push(mlib.box(0.0, 0.0, z0, t, depth, z1))
  parts.push(mlib.box(ln - t, 0.0, z0, ln, depth, z1))
  parts.push(mlib.box(0.0, 0.0, z1 - t * 1.4, ln, depth, z1))
  parts.push(mlib.box(0.0, 0.0, z0, ln, depth, z0 + t * 1.4))
  const inner = z1 - t * 1.4 - (z0 + t * 1.4)
  const zb = z0 + t * 1.4
  const zt = z1 - t * 1.4
  if (bays > 1) {
    const edges = [t, ...Array.from({ length: bays - 1 }, (_, i) => (ln * (i + 1)) / bays), ln - t]
    for (let i = 1; i < bays; i++) {
      const xx = edges[i]
      parts.push(mlib.box(xx - t / 2, 0.0, zb, xx + t / 2, depth, zt))
    }
    for (let k = 0; k < bays; k++) {
      const nt = stagger.length ? stagger[k % stagger.length] : tiers
      const a = edges[k] + (k ? t / 2 : 0)
      const b2 = edges[k + 1] - (k < bays - 1 ? t / 2 : 0)
      for (let i = 1; i < nt; i++) {
        const zz = zb + (inner * i) / nt
        parts.push(mlib.box(a, 0.0, zz - t / 2, b2, depth, zz + t / 2))
      }
    }
  } else {
    for (let i = 1; i < tiers; i++) {
      const zz = zb + (inner * i) / tiers
      parts.push(mlib.box(t, 0.0, zz - t / 2, ln - t, depth, zz + t / 2))
    }
  }
  const M4 = [
    [ux, nx, 0, p0[0]],
    [uy, ny, 0, p0[1]],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ]
  const ob = mlib.join(parts)
  mlib.transform4(ob, M4)
  mlib.recalcNormals(ob)
  mlib.bevel(ob, 0.002, 2)
  w.add(ob, M.turq)
}

function wedgeShelf(w: World, p0: Vec2, p1: Vec2, z: number, depth: number, M: MatSet): void {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const ln = Math.hypot(dx, dy)
  const ux = dx / ln
  const uy = dy / ln
  const nx = uy
  const ny = -ux
  const t = 0.024
  const parts: MeshData[] = [
    mlib.box(0.0, 0.0, z, ln, depth, z + t),
    mlib.box(0.0, depth - t, z, ln, depth, z + 0.055),
  ]
  const vs: Vec3[] = [
    [0.0, 0.0, z + t],
    [0.0, depth, z + t],
    [0.0, 0.0, z + 0.42],
    [t, 0.0, z + t],
    [t, depth, z + t],
    [t, 0.0, z + 0.42],
  ]
  const fs = [
    [0, 1, 2],
    [5, 4, 3],
    [0, 3, 4, 1],
    [1, 4, 5, 2],
    [2, 5, 3, 0],
  ]
  const tri = mlib.meshObj(vs, fs)
  mlib.recalcNormals(tri)
  parts.push(tri)
  const M4 = [
    [ux, nx, 0, p0[0]],
    [uy, ny, 0, p0[1]],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ]
  const ob = mlib.join(parts)
  mlib.transform4(ob, M4)
  mlib.recalcNormals(ob)
  mlib.bevel(ob, 0.002, 2)
  w.add(ob, M.turq)
}

// ------------------------------------------------------------------ peninsula
function peninsula(w: World, M: MatSet): void {
  const x0 = 0.0
  const x1 = 0.6
  const [y0, y1] = L.KIT_PEN
  const t = 0.024
  const parts: MeshData[] = []
  parts.push(mlib.box(x1 - t, y0, 0.0, x1, y1, CTR_H - 0.03))
  parts.push(mlib.box(x0, y0, 0.0, x0 + t, y1, CTR_H - 0.03))
  parts.push(mlib.box(x0, y1 - t, 0.0, x1, y1, CTR_H - 0.03))
  for (const zz of [0.2, 0.44, 0.68]) {
    parts.push(mlib.box(x0 + t, y0, zz, x1 - t, y1 - t, zz + t))
  }
  const top = mlib.box(x0 - 0.018, y0 - 0.026, CTR_H - 0.03, x1 + 0.03, y1 + 0.018, CTR_H)
  mlib.bevel(top, 0.006, 2)
  parts.push(top)
  const ob = mlib.join(parts)
  mlib.bevel(ob, 0.002, 2)
  w.add(ob, M.turq, { collide: true })
  // wooden mail pocket on the east face
  const back = mlib.prismXZ(
    [
      [0.0, 0.0],
      [0.196, 0.0],
      [0.196, 0.222],
      [0.176, 0.268],
      [0.14, 0.294],
      [0.098, 0.302],
      [0.056, 0.294],
      [0.02, 0.268],
      [0.0, 0.222],
    ],
    0.0,
    0.015,
  )
  const dip: Vec2[] = [
    [0.01, 0.0],
    [0.186, 0.0],
    [0.186, 0.14],
    [0.17, 0.128],
    [0.132, 0.116],
    [0.098, 0.113],
    [0.064, 0.116],
    [0.026, 0.128],
    [0.01, 0.14],
  ]
  const front = mlib.prismXZ(dip, 0.0, 0.013)
  mlib.translate(front, [0, 0.082, 0])
  const mbase = mlib.box(0.01, 0.0, -0.002, 0.186, 0.085, 0.011)
  const pocket = mlib.join([back, front, mbase])
  mlib.bevel(pocket, 0.002, 2)
  mlib.rotateZ(pocket, -Math.PI / 2)
  mlib.translate(pocket, [x1 + 0.001, (y0 + y1) / 2 + 0.098, 0.475])
  w.add(
    pocket,
    mats.wood('wood_plaque', ['C39A62', 'A57B44', '85602F'], { ring: 44, warp: 0.7, bump: 0.3, axis: 'Y', grainRelief: 0.4 }),
  )
}

// ---------------------------------------------------------------------- range
function proRange(w: World, M: MatSet): void {
  const [y0, y1] = L.KIT_STOVE
  const width = y1 - y0
  const x0 = 0.0
  const x1 = CTR_D - 0.01
  const placed: [MeshData, THREE.Material][] = []
  const body = mlib.box(x0, y0, 0.0, x1 - 0.02, y1, CTR_H - 0.015)
  mlib.bevel(body, 0.006, 2)
  placed.push([body, M.steel])
  const fas = mlib.box(x1 - 0.052, y0, CTR_H - 0.19, x1, y1, CTR_H - 0.015)
  mlib.bevel(fas, 0.004, 2)
  placed.push([fas, M.steel])
  const ct = mlib.box(x0 + 0.014, y0 + 0.01, CTR_H - 0.03, x1 - 0.052, y1 - 0.01, CTR_H - 0.004)
  placed.push([ct, M.steel_d])
  const GX = [x0 + 0.175, x0 + 0.43]
  const GY = [0, 1, 2].map((j) => y0 + 0.145 + (j * (width - 0.29)) / 2.0)
  for (const gx of GX) {
    for (const gy of GY) {
      const bu = mlib.revolve(
        [
          [0.0, 0.0],
          [0.045, 0.004],
          [0.047, 0.013],
          [0.028, 0.02],
          [0.013, 0.03],
          [0.0, 0.03],
        ],
        20,
      )
      mlib.translate(bu, [gx, gy, CTR_H - 0.028])
      mlib.smoothShade(bu, 40)
      placed.push([bu, M.castiron])
    }
  }
  // continuous cast-iron grates
  for (const gx of GX) {
    const gw = (width - 0.1) / 3.0
    const gd = 0.245
    for (const gy of GY) {
      const gp: MeshData[] = []
      for (const s of [-1, 1]) {
        gp.push(mlib.box(gx - gd / 2, gy + (s * gw) / 2 - 0.0055, 0.0, gx + gd / 2, gy + (s * gw) / 2 + 0.0055, 0.023))
      }
      for (let i = 0; i < 2; i++) {
        const yy = gy - gw / 2 + ((i + 1) * gw) / 3.0
        gp.push(mlib.box(gx - gd / 2, yy - 0.0045, 0.009, gx + gd / 2, yy + 0.0045, 0.023))
      }
      for (const s of [-1, 1]) {
        gp.push(mlib.box(gx + (s * gd) / 2 - 0.0055, gy - gw / 2, 0.0, gx + (s * gd) / 2 + 0.0055, gy + gw / 2, 0.023))
      }
      const gr = mlib.join(gp)
      mlib.translate(gr, [0, 0, CTR_H - 0.004])
      placed.push([gr, M.castiron])
    }
  }
  // back riser with its slotted vent
  const riser = mlib.box(x0, y0, CTR_H - 0.03, x0 + 0.052, y1, CTR_H + 0.118)
  mlib.bevel(riser, 0.005, 2)
  placed.push([riser, M.steel])
  for (let i = 0; i < 9; i++) {
    const sy = y0 + 0.075 + (i * (width - 0.15)) / 8.0
    placed.push([mlib.box(x0 + 0.048, sy - 0.014, CTR_H + 0.03, x0 + 0.056, sy + 0.014, CTR_H + 0.092), M.steel_d])
  }
  // --- oven door ----------------------------------------------------------
  const DZ0 = 0.152
  const DZ1 = CTR_H - 0.196
  const od = mlib.panelWithHoles(width - 0.03, DZ1 - DZ0, 0.026, [[0.072, 0.068, width - 0.102, DZ1 - DZ0 - 0.175]])
  mlib.transform4(od, [
    [0, 1, 0, x1 - 0.03],
    [1, 0, 0, y0 + 0.015],
    [0, 0, 1, DZ0],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(od)
  mlib.bevel(od, 0.004, 2)
  placed.push([od, M.steel])
  placed.push([mlib.box(x1 - 0.024, y0 + 0.087, DZ0 + 0.068, x1 - 0.014, y1 - 0.087, DZ1 - 0.107), M.ovenglass])
  // full-width tubular handle on two heavy standoffs
  const HZ = DZ1 - 0.052
  const tb = mlib.revolve(
    [
      [0.0, 0.0],
      [0.0115, 0.0],
      [0.0115, width - 0.086],
      [0.0, width - 0.086],
    ],
    16,
  )
  mlib.rotX(tb, -Math.PI / 2)
  mlib.translate(tb, [x1 + 0.042, y0 + 0.043, HZ])
  mlib.smoothShade(tb, 34)
  placed.push([tb, M.chrome_s])
  for (const yy of [y0 + 0.043, y1 - 0.043]) {
    const st = mlib.revolve(
      [
        [0.0, 0.0],
        [0.016, 0.0],
        [0.016, 0.03],
        [0.011, 0.042],
        [0.0, 0.042],
      ],
      14,
    )
    mlib.rotY(st, Math.PI / 2)
    mlib.translate(st, [x1 - 0.002, yy, HZ])
    mlib.smoothShade(st, 36)
    placed.push([st, M.chrome_s])
  }
  // five chunky chrome knobs with a dark centre boss
  for (let j = 0; j < 5; j++) {
    const ky = y0 + 0.092 + (j * (width - 0.184)) / 4.0
    const kb = mlib.revolve(
      [
        [0.0, 0.0],
        [0.017, 0.0],
        [0.017, 0.008],
        [0.031, 0.013],
        [0.032, 0.024],
        [0.029, 0.028],
        [0.0, 0.028],
      ],
      24,
    )
    mlib.rotY(kb, Math.PI / 2)
    mlib.translate(kb, [x1 + 0.001, ky, CTR_H - 0.1])
    mlib.smoothShade(kb, 32)
    placed.push([kb, M.chrome_s])
    placed.push([mlib.box(x1 + 0.028, ky - 0.0022, CTR_H - 0.094, x1 + 0.03, ky + 0.0022, CTR_H - 0.076), M.castiron])
  }
  // lower drawer
  const dw = mlib.box(x1 - 0.028, y0 + 0.015, 0.022, x1 - 0.004, y1 - 0.015, DZ0 - 0.012)
  mlib.bevel(dw, 0.004, 2)
  placed.push([dw, M.steel])
  for (const [ob, mm] of placed) w.add(ob, mm)
  // towels thrown over the door handle
  const towels: [number, THREE.Material][] = [
    [y0 + 0.255, M.towel_r],
    [y0 + 0.495, M.towel_b],
  ]
  towels.forEach(([yy, mm], k) => {
    const tw = towel(k * 7 + 3)
    mlib.rotateZ(tw, Math.PI / 2)
    mlib.translate(tw, [x1 + 0.042, yy, HZ])
    w.add(tw, mm)
  })
  w.box2(x0, y0, x1 + 0.04, y1)
}

function towel(seed = 0, w = 0.235, drop = 0.345, back = 0.215, r = 0.014): MeshData {
  const rng = new PyRandom(seed)
  const ph = rng.uniform(0.0, Math.PI * 2)
  const nu = 17
  const tail = 14
  const rings: Vec3[][] = []
  for (let k = 0; k < nu; k++) {
    const s = k / (nu - 1.0)
    const xx = (s - 0.5) * w
    const sw = 0.85 + 0.3 * Math.sin(s * 5.3 + ph)
    const df = drop * (1.0 + 0.055 * Math.sin(s * 4.1 + ph * 1.7))
    const db = back * (1.0 + 0.08 * Math.sin(s * 3.3 + ph))
    const prof: Vec2[] = []
    for (let i = tail; i > 0; i--) {
      const t = i / tail
      prof.push([-r - 0.018 * sw * Math.sin(t * 2.3) - 0.03 * t ** 3, -df * t])
    }
    for (let i = 0; i < 13; i++) {
      const a = (Math.PI * i) / 12.0
      prof.push([-r * Math.cos(a), r * Math.sin(a)])
    }
    for (let i = 1; i <= tail; i++) {
      const t = i / tail
      prof.push([r + 0.011 * sw * Math.sin(t * 2.6), -db * t])
    }
    rings.push(prof.map(([y, z]) => [xx, y, z] as Vec3))
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.0038)
  mlib.smoothShade(ob, 50)
  return ob
}

// ----------------------------------------------------------------------- sink
function doubleSink(w: World, M: MatSet): void {
  const { dir, len: cl } = L.chamferDir()
  const [dxc, dyc] = dir
  const cen = L.chamferPt(cl * 0.5, CTR_D * 0.52)
  const parts: MeshData[] = []
  const HX = 0.1725
  const HY = 0.1875
  const GAP = 0.0155
  const rim: [number, number, number, number][] = [
    [-0.39, -0.22, 0.39, -HY],
    [-0.39, HY, 0.39, 0.22],
    [-0.39, -HY, -0.188 - HX, HY],
    [0.188 + HX, -HY, 0.39, HY],
    [-GAP, -HY, GAP, HY],
  ]
  for (const a of rim) {
    const o = mlib.box(a[0], a[1], CTR_H - 0.004, a[2], a[3], CTR_H + 0.004)
    mlib.bevel(o, 0.003, 2)
    parts.push(o)
  }
  for (const sx of [-1, 1]) {
    const r = mlib.roundedRect(0.345, 0.375, 0.04, 4)
    const lv: [number, number][] = [
      [0.0, 1.0],
      [-0.03, 0.985],
      [-0.14, 0.955],
      [-0.175, 0.9],
    ]
    const rings: Vec3[][] = lv.map(([dz, s]) => r.map(([x, y]) => [x * s + sx * 0.188, y * s, CTR_H + dz] as Vec3))
    rings.push(r.map(([x, y]) => [x * 0.86 + sx * 0.188, y * 0.86, CTR_H - 0.178] as Vec3))
    const bw = mlib.loft(rings, { closeV: true, capEnd: true })
    parts.push(bw)
  }
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 32)
  const ang = Math.atan2(dyc, dxc)
  mlib.rotateZ(ob, ang)
  mlib.translate(ob, [cen[0], cen[1], 0.0])
  w.add(ob, M.sink)
  // gooseneck faucet
  const base = mlib.revolve(
    [
      [0.0, 0.0],
      [0.03, 0.0],
      [0.03, 0.03],
      [0.02, 0.045],
      [0.019, 0.15],
    ],
    20,
  )
  const path: Vec3[] = [[0, 0, 0.15]]
  for (let i = 1; i <= 12; i++) {
    const t = i / 12.0
    const a = Math.PI * t
    path.push([0.085 * (1 - Math.cos(a)), 0, 0.15 + 0.115 * Math.sin(a)])
  }
  const neck = mlib.tubeAlong(path, mlib.circle(0.0165, 12))
  const lever = mlib.revolve(
    [
      [0.0, 0.0],
      [0.011, 0.0],
      [0.011, 0.075],
      [0.0, 0.08],
    ],
    12,
  )
  mlib.rotY(lever, rad(-58))
  mlib.translate(lever, [-0.028, 0.0, 0.118])
  const fa = mlib.join([base, neck, lever])
  mlib.smoothShade(fa, 34)
  const fc = L.chamferPt(cl * 0.5, 0.16)
  mlib.rotateZ(fa, ang)
  mlib.translate(fa, [fc[0], fc[1], CTR_H])
  w.add(fa, M.chrome)
}

// ---------------------------------------------------------------------- fridge
function fridge(w: World, M: MatSet): void {
  const [x0, x1] = L.FRIDGE_X
  const d = 0.7
  const y1 = L.NY - 0.012
  const y0 = y1 - d
  const width = x1 - x0
  const placed: [MeshData, THREE.Material][] = []
  const prof = mlib.roundedRect(width, d, 0.055, 5)
  const levels: [number, number, number][] = [
    [0.1, 0.965, 0.99],
    [0.16, 1.0, 1.0],
    [1.6, 1.0, 1.0],
    [1.7, 0.985, 0.992],
    [1.735, 0.94, 0.96],
  ]
  const rings: Vec3[][] = levels.map(([dz, s, sy]) => prof.map(([x, y]) => [x * s, y * sy, dz] as Vec3))
  const body = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(body, 34)
  placed.push([body, M.enamel])
  placed.push([mlib.prism(mlib.roundedRect(width - 0.03, d - 0.03, 0.03, 3), 0.0, 0.1), M.steel_d])
  placed.push([mlib.box(-width / 2 - 0.001, -d / 2 - 0.004, 1.26, width / 2 + 0.001, -d / 2 + 0.004, 1.272), M.steel_d])
  const hb = mlib.prism(mlib.roundedRect(0.048, 0.62, 0.02, 4), 0.0, 0.012)
  mlib.rotX(hb, -Math.PI / 2)
  mlib.translate(hb, [width / 2 - 0.085, -d / 2 - 0.004, 0.92])
  placed.push([hb, M.chrome_s])
  const hl = mlib.revolve(
    [
      [0.0, 0.0],
      [0.013, 0.0],
      [0.013, 0.4],
      [0.0, 0.4],
    ],
    14,
  )
  mlib.translate(hl, [width / 2 - 0.085, -d / 2 - 0.038, 0.72])
  mlib.smoothShade(hl, 34)
  placed.push([hl, M.chrome_s])
  for (const zz of [0.72, 1.12]) {
    const st = mlib.revolve(
      [
        [0.0, 0.0],
        [0.008, 0.0],
        [0.008, 0.036],
        [0.0, 0.036],
      ],
      10,
    )
    mlib.rotX(st, -Math.PI / 2)
    mlib.translate(st, [width / 2 - 0.085, -d / 2 - 0.038, zz])
    placed.push([st, M.chrome_s])
  }
  const hf = mlib.prism(mlib.roundedRect(0.1, 0.036, 0.014, 3), 0.0, 0.03)
  mlib.rotX(hf, -Math.PI / 2)
  mlib.translate(hf, [width / 2 - 0.085, -d / 2 - 0.004, 1.4])
  placed.push([hf, M.chrome_s])
  const bg = mlib.prism(mlib.roundedRect(0.09, 0.024, 0.01, 3), 0.0, 0.006)
  mlib.rotX(bg, -Math.PI / 2)
  mlib.translate(bg, [0.0, -d / 2 - 0.002, 1.52])
  placed.push([bg, M.chrome_s])
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [(x0 + x1) / 2, (y0 + y1) / 2, 0.0])
    w.add(ob, mm)
  }
  w.box2(x0 - 0.02, y0 - 0.05, x1 + 0.02, y1)
}

// -------------------------------------------------------------- hanging things
function saucepan(rr: number, hh: number, hl: number, M: MatSet, lined: boolean): [P.Placed[], Vec3] {
  const parts: P.Placed[] = []
  const wall = 0.0032
  const prf: Vec2[] = [
    [0.0, 0.0],
    [rr * 0.9, 0.0],
    [rr, 0.017],
    [rr, hh],
    [rr - wall, hh],
    [rr - wall, 0.017],
    [rr * 0.9 - wall, 0.0045],
    [0.0, 0.0045],
  ]
  const body = mlib.revolve(prf, 44)
  mlib.smoothShade(body, 32)
  parts.push({ md: body, mat: M.copper })
  if (lined) {
    const lin = mlib.revolve(
      [
        [0.0, 0.0052],
        [rr * 0.86, 0.0052],
        [rr - wall - 0.0008, 0.02],
        [rr - wall - 0.0008, hh - 0.0015],
      ],
      44,
      { capStart: false, capEnd: false },
    )
    mlib.smoothShade(lin, 42)
    parts.push({ md: lin, mat: M.tin })
  }
  // --- handle: a flat strap leaving the rim steeply and flattening off
  const hz = hh * 0.7
  const N = 12
  const b0 = rad(46.0)
  const b1 = rad(21.0)
  const step = hl / N
  const path: Vec3[] = [[rr - 0.004, 0.0, hz]]
  for (let i = 0; i < N; i++) {
    const a = b0 + (b1 - b0) * ((i + 0.5) / N)
    const [x, , z] = path[path.length - 1]
    path.push([x + step * Math.cos(a), 0.0, z + step * Math.sin(a)])
  }
  const sec = mlib.roundedRect(1.0, 1.0, 0.34, 3)
  const rings: Vec3[][] = []
  for (let i = 0; i <= N; i++) {
    const t = i / N
    const wdt = t < 0.2 ? 0.036 - 0.013 * (t / 0.2) ** 0.6 : 0.023 - (0.004 * (t - 0.2)) / 0.8
    const th = 0.005 - 0.0019 * t
    const p = path[i]
    const nx = path[Math.min(i + 1, N)]
    const pv = path[Math.max(i - 1, 0)]
    let tg: Vec3 = [nx[0] - pv[0], nx[1] - pv[1], nx[2] - pv[2]]
    const tl = Math.hypot(...tg) || 1
    tg = [tg[0] / tl, tg[1] / tl, tg[2] / tl]
    const nrm: Vec3 = [-tg[2], 0.0, tg[0]]
    rings.push(
      sec.map(([u, v]) => [p[0] + 0 * u + nrm[0] * (v * th), p[1] + 1.0 * (u * wdt), p[2] + nrm[2] * (v * th)] as Vec3),
    )
  }
  const hd = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(hd, 46)
  parts.push({ md: hd, mat: M.panhandle })
  return [parts, path[N]]
}

function colander(rr: number, M: MatSet): [P.Placed[], Vec3] {
  const parts: P.Placed[] = []
  const NR = 26
  const prf: Vec2[] = [[0.0, 0.0]]
  for (let i = 1; i <= NR; i++) {
    const a = (Math.PI * 0.53 * i) / NR
    prf.push([rr * Math.sin(a), rr * 0.8 * (1.0 - Math.cos(a))])
  }
  const bowlMd = mlib.revolve(prf, 48, { capStart: false, capEnd: false })
  const cz0 = rr * 0.8
  const top = rr * 0.8 * (1.0 - Math.cos(Math.PI * 0.53))
  bowlMd.colors = bowlMd.verts.map((co) => {
    const g = Math.hypot(co[0], co[1])
    const psi = Math.atan2(g, cz0 - co[2]) / (Math.PI * 0.53)
    if (g < 1e-7) return [1.0, 0.5, psi] as Vec3
    return [(co[0] / g) * 0.5 + 0.5, (co[1] / g) * 0.5 + 0.5, psi] as Vec3
  })
  bowlMd.colorName = 'surfq'
  mlib.smoothShade(bowlMd, 55)
  parts.push({ md: bowlMd, mat: M.perf })
  const rim = mlib.tubeAlong(
    Array.from({ length: 48 }, (_, i) => {
      const a = (i * Math.PI * 2) / 48
      return [rr * Math.sin(Math.PI * 0.53) * Math.cos(a), rr * Math.sin(Math.PI * 0.53) * Math.sin(a), top] as Vec3
    }),
    mlib.circle(0.0032, 8),
    { closePath: true },
  )
  mlib.smoothShade(rim, 40)
  parts.push({ md: rim, mat: M.panhandle })
  const rw = rr * Math.sin(Math.PI * 0.53)
  let eye: Vec3 = [0, 0, 0]
  for (const s of [1, -1]) {
    const pts: Vec3[] = []
    for (let i = 0; i < 13; i++) {
      const t = i / 12.0
      const ang = Math.PI * t
      pts.push([s * (rw - 0.004 + 0.03 * Math.sin(ang)), 0.0, top + 0.052 * Math.sin(ang) - 0.004 * Math.cos(ang)])
    }
    const lp = mlib.tubeAlong(pts, mlib.roundedRect(0.0075, 0.0032, 0.0014, 2), { up: [0, 1, 0] })
    mlib.smoothShade(lp, 40)
    parts.push({ md: lp, mat: M.panhandle })
    if (s > 0) eye = [s * (rw - 0.004 + 0.03), 0.0, top + 0.052]
  }
  return [parts, eye]
}

function sHook(hoopHw = 0.015, drop = 0.062): [MeshData, Vec3] {
  const r1 = 0.0088
  const r2 = 0.0105
  const c1: Vec2 = [0.0, hoopHw - r1 * 0.3]
  const c2: Vec2 = [0.0, c1[1] - drop]
  const pts: Vec3[] = []
  for (let k = 0; k < 15; k++) {
    const a = rad(205.0 - (250.0 * k) / 14.0)
    pts.push([c1[0] + r1 * Math.cos(a), 0.0, c1[1] + r1 * Math.sin(a)])
  }
  for (let k = 1; k < 16; k++) {
    const a = rad(75.0 + (250.0 * k) / 15.0)
    pts.push([c2[0] + r2 * Math.cos(a), 0.0, c2[1] + r2 * Math.sin(a)])
  }
  const ob = mlib.tubeAlong(pts, mlib.circle(0.0022, 7), { up: [0, 1, 0] })
  mlib.smoothShade(ob, 40)
  return [ob, [c2[0], 0.0, c2[1] - r2]]
}

function hang(parts: P.Placed[], eye: Vec3, comZ: number, hookPt: Vec3, face: number): void {
  const [ex, , ez] = eye
  const phi = Math.atan2(-ex, ez - comZ)
  for (const ob of parts) {
    mlib.translate(ob.md, [-ex, 0.0, -ez])
    mlib.rotY(ob.md, phi)
    mlib.rotateZ(ob.md, face)
    mlib.translate(ob.md, hookPt)
  }
}

function potRack(w: World, M: MatSet): void {
  const cx = 0.5
  const cy = 1.02
  const cz = 2.4
  const R = 0.3
  const DOME = 0.285
  const parts: MeshData[] = []
  const HW = 0.03
  const HT = 0.0052
  const strap: Vec2[] = [
    [-HT / 2, -HW / 2],
    [HT / 2, -HW / 2],
    [HT / 2, HW / 2],
    [-HT / 2, HW / 2],
  ]
  parts.push(
    mlib.tubeAlong(
      Array.from({ length: 72 }, (_, i) => {
        const a = (i * Math.PI * 2) / 72
        return [R * Math.cos(a), R * Math.sin(a), 0.0] as Vec3
      }),
      strap,
      { closePath: true },
    ),
  )
  const RW = 0.02
  const RT = 0.0044
  const rib: Vec2[] = [
    [-RT / 2, -RW / 2],
    [RT / 2, -RW / 2],
    [RT / 2, RW / 2],
    [-RT / 2, RW / 2],
  ]
  const R2 = R + (HT + RT) * 0.5
  for (let k = 0; k < 8; k++) {
    const a = (Math.PI * 2 * k) / 8
    const ca = Math.cos(a)
    const sa = Math.sin(a)
    const pts: Vec3[] = []
    for (let i = 0; i < 17; i++) {
      const psi = (rad(84.0) * i) / 16.0
      const rr = R2 * Math.cos(psi)
      pts.push([rr * ca, rr * sa, DOME * Math.sin(psi)])
    }
    parts.push(mlib.tubeAlong(pts, rib, { up: [-sa, ca, 0.0] }))
  }
  parts.push(
    mlib.revolve(
      [
        [0.0, DOME - 0.012],
        [0.03, DOME - 0.01],
        [0.03, DOME + 0.026],
        [0.0, DOME + 0.026],
      ],
      18,
    ),
  )
  parts.push(
    mlib.tubeAlong(
      [
        [0, 0, DOME + 0.026],
        [0, 0, L.CZ - cz],
      ],
      mlib.circle(0.006, 6),
    ),
  )
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 36)
  mlib.translate(ob, [cx, cy, cz])
  w.add(ob, M.iron)

  // --- the pans ------------------------------------------------------------
  const specs: [number, number, number, number, number, boolean][] = [
    [-104.0, 0.074, 0.046, 0.13, 30.0, true],
    [-64.0, 0.105, 0.055, 0.196, -32.0, false],
    [-24.0, 0.086, 0.056, 0.14, 118.0, true],
    [14.0, 0.108, 0.048, 0.201, -8.0, true],
    [52.0, 0.079, 0.051, 0.134, 156.0, false],
    [88.0, 0.096, 0.062, 0.178, 64.0, false],
  ]
  for (const [az, rr, hh, hl, mouth, lined] of specs) {
    const a = rad(az)
    const [hook, low] = sHook(HW * 0.5)
    mlib.rotateZ(hook, a)
    mlib.translate(hook, [cx + R * Math.cos(a), cy + R * Math.sin(a), cz])
    w.add(hook, M.iron)
    const [pan, eye] = saucepan(rr, hh, hl, M, lined)
    const hp: Vec3 = [cx + (R + low[0]) * Math.cos(a), cy + (R + low[0]) * Math.sin(a), cz + low[2]]
    hang(pan, eye, hh * 0.42, hp, rad(mouth - 180.0))
    for (const p of pan) w.add(p.md, p.mat)
  }
  // the colander, hung off its loop from the last hook
  const az = rad(-140.0)
  const [hook, low] = sHook(HW * 0.5)
  mlib.rotateZ(hook, az)
  mlib.translate(hook, [cx + R * Math.cos(az), cy + R * Math.sin(az), cz])
  w.add(hook, M.iron)
  const [col, eye] = colander(0.1, M)
  hang(col, eye, 0.1 * 0.34, [cx + (R + low[0]) * Math.cos(az), cy + (R + low[0]) * Math.sin(az), cz + low[2]], rad(-150.0 - 180.0))
  for (const p of col) w.add(p.md, p.mat)
}

function ceilingDome(w: World, loc: Vec3, M: MatSet, r = 0.165, energy = 300.0, kelvin = 6000.0): void {
  const brass = M.brass ?? mats.metal('brass_fitting', 'A8813C', { rough: 0.32, bump: 0.04 })
  // An analytic source cannot distinguish its own fixture from other casters.
  // Keep this emitter assembly out of the binary depth pass so it cannot cast
  // an enlarged silhouette of itself onto the ceiling or distant walls.
  const fixtureBrass = brass.clone()
  fixtureBrass.name = 'kitchen_ceiling_brass'
  fixtureBrass.userData.noShadow = true
  const can = mlib.revolve(
    [
      [0.0, 0.0],
      [0.072, -0.006],
      [0.076, -0.022],
      [0.044, -0.038],
      [0.0, -0.042],
    ],
    20,
  )
  const stem = mlib.revolve(
    [
      [0.0, -0.038],
      [0.014, -0.038],
      [0.014, -0.15],
      [0.0, -0.15],
    ],
    12,
  )
  const gal = mlib.revolve(
    [
      [0.0, -0.15],
      [0.052, -0.156],
      [0.058, -0.176],
      [0.04, -0.19],
      [0.0, -0.192],
    ],
    18,
  )
  for (const o of [can, stem, gal]) {
    mlib.translate(o, loc)
    w.add(o, fixtureBrass)
  }
  const prof: Vec2[] = []
  for (let i = 0; i < 15; i++) {
    const t = i / 14.0
    const a = Math.PI * 0.52 * t
    prof.push([r * Math.sin(a) * 1.0, -0.176 - r * 0.86 * (1 - Math.cos(a))])
  }
  const sh = mlib.revolve(prof, 30, { capStart: false, capEnd: false })
  mlib.solidify(sh, 0.005)
  mlib.smoothShade(sh, 46)
  const opal = mats.get('opal_shade') ?? mats.emissive('opal_shade', 'FFF0D2', { strength: 2.2, base: 'F6EEDC' })
  mlib.translate(sh, loc)
  w.add(sh, opal)
  const bl = P.bulb(30.0, 0.026)
  mlib.translate(bl.md, [0, 0, -0.246])
  mlib.translate(bl.md, loc)
  w.add(bl.md, bl.mat)
  // Approved real-time visual override: higher-power/cooler Blender practical
  // values look washed without Cycles' path-traced transport. A warmer source
  // plus a stronger soft mask restores the reference's depth and saturation.
  const visualEnergy = energy * 0.9
  const visualKelvin = Math.min(kelvin, 4200)
  w.pointLight([loc[0], loc[1], loc[2] - 0.35], visualEnergy, P.blackbody(visualKelvin), 0.1, {
    shadowIntensity: 0.6,
    shadowMapSize: 1024,
    shadowRadius: 1,
  })
}

function rattanPendant(w: World, loc: Vec3, r = 0.235, h = 0.225, drop = 1.05): void {
  const prof: Vec2[] = [
    [0.032, h],
    [0.046, h * 0.955],
    [0.062, h * 0.9],
    [0.079, h * 0.805],
    [0.098, h * 0.7],
    [0.117, h * 0.59],
    [0.136, h * 0.48],
    [0.153, h * 0.382],
    [0.17, h * 0.29],
    [0.187, h * 0.205],
    [0.202, h * 0.13],
    [0.22, h * 0.062],
    [r, 0.02],
    [r, 0.0],
  ]
  const wk = mats.wicker('rattan_shade', {
    light: 'CFAA6D',
    dark: '8A6229',
    rings: 46.0,
    stakes: 62.0,
    rough: 0.6,
    bump: 0.8,
    centre: [loc[0], loc[1]],
  })
  const fixtureWicker = wk.clone()
  fixtureWicker.name = 'kitchen_pendant_wicker'
  fixtureWicker.userData.noShadow = true
  const sh = mlib.revolve(prof, 32, { capStart: false, capEnd: false })
  mlib.solidify(sh, 0.008)
  mlib.smoothShade(sh, 46)
  mlib.translate(sh, loc)
  w.add(sh, fixtureWicker)
  const cordMat = mats.paint('cord_black', '18181A', { rough: 0.5 }).clone()
  cordMat.name = 'kitchen_pendant_cord'
  cordMat.userData.noShadow = true
  const cord = mlib.tubeAlong(
    [
      [0, 0, h],
      [0, 0, h + drop],
    ],
    mlib.circle(0.005, 6),
  )
  mlib.translate(cord, loc)
  w.add(cord, cordMat)
  const cap = mlib.revolve(
    [
      [0.0, h + drop - 0.03],
      [0.045, h + drop - 0.03],
      [0.045, h + drop],
      [0.0, h + drop],
    ],
    16,
  )
  mlib.translate(cap, loc)
  w.add(cap, cordMat)
  const bulbMd = mlib.revolve(
    [
      [0.0, 0.0],
      [0.028, 0.012],
      [0.032, 0.035],
      [0.024, 0.058],
      [0.011, 0.066],
      [0.011, 0.086],
      [0.0, 0.086],
    ],
    18,
  )
  mlib.translate(bulbMd, [0, 0, h * 0.45])
  mlib.smoothShade(bulbMd, 40)
  mlib.translate(bulbMd, loc)
  w.add(bulbMd, mats.get('bulb_warm') ?? mats.emissive('bulb_warm', 'FFE0AE', { strength: 46.0, base: 'FFF3E2' }))
  // Keep the analytic source just below the open shade. Placing it inside the
  // wicker makes the nearby shade fill most of the point-light cube map and
  // projects a hugely magnified self-shadow onto the far living-room wall.
  w.pointLight([loc[0], loc[1], loc[2] - 0.04], 32.0, [1.0, 0.82, 0.62], 0.06, {
    shadowMapSize: 1024,
    shadowRadius: 1,
  })
}

function placeChamfer(ob: MeshData, u: number, z: number, off = 0.02): MeshData {
  const { dir } = L.chamferDir()
  const [dxc, dyc] = dir
  const ix = dyc
  const iy = -dxc
  const p = L.chamferPt(u, off)
  mlib.transform4(ob, [
    [dxc, ix, 0, p[0]],
    [dyc, iy, 0, p[1]],
    [0, 0, 1, z],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(ob)
  return ob
}

// ------------------------------------------------------------------ build all
export function build(w: World): MatSet {
  const M = mkMats()
  const { len: cl } = L.chamferDir()

  // --- base runs -----------------------------------------------------------
  baseRun(w, [0.0, L.KIT_CTR[0]], [0.0, L.KIT_CTR[1]], M, 1, 1, 0.17)
  baseRun(w, L.chamferPt(0.0), L.chamferPt(cl), M, 2)
  baseRun(w, [L.N_BRICK[0], L.NY], [L.FRIDGE_X[0] - 0.02, L.NY], M, 2, 1, 0.17, CTR_D, true, M.block_n)
  peninsula(w, M)
  proRange(w, M)
  doubleSink(w, M)
  fridge(w, M)

  // --- upper shelving ------------------------------------------------------
  shelfUnit(w, [0.0, L.KIT_SHELF[0]], [0.0, L.KIT_SHELF[1]], 1.5, 2.42, 0.3, 4, M, SHELF_BAYS, SHELF_TIERS)
  wedgeShelf(w, [0.0, L.KIT_WEDGE[0]], [0.0, L.KIT_WEDGE[1]], 1.54, 0.19, M)
  // celadon wall cabinet above the fridge
  const cc = mlib.box(L.FRIDGE_X[0] + 0.02, L.NY - 0.36, 1.86, L.FRIDGE_X[1] + 0.04, L.NY - 0.012, 2.54)
  mlib.bevel(cc, 0.004, 2)
  w.add(cc, M.celadon)
  for (let i = 0; i < 2; i++) {
    const d = slabDoor((L.FRIDGE_X[1] - L.FRIDGE_X[0]) / 2 - 0.012, 0.64, 0.018, 0.055)
    mlib.rotateZ(d, Math.PI)
    mlib.translate(d, [L.FRIDGE_X[0] + 0.04 + (i + 0.5) * ((L.FRIDGE_X[1] - L.FRIDGE_X[0]) / 2), L.NY - 0.375, 1.88])
    w.add(d, M.celadon)
  }
  // small paper-towel shelf under the big shelf unit
  w.add(
    mlib.box(0.0, L.KIT_WEDGE[0], 1.34, 0.19, L.KIT_WEDGE[1], 1.36),
    mats.wood('wood_shelf_small', ['D9B47C', 'B08148', '7A5220'], { ring: 26, warp: 0.5, bump: 0.3, axis: 'X' }),
  )
  potRack(w, M)
  rattanPendant(w, [0.62, 3.28, 1.96])
  ceilingDome(w, [1.62, 2.02, L.CZ], M, 0.165, 300.0, 6000.0)
  dress(w, M)
  return M
}

// ------------------------------------------------------------------- dressing
function dress(w: World, M: MatSet): void {
  const pool = P.palette(4, 24)
  const z0 = 1.5
  const z1 = 2.42
  const t = 0.024
  const zb = z0 + t * 1.4
  const inner = z1 - t * 1.4 - zb
  const [y0, y1] = L.KIT_SHELF
  const edges = Array.from({ length: SHELF_BAYS + 1 }, (_, k) => y0 + ((y1 - y0) * k) / SHELF_BAYS)
  let n = 0
  for (let k = 0; k < SHELF_BAYS; k++) {
    const nt = SHELF_TIERS[k % SHELF_TIERS.length]
    for (let i = 0; i < nt; i++) {
      const zz = zb + (inner * i) / nt + t / 2
      const frac = i / Math.max(1, nt - 1)
      P.fillShelf(
        w,
        [0.02, edges[k] + 0.055],
        [0.02, edges[k + 1] - 0.055],
        zz,
        0.28,
        100 + n,
        inner / nt - 0.045,
        1.0,
        pool,
        0.55,
        1.0 - 0.52 * frac ** 1.5,
      )
      n += 1
    }
  }
  // bottle shelf over the range
  P.fillShelf(w, [0.02, L.KIT_WEDGE[0] + 0.03], [0.02, L.KIT_WEDGE[1] - 0.03], 1.566, 0.17, 77, 0.3, 1.0, pool, 0.5)
  // peninsula shelves
  const penZ = [0.224, 0.464, 0.704]
  penZ.forEach((zz, i) => {
    P.fillShelf(w, [0.05, L.KIT_PEN[0] + 0.05], [0.05, L.KIT_PEN[1] - 0.05], zz, 0.3, 40 + i, 0.2, 1.0, pool, 0.5)
  })
  // counter dressing on the north run
  P.fillShelf(w, [L.N_BRICK[0] + 0.1, L.NY - 0.001], [L.FRIDGE_X[0] - 0.14, L.NY - 0.001], L.CTR_H, 0.62, 9, 0.3, 1.0, pool, 0.34)
  // counter dressing on the west run
  P.fillShelf(w, [0.001, L.KIT_CTR[0] + 0.08], [0.001, L.KIT_CTR[1] - 0.06], L.CTR_H, 0.62, 13, 0.3, 1.0, pool, 0.34)
  // yellow floral swag + tails over the kitchen window
  const chintz = mats.floralChintz('chintz_yellow', {
    ground: 'DCA412',
    petal: 'B81C55',
    petal2: 'DE6389',
    leaf: '1E4E33',
    leaf2: '5F8C44',
    scale: 2.3,
  })
  const u0 = L.KW_U[0] - 0.06
  const u1 = L.KW_U[1] + 0.06
  const zt = L.KW_Z[1] + 0.1
  const sw = P.swag(-(u1 - u0) / 2, (u1 - u0) / 2, 0.0, 0.3, 0.13, 5)
  for (let k = 0; k < 2; k++) {
    const j = P.jabot((k === 0 ? -1 : 1) * ((u1 - u0) / 2 - 0.01), 0.02, 1.18, 0.17, 0.12, k === 0 ? -1 : 1)
    placeChamfer(j, (u0 + u1) / 2, zt)
    w.add(j, chintz)
  }
  placeChamfer(sw, (u0 + u1) / 2, zt)
  w.add(sw, chintz)
  // little café skirt under the sink cabinet
  const sk = P.curtainPanel(-(u1 - u0) / 2 + 0.06, (u1 - u0) / 2 - 0.06, 0.0, -0.42, 0.05, 11, 0.8, 1.0, 19, 0, 2.6)
  placeChamfer(sk, (u0 + u1) / 2, L.CTR_H - 0.05)
  w.add(sk, chintz)
  // framed botanical prints on the north brick
  const gold = mats.paint('paint_gilt', 'C9A24A', { rough: 0.3, coat: 0.4 })
  const art: [number, number, number, number][] = [
    [1.42, 1.98, 0.27, 0.33],
    [1.98, 1.86, 0.24, 0.3],
  ]
  art.forEach(([xx, zz, aw, ah], i) => {
    P.framed(
      w,
      aw,
      ah,
      [xx, L.NY - 0.02, zz],
      [0, -1],
      gold,
      mats.botanical(`art_botanical_${i}`, {
        normal: [0, -1],
        seed: 47 + i * 7,
        ground: 'E5DCBE',
        stem: '55642E',
        leafc: ['445A28', '7A8A4C'],
        bloom: ['A85E30', 'D9A867'],
      }),
    )
  })
  // wrought-iron ornament + coat hooks beside the front door
  const hk: MeshData[] = []
  hk.push(mlib.box(0.004, 1.3, 1.62, 0.026, 1.34, 1.7))
  for (const yy of [1.305, 1.318, 1.331]) {
    const pts: Vec3[] = [
      [0.02, yy, 1.655],
      [0.055, yy, 1.65],
      [0.062, yy, 1.628],
      [0.048, yy, 1.618],
    ]
    hk.push(mlib.tubeAlong(pts, mlib.circle(0.0045, 6)))
  }
  w.add(mlib.join(hk), M.iron)
}
