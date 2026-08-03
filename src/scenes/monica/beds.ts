/** Monica's and Rachel's bedrooms + hall/bathroom dressing - port of f_beds.py. */
import type * as THREE from 'three/webgpu'
import * as L from './L'
import * as mlib from '../../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import { PyRandom } from '../../lib/rng'
import * as mats from '../../mats/mats'
import * as P from './props'
import * as FL from './living'
import type { MatSet } from './shell'
import type { World } from '../../core/world'

function rad(d: number): number {
  return (d * Math.PI) / 180
}

export function mkMats(): MatSet {
  const M: MatSet = {}
  const BOK: [string, string, string] = ['A8783C', '7E5426', '4E3216']
  const BKK = { ring: 14.0, warp: 0.11, warpScale: 1.2, distort: 1.6, blotch: 0.16, bump: 0.1, rough: [0.18, 0.3] as [number, number] }
  M.oak = mats.wood('wood_bed_oak', BOK, { axis: 'YZ', ...BKK })
  M.oak_v = mats.wood('wood_bed_oak_v', BOK, { axis: 'XY', ...BKK })
  M.oak_h = mats.wood('wood_bed_oak_h', BOK, { axis: 'Z', ...BKK })
  M.white = mats.paint('paint_bed_white', 'E9E3D4', { rough: 0.28, coat: 0.3 })
  M.linen = mats.fabric('fabric_linen_white', 'D8D2C0', { rough: 0.84, sheen: 0.2, weave: 520 })
  M.quiltA = mats.floralChintz('chintz_quilt_a', {
    ground: 'BEC6CC',
    petal: 'AE7480',
    petal2: 'C69CA6',
    leaf: '566B52',
    leaf2: '87977A',
    scale: 9.0,
  })
  M.quiltB = mats.floralChintz('chintz_quilt_b', {
    ground: 'C9B084',
    petal: '9C4A3C',
    petal2: 'C4795A',
    leaf: '5A6238',
    leaf2: '90A05E',
    scale: 6.8,
  })
  M.rug = mats.fabric('fabric_bed_rug', 'A88C6E', { rough: 0.9, sheen: 0.1, weave: 340, bump: 0.5 })
  M.brass = mats.get('metal_brass')!
  return M
}

function bedspread(cx: number, cy: number, ln: number, wd: number, ztop: number, drop: number, seed = 0): MeshData {
  const rng = new PyRandom(seed)
  const s1 = rng.uniform(0, Math.PI * 2)
  const s2 = rng.uniform(0, Math.PI * 2)
  const pts = mlib.roundedRect(ln, wd, 0.115, 6)
  const LEV: [number, number][] = [
    [0.0, 0.94],
    [0.16, 0.99],
    [0.45, 1.0],
    [0.74, 1.0],
    [0.9, 0.985],
    [1.0, 0.93],
  ]
  const rings: Vec3[][] = LEV.map(([t, s]) => {
    const z = ztop - drop + drop * t
    return pts.map(([x, y]) => {
      const wr = (0.011 * Math.sin(x * 5.7 + s1) + 0.009 * Math.sin(y * 8.1 + s2) + 0.006 * Math.sin((x + y) * 10.6 + s1 * 1.7)) * t ** 2
      return [cx + x * s, cy + y * s, z + wr] as Vec3
    })
  })
  const ob = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(ob, 48)
  return ob
}

function bed(w: World, cy: number, M: MatSet, quilt: THREE.Material, ML: MatSet): void {
  const x1 = L.EXT_E - 0.03
  const x0 = x1 - L.BED_L
  const bw = L.BED_W
  const y0 = cy - bw / 2
  const y1 = cy + bw / 2
  const placed: [MeshData, THREE.Material][] = []
  // headboard against the east wall
  const hb = mlib.prismYZ(
    [
      [y0, 0.1],
      [y1, 0.1],
      [y1, 0.98],
      [y1 - 0.06, 1.04],
      [y0 + 0.06, 1.04],
      [y0, 0.98],
    ],
    x1 - 0.055,
    x1,
  )
  mlib.bevel(hb, 0.008, 2)
  placed.push([hb, M.oak_v])
  const rails: [number, number, number, number, number, number][] = [
    [x0, y0, 0.14, x1 - 0.05, y0 + 0.055, 0.4],
    [x0, y1 - 0.055, 0.14, x1 - 0.05, y1, 0.4],
    [x0, y0, 0.14, x0 + 0.055, y1, 0.6],
  ]
  for (const a of rails) {
    const o = mlib.box(a[0], a[1], a[2], a[3], a[4], a[5])
    mlib.bevel(o, 0.006, 2)
    placed.push([o, M.oak])
  }
  const legPos: [number, number][] = [
    [x0 + 0.03, y0 + 0.03],
    [x0 + 0.03, y1 - 0.03],
    [x1 - 0.05, y0 + 0.03],
    [x1 - 0.05, y1 - 0.03],
  ]
  for (const [fx, fy] of legPos) {
    const lg = mlib.revolve(
      [
        [0.0, 0.0],
        [0.03, 0.006],
        [0.034, 0.03],
        [0.03, 0.14],
        [0.0, 0.14],
      ],
      14,
    )
    mlib.translate(lg, [fx, fy, 0.0])
    mlib.smoothShade(lg, 40)
    placed.push([lg, M.oak_v])
  }
  for (const [o, mm] of placed) w.add(o, mm)
  w.box2(x0 - 0.02, y0 - 0.02, x1, y1 + 0.02)
  // mattress + duvet + pillows
  const mat_ = mlib.cushion(L.BED_L - 0.12, bw - 0.1, 0.22, 0.06)
  mlib.translate(mat_, [(x0 + x1) / 2 - 0.02, cy, 0.4])
  w.add(mat_, M.linen)
  // Extend the spread past the mattress foot so the two bulged surfaces do not
  // sit within a few millimetres and z-fight at grazing views.
  const duv = bedspread((x0 + x1) / 2 - 0.12, cy, L.BED_L - 0.02, bw + 0.14, 0.665, 0.3, Math.abs(Math.trunc(Math.abs(cy) * 97)) % 991)
  w.add(duv, quilt)
  for (const s of [-1, 1]) {
    const pw = mlib.cushion(0.44, 0.62, 0.175, 0.085)
    mlib.rotY(pw, rad(-21))
    mlib.rotX(pw, rad(s * 3.5))
    mlib.translate(pw, [x1 - 0.34, cy + s * 0.325, 0.615])
    w.add(pw, M.linen)
  }
  // nightstands flanking the head
  for (const s of [-1, 1]) {
    const nx = x1 - 0.24
    const ny = cy + s * (bw / 2 + 0.34)
    const body = mlib.box(nx - 0.22, ny - 0.22, 0.09, nx + 0.22, ny + 0.22, 0.56)
    mlib.bevel(body, 0.006, 2)
    w.add(body, M.oak_h)
    const top = mlib.box(nx - 0.245, ny - 0.245, 0.56, nx + 0.245, ny + 0.245, 0.6)
    mlib.bevel(top, 0.005, 3)
    w.add(top, M.oak_h)
    const dw = mlib.box(nx - 0.245, ny - 0.185, 0.2, nx - 0.222, ny + 0.185, 0.44)
    mlib.bevel(dw, 0.004, 2)
    w.add(dw, M.oak_h)
    w.box2(nx - 0.25, ny - 0.25, nx + 0.25, ny + 0.25)
    const kb = mlib.revolve(
      [
        [0.0, 0.0],
        [0.016, 0.004],
        [0.018, 0.012],
        [0.01, 0.02],
        [0.0, 0.022],
      ],
      14,
    )
    mlib.rotY(kb, -Math.PI / 2)
    mlib.translate(kb, [nx - 0.246, ny, 0.32])
    mlib.smoothShade(kb, 40)
    w.add(kb, M.brass)
    FL.tableLamp(w, nx, ny, 0.6, ML, 14.0, 0.78)
  }
}

function chest(w: World, cx: number, cy: number, rotz: number, M: MatSet, cw = 1.02, d = 0.46, h = 0.86): void {
  const parts: MeshData[] = []
  const body = mlib.box(-d / 2, -cw / 2, 0.075, d / 2, cw / 2, h - 0.04)
  mlib.bevel(body, 0.008, 2)
  parts.push(body)
  const top = mlib.box(-d / 2 - 0.022, -cw / 2 - 0.022, h - 0.04, d / 2 + 0.022, cw / 2 + 0.022, h)
  mlib.bevel(top, 0.006, 3)
  parts.push(top)
  for (let k = 0; k < 3; k++) {
    const z = 0.1 + (k * (h - 0.2)) / 3
    const dw = mlib.box(-d / 2 - 0.02, -cw / 2 + 0.03, z + 0.008, -d / 2, cw / 2 - 0.03, z + (h - 0.2) / 3 - 0.008)
    mlib.bevel(dw, 0.004, 2)
    parts.push(dw)
  }
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const lg = mlib.box(sx * (d / 2 - 0.055) - 0.028, sy * (cw / 2 - 0.055) - 0.028, 0.0, sx * (d / 2 - 0.055) + 0.028, sy * (cw / 2 - 0.055) + 0.028, 0.08)
    mlib.bevel(lg, 0.005, 2)
    parts.push(lg)
  }
  const ob = mlib.join(parts)
  mlib.rotateZ(ob, rotz)
  mlib.translate(ob, [cx, cy, 0.0])
  w.add(ob, M.oak)
  w.obb(cx, cy, d / 2 + 0.03, cw / 2 + 0.03, rotz)
  const knobs: MeshData[] = []
  for (let k = 0; k < 3; k++) {
    const z = 0.1 + (k * (h - 0.2)) / 3 + (h - 0.2) / 6
    for (const s of [-1, 1]) {
      const kb = mlib.revolve(
        [
          [0.0, 0.0],
          [0.018, 0.006],
          [0.02, 0.016],
          [0.011, 0.026],
          [0.0, 0.028],
        ],
        14,
      )
      mlib.rotY(kb, -Math.PI / 2)
      mlib.translate(kb, [-d / 2 - 0.021, s * 0.22, z])
      knobs.push(kb)
    }
  }
  const ko = mlib.join(knobs)
  mlib.smoothShade(ko, 40)
  mlib.rotateZ(ko, rotz)
  mlib.translate(ko, [cx, cy, 0.0])
  w.add(ko, M.brass)
}

function areaRug(w: World, cx: number, cy: number, cw: number, d: number, M: MatSet): void {
  const ob = mlib.prism(mlib.roundedRect(cw, d, 0.03, 3), 0.0008, 0.0108)
  mlib.bevel(ob, 0.003, 2)
  w.add(ob, M.rug, { at: [cx, cy, 0.0] })
}

export function build(w: World): void {
  const M = mkMats()
  const ML = FL.mkMats()
  const gold = mats.get('paint_gilt') ?? mats.paint('paint_gilt', 'C9A24A', { rough: 0.3 })

  // ------------------------------------------------------ Rachel's bedroom
  bed(w, L.RB_WIN_Y, M, M.quiltA, ML)
  chest(w, L.BED_X[0] + 0.28, L.RB_Y[0] + 0.95, 0.0, M)
  areaRug(w, 9.9, L.RB_WIN_Y - 0.1, 1.6, 2.1, M)
  P.framed(
    w,
    0.4,
    0.52,
    [L.EXW + 0.03, (L.CD_Y[1] + L.RB_Y[1]) * 0.5, 1.62],
    [1, 0],
    gold,
    mats.botanical('art_rb', {
      normal: [1, 0],
      seed: 11,
      ground: 'E7DEC0',
      stem: '53642F',
      leafc: ['40602C', '75894C'],
      bloom: ['B4604A', 'E3B98E'],
    }),
  )
  FL.sconce(w, [L.EXW + 0.02, L.CD_Y[0] - 0.62, 1.8], [1, 0], ML, 16.0, true)

  // ------------------------------------------------------ Monica's bedroom
  bed(w, L.MB_WIN_Y, M, M.quiltB, ML)
  chest(w, L.BED_X[0] + 0.28, L.MD_Y[1] + 0.68, 0.0, M)
  areaRug(w, 9.9, L.MB_WIN_Y + 0.1, 1.6, 2.1, M)
  P.framed(
    w,
    0.36,
    0.46,
    [L.EXW + 0.03, L.MD_Y[1] + 0.68, 1.62],
    [1, 0],
    gold,
    mats.botanical('art_mb', {
      normal: [1, 0],
      seed: 19,
      ground: 'E2DCC4',
      stem: '4C5C38',
      leafc: ['44583A', '7A8A5A'],
      bloom: ['8A6C92', 'C7B2CE'],
    }),
  )
  FL.sconce(w, [L.EXW + 0.02, L.MB_Y[1] - 0.85, 1.8], [1, 0], ML, 16.0, true)
}

/** One horizontal section through the WC pan. The asymmetric egg plan keeps
 * the rear blunt and gives the front the long taper of a cast china bowl. */
function panRing(hw: number, yb: number, yf: number, z: number, n = 44, waist = 0.38): Vec3[] {
  const cy = yb + (yf - yb) * waist
  return Array.from({ length: n }, (_, i) => {
    const a = (Math.PI * 2 * i) / n
    const c = Math.cos(a)
    return [hw * Math.sin(a), c >= 0 ? cy + (yf - cy) * c : cy + (cy - yb) * c, z]
  })
}

/** Close-coupled two-piece WC, facing local +Y with its tank against the
 * south wall. Ported section-for-section from the authoritative Blender mesh. */
function waterCloset(w: World, cx: number, cy: number, wht: THREE.Material, chrome: THREE.Material, wallY: number): void {
  const rim = 0.395
  const seatT = 0.019
  const lidT = 0.026
  const shelfZ = rim + seatT + lidT + 0.007
  const tankZ = shelfZ + 0.31
  const tankLidZ = shelfZ + 0.34
  const hw = 0.185
  const yb = -0.118
  const yf = 0.352
  const tankY = -0.254

  const pan = mlib.loft(
    [
      panRing(0.118, -0.29, 0.15, 0.0),
      panRing(0.112, -0.288, 0.144, 0.024),
      panRing(0.09, -0.28, 0.11, 0.13),
      panRing(0.1, -0.276, 0.138, 0.208),
      panRing(0.14, -0.24, 0.226, 0.284),
      panRing(0.174, -0.172, 0.314, 0.356),
      panRing(hw, yb, yf, rim - 0.014),
      panRing(hw, yb, yf, rim),
      panRing(0.152, yb + 0.022, 0.282, rim - 0.004),
      panRing(0.132, yb + 0.038, 0.252, 0.347),
      panRing(0.102, yb + 0.064, 0.192, 0.282),
      panRing(0.064, yb + 0.098, 0.118, 0.228),
      panRing(0.032, yb + 0.122, 0.062, 0.202),
    ],
    { closeV: true, capStart: true, capEnd: true },
  )
  mlib.smoothShade(pan, 44)

  const shelf = mlib.loft(
    [
      mlib.roundedRect(0.196, 0.204, 0.046, 4).map(([x, y]) => [x, y - 0.25, 0.17] as Vec3),
      mlib.roundedRect(0.25, 0.212, 0.044, 4).map(([x, y]) => [x, y - 0.246, 0.29] as Vec3),
      mlib.roundedRect(0.31, 0.19, 0.036, 4).map(([x, y]) => [x, y - 0.257, 0.396] as Vec3),
      mlib.roundedRect(0.33, 0.176, 0.03, 4).map(([x, y]) => [x, y - 0.264, shelfZ] as Vec3),
    ],
    { closeV: true, capStart: true, capEnd: true },
  )
  mlib.bevel(shelf, 0.008, 2)
  mlib.smoothShade(shelf, 46)

  const hingeFlat = mlib.prism(mlib.roundedRect(0.32, 0.09, 0.026, 3), 0.32, rim)
  mlib.translate(hingeFlat, [0.0, -0.15, 0.0])
  mlib.bevel(hingeFlat, 0.008, 2)

  const tank = mlib.prism(mlib.roundedRect(0.428, 0.196, 0.026, 4), shelfZ - 0.006, tankZ)
  mlib.bevel(tank, 0.012, 3)
  mlib.translate(tank, [0.0, tankY, 0.0])
  const tankLid = mlib.prism(mlib.roundedRect(0.452, 0.22, 0.03, 4), tankZ, tankLidZ)
  mlib.bevel(tankLid, 0.009, 3)
  mlib.translate(tankLid, [0.0, tankY, 0.0])

  const body = mlib.join([pan, shelf, hingeFlat, tank, tankLid])
  mlib.translate(body, [cx, cy, 0.0])
  w.add(body, wht, { collide: true })

  const plan = panRing(hw, yb, yf, 0.0).map(([x, y]) => [x, y] as Vec2)
  const planCy = yb + (yf - yb) * 0.38
  const ring2d = (scale: number, dy = 0): Vec2[] => plan.map(([x, y]) => [x * scale, planCy + (y - planCy) * scale + dy])
  const seat = mlib.annularPrism(ring2d(1.008), ring2d(0.66, 0.03), rim, rim + seatT, 0.006, 3)
  mlib.smoothShade(seat, 40)
  const closedLid = mlib.loft(
    [
      ring2d(1.018).map(([x, y]) => [x, y, rim + seatT] as Vec3),
      ring2d(1.014).map(([x, y]) => [x, y, rim + seatT + lidT * 0.62] as Vec3),
      ring2d(0.93).map(([x, y]) => [x, y, rim + seatT + lidT] as Vec3),
    ],
    { closeV: true, capStart: true, capEnd: true },
  )
  mlib.bevel(closedLid, 0.008, 3)
  mlib.smoothShade(closedLid, 44)
  const seatParts = mlib.join([seat, closedLid])
  mlib.translate(seatParts, [cx, cy, 0.0])
  w.add(seatParts, wht)

  const tankFront = tankY + 0.098
  const fittings: MeshData[] = []
  const escutcheon = mlib.revolve(
    [
      [0.0, 0.0],
      [0.02, 0.0],
      [0.019, 0.014],
      [0.01, 0.02],
      [0.0, 0.02],
    ],
    14,
  )
  mlib.rotX(escutcheon, -Math.PI / 2)
  mlib.translate(escutcheon, [-0.128, tankFront - 0.004, tankZ - 0.072])
  fittings.push(escutcheon)
  fittings.push(
    mlib.tubeAlong(
      [
        [-0.128, tankFront + 0.016, tankZ - 0.072],
        [-0.128, tankFront + 0.024, tankZ - 0.074],
        [-0.052, tankFront + 0.028, tankZ - 0.102],
      ],
      mlib.roundedRect(0.022, 0.008, 0.004, 2),
    ),
  )

  const wallOffsetY = wallY - cy
  const stop = mlib.revolve(
    [
      [0.0, 0.0],
      [0.022, 0.0],
      [0.022, 0.052],
      [0.03, 0.058],
      [0.03, 0.07],
      [0.0, 0.07],
    ],
    14,
  )
  mlib.rotX(stop, -Math.PI / 2)
  mlib.translate(stop, [-0.242, wallOffsetY, 0.19])
  fittings.push(stop)
  const supplyCurve = mlib.bez(
    [wallOffsetY + 0.068, 0.19],
    [wallOffsetY + 0.2, 0.198],
    [wallOffsetY + 0.16, 0.34],
    [wallOffsetY + 0.076, shelfZ - 0.024],
    10,
  )
  const supplySteps = supplyCurve.length - 1
  fittings.push(
    mlib.tubeAlong(
      supplyCurve.map(([y, z], i) => [-0.242 + 0.057 * (i / supplySteps), y, z] as Vec3),
      mlib.circle(0.0095, 10),
    ),
  )
  const nut = mlib.revolve(
    [
      [0.0, 0.0],
      [0.021, 0.0],
      [0.021, 0.03],
      [0.0, 0.03],
    ],
    12,
  )
  mlib.translate(nut, [-0.185, supplyCurve[supplyCurve.length - 1][0], shelfZ - 0.034])
  fittings.push(nut)
  for (const sx of [-0.076, 0.076]) {
    const hinge = mlib.revolve(
      [
        [0.0, 0.0],
        [0.013, 0.0],
        [0.013, 0.054],
        [0.0, 0.054],
      ],
      12,
    )
    mlib.rotY(hinge, Math.PI / 2)
    mlib.translate(hinge, [sx - 0.027, -0.15, rim + 0.013])
    fittings.push(hinge)
  }
  const fittingMesh = mlib.join(fittings)
  mlib.smoothShade(fittingMesh, 38)
  mlib.translate(fittingMesh, [cx, cy, 0.0])
  w.add(fittingMesh, chrome)
}

export function dressHall(w: World): void {
  const ML2 = FL.mkMats()
  const gold = mats.get('paint_gilt') ?? mats.paint('paint_gilt', 'C9A24A', { rough: 0.3 })
  const artSpecs: [number, number, number, number][] = [
    [4.36, 1.86, 0.24, 0.3],
    [4.36, 1.5, 0.24, 0.3],
  ]
  artSpecs.forEach(([yy, zz, aw, ah], i) => {
    P.framed(
      w,
      aw,
      ah,
      [L.HALL_X[0] + 0.03, yy, zz],
      [1, 0],
      gold,
      mats.botanical(`art_hall_${i}`, {
        normal: [1, 0],
        seed: 31 + i * 5,
        ground: 'E6DEC6',
        stem: '5C6A40',
        leafc: ['4E5E36', '86946A'],
        bloom: ['A87A52', 'DCC69C'],
      }),
    )
  })
  const tw = 0.44
  const td = 0.34
  const th = 0.72
  const white = mats.paint('paint_white_table', 'E2D9C6', { rough: 0.34, coat: 0.28 })
  const parts: MeshData[] = []
  const top = mlib.prism(mlib.roundedRect(td, tw, 0.05, 4), th - 0.026, th)
  mlib.bevel(top, 0.005, 3)
  parts.push(top)
  const ap = mlib.prism(mlib.roundedRect(td - 0.055, tw - 0.055, 0.03, 3), th - 0.084, th - 0.026)
  mlib.bevel(ap, 0.004, 2)
  parts.push(ap)
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const pts = mlib.bez([0.0, th - 0.03], [0.05, th - 0.28], [0.08, th - 0.52], [0.025, 0.004], 10)
    const path = pts.map(([p, z]) => [sx * (td / 2 - 0.055 + p * 0.8), sy * (tw / 2 - 0.055 + p * 0.8), z] as Vec3)
    parts.push(mlib.tubeAlong(path, mlib.circle(0.0185, 8)))
  }
  const tob = mlib.join(parts)
  mlib.smoothShade(tob, 40)
  const hty = L.NW_Y - 0.45
  mlib.translate(tob, [L.HALL_X[1] - 0.24, hty, 0.0])
  w.add(tob, white, { collide: true })
  FL.tableLamp(w, L.HALL_X[1] - 0.24, hty, 0.72, ML2, 16.0, 0.85)
  FL.sconce(w, [L.HALL_X[0] + 0.02, 4.36, 2.16], [1, 0], ML2, 11.0)

  // ------------------------------------------------------------ bathroom
  const wht = mats.paint('porcelain', 'F2F0E8', { rough: 0.1, coat: 0.6 })
  const chrome = mats.get('metal_chrome') ?? mats.metal('metal_chrome', 'D8DCE0', { rough: 0.1, bump: 0.02 })
  const TW_ = 1.5
  const TD_ = 0.72
  const TCX = L.BA_X[0] + 0.06 + TW_ / 2
  const TCY = L.BA_Y[1] - 0.03 - TD_ / 2
  // hollowed for real: outer shell with the rounded cavity sunk from the rim
  const tb = mlib.hollowPrism(
    mlib.roundedRect(TW_, TD_, 0.22, 6).map(([x, y]) => [x + TCX, y + TCY] as Vec2),
    0.0,
    0.58,
    mlib.roundedRect(TW_ - 0.12, TD_ - 0.12, 0.19, 6).map(([x, y]) => [x + TCX, y + TCY] as Vec2),
    0.19,
    0.016,
  )
  w.add(tb, wht, { collide: true })
  // mixer, riser and shower rose on the tub's west end
  const fit: MeshData[] = []
  for (const dy of [-0.09, 0.09]) {
    const hnd = mlib.revolve(
      [
        [0.0, 0.0],
        [0.026, 0.0],
        [0.02, 0.03],
        [0.03, 0.052],
        [0.03, 0.062],
        [0.0, 0.062],
      ],
      14,
    )
    mlib.rotY(hnd, Math.PI / 2)
    mlib.translate(hnd, [TCX - TW_ / 2 + 0.03, TCY + dy, 0.66])
    fit.push(hnd)
  }
  fit.push(
    mlib.tubeAlong(
      [
        [TCX - TW_ / 2 + 0.03, TCY, 0.64],
        [TCX - TW_ / 2 + 0.17, TCY, 0.64],
        [TCX - TW_ / 2 + 0.21, TCY, 0.61],
      ],
      mlib.circle(0.014, 10),
    ),
  )
  fit.push(
    mlib.tubeAlong(
      [
        [TCX - TW_ / 2 + 0.03, TCY, 0.7],
        [TCX - TW_ / 2 + 0.03, TCY, 1.86],
        [TCX - TW_ / 2 + 0.13, TCY, 1.94],
      ],
      mlib.circle(0.011, 10),
    ),
  )
  const rose = mlib.revolve(
    [
      [0.0, 0.0],
      [0.055, 0.012],
      [0.058, 0.03],
      [0.026, 0.052],
      [0.0, 0.056],
    ],
    18,
  )
  mlib.rotY(rose, rad(150))
  mlib.translate(rose, [TCX - TW_ / 2 + 0.15, TCY, 1.95])
  fit.push(rose)
  const fo = mlib.join(fit)
  mlib.smoothShade(fo, 38)
  w.add(fo, chrome)
  // curtain rail round the two open sides of the tub, and the curtain
  const rail = mlib.tubeAlong(
    [
      [TCX - TW_ / 2 + 0.02, TCY - TD_ / 2 + 0.02, 1.98],
      [TCX + TW_ / 2 - 0.02, TCY - TD_ / 2 + 0.02, 1.98],
      [TCX + TW_ / 2 - 0.02, TCY + TD_ / 2 - 0.02, 1.98],
    ],
    mlib.circle(0.01, 10),
  )
  mlib.smoothShade(rail, 38)
  w.add(rail, chrome)
  const cur = P.curtainPanel(TCX + TW_ / 2 - 0.4, TCX + TW_ / 2 - 0.02, 1.96, 0.22, 0.075, 6, 0.75, 1.0, 5, 0.022, 3.0)
  mlib.translate(cur, [0.0, TCY - TD_ / 2 + 0.1, 0.0])
  w.add(cur, mats.paint('shower_curtain', 'DFE4E2', { rough: 0.34, coat: 0.4 }))
  // pedestal basin, bowl hollowed out, in the north-east corner
  const BX = L.BA_X[1] - 0.35
  const BY = L.BA_Y[1] - 0.26
  const ped = mlib.revolve(
    [
      [0.0, 0.0],
      [0.115, 0.0],
      [0.1, 0.05],
      [0.072, 0.3],
      [0.085, 0.58],
      [0.14, 0.66],
      [0.0, 0.66],
    ],
    20,
  )
  mlib.smoothShade(ped, 34)
  mlib.translate(ped, [BX, BY, 0.0])
  w.add(ped, wht, { collide: true })
  const bs = mlib.hollowPrism(
    mlib.roundedRect(0.5, 0.4, 0.12, 5).map(([x, y]) => [x + BX, y + BY] as Vec2),
    0.64,
    0.8,
    mlib.roundedRect(0.36, 0.26, 0.1, 5).map(([x, y]) => [x + BX, y + BY] as Vec2),
    0.7,
    0.012,
  )
  w.add(bs, wht)
  const btap = mlib.tubeAlong(
    [
      [BX, BY + 0.15, 0.8],
      [BX, BY + 0.15, 0.885],
      [BX, BY + 0.075, 0.9],
    ],
    mlib.circle(0.012, 10),
  )
  mlib.smoothShade(btap, 38)
  w.add(btap, chrome)
  // mirrored cabinet over the basin
  const mc = mlib.box(BX - 0.26, L.BA_Y[1] - 0.16, 1.12, BX + 0.26, L.BA_Y[1] - 0.005, 1.66)
  mlib.bevel(mc, 0.005, 2)
  w.add(mc, wht)
  w.add(mlib.box(BX - 0.235, L.BA_Y[1] - 0.175, 1.15, BX + 0.235, L.BA_Y[1] - 0.158, 1.63), mats.metal('mirror_glass', 'F0F2F4', { rough: 0.02, bump: 0.0 }))
  // Detailed close-coupled WC, tight in the inner corner against the south wall.
  const WX = L.BA_X[0] + 0.4
  const WY = L.BA_Y[0] + 0.376
  waterCloset(w, WX, WY, wht, chrome, L.BA_Y[0])
  // bathroom overhead: a fitting, not a bare lamp
  P.flushDome(w, [(L.BA_X[0] + L.BA_X[1]) * 0.5, (L.BA_Y[0] + L.BA_Y[1]) * 0.5, 2.62], 0.115, 17.0, [1.0, 0.9, 0.8], 0.07)
}
