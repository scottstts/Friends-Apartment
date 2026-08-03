/** Central Perk material library: build_scripts/Central_Perk/mats.py ported
 * node graph by node graph into TSL.  Every cache key is perk-prefixed so
 * nothing aliases Monica's or Joey's datablocks.  The only bitmaps are the two
 * the Blender build sanctions (the Liberty canvas and the window decal).
 */
import * as THREE from 'three/webgpu'
import {
  Fn,
  abs,
  add,
  clamp,
  cos,
  atan,
  dot,
  float,
  floor,
  fract,
  hash,
  max,
  min,
  mix,
  mul,
  normalWorld,
  positionLocal,
  pow,
  select,
  sin,
  sqrt,
  sub,
  texture,
  uv,
  vec2,
  vec3,
} from 'three/tsl'
import { principled, pane as sharedPane, emissive as sharedEmissive, type N } from '../../mats/mats'
import { bnoise, bnoise3, bumpNormal, layerWeightFacing, lum, mapping, ramp, rampF, srgb, srgbTriple, voronoi } from '../../mats/tsl'

const TAU = Math.PI * 2

const mats = new Map<string, THREE.Material>()
const key = (name: string): string => `perk:${name}`

function cached(name: string, build: () => THREE.Material): THREE.Material {
  const prior = mats.get(name)
  if (prior) return prior
  const material = build()
  material.name = key(name)
  mats.set(name, material)
  return material
}

export function get(name: string): THREE.Material {
  const material = mats.get(name)
  if (!material) throw new Error(`Central Perk material ${name} has not been built`)
  return material
}

export function clearRegistry(): void {
  mats.clear()
}

const scaled = (hex: string, k: number, warm = 1): [number, number, number] =>
  srgbTriple(hex).map((c, i) => Math.min(1, c * k * (i === 0 ? warm : 1))) as [number, number, number]

/** Boolean node -> 0/1 float, so comparisons can drive mix factors. */
const bit = (cond: N): N => select(cond, float(1), float(0))

/** Vector along a vertical surface: u = horizontal arc-length in the wall
 * plane, v = z (mats.wall_proj). */
function wallProj(): N {
  const p = positionLocal
  const n = normalWorld
  const lenN = sqrt(add(mul(n.x, n.x), mul(n.y, n.y)))
  const safe = max(lenN, 0.06)
  const d = sub(mul(p.x, n.y), mul(p.y, n.x))
  return vec3(d.div(safe), p.z, 0)
}

/** mats._tri_vec: 2-D surface coordinate that follows the surface. Picks the
 * coordinate pair spanned by the face based on the dominant normal axis. */
function triVec(scale: [number, number]): N {
  const p = positionLocal
  const an = abs(normalWorld)
  const kx = mul(bit(an.x.greaterThan(an.y)), bit(an.x.greaterThan(an.z)))
  const kz = mul(bit(an.z.greaterThan(an.x)), bit(an.z.greaterThan(an.y)))
  const a = mix(p.x, p.y, kx)
  const b = mix(p.z, p.y, kz)
  return vec3(mul(a, scale[0]), mul(b, scale[1]), 0)
}

/** mats._weave: two crossed sine sets, one stretched. */
function weave(v: N, scale = 340, aniso = 1): N {
  return add(sin(mul(v.x, scale * TAU)), sin(mul(v.y, (scale * TAU) / aniso)))
}

/** mats._cell_uv: per-cell coords, half-drop on odd rows, |u| mirrored. */
function cellUv(v: N): { au: N; cv: N } {
  const row = floor(v.y)
  const drop = add(v.x, mul(row, 0.5))
  const cu = sub(fract(drop), 0.5)
  const cv = sub(fract(v.y), 0.5)
  return { au: abs(cu), cv }
}

/** White-noise value per lattice cell (ShaderNodeTexWhiteNoise 3D port). */
function cellRand(cell: N, seed = 0): N {
  const c = seed ? add(cell, vec3(seed, seed * 1.7, seed * 0.3)) : cell
  return hash(add(dot(c, vec3(127.1, 311.7, 74.7)), 311.7))
}

/** Blender OVERLAY mix, per channel, faded by `fac`. */
function overlayMix(a: N, b: N, fac: N | number): N {
  const two = mul(mul(a, b), 2)
  const screen = sub(1, mul(mul(sub(1, a), sub(1, b)), 2))
  const gate = clamp(mul(sub(a, 0.5), 1e5), 0, 1)
  return mix(a, mix(two, screen, gate), fac)
}

/** mats._lobe: rotated superellipse, > 0 inside. */
function lobe(au: N, cv: N, cx: number, cy: number, rx: number, ry: number, rot = 0, p = 1.35): N {
  let du: N = sub(au, cx)
  let dv: N = sub(cv, cy)
  if (rot) {
    const c = Math.cos(rot)
    const s = Math.sin(rot)
    const du2 = add(mul(du, c), mul(dv, s))
    const dv2 = add(mul(du, -s), mul(dv, c))
    du = du2
    dv = dv2
  }
  const nu = abs(du.div(rx))
  const nv = abs(dv.div(ry))
  const r = add(pow(nu, p), pow(nv, p)).pow(1 / p)
  return sub(1, r)
}

/** F1/F2 half-gap, Blender's DISTANCE_TO_EDGE stand-in. */
const voronoiEdgeFns = new Map<number, N>()

function voronoiEdge(p: N, scale: number): N {
  let fn = voronoiEdgeFns.get(scale)
  if (!fn) {
    fn = Fn(([pp]: [N]) => {
      const q = mul(pp, scale).toVar()
      const cell = floor(q).toVar()
      const d1 = float(1e9).toVar()
      const d2 = float(1e9).toVar()
      for (let dz = -1; dz <= 1; dz++) {
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const c = add(cell, vec3(dx, dy, dz))
            const h = vec3(
              hash(dot(c, vec3(127.1, 311.7, 74.7))),
              hash(dot(c, vec3(269.5, 183.3, 246.1))),
              hash(dot(c, vec3(113.5, 271.9, 124.6))),
            )
            const d = sub(add(c, h), q).length()
            const closer = d.lessThan(d1)
            d2.assign(select(closer, d1, min(d2, d)))
            d1.assign(min(d1, d))
          }
        }
      }
      return mul(sub(d2, d1), 0.5)
    })
    voronoiEdgeFns.set(scale, fn)
  }
  return fn(p)
}

/** Blender's 2-D voronoi F1 distance: feature points on the xy plane only -
 * a z=0 slice of the 3-D field would starve near-zero distances. */
const voronoi2Fns = new Map<number, N>()

function voronoi2(p: N, scale: number): N {
  let fn = voronoi2Fns.get(scale)
  if (!fn) {
    fn = Fn(([pp]: [N]) => {
      const q = mul(vec2(pp.x, pp.y), scale).toVar()
      const cell = floor(q).toVar()
      const d1 = float(1e9).toVar()
      for (let dy = -1; dy <= 1; dy++) {
        for (let dx = -1; dx <= 1; dx++) {
          const c = add(cell, vec2(dx, dy))
          const h = vec2(hash(dot(c, vec2(127.1, 311.7))), hash(dot(c, vec2(269.5, 183.3))))
          d1.assign(min(d1, sub(add(c, h), q).length()))
        }
      }
      return d1
    })
    voronoi2Fns.set(scale, fn)
  }
  return fn(p)
}

// ==================================================================== FLOORS

export function concrete(name: string, hexcol = '7C8179', rough: [number, number] = [0.42, 0.72], scale = 1.6): THREE.Material {
  return cached(name, () => {
    const v = mapping(positionLocal, [scale, scale, scale])
    const drift = bnoise(v, 0.9, 4, 0.62)
    const fine = bnoise(v, 26, 8, 0.75)
    const grit = clamp(voronoi(v, 140).distance, 0, 1)
    const base = srgbTriple(hexcol)
    const dark = base.map((c) => c * 0.74) as [number, number, number]
    const lite = base.map((c) => Math.min(1, c * 1.26)) as [number, number, number]
    const c1 = mix(vec3(...dark), vec3(...lite), drift)
    const c2 = mix(c1, vec3(base[0] * 0.86, base[1] * 0.9, base[2] * 0.86), fine)
    const c3 = mix(c2, vec3(...lite), grit)
    const rg = rampF(drift, [
      [0.15, rough[0]],
      [0.85, rough[1]],
    ])
    const bp = bumpNormal(add(fine, grit), 0.22, 0.6)
    return principled({ base: c3, roughN: rg, normal: bp, spec: 0.42 })
  })
}

export function plankFloor(name: string, light = 'B98A52', dark = '6E4522', bw = 0.135, bl = 1.35, gap = 0.0016): THREE.Material {
  return cached(name, () => {
    const p = positionLocal
    const row = p.y.div(bw)
    const rowf = floor(row)
    const rh = hash(add(mul(rowf, 269.5), 113.5))
    const xs = add(p.x, mul(rh, bl))
    const colu = xs.div(bl)
    const cell = vec3(floor(colu), floor(row), 0)
    const fx = abs(sub(fract(colu), 0.5))
    const fy = abs(sub(fract(row), 0.5))
    const rnd = cellRand(cell)
    const jx = bit(fx.greaterThan(0.5 - gap / bl))
    const jy = bit(fy.greaterThan(0.5 - gap / bw))
    const joint = max(jx, jy)
    const gv = vec3(colu, mul(row, 26), 0)
    const grain = bnoise(gv, 7, 9, 0.68, 1.3)
    const fine = bnoise(gv, 48, 4, 0.5)
    const lo = srgb(dark)
    const hi = srgbTriple(light)
    const tone = mix(lo, vec3(...hi), rnd)
    // mats.py sets Factor defaults after linking; a linked socket wins, so
    // the graph evaluates with the full noise factor (here and below)
    const col = mix(tone, lo, grain)
    const col2 = overlayMix(col, vec3(Math.min(1, hi[0] * 1.1), Math.min(1, hi[1] * 1.08), hi[2]), fine)
    const fin = mix(col2, vec3(0.01, 0.008, 0.006), joint)
    const rg = rampF(grain, [
      [0.2, 0.22],
      [0.8, 0.44],
    ])
    const rg2 = mix(rg, float(0.85), joint)
    const bp = bumpNormal(sub(grain, joint), 0.16, 0.5)
    return principled({ base: fin, roughN: rg2, normal: bp, spec: 0.5, coat: 0.18 })
  })
}

export function dotTile(
  name: string,
  field = 'EDE6D6',
  dotc = '2B2723',
  grout = 'C0B7A3',
  size = 0.098,
  gw = 0.05,
  dr = 0.115,
): THREE.Material {
  return cached(name, () => {
    const v = mapping(positionLocal, [1 / size, 1 / size, 1 / size])
    const gx = abs(sub(fract(v.x), 0.5))
    const gy = abs(sub(fract(v.y), 0.5))
    const edge = max(gx, gy)
    const joint = bit(edge.greaterThan(0.5 - gw))
    const dia = add(sub(0.5, gx), sub(0.5, gy))
    const dmask = bit(dia.lessThan(dr))
    const grime = bnoise(v, 3.2, 6, 0.6)
    const spot = bnoise(v, 40, 5)
    const f = srgbTriple(field)
    const c1 = mix(vec3(...f), vec3(f[0] * 0.82, f[1] * 0.82, f[2] * 0.8), grime)
    const c2 = mix(c1, srgb(dotc), dmask)
    const c3 = mix(c2, srgb(grout), joint)
    const rg = mix(float(0.14), float(0.7), joint)
    const rg2 = mix(rg, float(0.34), spot)
    const bp = bumpNormal(sub(1, joint), 0.5, 0.0022)
    return principled({ base: c3, roughN: rg2, normal: bp, spec: 0.55, coat: 0.22 })
  })
}

// ==================================================================== WALLS

export interface BrickOpts {
  face?: string
  face2?: string
  mortar?: string
  bw?: number
  bh?: number
  mort?: number
  spread?: number
}

export function brick(name: string, o: BrickOpts = {}): THREE.Material {
  return cached(name, () => {
    const { face = '6E4030', face2 = '4A2C20', mortar = '7E7466', bw = 0.215, bh = 0.068, mort = 0.011, spread = 1 } = o
    const proj = wallProj()
    const su = proj.x.div(bw)
    const sv = proj.y.div(bh)
    const course = floor(sv)
    const xs = add(su, mul(course, 0.5))
    const cell = vec3(floor(xs), course, 0)
    const fx = abs(sub(fract(xs), 0.5))
    const fy = abs(sub(fract(sv), 0.5))
    const rnd = cellRand(cell, 3)
    const jx = bit(fx.greaterThan(0.5 - mort / bw))
    const jy = bit(fy.greaterThan(0.5 - mort / bh))
    const joint = max(jx, jy)
    const roughN = bnoise(positionLocal, 160, 8, 0.72)
    const blot = bnoise(positionLocal, 9, 6, 0.6)
    const f1 = srgbTriple(face)
    const f2 = srgbTriple(face2)
    const s = spread
    const tone = ramp(rnd, [
      [0, scaled(face2, 1 - 0.42 * s)],
      [0.34, [...f2] as [number, number, number]],
      [0.66, [...f1] as [number, number, number]],
      [1, scaled(face, 1 + 0.55 * s, 1.06)],
    ])
    const tone2 = mix(tone, vec3(f2[0] * 0.7, f2[1] * 0.72, f2[2] * 0.7), blot)
    const tone3 = mix(tone2, vec3(Math.min(1, f1[0] * 1.15), Math.min(1, f1[1] * 1.1), Math.min(1, f1[2] * 1.05)), roughN)
    const col = mix(tone3, srgb(mortar), joint)
    const rg = mix(float(0.62), float(0.92), joint)
    const hj = sub(mul(roughN, 0.35), joint)
    const bp = bumpNormal(hj, 0.75, 0.01)
    return principled({ base: col, roughN: rg, normal: bp, spec: 0.28 })
  })
}

export function plaster(name: string, hexcol: string, rough = 0.74, bump = 0.35, scale = 22, mottle = 0.3): THREE.Material {
  return cached(name, () => {
    const v = mapping(positionLocal, [scale, scale, scale])
    const n1 = bnoise(v, 2.4, 8, 0.62)
    const n2 = bnoise(v, 17, 6, 0.5)
    const base = srgbTriple(hexcol)
    const dk = base.map((c) => c * (1 - mottle)) as [number, number, number]
    const lt = base.map((c) => Math.min(1, c * (1 + mottle * 0.8))) as [number, number, number]
    const c1 = mix(vec3(...dk), vec3(...lt), n1)
    const c2 = mix(c1, vec3(...dk), n2)
    const bp = bumpNormal(add(n1, n2), bump, 0.9)
    const rg = rampF(n2, [
      [0.2, rough - 0.06],
      [0.8, rough + 0.06],
    ])
    return principled({ base: c2, roughN: rg, normal: bp, spec: 0.3 })
  })
}

export interface PaintOpts {
  rough?: number
  sheen?: number
  bump?: number
  scale?: number
  coat?: number
}

export function paint(name: string, hexcol: string, o: PaintOpts = {}): THREE.Material {
  return cached(name, () => {
    const { rough = 0.34, sheen = 0, bump = 0.05, scale = 90, coat = 0 } = o
    const v = mapping(positionLocal, [scale, scale * 0.22, scale])
    const n = bnoise(v, 6, 6, 0.5)
    const fine = bnoise(v, 48, 3)
    const base = srgbTriple(hexcol)
    const c = mix(
      vec3(...(base.map((x) => x * 0.93) as [number, number, number])),
      vec3(...(base.map((x) => Math.min(1, x * 1.06)) as [number, number, number])),
      n,
    )
    const rg = rampF(n, [
      [0.2, rough - 0.05],
      [0.85, rough + 0.05],
    ])
    const bp = bumpNormal(add(n, fine), bump, 1)
    return principled({ base: c, roughN: rg, normal: bp, spec: 0.5, coat, sheen, sheenTint: vec3(...base) })
  })
}

export function iron(name: string, hexcol = '17372B', rough = 0.42): THREE.Material {
  return cached(name, () => {
    const v = mapping(positionLocal, [50, 50, 50])
    const cast = bnoise(v, 8, 8, 0.72)
    const pit = clamp(voronoi(v, 62).distance, 0, 1)
    const base = srgbTriple(hexcol)
    const c = mix(
      vec3(...(base.map((x) => x * 0.8) as [number, number, number])),
      vec3(...(base.map((x) => Math.min(1, x * 1.18)) as [number, number, number])),
      cast,
    )
    const rg = rampF(cast, [
      [0.15, rough - 0.1],
      [0.85, rough + 0.12],
    ])
    const bp = bumpNormal(add(mul(cast, 0.6), pit), 0.3, 0.7)
    return principled({ base: c, roughN: rg, normal: bp, spec: 0.55 })
  })
}

export interface WoodOpts {
  light?: string
  dark?: string
  ring?: number
  scale?: number
  rough?: [number, number]
  axis?: 'X' | 'Y' | 'Z'
  coat?: number
  bump?: number
}

export function wood(name: string, o: WoodOpts = {}): THREE.Material {
  return cached(name, () => {
    const { light = '9A6633', dark = '4A2A12', ring = 34, scale = 1, rough = [0.24, 0.46], axis = 'Z', coat = 0.22, bump = 0.14 } = o
    const sc: Record<'X' | 'Y' | 'Z', [number, number, number]> = {
      X: [scale, scale * ring, scale * ring],
      Y: [scale * ring, scale, scale * ring],
      Z: [scale * ring, scale * ring, scale],
    }
    const v = mapping(positionLocal, sc[axis])
    const warp = bnoise3(v, 1.1, 6, 0.6)
    const wv = add(v, warp)
    // Blender TexWave RINGS with the default rings direction: radial distance
    // around the X axis, sin profile, distortion 6, detail 3.
    let n: N = mul(sqrt(add(mul(wv.y, wv.y), mul(wv.z, wv.z))), 20)
    n = add(n, mul(sub(mul(bnoise(wv, 1, 3, 0.5), 2), 1), 6))
    const w2 = add(mul(sin(n), 0.5), 0.5)
    const pore = bnoise(v, ring * 6, 4)
    const lo = srgbTriple(dark)
    const hi = srgbTriple(light)
    const c1 = ramp(w2, [
      [0, [...lo] as [number, number, number]],
      [0.42, [...hi] as [number, number, number]],
      [0.58, [...hi] as [number, number, number]],
      [1, [...lo] as [number, number, number]],
    ])
    const c2 = mix(c1, vec3(...lo), pore)
    const rg = rampF(w2, [
      [0.1, rough[1]],
      [0.9, rough[0]],
    ])
    const bp = bumpNormal(add(w2, pore), bump, 0.5)
    return principled({ base: c2, roughN: rg, normal: bp, spec: 0.5, coat })
  })
}

export interface MarbleOpts {
  base?: string
  vein?: string
  vein2?: string
  scale?: number
}

export function marble(name: string, o: MarbleOpts = {}): THREE.Material {
  return cached(name, () => {
    const { base = '9DA396', vein = '4C5A4A', vein2 = 'D8DCCE', scale = 2.4 } = o
    const v = mapping(positionLocal, [scale, scale * 0.55, scale])
    const warp = bnoise3(v, 1.6, 8, 0.62)
    const wv = add(v, mul(warp, 0.55))
    const n1 = bnoise(wv, 3, 9, 0.55)
    const v1 = rampF(n1, [
      [0.44, 0],
      [0.5, 1],
      [0.56, 0],
    ])
    const n2 = bnoise(wv, 8, 7, 0.5)
    const v2 = rampF(n2, [
      [0.46, 0],
      [0.5, 1],
      [0.54, 0],
    ])
    const fld = bnoise(v, 2.2, 6)
    const bs = srgbTriple(base)
    const c0 = mix(vec3(...bs), vec3(...(bs.map((x) => x * 0.78) as [number, number, number])), fld)
    const c1 = mix(c0, srgb(vein), v1)
    const c2 = mix(c1, srgb(vein2), v2)
    const rg = mix(float(0.1), float(0.22), v1)
    const bp = bumpNormal(v1, 0.06, 0.4)
    return principled({ base: c2, roughN: rg, normal: bp, spec: 0.6, coat: 0.4 })
  })
}

export function glass(name: string, tint = 'EAF0EE', rough = 0.02): THREE.Material {
  return cached(name, () => sharedPane(key(name), { tint, rough, baseAlpha: 0.075, edge: 0.68, bumpn: 9 }))
}

export function emissive(name: string, hexcol: string, strength = 8): THREE.Material {
  return cached(name, () => sharedEmissive(key(name), hexcol, { strength }))
}

/** A shade with a lamp burning inside it: dielectric surface + fresnel-graded
 * glow, brighter through the middle than at the rim. */
export function lampshade(name: string, hexcol = 'F4EADA', glow = 'FFD9A6', strength = 9, rough = 0.3): THREE.Material {
  return cached(name, () => {
    const facing = layerWeightFacing(0.5)
    const f0 = ((1.42 - 1) / (1.42 + 1)) ** 2
    const fresnel = add(f0, mul(1 - f0, pow(facing, 5)))
    const g = srgbTriple(glow)
    const shadeCol = ramp(fresnel, [
      [0, [...g] as [number, number, number]],
      [0.85, g.map((c) => c * 0.3) as [number, number, number]],
    ])
    const m = principled({ color: hexcol, rough, coat: 0.25, emis: mul(shadeCol, strength) })
    m.userData.noShadow = true
    return m
  })
}

export function flat(name: string, hexcol: string, rough = 0.6): THREE.Material {
  return cached(name, () => principled({ color: hexcol, rough }))
}

// =================================================================== TEXTILES

// The pomegranate palmette (cx, cy, rx, ry, rot, exponent), au pre-mirrored.
const DAMASK_LOBES: [number, number, number, number, number, number][] = [
  [0, -0.115, 0.132, 0.23, 0, 1.3],
  [0, 0.15, 0.088, 0.092, 0, 1.55],
  [0.082, 0.262, 0.056, 0.108, -0.48, 1.28],
  [0, 0.348, 0.038, 0.08, 0, 1.2],
  [0.244, 0.035, 0.172, 0.048, 0.56, 1.24],
  [0.204, -0.238, 0.146, 0.043, -0.62, 1.24],
  [0.372, 0.205, 0.042, 0.068, 0.42, 1.3],
  [0, -0.398, 0.021, 0.108, 0, 1.7],
]

export interface DamaskOpts {
  ground?: string
  motif?: string
  sheenC?: string
  scale?: [number, number]
  rough?: number
  bump?: number
}

export function damask(name: string, o: DamaskOpts = {}): THREE.Material {
  return cached(name, () => {
    const { ground = '7A1418', motif = 'C08A34', sheenC = 'E0B15E', scale = [4.2, 3], rough = 0.58, bump = 0.22 } = o
    const v = triVec(scale)
    const { au, cv } = cellUv(v)
    let sil: N = lobe(au, cv, ...DAMASK_LOBES[0])
    for (let i = 1; i < DAMASK_LOBES.length; i++) sil = max(sil, lobe(au, cv, ...DAMASK_LOBES[i]))
    // the ogee lattice band the ornament sits in
    const og = sub(add(mul(cos(mul(cv, TAU)), 0.3), 0.335), au)
    sil = max(sil, sub(0.052, abs(og)))
    const burr = bnoise(v, 90, 4, 0.6)
    const pat = add(sil, sub(mul(burr, 0.055), 0.0275))
    const edge = rampF(pat, [
      [0, 0],
      [0.02, 1],
    ])
    const core = rampF(pat, [
      [0.115, 0],
      [0.15, 1],
    ])
    const band = clamp(sub(edge, core), 0, 1)
    const gd = srgbTriple(ground)
    let col: N = mix(srgb(ground), srgb(motif), edge)
    col = mix(col, vec3(...(gd.map((c) => c * 0.46) as [number, number, number])), band)
    const w = weave(v, 150, 1.35)
    const hgt = add(w, mul(edge, 0.35))
    const bmp = bumpNormal(hgt, bump, 0.02)
    const rr = mix(float(rough), float(rough - 0.16), edge)
    return principled({ base: col, roughN: rr, normal: bmp, sheen: 0.42, sheenTint: srgb(sheenC), spec: 0.32 })
  })
}

export function velvet(name: string, hexcol = 'C4642A', rough = 0.44, pile = 0.9): THREE.Material {
  return cached(name, () => {
    const base = srgbTriple(hexcol)
    const v = mapping(positionLocal, [9, 9, 9])
    const fib = bnoise(v, 60, 8, 0.72)
    const crush = bnoise(mapping(positionLocal, [7, 7, 7]), 3.2, 6, 0.6)
    const nap = pow(layerWeightFacing(0.34), 1.5)
    const lift = mul(nap, pile)
    const tone = add(add(lift, mul(crush, 0.16)), sub(mul(fib, 0.3), 0.15))
    const lo = base.map((c) => c * 0.6) as [number, number, number]
    const hi = base.map((c) => Math.min(1, c * 1.3 + 0.02)) as [number, number, number]
    const col = mix(vec3(...lo), vec3(...hi), clamp(tone, 0, 1))
    const rr = add(mul(fib, 0.16), rough - 0.08)
    const bmp = bumpNormal(fib, 0.32, 0.0035)
    return principled({ base: col, roughN: rr, normal: bmp, sheen: 0.85, sheenTint: vec3(...hi), spec: 0.24 })
  })
}

export interface TapestryOpts {
  ground?: string
  a?: string
  b?: string
  c?: string
  scale?: number
}

export function tapestry(name: string, o: TapestryOpts = {}): THREE.Material {
  return cached(name, () => {
    const { ground = '24201A', a = 'B04A2E', b = '55663E', c = 'D8B45C', scale = 7 } = o
    const v = triVec([scale, scale])
    const dn = mul(floor(mul(v, 30)), 1 / 30)
    const vor = voronoi(dn, 2.6)
    const warp = bnoise(dn, 4, 4, 0.55)
    const bloom = ramp(
      clamp(vor.distance, 0, 1),
      [
        [0, srgbTriple(c)],
        [0.1, srgbTriple(a)],
        [0.2, srgbTriple(b)],
        [0.3, srgbTriple(ground)],
      ],
      'CONSTANT',
    )
    const tint = ramp(
      lum(vor.color),
      [
        [0.3, srgbTriple(a)],
        [0.55, srgbTriple(c)],
        [0.8, srgbTriple(b)],
      ],
      'CONSTANT',
    )
    const heart = rampF(
      clamp(vor.distance, 0, 1),
      [
        [0.16, 1],
        [0.18, 0],
      ],
      'CONSTANT',
    )
    const col = mix(bloom, tint, heart)
    const leaf = rampF(
      warp,
      [
        [0.44, 0],
        [0.5, 1],
      ],
      'CONSTANT',
    )
    const lm = mul(leaf, sub(1, heart))
    const col2 = mix(col, srgb(b), lm)
    const col3 = mix(col2, srgb(ground), warp)
    const w = weave(v, 15, 1)
    const bmp = bumpNormal(w, 0.55, 0.012)
    return principled({ base: col3, roughN: float(0.78), normal: bmp, sheen: 0.3, sheenTint: srgb(c), spec: 0.2 })
  })
}

export interface PersianOpts {
  ground?: string
  border?: string
  motif?: string
  accent?: string
  dark?: string
  scale?: number
  wd?: [number, number]
  phase?: number
}

// the rosette worked on a 150 mm cell right across the field
const PERSIAN_PETALS: [number, number, number, number, number, number][] = [
  [0, 0, 0.19, 0.19, 0, 1.15],
  [0, 0.3, 0.082, 0.14, 0, 1.1],
  [0, -0.3, 0.082, 0.14, 0, 1.1],
  [0.32, 0, 0.14, 0.082, 0, 1.1],
  [0.245, 0.245, 0.078, 0.078, 0.79, 1.2],
  [0.245, -0.245, 0.078, 0.078, -0.79, 1.2],
]

export function persian(name: string, o: PersianOpts = {}): THREE.Material {
  return cached(name, () => {
    const {
      ground = '82291B',
      border = '1D2C46',
      motif = 'CFBC94',
      accent = '2C4A36',
      dark = '2A100C',
      scale = 1,
      wd = [1, 1],
      phase = 0,
    } = o
    const mp = mapping(positionLocal, [2 / wd[0], 2 / wd[1], 1])
    const au = abs(mp.x)
    const av = abs(mp.y)
    const d = max(au, av)
    const orn = vec3(au, av, 0)
    const vor = voronoi2(orn, 24)
    const pal = rampF(clamp(vor, 0, 1), [
      [0, 1],
      [0.07, 0],
    ])
    const ab = bnoise(orn, 3.2, 4, 0.5)

    const cellsz = 0.15
    const fv = mapping(positionLocal, [1 / cellsz, 1 / cellsz, 1 / cellsz], [0, 0, 0], [phase, phase * 0.63, phase * 0.31])
    const cuv = cellUv(fv)
    let ros: N = lobe(cuv.au, cuv.cv, ...PERSIAN_PETALS[0])
    for (let i = 1; i < PERSIAN_PETALS.length; i++) ros = max(ros, lobe(cuv.au, cuv.cv, ...PERSIAN_PETALS[i]))
    const fcell = floor(fv)
    const frnd = cellRand(fcell, 11)
    const fcol = ramp(
      frnd,
      [
        [0, srgbTriple(motif)],
        [0.34, srgbTriple(border)],
        [0.62, srgbTriple(accent)],
        [0.84, srgbTriple(dark)],
      ],
      'CONSTANT',
    )
    const rin = rampF(ros, [
      [0, 0],
      [0.02, 1],
    ])
    const rcore = rampF(ros, [
      [0.16, 0],
      [0.2, 1],
    ])
    let f1: N = mix(srgb(ground), srgb(dark), rin)
    f1 = mix(f1, fcol, rcore)
    const gTri = srgbTriple(ground)
    const field = mix(f1, vec3(...(gTri.map((c) => c * 0.76) as [number, number, number])), ab)

    const ell = sqrt(add(mul(mul(mp.x, 2.9), mul(mp.x, 2.9)), mul(mul(mp.y, 1.75), mul(mp.y, 1.75))))
    const ang = atan(mp.y, mp.x)
    const notch = add(mul(cos(mul(ang, 8)), 0.055), 0.6)
    const med = sub(notch, ell)
    const medr = rampF(med, [
      [0, 0],
      [0.02, 1],
    ])
    const medc = mix(srgb(border), srgb(motif), pal)
    const body = mix(field, medc, medr)

    const g1 = rampF(
      d,
      [
        [0.848, 0],
        [0.858, 1],
      ],
      'CONSTANT',
    )
    const g2 = rampF(
      d,
      [
        [0.952, 0],
        [0.962, 1],
      ],
      'CONSTANT',
    )
    const bandB = sub(g1, g2)
    const bcol = mix(srgb(border), srgb(motif), pal)
    const withb = mix(body, bcol, bandB)
    let edge: N = mix(withb, srgb(dark), g2)

    const pv = mapping(positionLocal, [scale, scale, scale])
    const fine = bnoise(pv, 260, 6, 0.7)
    const knot = bnoise(pv, 95, 3, 0.5)
    edge = overlayMix(edge, vec3(0, 0, 0), knot)
    const bmp = bumpNormal(fine, 0.55, 0.01)
    const rr = mix(float(0.92), float(0.8), fine)
    return principled({ base: edge, roughN: rr, normal: bmp, sheen: 0.22, sheenTint: srgb(motif), spec: 0.16 })
  })
}

export function leather(name: string, hexcol = '7E7360', rough = 0.46): THREE.Material {
  return cached(name, () => {
    const base = srgbTriple(hexcol)
    const v = mapping(positionLocal, [8, 8, 8])
    const cellEdge = voronoiEdge(v, 30)
    const fine = bnoise(v, 180, 6, 0.7)
    const crease = bnoise(mapping(positionLocal, [14, 14, 14]), 4, 7, 0.72, 1.1)
    const grain = rampF(cellEdge, [
      [0, 0],
      [0.12, 1],
    ])
    const cr = rampF(crease, [
      [0.4, 0],
      [0.52, 1],
    ])
    const hgt = mul(add(mul(grain, 0.7), mul(fine, 0.3)), sub(1, cr))
    const lo = base.map((c) => c * 0.9) as [number, number, number]
    const hi = base.map((c) => Math.min(1, c * 1.09 + 0.01)) as [number, number, number]
    const col = mix(vec3(...lo), vec3(...hi), grain)
    const col2 = mix(col, vec3(...lo), cr)
    const bmp = bumpNormal(hgt, 0.52, 0.01)
    const rr = mix(float(rough + 0.16), float(rough - 0.1), grain)
    return principled({ base: col2, roughN: rr, normal: bmp, sheen: 0.22, sheenTint: vec3(...hi), spec: 0.4 })
  })
}

// ===================================================================== METALS

export interface MetalOpts {
  rough?: number
  patina?: string
  tarnish?: number
  scale?: number
  aniso?: number
}

export function metal(name: string, hexcol = 'B8892E', o: MetalOpts = {}): THREE.Material {
  return cached(name, () => {
    const { rough = 0.28, patina = '2E3A28', tarnish = 0.45, scale = 6, aniso = 0 } = o
    const v = mapping(positionLocal, [scale, scale, scale])
    const broad = bnoise(v, 2.2, 5, 0.6)
    const fine = bnoise(v, 40, 6, 0.75)
    // pointiness has no raster analogue; a mid-surface constant stands in
    const dirt = mul(broad, 0.32)
    const dm = clamp(mul(dirt, tarnish * 1.8), 0, 1)
    const col = mix(srgb(hexcol), srgb(patina), dm)
    const rr = add(mul(fine, 0.22), rough)
    const rr2 = mix(rr, float(0.85), dm)
    const bmp = bumpNormal(fine, 0.1, 0.003)
    return principled({ base: col, roughN: rr2, metal: 1, normal: bmp, aniso })
  })
}

export function chrome(name: string, rough = 0.06, tint = 'E8ECEF'): THREE.Material {
  return metal(name, tint, { rough, patina: '6A6E72', tarnish: 0.18, scale: 10 })
}

// ================================================================== SIGNAGE

export function chalkboard(name: string, hexcol = '1E2B24', dust = 0.5): THREE.Material {
  return cached(name, () => {
    const v = mapping(positionLocal, [1.4, 1.4, 1.4])
    const smear = bnoise(mapping(v, [1, 9, 1]), 3, 6, 0.62, 0.8)
    const grit = bnoise(v, 120, 6, 0.7)
    const sm = rampF(smear, [
      [0.42, 0],
      [0.72, 1],
    ])
    const d = mul(sm, dust)
    const col = mix(srgb(hexcol), srgb('9CA79E'), d)
    const bmp = bumpNormal(grit, 0.16, 0.002)
    const rr = mix(float(0.72), float(0.86), d)
    return principled({ base: col, roughN: rr, normal: bmp, spec: 0.3 })
  })
}

/** Lit neon tube: bright straight through, brighter along the rim.  The rim
 * rides Blender's LayerWeight FRESNEL output (blend 0.28 -> eta 1/0.72,
 * schlick like the lampshade), and the 12% glass / 88% emission shader mix
 * folds into a dimmed dielectric under the scaled emission. */
export function neon(name: string, hexcol = 'FF2D55', strength = 26, glassCol = '1A1418'): THREE.Material {
  return cached(name, () => {
    const f0 = ((1 / 0.72 - 1) / (1 / 0.72 + 1)) ** 2
    const fres = add(f0, mul(1 - f0, pow(layerWeightFacing(0.5), 5)))
    const rim = pow(fres, 1.6)
    const lift = add(mul(rim, strength * 0.9), strength)
    const g = srgbTriple(glassCol).map((c) => c * 0.12) as [number, number, number]
    const m = principled({ base: vec3(...g), rough: 0.08, spec: 0.06, emis: mul(mul(srgb(hexcol), lift), 0.88) })
    m.userData.noShadow = true
    return m
  })
}

export function imgMat(name: string, path: string, o: { emit?: number; alpha?: boolean; rough?: number } = {}): THREE.Material {
  return cached(name, () => {
    const image = new THREE.TextureLoader().load(path)
    image.colorSpace = THREE.SRGBColorSpace
    image.wrapS = THREE.ClampToEdgeWrapping
    image.wrapT = THREE.ClampToEdgeWrapping
    const tex = texture(image, uv())
    const m = principled({
      base: tex.rgb,
      rough: o.rough ?? 0.52,
      spec: 0.3,
      emis: o.emit ? mul(tex.rgb, o.emit) : undefined,
      alphaN: o.alpha ? tex.a : undefined,
      transparentBlend: o.alpha,
      doubleSide: true,
    })
    if (o.alpha) m.userData.noShadow = true
    return m
  })
}

export interface FabricOpts {
  rough?: number
  sheen?: number
  scale?: number
  aniso?: number
  bump?: number
  stripes?: [number, string][]
  pitch?: number
}

export function fabric(name: string, hexcol: string, o: FabricOpts = {}): THREE.Material {
  return cached(name, () => {
    const { rough = 0.76, sheen = 0.35, scale = 200, aniso = 1, bump = 0.3, stripes, pitch = 0.24 } = o
    const base = srgbTriple(hexcol)
    const v = positionLocal
    const w = weave(v, scale, aniso)
    const drift = bnoise(v, 4, 5, 0.6)
    let col: N = mix(
      vec3(...(base.map((c) => c * 0.86) as [number, number, number])),
      vec3(...(base.map((c) => Math.min(1, c * 1.12)) as [number, number, number])),
      drift,
    )
    if (stripes) {
      const fr = fract(v.z.div(pitch))
      const total = stripes.reduce((sum, s) => sum + s[0], 0)
      let acc = 0
      const stops: [number, [number, number, number]][] = []
      for (const [wdt, hx] of stripes) {
        stops.push([acc / total, srgbTriple(hx)])
        acc += wdt
      }
      col = mix(col, ramp(fr, stops, 'CONSTANT'), 0.8)
    }
    const bmp = bumpNormal(w, bump, 0.004)
    return principled({
      base: col,
      rough,
      normal: bmp,
      sheen,
      sheenTint: vec3(...(base.map((c) => Math.min(1, c * 1.4 + 0.08)) as [number, number, number])),
      spec: 0.22,
    })
  })
}

export function foliage(name: string, light = '4E7A3A', dark = '24401E', scale = 40): THREE.Material {
  return cached(name, () => {
    const v = mapping(positionLocal, [scale, scale, scale])
    const n1 = bnoise(v, 6, 6, 0.65)
    const n2 = bnoise(v, 34, 5, 0.6)
    const col = mix(srgb(dark), srgb(light), n1)
    const col2 = mix(col, srgb('7E9440'), n2)
    const bmp = bumpNormal(n2, 0.3, 0.006)
    return principled({ base: col2, rough: 0.42, normal: bmp, coat: 0.3 })
  })
}

export function petal(name: string, hexcol = 'E2621F', rough = 0.55): THREE.Material {
  return cached(name, () => {
    const base = srgbTriple(hexcol)
    const v = mapping(positionLocal, [30, 30, 30])
    const n = bnoise(v, 14, 5, 0.6)
    const col = mix(
      vec3(...(base.map((c) => c * 0.7) as [number, number, number])),
      vec3(...(base.map((c) => Math.min(1, c * 1.3 + 0.04)) as [number, number, number])),
      n,
    )
    return principled({ base: col, rough, translucent: 0.35 })
  })
}

export { srgb, srgbTriple }
export type { N }
