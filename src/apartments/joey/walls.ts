/** Apartment 19 wall, trim and opening-frame geometry. */
import type { Vec2 } from '../../lib/mesh'
import { MeshData, faceNormal } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { runMolding } from '../../scene/walls'
import * as L from './layout'

export type Hole = [number, number, number, number]

/** Map local XZ geometry onto p0 -> p1. The main footprint is CCW: left is
 * room-facing and right is masonry-facing. */
export function toWall(md: MeshData, p0: Vec2, p1: Vec2, u0 = 0, z0 = 0, intoWall = false): MeshData {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  const tx = dx / length
  const ty = dy / length
  const nx = intoWall ? ty : -ty
  const ny = intoWall ? -tx : tx
  mlib.transform4(md, [
    [tx, nx, 0, p0[0] + tx * u0],
    [ty, ny, 0, p0[1] + ty * u0],
    [0, 0, 1, z0],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(md)
  return md
}

/** Wall solid growing to the right/outside of the CCW room edge. */
export function wall(p0: Vec2, p1: Vec2, thickness: number, z0: number, z1: number, holes: Hole[] = []): MeshData {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  const localHoles = holes.map(([u0, a, u1, b]) => [u0, a - z0, u1, b - z0] as Hole)
  return toWall(mlib.panelWithHoles(length, z1 - z0, thickness, localHoles), p0, p1, 0, z0, true)
}

export function faceMat(
  md: MeshData,
  index: number,
  predicate: (center: [number, number, number], normal: [number, number, number]) => boolean,
): MeshData {
  if (!md.faceMat) md.faceMat = md.faces.map(() => 0)
  md.faces.forEach((face, fi) => {
    const center: [number, number, number] = [0, 0, 0]
    for (const vi of face) {
      center[0] += md.verts[vi][0] / face.length
      center[1] += md.verts[vi][1] / face.length
      center[2] += md.verts[vi][2] / face.length
    }
    const normal = faceNormal(md.verts, face)
    const length = Math.hypot(...normal) || 1
    const unit: [number, number, number] = [normal[0] / length, normal[1] / length, normal[2] / length]
    if (predicate(center, unit)) md.faceMat![fi] = index
  })
  return md
}

const SINK = 0.002

export function baseProfile(h = L.BASE_H, t = L.BASE_T): Vec2[] {
  return [
    [-SINK, 0],
    [t, 0],
    [t, h - 0.03],
    [t * 0.86, h - 0.02],
    [t * 0.86, h - 0.012],
    [t * 0.4, h - 0.002],
    [-SINK, h],
  ]
}

export const panelProfile = (): Vec2[] => [
  [0, -SINK],
  [0.046, -SINK],
  [0.046, 0.006],
  [0.033, 0.012],
  [0.026, 0.015],
  [0.013, 0.015],
  [0.004, 0.009],
]

export const casingProfile = (w = 0.115, d = 0.021): Vec2[] => [
  [0, -SINK],
  [w, -SINK],
  [w, d * 0.55],
  [w * 0.9, d * 0.72],
  [w * 0.9, d],
  [w * 0.1, d],
  [0, d * 0.8],
]

export const corniceProfile = (h = 0.055, d = 0.035): Vec2[] => [
  [-SINK, SINK],
  [-SINK, -h],
  [d * 0.3, -h * 0.86],
  [d * 0.62, -h * 0.55],
  [d * 0.86, -h * 0.22],
  [d, SINK],
]

export function trimRun(path: Vec2[], a = 0, b = 0): Vec2[] {
  const result = path.map((p) => [...p] as Vec2)
  if (a && result.length > 1) {
    const dx = result[1][0] - result[0][0]
    const dy = result[1][1] - result[0][1]
    const length = Math.hypot(dx, dy) || 1
    result[0][0] += (dx / length) * a
    result[0][1] += (dy / length) * a
  }
  if (b && result.length > 1) {
    const n = result.length
    const dx = result[n - 1][0] - result[n - 2][0]
    const dy = result[n - 1][1] - result[n - 2][1]
    const length = Math.hypot(dx, dy) || 1
    result[n - 1][0] -= (dx / length) * b
    result[n - 1][1] -= (dy / length) * b
  }
  return result
}

function sweep(path: Vec2[], profile: Vec2[], closed = false): MeshData {
  // shared runMolding takes (z, depth), while the Blender helpers own
  // (depth, z). Keep this adapter explicit at the apartment boundary.
  return runMolding(path, profile.map(([depth, z]) => [z, depth] as Vec2), !closed, closed)
}

export function baseboard(path: Vec2[], h = L.BASE_H, t = L.BASE_T): MeshData {
  return mlib.bevel(sweep(path, baseProfile(h, t)), 0.0015, 1)
}

export function wallPanel(p0: Vec2, p1: Vec2, uCenter: number, zCenter: number, width: number, height: number): MeshData {
  const md = mlib.sweepRectFrame(width, height, panelProfile())
  mlib.translate(md, [uCenter, 0, zCenter])
  return toWall(md, p0, p1)
}

export function pilaster(p0: Vec2, p1: Vec2, uCenter: number, width = 0.34, depth = 0.085, z1 = L.CZ): MeshData {
  const half = width * 0.5
  const pb = L.BASE_T + 0.012
  const ph = L.BASE_H + 0.02
  const md = mlib.join([
    mlib.box(uCenter - half, 0, ph, uCenter + half, depth, z1),
    mlib.box(uCenter - half - 0.014, 0, 0, uCenter + half + 0.014, depth + pb, ph),
    mlib.box(uCenter - half - 0.02, 0, z1 - 0.075, uCenter + half + 0.02, depth + 0.022, z1),
  ])
  mlib.bevel(md, 0.003, 2)
  return toWall(md, p0, p1)
}

export const ceiling = (outline: Vec2[], z: number, thickness = 0.14): MeshData => mlib.prism(outline, z, z + thickness)

export function cornice(path: Vec2[], z: number): MeshData {
  const md = sweep(path, corniceProfile())
  mlib.translate(md, [0, 0, z])
  return md
}
