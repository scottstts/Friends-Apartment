/** Real apartment 19 bathroom tiles, one shallow slab per tile. */
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { toWall } from './walls'

export const TILE = 0.104
export const JOINT = 0.0048
export const PITCH = TILE + JOINT
export const THICKNESS = 0.013
const SINK = 0.002

export const courses = (height: number): number => Math.max(1, Math.round(height / PITCH))
export const tiledHeight = (count: number): number => count * PITCH - JOINT
export const height = tiledHeight

export function field(
  p0: Vec2,
  p1: Vec2,
  u0: number,
  u1: number,
  z0: number,
  courseCount: number,
  options: { cap?: boolean; thickness?: number; startU?: number } = {},
): MeshData[] {
  const start = options.startU ?? u0
  const z1 = z0 + tiledHeight(courseCount)
  const joint = JOINT * 0.5
  const verts: Vec3[] = []
  const faces: number[][] = []
  const slab = (a: number, b: number, c: number, d: number): void => {
    if (b - a < 0.004 || d - c < 0.004) return
    const base = verts.length
    for (const y of [-SINK, options.thickness ?? THICKNESS]) verts.push([a, y, c], [b, y, c], [b, y, d], [a, y, d])
    for (const f of [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]) faces.push(f.map((i) => base + i))
  }
  const i0 = Math.floor((u0 - start) / PITCH)
  const i1 = Math.ceil((u1 - start) / PITCH)
  for (let i = i0; i <= i1; i++) {
    const a = Math.max(start + i * PITCH + joint, u0)
    const b = Math.min(start + i * PITCH + joint + TILE, u1)
    for (let row = 0; row < courseCount; row++) {
      const c = z0 + row * PITCH + joint
      slab(a, b, c, Math.min(c + TILE, z1))
    }
  }
  const out = [toWall(MeshData.from(verts, faces), p0, p1)]
  if (options.cap !== false) {
    const cap = mlib.box(u0, -SINK, z1, u1, (options.thickness ?? THICKNESS) + 0.006, z1 + 0.021)
    mlib.bevel(cap, 0.006, 3)
    mlib.smoothShade(cap, 40)
    out.push(toWall(cap, p0, p1))
  }
  return out
}

/** Vertical bullnose closing the exposed end of a tile run. */
export function stopBead(p0: Vec2, p1: Vec2, u: number, z0: number, z1: number, thickness = THICKNESS): MeshData {
  const md = mlib.box(u, -SINK, z0, u + 0.021, thickness + 0.006, z1)
  mlib.bevel(md, 0.006, 3)
  mlib.smoothShade(md, 40)
  return toWall(md, p0, p1)
}
