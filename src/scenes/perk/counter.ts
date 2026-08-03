/** The service counter, the back bar and everything standing on them, from
 * f_counter.py: fielded panels and pilasters on the faceted island, the
 * bullnosed stone tops, the lever espresso machine, the brass urn, the till,
 * the chalk menu and the retail stock. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import type { World } from '../../core/world'
import * as G from './geo'
import * as L from './layout'
import * as M from './materials'
import { textMesh } from './text'

const CHALK_Y: [number, number] = [5.35, 7.05]
const CHALK_Z: [number, number] = [1.55, 2.66]
const CASE_Y: [number, number] = [6.16, 7.1]
const CASE_Z: [number, number, number] = [0.18, 0.43, 0.68]

function mats(): void {
  M.wood('cw_oak', { light: '7A5228', dark: '341C0C', ring: 24, scale: 1.2 })
  M.wood('cw_oak_dk', { light: '5A3A1C', dark: '24130A', ring: 22, scale: 1 })
  M.marble('cw_marble', { base: '8E7C63', vein: '4A3826', vein2: 'B4A484', scale: 2.6 })
  M.metal('cw_brass', 'B08A32', { rough: 0.24, tarnish: 0.42 })
  M.chrome('cw_chrome', 0.07)
  M.metal('cw_steel', 'B4B8BA', { rough: 0.3, patina: '4A4E50', tarnish: 0.25 })
  M.flat('cw_black', '15161A', 0.34)
  M.chalkboard('cw_chalk', '17281F')
  M.glass('cw_glass', 'EEF4F0', 0.02)
  M.paint('cw_green', L.GREEN_IRON, { rough: 0.34, coat: 0.15 })
  M.flat('cw_card', 'C8B48A', 0.72)
}

// ------------------------------------------------------------------ joinery

/** One fielded panel between two pilasters: set back, chamfered edge. */
function panelBay(p0: Vec2, p1: Vec2, nx: Vec2, z0: number, z1: number, depth = 0.022, bead = 0.02): MeshData {
  let ux = p1[0] - p0[0]
  let uy = p1[1] - p0[1]
  const ll = Math.hypot(ux, uy) || 1
  ux /= ll
  uy /= ll
  const levels: [number, number][] = [
    [0, 0],
    [bead, -depth * 0.55],
    [bead * 1.9, -depth],
  ]
  const rings: Vec3[][] = []
  for (const [ins, dp] of levels) {
    const a: Vec2 = [p0[0] + ux * ins + nx[0] * dp, p0[1] + uy * ins + nx[1] * dp]
    const b: Vec2 = [p1[0] - ux * ins + nx[0] * dp, p1[1] - uy * ins + nx[1] * dp]
    rings.push([
      [a[0], a[1], z0 + ins],
      [b[0], b[1], z0 + ins],
      [b[0], b[1], z1 - ins],
      [a[0], a[1], z1 - ins],
    ])
  }
  return mlib.loft(rings, { closeV: true, capEnd: true })
}

/** Stone slab with a bullnosed lip: a true half-round edge. */
function bullnoseTop(poly: Vec2[], z0: number, z1: number, over = 0.045): MeshData {
  const levels: [number, number][] = [
    [-0.004, 0],
    [over * 0.72, 0.006],
    [over, (z1 - z0) * 0.5],
    [over * 0.72, z1 - z0 - 0.006],
    [-0.004, z1 - z0],
  ]
  const rings = levels.map(([o, dz]) => G.polyOffset(poly, o).map(([x, y]) => [x, y, z0 + dz] as Vec3))
  const md = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(md, 34)
  return md
}

// ------------------------------------------------------------ service counter

function serviceCounter(world: World): void {
  const wood: MeshData[] = []
  const stone: MeshData[] = []
  const front = [...L.SERVE_FRONT]
  const back: Vec2[] = [...front].reverse().map((p) => [L.SERVE_BACK, p[1]])
  const poly = G.ccw([...front, ...back])
  const H = L.SERVE_H

  const pl = mlib.prism(G.polyOffset(poly, -0.022), 0, 0.115)
  mlib.bevel(pl, 0.006, 2)
  wood.push(pl)

  // the retail case is hollowed out of the counter's front: two carcass
  // prisms with the recess between them and a back slab closing it
  const [CY0, CY1] = CASE_Y
  const CD = 0.285
  const CX = 2.07
  const body = G.polyOffset(poly, -0.03)
  const BK = L.SERVE_BACK + 0.03
  const ys = body.map((p) => p[1])
  const zt = H - 0.062
  const spans: [string, number, number][] = [
    ['n', CY1, Math.max(...ys)],
    ['s', Math.min(...ys), CY0],
  ]
  for (const [, y0, y1] of spans) {
    const sub = body.filter((p) => p[1] >= y0 - 1e-6 && p[1] <= y1 + 1e-6)
    if (sub.length < 3) continue
    const closed = G.ccw([...sub, [CX - 0.03, y1], [BK, y1], [BK, y0], [CX - 0.03, y0]])
    wood.push(mlib.prism(closed, 0.1, zt))
  }
  wood.push(
    mlib.prism(
      G.ccw([
        [BK, CY0],
        [CX - CD, CY0],
        [CX - CD, CY1],
        [BK, CY1],
      ]),
      0.1,
      zt,
    ),
  )
  const caseBoxes: [number, number, number, number, number, number][] = [
    [CX - CD, CY0, 0.1, CX, CY0 + 0.03, zt],
    [CX - CD, CY1 - 0.03, 0.1, CX, CY1, zt],
    [CX - CD, CY0, zt - 0.032, CX, CY1, zt],
    [CX - CD, CY0, 0.1, CX, CY1, 0.135],
  ]
  for (const [a, b, c, d, e, f] of caseBoxes) {
    const p = mlib.box(a, b, c, d, e, f)
    mlib.bevel(p, 0.004, 2)
    wood.push(p)
  }
  for (const z of CASE_Z) {
    const sl = mlib.box(CX - CD + 0.004, CY0 + 0.03, z, CX - 0.012, CY1 - 0.03, z + 0.02)
    mlib.bevel(sl, 0.003, 2)
    wood.push(sl)
  }

  // walk the front line: a pilaster every ~620 mm, a fielded panel between
  const seg: [Vec2, Vec2, number, number][] = []
  for (let i = 0; i < front.length - 1; i++) {
    const a = front[i]
    const b = front[i + 1]
    const ln = Math.hypot(b[0] - a[0], b[1] - a[1])
    const n = Math.max(1, Math.round(ln / 0.62))
    for (let k = 0; k < n; k++) seg.push([a, b, k / n, (k + 1) / n])
  }
  seg.forEach(([a, b, t0, t1], idx) => {
    let ux = b[0] - a[0]
    let uy = b[1] - a[1]
    const dd = Math.hypot(ux, uy) || 1
    ux /= dd
    uy /= dd
    const nx: Vec2 = [uy, -ux]
    const p0: Vec2 = [a[0] + ux * dd * t0, a[1] + uy * dd * t0]
    const p1: Vec2 = [a[0] + ux * dd * t1, a[1] + uy * dd * t1]
    // no panel and no pilasters where the display case is let in
    const mid = (p0[1] + p1[1]) * 0.5
    if (mid > CASE_Y[0] - 0.12 && mid < CASE_Y[1] + 0.12 && Math.abs(p0[0] - 2.07) < 0.02) return
    wood.push(
      panelBay(
        [p0[0] + ux * 0.055, p0[1] + uy * 0.055],
        [p1[0] - ux * 0.055, p1[1] - uy * 0.055],
        nx,
        0.15,
        H - 0.115,
        0.026,
      ),
    )
    for (const [q, end] of [
      [p0, 0],
      [p1, 1],
    ] as [Vec2, number][]) {
      if (end === 1 && idx !== seg.length - 1) continue
      const pil = mlib.prism(
        G.ccw([
          [q[0] - ux * 0.042 + nx[0] * 0.03, q[1] - uy * 0.042 + nx[1] * 0.03],
          [q[0] + ux * 0.042 + nx[0] * 0.03, q[1] + uy * 0.042 + nx[1] * 0.03],
          [q[0] + ux * 0.042 - nx[0] * 0.02, q[1] + uy * 0.042 - nx[1] * 0.02],
          [q[0] - ux * 0.042 - nx[0] * 0.02, q[1] - uy * 0.042 - nx[1] * 0.02],
        ]),
        0.1,
        H - 0.07,
      )
      mlib.bevel(pil, 0.004, 2)
      wood.push(pil)
    }
  })

  stone.push(bullnoseTop(poly, H - 0.055, H, 0.048))
  world.add(mlib.join(wood), M.get('cw_oak'))
  world.add(mlib.join(stone), M.get('cw_marble'))

  // collision: back body, the two straight front strips, the two diagonals
  world.box2(L.SERVE_BACK, 6, 2, 10.04, 0, L.SERVE_H)
  world.box2(2, 6, 2.07, 7.18, 0, L.SERVE_H)
  world.box2(2, 7.64, 2.5, 8.86, 0, L.SERVE_H)
  const diagObb = (a: Vec2, b: Vec2): void => {
    const dx = b[0] - a[0]
    const dy = b[1] - a[1]
    const len = Math.hypot(dx, dy)
    world.obb((a[0] + b[0]) / 2 - (dy / len) * 0.04, (a[1] + b[1]) / 2 + (dx / len) * 0.04, len / 2, 0.05, Math.atan2(dy, dx), 0, L.SERVE_H)
  }
  diagObb([2, 9.36], [2.5, 8.86])
  diagObb([2.5, 7.64], [2.07, 7.18])
}

// --------------------------------------------------------------- back bar

function backBar(world: World): void {
  const wood: MeshData[] = []
  const stone: MeshData[] = []
  const glassP: MeshData[] = []
  const brassP: MeshData[] = []
  const y0 = L.BACK_TALL_S[1]
  const y1 = L.BACK_TALL_N[0]
  const D = L.BACK_D
  const H = L.BACK_H

  wood.push(
    mlib.prism(
      [
        [0, y0],
        [D, y0],
        [D, y1],
        [0, y1],
      ],
      0.095,
      H - 0.045,
    ),
  )
  const plinth = mlib.prism(
    [
      [0, y0],
      [D - 0.045, y0],
      [D - 0.045, y1],
      [0, y1],
    ],
    0,
    0.1,
  )
  mlib.bevel(plinth, 0.005, 2)
  wood.push(plinth)
  const n = Math.max(1, Math.round((y1 - y0) / 0.58))
  const pitch = (y1 - y0) / n
  for (let i = 0; i < n; i++) {
    const yy = y0 + i * pitch
    wood.push(panelBay([D, yy + 0.022], [D, yy + pitch - 0.022], [1, 0], 0.115, H - 0.06, 0.02))
    const kn = mlib.revolve(
      [
        [0, 0],
        [0.012, 0.004],
        [0.016, 0.016],
        [0.01, 0.026],
        [0, 0.028],
      ],
      12,
    )
    mlib.rotY(kn, Math.PI / 2)
    mlib.translate(kn, [D + 0.004, yy + pitch * 0.5, H - 0.2])
    mlib.smoothShade(kn, 40)
    brassP.push(kn)
  }
  stone.push(
    bullnoseTop(
      [
        [0, y0],
        [D + 0.02, y0],
        [D + 0.02, y1],
        [0, y1],
      ],
      H - 0.045,
      H,
      0.03,
    ),
  )

  // open shelves above, starting north of the menu board
  const y0s = CHALK_Y[1] + 0.3
  const shelfZ = [1.36, 1.72, 2.08]
  for (const z of shelfZ) {
    const sl = mlib.box(-0.005, y0s + 0.02, z, 0.3, y1 - 0.02, z + 0.026)
    mlib.bevel(sl, 0.004, 2)
    wood.push(sl)
    for (let i = 0; i < Math.floor((y1 - y0s) / 0.92) + 1; i++) {
      const yy = Math.min(y1 - 0.1, y0s + 0.12 + i * 0.92)
      wood.push(
        mlib.prismXZ(
          [
            [-0.005, z],
            [0.275, z],
            [-0.005, z - 0.16],
          ],
          yy,
          yy + 0.022,
        ),
      )
    }
  }

  // the tall dressers at each end
  for (const [a, bq] of [L.BACK_TALL_S, L.BACK_TALL_N]) {
    wood.push(
      mlib.prism(
        [
          [0, a],
          [0.46, a],
          [0.46, bq],
          [0, bq],
        ],
        0.095,
        L.BACK_TALL_H,
      ),
    )
    wood.push(
      mlib.prism(
        [
          [0, a],
          [0.42, a],
          [0.42, bq],
          [0, bq],
        ],
        0,
        0.1,
      ),
    )
    const cor = mlib.prism(
      [
        [0, a - 0.018],
        [0.5, a - 0.018],
        [0.5, bq + 0.018],
        [0, bq + 0.018],
      ],
      L.BACK_TALL_H,
      L.BACK_TALL_H + 0.055,
    )
    mlib.bevel(cor, 0.008, 2)
    wood.push(cor)
    for (const k of [0, 1]) {
      const z0 = k ? 1.15 : 0.16
      const z1 = k ? L.BACK_TALL_H - 0.09 : 1.05
      wood.push(panelBay([0.46, a + 0.03], [0.46, bq - 0.03], [1, 0], z0, z1, 0.02))
      if (k) glassP.push(mlib.box(0.452, a + 0.075, z0 + 0.045, 0.462, bq - 0.075, z1 - 0.045))
    }
    for (const i of [0, 1]) {
      wood.push(mlib.box(0.02, a + 0.02, 1.3 + i * 0.34, 0.44, bq - 0.02, 1.32 + i * 0.34))
    }
  }

  world.add(mlib.join(wood), M.get('cw_oak_dk'))
  world.add(mlib.join(stone), M.get('cw_marble'))
  world.add(mlib.join(glassP), M.get('cw_glass'))
  world.add(mlib.join(brassP), M.get('cw_brass'))
  world.box2(0, L.BACK_TALL_S[0] - 0.02, 0.58, L.BACK_TALL_N[1] + 0.02)
}

// ------------------------------------------------------------------ machines

/** Lever espresso machine: chrome body, raised hood, dark cheeks, two group
 * heads with portafilters, wands, gauges, a drip grid and warming cups. */
function espresso(world: World, cx: number, cy: number, cz: number, rot = 0): void {
  const steel: MeshData[] = []
  const blk: MeshData[] = []
  const brs: MeshData[] = []
  const wht: MeshData[] = []
  const W = 0.72
  const D = 0.46
  const pl = mlib.prism(mlib.roundedRect(W - 0.03, D - 0.03, 0.02, 4), 0, 0.055)
  mlib.bevel(pl, 0.006, 2)
  blk.push(pl)
  const bodyMd = mlib.prism(mlib.roundedRect(W, D, 0.055, 5), 0.05, 0.3)
  mlib.bevel(bodyMd, 0.012, 2)
  steel.push(bodyMd)
  const hood = mlib.prism(mlib.roundedRect(W - 0.1, D - 0.07, 0.045, 5), 0.292, 0.392)
  mlib.bevel(hood, 0.014, 2)
  steel.push(hood)
  const dome = mlib.revolve(
    [
      [0, 0.386],
      [0.24, 0.382],
      [0.255, 0.402],
      [0.225, 0.452],
      [0.14, 0.486],
      [0, 0.496],
    ],
    28,
  )
  mlib.scaleMesh(dome, [1.28, 0.8, 1])
  mlib.smoothShade(dome, 40)
  steel.push(dome)
  const fin = mlib.revolve(
    [
      [0, 0.49],
      [0.022, 0.494],
      [0.026, 0.512],
      [0.014, 0.526],
      [0, 0.53],
    ],
    14,
  )
  mlib.smoothShade(fin, 40)
  brs.push(fin)
  for (const s of [-1, 1]) {
    const ck = mlib.prism(mlib.roundedRect(0.055, D - 0.1, 0.02, 4), 0.085, 0.272)
    mlib.translate(ck, [s * (W / 2 - 0.02), 0, 0])
    mlib.bevel(ck, 0.005, 2)
    blk.push(ck)
    const gh = mlib.revolve(
      [
        [0, 0],
        [0.046, 0],
        [0.042, 0.048],
        [0.056, 0.062],
        [0.056, 0.082],
        [0.03, 0.094],
        [0, 0.096],
      ],
      18,
    )
    mlib.translate(gh, [s * 0.19, -D / 2 - 0.03, 0.098])
    mlib.smoothShade(gh, 40)
    steel.push(gh)
    const pf = mlib.revolve(
      [
        [0, 0],
        [0.04, 0.004],
        [0.042, 0.026],
        [0.03, 0.03],
        [0.022, 0.012],
        [0, 0.01],
      ],
      16,
    )
    mlib.translate(pf, [s * 0.19, -D / 2 - 0.03, 0.07])
    steel.push(pf)
    const hnd = mlib.tubeAlong(
      [
        [s * 0.19, -D / 2 - 0.062, 0.076],
        [s * 0.19, -D / 2 - 0.15, 0.062],
      ],
      mlib.circle(0.014, 10),
    )
    mlib.smoothShade(hnd, 40)
    blk.push(hnd)
    const wd = mlib.tubeAlong(
      [
        [s * (W / 2 - 0.035), -0.09, 0.235],
        [s * (W / 2 - 0.012), -0.2, 0.185],
        [s * (W / 2 - 0.01), -0.235, 0.095],
      ],
      mlib.circle(0.008, 8),
    )
    mlib.smoothShade(wd, 40)
    steel.push(wd)
    const kn = mlib.revolve(
      [
        [0, 0],
        [0.026, 0.004],
        [0.024, 0.022],
        [0, 0.026],
      ],
      12,
    )
    mlib.rotX(kn, -Math.PI / 2)
    mlib.translate(kn, [s * (W / 2 - 0.045), -D / 2 - 0.006, 0.235])
    blk.push(kn)
    const g = mlib.revolve(
      [
        [0, 0],
        [0.036, 0],
        [0.04, 0.006],
        [0.036, 0.014],
        [0, 0.015],
      ],
      18,
    )
    mlib.rotX(g, -Math.PI / 2)
    mlib.translate(g, [s * 0.085, -D / 2 - 0.004, 0.215])
    brs.push(g)
    const gf = mlib.revolve(
      [
        [0, 0],
        [0.03, 0],
        [0.03, 0.004],
        [0, 0.004],
      ],
      18,
    )
    mlib.rotX(gf, -Math.PI / 2)
    mlib.translate(gf, [s * 0.085, -D / 2 - 0.014, 0.215])
    wht.push(gf)
  }
  for (let i = 0; i < 9; i++) {
    steel.push(mlib.box(-0.3 + i * 0.0725, -D / 2 - 0.02, 0.066, -0.276 + i * 0.0725, -0.06, 0.074))
  }
  for (let i = 0; i < 5; i++) {
    const cp = mlib.revolve(
      [
        [0, 0],
        [0.036, 0.002],
        [0.033, 0.052],
        [0.036, 0.056],
        [0.031, 0.056],
        [0.028, 0.006],
        [0, 0.004],
      ],
      14,
    )
    mlib.smoothShade(cp, 44)
    mlib.translate(cp, [-0.24 + i * 0.12, -0.02 - 0.055 * (i % 2), 0.392])
    wht.push(cp)
  }
  const groups: [MeshData[], THREE.Material][] = [
    [steel, M.get('cw_chrome')],
    [blk, M.get('cw_black')],
    [wht, M.get('cw_card')],
    [brs, M.get('cw_brass')],
  ]
  for (const [list, mat] of groups) {
    const md = mlib.join(list)
    if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
    mlib.translate(md, [cx, cy, cz])
    world.add(md, mat)
  }
}

/** The big brass coffee urn: body, legs, spigot. */
function urn(world: World, cx: number, cy: number, cz: number, rot = 0): void {
  const brs: MeshData[] = []
  const blk: MeshData[] = []
  const bodyMd = mlib.revolve(
    [
      [0, 0],
      [0.135, 0],
      [0.138, 0.03],
      [0.118, 0.055],
      [0.15, 0.115],
      [0.163, 0.255],
      [0.15, 0.4],
      [0.128, 0.47],
      [0.14, 0.492],
      [0.12, 0.512],
      [0.07, 0.545],
      [0.086, 0.575],
      [0.052, 0.6],
      [0.03, 0.64],
      [0.044, 0.665],
      [0, 0.69],
    ],
    32,
  )
  mlib.smoothShade(bodyMd, 42)
  brs.push(bodyMd)
  for (let i = 0; i < 3; i++) {
    const a = ((20 + i * 120) * Math.PI) / 180
    const lg = mlib.revolve(
      [
        [0, 0],
        [0.022, 0.004],
        [0.016, 0.04],
        [0.024, 0.07],
        [0, 0.075],
      ],
      12,
    )
    mlib.translate(lg, [0.115 * Math.cos(a), 0.115 * Math.sin(a), -0.075])
    brs.push(lg)
  }
  const spig = mlib.tubeAlong(
    [
      [0.14, 0, 0.16],
      [0.215, 0, 0.155],
      [0.222, 0, 0.105],
    ],
    mlib.circle(0.013, 10),
  )
  mlib.smoothShade(spig, 40)
  brs.push(spig)
  const tap = mlib.revolve(
    [
      [0, 0],
      [0.03, 0.006],
      [0.024, 0.016],
      [0, 0.018],
    ],
    12,
  )
  mlib.rotY(tap, Math.PI / 2)
  mlib.translate(tap, [0.222, 0, 0.175])
  blk.push(tap)
  for (const [list, mat] of [
    [brs, M.get('cw_brass')],
    [blk, M.get('cw_black')],
  ] as [MeshData[], THREE.Material][]) {
    const md = mlib.join(list)
    if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
    mlib.translate(md, [cx, cy, cz + 0.075])
    world.add(md, mat)
  }
}

/** Glass bean jar on a small foot. */
function beanCylinder(world: World, cx: number, cy: number, cz: number, h = 0.52, r = 0.085): void {
  const tube = mlib.revolve(
    [
      [r - 0.02, 0.006],
      [r - 0.004, 0.014],
      [r, 0.026],
      [r, h - 0.02],
      [r - 0.006, h],
      [r - 0.012, h],
      [r - 0.012, 0.03],
      [r - 0.02, 0.018],
      [r - 0.02, 0.006],
    ],
    24,
  )
  mlib.smoothShade(tube, 42)
  const beans = mlib.revolve(
    [
      [0, 0],
      [r - 0.014, 0],
      [r - 0.014, h * 0.78],
      [0, h * 0.8],
    ],
    24,
  )
  mlib.smoothShade(beans, 40)
  const cap = mlib.revolve(
    [
      [0, h],
      [r + 0.006, h],
      [r + 0.004, h + 0.03],
      [0, h + 0.045],
    ],
    24,
  )
  const beansMat = M.wood('cw_beans', { light: '6B3A18', dark: '2A1408', ring: 180, scale: 0.06 })
  for (const [md, mat] of [
    [tube, M.get('cw_glass')],
    [beans, beansMat],
    [cap, M.get('cw_brass')],
  ] as [MeshData, THREE.Material][]) {
    mlib.translate(md, [cx, cy, cz])
    world.add(md, mat)
  }
}

/** Footed glass cake stand with a domed cover. */
function cakeDome(world: World, cx: number, cy: number, cz: number, r = 0.17): void {
  const glassMat = M.get('cw_glass')
  const stand = mlib.revolve(
    [
      [0, 0],
      [0.062, 0.004],
      [0.058, 0.014],
      [0.02, 0.03],
      [0.017, 0.075],
      [0.03, 0.092],
      [r, 0.1],
      [r, 0.112],
      [0, 0.112],
    ],
    28,
  )
  mlib.smoothShade(stand, 40)
  const domeProf: Vec2[] = [
    [r - 0.002, 0.112],
    [r - 0.002, 0.15],
  ]
  for (let a = 0; a <= 90; a += 9) {
    domeProf.push([(r - 0.004) * Math.cos((a * Math.PI) / 180), 0.15 + r * 1.05 * Math.sin((a * Math.PI) / 180)])
  }
  const dome = mlib.revolve(domeProf, 28, { capStart: false, capEnd: false })
  mlib.solidify(dome, 0.004)
  mlib.smoothShade(dome, 44)
  const knob = mlib.revolve(
    [
      [0, 0],
      [0.016, 0.004],
      [0.02, 0.018],
      [0.012, 0.03],
      [0, 0.032],
    ],
    14,
  )
  mlib.translate(knob, [0, 0, 0.15 + r * 1.05])
  const cake = mlib.revolve(
    [
      [0, 0.114],
      [r * 0.66, 0.114],
      [r * 0.64, 0.175],
      [0, 0.18],
    ],
    24,
  )
  const cakeMat = M.paint('cw_cake', 'D9B36A', { rough: 0.62, bump: 0.25 })
  for (const [md, mat] of [
    [stand, glassMat],
    [dome, glassMat],
    [knob, glassMat],
    [cake, cakeMat],
  ] as [MeshData, THREE.Material][]) {
    mlib.translate(md, [cx, cy, cz])
    world.add(md, mat)
  }
}

/** Brass National-style till: moulded plinth, panelled case, cast crest,
 * glazed price window, stepped keyboard, drawer. */
function register(world: World, cx: number, cy: number, cz: number, rot = 0): void {
  const brs: MeshData[] = []
  const blk: MeshData[] = []
  const wht: MeshData[] = []
  const w = 0.34
  const d = 0.36
  const courses: [number, number, number, number, number][] = [
    [w, d, 0, 0.035, 0.01],
    [w - 0.028, d - 0.028, 0.03, 0.052, 0.006],
    [w - 0.046, d - 0.046, 0.048, 0.238, 0.01],
    [w - 0.02, d - 0.02, 0.232, 0.262, 0.008],
  ]
  for (const [sw, sd, z0, z1, bv] of courses) {
    const p = mlib.prism(mlib.roundedRect(sw, sd, 0.026, 4), z0, z1)
    mlib.bevel(p, bv, 2)
    brs.push(p)
  }
  for (const s of [-1, 1]) {
    const pn = mlib.prism(mlib.roundedRect(w - 0.1, d - 0.1, 0.022, 4), 0.072, 0.212)
    mlib.translate(pn, [0, s * 0.006, 0])
    mlib.bevel(pn, 0.005, 2)
    brs.push(pn)
  }
  const neck = mlib.prismXZ(
    [
      [-0.128, 0.258],
      [0.128, 0.258],
      [0.118, 0.296],
      [-0.118, 0.296],
    ],
    -0.072,
    0.072,
  )
  brs.push(neck)
  const arc: Vec2[] = [
    [-0.15, 0.292],
    [0.15, 0.292],
  ]
  for (let t = 6; t < 175; t += 12) {
    arc.push([0.15 * Math.cos((t * Math.PI) / 180), 0.292 + 0.15 * Math.sin((t * Math.PI) / 180) * 0.92])
  }
  brs.push(mlib.prismXZ(G.ccw(arc), -0.052, 0.052))
  for (const s of [-1, 1]) {
    blk.push(
      mlib.prismXZ(
        [
          [-0.112, 0.306],
          [0.112, 0.306],
          [0.112, 0.416],
          [-0.112, 0.416],
        ],
        s * 0.056,
        s * 0.062,
      ),
    )
  }
  wht.push(
    mlib.prismXZ(
      [
        [-0.098, 0.318],
        [0.098, 0.318],
        [0.098, 0.404],
        [-0.098, 0.404],
      ],
      -0.01,
      0.01,
    ),
  )
  const bed = mlib.prismXZ(
    [
      [-0.15, 0.058],
      [0.15, 0.058],
      [0.15, 0.196],
      [-0.15, 0.196],
    ],
    -0.148,
    -0.07,
  )
  brs.push(bed)
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 6; c++) {
      const k = mlib.revolve(
        [
          [0, 0],
          [0.011, 0.003],
          [0.01, 0.014],
          [0, 0.015],
        ],
        10,
      )
      mlib.rotX(k, (-74 * Math.PI) / 180)
      mlib.translate(k, [-0.125 + c * 0.05, -0.152 + r * 0.016, 0.072 + r * 0.03])
      if ((r + c) % 4 === 0) wht.push(k)
      else blk.push(k)
    }
  }
  const dr = mlib.prismXZ(
    [
      [-0.132, 0.056],
      [0.132, 0.056],
      [0.132, 0.122],
      [-0.132, 0.122],
    ],
    -0.196,
    -0.152,
  )
  brs.push(dr)
  const pull = mlib.tubeAlong(
    [
      [-0.052, -0.206, 0.09],
      [0.052, -0.206, 0.09],
    ],
    mlib.circle(0.007, 8),
  )
  mlib.smoothShade(pull, 40)
  brs.push(pull)
  for (const [list, mat] of [
    [brs, M.get('cw_brass')],
    [blk, M.get('cw_black')],
    [wht, M.get('cw_card')],
  ] as [MeshData[], THREE.Material][]) {
    const md = mlib.join(list)
    if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
    mlib.translate(md, [cx, cy, cz])
    world.add(md, mat)
  }
}

/** The menu board over the back bar, slate rebated into a green frame. */
function chalkboard(world: World, x: number, y0: number, y1: number, z0: number, z1: number): void {
  world.add(mlib.box(x + 0.007, y0 + 0.065, z0 + 0.065, x + 0.029, y1 - 0.065, z1 - 0.065), M.get('cw_chalk'))
  const fr: MeshData[] = []
  const bands: [number, number, number, number][] = [
    [y0, y1, z1 - 0.075, z1],
    [y0, y1, z0, z0 + 0.075],
    [y0, y0 + 0.075, z0, z1],
    [y1 - 0.075, y1, z0, z1],
  ]
  for (const [a, b, c, d] of bands) {
    const p = mlib.box(x, a, c, x + 0.046, b, d)
    mlib.bevel(p, 0.005, 2)
    fr.push(p)
  }
  world.add(mlib.join(fr), M.get('cw_green'))
}

// --------------------------------------------------------------- chalk menu

const MENU: [string, number, string | null][] = [
  ['CENTRAL PERK', 0.115, 'F2EFE6'],
  ['', 0, null],
  ['HOUSE BLEND      1.50', 0.062, 'E8E4D6'],
  ['CAFE AU LAIT     1.75', 0.062, 'E8E4D6'],
  ['CAPPUCCINO       2.25', 0.062, 'F0C86A'],
  ['ESPRESSO         1.95', 0.062, 'E8E4D6'],
  ['LATTE            2.25', 0.062, 'E88A9C'],
  ['MOCHA            2.50', 0.062, 'E8E4D6'],
  ['MUFFIN . SCONE . PIE', 0.055, 'A8D08A'],
]

/** The menu written on the board, fitted to the slate. */
function chalkMenu(world: World, x: number, y0: number, _y1: number, z0: number, z1: number): void {
  const ph = 0.075
  const pv = 0.055
  const sTop = z1 - 0.065
  const sBot = z0 + 0.065
  const units = MENU.reduce((s, [body]) => s + (body ? 1 : 0.6), 0) - 1
  const last = [...MENU].reverse().find(([body]) => body)![1]
  const avail = sTop - sBot - 2 * pv - last
  const pitch = Math.min(0.105, avail / Math.max(1e-6, units))
  const top = sTop - pv
  let line = 0
  for (const [body, size, col] of MENU) {
    if (!body) {
      line += 0.6
      continue
    }
    const md = textMesh(body, size, { extrude: 0.0016, align: 'LEFT', alignY: 'TOP', spacing: 1.06 })
    mlib.rotX(md, Math.PI / 2)
    mlib.rotateZ(md, Math.PI / 2)
    mlib.translate(md, [x + 0.026, y0 + ph, top - line * pitch])
    world.add(md, M.paint('chalkink_' + (col ?? 'F2EFE6'), col ?? 'F2EFE6', { rough: 0.9, bump: 0.3, scale: 200 }))
    line += size < 0.1 ? 1 : 1.5
  }
}

// --------------------------------------------------------------- shop stock

function jar(world: World, x: number, y: number, z: number, r = 0.048, h = 0.155): void {
  const g = mlib.revolve(
    [
      [r * 0.72, 0],
      [r, 0.02],
      [r, h - 0.03],
      [r * 0.82, h - 0.004],
      [r * 0.8, h + 0.014],
      [r * 0.74, h + 0.016],
      [r * 0.74, h - 0.006],
      [r * 0.94, h - 0.03],
      [r * 0.94, 0.024],
      [r * 0.66, 0.008],
    ],
    18,
  )
  mlib.smoothShade(g, 42)
  const fill = mlib.revolve(
    [
      [0, 0.01],
      [r * 0.9, 0.01],
      [r * 0.9, h * 0.72],
      [0, h * 0.74],
    ],
    18,
  )
  const lid = mlib.revolve(
    [
      [0, h + 0.012],
      [r * 0.8, h + 0.01],
      [r * 0.84, h + 0.03],
      [0, h + 0.034],
    ],
    18,
  )
  const fillMat = M.wood('cw_jarfill', { light: '6B4522', dark: '2A1608', ring: 140, scale: 0.05 })
  for (const [md, mat] of [
    [g, M.get('cw_glass')],
    [fill, fillMat],
    [lid, M.get('cw_brass')],
  ] as [MeshData, THREE.Material][]) {
    mlib.translate(md, [x, y, z])
    world.add(md, mat)
  }
}

/** A retail carton, face out, its label rebated into the face. */
function carton(
  world: World,
  x: number,
  y: number,
  z: number,
  w: number,
  d: number,
  h: number,
  colour: string,
  label: string,
  rot = 0,
): void {
  const body = mlib.box(-w / 2, -d / 2, 0, w / 2, d / 2, h)
  mlib.bevel(body, 0.004, 2)
  const pan = mlib.box(-w / 2 + 0.006, d / 2 - 0.005, h * 0.24, w / 2 - 0.006, d / 2 + 0.0032, h * 0.86)
  for (const [md, mat] of [
    [body, M.flat('carton_' + colour, colour, 0.62)],
    [pan, M.flat('label_' + label, label, 0.55)],
  ] as [MeshData, THREE.Material][]) {
    if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
    mlib.translate(md, [x, y, z])
    world.add(md, mat)
  }
}

/** A gusseted retail coffee bag with a folded top. */
function bag(world: World, x: number, y: number, z: number, w: number, d: number, h: number, colour: string, rot = 0): void {
  const rings: Vec3[][] = []
  const levels: [number, number, number][] = [
    [0, 0.98, 0.98],
    [0.1, 1.02, 1.02],
    [0.62, 1, 1],
    [0.86, 0.94, 0.72],
    [0.97, 0.88, 0.3],
    [1, 0.86, 0.16],
  ]
  for (const [t, sw, sd] of levels) {
    const poly = mlib.roundedRect(w * sw, d * sd, Math.min(w * sw, d * sd) * 0.3, 3)
    rings.push(poly.map(([px, py]) => [px, py, z + h * t] as Vec3))
  }
  const md = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(md, 46)
  if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
  mlib.translate(md, [x, y, 0])
  world.add(md, M.paint('bag_' + colour, colour, { rough: 0.52, coat: 0.12, bump: 0.14 }))
}

function tin(world: World, x: number, y: number, z: number, r: number, h: number, colour: string): void {
  const md = mlib.revolve(
    [
      [0, 0],
      [r, 0],
      [r, h - 0.008],
      [r * 0.96, h - 0.004],
      [r * 0.96, h],
      [r * 0.9, h + 0.006],
      [0, h + 0.006],
    ],
    20,
  )
  mlib.smoothShade(md, 40)
  mlib.translate(md, [x, y, z])
  world.add(md, M.paint('tin_' + colour, colour, { rough: 0.3, coat: 0.35 }))
}

// mostly brown and unbleached paper, with two accents
const COLOURS = ['5E3A22', '4A2E1C', '6E4A2A', '7A5A3A', '3A4A34', '8A5A24', '5A4632', '7A2A20', '2E4258']

function stock(world: World): void {
  const y0s = CHALK_Y[1] + 0.3
  const y1 = L.BACK_TALL_N[0]
  let k = 0
  for (const z of [1.386, 1.746, 2.106]) {
    let y = y0s + 0.12
    while (y < y1 - 0.16) {
      k += 1
      const pick = (k * 2) % 5
      if (pick === 0 || pick === 1) {
        jar(world, 0.135, y + 0.055, z, 0.044 + 0.008 * ((k % 3) / 2), 0.135 + 0.05 * ((k % 4) / 3))
        y += 0.125
      } else if (pick === 2 || pick === 3) {
        bag(world, 0.13, y + 0.052, z, 0.098, 0.062, 0.175 + 0.04 * ((k % 3) / 2), COLOURS[k % COLOURS.length], ((k * 13) % 25) - 12)
        y += 0.118
      } else {
        tin(world, 0.128, y + 0.05, z, 0.04 + 0.006 * (k % 2), 0.095 + 0.04 * ((k % 3) / 2), COLOURS[(k + 3) % COLOURS.length])
        y += 0.11
      }
    }
  }
  // the retail display in the counter: upright cartons packed edge to edge
  for (const z of CASE_Z) {
    let y = CASE_Y[0] + 0.046
    while (y < CASE_Y[1] - 0.105) {
      k += 1
      const bw = 0.058 + (0.03 * ((k * 3) % 4)) / 3
      const bh = 0.15 + (0.06 * ((k * 5) % 3)) / 2
      carton(world, 1.945, y + bw * 0.5, z + 0.02, bw, 0.072, bh, COLOURS[k % COLOURS.length], COLOURS[(k + 4) % COLOURS.length], ((k * 11) % 9) - 4)
      y += bw + 0.007
    }
  }
  for (let i = 0; i < 4; i++) jar(world, 0.2, 10.05 + i * 0.16, L.BACK_H, 0.05, 0.185)
}

/** A bag placed off the shelf frame in stock() keeps its own z base. */

export function build(world: World): void {
  mats()
  serviceCounter(world)
  backBar(world)
  const z = L.BACK_H
  // rot=+90: the working face of the machine points into the room
  espresso(world, 0.36, 8.3, z, 90)
  urn(world, 0.26, 7.3, z, -90)
  beanCylinder(world, 0.3, 7.72, z)
  chalkboard(world, -0.004, CHALK_Y[0], CHALK_Y[1], CHALK_Z[0], CHALK_Z[1])
  chalkMenu(world, 0.018, CHALK_Y[0], CHALK_Y[1], CHALK_Z[0], CHALK_Z[1])
  // burr grinder
  const grBase = mlib.prism(mlib.roundedRect(0.16, 0.18, 0.02, 4), 0, 0.2)
  mlib.translate(grBase, [0.3, 5.95, z])
  world.add(grBase, M.get('cw_steel'))
  const hop = mlib.revolve(
    [
      [0, 0.2],
      [0.055, 0.22],
      [0.075, 0.3],
      [0.078, 0.42],
      [0.07, 0.44],
      [0, 0.44],
    ],
    20,
  )
  mlib.smoothShade(hop, 40)
  mlib.translate(hop, [0.3, 5.95, z])
  world.add(hop, M.get('cw_glass'))
  // filter brewer with two glass jugs
  const br = mlib.prism(mlib.roundedRect(0.3, 0.22, 0.02, 4), 0, 0.11)
  const top = mlib.prism(mlib.roundedRect(0.3, 0.22, 0.02, 4), 0.34, 0.46)
  const col = mlib.box(-0.15, -0.11, 0.11, -0.09, 0.11, 0.34)
  const brew = mlib.join([br, top, col])
  mlib.translate(brew, [0.26, 6.55, z])
  world.add(brew, M.get('cw_black'))
  for (let i = 0; i < 2; i++) {
    const jug = mlib.revolve(
      [
        [0, 0],
        [0.07, 0],
        [0.074, 0.02],
        [0.072, 0.135],
        [0.082, 0.15],
        [0.078, 0.165],
        [0.07, 0.165],
        [0.07, 0.155],
        [0, 0.155],
      ],
      20,
    )
    mlib.smoothShade(jug, 40)
    mlib.translate(jug, [0.26, 6.44 + i * 0.22, z + 0.115])
    world.add(jug, M.get('cw_glass'))
  }
  // stacked cups and saucers
  const cupWhite = M.paint('cw_cupwhite', 'E4E0D6', { rough: 0.16, coat: 0.5 })
  for (let kk = 0; kk < 3; kk++) {
    const st: MeshData[] = []
    for (let i = 0; i < 4; i++) {
      const c = mlib.revolve(
        [
          [0, 0],
          [0.036, 0.004],
          [0.041, 0.052],
          [0.038, 0.056],
          [0.034, 0.01],
          [0, 0.008],
        ],
        16,
      )
      mlib.translate(c, [0, 0, i * 0.032])
      st.push(c)
    }
    const o = mlib.join(st)
    mlib.smoothShade(o, 40)
    mlib.translate(o, [0.22 + (kk % 2) * 0.13, 9.3 + kk * 0.19, z])
    world.add(o, cupWhite)
  }
  stock(world)
  cakeDome(world, 1.7, 9.2, L.SERVE_H)
  cakeDome(world, 2.02, 8.72, L.SERVE_H, 0.145)
  register(world, 1.68, 9.8, L.SERVE_H, -96)
}
