/** Parquet floor - port of build_scripts/s_floor.py.
 * Real geometry, one slab per parquet piece: mitred border strips, central
 * lozenge and corner triangles per 45-degree tile, each piece with its own
 * grain direction via UVs and its own tonal jitter via the ptint attribute.
 */
import { MeshData, insetPoly, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'

type Piece = { poly: Vec2[]; gd: Vec2 }

function tilePieces(b = 0.152): Piece[] {
  const U = 1.0
  const V = 1.0
  const i0 = b
  const i1 = 1 - b
  void i0
  const P: Piece[] = []
  // four mitred border strips
  P.push({ poly: [[0, 0], [U, 0], [i1, b], [b, b]], gd: [1, 0] })
  P.push({ poly: [[U, 0], [U, V], [i1, i1], [i1, b]], gd: [0, 1] })
  P.push({ poly: [[U, V], [0, V], [b, i1], [i1, i1]], gd: [1, 0] })
  P.push({ poly: [[0, V], [0, 0], [b, b], [b, i1]], gd: [0, 1] })
  // central lozenge
  const mid = 0.5
  P.push({ poly: [[mid, b], [i1, mid], [mid, i1], [b, mid]], gd: [0.7071, 0.7071] })
  // four corner triangles
  P.push({ poly: [[b, b], [mid, b], [b, mid]], gd: [0.7071, -0.7071] })
  P.push({ poly: [[i1, b], [i1, mid], [mid, b]], gd: [0.7071, 0.7071] })
  P.push({ poly: [[i1, i1], [mid, i1], [i1, mid]], gd: [0.7071, -0.7071] })
  P.push({ poly: [[b, i1], [b, mid], [mid, i1]], gd: [0.7071, 0.7071] })
  return P
}

function hsvToRgb(h: number, s: number, v: number): [number, number, number] {
  if (s === 0) return [v, v, v]
  const i = Math.floor(h * 6)
  const f = h * 6 - i
  const p = v * (1 - s)
  const q = v * (1 - s * f)
  const t = v * (1 - s * (1 - f))
  switch (i % 6) {
    case 0:
      return [v, t, p]
    case 1:
      return [q, v, p]
    case 2:
      return [p, v, t]
    case 3:
      return [p, q, v]
    case 4:
      return [t, p, v]
    default:
      return [v, p, q]
  }
}

export function buildParquet(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  T = 0.445,
  gap = 0.0014,
  th = 0.0095,
  ang = Math.PI / 4,
  covered?: (x: number, y: number) => boolean,
): MeshData {
  const ca = Math.cos(ang)
  const sa = Math.sin(ang)
  const toWorld = (u: number, v: number): Vec2 => [u * ca - v * sa, u * sa + v * ca]
  const toUv = (x: number, y: number): Vec2 => [x * ca + y * sa, -x * sa + y * ca]

  const us: number[] = []
  const vs: number[] = []
  for (const [x, y] of [
    [x0, y0],
    [x1, y0],
    [x1, y1],
    [x0, y1],
  ] as Vec2[]) {
    const [u, v] = toUv(x, y)
    us.push(u)
    vs.push(v)
  }
  const ui0 = Math.floor(Math.min(...us) / T) - 1
  const ui1 = Math.ceil(Math.max(...us) / T) + 1
  const vj0 = Math.floor(Math.min(...vs) / T) - 1
  const vj1 = Math.ceil(Math.max(...vs) / T) + 1

  const pieces = tilePieces()
  const verts: Vec3[] = []
  const faces: number[][] = []
  const uvs: (Vec2[] | null)[] = []
  const cols: Vec3[] = []
  const rng = new PyRandom(20240)

  const tint = (): Vec3 => {
    const h = rng.uniform(0.055, 0.085)
    const s = rng.uniform(0.12, 0.42)
    const v = rng.uniform(0.72, 1.18)
    const [r, g, bb] = hsvToRgb(h, s, Math.min(1.0, v))
    const k = rng.uniform(0.8, 1.15)
    return [Math.min(1.4, r * k * 1.25), Math.min(1.4, g * k * 1.12), Math.min(1.4, bb * k)]
  }

  for (let i = ui0; i < ui1; i++) {
    for (let j = vj0; j < vj1; j++) {
      const ou = i * T
      const ov = j * T
      for (const { poly, gd } of pieces) {
        let wp = poly.map(([pu, pv]) => toWorld(ou + pu * T, ov + pv * T))
        const cx = wp.reduce((s2, p) => s2 + p[0], 0) / wp.length
        const cy = wp.reduce((s2, p) => s2 + p[1], 0) / wp.length
        if (!(x0 - 0.35 < cx && cx < x1 + 0.35 && y0 - 0.35 < cy && cy < y1 + 0.35)) continue
        wp = insetPoly(wp, gap * 0.5)
        const gx = gd[0] * ca - gd[1] * sa
        const gy = gd[0] * sa + gd[1] * ca
        const ro: Vec2 = [rng.uniform(-9, 9), rng.uniform(-9, 9)]
        const t = tint()
        // Blender builds the full continuous lattice and trims it afterwards.
        // Consume the same seeded draws even for pieces outside the shell so
        // every retained board keeps its original grain offset and tone.
        if (covered && !covered(cx, cy)) continue
        const n = wp.length
        const base = verts.length
        for (const [px, py] of wp) verts.push([px, py, 0])
        for (const [px, py] of wp) verts.push([px, py, th])
        const uvOf = (px: number, py: number): Vec2 => {
          const across = px * -gy + py * gx
          const along = px * gx + py * gy
          return [across + ro[0], along + ro[1]]
        }
        const top = Array.from({ length: n }, (_, k) => base + n + k)
        const bot = Array.from({ length: n }, (_, k) => base + n - 1 - k)
        faces.push(top)
        uvs.push(wp.map(([px, py]) => uvOf(px, py)))
        faces.push(bot)
        uvs.push(wp.map((_, k) => uvOf(...wp[n - 1 - k])))
        for (let k = 0; k < n; k++) {
          const k2 = (k + 1) % n
          faces.push([base + k, base + k2, base + n + k2, base + n + k])
          uvs.push([uvOf(...wp[k]), uvOf(...wp[k2]), uvOf(...wp[k2]), uvOf(...wp[k])])
        }
        for (let k = 0; k < 2 * n; k++) cols.push(t)
      }
    }
  }
  const md = MeshData.from(verts, faces)
  md.uvs = uvs
  md.colors = cols
  md.colorName = 'ptint'
  mlib.recalcNormals(md)
  return md
}
