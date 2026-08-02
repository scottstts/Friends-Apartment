/** Dimensioned furniture primitives from build_scripts/Joeys_apt/props.py. */
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'

const TAU = Math.PI * 2

export const cyl = (r: number, z0: number, z1: number, seg = 24, cx = 0, cy = 0, phase = 0): MeshData =>
  mlib.prism(mlib.circle(r, seg, cx, cy, phase), z0, z1)

export function lathe(profile: Vec2[], seg = 28, smooth = 42, cap = true): MeshData {
  const md = mlib.revolve(profile, seg, { capStart: cap, capEnd: cap })
  if (smooth) mlib.smoothShade(md, smooth)
  return md
}

export const rod = (p0: Vec3, p1: Vec3, radius: number, seg = 12, cap = true): MeshData =>
  mlib.tubeAlong([p0, p1], mlib.circle(radius, seg), { cap })

export function torus(major: number, minor: number, uSegments = 32, vSegments = 12, center: Vec3 = [0, 0, 0], arc = TAU): MeshData {
  const rings: Vec3[][] = []
  const count = Math.abs(arc - TAU) < 1e-6 ? uSegments : uSegments + 1
  for (let i = 0; i < count; i++) {
    const a = (arc * i) / uSegments
    const ca = Math.cos(a)
    const sa = Math.sin(a)
    const ring: Vec3[] = []
    for (let j = 0; j < vSegments; j++) {
      const b = (TAU * j) / vSegments
      const radius = major + minor * Math.cos(b)
      ring.push([center[0] + radius * ca, center[1] + radius * sa, center[2] + minor * Math.sin(b)])
    }
    rings.push(ring)
  }
  const md = mlib.loft(rings, { closeU: Math.abs(arc - TAU) < 1e-6, closeV: true })
  mlib.smoothShade(md, 60)
  return md
}

const vsub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
const vdot = (a: Vec3, b: Vec3): number => a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
const vcross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
const vnorm = (a: Vec3): Vec3 => {
  const length = Math.hypot(...a) || 1
  return [a[0] / length, a[1] / length, a[2] / length]
}

/** Parallel-transported elliptical sweep used by organic furniture and props. */
export function sweepVar(spine: Vec3[], radii: Vec2[], seg = 14, up: Vec3 = [0, 0, 1], cap = true, smooth = 60): MeshData {
  const tangents = spine.map((_, i) => vnorm(i === 0 ? vsub(spine[1], spine[0]) : i === spine.length - 1 ? vsub(spine.at(-1)!, spine.at(-2)!) : vsub(spine[i + 1], spine[i - 1])))
  let reference = [...up] as Vec3
  if (Math.abs(vdot(tangents[0], reference)) > 0.9) reference = [1, 0, 0]
  let side = vnorm(vcross(tangents[0], reference))
  const rings = spine.map((point, i) => {
    const tangent = tangents[i]
    const projected: Vec3 = [side[0] - tangent[0] * vdot(side, tangent), side[1] - tangent[1] * vdot(side, tangent), side[2] - tangent[2] * vdot(side, tangent)]
    side = Math.hypot(...projected) < 1e-6 ? vnorm(vcross(tangent, Math.abs(tangent[2]) < 0.9 ? [0, 0, 1] : [1, 0, 0])) : vnorm(projected)
    const up2 = vnorm(vcross(side, tangent))
    const [across, vertical] = radii[i]
    return Array.from({ length: seg }, (_, j) => {
      const angle = (TAU * j) / seg
      return [
        point[0] + side[0] * across * Math.cos(angle) + up2[0] * vertical * Math.sin(angle),
        point[1] + side[1] * across * Math.cos(angle) + up2[1] * vertical * Math.sin(angle),
        point[2] + side[2] * across * Math.cos(angle) + up2[2] * vertical * Math.sin(angle),
      ] as Vec3
    })
  })
  const md = mlib.loft(rings, { closeV: true, capStart: cap, capEnd: cap })
  if (smooth) mlib.smoothShade(md, smooth)
  return md
}

export function faceY(md: MeshData, sign = -1, at: Vec3 = [0, 0, 0]): MeshData {
  mlib.rotX(md, (-Math.PI * 0.5) * sign)
  return mlib.translate(md, at)
}

export function faceX(md: MeshData, sign = 1, at: Vec3 = [0, 0, 0]): MeshData {
  mlib.rotY(md, Math.PI * 0.5 * sign)
  return mlib.translate(md, at)
}

export function cabinetDoor(width: number, height: number, thickness = 0.019, rail = 0.058, inset = 0.01, proud = 0.0055, bevel = true): MeshData {
  const md = mlib.join([
    mlib.box(0, 0, 0, rail, thickness, height),
    mlib.box(width - rail, 0, 0, width, thickness, height),
    mlib.box(rail, 0, 0, width - rail, thickness, rail),
    mlib.box(rail, 0, height - rail, width - rail, thickness, height),
    mlib.box(rail - 0.004, thickness - 0.01, rail - 0.004, width - rail + 0.004, thickness, height - rail + 0.004),
    mlib.box(rail + inset, thickness - 0.01 - proud, rail + inset, width - rail - inset, thickness - 0.004, height - rail - inset),
  ])
  if (bevel) mlib.bevel(md, Math.min(proud * 0.85, 0.0045), 3)
  return md
}

export function slabFront(width: number, height: number, thickness = 0.019): MeshData {
  return mlib.bevel(mlib.box(0, 0, 0, width, thickness, height), 0.0035, 3)
}

export function carcass(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  z0: number,
  z1: number,
  options: { back?: number; side?: number; top?: number; backAt?: 'y0' | 'y1'; shelves?: number[]; lid?: boolean } = {},
): MeshData {
  const back = options.back ?? 0.012
  const side = options.side ?? 0.016
  const top = options.top ?? 0.016
  const backAt = options.backAt ?? 'y0'
  const by0 = backAt === 'y0' ? y0 : y1 - back
  const by1 = backAt === 'y0' ? y0 + back : y1
  const iy0 = backAt === 'y0' ? by1 : y0
  const iy1 = backAt === 'y0' ? y1 : by0
  const parts = [
    mlib.box(x0, y0, z0, x0 + side, y1, z1),
    mlib.box(x1 - side, y0, z0, x1, y1, z1),
    mlib.box(x0 + side, by0, z0, x1 - side, by1, z1),
    mlib.box(x0 + side, iy0, z0, x1 - side, iy1, z0 + top),
  ]
  if (options.lid !== false) parts.push(mlib.box(x0 + side, iy0, z1 - top, x1 - side, iy1, z1))
  for (const shelf of options.shelves ?? []) parts.push(mlib.box(x0 + side, iy0, shelf - 0.009, x1 - side, iy1, shelf + 0.009))
  return mlib.bevel(mlib.join(parts), 0.0016, 2)
}

function arcPoints(cx: number, cy: number, radius: number, a0: number, a1: number, segments: number): Vec2[] {
  return Array.from({ length: segments + 1 }, (_, i) => {
    const a = a0 + (a1 - a0) * (i / segments)
    return [cx + Math.cos(a) * radius, cy + Math.sin(a) * radius] as Vec2
  })
}

export function worktop(
  x0: number,
  y0: number,
  x1: number,
  y1: number,
  top: number,
  options: { thickness?: number; radius?: number; segments?: number; radii?: [number, number, number, number] } = {},
): MeshData {
  const thickness = options.thickness ?? 0.038
  const radius = options.radius ?? 0.008
  const segments = options.segments ?? 4
  const radii = options.radii ?? [radius, radius, radius, radius]
  const spec: [[number, number], number, number][] = [
    [[x0 + radii[0], y0 + radii[0]], Math.PI, radii[0]],
    [[x1 - radii[1], y0 + radii[1]], Math.PI * 1.5, radii[1]],
    [[x1 - radii[2], y1 - radii[2]], 0, radii[2]],
    [[x0 + radii[3], y1 - radii[3]], Math.PI * 0.5, radii[3]],
  ]
  const points: Vec2[] = []
  for (const [center, start, corner] of spec) points.push(...(corner <= 1e-6 ? [center] : arcPoints(center[0], center[1], corner, start, start + Math.PI * 0.5, segments)))
  const md = mlib.prism(points, top - thickness, top)
  mlib.bevel(md, Math.min(0.004, thickness * 0.16), 3)
  mlib.smoothShade(md, 34)
  return md
}

export const plinth = (x0: number, y0: number, x1: number, y1: number, z0: number, z1: number): MeshData =>
  mlib.bevel(mlib.box(x0, y0, z0, x1, y1, z1), 0.003, 2)

export function knob(radius = 0.017, stem = 0.014): MeshData {
  const r = radius
  return lathe([[0, 0], [r * 0.62, 0], [r * 0.6, 0.004], [r * 0.3, 0.007], [r * 0.28, stem * 0.55], [r * 0.52, stem * 0.86], [r * 0.98, stem + r * 0.3], [r * 0.94, stem + r * 0.72], [r * 0.62, stem + r * 1.02], [0, stem + r * 1.1]], 22, 46)
}

export function barPull(length: number, radius = 0.0062, stand = 0.03): MeshData {
  const a = length * 0.5 - 0.014
  const path: Vec3[] = [[-a, 0, 0], [-a, -stand + radius * 1.4, 0], [-a, -stand, 0], [a, -stand, 0], [a, -stand + radius * 1.4, 0], [a, 0, 0]]
  const md = mlib.tubeAlong(path, mlib.circle(radius, 12))
  mlib.smoothShade(md, 46)
  return md
}

export function handleBar(length: number, radius = 0.011, stand = 0.052, plate = 0.03): MeshData {
  const a = length * 0.5
  const parts = [mlib.tubeAlong([[-a, -stand, 0], [a, -stand, 0]], mlib.circle(radius, 14))]
  for (const side of [-1, 1]) {
    const post = lathe([[0, 0], [plate * 0.5, 0], [plate * 0.46, 0.01], [radius * 1.5, stand - radius], [0, stand - radius]], 16)
    faceY(post, -1, [a * side, 0, 0])
    parts.push(post)
  }
  const md = mlib.join(parts)
  mlib.smoothShade(md, 44)
  return md
}

export const turnedLeg = (height: number, topRadius = 0.026, segments = 20, taper = 0.55): MeshData => {
  const r = topRadius
  return lathe([[0, 0], [r * taper * 0.9, 0], [r * taper * 1.05, 0.014], [r * taper * 0.86, 0.03], [r * 0.8, height * 0.3], [r * 0.98, height * 0.52], [r * 0.92, height * 0.74], [r * 1.02, height * 0.88], [r * 0.99, height * 0.95], [r, height], [0, height]], segments, 44)
}

export function taperLeg(height: number, top = 0.042, bottom = 0.022, radius = 0.004): MeshData {
  const rings = [[0, bottom], [1, top]].map(([t, size]) => mlib.roundedRect(size, size, radius, 3).map(([x, y]) => [x, y, t * height] as Vec3))
  const md = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  return mlib.bevel(md, 0.0015, 2)
}

export function hairpin(height: number, spread = 0.16, radius = 0.005, legs = 3, plate = 0.038): MeshData {
  const parts = [mlib.box(-plate, -plate, height - 0.004, plate, plate, height)]
  for (let i = 0; i < legs; i++) {
    const angle = (TAU * i) / legs + Math.PI * 0.25
    const dx = Math.cos(angle) * spread
    const dy = Math.sin(angle) * spread
    parts.push(mlib.tubeAlong([[dx, dy, 0], [dx * 0.94, dy * 0.94, height * 0.1], [dx * 0.62, dy * 0.62, height * 0.44], [dx * 0.22, dy * 0.22, height * 0.8], [0, 0, height - 0.002]], mlib.circle(radius, 8)))
  }
  const md = mlib.join(parts)
  mlib.smoothShade(md, 46)
  return md
}

export function drape(
  x0: number,
  x1: number,
  y: number,
  z0: number,
  z1: number,
  options: { folds?: number; amplitude?: number; nz?: number; taper?: number; seed?: number; axis?: 'X' | 'Y'; flare?: number; thickness?: number } = {},
): MeshData {
  const folds = options.folds ?? 7
  const amplitude = options.amplitude ?? 0.055
  const nz = options.nz ?? 14
  const taper = options.taper ?? 0.55
  const flare = options.flare ?? 1.18
  const rng = new PyRandom(options.seed ?? 3)
  const span = x1 - x0
  const columns = Math.max(24, Math.floor(folds * 9))
  const jitter = Array.from({ length: folds + 2 }, () => 1 + rng.uniform(-0.3, 0.3))
  const rings: Vec3[][] = []
  for (let column = 0; column <= columns; column++) {
    const u = column / columns
    const f = u * folds
    const depth = Math.cos(f * TAU) * jitter[Math.floor(f) % jitter.length]
    const edge = Math.min(1, Math.min(u, 1 - u) / 0.06)
    const ring: Vec3[] = []
    for (let row = 0; row <= nz; row++) {
      const t = row / nz
      const grow = taper + (1 - taper) * t ** 0.65 * flare
      const off = depth * amplitude * grow * edge
      const z = z0 + (z1 - z0) * t - (1 - Math.abs(depth)) * 0.006 * (1 - t) ** 2
      ring.push(options.axis === 'Y' ? [y + off, x0 + span * u, z] : [x0 + span * u, y + off, z])
    }
    rings.push(ring)
  }
  const md = mlib.loft(rings)
  mlib.solidify(md, options.thickness ?? 0.0045)
  mlib.smoothShade(md, 52)
  return md
}

export const skirt = (x0: number, x1: number, y: number, z0: number, z1: number, folds = 9, amplitude = 0.026, seed = 7): MeshData =>
  drape(x0, x1, y, z0, z1, { folds, amplitude, nz: 8, taper: 0.28, seed, flare: 1.25, thickness: 0.0035 })

export const pillow = (width: number, height: number, depth: number): MeshData => mlib.cushion(width, height, depth, Math.min(width, height) * 0.34, 6)

export function bolster(length: number, radius: number, segments = 20): MeshData {
  return lathe([[0, 0], [radius * 0.3, 0.006], [radius * 0.8, 0.03], [radius, 0.1], [radius * 1.02, length * 0.5], [radius, length - 0.1], [radius * 0.8, length - 0.03], [radius * 0.3, length - 0.006], [0, length]], segments, 50)
}

export function rug(
  cx: number,
  cy: number,
  width: number,
  depth: number,
  region: (u: number, v: number) => number,
  options: { cell?: number; thickness?: number; pile?: number; seed?: number; rotation?: number; z0?: number } = {},
): MeshData {
  const cell = options.cell ?? 0.035
  const thickness = options.thickness ?? 0.014
  const pile = options.pile ?? 0.0016
  const rng = new PyRandom(options.seed ?? 11)
  const nx = Math.max(4, Math.round(width / cell))
  const ny = Math.max(4, Math.round(depth / cell))
  const x0 = -width * 0.5
  const y0 = -depth * 0.5
  const top = new Map<string, number>()
  const verts: Vec3[] = []
  const faces: number[][] = []
  const materials: number[] = []
  const tv = (i: number, j: number): number => {
    const key = `${i}:${j}`
    let index = top.get(key)
    if (index === undefined) {
      index = verts.length
      verts.push([x0 + (width * i) / nx, y0 + (depth * j) / ny, thickness + rng.uniform(-pile, pile)])
      top.set(key, index)
    }
    return index
  }
  for (let i = 0; i < nx; i++) {
    for (let j = 0; j < ny; j++) {
      faces.push([tv(i, j), tv(i + 1, j), tv(i + 1, j + 1), tv(i, j + 1)])
      materials.push(region((i + 0.5) / nx, (j + 0.5) / ny))
    }
  }
  const loop: [number, number][] = [
    ...Array.from({ length: nx + 1 }, (_, i) => [i, 0] as [number, number]),
    ...Array.from({ length: ny }, (_, i) => [nx, i + 1] as [number, number]),
    ...Array.from({ length: nx }, (_, i) => [nx - 1 - i, ny] as [number, number]),
    ...Array.from({ length: ny - 1 }, (_, i) => [0, ny - 1 - i] as [number, number]),
  ]
  const low: number[] = []
  for (const [i, j] of loop) {
    const upper = verts[tv(i, j)]
    low.push(verts.length)
    verts.push([upper[0], upper[1], 0])
  }
  for (let i = 0; i < loop.length; i++) {
    const [a0, a1] = loop[i]
    const [b0, b1] = loop[(i + 1) % loop.length]
    faces.push([tv(a0, a1), low[i], low[(i + 1) % loop.length], tv(b0, b1)])
    materials.push(0)
  }
  faces.push([...low].reverse())
  materials.push(0)
  const md = MeshData.from(verts, faces)
  md.faceMat = materials
  mlib.recalcNormals(md)
  if (options.rotation) mlib.rotateZ(md, options.rotation)
  mlib.translate(md, [cx, cy, options.z0 ?? 0])
  return md
}

export function book(width: number, height: number, thickness: number): MeshData {
  return mlib.bevel(mlib.join([mlib.box(0, 0, 0, width, thickness, height), mlib.box(0.004, 0.0022, 0.004, width - 0.002, thickness - 0.0022, height - 0.004)]), 0.0012, 2)
}

export function can(cx: number, cy: number, z0: number, radius = 0.033, height = 0.122): MeshData {
  const md = lathe([[0, 0], [radius * 0.86, 0], [radius * 0.94, 0.004], [radius, 0.014], [radius, height - 0.014], [radius * 0.94, height - 0.004], [radius * 0.86, height - 0.001], [radius * 0.9, height], [0, height]], 20, 44)
  return mlib.translate(md, [cx, cy, z0])
}

export function bottle(cx: number, cy: number, z0: number, radius = 0.036, height = 0.24, neck = 0.013): MeshData {
  const md = lathe([[0, 0], [radius * 0.9, 0], [radius, 0.012], [radius, height * 0.52], [radius * 0.96, height * 0.62], [neck * 1.9, height * 0.76], [neck, height * 0.84], [neck, height - 0.014], [neck * 1.18, height - 0.01], [neck * 1.18, height], [0, height]], 20, 46)
  return mlib.translate(md, [cx, cy, z0])
}

export function jar(cx: number, cy: number, z0: number, radius = 0.052, height = 0.15): MeshData {
  const md = lathe([[0, 0], [radius * 0.88, 0], [radius, 0.018], [radius, height * 0.7], [radius * 0.9, height * 0.82], [radius * 0.74, height * 0.9], [radius * 0.78, height], [0, height]], 22, 46)
  return mlib.translate(md, [cx, cy, z0])
}

export function mug(cx: number, cy: number, z0: number, radius = 0.042, height = 0.098, handle = true, rotation = 0): MeshData {
  const body = lathe([[0, 0], [radius * 0.8, 0], [radius * 0.86, 0.006], [radius * 0.8, 0.012], [radius * 0.94, 0.03], [radius, height - 0.004], [radius, height], [radius - 0.0045, height - 0.002], [radius - 0.0045, 0.015], [0, 0.016]], 22, 48, false)
  const parts = [body]
  if (handle) {
    const path: Vec3[] = [[radius * 0.84, 0, height * 0.8], [radius * 1.34, 0, height * 0.82], [radius * 1.52, 0, height * 0.56], [radius * 1.32, 0, height * 0.3], [radius * 0.84, 0, height * 0.26]]
    const hd = mlib.tubeAlong(path, mlib.circle(0.0058, 8))
    mlib.smoothShade(hd, 50)
    parts.push(hd)
  }
  const md = mlib.join(parts)
  if (rotation) mlib.rotateZ(md, rotation)
  return mlib.translate(md, [cx, cy, z0])
}

export function bowl(cx: number, cy: number, z0: number, radius = 0.1, height = 0.062): MeshData {
  const md = lathe([[0, 0], [radius * 0.42, 0], [radius * 0.46, 0.004], [radius * 0.74, height * 0.35], [radius, height], [radius - 0.004, height - 0.002], [radius * 0.7, height * 0.34], [radius * 0.4, 0.006], [0, 0.006]], 26, 50, false)
  return mlib.translate(md, [cx, cy, z0])
}

export function boxProp(cx: number, cy: number, z0: number, width: number, depth: number, height: number, rotation = 0, radius = 0.004): MeshData {
  const md = mlib.bevel(mlib.box(-width * 0.5, -depth * 0.5, 0, width * 0.5, depth * 0.5, height), radius, 2)
  if (rotation) mlib.rotateZ(md, rotation)
  return mlib.translate(md, [cx, cy, z0])
}

function planarUvs(md: MeshData): void {
  const xs = md.verts.map((v) => v[0])
  const zs = md.verts.map((v) => v[2])
  const x0 = Math.min(...xs)
  const x1 = Math.max(...xs)
  const z0 = Math.min(...zs)
  const z1 = Math.max(...zs)
  md.uvs = md.faces.map((face) => face.map((vi) => [(md.verts[vi][0] - x0) / Math.max(1e-6, x1 - x0), (md.verts[vi][2] - z0) / Math.max(1e-6, z1 - z0)] as Vec2))
}

export function frameArt(width: number, height: number, depth = 0.03, moulding = 0.042, rebate = 0.008, standoff = 0): [MeshData, MeshData] {
  const back = standoff || -0.002
  const front = back + depth
  const profile: Vec2[] = [[0, back], [moulding, back], [moulding, back + depth * 0.58], [moulding * 0.66, front], [0, front]]
  const frame = mlib.sweepRectFrame(width, height, profile)
  mlib.bevel(frame, 0.0018, 2)
  const scale = 1 + Math.min((moulding * 0.8) / Math.min(width, height), (moulding * 1.6) / Math.max(width, height))
  const iw = width * 0.5 * scale
  const ih = height * 0.5 * scale
  const picture = mlib.box(-iw, front - rebate - 0.005, -ih, iw, front - rebate, ih)
  planarUvs(picture)
  return [frame, picture]
}

export function wallPlace(objects: MeshData[], wall: 'N' | 'S' | 'E' | 'W', u: number, z: number, at: number): MeshData[] {
  for (const md of objects) {
    if (wall === 'N') {
      mlib.rotateZ(md, Math.PI)
      mlib.translate(md, [u, at, z])
    } else if (wall === 'S') mlib.translate(md, [u, at, z])
    else if (wall === 'E') {
      mlib.rotateZ(md, Math.PI * 0.5)
      mlib.translate(md, [at, u, z])
    } else {
      mlib.rotateZ(md, -Math.PI * 0.5)
      mlib.translate(md, [at, u, z])
    }
  }
  return objects
}
