/** Walls, mouldings and profiles - port of build_scripts/s_walls.py.
 * Each wall is one closed solid panel whose inner face sits exactly on the
 * room boundary and whose body extends outward.
 */
import * as L from './L'
import * as mlib from '../../lib/mlib'
import { MeshData, faceNormal, type Vec2 } from '../../lib/mesh'

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

/* The mitred sweep helpers (offsetPolyline, runMolding) moved to
 * lib/molding.ts so apartment 19's trim shares them; the s_walls.py port
 * surface stays complete through this re-export. */
export { offsetPolyline, runMolding } from '../../lib/molding'

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
