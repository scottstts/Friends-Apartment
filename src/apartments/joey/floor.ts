/** Apartment 19 mosaic parquet: direct port of s_floor.py. */
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'

const T = 0.3048
const NFING = 5
const JOINT = 0.0012
const TH = 0.0105
const DECK = 0.0026
const SUB = 0.03

export type Region = [number, number, number, number]

function clip(poly: Vec2[], rect: Region): Vec2[] {
  const [x0, y0, x1, y1] = rect
  const edges: [0 | 1, number, 1 | -1][] = [
    [0, x0, 1],
    [0, x1, -1],
    [1, y0, 1],
    [1, y1, -1],
  ]
  let out = poly.map((p) => [...p] as Vec2)
  for (const [axis, value, sign] of edges) {
    if (!out.length) return []
    const source = out
    out = []
    for (let i = 0; i < source.length; i++) {
      const a = source[i]
      const b = source[(i + 1) % source.length]
      const da = (a[axis] - value) * sign
      const db = (b[axis] - value) * sign
      if (da >= -1e-9) out.push(a)
      if ((da > 1e-9) !== (db > 1e-9) && Math.abs(da - db) > 1e-12) {
        const t = da / (da - db)
        out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])
      }
    }
  }
  const clean: Vec2[] = []
  for (const p of out) {
    const q = clean.at(-1)
    if (!q || Math.abs(p[0] - q[0]) > 1e-7 || Math.abs(p[1] - q[1]) > 1e-7) clean.push(p)
  }
  if (clean.length > 2) {
    const first = clean[0]
    const last = clean.at(-1)!
    if (Math.abs(first[0] - last[0]) < 1e-7 && Math.abs(first[1] - last[1]) < 1e-7) clean.pop()
  }
  return clean.length >= 3 ? clean : []
}

function subtractRect(region: Region, cut: Region): Region[] {
  const [x0, y0, x1, y1] = region
  const [a0, b0, a1, b1] = cut
  if (a1 <= x0 || a0 >= x1 || b1 <= y0 || b0 >= y1) return [region]
  const out: Region[] = []
  if (a0 > x0) out.push([x0, y0, a0, y1])
  if (a1 < x1) out.push([a1, y0, x1, y1])
  const mx0 = Math.max(x0, a0)
  const mx1 = Math.min(x1, a1)
  if (b0 > y0) out.push([mx0, y0, mx1, b0])
  if (b1 < y1) out.push([mx0, b1, mx1, y1])
  return out.filter((r) => r[2] - r[0] > 1e-6 && r[3] - r[1] > 1e-6)
}

function disjoint(regions: Region[]): Region[] {
  const out: Region[] = []
  const done: Region[] = []
  for (const region of regions) {
    let pending = [region]
    for (const prior of done) pending = pending.flatMap((part) => subtractRect(part, prior))
    out.push(...pending)
    done.push(region)
  }
  return out
}

function area(poly: Vec2[]): number {
  let value = 0
  for (let i = 0; i < poly.length; i++) {
    const a = poly[i]
    const b = poly[(i + 1) % poly.length]
    value += a[0] * b[1] - b[0] * a[1]
  }
  return Math.abs(value) * 0.5
}

function hsvToRgb(h: number, s: number, v: number): Vec3 {
  const i = Math.floor(h * 6)
  const f = h * 6 - i
  const p = v * (1 - s)
  const q = v * (1 - s * f)
  const t = v * (1 - s * (1 - f))
  return ([
    [v, t, p],
    [q, v, p],
    [p, v, t],
    [p, q, v],
    [t, p, v],
    [v, p, q],
  ] as Vec3[])[i % 6]
}

export function buildParquet(regions: Region[], z = 0, seed = 7311, phase: Vec2 = [0, 0]): MeshData {
  const rng = new PyRandom(seed)
  const verts: Vec3[] = []
  const faces: number[][] = []
  const uvs: Vec2[][] = []
  const colors: Vec3[] = []
  const fingerWidth = T / NFING
  const x0 = Math.min(...regions.map((r) => r[0]))
  const y0 = Math.min(...regions.map((r) => r[1]))
  const x1 = Math.max(...regions.map((r) => r[2]))
  const y1 = Math.max(...regions.map((r) => r[3]))
  const i0 = Math.floor((x0 - phase[0]) / T) - 1
  const i1 = Math.ceil((x1 - phase[0]) / T) + 1
  const j0 = Math.floor((y0 - phase[1]) / T) - 1
  const j1 = Math.ceil((y1 - phase[1]) / T) + 1

  const tone = (): Vec3 => {
    const rgb = hsvToRgb(rng.uniform(0.058, 0.082), rng.uniform(0.12, 0.27), Math.min(1, rng.uniform(0.9, 1.08)))
    const gain = rng.uniform(0.93, 1.07)
    return [Math.min(1.45, rgb[0] * gain * 1.3), Math.min(1.45, rgb[1] * gain * 1.14), Math.min(1.45, rgb[2] * gain * 0.98)]
  }

  for (let i = i0; i < i1; i++) {
    for (let j = j0; j < j1; j++) {
      const ox = phase[0] + i * T
      const oy = phase[1] + j * T
      const horizontal = (i + j) % 2 === 0
      for (let k = 0; k < NFING; k++) {
        let poly: Vec2[]
        let gx: number
        let gy: number
        if (horizontal) {
          poly = [[ox, oy + k * fingerWidth], [ox + T, oy + k * fingerWidth], [ox + T, oy + (k + 1) * fingerWidth], [ox, oy + (k + 1) * fingerWidth]]
          gx = 1
          gy = 0
        } else {
          poly = [[ox + k * fingerWidth, oy], [ox + (k + 1) * fingerWidth, oy], [ox + (k + 1) * fingerWidth, oy + T], [ox + k * fingerWidth, oy + T]]
          gx = 0
          gy = 1
        }
        const h = JOINT * 0.5
        poly = [[poly[0][0] + h, poly[0][1] + h], [poly[1][0] - h, poly[1][1] + h], [poly[2][0] - h, poly[2][1] - h], [poly[3][0] + h, poly[3][1] - h]]
        for (const region of regions) {
          const clipped = clip(poly, region)
          if (clipped.length < 3 || area(clipped) < 1.2e-4) continue
          const dz = rng.uniform(-0.0001, 0.00016)
          const ro: Vec2 = [rng.uniform(-11, 11), rng.uniform(-11, 11)]
          const tint = tone()
          const base = verts.length
          for (const [x, y] of clipped) verts.push([x, y, z + dz])
          for (const [x, y] of clipped) verts.push([x, y, z + TH + dz])
          const uvOf = (x: number, y: number): Vec2 => [x * -gy + y * gx + ro[0], x * gx + y * gy + ro[1]]
          const n = clipped.length
          faces.push(Array.from({ length: n }, (_, index) => base + n + index))
          uvs.push(clipped.map(([x, y]) => uvOf(x, y)))
          faces.push(Array.from({ length: n }, (_, index) => base + n - 1 - index))
          uvs.push(Array.from({ length: n }, (_, index) => uvOf(...clipped[n - 1 - index])))
          for (let m = 0; m < n; m++) {
            const m2 = (m + 1) % n
            faces.push([base + m, base + m2, base + n + m2, base + n + m])
            uvs.push([uvOf(...clipped[m]), uvOf(...clipped[m2]), uvOf(...clipped[m2]), uvOf(...clipped[m])])
          }
          for (let m = 0; m < 2 * n; m++) colors.push(tint)
        }
      }
    }
  }

  const deckTop = z + TH - DECK
  for (const [a, b, c, d] of disjoint(regions)) {
    const base = verts.length
    for (const zz of [z - SUB, deckTop]) verts.push([a, b, zz], [c, b, zz], [c, d, zz], [a, d, zz])
    for (const face of [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]) {
      faces.push(face.map((index) => base + index))
      uvs.push(face.map((index) => [verts[base + index][0], verts[base + index][1]] as Vec2))
    }
    for (let index = 0; index < 8; index++) colors.push([0.88, 0.8, 0.7])
  }

  const md = MeshData.from(verts, faces)
  md.uvs = uvs
  md.colors = colors
  md.colorName = 'ptint'
  mlib.recalcNormals(md)
  return md
}
