/** Central Perk mesh helpers: ports of the central_perk add-ons in
 * build_scripts/Central_Perk/mlib.py that the shared lib does not carry
 * (wall_run, poly_offset, densify, mitred tube_along, grid_plane, arc_pts).
 */
import { MeshData, type Vec2, type Vec3, recalcNormals } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'

export type Hole = [number, number, number, number]

/** A straight wall between two plan points, built as ONE welded solid.
 * `t` is measured from the p0->p1 line towards `side` (+1 = left of travel),
 * so the inner face of every wall lands exactly on its layout line.
 * `holes` are (u0, u1, z0, z1) in metres along the run. */
export function wallRun(
  p0: Vec2,
  p1: Vec2,
  t: number,
  z0: number,
  z1: number,
  holes: Hole[] = [],
  side = 1,
  cap0 = true,
  cap1 = true,
): MeshData {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy)
  const ux = dx / length
  const uy = dy / length
  const nx = -uy * t * side
  const ny = ux * t * side

  const q = (v: number): number => Math.round(v * 1e5) / 1e5
  const snapped = holes.map((hh) => hh.map(q) as Hole)
  const us = [...new Set([q(0), q(length), ...snapped.flatMap((hh) => [hh[0], hh[1]])])].sort((a, b) => a - b)
  const zs = [...new Set([q(z0), q(z1), ...snapped.flatMap((hh) => [hh[2], hh[3]])])].sort((a, b) => a - b)
  const nu = us.length - 1
  const nz = zs.length - 1

  const solid = (i: number, j: number): boolean => {
    if (i < 0 || j < 0 || i >= nu || j >= nz) return false
    const u0 = us[i]
    const u1 = us[i + 1]
    const c0 = zs[j]
    const c1 = zs[j + 1]
    for (const [a, b, e, f] of snapped) {
      if (a - 1e-6 <= u0 && u1 <= b + 1e-6 && e - 1e-6 <= c0 && c1 <= f + 1e-6) return false
    }
    return true
  }

  const verts: Vec3[] = []
  const idx = new Map<string, number>()
  const vid = (i: number, j: number, s: number): number => {
    const k = `${i}_${j}_${s}`
    let r = idx.get(k)
    if (r === undefined) {
      r = verts.length
      verts.push([p0[0] + ux * us[i] + (s ? nx : 0), p0[1] + uy * us[i] + (s ? ny : 0), zs[j]])
      idx.set(k, r)
    }
    return r
  }

  const faces: number[][] = []
  for (let i = 0; i < nu; i++) {
    for (let j = 0; j < nz; j++) {
      if (!solid(i, j)) continue
      const a = vid(i, j, 0)
      const b = vid(i + 1, j, 0)
      const c = vid(i + 1, j + 1, 0)
      const e = vid(i, j + 1, 0)
      faces.push([a, b, c, e])
      const a2 = vid(i, j, 1)
      const b2 = vid(i + 1, j, 1)
      const c2 = vid(i + 1, j + 1, 1)
      const e2 = vid(i, j + 1, 1)
      faces.push([e2, c2, b2, a2])
      if (!solid(i, j - 1)) faces.push([b, a, a2, b2])
      if (!solid(i, j + 1)) faces.push([e, c, c2, e2])
      if (!solid(i - 1, j) && (i > 0 || cap0)) faces.push([a, e, e2, a2])
      if (!solid(i + 1, j) && (i < nu - 1 || cap1)) faces.push([c, b, b2, c2])
    }
  }
  const md = MeshData.from(verts, faces)
  recalcNormals(md)
  return md
}

/** Offset a convex-ish CCW polygon outward by d using edge-normal miters. */
export function polyOffset(poly: Vec2[], d: number): Vec2[] {
  const n = poly.length
  const out: Vec2[] = []
  for (let i = 0; i < n; i++) {
    const a = poly[(i - 1 + n) % n]
    const b = poly[i]
    const c = poly[(i + 1) % n]
    let e0x = b[0] - a[0]
    let e0y = b[1] - a[1]
    let e1x = c[0] - b[0]
    let e1y = c[1] - b[1]
    const l0 = Math.hypot(e0x, e0y) || 1
    const l1 = Math.hypot(e1x, e1y) || 1
    e0x /= l0
    e0y /= l0
    e1x /= l1
    e1y /= l1
    const n0: Vec2 = [e0y, -e0x]
    const n1: Vec2 = [e1y, -e1x]
    let mx = n0[0] + n1[0]
    let my = n0[1] + n1[1]
    const ml = Math.hypot(mx, my)
    if (ml < 1e-9) {
      mx = n0[0]
      my = n0[1]
    } else {
      mx /= ml
      my /= ml
    }
    const scale = 1 / Math.max(0.25, mx * n0[0] + my * n0[1])
    out.push([b[0] + mx * d * scale, b[1] + my * d * scale])
  }
  return out
}

export function polyArea(poly: Vec2[]): number {
  let s = 0
  const n = poly.length
  for (let i = 0; i < n; i++) {
    const [x0, y0] = poly[i]
    const [x1, y1] = poly[(i + 1) % n]
    s += x0 * y1 - x1 * y0
  }
  return s * 0.5
}

export function ccw(poly: Vec2[]): Vec2[] {
  return polyArea(poly) > 0 ? [...poly] : [...poly].reverse()
}

/** Insert a point d before and d after every interior corner, so a swept
 * profile's mitre stays confined to the corner. */
export function densify(pts: Vec3[], d = 0.05): Vec3[] {
  const out: Vec3[] = [[...pts[0]] as Vec3]
  for (let i = 1; i < pts.length - 1; i++) {
    const a = pts[i - 1]
    const b = pts[i]
    const c = pts[i + 1]
    const din: Vec3 = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
    const dout: Vec3 = [c[0] - b[0], c[1] - b[1], c[2] - b[2]]
    const li = Math.hypot(...din)
    const lo = Math.hypot(...dout)
    if (li > 2.5 * d) out.push([b[0] - (din[0] / li) * d, b[1] - (din[1] / li) * d, b[2] - (din[2] / li) * d])
    out.push([...b] as Vec3)
    if (lo > 2.5 * d) out.push([b[0] + (dout[0] / lo) * d, b[1] + (dout[1] / lo) * d, b[2] + (dout[2] / lo) * d])
  }
  out.push([...pts[pts.length - 1]] as Vec3)
  return out
}

/** Sweep a closed 2D profile along a 3D path, with the mitre-width correction
 * mlib.py's tube_along(miter=True) applies at interior corners. */
export function tubeAlongMiter(
  path: Vec3[],
  profile: Vec2[],
  opts: { closePath?: boolean; up?: Vec3; cap?: boolean; miter?: boolean } = {},
): MeshData {
  const { closePath = false, up = [0, 0, 1] as Vec3, cap = true, miter = false } = opts
  const P = path
  const n = P.length
  const rings: Vec3[][] = []
  for (let i = 0; i < n; i++) {
    let t: Vec3
    if (i === 0) {
      t = closePath
        ? [P[1][0] - P[n - 1][0], P[1][1] - P[n - 1][1], P[1][2] - P[n - 1][2]]
        : [P[1][0] - P[0][0], P[1][1] - P[0][1], P[1][2] - P[0][2]]
    } else if (i === n - 1) {
      t = closePath
        ? [P[0][0] - P[n - 2][0], P[0][1] - P[n - 2][1], P[0][2] - P[n - 2][2]]
        : [P[n - 1][0] - P[n - 2][0], P[n - 1][1] - P[n - 2][1], P[n - 1][2] - P[n - 2][2]]
    } else {
      t = [P[i + 1][0] - P[i - 1][0], P[i + 1][1] - P[i - 1][1], P[i + 1][2] - P[i - 1][2]]
    }
    const tl = Math.hypot(...t) || 1
    t = [t[0] / tl, t[1] / tl, t[2] / tl]
    let u: Vec3 = [...up] as Vec3
    if (Math.abs(t[0] * u[0] + t[1] * u[1] + t[2] * u[2]) > 0.999) u = [1, 0, 0]
    let s: Vec3 = [t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0]]
    const sl = Math.hypot(...s) || 1
    s = [s[0] / sl, s[1] / sl, s[2] / sl]
    let u2: Vec3 = [s[1] * t[2] - s[2] * t[1], s[2] * t[0] - s[0] * t[2], s[0] * t[1] - s[1] * t[0]]
    const ul = Math.hypot(...u2) || 1
    u2 = [u2[0] / ul, u2[1] / ul, u2[2] / ul]
    let k = 1
    if (miter && i > 0 && i < n - 1) {
      const e: Vec3 = [P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1], P[i][2] - P[i - 1][2]]
      const el = Math.hypot(...e)
      if (el > 1e-9) k = 1 / Math.max(0.4, (e[0] / el) * t[0] + (e[1] / el) * t[1] + (e[2] / el) * t[2])
    }
    rings.push(
      profile.map(([a, b]) => [
        P[i][0] + s[0] * a * k + u2[0] * b,
        P[i][1] + s[1] * a * k + u2[1] * b,
        P[i][2] + s[2] * a * k + u2[2] * b,
      ] as Vec3),
    )
  }
  return mlib.loft(rings, {
    closeU: closePath,
    closeV: true,
    capStart: cap && !closePath,
    capEnd: cap && !closePath,
  })
}

/** A floor plane subdivided into a grid, clipped to the poly's bounds. */
export function gridPlane(poly: Vec2[], z: number, nx: number, ny: number, flip = false): MeshData {
  const xs = poly.map((p) => p[0])
  const ys = poly.map((p) => p[1])
  const x0 = Math.min(...xs)
  const x1 = Math.max(...xs)
  const y0 = Math.min(...ys)
  const y1 = Math.max(...ys)
  const verts: Vec3[] = []
  const faces: number[][] = []
  for (let j = 0; j <= ny; j++) {
    for (let i = 0; i <= nx; i++) {
      verts.push([x0 + ((x1 - x0) * i) / nx, y0 + ((y1 - y0) * j) / ny, z])
    }
  }
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const a = j * (nx + 1) + i
      faces.push([a, a + 1, a + nx + 2, a + nx + 1])
    }
  }
  const md = MeshData.from(verts, faces)
  recalcNormals(md, flip)
  return md
}

export function arcPts(cx: number, cy: number, r: number, a0: number, a1: number, n = 8, skipFirst = false): Vec2[] {
  const out: Vec2[] = []
  for (let i = skipFirst ? 1 : 0; i <= n; i++) {
    const a = a0 + ((a1 - a0) * i) / n
    out.push([cx + r * Math.cos(a), cy + r * Math.sin(a)])
  }
  return out
}
