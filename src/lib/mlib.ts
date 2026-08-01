/** mlib - modelling helpers, ported 1:1 from build_scripts/mlib.py.
 *
 * Everything is real geometry: quad-dominant meshes built from profiles,
 * lathes, lofts and mitred sweeps.  All builders return MeshData in world
 * space, exactly as the Blender build moved vertices rather than objects.
 */
import {
  MeshData,
  type Vec2,
  type Vec3,
  recalcNormals,
  markBox,
  markPrism,
  translate as mTranslate,
  smoothShade,
  bevel as mBevel,
  solidify as mSolidify,
  subsurf as mSubsurf,
} from './mesh'

export const TAU = Math.PI * 2

// ---------------------------------------------------------------- mesh making

export function meshObj(verts: Vec3[], faces: number[][]): MeshData {
  return MeshData.from(
    verts.map((v) => [...v] as Vec3),
    faces.map((f) => [...f]),
  )
}

/** Axis aligned box, 8 verts / 6 quads, outward normals. */
export function box(x0: number, y0: number, z0: number, x1: number, y1: number, z1: number): MeshData {
  const v: Vec3[] = [
    [x0, y0, z0],
    [x1, y0, z0],
    [x1, y1, z0],
    [x0, y1, z0],
    [x0, y0, z1],
    [x1, y0, z1],
    [x1, y1, z1],
    [x0, y1, z1],
  ]
  const f = [
    [3, 2, 1, 0],
    [4, 5, 6, 7],
    [0, 1, 5, 4],
    [1, 2, 6, 5],
    [2, 3, 7, 6],
    [3, 0, 4, 7],
  ]
  const m = MeshData.from(v, f)
  markBox(m, [x0, y0, z0, x1, y1, z1])
  return m
}

/** Extrude a closed 2D polygon (CCW) between two z levels. */
export function prism(poly: Vec2[], z0: number, z1: number, flip = false): MeshData {
  const n = poly.length
  const verts: Vec3[] = []
  for (const p of poly) verts.push([p[0], p[1], z0])
  for (const p of poly) verts.push([p[0], p[1], z1])
  const faces: number[][] = [
    Array.from({ length: n }, (_, i) => n - 1 - i),
    Array.from({ length: n }, (_, i) => n + i),
  ]
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    faces.push([i, j, j + n, i + n])
  }
  const m = MeshData.from(verts, faces)
  recalcNormals(m, flip)
  markPrism(m, poly, z0, z1)
  return m
}

/** Extrude a closed 2D polygon given in (x, z) along Y. */
export function prismXZ(poly: Vec2[], y0: number, y1: number): MeshData {
  const n = poly.length
  const verts: Vec3[] = []
  for (const p of poly) verts.push([p[0], y0, p[1]])
  for (const p of poly) verts.push([p[0], y1, p[1]])
  const faces: number[][] = [
    Array.from({ length: n }, (_, i) => i),
    Array.from({ length: n }, (_, i) => 2 * n - 1 - i),
  ]
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    faces.push([i, j, j + n, i + n])
  }
  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  return m
}

/** Extrude a closed 2D polygon given in (y, z) along X. */
export function prismYZ(poly: Vec2[], x0: number, x1: number): MeshData {
  const n = poly.length
  const verts: Vec3[] = []
  for (const p of poly) verts.push([x0, p[0], p[1]])
  for (const p of poly) verts.push([x1, p[0], p[1]])
  const faces: number[][] = [
    Array.from({ length: n }, (_, i) => i),
    Array.from({ length: n }, (_, i) => 2 * n - 1 - i),
  ]
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n
    faces.push([i, j, j + n, i + n])
  }
  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  return m
}

export type Hole = [number, number, number, number]

/** Flat wall panel in the XZ plane (y = 0..thickness) with rectangular
 * openings.  Built as a welded vertex grid -> perfect manifold quads. */
export function panelWithHoles(w: number, h: number, thickness: number, holes: Hole[] = []): MeshData {
  const xsSet = new Set<number>([0, w])
  const zsSet = new Set<number>([0, h])
  for (const hh of holes) {
    xsSet.add(hh[0])
    xsSet.add(hh[2])
    zsSet.add(hh[1])
    zsSet.add(hh[3])
  }
  const xs = [...xsSet].sort((a, b) => a - b)
  const zs = [...zsSet].sort((a, b) => a - b)
  const nx = xs.length - 1
  const nz = zs.length - 1
  const solid = (i: number, j: number): boolean => {
    if (i < 0 || j < 0 || i >= nx || j >= nz) return false
    const cx0 = xs[i],
      cx1 = xs[i + 1],
      cz0 = zs[j],
      cz1 = zs[j + 1]
    for (const [a, b, c, d] of holes) {
      if (a - 1e-6 <= cx0 && cx1 <= c + 1e-6 && b - 1e-6 <= cz0 && cz1 <= d + 1e-6) return false
    }
    return true
  }
  const idx = new Map<string, number>()
  const verts: Vec3[] = []
  const vid = (i: number, j: number, side: number): number => {
    const k = `${i}_${j}_${side}`
    let r = idx.get(k)
    if (r === undefined) {
      r = verts.length
      verts.push([xs[i], side ? thickness : 0, zs[j]])
      idx.set(k, r)
    }
    return r
  }
  const faces: number[][] = []
  for (let i = 0; i < nx; i++) {
    for (let j = 0; j < nz; j++) {
      if (!solid(i, j)) continue
      const a = vid(i, j, 0),
        b = vid(i + 1, j, 0),
        c = vid(i + 1, j + 1, 0),
        d = vid(i, j + 1, 0)
      faces.push([a, b, c, d]) // front (-y)
      const a2 = vid(i, j, 1),
        b2 = vid(i + 1, j, 1),
        c2 = vid(i + 1, j + 1, 1),
        d2 = vid(i, j + 1, 1)
      faces.push([d2, c2, b2, a2]) // back (+y)
      if (!solid(i, j - 1)) faces.push([b, a, a2, b2])
      if (!solid(i, j + 1)) faces.push([d, c, c2, d2])
      if (!solid(i - 1, j)) faces.push([a, d, d2, a2])
      if (!solid(i + 1, j)) faces.push([c, b, b2, c2])
    }
  }
  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  return m
}

// ---------------------------------------------------------------- lathe / loft

export interface LoftOpts {
  closeU?: boolean
  closeV?: boolean
  weldPoles?: boolean
  capStart?: boolean
  capEnd?: boolean
}

export function loft(rings: Vec3[][], opts: LoftOpts = {}): MeshData {
  const { closeU = false, closeV = false, weldPoles = false, capStart = false, capEnd = false } = opts
  const nu = rings.length
  const nv = rings[0].length
  const verts: Vec3[] = []
  const grid: number[][] = []
  let poleA = -1
  let poleB = -1
  for (let i = 0; i < nu; i++) {
    const row: number[] = []
    for (let j = 0; j < nv; j++) {
      const p = rings[i][j]
      if (weldPoles && j === 0 && Math.abs(p[0]) < 1e-9 && Math.abs(p[1]) < 1e-9) {
        if (poleA < 0) {
          poleA = verts.length
          verts.push([...p] as Vec3)
        }
        row.push(poleA)
        continue
      }
      if (weldPoles && j === nv - 1 && Math.abs(p[0]) < 1e-9 && Math.abs(p[1]) < 1e-9) {
        if (poleB < 0) {
          poleB = verts.length
          verts.push([...p] as Vec3)
        }
        row.push(poleB)
        continue
      }
      row.push(verts.length)
      verts.push([...p] as Vec3)
    }
    grid.push(row)
  }
  const faces: number[][] = []
  const ulim = closeU ? nu : nu - 1
  const vlim = closeV ? nv : nv - 1
  for (let i = 0; i < ulim; i++) {
    const i2 = (i + 1) % nu
    for (let j = 0; j < vlim; j++) {
      const j2 = (j + 1) % nv
      const q = [grid[i][j], grid[i2][j], grid[i2][j2], grid[i][j2]]
      const uq: number[] = []
      for (const k of q) if (!uq.includes(k)) uq.push(k)
      if (uq.length >= 3) faces.push(uq)
    }
  }
  if (closeU && !closeV) {
    // revolve-style: u sweeps around, v is the profile -> cap the profile ends
    if (capStart && grid[0][0] !== grid[1][0]) {
      faces.push(Array.from({ length: nu }, (_, k) => grid[nu - 1 - k][0]))
    }
    if (capEnd && grid[0][nv - 1] !== grid[1][nv - 1]) {
      faces.push(Array.from({ length: nu }, (_, k) => grid[k][nv - 1]))
    }
  } else if (closeV && !closeU) {
    // stacked-ring style: v wraps around, u steps through levels
    if (capStart) faces.push(Array.from({ length: nv }, (_, j) => grid[0][nv - 1 - j]))
    if (capEnd) faces.push(Array.from({ length: nv }, (_, j) => grid[nu - 1][j]))
  }
  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  return m
}

/** profile: list of (r, z).  Sweeps around the Z axis. */
export function revolve(
  profile: Vec2[],
  segments = 32,
  opts: { arc?: number; capStart?: boolean; capEnd?: boolean; close?: boolean } = {},
): MeshData {
  const { arc = TAU, capStart = true, capEnd = true } = opts
  const close = opts.close ?? Math.abs(arc - TAU) < 1e-6
  const nseg = close ? segments : segments + 1
  const rings: Vec3[][] = []
  for (let s = 0; s < nseg; s++) {
    const a = arc * (s / segments)
    const ca = Math.cos(a)
    const sa = Math.sin(a)
    rings.push(profile.map(([r, z]) => [r * ca, r * sa, z] as Vec3))
  }
  return loft(rings, { closeU: close, weldPoles: true, capStart, capEnd })
}

/** Sweep a closed 2D profile (list of (a,b)) along a 3D path. */
export function tubeAlong(
  path: Vec3[],
  profile: Vec2[],
  opts: { closePath?: boolean; up?: Vec3; cap?: boolean } = {},
): MeshData {
  const { closePath = false, up = [0, 0, 1] as Vec3, cap = true } = opts
  const P = path
  const n = P.length
  const rings: Vec3[][] = []
  for (let i = 0; i < n; i++) {
    let t: Vec3
    if (i === 0) {
      t = closePath ? [P[1][0] - P[n - 1][0], P[1][1] - P[n - 1][1], P[1][2] - P[n - 1][2]] : [P[1][0] - P[0][0], P[1][1] - P[0][1], P[1][2] - P[0][2]]
    } else if (i === n - 1) {
      t = closePath
        ? [P[0][0] - P[n - 2][0], P[0][1] - P[n - 2][1], P[0][2] - P[n - 2][2]]
        : [P[n - 1][0] - P[n - 2][0], P[n - 1][1] - P[n - 2][1], P[n - 1][2] - P[n - 2][2]]
    } else {
      t = [P[i + 1][0] - P[i - 1][0], P[i + 1][1] - P[i - 1][1], P[i + 1][2] - P[i - 1][2]]
    }
    const tl = Math.hypot(t[0], t[1], t[2]) || 1
    t = [t[0] / tl, t[1] / tl, t[2] / tl]
    let u: Vec3 = [...up] as Vec3
    if (Math.abs(t[0] * u[0] + t[1] * u[1] + t[2] * u[2]) > 0.999) u = [1, 0, 0]
    let s: Vec3 = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]]
    const sl = Math.hypot(s[0], s[1], s[2]) || 1
    s = [s[0] / sl, s[1] / sl, s[2] / sl]
    let u2: Vec3 = [s[1] * t[2] - s[2] * t[1], s[2] * t[0] - s[0] * t[2], s[0] * t[1] - s[1] * t[0]]
    const ul = Math.hypot(u2[0], u2[1], u2[2]) || 1
    u2 = [u2[0] / ul, u2[1] / ul, u2[2] / ul]
    rings.push(
      profile.map(([a, b]) => [
        P[i][0] + s[0] * a + u2[0] * b,
        P[i][1] + s[1] * a + u2[1] * b,
        P[i][2] + s[2] * a + u2[2] * b,
      ] as Vec3),
    )
  }
  return loft(rings, {
    closeU: closePath,
    closeV: true,
    capStart: cap && !closePath,
    capEnd: cap && !closePath,
  })
}

/** Mitred rectangular frame (picture frame / panel moulding / casing).
 * profile: list of (a, b): a = outward offset in the frame plane,
 * b = offset along the frame normal.  Frame lies in XZ, centred on origin,
 * normal +Y. */
export function sweepRectFrame(w: number, h: number, profile: Vec2[]): MeshData {
  const hw = w * 0.5
  const hh = h * 0.5
  const corners: Vec2[] = [
    [-hw, -hh],
    [hw, -hh],
    [hw, hh],
    [-hw, hh],
  ]
  const dirs: Vec2[] = [
    [-1, -1],
    [1, -1],
    [1, 1],
    [-1, 1],
  ]
  const rings: Vec3[][] = []
  for (let k = 0; k < 4; k++) {
    const [cx, cz] = corners[k]
    const [sx, sz] = dirs[k]
    rings.push(profile.map(([a, b]) => [cx + sx * a, b, cz + sz * a] as Vec3))
  }
  return loft(rings, { closeU: true, closeV: true })
}

/** Sweep a profile around a closed loop that lies in the XZ plane. */
export function sweepPlanarLoop(path: Vec2[], profile: Vec2[], close = true): MeshData {
  const n = path.length
  const rings: Vec3[][] = []
  for (let i = 0; i < n; i++) {
    const p: Vec3 = [path[i][0], 0, path[i][1]]
    const a = path[(i - 1 + n) % n]
    const b = path[(i + 1) % n]
    let t: Vec3 = [b[0] - a[0], 0, b[1] - a[1]]
    const tl = Math.hypot(t[0], t[2]) || 1
    t = [t[0] / tl, 0, t[2] / tl]
    const nn: Vec3 = [t[2], 0, -t[0]] // outward for CCW in XZ
    rings.push(profile.map(([aa, bb]) => [p[0] + nn[0] * aa, bb, p[2] + nn[2] * aa] as Vec3))
  }
  return loft(rings, { closeU: close, closeV: true })
}

// ---------------------------------------------------------------- misc shapes

/** CCW list of (x,y) for a rounded rectangle centred on origin. */
export function roundedRect(w: number, h: number, r: number, seg = 6): Vec2[] {
  const hw = w * 0.5 - r
  const hh = h * 0.5 - r
  const pts: Vec2[] = []
  const corners: [number, number, number][] = [
    [hw, hh, 0],
    [-hw, hh, Math.PI * 0.5],
    [-hw, -hh, Math.PI],
    [hw, -hh, Math.PI * 1.5],
  ]
  for (const [cx, cy, a0] of corners) {
    for (let k = 0; k <= seg; k++) {
      const a = a0 + Math.PI * 0.5 * (k / seg)
      pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)])
    }
  }
  return pts
}

export function circle(r: number, seg = 32, cx = 0, cy = 0, phase = 0): Vec2[] {
  return Array.from({ length: seg }, (_, i) => [
    cx + r * Math.cos(phase + (TAU * i) / seg),
    cy + r * Math.sin(phase + (TAU * i) / seg),
  ] as Vec2)
}

export function bez(p0: Vec2, p1: Vec2, p2: Vec2, p3: Vec2, n = 8, skipFirst = false): Vec2[] {
  const out: Vec2[] = []
  for (let i = skipFirst ? 1 : 0; i <= n; i++) {
    const t = i / n
    const mt = 1 - t
    out.push([
      mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
      mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1],
    ])
  }
  return out
}

/** A plump upholstered cushion: rounded box, lightly subdivided. */
export function cushion(w: number, d: number, h: number, r = 0.06, seg = 6): MeshData {
  const pts = roundedRect(w, d, Math.min(r, Math.min(w, d) * 0.45), seg)
  const levels: [number, number][] = [
    [0.0, 0.86],
    [0.08, 0.985],
    [0.5, 1.055],
    [0.92, 0.985],
    [1.0, 0.86],
  ]
  const rings: Vec3[][] = levels.map(([t, s]) => pts.map(([x, y]) => [x * s, y * s, t * h] as Vec3))
  const ob = loft(rings, { closeV: true, capStart: true, capEnd: true })
  mSubsurf(ob, 1)
  smoothShade(ob, 44)
  return ob
}

/** The boolean-difference stand-in: an outer z-prism hollowed by an inner
 * rounded cavity sunk from above (the tub and the basin).  Same silhouette the
 * Blender boolean produced, built directly as one closed shell. */
export function hollowPrism(
  outerPoly: Vec2[],
  z0: number,
  z1: number,
  innerPoly: Vec2[],
  cavityZ: number,
  rimBevel = 0.012,
): MeshData {
  const n = outerPoly.length
  if (innerPoly.length !== n) {
    // resample inner to match (both are roundedRect with same seg counts in use)
    throw new Error('hollowPrism: outline vertex counts must match')
  }
  const verts: Vec3[] = []
  const rings: Vec3[][] = []
  const push = (poly: Vec2[], z: number) => rings.push(poly.map((p) => [p[0], p[1], z] as Vec3))
  const outIn = insetPolyLocal(outerPoly, rimBevel)
  push(outerPoly, z0)
  push(outerPoly, z1 - rimBevel)
  push(outIn, z1) // rounded-over outer rim edge
  const inOut = insetPolyLocal(innerPoly, -rimBevel)
  push(inOut, z1)
  push(innerPoly, z1 - rimBevel)
  push(innerPoly, cavityZ + rimBevel)
  push(insetPolyLocal(innerPoly, rimBevel), cavityZ)
  const nr = rings.length
  for (const ring of rings) for (const p of ring) verts.push(p)
  const faces: number[][] = []
  for (let i = 0; i < nr - 1; i++) {
    for (let j = 0; j < n; j++) {
      const j2 = (j + 1) % n
      faces.push([i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j])
    }
  }
  faces.push(Array.from({ length: n }, (_, j) => n - 1 - j)) // bottom
  faces.push(Array.from({ length: n }, (_, j) => (nr - 1) * n + j)) // cavity floor
  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  smoothShade(m, 40)
  return m
}

/** A closed, through-cut annular z-prism with rounded inner and outer edges.
 * This is the direct mesh equivalent of beveling a Blender boolean-cut ring,
 * without leaving a false cavity floor across the opening. */
export function annularPrism(outerPoly: Vec2[], innerPoly: Vec2[], z0: number, z1: number, bevelRadius = 0, bevelSegments = 1): MeshData {
  const n = outerPoly.length
  if (innerPoly.length !== n) throw new Error('annularPrism: outline vertex counts must match')

  const radius = Math.max(0, Math.min(bevelRadius, (z1 - z0) / 2 - 1e-5))
  const segments = Math.max(1, bevelSegments)
  const levels: { inset: number; z: number }[] = []
  if (radius > 0) {
    for (let k = 0; k <= segments; k++) {
      const a = (Math.PI / 2) * (k / segments)
      levels.push({ inset: radius * (1 - Math.sin(a)), z: z0 + radius * (1 - Math.cos(a)) })
    }
    for (let k = 0; k <= segments; k++) {
      const a = (Math.PI / 2) * (k / segments)
      levels.push({ inset: radius * (1 - Math.cos(a)), z: z1 - radius * (1 - Math.sin(a)) })
    }
  } else {
    levels.push({ inset: 0, z: z0 }, { inset: 0, z: z1 })
  }

  const verts: Vec3[] = []
  for (const level of levels) {
    for (const [x, y] of insetPolyLocal(outerPoly, level.inset)) verts.push([x, y, level.z])
    for (const [x, y] of insetPolyLocal(innerPoly, -level.inset)) verts.push([x, y, level.z])
  }

  const faces: number[][] = []
  const stride = n * 2
  for (let level = 0; level < levels.length - 1; level++) {
    const a = level * stride
    const b = (level + 1) * stride
    for (let j = 0; j < n; j++) {
      const j2 = (j + 1) % n
      faces.push([a + j, a + j2, b + j2, b + j])
      faces.push([a + n + j2, a + n + j, b + n + j, b + n + j2])
    }
  }

  const bottom = 0
  const top = (levels.length - 1) * stride
  for (let j = 0; j < n; j++) {
    const j2 = (j + 1) % n
    faces.push([bottom + j2, bottom + j, bottom + n + j, bottom + n + j2])
    faces.push([top + j, top + j2, top + n + j2, top + n + j])
  }

  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  smoothShade(m, 40)
  return m
}

function insetPolyLocal(poly: Vec2[], d: number): Vec2[] {
  const n = poly.length
  const out: Vec2[] = []
  for (let i = 0; i < n; i++) {
    const p = poly[i]
    const a = poly[(i - 1 + n) % n]
    const b = poly[(i + 1) % n]
    const e0x = p[0] - a[0]
    const e0y = p[1] - a[1]
    const e1x = b[0] - p[0]
    const e1y = b[1] - p[1]
    const l0 = Math.hypot(e0x, e0y) || 1
    const l1 = Math.hypot(e1x, e1y) || 1
    const n0x = -e0y / l0
    const n0y = e0x / l0
    const n1x = -e1y / l1
    const n1y = e1x / l1
    let bx = n0x + n1x
    let by = n0y + n1y
    const bl = Math.hypot(bx, by)
    if (bl < 1e-6) {
      bx = n0x
      by = n0y
    } else {
      bx /= bl
      by /= bl
    }
    const cosh = Math.max(0.2, bx * n0x + by * n0y)
    out.push([p[0] + (bx * d) / cosh, p[1] + (by * d) / cosh])
  }
  return out
}

// re-exports so scene code can `import * as mlib`
export { translate, rotateZ, rotX, rotY, scaleMesh, transform4, join, recalcNormals, smoothShade, flatShade } from './mesh'
export { MeshData } from './mesh'
export const bevel = mBevel
export const solidify = mSolidify
export const subsurf = mSubsurf
export const translateMesh = mTranslate
