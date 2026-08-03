/** Mitred moulding sweeps: offset a plan polyline, then loft a (z, depth)
 * profile along it.  Extracted from the s_walls.py port (scenes/monica/walls)
 * so every scene's trim can share it. */
import * as mlib from './mlib'
import type { MeshData, Vec2 } from './mesh'

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
