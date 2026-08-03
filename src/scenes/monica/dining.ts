/** Round pedestal table plus the mismatched chairs - port of f_dining.py. */
import type * as THREE from 'three/webgpu'
import * as L from './L'
import * as mlib from '../../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import { PyRandom } from '../../lib/rng'
import * as mats from '../../mats/mats'
import * as P from './props'
import type { MatSet } from './shell'
import type { World } from '../../core/world'

function rad(d: number): number {
  return (d * Math.PI) / 180
}

export function mkMats(): MatSet {
  const M: MatSet = {}
  const OAKC: [string, string, string] = ['A17A4E', '9A7449', '8E6A40']
  const OAKK = { ring: 26.0, warp: 0.22, warpScale: 1.3, distort: 2.2, bump: 0.05, rough: [0.28, 0.46] as [number, number] }
  M.oak_top = mats.wood('wood_oak_table_top', OAKC, { axis: 'YZ', ...OAKK })
  M.oak = mats.wood('wood_oak_table', OAKC, { axis: 'XY', ...OAKK })
  M.oak_z = mats.wood('wood_oak_table_z', OAKC, { axis: 'Z', ...OAKK })
  M.chair = mats.wood('wood_chair_honey', ['D2A05E', 'B98844', '96682C'], {
    ring: 20.0,
    warp: 0.18,
    warpScale: 1.2,
    distort: 1.6,
    bump: 0.05,
    rough: [0.18, 0.32],
    axis: 'XY',
  })
  M.bentwood = mats.wood('wood_bentwood', ['68391F', '552C15', '41200D'], {
    ring: 24.0,
    warp: 0.16,
    distort: 1.4,
    bump: 0.06,
    rough: [0.16, 0.3],
    axis: 'XY',
  })
  M.glass = mats.get('glass_clear') ?? mats.pane('glass_clear')
  M.tapestry = mats.floralChintz('chintz_tapestry', {
    ground: '7C8593',
    petal: '8A6570',
    petal2: '90696E',
    leaf: '4E5A48',
    leaf2: '63705A',
    scale: 21.0,
    rough: 0.84,
  })
  M.cushpurple = mats.velvet('velvet_purple_seat', '4A2E5E')
  M.piping = mats.fabric('fabric_white_pipe', 'EFEAE0', { rough: 0.7 })
  return M
}

function roundTable(w: World, cx: number, cy: number, M: MatSet, r = 0.6, h = 0.755): void {
  const placed: [MeshData, THREE.Material][] = []
  const tp: Vec2[] = [
    [0.0, h - 0.052],
    [r - 0.03, h - 0.052],
    [r - 0.01, h - 0.046],
    [r, h - 0.034],
    [r, h - 0.02],
    [r - 0.008, h - 0.01],
    [r - 0.004, h - 0.004],
    [r - 0.014, h],
    [0.0, h],
  ]
  const top = mlib.revolve(tp, 56)
  mlib.smoothShade(top, 26)
  placed.push([top, M.oak_top])
  const ap: Vec2[] = [
    [0.0, h - 0.115],
    [r - 0.055, h - 0.115],
    [r - 0.04, h - 0.1],
    [r - 0.036, h - 0.07],
    [r - 0.026, h - 0.056],
    [0.0, h - 0.052],
  ]
  const apr = mlib.revolve(ap, 48)
  mlib.smoothShade(apr, 30)
  placed.push([apr, M.oak_z])
  const pd: Vec2[] = [
    [0.0, 0.075],
    [0.15, 0.075],
    [0.155, 0.09],
    [0.14, 0.11],
    [0.098, 0.135],
    [0.086, 0.16],
    [0.096, 0.19],
    [0.13, 0.235],
    [0.158, 0.29],
    [0.166, 0.345],
    [0.15, 0.4],
    [0.112, 0.448],
    [0.082, 0.482],
    [0.072, 0.52],
    [0.08, 0.552],
    [0.104, 0.575],
    [0.1, 0.596],
    [0.078, 0.612],
    [0.076, h - 0.115],
    [0.0, h - 0.115],
  ]
  const ped = mlib.revolve(pd, 40)
  mlib.smoothShade(ped, 30)
  placed.push([ped, M.oak])
  for (let k = 0; k < 4; k++) {
    const a = (Math.PI * 2 * k) / 4 + Math.PI / 4
    const prof: Vec2[] = [
      [0.055, 0.0],
      [0.48, 0.0],
      [0.5, 0.016],
      [0.47, 0.046],
      [0.34, 0.062],
      [0.22, 0.076],
      [0.13, 0.086],
      [0.055, 0.088],
    ]
    const n = prof.length
    const half = 0.062
    const vs: Vec3[] = []
    for (const [rr, zz] of prof) vs.push([rr, -half * (0.45 + 0.55 * (1 - rr / 0.5)), zz])
    for (const [rr, zz] of prof) vs.push([rr, half * (0.45 + 0.55 * (1 - rr / 0.5)), zz])
    const fs: number[][] = []
    for (let i = 0; i < n - 1; i++) fs.push([i, i + 1, n + i + 1, n + i])
    fs.push(Array.from({ length: n }, (_, i) => i))
    fs.push(Array.from({ length: n }, (_, i) => 2 * n - 1 - i))
    const foot = mlib.meshObj(vs, fs)
    mlib.recalcNormals(foot)
    mlib.rotateZ(foot, a)
    placed.push([foot, M.oak])
    const pf = mlib.revolve(
      [
        [0.0, 0.0],
        [0.05, 0.006],
        [0.054, 0.026],
        [0.04, 0.044],
        [0.0, 0.048],
      ],
      16,
    )
    mlib.translate(pf, [0.455 * Math.cos(a), 0.455 * Math.sin(a), 0.0])
    mlib.smoothShade(pf, 40)
    placed.push([pf, M.oak])
  }
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [cx, cy, 0.0])
    w.add(ob, mm)
  }
  w.obb(cx, cy, r * 0.85, r * 0.85, 0)
}

// ------------------------------------------------------------------- chairs

function aim(ob: MeshData, a: Vec3, b2: Vec3): MeshData {
  const d: Vec3 = [b2[0] - a[0], b2[1] - a[1], b2[2] - a[2]]
  const ln = Math.hypot(...d)
  const dn: Vec3 = [d[0] / ln, d[1] / ln, d[2] / ln]
  const phi = Math.asin(Math.max(-1.0, Math.min(1.0, dn[0])))
  const c = Math.sqrt(Math.max(1e-9, 1.0 - dn[0] * dn[0]))
  const psi = Math.atan2(-dn[1] / c, dn[2] / c)
  mlib.rotY(ob, phi)
  mlib.rotX(ob, psi)
  mlib.translate(ob, a)
  return ob
}

function turned(ln: number, prof: Vec2[], seg = 14): MeshData {
  const p: Vec2[] = [[0.0, 0.0]]
  for (const [t, r] of prof) p.push([r, t * ln])
  p.push([0.0, ln])
  const ob = mlib.revolve(p, seg)
  mlib.smoothShade(ob, 36)
  return ob
}

const LEG_PROF: Vec2[] = [
  [0.0, 0.006],
  [0.007, 0.0115],
  [0.016, 0.0152],
  [0.03, 0.0172],
  [0.048, 0.0158],
  [0.075, 0.0138],
  [0.105, 0.0148],
  [0.19, 0.014],
  [0.31, 0.015],
  [0.44, 0.0168],
  [0.575, 0.0192],
  [0.675, 0.0222],
  [0.745, 0.025],
  [0.8, 0.026],
  [0.85, 0.0238],
  [0.888, 0.0198],
  [0.925, 0.019],
  [0.952, 0.0216],
  [0.978, 0.023],
  [1.0, 0.0208],
]
const STR_PROF: Vec2[] = [
  [0.0, 0.0125],
  [0.06, 0.0115],
  [0.3, 0.01],
  [0.395, 0.0112],
  [0.43, 0.015],
  [0.47, 0.0165],
  [0.53, 0.0165],
  [0.57, 0.015],
  [0.605, 0.0112],
  [0.7, 0.01],
  [0.94, 0.0115],
  [1.0, 0.0125],
]
const SPN_PROF: Vec2[] = [
  [0.0, 0.011],
  [0.07, 0.0125],
  [0.17, 0.0115],
  [0.3, 0.0092],
  [0.5, 0.0078],
  [0.72, 0.0068],
  [0.9, 0.0062],
  [1.0, 0.0058],
]

function seatOutline(sw: number, sd: number, n = 72): Vec2[] {
  const pts: Vec2[] = []
  for (let i = 0; i < n; i++) {
    const a = (Math.PI * 2 * i) / n
    const c = Math.cos(a)
    const s = Math.sin(a)
    const k = s >= 0 ? 2.35 : 3.6
    const taper = s >= 0 ? 1.0 : 1.0 - 0.075 * (-s) ** 1.4
    const x = (sw / 2) * taper * Math.sign(c) * Math.abs(c) ** (2.0 / k)
    const y = (sd / 2) * Math.sign(s) * Math.abs(s) ** (2.0 / k)
    pts.push([x, y])
  }
  return pts
}

function windsorChair(w: World, cx: number, cy: number, rot: number, M: MatSet, seatH = 0.455, cushionOn = true): void {
  const parts: MeshData[] = []
  const sw = 0.425
  const sd = 0.395
  const st = 0.033
  const ztop = seatH
  const zbot = seatH - st

  // ---------------------------------------------------------------- seat
  const out = seatOutline(sw, sd)
  const seatRings: Vec3[][] = (
    [
      [-st, 0.9],
      [-st + 0.009, 0.965],
      [-0.013, 1.0],
      [0.0, 1.0],
    ] as [number, number][]
  ).map(([dz, s]) => out.map(([x, y]) => [x * s, y * s, ztop + dz] as Vec3))
  const seat = mlib.loft(seatRings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(seat, 38)
  parts.push(seat)

  // ---------------------------------------------------------------- legs
  const RAKE_X = rad(7.5)
  const RAKE_Y = rad(8.0)
  const tops = new Map<string, Vec3>()
  const feet = new Map<string, Vec3>()
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const top: Vec3 = [sx * (sw / 2 - 0.068), sy * (sd / 2 - 0.062), zbot + 0.008]
    const foot: Vec3 = [top[0] + sx * top[2] * Math.tan(RAKE_X), top[1] + sy * top[2] * Math.tan(RAKE_Y), 0.0]
    tops.set(`${sx}_${sy}`, top)
    feet.set(`${sx}_${sy}`, foot)
    const ln = Math.hypot(top[0] - foot[0], top[1] - foot[1], top[2] - foot[2])
    const lg = turned(ln, LEG_PROF, 16)
    aim(lg, foot, top)
    parts.push(lg)
  }
  const onLeg = (key: string, z: number): Vec3 => {
    const a = feet.get(key)!
    const b2 = tops.get(key)!
    const t = (z - a[2]) / (b2[2] - a[2])
    return [a[0] + (b2[0] - a[0]) * t, a[1] + (b2[1] - a[1]) * t, z]
  }

  // ------------------------------------------------------- H stretcher
  const ZS = 0.19
  const mids: Vec3[] = []
  for (const sx of [-1, 1]) {
    const a = onLeg(`${sx}_1`, ZS)
    const b2 = onLeg(`${sx}_-1`, ZS)
    const dv: Vec3 = [b2[0] - a[0], b2[1] - a[1], b2[2] - a[2]]
    const dl = Math.hypot(...dv)
    const d: Vec3 = [(dv[0] / dl) * 0.014, (dv[1] / dl) * 0.014, (dv[2] / dl) * 0.014]
    const a2: Vec3 = [a[0] - d[0], a[1] - d[1], a[2] - d[2]]
    const b3: Vec3 = [b2[0] + d[0], b2[1] + d[1], b2[2] + d[2]]
    const sr = turned(Math.hypot(b3[0] - a2[0], b3[1] - a2[1], b3[2] - a2[2]), STR_PROF, 12)
    aim(sr, a2, b3)
    parts.push(sr)
    mids.push([(a[0] + b2[0]) * 0.5, (a[1] + b2[1]) * 0.5, (a[2] + b2[2]) * 0.5])
  }
  {
    const dv: Vec3 = [mids[1][0] - mids[0][0], mids[1][1] - mids[0][1], mids[1][2] - mids[0][2]]
    const dl = Math.hypot(...dv)
    const d: Vec3 = [(dv[0] / dl) * 0.012, (dv[1] / dl) * 0.012, (dv[2] / dl) * 0.012]
    const cr = turned(dl + 0.024, STR_PROF, 12)
    aim(cr, [mids[0][0] - d[0], mids[0][1] - d[1], mids[0][2] - d[2]], [mids[1][0] + d[0], mids[1][1] + d[1], mids[1][2] + d[2]])
    parts.push(cr)
  }

  // ------------------------------------------------------------- hoop
  const BASE_HW = 0.176
  const ARCH_HW = 0.166
  const ARCH_H = 0.205
  const POST_H = 0.36
  const LEAN = rad(9.5)
  const BASE_Y = -sd / 2 + 0.048
  const hoopPt = (u: number, v: number): Vec3 => [u, BASE_Y - v * Math.sin(LEAN), ztop - 0.014 + v * Math.cos(LEAN)]
  const path: Vec3[] = []
  for (let i = 0; i < 9; i++) {
    const t = i / 8.0
    path.push(hoopPt(-BASE_HW + (BASE_HW - ARCH_HW) * t, POST_H * t))
  }
  for (let i = 1; i < 30; i++) {
    const th = (Math.PI * i) / 30.0
    path.push(hoopPt(-ARCH_HW * Math.cos(th), POST_H + ARCH_H * Math.sin(th)))
  }
  for (let i = 0; i < 9; i++) {
    const t = 1.0 - i / 8.0
    path.push(hoopPt(BASE_HW - (BASE_HW - ARCH_HW) * t, POST_H * t))
  }
  const hoop = mlib.tubeAlong(path, mlib.roundedRect(0.03, 0.023, 0.009, 3))
  mlib.smoothShade(hoop, 40)
  parts.push(hoop)

  // ---------------------------------------------------------- spindles
  const NSP = 5
  for (let k = 0; k < NSP; k++) {
    const f = (k - (NSP - 1) / 2.0) / ((NSP - 1) / 2.0)
    const uTop = f * ARCH_HW * 0.74
    const th = Math.acos(Math.max(-1.0, Math.min(1.0, -uTop / ARCH_HW)))
    const vTop = POST_H + ARCH_H * Math.sin(th)
    let tp = hoopPt(uTop, vTop)
    tp = [tp[0], tp[1] + 0.011 * Math.cos(LEAN), tp[2] - 0.011 * Math.sin(LEAN)]
    const bs: Vec3 = [f * BASE_HW * 0.6, BASE_Y + 0.004, ztop - 0.012]
    const ln = Math.hypot(tp[0] - bs[0], tp[1] - bs[1], tp[2] - bs[2])
    const sp = turned(ln, SPN_PROF, 10)
    aim(sp, bs, tp)
    parts.push(sp)
  }

  const ob = mlib.join(parts)
  mlib.rotateZ(ob, rot)
  mlib.translate(ob, [cx, cy, 0.0])
  w.add(ob, M.chair)
  w.obb(cx, cy, 0.26, 0.26, rot)
  if (cushionOn) {
    const pts = seatOutline(sw - 0.01, sd - 0.004, 56)
    const z0 = ztop + 0.003
    const sag = (y: number): number => {
      const f = Math.max(0.0, Math.min(1.0, (y / (sd * 0.5) - 0.1) / 0.9))
      return f * f
    }
    const rings: Vec3[][] = (
      [
        [0.0, 0.94, 0.3],
        [0.013, 1.005, 0.85],
        [0.04, 1.025, 1.0],
        [0.068, 1.0, 0.8],
        [0.081, 0.92, 0.45],
      ] as [number, number, number][]
    ).map(([dz, s, dp]) => pts.map(([x, y]) => [x * s, y * s, z0 + dz - 0.026 * dp * sag(y)] as Vec3))
    const cu = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
    mlib.smoothShade(cu, 50)
    mlib.rotateZ(cu, rot)
    mlib.translate(cu, [cx, cy, 0.0])
    w.add(cu, M.tapestry)
    const pipe = mlib.tubeAlong(
      [...pts.map(([x, y]) => [x * 1.028, y * 1.028, z0 + 0.04 - 0.026 * sag(y)] as Vec3)],
      mlib.circle(0.0055, 7),
      { closePath: true },
    )
    mlib.smoothShade(pipe, 40)
    mlib.rotateZ(pipe, rot)
    mlib.translate(pipe, [cx, cy, 0.0])
    w.add(pipe, M.piping)
  }
}

function bentwoodChair(w: World, cx: number, cy: number, rot: number, M: MatSet, seatH = 0.455): void {
  const parts: MeshData[] = []
  const r = 0.205
  const st = mlib.revolve(
    [
      [0.0, 0.0],
      [r - 0.012, 0.0],
      [r, 0.01],
      [r, 0.026],
      [r - 0.014, 0.034],
      [r - 0.07, 0.03],
      [0.0, 0.026],
    ],
    44,
  )
  mlib.smoothShade(st, 34)
  mlib.translate(st, [0, 0, seatH - 0.034])
  parts.push(st)
  const curl = (p0: Vec3, sign: number, drop: number): Vec3[] => {
    const out: Vec3[] = []
    for (let j = 1; j <= 6; j++) {
      const u = j / 6
      out.push([p0[0] + sign * 0.012 * u, p0[1] + 0.02 * u, p0[2] - drop * u ** 0.85])
    }
    return out
  }
  const pts: Vec3[] = []
  const n = 48
  for (let i = 0; i <= n; i++) {
    const a = Math.PI * (1.0 - i / n)
    const s = Math.sin(a)
    pts.push([r * 0.92 * Math.cos(a), 0.088 - 0.285 * s ** 1.4, seatH + 0.455 * s ** 0.55])
  }
  const full: Vec3[] = [...curl(pts[0], -1, 0.08).reverse(), ...pts, ...curl(pts[pts.length - 1], 1, 0.08)]
  parts.push(mlib.tubeAlong(full, mlib.circle(0.0135, 14)))
  const innerPts: Vec3[] = []
  const n2 = 34
  for (let i = 0; i <= n2; i++) {
    const a = Math.PI * (1.0 - i / n2)
    const s = Math.sin(a)
    innerPts.push([r * 0.56 * Math.cos(a), 0.058 - 0.19 * s ** 1.4, seatH + 0.058 + 0.29 * s ** 0.62])
  }
  const inner: Vec3[] = [...curl(innerPts[0], -1, 0.128).reverse(), ...innerPts, ...curl(innerPts[innerPts.length - 1], 1, 0.128)]
  parts.push(mlib.tubeAlong(inner, mlib.circle(0.0105, 12)))
  for (let k = 0; k < 4; k++) {
    const a = (Math.PI * 2 * k) / 4 + Math.PI / 4
    parts.push(
      mlib.tubeAlong(
        [
          [r * 0.72 * Math.cos(a), r * 0.72 * Math.sin(a), seatH - 0.03],
          [r * 0.95 * Math.cos(a), r * 0.95 * Math.sin(a), seatH * 0.55],
          [r * 1.18 * Math.cos(a), r * 1.18 * Math.sin(a), 0.0],
        ],
        mlib.circle(0.0145, 12),
      ),
    )
  }
  parts.push(
    mlib.tubeAlong(
      Array.from({ length: 36 }, (_, i) => {
        const a = (i * Math.PI * 2) / 36
        return [r * Math.cos(a), r * Math.sin(a), 0.2] as Vec3
      }),
      mlib.circle(0.0105, 10),
      { closePath: true },
    ),
  )
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 40)
  mlib.rotateZ(ob, rot)
  mlib.translate(ob, [cx, cy, 0.0])
  w.add(ob, M.bentwood)
  w.obb(cx, cy, 0.25, 0.25, rot)
}

export function build(w: World): MatSet {
  const M = mkMats()
  const [cx, cy] = L.TABLE_C
  roundTable(w, cx, cy, M)
  windsorChair(w, cx - 0.8, cy - 0.1, rad(-82), M)
  windsorChair(w, cx + 0.22, cy - 0.78, rad(14), M)
  bentwoodChair(w, cx + 0.78, cy + 0.22, rad(108), M)
  windsorChair(w, cx - 0.18, cy + 0.8, rad(190), M, 0.455, false)
  // a bowl of fruit + a couple of mugs on the glass top
  const pool = P.palette(21, 8)
  const bw = P.bowl(0.115, 0.062, mats.paint('bowl_white', 'F0EBDC', { rough: 0.14, coat: 0.6 }))
  for (const o of bw) {
    mlib.translate(o.md, [cx + 0.06, cy + 0.05, 0.766])
    w.add(o.md, o.mat)
  }
  const rng = new PyRandom(3)
  const fm = mats.paint('fruit_orange', 'D9721F', { rough: 0.42, coat: 0.2 })
  for (let i = 0; i < 5; i++) {
    const a = (Math.PI * 2 * i) / 5
    const fr = mlib.revolve(
      [
        [0.0, -0.031],
        [0.024, -0.02],
        [0.031, 0.0],
        [0.024, 0.02],
        [0.0, 0.031],
      ],
      16,
    )
    mlib.smoothShade(fr, 40)
    mlib.translate(fr, [cx + 0.06 + 0.042 * Math.cos(a), cy + 0.05 + 0.042 * Math.sin(a), 0.828])
    w.add(fr, fm)
  }
  const mugPos: [number, number][] = [
    [-0.3, 0.16],
    [-0.24, -0.14],
  ]
  for (const [dx, dy] of mugPos) {
    for (const o of P.cup(0.042, 0.088, rng.choice(pool))) {
      mlib.rotateZ(o.md, rng.uniform(0, 6.2))
      mlib.translate(o.md, [cx + dx, cy + dy, 0.764])
      w.add(o.md, o.mat)
    }
  }
  return M
}
