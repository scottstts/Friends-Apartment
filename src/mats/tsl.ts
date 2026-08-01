/** TSL ports of the Blender shading nodes the build's materials are made of:
 * fBM noise, wave, brick, voronoi, colour ramp, layer weight, bump.
 *
 * Numeric behaviour follows Blender's node implementations (fBM accumulation,
 * brick offsets, wave profiles, mapping order); the underlying gradient noise
 * is MaterialX perlin, which shares Blender-noise's range and character.
 */
import * as THREE from 'three/webgpu'
import {
  Fn,
  abs,
  add,
  clamp,
  dot,
  dFdx,
  dFdy,
  float,
  floor,
  fract,
  hash,
  min,
  mix,
  mul,
  mx_noise_float,
  normalView,
  positionView,
  select,
  sin,
  smoothstep,
  sub,
  vec3,
  vec4,
} from 'three/tsl'

// The TSL object graph is untyped enough that a loose alias keeps the port
// readable; every helper both accepts and returns node objects.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type N = any

/** hex -> linear rgb triple (Blender's srgb() port). */
export function srgbTriple(h: string | [number, number, number]): [number, number, number] {
  let r: number, g: number, b: number
  if (typeof h === 'string') {
    const s = h.replace('#', '')
    r = parseInt(s.slice(0, 2), 16) / 255
    g = parseInt(s.slice(2, 4), 16) / 255
    b = parseInt(s.slice(4, 6), 16) / 255
  } else {
    ;[r, g, b] = h
  }
  const f = (u: number) => (u <= 0.04045 ? u / 12.92 : ((u + 0.055) / 1.055) ** 2.4)
  return [f(r), f(g), f(b)]
}

export function srgb(h: string | [number, number, number]): N {
  const [r, g, b] = srgbTriple(h)
  return vec3(r, g, b)
}

export function srgbColor(h: string | [number, number, number]): THREE.Color {
  const [r, g, b] = srgbTriple(h)
  return new THREE.Color(r, g, b)
}

/** Blender implicit color -> float conversion (rec709 luminance). */
export function lum(c: N): N {
  return dot(c, vec3(0.2126, 0.7152, 0.0722))
}

// ------------------------------------------------------------------- mapping

/** Blender Mapping node (point): rot_euler_xyz(p * scale) + loc. */
export function mapping(p: N, scale: [number, number, number] = [1, 1, 1], rot: [number, number, number] = [0, 0, 0], loc: [number, number, number] = [0, 0, 0]): N {
  let q: N = mul(p, vec3(...scale))
  const [rx, ry, rz] = rot
  if (rx !== 0) {
    const c = Math.cos(rx)
    const s = Math.sin(rx)
    q = vec3(q.x, add(mul(q.y, c), mul(q.z, -s)), add(mul(q.y, s), mul(q.z, c)))
  }
  if (ry !== 0) {
    const c = Math.cos(ry)
    const s = Math.sin(ry)
    q = vec3(add(mul(q.x, c), mul(q.z, s)), q.y, add(mul(q.x, -s), mul(q.z, c)))
  }
  if (rz !== 0) {
    const c = Math.cos(rz)
    const s = Math.sin(rz)
    q = vec3(sub(mul(q.x, c), mul(q.y, s)), add(mul(q.x, s), mul(q.y, c)), q.z)
  }
  if (loc[0] !== 0 || loc[1] !== 0 || loc[2] !== 0) q = add(q, vec3(...loc))
  return q
}

// --------------------------------------------------------------------- noise

/** Blender Noise Texture Fac: normalised fBM remapped to 0..1. */
export function bnoise(p: N, scale: number, detail = 2, rough = 0.5, distortion = 0): N {
  let q: N = mul(p, scale)
  if (distortion !== 0) {
    const d = vec3(
      mx_noise_float(add(q, vec3(551.0, 13.5, 21.6))),
      mx_noise_float(add(q, vec3(762.0, 550.0, 231.0))),
      mx_noise_float(add(q, vec3(91.0, 113.0, 4130.0))),
    )
    q = add(q, mul(d, distortion))
  }
  const octs = Math.floor(Math.min(15, Math.max(0, detail)))
  let sum: N = float(0)
  let amp = 1
  let maxamp = 0
  let fscale = 1
  for (let i = 0; i <= octs; i++) {
    sum = add(sum, mul(mx_noise_float(mul(q, fscale)), amp))
    maxamp += amp
    amp *= rough
    fscale *= 2
  }
  return add(mul(sum.div(maxamp), 0.5), 0.5)
}

/** Colour variant: three offset samples, like Blender's vector fBM. */
export function bnoise3(p: N, scale: number, detail = 2, rough = 0.5): N {
  return vec3(
    bnoise(add(p, vec3(0, 0, 0)), scale, detail, rough),
    bnoise(add(p, vec3(23.1, 113.2, 71.7)), scale, detail, rough),
    bnoise(add(p, vec3(-58.9, 17.4, 155.2)), scale, detail, rough),
  )
}

// ---------------------------------------------------------------------- wave

export interface WaveOpts {
  type?: 'BANDS' | 'RINGS'
  dir?: 'X' | 'Y' | 'DIAGONAL' | 'SPHERICAL'
  profile?: 'SIN' | 'TRI' | 'SAW'
  scale?: number
  distortion?: number
  detail?: number
}

/** Blender Wave Texture Fac. */
export function wave(p: N, opts: WaveOpts): N {
  const { type = 'BANDS', dir = 'X', profile = 'SIN', scale = 1, distortion = 0, detail = 2 } = opts
  const q: N = mul(p, scale)
  let n: N
  if (type === 'BANDS') {
    if (dir === 'X') n = mul(q.x, 20)
    else if (dir === 'Y') n = mul(q.y, 20)
    else n = mul(add(add(q.x, q.y), q.z), 10)
  } else {
    // RINGS (spherical)
    n = mul(q.length(), 20)
  }
  if (distortion !== 0) {
    n = add(n, mul(sub(mul(bnoise(q, 1, detail, 0.5), 2), 1), distortion))
  }
  if (profile === 'SIN') {
    return add(mul(sin(n), 0.5), 0.5)
  } else if (profile === 'SAW') {
    return fract(n.div(Math.PI * 2))
  }
  // TRI
  const f = n.div(Math.PI * 2)
  return mul(abs(sub(f, floor(add(f, 0.5)))), 2)
}

// --------------------------------------------------------------------- brick

export interface BrickOpts {
  offset?: number
  offsetFreq?: number
  squash?: number
  squashFreq?: number
  scale?: number
  mortarSize?: number
  mortarSmooth?: number
  bias?: number
  brickWidth?: number
  rowHeight?: number
}

/** Blender Brick Texture -> { tint (per-brick random 0..1), fac (mortar mask) }.
 * Colour is assembled by the caller from color1/color2/mortar like the node does. */
export function brickTex(p: N, opts: BrickOpts): { tint: N; fac: N } {
  const {
    offset = 0.5,
    offsetFreq = 2,
    squash = 1,
    squashFreq = 2,
    scale = 1,
    mortarSize = 0.01,
    mortarSmooth = 0.1,
    bias = 0,
    brickWidth = 0.5,
    rowHeight = 0.25,
  } = opts
  const q: N = mul(p, scale)
  const rownum: N = floor(q.y.div(rowHeight))
  const rowMod = (f: number): N => sub(rownum, mul(floor(rownum.div(f)), f))
  const bw: N = select(rowMod(squashFreq).lessThan(0.5), mul(brickWidth, squash), float(brickWidth))
  const off: N = select(rowMod(offsetFreq).lessThan(0.5), float(0), mul(bw, offset))
  const bricknum: N = floor(add(q.x, off).div(bw))
  const x: N = sub(add(q.x, off), mul(bw, bricknum))
  const y: N = sub(q.y, mul(rowHeight, rownum))
  const tint: N = add(hash(add(mul(rownum, 641.13), mul(bricknum, 173.7))), bias)
  const minDist: N = min(min(x, y), min(sub(bw, x), sub(float(rowHeight), y)))
  let fac: N
  if (mortarSmooth === 0) {
    fac = select(minDist.greaterThanEqual(mortarSize), float(0), float(1))
  } else {
    const s = smoothstep(0, mortarSmooth, sub(1, minDist.div(mortarSize)))
    fac = select(minDist.greaterThanEqual(mortarSize), float(0), s)
  }
  return { tint: clamp(tint, 0, 1), fac }
}

// ------------------------------------------------------------------- voronoi

function hash3(cell: N): N {
  return vec3(
    hash(dot(cell, vec3(127.1, 311.7, 74.7))),
    hash(dot(cell, vec3(269.5, 183.3, 246.1))),
    hash(dot(cell, vec3(113.5, 271.9, 124.6))),
  )
}

export interface VoronoiOut {
  /** distance to F1 in the scaled space (Blender 4.x semantics) */
  distance: N
  /** random colour of the winning cell */
  color: N
  /** feature position divided back into input space (Blender 4.x semantics) */
  position: N
}

const voronoiFns = new Map<string, N>()

function voronoiFn(scale: number, randomness: number, exponent: number | undefined, out: 'posDist' | 'col'): N {
  const key = `${scale}_${randomness}_${exponent}_${out}`
  let fn = voronoiFns.get(key)
  if (!fn) {
    fn = Fn(([pp]: [N]) => {
      const q = mul(pp, scale).toVar()
      const cell = floor(q).toVar()
      const best = float(1e9).toVar()
      const bestPos = vec3(0).toVar()
      const bestCol = vec3(0).toVar()
      for (let dz = -1; dz <= 1; dz++) {
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const c = add(cell, vec3(dx, dy, dz))
            const pos = add(c, mul(hash3(c), randomness))
            const d = sub(pos, q)
            let dist: N
            if (exponent !== undefined) {
              const e = exponent
              dist = add(add(abs(d.x).pow(e), abs(d.y).pow(e)), abs(d.z).pow(e)).pow(1 / e)
            } else {
              dist = d.length()
            }
            const closer = dist.lessThan(best)
            bestPos.assign(select(closer, pos, bestPos))
            if (out === 'col') bestCol.assign(select(closer, hash3(c), bestCol))
            best.assign(select(closer, dist, best))
          }
        }
      }
      if (out === 'col') return bestCol
      return vec4(bestPos, best)
    })
    voronoiFns.set(key, fn)
  }
  return fn
}

/** 3D F1 voronoi with randomness and optional Minkowski exponent. */
export function voronoi(p: N, scale: number, randomness = 1, exponent?: number): VoronoiOut {
  const pd = voronoiFn(scale, randomness, exponent, 'posDist')(p)
  return {
    distance: pd.w,
    get color() {
      return voronoiFn(scale, randomness, exponent, 'col')(p)
    },
    position: pd.xyz.div(scale),
  }
}

// --------------------------------------------------------------------- ramps

export type RampStop = [number, [number, number, number] | N]

/** Blender ColorRamp.  Returns vec3; take .r where a float is wanted. */
export function ramp(fac: N, stops: RampStop[], interp: 'LINEAR' | 'CONSTANT' | 'B_SPLINE' = 'LINEAR'): N {
  const col = (c: RampStop[1]): N => (Array.isArray(c) ? vec3(c[0], c[1], c[2]) : c)
  let out: N = col(stops[0][1])
  for (let i = 0; i < stops.length - 1; i++) {
    const [p0] = stops[i]
    const [p1, c1] = stops[i + 1]
    let t: N
    if (interp === 'CONSTANT') {
      t = select(fac.lessThan(p1), float(0), float(1))
    } else if (p1 - p0 < 1e-9) {
      t = select(fac.lessThan(p1), float(0), float(1))
    } else if (interp === 'B_SPLINE') {
      t = smoothstep(p0, p1, fac)
    } else {
      t = clamp(sub(fac, p0).div(p1 - p0), 0, 1)
    }
    out = mix(out, col(c1), t)
  }
  return out
}

/** Grey ramp helper: float stops -> float output. */
export function rampF(fac: N, stops: [number, number][], interp: 'LINEAR' | 'CONSTANT' | 'B_SPLINE' = 'LINEAR'): N {
  return ramp(
    fac,
    stops.map(([p, v]) => [p, [v, v, v]] as RampStop),
    interp,
  ).r
}

// ------------------------------------------------------------------ facing

/** Blender Layer Weight 'Facing' output. */
export function layerWeightFacing(blend: number): N {
  const cosi = abs(dot(normalView.normalize(), positionView.negate().normalize()))
  let b = Math.min(Math.max(blend, 0), 1 - 1e-5)
  if (b !== 0.5) b = b < 0.5 ? 2 * b : 0.5 / (1 - b)
  return sub(1, cosi.pow(b))
}

// -------------------------------------------------------------------- bump

/** Height-field bump via screen-space derivatives (the realtime equivalent of
 * Blender's Bump node).  Returns a view-space normal for material.normalNode. */
export function bumpNormal(height: N, strength: number, dist = 1): N {
  const h = mul(height, strength * dist * 60.0)
  const dHdx = dFdx(h)
  const dHdy = dFdy(h)
  const sigmaX = dFdx(positionView)
  const sigmaY = dFdy(positionView)
  const vN = normalView
  const R1 = sigmaY.cross(vN)
  const R2 = vN.cross(sigmaX)
  const det = sigmaX.dot(R1)
  const grad = mul(det.sign(), add(mul(dHdx, R1), mul(dHdy, R2)))
  return sub(mul(det.abs(), vN), grad).normalize()
}
