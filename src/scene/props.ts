/** Reusable dressing - port of build_scripts/props.py.  All lathed / lofted
 * geometry, all procedural materials.  RNG call order follows the Python
 * exactly so every shelf holds the same jumble.
 */
import type * as THREE from 'three/webgpu'
import * as mlib from '../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../lib/mesh'
import { PyRandom } from '../lib/rng'
import * as mats from '../mats/mats'
import type { World } from './world'

export type Placed = { md: MeshData; mat: THREE.Material }

// --------------------------------------------------------------- material pool

export function colMat(key: string, hexcol: string, rough = 0.28, coat = 0.4): THREE.Material {
  const k = 'prop_' + key
  return mats.get(k) ?? mats.paint(k, hexcol, { rough, coat, variation: 0.02 })
}

export function palette(seed = 0, n = 26): THREE.Material[] {
  const rng = new PyRandom(seed)
  const hexes = [
    'E4DFD2', 'D9CBB0', 'C8452F', 'D97B2B', 'E8B93C', '6E9E4C', '2E7D9A', '3E4C8A',
    '8C4A7A', '9B2F30', '4C4A46', 'F0EDE6', 'BFC9CC', 'A8763E', '6B3F2A', 'D8A0A8',
    '7FB2A5', 'EAD6A0', '2F5C3A', '8E9AA8', 'C6D2B0', 'E2C9E0', '3A3A44', 'B8543A',
    '5E7BA8', 'DAB86A',
  ]
  const out: THREE.Material[] = []
  for (let i = 0; i < n; i++) {
    const rough = rng.uniform(0.12, 0.55)
    const coat = rng.uniform(0.1, 0.6)
    out.push(colMat(`c${i}`, hexes[i % hexes.length], rough, coat))
  }
  return out
}

// ------------------------------------------------------------------- crockery

export function jar(r = 0.045, h = 0.13, neck = 0.62, lid = true, mat?: THREE.Material, lidmat?: THREE.Material): Placed[] {
  const p: Vec2[] = [
    [0.0, 0.0],
    [r * 0.92, 0.004],
    [r, 0.022],
    [r, h * 0.72],
    [r * neck, h * 0.86],
    [r * neck, h],
  ]
  const ob = mlib.revolve(p, 22)
  mlib.smoothShade(ob, 34)
  const out: Placed[] = [{ md: ob, mat: mat! }]
  if (lid) {
    const lp: Vec2[] = [
      [0.0, 0.0],
      [r * neck + 0.004, 0.0],
      [r * neck + 0.004, 0.016],
      [r * neck * 0.7, 0.02],
      [0.0, 0.02],
    ]
    const lo = mlib.revolve(lp, 22)
    mlib.translate(lo, [0, 0, h])
    mlib.smoothShade(lo, 40)
    out.push({ md: lo, mat: lidmat ?? mat! })
  }
  return out
}

export function can(r = 0.038, h = 0.11, mat?: THREE.Material): Placed[] {
  const ob = mlib.revolve(
    [
      [0.0, 0.0],
      [r, 0.006],
      [r, h - 0.006],
      [r * 0.96, h],
      [0.0, h],
    ],
    20,
  )
  mlib.smoothShade(ob, 38)
  return [{ md: ob, mat: mat! }]
}

export function bottle(r = 0.036, h = 0.28, mat?: THREE.Material): Placed[] {
  const ob = mlib.revolve(
    [
      [0.0, 0.0],
      [r * 0.9, 0.004],
      [r, 0.02],
      [r, h * 0.52],
      [r * 0.72, h * 0.62],
      [r * 0.3, h * 0.72],
      [r * 0.26, h * 0.94],
      [r * 0.3, h],
      [0.0, h],
    ],
    22,
  )
  mlib.smoothShade(ob, 40)
  return [{ md: ob, mat: mat! }]
}

export function cup(r = 0.042, h = 0.085, mat?: THREE.Material, handle = true): Placed[] {
  const p: Vec2[] = [
    [0.0, 0.0],
    [r * 0.62, 0.0],
    [r * 0.7, 0.008],
    [r * 0.86, h * 0.4],
    [r, h],
    [r - 0.004, h],
    [r * 0.82, h * 0.4],
    [r * 0.6, 0.01],
    [0.0, 0.01],
  ]
  const ob = mlib.revolve(p, 20)
  mlib.smoothShade(ob, 36)
  const parts = [ob]
  if (handle) {
    const path: Vec3[] = []
    for (let i = 0; i < 9; i++) {
      const t = i / 8.0
      const a = Math.PI * (t - 0.5)
      path.push([r * 0.92 + 0.03 * Math.cos(a), 0.0, h * 0.62 + 0.03 * Math.sin(a) * 1.3])
    }
    parts.push(mlib.tubeAlong(path, mlib.circle(0.0055, 8)))
  }
  const joined = mlib.join(parts)
  return [{ md: joined, mat: mat! }]
}

export function bowl(r = 0.1, h = 0.055, mat?: THREE.Material): Placed[] {
  const p: Vec2[] = [
    [0.0, 0.0],
    [r * 0.42, 0.0],
    [r * 0.5, 0.006],
    [r * 0.78, h * 0.5],
    [r, h],
    [r - 0.004, h],
    [r * 0.74, h * 0.5],
    [r * 0.44, 0.008],
    [0.0, 0.008],
  ]
  const ob = mlib.revolve(p, 26)
  mlib.smoothShade(ob, 34)
  return [{ md: ob, mat: mat! }]
}

export function plateStack(r = 0.105, n = 4, mat?: THREE.Material): Placed[] {
  const parts: MeshData[] = []
  for (let i = 0; i < n; i++) {
    const p: Vec2[] = [
      [0.0, 0.0],
      [r * 0.5, 0.0],
      [r * 0.72, 0.004],
      [r, 0.014],
      [r - 0.003, 0.016],
      [r * 0.68, 0.009],
      [r * 0.46, 0.005],
      [0.0, 0.005],
    ]
    const o = mlib.revolve(p, 24)
    mlib.translate(o, [0, 0, i * 0.016])
    parts.push(o)
  }
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 34)
  return [{ md: ob, mat: mat! }]
}

export function stemware(r = 0.035, h = 0.155, mat?: THREE.Material): Placed[] {
  const bowlZ = h * 0.42
  const p: Vec2[] = [
    [0.0, 0.0],
    [r * 0.86, 0.0],
    [r * 0.9, 0.004],
    [r * 0.34, 0.01],
    [(0.0175 * r) / 0.035, 0.02],
    [(0.0165 * r) / 0.035, bowlZ * 0.86],
    [r * 0.42, bowlZ],
    [r * 0.86, bowlZ + (h - bowlZ) * 0.36],
    [r, bowlZ + (h - bowlZ) * 0.74],
    [r * 0.94, h],
    [r * 0.94 - 0.0012, h],
    [r * 0.86, bowlZ + (h - bowlZ) * 0.74],
    [r * 0.3, bowlZ + 0.004],
    [0.0, bowlZ + 0.006],
  ]
  const ob = mlib.revolve(p, 24)
  mlib.smoothShade(ob, 44)
  return [{ md: ob, mat: mat! }]
}

export function carton(w = 0.075, d = 0.05, h = 0.16, mat?: THREE.Material, band?: THREE.Material | null): Placed[] {
  const ob = mlib.box(-w / 2, -d / 2, 0, w / 2, d / 2, h)
  mlib.bevel(ob, 0.003, 2)
  const out: Placed[] = [{ md: ob, mat: mat! }]
  if (band) {
    const z0 = h * new PyRandom(Math.trunc(w * 9973)).uniform(0.3, 0.52)
    const lb = mlib.box(-w / 2 - 0.0008, -d / 2 - 0.0008, z0, w / 2 + 0.0008, d / 2 + 0.0008, z0 + h * 0.26)
    mlib.bevel(lb, 0.0022, 2)
    out.push({ md: lb, mat: band })
  }
  return out
}

export function book(w = 0.16, t = 0.032, h = 0.225, mat?: THREE.Material): Placed[] {
  const ob = mlib.box(-w / 2, -t / 2, 0, w / 2, t / 2, h)
  mlib.bevel(ob, 0.0025, 2)
  return [{ md: ob, mat: mat! }]
}

const ITEMS: [string, number][] = [
  ['jar', 0.18],
  ['can', 0.14],
  ['bottle', 0.12],
  ['cup', 0.12],
  ['bowl', 0.1],
  ['plates', 0.14],
  ['carton', 0.08],
  ['book', 0.03],
  ['stem', 0.09],
]

/** Scatter believable crockery along a shelf running p0->p1 at height z. */
export function fillShelf(
  w: World,
  p0: Vec2,
  p1: Vec2,
  z: number,
  depth: number,
  seed = 0,
  maxh = 0.2,
  density = 1.0,
  matsPool?: THREE.Material[],
  back = 0.55,
  fill = 1.0,
): void {
  const rng = new PyRandom(seed)
  const pool = matsPool ?? palette(seed)
  const gl = [
    mats.get('glass_thick') ?? mats.pane('glass_thick', { tint: 'E8EEEA', baseAlpha: 0.16, edge: 0.72 }),
    mats.get('glass_clear') ?? mats.pane('glass_clear'),
  ]
  const brass = [
    mats.get('shelf_brass') ?? mats.metal('shelf_brass', 'A8813C', { rough: 0.34, bump: 0.05 }),
    mats.get('shelf_copper') ?? mats.metal('shelf_copper', 'A96A38', { rough: 0.36, bump: 0.06 }),
  ]
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const ln = Math.hypot(dx, dy)
  const ux = dx / ln
  const uy = dy / ln
  const nx = uy
  const ny = -ux
  const span = ln * Math.max(0.12, Math.min(1.0, fill))
  let u = rng.uniform(0.02, 0.06) + (ln - span) * rng.random()
  const stop = u + span
  let grp = rng.randint(3, 6)
  while (u < Math.min(stop, ln - 0.05)) {
    const kind = rng.choicesWeighted(
      ITEMS.map(([k]) => k),
      ITEMS.map(([, wt]) => wt),
    )
    let m = rng.choice(pool)
    if (['jar', 'bottle', 'cup', 'stem'].includes(kind) && rng.random() < 0.3) {
      m = rng.choice(gl)
    } else if (['bowl', 'jar'].includes(kind) && rng.random() < 0.16) {
      m = rng.choice(brass)
    }
    const v = depth * back + rng.uniform(-0.03, 0.03)
    let objs: Placed[]
    let wid: number
    if (kind === 'jar') {
      const r = rng.uniform(0.03, 0.052)
      const h = Math.min(maxh, rng.uniform(0.09, 0.17))
      objs = jar(r, h, 0.62, true, m, rng.choice(pool))
      wid = 2 * r
    } else if (kind === 'can') {
      const r = rng.uniform(0.028, 0.042)
      const h = Math.min(maxh, rng.uniform(0.08, 0.13))
      objs = can(r, h, m)
      wid = 2 * r
    } else if (kind === 'bottle') {
      const r = rng.uniform(0.026, 0.04)
      const h = Math.min(maxh + 0.04, rng.uniform(0.16, 0.26))
      objs = bottle(r, h, m)
      wid = 2 * r
    } else if (kind === 'cup') {
      const r = rng.uniform(0.034, 0.046)
      objs = cup(r, rng.uniform(0.07, 0.095), m)
      wid = 2.6 * r
    } else if (kind === 'bowl') {
      const r = rng.uniform(0.075, 0.115)
      objs = bowl(r, rng.uniform(0.045, 0.07), m)
      wid = 2 * r
    } else if (kind === 'plates') {
      const r = rng.uniform(0.085, 0.115)
      objs = plateStack(r, rng.randint(2, 5), m)
      wid = 2 * r
    } else if (kind === 'carton') {
      const cw = rng.uniform(0.055, 0.095)
      objs = carton(cw, rng.uniform(0.04, 0.07), Math.min(maxh, rng.uniform(0.1, 0.19)), m, rng.random() < 0.75 ? rng.choice(pool) : null)
      wid = cw
    } else if (kind === 'stem') {
      const r = rng.uniform(0.03, 0.04)
      objs = stemware(r, Math.min(maxh, rng.uniform(0.13, 0.175)), m)
      wid = 2.05 * r
    } else {
      const bw = rng.uniform(0.12, 0.19)
      objs = book(bw, rng.uniform(0.026, 0.05), Math.min(maxh, rng.uniform(0.17, 0.225)), m)
      wid = rng.uniform(0.026, 0.05)
    }
    u += wid * 0.5
    const ang = rng.uniform(-0.5, 0.5)
    for (const o of objs) {
      if (kind === 'carton' || kind === 'book') {
        mlib.rotateZ(o.md, Math.atan2(uy, ux) + ang)
      }
      mlib.translate(o.md, [p0[0] + ux * u + nx * v, p0[1] + uy * u + ny * v, z])
      w.add(o.md, o.mat)
    }
    grp -= 1
    if (grp <= 0) {
      grp = rng.randint(3, 6)
      u += wid * 0.5 + rng.uniform(0.022, 0.08) / density
    } else {
      u += wid * 0.5 + rng.uniform(0.001, 0.01) / density
    }
  }
}

// ---------------------------------------------------------------------- plants

export function leafBlade(ln = 0.22, w = 0.035, seg = 7, curl = 0.5, peak = 0.5): MeshData {
  const rings: Vec3[][] = []
  for (let i = 0; i <= seg; i++) {
    const t = i / seg
    const u = t < peak ? t / peak : 1.0 - (t - peak) / (1.0 - peak)
    const ww = w * Math.max(0.0, u) ** 0.55
    const droop = -curl * ln * t * t * 0.5
    const fold = 0.34 * ww
    rings.push([
      [-ww, ln * t, droop - fold * 0.3],
      [-ww * 0.55, ln * t, droop + fold * 0.55],
      [0.0, ln * t, droop + fold],
      [ww * 0.55, ln * t, droop + fold * 0.55],
      [ww, ln * t, droop - fold * 0.3],
    ])
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.0016)
  mlib.smoothShade(ob, 50)
  return ob
}

export function fern(
  w: World,
  loc: Vec3,
  r = 0.24,
  n = 26,
  seed = 1,
  pot = true,
  leafmat?: THREE.Material,
  potmat?: THREE.Material,
  scale = 1.0,
): void {
  const rng = new PyRandom(seed)
  const fronds: MeshData[] = []
  for (let i = 0; i < n; i++) {
    const a = rng.uniform(0, Math.PI * 2)
    const tilt = rng.uniform(0.55, 1.35)
    const ln = r * rng.uniform(0.7, 1.25) * scale
    const zfloor = -(loc[2] - 0.035)
    const stemPts: Vec3[] = []
    for (let k = 0; k < 9; k++) {
      const t = k / 8.0
      const zz = ln * (0.55 * Math.sin(t * 1.9) - tilt * 0.85 * t * t)
      stemPts.push([Math.cos(a) * ln * t, Math.sin(a) * ln * t, Math.max(zz, zfloor)])
    }
    fronds.push(mlib.tubeAlong(stemPts, mlib.circle(0.0035, 5)))
    for (let k = 1; k < 8; k++) {
      const t = k / 8.0
      for (const s of [-1, 1]) {
        const lf = leafBlade(ln * 0.3 * (1 - 0.55 * t), 0.016 * scale, 5, 0.7)
        mlib.rotateZ(lf, a + s * rng.uniform(1.0, 1.4))
        mlib.rotX(lf, rng.uniform(-0.35, 0.1))
        mlib.translate(lf, stemPts[k])
        fronds.push(lf)
      }
    }
  }
  const ob = mlib.join(fronds)
  if (leafmat) {
    mlib.translate(ob, loc)
    w.add(ob, leafmat)
  }
  if (pot) {
    const p: Vec2[] = [
      [0.0, 0.0],
      [r * 0.42, 0.0],
      [r * 0.46, 0.012],
      [r * 0.55, r * 0.55],
      [r * 0.6, r * 0.62],
      [r * 0.555, r * 0.62],
      [r * 0.5, r * 0.55],
      [r * 0.4, 0.014],
      [0.0, 0.014],
    ]
    const po = mlib.revolve(p, 26)
    mlib.smoothShade(po, 34)
    mlib.translate(po, [loc[0], loc[1], loc[2] - r * 0.62])
    if (potmat) w.add(po, potmat, { collide: true })
  }
}

export function trailingPlant(
  w: World,
  loc: Vec3,
  n = 14,
  seed = 2,
  leafmat?: THREE.Material,
  potmat?: THREE.Material,
  r = 0.11,
): void {
  const rng = new PyRandom(seed)
  const parts: MeshData[] = []
  for (let i = 0; i < n; i++) {
    const a = rng.uniform(0, Math.PI * 2)
    const ln = rng.uniform(0.22, 0.55)
    const pts: Vec3[] = []
    for (let k = 0; k < 10; k++) {
      const t = k / 9.0
      pts.push([
        Math.cos(a) * ln * 0.55 * t ** 0.7,
        Math.sin(a) * ln * 0.55 * t ** 0.7,
        0.1 * Math.sin(t * 2.4) - ln * t ** 1.7,
      ])
    }
    parts.push(mlib.tubeAlong(pts, mlib.circle(0.0028, 5)))
    for (let k = 2; k < 10; k++) {
      const lf = leafBlade(rng.uniform(0.07, 0.105), rng.uniform(0.042, 0.058), 6, 0.25, 0.34)
      mlib.rotateZ(lf, a + rng.uniform(-2.2, 2.2))
      mlib.rotX(lf, rng.uniform(-0.7, 0.2))
      mlib.translate(lf, pts[k])
      parts.push(lf)
    }
  }
  const ob = mlib.join(parts)
  mlib.translate(ob, loc)
  if (leafmat) w.add(ob, leafmat)
  const p: Vec2[] = [
    [0.0, 0.0],
    [r * 0.7, 0.0],
    [r * 0.78, 0.012],
    [r, r * 0.85],
    [r * 1.04, r * 0.95],
    [r * 0.98, r * 0.95],
    [r * 0.94, r * 0.85],
    [r * 0.66, 0.014],
    [0.0, 0.014],
  ]
  const po = mlib.revolve(p, 22)
  mlib.smoothShade(po, 34)
  mlib.translate(po, [loc[0], loc[1], loc[2] - r * 0.95])
  if (potmat) w.add(po, potmat)
}

// ------------------------------------------------------------------ framed art

export function framed(
  w: World,
  width: number,
  h: number,
  loc: Vec3,
  normal: Vec2,
  framemat?: THREE.Material,
  artmat?: THREE.Material,
  matW = 0.055,
  fw = 0.032,
  fd = 0.026,
  matmat?: THREE.Material,
): void {
  const prof: Vec2[] = [
    [-fw / 2, 0.0015],
    [-fw / 2, fd * 0.55],
    [-fw / 2 + 0.006, fd],
    [fw / 2 - 0.008, fd * 0.92],
    [fw / 2 - 0.004, fd * 0.42],
    [fw / 2, fd * 0.3],
    [fw / 2, 0.0015],
  ]
  const fr = mlib.sweepRectFrame(width + fw, h + fw, prof)
  const parts: Placed[] = [{ md: fr, mat: framemat! }]
  if (matW > 0) {
    const mb = mlib.panelWithHoles(width, h, 0.004, [[matW, matW, width - matW, h - matW]])
    mlib.translate(mb, [-width / 2, 0, -h / 2])
    mlib.translate(mb, [0, fd * 0.22, 0])
    parts.push({ md: mb, mat: matmat ?? mats.paint('mount_cream', 'EDE6D2', { rough: 0.75, coat: 0.0 }) })
  }
  const art = mlib.box(-width / 2 + 0.004, fd * 0.3, -h / 2 + 0.004, width / 2 - 0.004, fd * 0.3 + 0.003, h / 2 - 0.004)
  // Give both paper faces a full, consistently oriented UV rectangle. Most
  // art remains procedural, while asset-backed pieces (the Jouets poster) can
  // now use the same dimensioned frame without a bespoke render mesh.
  art.uvs = [
    null,
    null,
    [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 1],
    ],
    null,
    [
      [0, 0],
      [1, 0],
      [1, 1],
      [0, 1],
    ],
    null,
  ]
  parts.push({ md: art, mat: artmat! })
  const ang = Math.atan2(normal[1], normal[0]) - Math.PI / 2
  for (const ob of parts) {
    mlib.rotateZ(ob.md, ang)
    mlib.translate(ob.md, loc)
    w.add(ob.md, ob.mat)
  }
}

// ---------------------------------------------------------------------- drapes

/** A draped fabric swag: straight at the rod, sagging in the middle. */
export function swag(x0: number, x1: number, ztop: number, sag = 0.34, depth = 0.14, folds = 7, nseg = 48): MeshData {
  const rings: Vec3[][] = []
  const w = x1 - x0
  for (let i = 0; i <= nseg; i++) {
    const u = i / nseg
    const x = x0 + w * u
    const rip = Math.sin(u * folds * Math.PI)
    const col: Vec3[] = []
    for (let j = 0; j < 9; j++) {
      const v = j / 8.0
      const drop = sag * Math.sin(Math.PI * u) ** 0.85 * v
      const yy = depth * (0.35 + 0.65 * v) * (0.55 + 0.45 * rip)
      col.push([x, yy, ztop - drop - 0.02 * v * v])
    }
    rings.push(col)
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.006)
  mlib.smoothShade(ob, 55)
  return ob
}

/** Cascading tail beside a window. */
export function jabot(x: number, ztop: number, ln = 1.05, w = 0.2, depth = 0.13, side = 1): MeshData {
  const rings: Vec3[][] = []
  for (let i = 0; i < 15; i++) {
    const t = i / 14.0
    const col: Vec3[] = []
    for (let j = 0; j < 25; j++) {
      const v = j / 24.0
      const fold = Math.sin(v * 3.4 * Math.PI + t * 1.4)
      col.push([
        x + side * (w * v * (0.55 + 0.45 * t)),
        depth * (0.25 + 0.75 * v) * (0.6 + 0.4 * fold),
        ztop - ln * t - 0.1 * v * t,
      ])
    }
    rings.push(col)
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.006)
  mlib.smoothShade(ob, 55)
  return ob
}

/** Long curtain with vertical folds, gathered at the top (see props.py). */
export function curtainPanel(
  x0: number,
  x1: number,
  ztop: number,
  zbot: number,
  depth = 0.1,
  folds = 9,
  gather = 0.55,
  flare = 1.25,
  seed = 0,
  hem = 0.0,
  fullness = 2.2,
): MeshData {
  const rng = new PyRandom(seed)
  const s1 = rng.uniform(0, Math.PI * 2)
  const s2 = rng.uniform(0, Math.PI * 2)
  const s3 = rng.uniform(0, Math.PI * 2)
  const rings: Vec3[][] = []
  const w = x1 - x0
  const nseg = Math.max(48, folds * 16)
  const kmax = Math.sqrt(Math.max(fullness * fullness - 1.0, 0.0) / 2.0) / Math.PI
  const spread = (v: number) => 0.86 + 0.14 * v
  const ampF = (u: number, v: number, k: number) => {
    const vary = 1.0 + 0.22 * Math.sin(u * folds * 1.3 + v * 2.1 + s3)
    return depth * k * vary * (gather + (1 - gather) * v) * flare ** v
  }
  const kF = (u: number) => 1.0 + 0.3 * Math.sin(u * folds * 2.0 + s1) + 0.17 * Math.sin(u * folds * 3.7 + s2)
  let scale = 1.0
  for (let i = 0; i <= nseg; i++) {
    const u = i / nseg
    for (let j = 0; j < 13; j++) {
      const v = j / 12.0
      const a = ampF(u, v, kF(u))
      if (a > 1e-9) scale = Math.min(scale, ((kmax * w * spread(v)) / (folds + 0.72)) / a)
    }
  }
  for (let i = 0; i <= nseg; i++) {
    const u = i / nseg
    const k = kF(u)
    const col: Vec3[] = []
    for (let j = 0; j < 13; j++) {
      const v = j / 12.0
      const ph = (u * folds + 0.14 * Math.sin(v * 2.3 + u * 5.1)) * Math.PI * 2
      const amp = ampF(u, v, k) * scale
      const xx = x0 + w * (u * spread(v))
      const yy = amp * Math.sin(ph)
      let zz = ztop - (ztop - zbot) * v
      if (hem) {
        zz += hem * v ** 3 * (0.5 + 0.5 * Math.sin(u * folds * 1.7 + s3))
      }
      col.push([xx, yy, zz])
    }
    rings.push(col)
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.0035)
  mlib.smoothShade(ob, 55)
  return ob
}

// --------------------------------------------------------------------- lamps

export function pleatedShade(rt = 0.09, rb = 0.17, h = 0.19, pleats = 26): MeshData {
  const cols: Vec3[][] = []
  for (let i = 0; i < pleats * 2; i++) {
    const a = (Math.PI * 2 * i) / (pleats * 2)
    const k = i % 2 === 0 ? 0.022 : -0.01
    cols.push([
      [rt * (1 + k) * Math.cos(a), rt * (1 + k) * Math.sin(a), h],
      [rb * (1 + k) * Math.cos(a), rb * (1 + k) * Math.sin(a), 0.0],
    ])
  }
  const ob = mlib.loft(cols, { closeU: true })
  mlib.solidify(ob, 0.0035)
  mlib.smoothShade(ob, 24)
  return ob
}

export function bulb(e = 40.0, r = 0.028): Placed {
  // Under the Python build's cache-then-rebuild flow the shared 'bulb_warm'
  // material ends the build at the pendant's strength 46; use that final state.
  void e
  const p: Vec2[] = [
    [0.0, 0.0],
    [r, 0.014],
    [r * 1.1, 0.038],
    [r * 0.85, 0.062],
    [r * 0.4, 0.074],
    [r * 0.4, 0.094],
    [0.0, 0.094],
  ]
  const ob = mlib.revolve(p, 18)
  mlib.smoothShade(ob, 40)
  const mat = mats.get('bulb_warm') ?? mats.emissive('bulb_warm', 'FFE0AE', { strength: 46.0, base: 'FFF3E2' })
  return { md: ob, mat }
}

/** Small opal ceiling fitting - a dome on a ring, bulb inside, lamp at the
 * bulb. */
export function flushDome(
  w: World,
  loc: Vec3,
  r = 0.115,
  energy = 16.0,
  colr: [number, number, number] = [1.0, 0.86, 0.7],
  drop = 0.075,
): void {
  const ring = mlib.revolve(
    [
      [0.0, 0.0],
      [r * 0.8, -0.004],
      [r * 0.84, -0.016],
      [r * 0.62, -0.024],
      [0.0, -0.026],
    ],
    20,
  )
  const brassMat = mats.get('shelf_brass') ?? mats.metal('shelf_brass', 'A8813C', { rough: 0.34, bump: 0.05 })
  mlib.translate(ring, loc)
  w.add(ring, brassMat)
  const prof: Vec2[] = []
  for (let i = 0; i < 13; i++) {
    const t = i / 12.0
    const a = Math.PI * 0.5 * t
    prof.push([r * Math.sin(a), -0.018 - drop * (1.0 - Math.cos(a))])
  }
  const sh = mlib.revolve(prof, 26, { capStart: false, capEnd: false })
  mlib.solidify(sh, 0.004)
  mlib.smoothShade(sh, 46)
  const opal = mats.get('opal_shade') ?? mats.emissive('opal_shade', 'FFF0D2', { strength: 2.2, base: 'F6EEDC' })
  mlib.translate(sh, loc)
  w.add(sh, opal)
  const bl = bulb(24.0, 0.02)
  mlib.translate(bl.md, [0, 0, -drop - 0.03])
  mlib.translate(bl.md, loc)
  w.add(bl.md, bl.mat)
  w.pointLight([loc[0], loc[1], loc[2] - drop * 0.55], energy, colr, 0.07)
}

/** Linear-sRGB tint of a Planckian radiator at `kelvin` (props.blackbody). */
export function blackbody(kelvin: number): [number, number, number] {
  const g = (x: number, mu: number, s1: number, s2: number) =>
    Math.exp(-(((x - mu) / (x < mu ? s1 : s2)) ** 2) / 2.0)
  let X = 0
  let Y = 0
  let Z = 0
  for (let nm = 380; nm <= 780; nm += 5) {
    const lm = nm * 1e-9
    const sp = 1.0 / (lm ** 5 * (Math.exp(1.4387769e-2 / (lm * kelvin)) - 1.0))
    X += sp * (1.056 * g(nm, 599.8, 37.9, 31.0) + 0.362 * g(nm, 442.0, 16.0, 26.7) - 0.065 * g(nm, 501.1, 20.4, 26.2))
    Y += sp * (0.821 * g(nm, 568.8, 46.9, 40.5) + 0.286 * g(nm, 530.9, 16.3, 31.1))
    Z += sp * (1.217 * g(nm, 437.0, 11.8, 36.0) + 0.681 * g(nm, 459.0, 26.0, 13.8))
  }
  const rgb: [number, number, number] = [
    3.2406 * X - 1.5372 * Y - 0.4986 * Z,
    -0.9689 * X + 1.8758 * Y + 0.0415 * Z,
    0.0557 * X - 0.204 * Y + 1.057 * Z,
  ]
  const m = Math.max(...rgb)
  return [Math.max(rgb[0] / m, 0), Math.max(rgb[1] / m, 0), Math.max(rgb[2] / m, 0)]
}
