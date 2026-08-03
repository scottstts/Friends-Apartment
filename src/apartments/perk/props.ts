/** Fittings and dressing from f_props.py: every light is created by the thing
 * that emits it.  A fixture takes `energy` and defaults it to zero - with no
 * energy it glows through its own shade material and illuminates nothing;
 * the four that carry light data are named in dress.ts (f_layout.fittings). */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import * as G from './geo'
import * as L from './layout'
import * as M from './materials'
import { textMesh } from './text'

const TAU = Math.PI * 2
const ASSETS = '/'

export function mats(): void {
  M.lampshade('opal_glass_lit', 'F2EEE2', 'FFDCAE', 3.8, 0.22)
  M.lampshade('amber_glass_lit', 'D8A45A', 'FFB765', 8, 0.16)
  M.lampshade('enamel_white_lit', 'F0EDE4', 'FFD9A0', 5.5, 0.24)
  M.lampshade('bulb_lit', 'FFF4E2', 'FFE0B0', 8, 0.18)
  // the corridor globes are the only thing lighting that corridor
  M.lampshade('globe_lit', 'F6F0E0', 'FFD9A2', 22, 0.24)
  M.emissive('candle_flame', 'FFB05A', 26)
  M.metal('fit_brass', 'A88433', { rough: 0.28, tarnish: 0.5 })
  M.metal('fit_brass_dk', '8A6A28', { rough: 0.38, tarnish: 0.66 })
  M.iron('fit_iron', '1A1C1A', 0.5)
  M.paint('antler_horn', '473A2A', { rough: 0.66, bump: 0.28 })
  M.wood('prop_wood', { light: '6E4826', dark: '2A1608', ring: 28 })
  M.paint('sign_red', 'B01F1C', { rough: 0.42, coat: 0.2 })
  M.paint('sign_cream', 'CFC3A6', { rough: 0.46, coat: 0.16 })
  M.paint('sign_yellow', 'E8B62A', { rough: 0.4, coat: 0.2 })
  // the counter curtains are a bold woven ticking
  const TICK: [number, string][] = [
    [3, 'C9B894'],
    [1.6, '8E2A22'],
    [0.7, 'C9B894'],
    [1.8, '2C5240'],
    [0.6, 'B8912F'],
  ]
  M.fabric('curtain_stripe', 'C9B894', { rough: 0.8, sheen: 0.35, scale: 140, stripes: TICK, pitch: 0.3 })
  M.fabric('curtain_stripe2', 'C9B894', { rough: 0.82, sheen: 0.3, scale: 140, stripes: TICK, pitch: 0.26 })
  M.foliage('prop_leaf')
  M.foliage('prop_stem', '6E8A46', '3E5424', 70)
  M.flat('prop_paper', 'D8D2C4', 0.78)
}

// ------------------------------------------------------------------- lamps

/** Ribbed opal schoolhouse pendant; the lamp sits at the MOUTH of the shade,
 * so it throws down and out while the glass above still glows. */
export function schoolhouse(world: World, x: number, y: number, z: number, ztop: number, energy = 0): void {
  mats()
  const brass: MeshData[] = []
  const rod = mlib.tubeAlong(
    [
      [0, 0, z + 0.145],
      [0, 0, ztop],
    ],
    mlib.circle(0.01, 10),
  )
  brass.push(rod)
  brass.push(
    mlib.revolve(
      [
        [0, ztop - 0.03],
        [0.062, ztop - 0.028],
        [0.058, ztop - 0.006],
        [0, ztop],
      ],
      18,
    ),
  )
  brass.push(
    mlib.revolve(
      [
        [0, z + 0.155],
        [0.048, z + 0.15],
        [0.052, z + 0.118],
        [0.07, z + 0.104],
        [0.066, z + 0.086],
        [0, z + 0.086],
      ],
      20,
    ),
  )
  const prof: Vec2[] = [
    [0.062, z + 0.1],
    [0.088, z + 0.07],
    [0.126, z + 0.02],
    [0.15, z - 0.038],
    [0.155, z - 0.08],
    [0.14, z - 0.104],
    [0.118, z - 0.108],
    [0.126, z - 0.09],
    [0.14, z - 0.056],
    [0.132, z + 0.01],
    [0.1, z + 0.062],
    [0.058, z + 0.094],
  ]
  const seg = 36
  const rings: Vec3[][] = []
  for (let s = 0; s < seg; s++) {
    const a = (TAU * s) / seg
    const k = 1 + 0.02 * Math.cos(12 * a)
    rings.push(prof.map(([r, zz]) => [r * k * Math.cos(a), r * k * Math.sin(a), zz] as Vec3))
  }
  const sh = mlib.loft(rings, { closeU: true, closeV: true })
  mlib.smoothShade(sh, 40)
  mlib.translate(sh, [x, y, 0])
  world.add(sh, M.get('opal_glass_lit'))
  const obr = mlib.join(brass)
  mlib.translate(obr, [x, y, 0])
  world.add(obr, M.get('fit_brass'))
  if (energy) {
    world.pointLight([x, y, z - 0.135], energy, [1, 0.84, 0.6], 0.11, { distance: 9, shadowMapSize: 512 })
  }
}

/** Plain opal globe screwed straight to a corridor ceiling; emissive only. */
export function ceilingGlobe(world: World, x: number, y: number, z: number, r = 0.13): void {
  mats()
  const ring = mlib.revolve(
    [
      [0, z],
      [r * 0.52, z],
      [r * 0.55, z - 0.018],
      [r * 0.46, z - 0.03],
      [0, z - 0.03],
    ],
    20,
  )
  mlib.translate(ring, [x, y, 0])
  world.add(ring, M.get('fit_brass_dk'))
  const prof: Vec2[] = [[0, z - 0.022]]
  for (let k = 1; k < 13; k++) {
    const a = (Math.PI * k) / 13
    prof.push([r * Math.sin(a) * 1.02, z - 0.022 - r * 0.92 * (1 - Math.cos(a))])
  }
  prof.push([0, z - 0.022 - r * 1.84])
  const gl = mlib.revolve(prof, 24)
  mlib.smoothShade(gl, 44)
  mlib.translate(gl, [x, y, 0])
  world.add(gl, M.get('globe_lit'))
}

/** The antler chandelier by the entrance: nine horns, candle tubes, a flame
 * of emission on each wick, ONE lamp for the whole fitting. */
export function antlerChandelier(world: World, x: number, y: number, z: number, energy = 0, arms = 9): void {
  mats()
  const horn: MeshData[] = []
  const brs: MeshData[] = []
  const flame: MeshData[] = []
  brs.push(
    mlib.tubeAlong(
      [
        [0, 0, z + 0.1],
        [0, 0, L.CZ - 0.02],
      ],
      mlib.circle(0.008, 8),
    ),
  )
  for (let i = 0; i < arms; i++) {
    const a = (TAU * i) / arms
    const tilt = 0.34 + (0.26 * ((i * 7) % 3)) / 2
    const ln = 0.56 + (0.14 * ((i * 5) % 3)) / 2
    const pts: Vec3[] = [[0, 0, z]]
    for (let k = 1; k < 7; k++) {
      const t = k / 6
      const r = ln * t
      const zz = z + t ** 0.7 * tilt * 0.85 - 0.06 * Math.sin(t * Math.PI)
      const wob = 0.1 * Math.sin(t * 3.4 + i)
      pts.push([(r + wob * 0.2) * Math.cos(a + wob), (r + wob * 0.2) * Math.sin(a + wob), zz])
    }
    const rad = [0.034, 0.03, 0.026, 0.022, 0.018, 0.014, 0.01]
    const rings: Vec3[][] = pts.map((p, pi) =>
      Array.from({ length: 8 }, (_, k2) => {
        const t2 = (k2 * TAU) / 8
        return [p[0] + rad[pi] * Math.cos(t2), p[1] + rad[pi] * Math.sin(t2), p[2]] as Vec3
      }),
    )
    const hb = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
    mlib.smoothShade(hb, 40)
    horn.push(hb)
    const f0 = pts[3]
    const fk: Vec3[] = [f0]
    for (let k = 1; k < 4; k++) {
      const t = k / 3
      fk.push([f0[0] + 0.22 * t * Math.cos(a + 0.7), f0[1] + 0.22 * t * Math.sin(a + 0.7), f0[2] + 0.19 * t])
    }
    const fr = [0.019, 0.015, 0.012, 0.008]
    const frings: Vec3[][] = fk.map((p, pi) =>
      Array.from({ length: 7 }, (_, k2) => {
        const t2 = (k2 * TAU) / 7
        return [p[0] + fr[pi] * Math.cos(t2), p[1] + fr[pi] * Math.sin(t2), p[2]] as Vec3
      }),
    )
    const hf = mlib.loft(frings, { closeV: true, capStart: true, capEnd: true })
    mlib.smoothShade(hf, 40)
    horn.push(hf)
    const tp = pts[pts.length - 1]
    const cd = mlib.revolve(
      [
        [0, 0],
        [0.024, 0.002],
        [0.022, 0.016],
        [0.014, 0.02],
        [0.014, 0.09],
        [0, 0.094],
      ],
      12,
    )
    mlib.translate(cd, [tp[0], tp[1], tp[2]])
    brs.push(cd)
    const fl = mlib.revolve(
      [
        [0, 0.09],
        [0.009, 0.101],
        [0.011, 0.116],
        [0.006, 0.134],
        [0, 0.142],
      ],
      10,
    )
    mlib.smoothShade(fl, 40)
    mlib.translate(fl, [tp[0], tp[1], tp[2]])
    flame.push(fl)
  }
  const oh = mlib.join(horn)
  mlib.translate(oh, [x, y, 0])
  world.add(oh, M.get('antler_horn'))
  const ob = mlib.join(brs)
  mlib.translate(ob, [x, y, 0])
  world.add(ob, M.get('fit_brass_dk'))
  const of = mlib.join(flame)
  mlib.translate(of, [x, y, 0])
  world.add(of, M.get('candle_flame'))
  if (energy) {
    world.pointLight([x, y, z + 0.3], energy, [1, 0.72, 0.4], 0.34, { distance: 10, shadowMapSize: 512 })
  }
}

/** Brass wall bracket with an amber shade; `facing` is the outward normal. */
export function sconce(world: World, x: number, y: number, z: number, facing: [number, number]): void {
  mats()
  const [fx, fy] = facing
  const brs: MeshData[] = []
  const bp = mlib.revolve(
    [
      [0, 0],
      [0.055, 0],
      [0.052, 0.02],
      [0.03, 0.034],
      [0, 0.036],
    ],
    18,
  )
  mlib.rotX(bp, Math.PI / 2)
  mlib.rotateZ(bp, Math.atan2(fy, fx) + Math.PI / 2)
  brs.push(bp)
  const arm = mlib.tubeAlong(
    [
      [0, 0, 0],
      [fx * 0.075, fy * 0.075, 0.045],
      [fx * 0.135, fy * 0.135, 0.09],
      [fx * 0.15, fy * 0.15, 0.128],
    ],
    mlib.circle(0.01, 8),
  )
  mlib.smoothShade(arm, 40)
  brs.push(arm)
  const shade = mlib.revolve(
    [
      [0.03, 0.128],
      [0.052, 0.14],
      [0.086, 0.176],
      [0.098, 0.212],
      [0.094, 0.222],
      [0.08, 0.19],
      [0.046, 0.152],
      [0.028, 0.14],
    ],
    22,
  )
  mlib.smoothShade(shade, 42)
  mlib.translate(shade, [fx * 0.15, fy * 0.15, 0])
  const ob = mlib.join(brs)
  mlib.translate(ob, [x, y, z])
  world.add(ob, M.get('fit_brass'))
  mlib.translate(shade, [x, y, z])
  world.add(shade, M.get('amber_glass_lit'))
}

/** The green enamel cone over the counter: enamel outside, lit white inside. */
export function conePendant(world: World, x: number, y: number, z: number, ztop: number, energy = 0, r = 0.2, colour = '1F4032'): void {
  mats()
  const sh = mlib.revolve(
    [
      [0.03, 0.15],
      [0.052, 0.14],
      [r * 0.86, 0.048],
      [r, 0],
      [r, -0.012],
      [r * 0.84, 0.04],
      [0.046, 0.13],
      [0.028, 0.14],
    ],
    30,
  )
  mlib.smoothShade(sh, 40)
  mlib.translate(sh, [x, y, z])
  world.add(sh, M.paint('cone_enamel', colour, { rough: 0.2, coat: 0.45 }))
  const inner = mlib.revolve(
    [
      [0.028, 0.138],
      [0.046, 0.128],
      [r * 0.83, 0.038],
      [r * 0.99, -0.002],
    ],
    30,
    { capStart: false, capEnd: false },
  )
  mlib.smoothShade(inner, 40)
  mlib.translate(inner, [x, y, z])
  world.add(inner, M.get('enamel_white_lit'))
  const rod = mlib.tubeAlong(
    [
      [0, 0, 0.145],
      [0, 0, ztop - z],
    ],
    mlib.circle(0.008, 8),
  )
  mlib.translate(rod, [x, y, z])
  world.add(rod, M.get('fit_brass_dk'))
  const bulb = mlib.revolve(
    [
      [0, 0.02],
      [0.026, 0.006],
      [0.03, -0.02],
      [0.022, -0.044],
      [0, -0.05],
    ],
    14,
  )
  mlib.translate(bulb, [x, y, z])
  world.add(bulb, M.get('bulb_lit'))
  if (energy) {
    world.pointLight([x, y, z - 0.045], energy, [1, 0.83, 0.6], 0.1, { distance: 8, shadowMapSize: 512 })
  }
}

/** The leaded amber shade over the main seating: real facets. */
export function tiffanyPendant(world: World, x: number, y: number, z: number, ztop: number, energy = 0, r = 0.26): void {
  mats()
  const prof: [number, number][] = [
    [0.038, 0.21],
    [0.09, 0.19],
    [0.16, 0.14],
    [0.215, 0.075],
    [r, 0.01],
    [r * 1.02, -0.006],
  ]
  const seg = 20
  const rings: Vec3[][] = []
  for (let s = 0; s < seg; s++) {
    const a = (TAU * s) / seg
    const k = 1 + 0.028 * Math.cos(seg * a * 0.5) - 0.012
    rings.push(prof.map(([rr, zz]) => [rr * k * Math.cos(a), rr * k * Math.sin(a), zz] as Vec3))
  }
  const sh = mlib.loft(rings, { closeU: true })
  mlib.solidify(sh, 0.006)
  mlib.flatShade(sh)
  mlib.translate(sh, [x, y, z])
  world.add(sh, M.lampshade('tiffany_amber', 'B87322', 'FF9A2E', 2.2, 0.16))
  const cap = mlib.revolve(
    [
      [0, 0.232],
      [0.04, 0.226],
      [0.044, 0.204],
      [0, 0.2],
    ],
    18,
  )
  mlib.translate(cap, [x, y, z])
  world.add(cap, M.get('fit_brass_dk'))
  const ch = mlib.tubeAlong(
    [
      [0, 0, 0.23],
      [0, 0, ztop - z],
    ],
    mlib.circle(0.007, 7),
  )
  mlib.translate(ch, [x, y, z])
  world.add(ch, M.get('fit_brass_dk'))
  const bulb = mlib.revolve(
    [
      [0, 0.15],
      [0.03, 0.132],
      [0.034, 0.1],
      [0.024, 0.072],
      [0, 0.064],
    ],
    14,
  )
  mlib.translate(bulb, [x, y, z])
  world.add(bulb, M.get('bulb_lit'))
  if (energy) {
    world.pointLight([x, y, z - 0.01], energy, [1, 0.76, 0.48], 0.13, { distance: 9, shadowMapSize: 512 })
  }
}

/** A small shaded lamp for the bay side table. */
export function tableLamp(world: World, x: number, y: number, z: number, h = 0.52): void {
  mats()
  const base = mlib.revolve(
    [
      [0, 0],
      [0.085, 0.004],
      [0.08, 0.02],
      [0.036, 0.05],
      [0.028, 0.12],
      [0.034, 0.15],
      [0.026, 0.18],
      [0.014, h - 0.18],
      [0, h - 0.18],
    ],
    20,
  )
  mlib.smoothShade(base, 40)
  mlib.translate(base, [x, y, z])
  world.add(base, M.get('fit_brass'))
  const sh = mlib.revolve(
    [
      [0.072, h - 0.01],
      [0.128, h - 0.185],
      [0.13, h - 0.192],
      [0.074, h - 0.017],
    ],
    24,
    { capStart: false, capEnd: false },
  )
  mlib.smoothShade(sh, 44)
  mlib.translate(sh, [x, y, z])
  world.add(sh, M.lampshade('bay_lamp_shade', 'D6B078', 'FFC888', 4.2, 0.7))
}

// -------------------------------------------------------------------- neon

/** Squeeze a mesh to `width` across, about its own centre. */
function fitX(md: MeshData, width: number): MeshData {
  if (!md.verts.length) return md
  const xs = md.verts.map((v) => v[0])
  const w = Math.max(...xs) - Math.min(...xs)
  if (w > width && width > 0) mlib.scaleMesh(md, [width / w, 1, 1])
  return md
}

/** Bend (u, v) polylines into glass tube standing off a wall whose outward
 * plan normal is `facing`. */
function neonTubes(
  world: World,
  name: string,
  paths: Vec2[][],
  s: number,
  x: number,
  y: number,
  z: number,
  facing: [number, number],
  colour: string,
  rad = 0.0085,
  strength = 20,
): void {
  const ang = Math.atan2(facing[1], facing[0])
  const profile = mlib.circle(rad, 8)
  const parts: MeshData[] = []
  for (const p of paths) {
    const pts: Vec3[] = []
    for (const [u, v] of p) {
      const q: Vec3 = [0, u * s, v * s]
      if (pts.length && Math.abs(q[1] - pts[pts.length - 1][1]) < 1e-7 && Math.abs(q[2] - pts[pts.length - 1][2]) < 1e-7) continue
      pts.push(q)
    }
    if (pts.length < 2) continue
    const loop =
      Math.abs(pts[0][1] - pts[pts.length - 1][1]) < 1e-6 && Math.abs(pts[0][2] - pts[pts.length - 1][2]) < 1e-6
    const path = loop ? pts.slice(0, -1) : pts
    const t = mlib.tubeAlong(path, profile, { up: [1, 0, 0], closePath: loop })
    mlib.smoothShade(t, 40)
    parts.push(t)
  }
  const md = mlib.join(parts)
  mlib.rotateZ(md, ang)
  mlib.translate(md, [x, y, z])
  world.add(md, M.neon('neon_' + name, colour, strength))
}

function ell(cx: number, cy: number, rx: number, ry: number, a0 = 0, a1 = TAU, n = 28): Vec2[] {
  return Array.from({ length: n + 1 }, (_, i) => {
    const a = a0 + ((a1 - a0) * i) / n
    return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)] as Vec2
  })
}

/** The outline coffee cup on the entrance pier, bent tube off frontal.jpeg. */
export function neonCup(world: World, x: number, y: number, z: number, s: number, facing: [number, number]): void {
  const bowl: Vec2[] = [
    [-1, 0],
    [-0.96, -0.3],
    [-0.84, -0.6],
    [-0.62, -0.79],
    [-0.32, -0.9],
    [0, -0.92],
    [0.32, -0.9],
    [0.62, -0.79],
    [0.84, -0.6],
    [0.96, -0.3],
    [1, 0],
  ]
  const amber: Vec2[][] = [bowl, ell(0, 0, 1, 0.2), G.arcPts(1, -0.38, 0.52, (-78 * Math.PI) / 180, (78 * Math.PI) / 180, 14)]
  const steamCols: [number, number][] = [
    [-0.34, 1.2],
    [0.04, 1.14],
  ]
  steamCols.forEach(([dx, hgt], k) => {
    amber.push(
      Array.from({ length: 10 }, (_, i) => {
        const t = i / 9
        return [dx + 0.1 * Math.sin(t * 5.4 + k * 1.4), 0.1 + hgt * t] as Vec2
      }),
    )
  })
  neonTubes(world, 'cup', amber, s, x, y, z, facing, 'F5C518')
  neonTubes(world, 'cup_saucer', [ell(0, -0.79, 1.27, 0.41)], s, x, y, z, facing, '35E0C8')
}

// ------------------------------------------------------- script neon lettering
// The alphabet is a skeleton, one stroke per pen-lift, x-height 1, baseline 0.
// Every lower-case letter enters at (0.00, 0.18) and leaves at about
// (adv, 0.30), so the word joins up by construction.

type Stroke = Vec2[]
const bz = (p0: Vec2, p1: Vec2, p2: Vec2, p3: Vec2, skip = false): Vec2[] => mlib.bez(p0, p1, p2, p3, 10, skip)

const SCRIPT: Record<string, [Stroke[], number]> = {
  a: [
    [
      [
        ...bz([0, 0.18], [0.24, 0.52], [0.46, 0.82], [0.6, 0.92]),
        ...bz([0.6, 0.92], [0.28, 1.04], [0.02, 0.8], [0.06, 0.46], true),
        ...bz([0.06, 0.46], [0.1, 0.06], [0.52, -0.06], [0.66, 0.28], true),
        ...bz([0.66, 0.28], [0.69, 0.16], [0.71, 0.1], [0.75, 0.08], true),
        ...bz([0.75, 0.08], [0.86, 0.06], [0.94, 0.18], [1, 0.32], true),
      ],
    ],
    1.04,
  ],
  c: [
    [
      [
        ...bz([0, 0.18], [0.24, 0.52], [0.44, 0.82], [0.6, 0.92]),
        ...bz([0.6, 0.92], [0.3, 1.06], [0.02, 0.84], [0.06, 0.48], true),
        ...bz([0.06, 0.48], [0.1, 0.1], [0.48, -0.06], [0.72, 0.14], true),
        ...bz([0.72, 0.14], [0.79, 0.2], [0.84, 0.26], [0.88, 0.32], true),
      ],
    ],
    0.92,
  ],
  e: [
    [
      [
        ...bz([0, 0.18], [0.14, 0.34], [0.26, 0.46], [0.38, 0.52]),
        ...bz([0.38, 0.52], [0.14, 0.62], [0.1, 0.94], [0.34, 0.96], true),
        ...bz([0.34, 0.96], [0.58, 0.98], [0.66, 0.62], [0.46, 0.34], true),
        ...bz([0.46, 0.34], [0.32, 0.12], [0.46, -0.04], [0.66, 0.06], true),
        ...bz([0.66, 0.06], [0.76, 0.12], [0.84, 0.22], [0.9, 0.32], true),
      ],
    ],
    0.94,
  ],
  i: [
    [
      [
        ...bz([0, 0.18], [0.14, 0.52], [0.26, 0.82], [0.32, 0.94]),
        ...bz([0.32, 0.94], [0.3, 0.62], [0.28, 0.28], [0.32, 0.14], true),
        ...bz([0.32, 0.14], [0.42, 0.02], [0.56, 0.14], [0.64, 0.32], true),
      ],
      [
        [0.33, 1.22],
        [0.38, 1.31],
      ],
    ],
    0.7,
  ],
  n: [
    [
      [
        ...bz([0, 0.18], [0.14, 0.54], [0.24, 0.82], [0.3, 0.94]),
        ...bz([0.3, 0.94], [0.28, 0.66], [0.26, 0.36], [0.28, 0.2], true),
        ...bz([0.28, 0.2], [0.34, 0.72], [0.56, 1.02], [0.74, 0.86], true),
        ...bz([0.74, 0.86], [0.82, 0.76], [0.78, 0.36], [0.74, 0.14], true),
        ...bz([0.74, 0.14], [0.82, 0.04], [0.94, 0.14], [1.02, 0.32], true),
      ],
    ],
    1.06,
  ],
  o: [
    [
      [
        ...bz([0, 0.18], [0.24, 0.52], [0.44, 0.82], [0.58, 0.92]),
        ...bz([0.58, 0.92], [0.28, 1.06], [0.02, 0.82], [0.06, 0.48], true),
        ...bz([0.06, 0.48], [0.1, 0.08], [0.56, -0.06], [0.7, 0.3], true),
        ...bz([0.7, 0.3], [0.8, 0.58], [0.72, 0.82], [0.58, 0.9], true),
        ...bz([0.58, 0.9], [0.7, 0.97], [0.86, 0.9], [0.98, 0.76], true),
      ],
    ],
    1,
  ],
  p: [
    [
      [
        ...bz([0, 0.18], [0.14, 0.54], [0.26, 0.84], [0.32, 0.96]),
        ...bz([0.32, 0.96], [0.26, 0.48], [0.16, -0.14], [0.1, -0.56], true),
        ...bz([0.1, -0.56], [0.26, -0.44], [0.34, -0.16], [0.34, 0.06], true),
      ],
      [
        ...bz([0.31, 0.6], [0.52, 0.9], [0.9, 0.8], [0.9, 0.46]),
        ...bz([0.9, 0.46], [0.9, 0.2], [0.62, 0.06], [0.44, 0.18], true),
      ],
      bz([0.87, 0.34], [0.94, 0.26], [0.99, 0.26], [1.06, 0.34]),
    ],
    1.08,
  ],
  r: [
    [
      [
        ...bz([0, 0.18], [0.14, 0.52], [0.24, 0.8], [0.3, 0.92]),
        ...bz([0.3, 0.92], [0.32, 0.68], [0.28, 0.5], [0.34, 0.44], true),
        ...bz([0.34, 0.44], [0.46, 0.36], [0.58, 0.52], [0.68, 0.58], true),
        ...bz([0.68, 0.58], [0.78, 0.62], [0.88, 0.5], [0.94, 0.36], true),
      ],
    ],
    0.96,
  ],
  s: [
    [
      [
        ...bz([0, 0.18], [0.16, 0.5], [0.28, 0.8], [0.32, 0.92]),
        ...bz([0.32, 0.92], [0.24, 0.6], [0.06, 0.48], [0.1, 0.26], true),
        ...bz([0.1, 0.26], [0.14, 0.04], [0.44, 0], [0.54, 0.2], true),
        ...bz([0.54, 0.2], [0.62, 0.34], [0.72, 0.34], [0.8, 0.26], true),
      ],
    ],
    0.82,
  ],
  t: [
    [
      [
        ...bz([0, 0.18], [0.14, 0.6], [0.24, 1.1], [0.3, 1.42]),
        ...bz([0.3, 1.42], [0.28, 0.9], [0.24, 0.4], [0.28, 0.16], true),
        ...bz([0.28, 0.16], [0.36, 0], [0.54, 0.1], [0.64, 0.28], true),
      ],
      [
        [0, 0.79],
        [0.32, 0.84],
        [0.62, 0.89],
      ],
    ],
    0.74,
  ],
  u: [
    [
      [
        ...bz([0, 0.18], [0.16, 0.56], [0.28, 0.84], [0.34, 0.94]),
        ...bz([0.34, 0.94], [0.28, 0.6], [0.18, 0.2], [0.28, 0.08], true),
        ...bz([0.28, 0.08], [0.42, -0.04], [0.56, 0.2], [0.62, 0.52], true),
        ...bz([0.62, 0.52], [0.66, 0.74], [0.68, 0.86], [0.7, 0.94], true),
        ...bz([0.7, 0.94], [0.64, 0.6], [0.58, 0.24], [0.64, 0.12], true),
        ...bz([0.64, 0.12], [0.74, 0.02], [0.9, 0.14], [0.98, 0.32], true),
      ],
    ],
    1.02,
  ],
  C: [
    [
      [
        ...bz([1.3, 1.4], [1.16, 1.74], [0.62, 1.86], [0.34, 1.56]),
        ...bz([0.34, 1.56], [0, 1.18], [0.02, 0.42], [0.4, 0.14], true),
        ...bz([0.4, 0.14], [0.7, -0.06], [1, 0.06], [1.16, 0.3], true),
      ],
      bz([0.56, 1.58], [0.86, 1.68], [1.08, 1.58], [1.3, 1.38]),
    ],
    1.24,
  ],
  E: [
    [
      [
        ...bz([1.06, 1.5], [0.88, 1.78], [0.44, 1.74], [0.38, 1.4]),
        ...bz([0.38, 1.4], [0.32, 1.14], [0.62, 1.06], [0.76, 1.02], true),
        ...bz([0.76, 1.02], [0.42, 1], [0.26, 0.84], [0.28, 0.54], true),
        ...bz([0.28, 0.54], [0.3, 0.18], [0.68, 0.02], [1.02, 0.24], true),
      ],
    ],
    1.1,
  ],
  L: [
    [
      [
        ...bz([1.2, 1.52], [1.08, 1.82], [0.66, 1.86], [0.58, 1.5]),
        ...bz([0.58, 1.5], [0.5, 1.1], [0.6, 0.56], [0.42, 0.24], true),
        ...bz([0.42, 0.24], [0.26, -0.04], [0.06, 0.1], [0.14, 0.32], true),
        ...bz([0.14, 0.32], [0.26, 0.58], [0.7, 0.36], [1.02, 0.26], true),
      ],
    ],
    1.1,
  ],
}

const SLANT = 0.14

/** The word as (u, v) polylines, x-height 1, baseline 0, centred. */
function scriptWord(word: string, tight = 1): { paths: Vec2[][]; w: number } {
  const out: Vec2[][] = []
  let pen = 0
  for (const ch of word) {
    const g = SCRIPT[ch]
    if (!g) {
      pen += 0.5
      continue
    }
    const [strokes, adv] = g
    for (const st of strokes) out.push(st.map(([u, v]) => [u + pen + v * SLANT, v] as Vec2))
    pen += adv * tight
  }
  const us = out.flatMap((st) => st.map((p) => p[0]))
  const w = Math.max(...us) - Math.min(...us)
  const cx = (Math.max(...us) + Math.min(...us)) / 2
  return { paths: out.map((st) => st.map(([u, v]) => [u - cx, v] as Vec2)), w }
}

/** A neon word in joined-up script; `fit` caps the width, resizing x-height. */
export function neonScript(
  world: World,
  name: string,
  word: string,
  x: number,
  y: number,
  z: number,
  xh: number,
  colour: string,
  facing: [number, number],
  fit?: number,
): void {
  const { paths, w } = scriptWord(word)
  let height = xh
  if (fit && w * height > fit) height = fit / w
  const scaledPaths = paths.map((st) => st.map(([u, v]) => [u * height, v * height] as Vec2))
  neonTubes(world, name, scaledPaths, 1, x, y, z, facing, colour, 0.0085, 24)
}

/** The red SERVICE arrow hanging off the cross beam, pointing west. */
export function serviceSign(world: World, x: number, y: number, z: number, w = 1.58, h = 0.4, top?: number): void {
  mats()
  const outPoly = G.ccw([
    [-w / 2, -h / 2],
    [-w / 2 + h * 0.42, 0],
    [-w / 2, h / 2],
    [w / 2 - h * 0.92, h / 2],
    [w / 2, 0],
    [w / 2 - h * 0.92, -h / 2],
  ])
  const board = mlib.prismXZ(outPoly, -0.014, 0.014)
  const field = mlib.prismXZ(G.polyOffset(outPoly, -0.03), -0.019, 0.019)
  mlib.scaleMesh(board, [-1, 1, 1])
  mlib.recalcNormals(board)
  mlib.scaleMesh(field, [-1, 1, 1])
  mlib.recalcNormals(field)
  const fieldw = w - h * 0.92 - h * 0.55
  const txt = fitX(textMesh('SERVICE', h * 0.62, { extrude: 0.006 }), fieldw)
  mlib.rotX(txt, Math.PI / 2)
  mlib.translate(txt, [h * 0.2, -0.022, 0])
  const txt2 = fitX(textMesh('SERVICE', h * 0.62, { extrude: 0.006 }), fieldw)
  mlib.rotX(txt2, Math.PI / 2)
  mlib.rotateZ(txt2, Math.PI)
  mlib.translate(txt2, [h * 0.2, 0.022, 0])
  const hang: MeshData[] = []
  const ztop = (top ?? L.CZ) - z
  for (const s of [-1, 1]) {
    hang.push(
      mlib.tubeAlong(
        [
          [s * w * 0.3, 0, h * 0.42],
          [s * w * 0.3, 0, ztop],
        ],
        mlib.circle(0.005, 6),
      ),
    )
    const ey = mlib.revolve(
      [
        [0.005, h * 0.4],
        [0.018, h * 0.4],
        [0.018, h * 0.46],
        [0.005, h * 0.46],
      ],
      10,
    )
    mlib.translate(ey, [s * w * 0.3, 0, 0])
    hang.push(ey)
  }
  const pieces: [MeshData, THREE.Material][] = [
    [board, M.get('sign_cream')],
    [field, M.get('sign_red')],
    [txt, M.get('sign_yellow')],
    [txt2, M.get('sign_yellow')],
    [mlib.join(hang), M.get('fit_iron')],
  ]
  for (const [md, mat] of pieces) {
    mlib.translate(md, [x, y, z])
    world.add(md, mat)
  }
}

// ------------------------------------------------------------------ pictures

function planeUvs(md: MeshData, w: number, h: number): void {
  md.uvs = md.faces.map((face) =>
    face.map((vi) => {
      const v = md.verts[vi]
      return [(v[0] + w / 2) / w, (v[2] + h / 2) / h] as Vec2
    }),
  )
}

/** The Statue of Liberty canvas in a plain dark frame; square, as the art is. */
export function painting(world: World, x: number, y: number, z: number, w: number, facing: [number, number], path: string): void {
  mats()
  const h = w
  const canvas = G.gridPlane(
    [
      [-w / 2, -h / 2],
      [w / 2, -h / 2],
      [w / 2, h / 2],
      [-w / 2, h / 2],
    ],
    0,
    2,
    2,
  )
  mlib.rotX(canvas, Math.PI / 2)
  planeUvs(canvas, w, h)
  const fr = mlib.sweepRectFrame(w + 0.055, h + 0.055, [
    [0, -0.03],
    [0.048, -0.034],
    [0.052, 0.016],
    [0, 0.02],
  ])
  const ang = Math.atan2(facing[1], facing[0]) + Math.PI / 2
  for (const [md, mat] of [
    [canvas, M.imgMat('painting_img', path, { rough: 0.62 })],
    [fr, M.get('prop_wood')],
  ] as [MeshData, THREE.Material][]) {
    mlib.rotateZ(md, ang)
    mlib.translate(md, [x + facing[0] * 0.028, y + facing[1] * 0.028, z])
    world.add(md, mat)
  }
}

/** The Central Perk transfer on the middle bay light, facing the street. */
export function decal(world: World, x: number, y: number, z: number, w: number, facing: [number, number], path: string): void {
  const ratio = 1.5
  const h = w / ratio
  const pl = G.gridPlane(
    [
      [-w / 2, -h / 2],
      [w / 2, -h / 2],
      [w / 2, h / 2],
      [-w / 2, h / 2],
    ],
    0,
    2,
    2,
  )
  mlib.rotX(pl, Math.PI / 2)
  planeUvs(pl, w, h)
  mlib.rotateZ(pl, Math.atan2(facing[1], facing[0]) + Math.PI / 2)
  mlib.translate(pl, [x, y, z])
  world.add(pl, M.imgMat('decal_img', path, { alpha: true, rough: 0.4 }))
}

export const ASSET_PAINTING = ASSETS + 'status_of_liberty_painting.png'
export const ASSET_DECAL = ASSETS + 'central_perk_sticker.png'

// ------------------------------------------------------------------ curtains

/** A hung curtain: real gathers, wider than its opening. */
export function curtain(
  world: World,
  p0: Vec2,
  p1: Vec2,
  ztop: number,
  zbot: number,
  folds = 9,
  depth = 0.055,
  mat = 'curtain_stripe',
  gathered = 0.62,
): void {
  mats()
  let ux = p1[0] - p0[0]
  let uy = p1[1] - p0[1]
  const ll = Math.hypot(ux, uy) || 1
  ux /= ll
  uy /= ll
  const nx = uy
  const ny = -ux
  const n = folds * 8
  const rings: Vec3[][] = []
  for (let j = 0; j < 11; j++) {
    const t = j / 10
    const z = ztop - (ztop - zbot) * t
    const ring: Vec3[] = []
    for (let i = 0; i <= n; i++) {
      const u = i / n
      const ph = u * folds * TAU
      const amp = depth * (0.55 + 0.45 * (1 - t)) * Math.sin(ph)
      const s = u * ll * gathered + ll * (1 - gathered) * 0.5
      ring.push([p0[0] + ux * s + nx * amp, p0[1] + uy * s + ny * amp, z - 0.02 * Math.sin(u * Math.PI * 3) * t])
    }
    rings.push(ring)
  }
  const md = mlib.loft(rings)
  mlib.solidify(md, 0.006)
  mlib.smoothShade(md, 50)
  world.add(md, M.get(mat))
}

// -------------------------------------------------------------- plants etc.

/** One petal: a cupped blade rooted at the origin, pointing along +Y. */
function petalBlade(ln: number, wd: number, cup: number, n = 7): MeshData {
  const rings: Vec3[][] = []
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1)
    const w = wd * Math.sin(Math.PI * Math.min(1, 0.1 + t * 0.92)) ** 0.62
    const z = cup * t * t
    const th = 0.0016 * (1 - 0.7 * t)
    rings.push([
      [-w, ln * t, z * 0.45],
      [0, ln * t, z + th],
      [w, ln * t, z * 0.45],
      [0, ln * t, z - th],
    ])
  }
  const md = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(md, 50)
  return md
}

function vase(r: number, h: number, colour?: string | null): { md: MeshData; mat: THREE.Material } {
  const prof: Vec2[] = [
    [0, 0],
    [r * 0.62, 0],
    [r * 0.68, 0.02],
    [r * 0.92, h * 0.34],
    [r * 0.98, h * 0.6],
    [r * 0.86, h * 0.88],
    [r * 0.8, h],
    [r * 0.73, h],
    [r * 0.79, h * 0.88],
    [r * 0.91, h * 0.6],
    [r * 0.85, h * 0.34],
    [r * 0.6, 0.03],
    [0, 0.03],
  ]
  const md = mlib.revolve(prof, 26)
  mlib.smoothShade(md, 40)
  const mat = colour ? M.paint('vase_' + colour, colour, { rough: 0.22, coat: 0.5 }) : M.glass('vase_glass', 'E6EEE8', 0.05)
  return { md, mat }
}

export interface BouquetOpts {
  r?: number
  h?: number
  nstem?: number
  vase?: [number, number, string | null]
  colours?: string[]
}

/** A big loose arrangement: every stem is a swept tube with whorls of real
 * cupped petals on it. */
export function bouquet(world: World, x: number, y: number, z: number, o: BouquetOpts = {}): void {
  mats()
  const { r = 0.3, h = 0.52, nstem = 34, vase: vs, colours = ['E2621F', 'E8A41C', 'D8324A', 'EFE0C0'] } = o
  const stems: MeshData[] = []
  const heads = new Map<number, MeshData[]>()
  for (let i = 0; i < nstem; i++) {
    const a = (TAU * (i * 0.618)) % TAU
    const t = (i % 7) / 6
    const rr = r * (0.3 + 0.7 * t)
    const hh = h * (0.8 + (0.2 * ((i * 3) % 5)) / 4) * (1 - 0.3 * t * t)
    const leanK = 0.55 + 0.75 * t
    const bend = 0.12 * t
    const vh = vs ? vs[1] : 0
    const vm = vs ? vs[0] * 0.74 : 0
    const z0 = vh * 0.14
    const pts: Vec3[] = []
    for (let k = 0; k < 9; k++) {
      const u = k / 8
      const zz = z0 + (hh - z0) * u ** 0.72
      let g = Math.max(0, Math.min(1, (zz - vh * 0.96) / Math.max(1e-6, hh * 0.4)))
      g = g * g * (3 - 2 * g)
      let rad = rr * leanK * u * g + Math.max(0, u - 0.15) * vm * 0.55
      if (zz < vh) rad = Math.min(rad, vm)
      pts.push([
        rad * Math.cos(a) + bend * u * u * g * Math.cos(a + 1.2),
        rad * Math.sin(a) + bend * u * u * g * Math.sin(a + 1.2),
        zz,
      ])
    }
    stems.push(mlib.tubeAlong(pts, mlib.circle(0.0032, 5)))
    const cidx = i % colours.length
    const tip = pts[pts.length - 1]
    const head: MeshData[] = []
    const whorls: [number, number, number, number][] = [
      [8, 0.03, 62, 0],
      [7, 0.024, 40, 0.01],
      [5, 0.016, 20, 0.019],
      [3, 0.01, 6, 0.026],
    ]
    whorls.forEach(([np, rad, tilt, liftZ], ring) => {
      for (let p = 0; p < np; p++) {
        const pa = (TAU * p) / np + ring * 0.42
        const pet = petalBlade(rad, rad * 0.62, rad * 0.34)
        mlib.rotX(pet, ((90 - tilt) * Math.PI) / 180)
        mlib.rotateZ(pet, pa)
        mlib.translate(pet, [tip[0] + rad * 0.16 * Math.cos(pa), tip[1] + rad * 0.16 * Math.sin(pa), tip[2] + liftZ])
        head.push(pet)
      }
    })
    let list = heads.get(cidx)
    if (!list) {
      list = []
      heads.set(cidx, list)
    }
    list.push(...head)
  }
  const ost = mlib.join(stems)
  mlib.translate(ost, [x, y, z])
  world.add(ost, M.get('prop_stem'))
  if (vs) {
    const v = vase(vs[0], vs[1], vs[2])
    // bedded a millimetre into the top, the way the build seats its cups:
    // dead level with it, the coincident faces shimmer through the glass
    mlib.translate(v.md, [x, y, z - 0.001])
    world.add(v.md, v.mat)
  }
  for (const [cidx, list] of heads) {
    const md = mlib.join(list)
    mlib.translate(md, [x, y, z])
    world.add(md, M.petal('petal_' + colours[cidx], colours[cidx]))
  }
}

export function urnPlanter(world: World, x: number, y: number, z: number, r = 0.24, h = 0.6, colour = '4E6B4A'): void {
  const body = mlib.revolve(
    [
      [0, 0],
      [r * 0.62, 0],
      [r * 0.66, 0.03],
      [r * 0.82, 0.11],
      [r * 0.98, 0.3],
      [r, 0.43],
      [r * 0.92, h - 0.07],
      [r * 0.98, h - 0.03],
      [r * 1.03, h],
      [r * 0.94, h],
      [r * 0.88, h - 0.04],
      [r * 0.86, 0.12],
      [r * 0.54, 0.03],
      [0, 0.03],
    ],
    30,
  )
  mlib.smoothShade(body, 38)
  mlib.translate(body, [x, y, z])
  world.add(body, M.paint('urn_' + colour, colour, { rough: 0.4, coat: 0.25, bump: 0.1 }))
  world.box2(x - r * 1.05, y - r * 1.05, x + r * 1.05, y + r * 1.05, 0, z + h)
}

/** A leafy floor plant: terracotta pot, fronds swept from the crown.  Like
 * f_layout's settle(), an optional `ground` callback lifts the whole piece by
 * its full plan footprint - fronds overhang rugs the pot itself misses. */
export function potted(
  world: World,
  x: number,
  y: number,
  z: number,
  r = 0.24,
  ph = 0.4,
  sp = 0.95,
  ground?: (x0: number, y0: number, x1: number, y1: number) => number,
): void {
  mats()
  const pot = mlib.revolve(
    [
      [0, 0],
      [r * 0.66, 0],
      [r * 0.7, 0.02],
      [r * 0.92, ph - 0.07],
      [r, ph - 0.04],
      [r * 1.05, ph],
      [r * 0.96, ph],
      [r * 0.92, ph - 0.04],
      [r * 0.62, 0.03],
      [0, 0.03],
    ],
    24,
  )
  mlib.smoothShade(pot, 38)
  const fronds: MeshData[] = []
  for (let i = 0; i < 16; i++) {
    const a = (TAU * (i * 0.618)) % TAU
    const t = (i % 5) / 4
    const ln = sp * (0.55 + 0.45 * t)
    const pts: Vec3[] = []
    const wid: number[] = []
    for (let k = 0; k < 7; k++) {
      const u = k / 6
      pts.push([ln * 0.62 * u * Math.cos(a), ln * 0.62 * u * Math.sin(a), ph + ln * (u - 0.55 * u * u)])
      wid.push(0.055 * Math.sin(Math.PI * Math.min(1, u * 1.15)) + 0.006)
    }
    const rings: Vec3[][] = pts.map((p, pi) =>
      [-1, -0.4, 0, 0.4, 1].map(
        (cc) =>
          [
            p[0] + wid[pi] * Math.cos(a + Math.PI / 2) * cc,
            p[1] + wid[pi] * Math.sin(a + Math.PI / 2) * cc,
            p[2] + wid[pi] * 0.16 * (1 - Math.abs(cc)),
          ] as Vec3,
      ),
    )
    const fr = mlib.loft(rings)
    mlib.solidify(fr, 0.003)
    mlib.smoothShade(fr, 50)
    fronds.push(fr)
  }
  const of = mlib.join(fronds)
  mlib.translate(pot, [x, y, 0])
  mlib.translate(of, [x, y, 0])
  let base = z
  if (ground) {
    let x0 = Infinity
    let y0 = Infinity
    let x1 = -Infinity
    let y1 = -Infinity
    for (const md of [pot, of]) {
      for (const v of md.verts) {
        x0 = Math.min(x0, v[0])
        y0 = Math.min(y0, v[1])
        x1 = Math.max(x1, v[0])
        y1 = Math.max(y1, v[1])
      }
    }
    base = ground(x0, y0, x1, y1)
  }
  mlib.translate(pot, [0, 0, base])
  mlib.translate(of, [0, 0, base])
  world.add(pot, M.paint('pot_terracotta', '8A4A32', { rough: 0.72, bump: 0.22 }))
  world.add(of, M.get('prop_leaf'))
  world.box2(x - r * 1.05, y - r * 1.05, x + r * 1.05, y + r * 1.05, 0, base + ph)
}

// --------------------------------------------------------------- tabletop

/** A china cup, measured: 82 mm rim, 92 mm tall, on a 68 mm foot, with the
 * handle a bezier strap whose ends bury inside the wall. */
export function cup(world: World, x: number, y: number, z: number, colour = 'EDE8DC', saucer = true, rot = 0): void {
  const RIM = 0.041
  const FOOT = 0.0345
  const HT = 0.092
  const parts: MeshData[] = []
  const c = mlib.revolve(
    [
      [0, 0],
      [0.025, 0],
      [0.032, 0.0035],
      [FOOT, 0.009],
      [0.0362, 0.026],
      [0.0392, 0.062],
      [RIM, 0.086],
      [0.0409, HT - 0.0015],
      [0.0398, HT],
      [0.0384, HT - 0.002],
      [0.0378, 0.084],
      [0.0358, 0.056],
      [0.0326, 0.02],
      [0.03, 0.014],
      [0, 0.014],
    ],
    28,
  )
  mlib.smoothShade(c, 44)
  parts.push(c)
  const hp2 = [
    ...mlib.bez([0.039, 0.08], [0.062, 0.0836], [0.0706, 0.0704], [0.0706, 0.0552], 10),
    ...mlib.bez([0.0706, 0.0552], [0.0706, 0.0398], [0.0602, 0.03], [0.0355, 0.03], 10, true),
  ]
  const hp: Vec3[] = hp2.map(([u, v]) => [u, 0, v])
  const sec: Vec2[] = Array.from({ length: 12 }, (_, k) => {
    const t = (k * TAU) / 12
    return [0.0068 * Math.cos(t), 0.0036 * Math.sin(t)] as Vec2
  })
  const hd = mlib.tubeAlong(hp, sec, { up: [0, 1, 0] })
  mlib.smoothShade(hd, 46)
  parts.push(hd)
  if (saucer) {
    const s = mlib.revolve(
      [
        [0, 0],
        [0.03, 0],
        [0.04, 0.0025],
        [0.064, 0.009],
        [0.068, 0.0135],
        [0.0672, 0.0158],
        [0.062, 0.0128],
        [0.043, 0.0075],
        [0.03, 0.0062],
        [0, 0.0058],
      ],
      28,
    )
    mlib.smoothShade(s, 40)
    mlib.translate(c, [0, 0, 0.0062])
    mlib.translate(hd, [0, 0, 0.0062])
    parts.push(s)
  }
  const md = mlib.join(parts)
  if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
  mlib.translate(md, [x, y, z])
  world.add(md, M.paint('china_' + colour, colour, { rough: 0.14, coat: 0.55 }))
}

export function book(world: World, x: number, y: number, z: number, colour = '7A2A22', rot = 0, w = 0.16, d = 0.23, t = 0.028): void {
  mats()
  const cover = mlib.prism(mlib.roundedRect(w, d, 0.004, 2), 0, t)
  mlib.bevel(cover, 0.002, 2)
  const pg = mlib.prism(mlib.roundedRect(w - 0.016, d - 0.013, 0.003, 2), 0.004, t - 0.004)
  mlib.translate(pg, [0.004, 0, 0])
  for (const [md, mat] of [
    [cover, M.paint('book_' + colour, colour, { rough: 0.46, coat: 0.15 })],
    [pg, M.get('prop_paper')],
  ] as [MeshData, THREE.Material][]) {
    if (rot) mlib.rotateZ(md, (rot * Math.PI) / 180)
    mlib.translate(md, [x, y, z])
    world.add(md, mat)
  }
}

/** The acoustic guitar leaning by the entrance. */
export function guitar(world: World, x: number, y: number, z: number, rot = 0, lean = 14): void {
  const bodyPts: Vec2[] = []
  for (let i = 0; i < 52; i++) {
    const a = TAU * (i / 52)
    const rr = 0.17 + 0.052 * Math.cos(2 * a) - 0.02 * Math.cos(4 * a)
    bodyPts.push([rr * Math.sin(a) * 0.86, rr * Math.cos(a) * 1.28])
  }
  const rings: Vec3[][] = []
  const levels: [number, number][] = [
    [-0.02, 0],
    [0, 0.014],
    [0, 0.086],
    [-0.02, 0.1],
  ]
  for (const [o, dz] of levels) {
    rings.push(G.polyOffset(bodyPts, o).map(([px, py]) => [px, dz, py] as Vec3))
  }
  const bd = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(bd, 40)
  const neck = mlib.box(-0.026, 0.03, 0.215, 0.026, 0.078, 0.7)
  mlib.bevel(neck, 0.008, 2)
  const head = mlib.box(-0.038, 0.03, 0.69, 0.038, 0.074, 0.8)
  mlib.bevel(head, 0.005, 2)
  const hole = mlib.revolve(
    [
      [0.044, 0],
      [0.05, 0],
      [0.05, 0.004],
      [0.044, 0.004],
    ],
    22,
  )
  mlib.rotX(hole, -Math.PI / 2)
  mlib.translate(hole, [0, 0.084, 0.3])
  const md = mlib.join([bd, neck, head, hole])
  mlib.rotX(md, (lean * Math.PI) / 180)
  mlib.rotateZ(md, (rot * Math.PI) / 180)
  mlib.translate(md, [x, y, z])
  world.add(md, M.wood('guitar_spruce', { light: 'D9B577', dark: 'A07E44', ring: 40, scale: 0.6 }))
  world.box2(x - 0.25, y - 0.25, x + 0.25, y + 0.25, 0, 0.8)
}
