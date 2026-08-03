/** Polygon-mesh core for the port.
 *
 * The Blender build works on polygon meshes (quads + n-gons) that are only
 * triangulated at render time; every mlib helper moves vertices, not object
 * transforms, so everything lives in world space.  This module mirrors that:
 * MeshData holds polygons in world space, modifiers (solidify, subsurf,
 * bevel-on-box) are applied eagerly in the same order Blender's stack would,
 * and triangulation + angle-based smooth shading happen once at the end when
 * the data becomes a BufferGeometry.
 */
import * as THREE from 'three/webgpu'

export type Vec3 = [number, number, number]
export type Vec2 = [number, number]

export type Shading = { mode: 'flat' } | { mode: 'smooth'; angle: number }

interface BoxProvenance {
  kind: 'box'
  bounds: [number, number, number, number, number, number]
}
interface PrismProvenance {
  kind: 'prism'
  poly: Vec2[]
  z0: number
  z1: number
}
type Provenance = BoxProvenance | PrismProvenance | null

export class MeshData {
  verts: Vec3[] = []
  faces: number[][] = []
  /** per-face-corner uvs, parallel to faces (or null for a face without) */
  uvs: (Vec2[] | null)[] | null = null
  /** per-vertex colour attribute (ptint / surfq) */
  colors: Vec3[] | null = null
  colorName = ''
  shading: Shading = { mode: 'flat' }
  /** per-face material slot index (multi-material walls) */
  faceMat: number[] | null = null
  provenance: Provenance = null

  static from(verts: Vec3[], faces: number[][]): MeshData {
    const m = new MeshData()
    m.verts = verts
    m.faces = faces
    return m
  }

  clone(): MeshData {
    const m = new MeshData()
    m.verts = this.verts.map((v) => [...v] as Vec3)
    m.faces = this.faces.map((f) => [...f])
    m.uvs = this.uvs ? this.uvs.map((u) => (u ? u.map((p) => [...p] as Vec2) : null)) : null
    m.colors = this.colors ? this.colors.map((c) => [...c] as Vec3) : null
    m.colorName = this.colorName
    m.shading = { ...this.shading }
    m.faceMat = this.faceMat ? [...this.faceMat] : null
    m.provenance = null
    return m
  }
}

// ------------------------------------------------------------------ helpers

function sub(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
}
function cross(a: Vec3, b: Vec3): Vec3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
}
function dot(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}
function len(a: Vec3): number {
  return Math.hypot(a[0], a[1], a[2])
}
function norm(a: Vec3): Vec3 {
  const l = len(a) || 1
  return [a[0] / l, a[1] / l, a[2] / l]
}

/** Newell face normal (unnormalised — length is 2x area). */
export function faceNormal(verts: Vec3[], face: number[]): Vec3 {
  let nx = 0,
    ny = 0,
    nz = 0
  for (let i = 0; i < face.length; i++) {
    const a = verts[face[i]]
    const b = verts[face[(i + 1) % face.length]]
    nx += (a[1] - b[1]) * (a[2] + b[2])
    ny += (a[2] - b[2]) * (a[0] + b[0])
    nz += (a[0] - b[0]) * (a[1] + b[1])
  }
  return [nx, ny, nz]
}

/** Triangulate one polygon face into index triples (indices into `face`). */
function triangulateFace(verts: Vec3[], face: number[]): [number, number, number][] {
  const n = face.length
  if (n === 3) return [[0, 1, 2]]
  if (n === 4) {
    // split along the shorter diagonal, like Blender's beauty-ish default
    const d02 = len(sub(verts[face[0]], verts[face[2]]))
    const d13 = len(sub(verts[face[1]], verts[face[3]]))
    return d02 <= d13
      ? [
          [0, 1, 2],
          [0, 2, 3],
        ]
      : [
          [1, 2, 3],
          [1, 3, 0],
        ]
  }
  // n-gon: project on the dominant plane of the Newell normal and ear-clip
  const nrm = norm(faceNormal(verts, face))
  let u: Vec3
  if (Math.abs(nrm[0]) > 0.9) {
    u = [0, 1, 0]
  } else {
    u = [1, 0, 0]
  }
  const w = norm(cross(nrm, u))
  u = norm(cross(w, nrm))
  const pts2 = face.map((vi) => {
    const p = verts[vi]
    return new THREE.Vector2(dot(p, u), dot(p, w))
  })
  const tris = THREE.ShapeUtils.triangulateShape(pts2, [])
  if (tris.length === 0) {
    // degenerate fallback: fan
    const out: [number, number, number][] = []
    for (let i = 1; i < n - 1; i++) out.push([0, i, i + 1])
    return out
  }
  return tris as [number, number, number][]
}

// ---------------------------------------------------------------- transforms

export function translate(m: MeshData, d: Vec3): MeshData {
  for (const v of m.verts) {
    v[0] += d[0]
    v[1] += d[1]
    v[2] += d[2]
  }
  m.provenance = null
  return m
}

export function rotateZ(m: MeshData, ang: number, pivot: Vec2 = [0, 0]): MeshData {
  const c = Math.cos(ang)
  const s = Math.sin(ang)
  for (const v of m.verts) {
    const x = v[0] - pivot[0]
    const y = v[1] - pivot[1]
    v[0] = pivot[0] + x * c - y * s
    v[1] = pivot[1] + x * s + y * c
  }
  m.provenance = null
  return m
}

export function rotX(m: MeshData, ang: number, pivot: Vec3 = [0, 0, 0]): MeshData {
  const c = Math.cos(ang)
  const s = Math.sin(ang)
  for (const v of m.verts) {
    const y = v[1] - pivot[1]
    const z = v[2] - pivot[2]
    v[1] = pivot[1] + y * c - z * s
    v[2] = pivot[2] + y * s + z * c
  }
  m.provenance = null
  return m
}

export function rotY(m: MeshData, ang: number, pivot: Vec3 = [0, 0, 0]): MeshData {
  const c = Math.cos(ang)
  const s = Math.sin(ang)
  for (const v of m.verts) {
    const x = v[0] - pivot[0]
    const z = v[2] - pivot[2]
    v[0] = pivot[0] + x * c + z * s
    v[2] = pivot[2] - x * s + z * c
  }
  m.provenance = null
  return m
}

export function scaleMesh(m: MeshData, s: number | Vec3, pivot: Vec3 = [0, 0, 0]): MeshData {
  const sv: Vec3 = typeof s === 'number' ? [s, s, s] : s
  for (const v of m.verts) {
    v[0] = pivot[0] + (v[0] - pivot[0]) * sv[0]
    v[1] = pivot[1] + (v[1] - pivot[1]) * sv[1]
    v[2] = pivot[2] + (v[2] - pivot[2]) * sv[2]
  }
  m.provenance = null
  return m
}

/** 4x4 row-major (like mathutils.Matrix) applied to positions. */
export function transform4(m: MeshData, M: number[][]): MeshData {
  for (const v of m.verts) {
    const x = v[0],
      y = v[1],
      z = v[2]
    v[0] = M[0][0] * x + M[0][1] * y + M[0][2] * z + M[0][3]
    v[1] = M[1][0] * x + M[1][1] * y + M[1][2] * z + M[1][3]
    v[2] = M[2][0] * x + M[2][1] * y + M[2][2] * z + M[2][3]
  }
  m.provenance = null
  return m
}

export function join(parts: (MeshData | null)[]): MeshData {
  const list = parts.filter((p): p is MeshData => p !== null)
  const out = new MeshData()
  const anyUv = list.some((p) => p.uvs)
  const anyCol = list.some((p) => p.colors)
  if (anyUv) out.uvs = []
  if (anyCol) out.colors = []
  let shading: Shading = { mode: 'flat' }
  for (const p of list) {
    const base = out.verts.length
    for (const v of p.verts) out.verts.push([...v] as Vec3)
    for (let fi = 0; fi < p.faces.length; fi++) {
      out.faces.push(p.faces[fi].map((i) => i + base))
      if (anyUv) out.uvs!.push(p.uvs ? (p.uvs[fi] ?? null) : null)
    }
    if (anyCol) {
      const cols = p.colors ?? p.verts.map(() => [1, 1, 1] as Vec3)
      for (const c of cols) out.colors!.push([...c] as Vec3)
      if (p.colorName) out.colorName = p.colorName
    }
    if (p.shading.mode === 'smooth') shading = p.shading
  }
  out.shading = shading
  return out
}

// ------------------------------------------------------------ normal repair

/** Make winding consistent per connected component; flip closed components
 * outward by signed volume (the job Blender's recalc_face_normals did). */
export function recalcNormals(m: MeshData, flip = false): MeshData {
  const edgeMap = new Map<string, { face: number; fwd: boolean }[]>()
  const key = (a: number, b: number) => (a < b ? a + '_' + b : b + '_' + a)
  m.faces.forEach((f, fi) => {
    for (let i = 0; i < f.length; i++) {
      const a = f[i]
      const b = f[(i + 1) % f.length]
      if (a === b) continue
      const k = key(a, b)
      let list = edgeMap.get(k)
      if (!list) {
        list = []
        edgeMap.set(k, list)
      }
      list.push({ face: fi, fwd: a < b })
    }
  })
  const flipped = new Array<boolean>(m.faces.length).fill(false)
  const visited = new Array<boolean>(m.faces.length).fill(false)
  const comps: number[][] = []
  for (let start = 0; start < m.faces.length; start++) {
    if (visited[start]) continue
    const comp: number[] = []
    const stack = [start]
    visited[start] = true
    while (stack.length) {
      const fi = stack.pop()!
      comp.push(fi)
      const f = m.faces[fi]
      for (let i = 0; i < f.length; i++) {
        const a = f[i]
        const b = f[(i + 1) % f.length]
        if (a === b) continue
        const pair = edgeMap.get(key(a, b))!
        if (pair.length !== 2) continue
        for (const o of pair) {
          if (o.face === fi || visited[o.face]) continue
          const self = pair.find((p) => p.face === fi)!
          // consistent orientation: the two faces must traverse the edge in
          // opposite directions (after accounting for flips already applied)
          const selfFwd = self.fwd !== flipped[fi]
          const otherFwd = o.fwd !== flipped[o.face]
          if (selfFwd === otherFwd) flipped[o.face] = !flipped[o.face]
          visited[o.face] = true
          stack.push(o.face)
        }
      }
    }
    comps.push(comp)
  }
  // apply flips, then orient each component
  for (const comp of comps) {
    // closed test: every edge of the component shared exactly twice
    let closed = true
    for (const fi of comp) {
      const f = m.faces[fi]
      for (let i = 0; i < f.length; i++) {
        const a = f[i]
        const b = f[(i + 1) % f.length]
        if (a === b) continue
        if (edgeMap.get(key(a, b))!.length !== 2) {
          closed = false
          break
        }
      }
      if (!closed) break
    }
    let volume = 0
    let keepScore = 0
    for (const fi of comp) {
      const f = flipped[fi] ? [...m.faces[fi]].reverse() : m.faces[fi]
      const tris = triangulateFace(m.verts, f)
      for (const [i, j, k] of tris) {
        const a = m.verts[f[i]]
        const b = m.verts[f[j]]
        const c = m.verts[f[k]]
        volume += dot(a, cross(b, c))
      }
      keepScore += flipped[fi] ? -1 : 1
    }
    const flipComp = closed ? volume < 0 : keepScore < 0
    for (const fi of comp) {
      let doFlip = flipped[fi]
      if (flipComp) doFlip = !doFlip
      if (flip) doFlip = !doFlip
      if (doFlip) {
        m.faces[fi].reverse()
        if (m.uvs && m.uvs[fi]) m.uvs[fi]!.reverse()
      }
    }
  }
  return m
}

// ------------------------------------------------------------ modifier ports

/** Solidify with offset 0 and rim, like the build's cloth/shade shells. */
export function solidify(m: MeshData, thickness: number): MeshData {
  const half = thickness / 2
  const vnormals: Vec3[] = m.verts.map(() => [0, 0, 0])
  m.faces.forEach((f) => {
    const n = faceNormal(m.verts, f)
    for (const vi of f) {
      vnormals[vi][0] += n[0]
      vnormals[vi][1] += n[1]
      vnormals[vi][2] += n[2]
    }
  })
  const nrm = vnormals.map((v) => norm(v))
  const nv = m.verts.length
  const outer: Vec3[] = m.verts.map((v, i) => [
    v[0] + nrm[i][0] * half,
    v[1] + nrm[i][1] * half,
    v[2] + nrm[i][2] * half,
  ])
  const inner: Vec3[] = m.verts.map((v, i) => [
    v[0] - nrm[i][0] * half,
    v[1] - nrm[i][1] * half,
    v[2] - nrm[i][2] * half,
  ])
  // boundary edges for the rim
  const counts = new Map<string, [number, number, number]>()
  const key = (a: number, b: number) => (a < b ? a + '_' + b : b + '_' + a)
  m.faces.forEach((f) => {
    for (let i = 0; i < f.length; i++) {
      const a = f[i]
      const b = f[(i + 1) % f.length]
      const k = key(a, b)
      const e = counts.get(k)
      if (e) e[2]++
      else counts.set(k, [a, b, 1])
    }
  })
  const faces: number[][] = []
  for (const f of m.faces) faces.push([...f])
  for (const f of m.faces) faces.push([...f].reverse().map((i) => i + nv))
  for (const [a, b, c] of counts.values()) {
    if (c === 1) faces.push([b, a, a + nv, b + nv])
  }
  m.verts = outer.concat(inner)
  m.faces = faces
  m.uvs = null
  m.provenance = null
  recalcNormals(m)
  return m
}

/** One level of Catmull-Clark (what mlib.cushion's subsurf does). */
export function subsurf(m: MeshData, levels = 1): MeshData {
  for (let l = 0; l < levels; l++) ccOnce(m)
  m.provenance = null
  return m
}

function ccOnce(m: MeshData): void {
  const nv = m.verts.length
  const facePts: Vec3[] = []
  for (const f of m.faces) {
    const p: Vec3 = [0, 0, 0]
    for (const vi of f) {
      p[0] += m.verts[vi][0]
      p[1] += m.verts[vi][1]
      p[2] += m.verts[vi][2]
    }
    facePts.push([p[0] / f.length, p[1] / f.length, p[2] / f.length])
  }
  interface EdgeRec {
    a: number
    b: number
    faces: number[]
    idx: number
  }
  const edges = new Map<string, EdgeRec>()
  const key = (a: number, b: number) => (a < b ? a + '_' + b : b + '_' + a)
  m.faces.forEach((f, fi) => {
    for (let i = 0; i < f.length; i++) {
      const a = f[i]
      const b = f[(i + 1) % f.length]
      const k = key(a, b)
      let e = edges.get(k)
      if (!e) {
        e = { a, b, faces: [], idx: -1 }
        edges.set(k, e)
      }
      e.faces.push(fi)
    }
  })
  const edgePts: Vec3[] = []
  let ei = 0
  for (const e of edges.values()) {
    e.idx = ei++
    const va = m.verts[e.a]
    const vb = m.verts[e.b]
    if (e.faces.length === 2) {
      const fa = facePts[e.faces[0]]
      const fb = facePts[e.faces[1]]
      edgePts.push([
        (va[0] + vb[0] + fa[0] + fb[0]) / 4,
        (va[1] + vb[1] + fa[1] + fb[1]) / 4,
        (va[2] + vb[2] + fa[2] + fb[2]) / 4,
      ])
    } else {
      edgePts.push([(va[0] + vb[0]) / 2, (va[1] + vb[1]) / 2, (va[2] + vb[2]) / 2])
    }
  }
  // new vertex points
  const vFaces: number[][] = Array.from({ length: nv }, () => [])
  m.faces.forEach((f, fi) => {
    for (const vi of f) vFaces[vi].push(fi)
  })
  const vEdges: EdgeRec[][] = Array.from({ length: nv }, () => [])
  for (const e of edges.values()) {
    vEdges[e.a].push(e)
    vEdges[e.b].push(e)
  }
  const newVerts: Vec3[] = m.verts.map((v, vi) => {
    const boundary = vEdges[vi].filter((e) => e.faces.length === 1)
    if (boundary.length > 0) {
      // boundary rule: (6v + sum of the two boundary edge midpoints') / 8
      let sx = v[0] * 6,
        sy = v[1] * 6,
        sz = v[2] * 6
      let cnt = 6
      for (const e of boundary) {
        const o = e.a === vi ? m.verts[e.b] : m.verts[e.a]
        sx += o[0]
        sy += o[1]
        sz += o[2]
        cnt += 1
      }
      return [sx / cnt, sy / cnt, sz / cnt] as Vec3
    }
    const nf = vFaces[vi].length
    if (nf === 0) return [...v] as Vec3
    const F: Vec3 = [0, 0, 0]
    for (const fi of vFaces[vi]) {
      F[0] += facePts[fi][0]
      F[1] += facePts[fi][1]
      F[2] += facePts[fi][2]
    }
    F[0] /= nf
    F[1] /= nf
    F[2] /= nf
    const R: Vec3 = [0, 0, 0]
    const ne = vEdges[vi].length
    for (const e of vEdges[vi]) {
      R[0] += (m.verts[e.a][0] + m.verts[e.b][0]) / 2
      R[1] += (m.verts[e.a][1] + m.verts[e.b][1]) / 2
      R[2] += (m.verts[e.a][2] + m.verts[e.b][2]) / 2
    }
    R[0] /= ne
    R[1] /= ne
    R[2] /= ne
    const n = ne
    return [
      (F[0] + 2 * R[0] + (n - 3) * v[0]) / n,
      (F[1] + 2 * R[1] + (n - 3) * v[1]) / n,
      (F[2] + 2 * R[2] + (n - 3) * v[2]) / n,
    ] as Vec3
  })
  const verts: Vec3[] = [...newVerts, ...facePts, ...edgePts]
  const faceBase = nv
  const edgeBase = nv + facePts.length
  const faces: number[][] = []
  m.faces.forEach((f, fi) => {
    const n = f.length
    for (let i = 0; i < n; i++) {
      const v0 = f[i]
      const ePrev = edges.get(key(f[(i - 1 + n) % n], v0))!
      const eNext = edges.get(key(v0, f[(i + 1) % n]))!
      faces.push([v0, edgeBase + eNext.idx, faceBase + fi, edgeBase + ePrev.idx])
    }
  })
  m.verts = verts
  m.faces = faces
  m.uvs = null
  m.colors = null
}

// -------------------------------------------------------------- bevel (box)

/** Rounded box replacing `box + bevel`: per-axis knots concentrate the grid on
 * the bevel arc, clamp+project rounds it, exact shared-edge points weld. */
export function roundedBoxMesh(
  bounds: [number, number, number, number, number, number],
  radius: number,
  segments: number,
): MeshData {
  const [x0, y0, z0, x1, y1, z1] = bounds
  const h: Vec3 = [(x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2]
  const c: Vec3 = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
  const r = Math.min(radius, Math.min(h[0], h[1], h[2]) * 0.999)
  const s = Math.max(1, segments)
  const knots = (hh: number): number[] => {
    const inner = hh - r
    const out: number[] = []
    for (let k = s; k >= 0; k--) out.push(-(inner + r * Math.tan((Math.PI / 4) * (k / s))))
    for (let k = 0; k <= s; k++) out.push(inner + r * Math.tan((Math.PI / 4) * (k / s)))
    return out
  }
  const ax = [knots(h[0]), knots(h[1]), knots(h[2])]
  const project = (p: Vec3): Vec3 => {
    const inner: Vec3 = [Math.max(h[0] - r, 0), Math.max(h[1] - r, 0), Math.max(h[2] - r, 0)]
    const q: Vec3 = [
      Math.min(Math.max(p[0], -inner[0]), inner[0]),
      Math.min(Math.max(p[1], -inner[1]), inner[1]),
      Math.min(Math.max(p[2], -inner[2]), inner[2]),
    ]
    const d = sub(p, q)
    const l = len(d)
    if (l < 1e-12) return p
    return [q[0] + (d[0] / l) * r, q[1] + (d[1] / l) * r, q[2] + (d[2] / l) * r]
  }
  const vmap = new Map<string, number>()
  const verts: Vec3[] = []
  const faces: number[][] = []
  const vid = (p: Vec3): number => {
    const k = p.map((x) => Math.round(x * 1e7)).join('_')
    let idx = vmap.get(k)
    if (idx === undefined) {
      idx = verts.length
      verts.push([p[0] + c[0], p[1] + c[1], p[2] + c[2]])
      vmap.set(k, idx)
    }
    return idx
  }
  // six faces: (axis, sign); grid over the other two axes
  const AXES: [number, number, number][] = [
    [0, 1, 2],
    [1, 2, 0],
    [2, 0, 1],
  ]
  for (const [a, u, v] of AXES) {
    for (const sign of [-1, 1]) {
      const gu = ax[u]
      const gv = ax[v]
      for (let i = 0; i < gu.length - 1; i++) {
        for (let j = 0; j < gv.length - 1; j++) {
          const mk = (uu: number, vv: number): number => {
            const p: Vec3 = [0, 0, 0]
            p[a] = sign * h[a]
            p[u] = uu
            p[v] = vv
            return vid(project(p))
          }
          const q = [mk(gu[i], gv[j]), mk(gu[i + 1], gv[j]), mk(gu[i + 1], gv[j + 1]), mk(gu[i], gv[j + 1])]
          if (sign < 0) q.reverse()
          // drop degenerate quads (collapsed at weld points)
          const uq = q.filter((x, k) => q.indexOf(x) === k)
          if (uq.length >= 3) faces.push(uq)
        }
      }
    }
  }
  const m = MeshData.from(verts, faces)
  // axis-flip ordering: a-axis face windings need checking; recalc fixes them
  recalcNormals(m)
  m.shading = { mode: 'smooth', angle: 40 }
  return m
}

/** Convex-polygon inset (mitred), shared by the parquet and prism bevels. */
export function insetPoly(poly: Vec2[], d: number): Vec2[] {
  const n = poly.length
  const out: Vec2[] = []
  for (let i = 0; i < n; i++) {
    const p = poly[i]
    const a = poly[(i - 1 + n) % n]
    const b = poly[(i + 1) % n]
    const e0: Vec2 = [p[0] - a[0], p[1] - a[1]]
    const e1: Vec2 = [b[0] - p[0], b[1] - p[1]]
    const l0 = Math.hypot(e0[0], e0[1]) || 1
    const l1 = Math.hypot(e1[0], e1[1]) || 1
    e0[0] /= l0
    e0[1] /= l0
    e1[0] /= l1
    e1[1] /= l1
    const n0: Vec2 = [-e0[1], e0[0]]
    const n1: Vec2 = [-e1[1], e1[0]]
    let bis: Vec2 = [n0[0] + n1[0], n0[1] + n1[1]]
    const bl = Math.hypot(bis[0], bis[1])
    if (bl < 1e-6) bis = n0
    else bis = [bis[0] / bl, bis[1] / bl]
    const cosh = Math.max(0.2, bis[0] * n0[0] + bis[1] * n0[1])
    out.push([p[0] + (bis[0] * d) / cosh, p[1] + (bis[1] * d) / cosh])
  }
  return out
}

/** Prism with rounded top/bottom edges, replacing `prism + bevel` where the
 * bevel is what makes the piece read (glass table top, rugs, the tub rims). */
export function beveledPrismMesh(poly: Vec2[], z0: number, z1: number, r: number, segments: number): MeshData {
  const s = Math.max(1, segments)
  const rr = Math.min(r, (z1 - z0) / 2 - 1e-5)
  const rings: Vec3[][] = []
  const ringAt = (inset: number, z: number): Vec3[] => insetPoly(poly, inset).map((p) => [p[0], p[1], z] as Vec3)
  for (let k = 0; k <= s; k++) {
    const a = (Math.PI / 2) * (k / s)
    rings.push(ringAt(rr * (1 - Math.sin(a)), z0 + rr * (1 - Math.cos(a))))
  }
  for (let k = 0; k <= s; k++) {
    const a = (Math.PI / 2) * (k / s)
    rings.push(ringAt(rr * (1 - Math.cos(a)), z1 - rr * (1 - Math.sin(a))))
  }
  const n = poly.length
  const verts: Vec3[] = []
  const faces: number[][] = []
  for (const ring of rings) for (const p of ring) verts.push(p)
  const nr = rings.length
  for (let i = 0; i < nr - 1; i++) {
    for (let j = 0; j < n; j++) {
      const j2 = (j + 1) % n
      faces.push([i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j])
    }
  }
  faces.push(Array.from({ length: n }, (_, j) => n - 1 - j)) // bottom cap
  faces.push(Array.from({ length: n }, (_, j) => (nr - 1) * n + j)) // top cap
  const m = MeshData.from(verts, faces)
  recalcNormals(m)
  m.shading = { mode: 'smooth', angle: 40 }
  return m
}

/** Bevel port: boxes become rounded boxes, z-prisms get rounded rims,
 * everything else keeps its (already smooth-shaded) geometry. */
export function bevel(m: MeshData, amount = 0.004, segments = 2): MeshData {
  if (m.provenance?.kind === 'box') {
    const nm = roundedBoxMesh(m.provenance.bounds, amount, segments)
    m.verts = nm.verts
    m.faces = nm.faces
    m.shading = nm.shading
    m.provenance = null
  } else if (m.provenance?.kind === 'prism' && amount >= 0.003) {
    const p = m.provenance
    const nm = beveledPrismMesh(p.poly, p.z0, p.z1, amount, segments)
    m.verts = nm.verts
    m.faces = nm.faces
    m.shading = nm.shading
    m.provenance = null
  }
  return m
}

export function markBox(m: MeshData, bounds: [number, number, number, number, number, number]): MeshData {
  m.provenance = { kind: 'box', bounds }
  return m
}
export function markPrism(m: MeshData, poly: Vec2[], z0: number, z1: number): MeshData {
  m.provenance = { kind: 'prism', poly: poly.map((p) => [...p] as Vec2), z0, z1 }
  return m
}

// ------------------------------------------------------------- to geometry

export function smoothShade(m: MeshData, angle = 32): MeshData {
  m.shading = { mode: 'smooth', angle }
  return m
}
export function flatShade(m: MeshData): MeshData {
  m.shading = { mode: 'flat' }
  return m
}

/** Dissolve zero-area faces and weld coincident vertices (mlib.clean_mesh).
 * Lofts and joins leave both behind wherever a ring collapses - the fold at
 * the top of a bag, a ridge a wrap closes on - and shading breaks along the
 * whole edge loop when a normal is asked for there. */
export function cleanMesh(m: MeshData, dist = 2e-5): MeshData {
  const remap = new Array<number>(m.verts.length)
  const seen = new Map<string, number>()
  const verts: Vec3[] = []
  const colors: Vec3[] | null = m.colors ? [] : null
  for (let i = 0; i < m.verts.length; i++) {
    const v = m.verts[i]
    const key = `${Math.round(v[0] / dist)},${Math.round(v[1] / dist)},${Math.round(v[2] / dist)}`
    let idx = seen.get(key)
    if (idx === undefined) {
      idx = verts.length
      seen.set(key, idx)
      verts.push(v)
      if (colors && m.colors) colors.push(m.colors[i])
    }
    remap[i] = idx
  }
  const faces: number[][] = []
  const uvs: (Vec2[] | null)[] | null = m.uvs ? [] : null
  const faceMat: number[] | null = m.faceMat ? [] : null
  m.faces.forEach((face, fi) => {
    const ff: number[] = []
    const fuv: Vec2[] = []
    face.forEach((vi, c) => {
      const mi = remap[vi]
      if (!ff.includes(mi)) {
        ff.push(mi)
        const src = m.uvs?.[fi]
        if (src) fuv.push(src[c])
      }
    })
    if (ff.length < 3) return
    if (len(faceNormal(verts, ff)) < 1e-12) return
    faces.push(ff)
    if (uvs) uvs.push(m.uvs?.[fi] ? fuv : null)
    if (faceMat && m.faceMat) faceMat.push(m.faceMat[fi])
  })
  m.verts = verts
  m.faces = faces
  m.uvs = uvs
  m.colors = colors
  m.faceMat = faceMat
  m.provenance = null
  return m
}

/** Triangulate into a non-indexed BufferGeometry with angle-threshold smooth
 * normals (the Blender 4.x smooth-by-angle port). */
export function toGeometry(m: MeshData): THREE.BufferGeometry {
  const fNormals: Vec3[] = m.faces.map((f) => norm(faceNormal(m.verts, f)))
  const smooth = m.shading.mode === 'smooth'
  const cosLimit = smooth ? Math.cos(((m.shading as { angle: number }).angle * Math.PI) / 180) : 2
  // vertex -> adjacent faces
  const vFaces: number[][] = Array.from({ length: m.verts.length }, () => [])
  if (smooth) {
    m.faces.forEach((f, fi) => {
      for (const vi of f) vFaces[vi].push(fi)
    })
  }
  const positions: number[] = []
  const normals: number[] = []
  const uvs: number[] = []
  const cols: number[] = []
  const hasUv = !!m.uvs
  const hasCol = !!m.colors
  const cornerNormal = (vi: number, fi: number): Vec3 => {
    if (!smooth) return fNormals[fi]
    const fn = fNormals[fi]
    let nx = 0,
      ny = 0,
      nz = 0
    for (const ofi of vFaces[vi]) {
      const on = fNormals[ofi]
      if (dot(fn, on) >= cosLimit - 1e-9) {
        nx += on[0]
        ny += on[1]
        nz += on[2]
      }
    }
    const l = Math.hypot(nx, ny, nz)
    if (l < 1e-9) return fn
    return [nx / l, ny / l, nz / l]
  }
  m.faces.forEach((f, fi) => {
    const tris = triangulateFace(m.verts, f)
    const uvFace = hasUv ? m.uvs![fi] : null
    for (const t of tris) {
      for (const ci of t) {
        const vi = f[ci]
        const p = m.verts[vi]
        positions.push(p[0], p[1], p[2])
        const n = cornerNormal(vi, fi)
        normals.push(n[0], n[1], n[2])
        if (hasUv) {
          const u = uvFace ? uvFace[ci] : [0, 0]
          uvs.push(u[0], u[1])
        }
        if (hasCol) {
          const c = m.colors![vi]
          cols.push(c[0], c[1], c[2])
        }
      }
    }
  })
  const g = new THREE.BufferGeometry()
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  g.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3))
  if (hasUv) g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2))
  if (hasCol) g.setAttribute(m.colorName || 'color', new THREE.Float32BufferAttribute(cols, 3))
  return g
}
