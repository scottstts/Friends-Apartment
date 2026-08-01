/** Walls, mouldings and profiles - port of build_scripts/s_walls.py.
 * Each wall is one closed solid panel whose inner face sits exactly on the
 * room boundary and whose body extends outward.
 */
import * as L from '../lib/L'
import * as mlib from '../lib/mlib'
import { MeshData, faceNormal, type Vec2 } from '../lib/mesh'

export type Hole = [number, number, number, number]

/** Wall whose inner face runs p0->p1 (interior on the RIGHT of travel).
 * holes: (u0, z0, u1, z1) in wall-local coords measured from p0/floor. */
export function wall(
  p0: Vec2,
  p1: Vec2,
  z0: number,
  z1: number,
  t: number,
  holes: Hole[] = [],
): MeshData {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const ln = Math.hypot(dx, dy)
  const ux = dx / ln
  const uy = dy / ln
  const hh: Hole[] = holes.map((h) => [h[0], h[1] - z0, h[2], h[3] - z0])
  const ob = mlib.panelWithHoles(ln, z1 - z0, t, hh)
  mlib.transform4(ob, [
    [ux, -uy, 0, p0[0]],
    [uy, ux, 0, p0[1]],
    [0, 0, 1, z0],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(ob)
  return ob
}

/** Assign material slot `index` to faces where pred(center, normal). */
export function faceMat(
  md: MeshData,
  index: number,
  pred: (c: [number, number, number], n: [number, number, number]) => boolean,
): MeshData {
  if (!md.faceMat) md.faceMat = md.faces.map(() => 0)
  md.faces.forEach((f, fi) => {
    let cx = 0,
      cy = 0,
      cz = 0
    for (const vi of f) {
      cx += md.verts[vi][0]
      cy += md.verts[vi][1]
      cz += md.verts[vi][2]
    }
    const c: [number, number, number] = [cx / f.length, cy / f.length, cz / f.length]
    const nr = faceNormal(md.verts, f)
    const l = Math.hypot(...nr) || 1
    if (pred(c, [nr[0] / l, nr[1] / l, nr[2] / l])) md.faceMat![fi] = index
  })
  return md
}

function isect(a0: Vec2, u0: Vec2, b0: Vec2, u1: Vec2): Vec2 {
  const den = u0[0] * -u1[1] - u0[1] * -u1[0]
  if (Math.abs(den) < 1e-9) return b0
  const wx = b0[0] - a0[0]
  const wy = b0[1] - a0[1]
  const tt = (wx * -u1[1] - wy * -u1[0]) / den
  return [a0[0] + u0[0] * tt, a0[1] + u0[1] * tt]
}

/** Offset a polyline to its right-hand side by d, mitring the corners. */
export function offsetPolyline(pts: Vec2[], d: number, closed = false): Vec2[] {
  const P = pts
  const n = P.length
  const segs: [Vec2, Vec2, Vec2][] = []
  const m = closed ? n : n - 1
  for (let i = 0; i < m; i++) {
    const a = P[i]
    const b = P[(i + 1) % n]
    const dx = b[0] - a[0]
    const dy = b[1] - a[1]
    const l = Math.hypot(dx, dy) || 1
    const u: Vec2 = [dx / l, dy / l]
    const nn: Vec2 = [u[1], -u[0]] // right of travel
    segs.push([
      [a[0] + nn[0] * d, a[1] + nn[1] * d],
      [b[0] + nn[0] * d, b[1] + nn[1] * d],
      u,
    ])
  }
  const out: Vec2[] = []
  if (closed) {
    for (let i = 0; i < n; i++) {
      const sp = segs[(i - 1 + m) % m]
      const sc = segs[i % m]
      out.push(isect(sp[0], sp[2], sc[0], sc[2]))
    }
  } else {
    out.push(segs[0][0])
    for (let i = 0; i < segs.length - 1; i++) {
      out.push(isect(segs[i][0], segs[i][2], segs[i + 1][0], segs[i + 1][2]))
    }
    out.push(segs[segs.length - 1][1])
  }
  return out
}

/** Sweep a closed profile [(z, depth_into_room), ...] along a plan path.
 * Interior is on the RIGHT of travel; depth measured into the room. */
export function runMolding(path: Vec2[], profile: Vec2[], cap = true, closed = false): MeshData {
  const offs = new Map<number, Vec2[]>()
  for (const [, d] of profile) {
    if (!offs.has(d)) offs.set(d, offsetPolyline(path, d, closed))
  }
  const rings: [number, number, number][][] = []
  for (let i = 0; i < path.length; i++) {
    rings.push(
      profile.map(([z, d]) => {
        const p = offs.get(d)![i]
        return [p[0], p[1], z] as [number, number, number]
      }),
    )
  }
  return mlib.loft(rings, {
    closeU: closed,
    closeV: true,
    capStart: cap && !closed,
    capEnd: cap && !closed,
  })
}

/** Applied rectangular panel moulding on a wall.  normal = outward from the
 * wall into the room (unit 2D). */
export function panelMoulding(
  cx: number,
  cy: number,
  cz: number,
  w: number,
  h: number,
  normal: Vec2,
  prof?: Vec2[],
): MeshData {
  const p =
    prof ??
    ([
      [-0.026, 0.001],
      [0.026, 0.001],
      [0.026, 0.0062],
      [0.019, 0.0128],
      [0.01, 0.0165],
      [-0.002, 0.0175],
      [-0.015, 0.0128],
      [-0.026, 0.0072],
    ] as Vec2[])
  const ob = mlib.sweepRectFrame(w, h, p)
  const ang = Math.atan2(normal[1], normal[0]) - Math.PI / 2
  const ca = Math.cos(ang)
  const sa = Math.sin(ang)
  mlib.transform4(ob, [
    [ca, -sa, 0, cx],
    [sa, ca, 0, cy],
    [0, 0, 1, cz],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(ob)
  return ob
}

// ------------------------------------------------------------------ profiles

export const BASE_PROF: Vec2[] = [
  [0.0, 0.0012],
  [0.0, 0.0215],
  [0.118, 0.0215],
  [0.128, 0.0275],
  [0.14, 0.0275],
  [0.148, 0.0205],
  [0.155, 0.011],
  [0.155, 0.0012],
]

export const RAIL_PROF: Vec2[] = [
  [2.688, 0.0012],
  [2.688, 0.0295],
  [2.716, 0.0325],
  [2.734, 0.027],
  [2.742, 0.015],
  [2.742, 0.0012],
]

export const CROWN_PROF: Vec2[] = [
  [3.086, 0.0012],
  [3.104, 0.0175],
  [3.146, 0.0455],
  [3.196, 0.068],
  [3.242, 0.0808],
  [3.2585, 0.0845],
  [3.2585, 0.0012],
]

export const ALCOVE_CROWN: Vec2[] = CROWN_PROF.map(([z, d]) => [z - (L.CZ - L.AL_Z), d])
