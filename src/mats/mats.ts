/** mats - fully procedural materials, ported node graph by node graph from
 * build_scripts/mats.py into TSL MeshPhysicalNodeMaterial.  No image files,
 * no external assets.
 */
import * as THREE from 'three/webgpu'
import {
  add,
  attribute,
  clamp,
  cos,
  div,
  dot,
  atan,
  faceDirection,
  float,
  floor,
  fract,
  max,
  mix,
  mul,
  normalWorld,
  positionLocal,
  sqrt,
  sub,
  uniform,
  uv,
  vec3,
} from 'three/tsl'
import {
  type N,
  bnoise,
  bnoise3,
  brickTex,
  bumpNormal,
  layerWeightFacing,
  lum,
  mapping,
  ramp,
  rampF,
  srgb,
  srgbColor,
  srgbTriple,
  voronoi,
  wave,
} from './tsl'

// ------------------------------------------------------------------- registry

const CACHE = new Map<string, THREE.Material>()

export function get(name: string): THREE.Material | undefined {
  return CACHE.get(name)
}

function keep<T extends THREE.Material>(name: string, m: T): T {
  m.name = name
  CACHE.set(name, m)
  return m
}

function cached(name: string, make: () => THREE.Material): THREE.Material {
  const c = CACHE.get(name)
  if (c) return c
  return keep(name, make())
}

// -------------------------------------------------- translucency backlight
// Thin-surface translucency (blinds, foliage, lampshade slats).  EEVEE gives
// these a real translucent BSDF; the closest steady-state stand-in is the sun
// seen through the surface from behind, plus a whisper of sky.
export const backlight = {
  dirToSun: uniform(new THREE.Vector3(0, 0, 1)),
  sunColor: uniform(new THREE.Color(0, 0, 0)),
  skyAmb: uniform(new THREE.Color(0, 0, 0)),
}

function translucentEmission(base: N, factor: number): N {
  const nf = mul(normalWorld, faceDirection)
  const through = max(0, dot(mul(nf, -1), backlight.dirToSun))
  const light = add(mul(vec3(backlight.sunColor), through), vec3(backlight.skyAmb))
  return mul(mul(base, light), factor)
}

// ------------------------------------------------------------- principled

export interface PrincipledOpts {
  base?: N
  color?: string | [number, number, number]
  rough?: number
  roughN?: N
  metal?: number
  normal?: N | null
  spec?: number
  ior?: number
  sheen?: number
  sheenTint?: N
  coat?: number
  emis?: N
  emisStrength?: number
  aniso?: number
  translucent?: number
  alphaN?: N
  transparentBlend?: boolean
  alphaTest?: boolean
  doubleSide?: boolean
}

export function principled(o: PrincipledOpts): THREE.MeshPhysicalNodeMaterial {
  const m = new THREE.MeshPhysicalNodeMaterial()
  // Blender shades every mesh double-sided (no backface culling); keep that.
  m.side = THREE.DoubleSide
  const baseNode: N = o.base ?? (o.color !== undefined ? srgb(o.color) : vec3(0.8, 0.8, 0.8))
  m.colorNode = baseNode
  if (o.roughN) m.roughnessNode = o.roughN
  else m.roughness = o.rough ?? 0.45
  m.metalness = o.metal ?? 0
  if (o.normal) m.normalNode = o.normal
  // Blender 'Specular IOR Level' 0.5 is neutral; three specularIntensity 1 is
  // the same neutral F0, so the mapping is 2x.
  m.specularIntensity = Math.min(2, (o.spec ?? 0.5) * 2)
  m.ior = o.ior ?? 1.45
  if (o.sheen) {
    m.sheen = 1
    m.sheenNode = mul(o.sheenTint ?? baseNode, Math.min(1, o.sheen))
    m.sheenRoughness = 0.35
  }
  if (o.coat) {
    m.clearcoat = o.coat
    m.clearcoatRoughness = 0.06
  }
  if (o.emis !== undefined) {
    m.emissiveNode = o.emis
  }
  if (o.translucent) {
    const e = translucentEmission(baseNode, o.translucent)
    m.emissiveNode = o.emis !== undefined ? add(o.emis, e) : e
    m.side = THREE.DoubleSide
  }
  if (o.aniso) {
    m.anisotropy = o.aniso
  }
  if (o.alphaN) {
    m.opacityNode = o.alphaN
    if (o.alphaTest) {
      m.alphaTest = 0.5
    } else if (o.transparentBlend) {
      m.transparent = true
      m.depthWrite = false
    }
  }
  if (o.doubleSide) m.side = THREE.DoubleSide
  return m
}

/** Vector that runs along a vertical surface: u = horizontal arc-length in the
 * wall plane, v = z.  Port of mats.wall_proj (object coords + true normal). */
function wallProj(): N {
  const p = positionLocal
  const n = normalWorld
  const lenN = sqrt(add(mul(n.x, n.x), mul(n.y, n.y)))
  const safe = max(lenN, 0.06)
  const d = sub(mul(p.x, n.y), mul(p.y, n.x))
  return vec3(div(d, safe), p.z, 0)
}

// ================================================================== WOOD

export interface WoodOpts {
  ring?: number
  warp?: number
  rough?: [number, number]
  coord?: 'Object' | 'UV'
  axis?: 'X' | 'Y' | 'Z' | 'XY' | 'XZ' | 'YZ' | 'D'
  bump?: number
  pore?: number
  tintAttr?: string
  sheen?: number
  scale?: number
  aniso?: number
  distort?: number
  blotch?: number
  warpScale?: number
  translucent?: number
  grainRelief?: number
}

export function wood(name: string, cols: [string, string, string], o: WoodOpts = {}): THREE.Material {
  return cached(name, () => {
    const {
      ring = 26.0,
      rough = [0.28, 0.52],
      coord = 'Object',
      axis = 'X',
      bump = 0.16,
      pore = 1.0,
      tintAttr,
      sheen = 0.0,
      scale = 1.0,
      aniso = 0.35,
      blotch = 0.16,
      warpScale = 1.6,
      translucent = 0.0,
      grainRelief = 0.16,
    } = o
    let { warp = 0.55, distort = 1.6 } = o
    const ROT: Record<string, [number, number, number]> = {
      X: [0, 0, 0],
      Y: [0, 0, Math.PI / 2],
      Z: [0, Math.PI / 2, 0],
      XY: [0, 0, -Math.PI / 4],
      XZ: [0, Math.PI / 4, 0],
      YZ: [0, Math.PI / 2, -Math.PI / 4],
      D: [0, 0, (32 * Math.PI) / 180],
    }
    const rot = ROT[axis] ?? ([0, 0, 0] as [number, number, number])
    const src: N = coord === 'UV' ? vec3(uv(), 0) : positionLocal
    const mp = mapping(src, [scale, scale, scale], rot)
    // hold total axis shove against the ring period (see mats.py)
    const amp = Math.abs(warp) * 1.33 + Math.abs(distort) * 0.055
    const k = amp > 1e-9 ? Math.min(1.0, 0.55 / Math.max(ring, 1e-6) / amp) : 1.0
    warp *= k
    distort *= k
    // compress the palette towards its own mean past 34% luminance spread
    let cl = cols.map((c) => srgbTriple(c))
    const lums = cl.map((c) => 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
    const hi = Math.max(...lums)
    const lo = Math.min(...lums)
    if (hi > 1e-6 && (hi - lo) / hi > 0.34) {
      const t = (0.34 * hi) / (hi - lo)
      const md = [0, 1, 2].map((i) => (cl[0][i] + cl[1][i] + cl[2][i]) / 3)
      cl = cl.map((c) => [0, 1, 2].map((i) => md[i] + (c[i] - md[i]) * t) as [number, number, number])
    }
    const wn = bnoise(mp, warpScale, 3.0, 0.6)
    const w1 = add(mul(wn, warp), -0.5 * warp)
    const wn2 = bnoise(mp, warpScale * 4.3, 3.0, 0.55)
    const w2 = add(mul(wn2, warp * 0.33), -0.5 * warp * 0.33)
    const wn3 = bnoise(mp, 0.42, 2.0, 0.5)
    const w3 = add(mul(wn3, distort * 0.055), -0.5 * distort * 0.055)
    const wsc = add(add(w1, w2), w3)
    const warped = add(mp.x, wsc)
    const dn = bnoise(mp, 0.55, 2.0, 0.5)
    const dj = add(mul(dn, ring * 0.72), -0.36 * ring)
    const rr = add(mul(warped, ring), dj)
    const grain = fract(rr)
    const rampCol = ramp(grain, [
      [0.0, cl[0]],
      [0.34, cl[0]],
      [0.74, cl[1]],
      [0.97, cl[2]],
      [1.0, cl[2]],
    ])
    const mean = [0, 1, 2].map((i) => (cl[0][i] + cl[1][i] + cl[2][i]) / 3) as [number, number, number]
    const soft = mix(rampCol, vec3(...mean), 0.3)
    const gn = bnoise(mp, 1.35, 3.0, 0.55)
    const gm = rampF(gn, [
      [0.24, 0.34],
      [0.78, 1.0],
    ])
    const faded = mix(vec3(...mean), soft, gm)
    const blot = bnoise(mp, 0.9, 4.0, 0.65)
    const bl = rampF(blot, [
      [0.32, 0.0],
      [0.72, 1.0],
    ])
    const blf = mul(bl, blotch)
    const colMul = mul(faded, vec3(0.6, 0.5, 0.36))
    const col2 = mix(faded, colMul, blf)
    // pores ride on (warped*6, y, z) so ring count cannot compound into them
    const pcmb = vec3(mul(warped, 6.0), mp.y, mp.z)
    const pn = bnoise(pcmb, 42.0 * pore, 6.0, 0.72)
    const fine = bnoise(mp, 220.0, 4.0, 0.5)
    const gh = rampF(grain, [
      [0.0, 0.55],
      [0.34, 0.62],
      [0.8, 0.16],
      [1.0, 0.55],
    ])
    const gw = mul(gh, grainRelief)
    const hmix = add(gw, pn)
    const h2 = mul(hmix, 0.5)
    const h3 = add(h2, fine)
    const bmp = bumpNormal(h3, bump, 0.4)
    const rn = rampF(pn, [
      [0.25, rough[0]],
      [0.85, rough[1]],
    ])
    let baseSrc: N = col2
    if (tintAttr) {
      const at = attribute(tintAttr, 'vec3')
      baseSrc = mix(col2, mul(col2, at), 0.85)
    }
    return principled({
      base: baseSrc,
      roughN: rn,
      normal: bmp,
      spec: 0.5,
      sheen,
      aniso: coord === 'UV' ? aniso : 0,
      translucent,
    })
  })
}

// ================================================================== PAINT

export function paint(
  name: string,
  hexcol: string,
  o: { rough?: number; sheen?: number; coat?: number; bump?: number; noise?: number; variation?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { rough = 0.36, sheen = 0.0, coat = 0.0, bump = 0.02, noise = 140.0, variation = 0.03 } = o
    const p = positionLocal
    const n1 = bnoise(p, noise, 3.0, 0.5)
    const n2 = bnoise(p, 2.4, 4.0, 0.6)
    const base = srgbTriple(hexcol)
    const dark = base.map((c) => c * (1 - variation)) as [number, number, number]
    const lite = base.map((c) => Math.min(1, c * (1 + variation))) as [number, number, number]
    const col = mix(vec3(...dark), vec3(...lite), n2)
    const rn = rampF(n1, [
      [0.3, rough * 0.86],
      [0.8, rough * 1.14],
    ])
    const bmp = bumpNormal(n1, bump, 0.3)
    return principled({ base: col, roughN: rn, normal: bmp, sheen, coat })
  })
}

export function plaster(
  name: string,
  hexcol: string,
  o: { rough?: number; bump?: number; scale?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { rough = 0.72, bump = 0.28, scale = 26.0 } = o
    const p = positionLocal
    const n1 = bnoise(p, scale, 8.0, 0.62)
    const n2 = bnoise(p, 1.1, 5.0, 0.55)
    const base = srgbTriple(hexcol)
    const d = base.map((c) => c * 0.93) as [number, number, number]
    const l = base.map((c) => Math.min(1, c * 1.05)) as [number, number, number]
    const col = mix(vec3(...d), vec3(...l), n2)
    const n3 = bnoise(p, 420.0, 3.0, 0.5)
    const hh = add(n1, n3)
    const bmp = bumpNormal(hh, bump, 0.16)
    const rn = rampF(n1, [
      [0.2, rough - 0.08],
      [0.9, rough + 0.08],
    ])
    return principled({ base: col, roughN: rn, normal: bmp, spec: 0.35 })
  })
}

// ================================================================== BRICK

export function brickWall(
  name = 'brick_kitchen',
  cols: { c1?: string; c2?: string; mortar?: string } = {},
): THREE.Material {
  return cached(name, () => {
    const { c1 = 'AA6046', c2 = '90452F', mortar = 'B6AC9A' } = cols
    const mp = wallProj()
    const br = brickTex(mp, {
      offset: 0.5,
      offsetFreq: 2,
      squash: 1.0,
      squashFreq: 2,
      scale: 1.0,
      mortarSize: 0.0115,
      mortarSmooth: 0.22,
      bias: 0.0,
      brickWidth: 0.207,
      rowHeight: 0.0705,
    })
    const brColor = mix(mix(srgb(c1), srgb(c2), br.tint), srgb(mortar), br.fac)
    // per-brick colour jitter driven off a noise over the same projection
    const jn = bnoise(mp, 9.0, 2.0, 0.5)
    const tone = ramp(
      jn,
      [
        [0.18, srgb('8E5238')],
        [0.45, srgb('B06A4C')],
        [0.68, srgb('C08A6A')],
        [0.86, srgb('9B5A45')],
      ],
      'B_SPLINE',
    )
    const brk = mix(brColor, tone, 0.62)
    const grit = bnoise(mp, 190.0, 6.0, 0.7)
    const fine = bnoise(mp, 760.0, 3.0, 0.5)
    const gcol = mix(brk, mul(brk, vec3(0.35, 0.3, 0.28)), mul(grit, 0.16))
    const mortarMask = rampF(br.fac, [
      [0.15, 0.0],
      [0.65, 1.0],
    ])
    const mcol = mix(gcol, srgb('BDB4A2'), mortarMask)
    const hb = sub(1.0, mortarMask)
    const hg = mul(grit, 0.22)
    const hf = mul(fine, 0.1)
    const h2 = add(add(hb, hg), hf)
    const bmp = bumpNormal(h2, 0.75, 0.035)
    const rn = rampF(grit, [
      [0.2, 0.62],
      [0.9, 0.88],
    ])
    const rn2 = mix(rn, float(0.95), mortarMask)
    return principled({ base: mcol, roughN: rn2, normal: bmp, spec: 0.3 })
  })
}

export function subwayTile(
  name = 'tile_white',
  o: { size?: number; hexcol?: string; grout?: string; stack?: boolean; rough?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { size = 0.107, hexcol = 'F2F0EA', grout = 'C9C4B6', stack = false, rough = 0.13 } = o
    const mp = wallProj()
    const br = brickTex(mp, {
      offset: stack ? 0.0 : 0.5,
      squash: 1.0,
      scale: 1.0 / size,
      mortarSize: 0.022,
      mortarSmooth: 0.1,
      brickWidth: 1.0,
      rowHeight: 1.0,
    })
    const brColor = mix(srgb(hexcol), srgb(grout), br.fac)
    const jn = bnoise(mp, 1.0 / (size * 1.02), 1.0, 0.5)
    const tint = ramp(jn, [
      [0.3, [0.93, 0.94, 0.93]],
      [0.7, [1.0, 1.0, 0.99]],
    ])
    const col = mix(brColor, mul(brColor, tint), 0.7)
    const grt = rampF(br.fac, [
      [0.1, 0.0],
      [0.55, 1.0],
    ])
    const gn = bnoise(mp, 280.0, 4.0, 0.5)
    const h = sub(1.0, grt)
    const h2 = mul(gn, 0.16)
    const h3 = add(h, h2)
    const bmp = bumpNormal(h3, 0.6, 0.012)
    const rn = mix(float(rough), float(0.68), grt)
    const col2 = mix(col, srgb(grout), grt)
    return principled({ base: col2, roughN: rn, normal: bmp, spec: 0.6, coat: 0.35 })
  })
}

// ================================================================== METAL

export function metal(
  name: string,
  hexcol: string,
  o: { rough?: number; aniso?: number; bump?: number; scale?: number; brush?: [number, number, number] } = {},
): THREE.Material {
  return cached(name, () => {
    const { rough = 0.28, bump = 0.03, scale = 140.0, brush } = o
    const mp = mapping(positionLocal, brush ?? [1, 1, 1])
    const n1 = bnoise(mp, scale, 5.0, 0.6)
    const n2 = bnoise(mp, 6.0, 4.0, 0.5)
    const rn = rampF(n1, [
      [0.2, rough * 0.7],
      [0.85, Math.min(1, rough * 1.4)],
    ])
    const base = srgbTriple(hexcol)
    const dark = base.map((c) => c * 0.9) as [number, number, number]
    const col = mix(vec3(...dark), vec3(...base), n2)
    const bmp = bumpNormal(n1, bump, 0.06)
    return principled({ base: col, roughN: rn, metal: 1.0, normal: bmp })
  })
}

/** Woven cane for the kitchen pendant (see mats.py wicker docstring). */
export function wicker(
  name: string,
  o: {
    light?: string
    dark?: string
    rings?: number
    stakes?: number
    rough?: number
    bump?: number
    centre?: [number, number]
  } = {},
): THREE.Material {
  return cached(name, () => {
    const { light = 'D8B478', dark = '9C7238', rings = 34.0, stakes = 30.0, rough = 0.62, bump = 0.85, centre = [0, 0] } = o
    const p = positionLocal
    const dx = sub(p.x, centre[0])
    const dy = sub(p.y, centre[1])
    const th = atan(dy, dx)
    const u = mul(th, stakes / (Math.PI * 2))
    const v = mul(p.z, rings)
    const triOf = (s: N): N => {
      const w = fract(s)
      const t = sub(mul(w, 2.0), 1.0)
      return sub(1.0, t.abs())
    }
    const triU = triOf(u)
    const triV = triOf(v)
    const par = fract(add(floor(u), floor(v)).mul(0.5)).mul(2.0) // 0 even, 1 odd
    const hgt = mix(triU, triV, par)
    const col = mix(srgb(dark), srgb(light), hgt)
    const bmp = bumpNormal(hgt, bump, 0.01)
    const rn = rampF(hgt, [
      [0.0, rough * 1.25],
      [1.0, rough * 0.8],
    ])
    return principled({ base: col, roughN: rn, normal: bmp, sheen: 0.25, doubleSide: true })
  })
}

export function gingham(
  name = 'fabric_check_quilt',
  o: {
    band?: number
    light?: string
    dark?: string
    rough?: number
    sheen?: number
    weave?: number
    bump?: number
  } = {},
): THREE.Material {
  return cached(name, () => {
    const { band = 0.015, light = 'EFE7D2', dark = '8E1F2A', rough = 0.82, sheen = 0.6, weave = 700.0, bump = 0.2 } = o
    const p = positionLocal
    const f = 0.5 / band
    const u = add(p.x, p.y)
    const stripeOf = (s: N): N =>
      rampF(fract(mul(s, f)), [
        [0.47, 1.0],
        [0.5, 0.0],
      ])
    const s1 = stripeOf(u)
    const s2 = stripeOf(p.z)
    const half = mul(add(s1, s2), 0.5)
    const lc = srgbTriple(light)
    const dc = srgbTriple(dark)
    const mid = [0, 1, 2].map((i) => lc[i] * 0.42 + dc[i] * 0.58) as [number, number, number]
    const br = ramp(half, [
      [0.0, lc],
      [0.5, mid],
      [1.0, dc],
    ])
    const wv = wave(p, { type: 'BANDS', profile: 'TRI', scale: weave })
    const bmp = bumpNormal(wv, bump, 0.005)
    return principled({ base: br, rough, normal: bmp, sheen, spec: 0.25, sheenTint: br })
  })
}

/** Punched sheet - the colander (rides on the baked surfq attribute). */
export function perforated(
  name: string,
  o: {
    hexcol?: string
    rough?: number
    around?: number
    rows?: number
    hole?: number
    bump?: number
    attr?: string
    vmin?: number
  } = {},
): THREE.Material {
  return cached(name, () => {
    const { hexcol = 'B9BEC2', rough = 0.26, around = 36, rows = 11, hole = 0.3, bump = 0.03, attr = 'surfq', vmin = 0.32 } = o
    const at = attribute(attr, 'vec3')
    const cs = sub(mul(at.x, 2.0), 1.0)
    const sn = sub(mul(at.y, 2.0), 1.0)
    const th = atan(sn, cs)
    const u = mul(th, around / (Math.PI * 2))
    const v = mul(at.z, rows)
    const rw = floor(v)
    const od = sub(rw, mul(floor(mul(rw, 0.5)), 2.0))
    const us = add(mul(od, 0.5), u)
    const wrapC = (s: N): N => sub(fract(s), 0.5)
    const du = wrapC(us)
    const dv = wrapC(v)
    const d = sqrt(add(mul(du, du), mul(dv, dv)))
    const hm = rampF(d, [
      [hole * 0.72, 0.0],
      [hole, 1.0],
    ])
    const solid = rampF(at.z, [
      [vmin - 0.05, 1.0],
      [vmin, 0.0],
    ])
    const a = mix(hm, float(1.0), solid)
    const n1 = bnoise(positionLocal, 90.0, 4.0, 0.5)
    const rn = rampF(n1, [
      [0.25, rough * 0.75],
      [0.85, Math.min(1, rough * 1.3)],
    ])
    const bmp = bumpNormal(a, bump, 0.004)
    return principled({
      color: hexcol,
      roughN: rn,
      metal: 1.0,
      normal: bmp,
      alphaN: a,
      alphaTest: true,
      doubleSide: true,
    })
  })
}

/** Architectural glazing: alpha-blended with a Fresnel-weighted reflection. */
export function pane(
  name: string,
  o: { tint?: string; rough?: number; baseAlpha?: number; edge?: number; bumpn?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { tint = 'EDF2F0', rough = 0.025, baseAlpha = 0.055, edge = 0.6, bumpn = 0.0 } = o
    const facing = layerWeightFacing(0.13)
    const a = add(mul(facing, edge), baseAlpha)
    let nrm: N | null = null
    if (bumpn) {
      const nz = bnoise(positionLocal, bumpn, 4.0, 0.5)
      nrm = bumpNormal(nz, 0.25, 0.004)
    }
    const m = principled({
      color: tint,
      rough,
      spec: 0.65,
      normal: nrm,
      alphaN: clamp(a, 0, 1),
      transparentBlend: true,
      doubleSide: true,
    })
    m.userData.noShadow = true
    return m
  })
}

export function emissive(
  name: string,
  hexcol: string,
  o: { strength?: number; rough?: number; base?: string } = {},
): THREE.Material {
  return cached(name, () => {
    const { strength = 6.0, rough = 0.6, base } = o
    return principled({
      color: base ?? hexcol,
      rough,
      emis: mul(srgb(hexcol), strength),
    })
  })
}

// ================================================================== FABRIC

export function fabric(
  name: string,
  hexcol: string,
  o: { rough?: number; sheen?: number; weave?: number; bump?: number; blotch?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { rough = 0.72, sheen = 0.22, weave = 520.0, bump = 0.3, blotch = 0.06 } = o
    const p = positionLocal
    const wv = wave(p, { type: 'BANDS', dir: 'X', profile: 'TRI', scale: weave, distortion: 0.6 })
    const wv2 = wave(p, { type: 'BANDS', dir: 'Y', profile: 'TRI', scale: weave, distortion: 0.6 })
    const wsum = mul(wv, wv2)
    const n2 = bnoise(p, 2.6, 5.0, 0.6)
    const base = srgbTriple(hexcol)
    const d = base.map((c) => c * (1 - blotch)) as [number, number, number]
    const l = base.map((c) => Math.min(1, c * (1 + blotch))) as [number, number, number]
    const col = mix(vec3(...d), vec3(...l), n2)
    const fz = bnoise(p, 900.0, 3.0, 0.5)
    const hh = add(wsum, fz)
    const bmp = bumpNormal(hh, bump, 0.008)
    const rn = rampF(wsum, [
      [0.1, rough + 0.1],
      [0.9, rough - 0.1],
    ])
    const st = base.map((c) => c * 0.9) as [number, number, number]
    return principled({ base: col, roughN: rn, normal: bmp, sheen, spec: 0.28, sheenTint: vec3(...st) })
  })
}

/** Tone-on-tone jacquard: warped wave lattice + voronoi blossoms. */
export function damask(
  name: string,
  o: { base?: string; motif?: string; scale?: number; rough?: number; sheen?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { base = 'E6DEC8', motif = 'D8CDB2', scale = 2.6, rough = 0.74, sheen = 0.24 } = o
    const mp = mapping(positionLocal, [scale, scale, scale])
    const warpN = bnoise3(mp, 3.2, 4.0, 0.55)
    const wv = add(mul(warpN, vec3(0.22, 0.22, 0.22)), mp)
    const vor = voronoi(wv, 3.4, 0.85, 3.5)
    const lat = wave(wv, { type: 'RINGS', dir: 'SPHERICAL', profile: 'SIN', scale: 3.2, distortion: 0.9, detail: 2 })
    const mixm = mul(vor.distance, lat)
    const pat = rampF(
      mixm,
      [
        [0.06, 0.0],
        [0.16, 1.0],
        [0.38, 1.0],
        [0.52, 0.0],
      ],
      'B_SPLINE',
    )
    const col = mix(srgb(base), srgb(motif), pat)
    const wvv = wave(mp, { type: 'BANDS', profile: 'TRI', scale: 900.0 })
    const hh = mul(pat, 0.7)
    const h2 = add(hh, wvv)
    const bmp = bumpNormal(h2, 0.03, 0.01)
    const rn = rampF(pat, [
      [0.0, rough],
      [1.0, rough - 0.02],
    ])
    const st = srgbTriple(base).map((c) => c * 0.85) as [number, number, number]
    return principled({ base: col, roughN: rn, normal: bmp, sheen, spec: 0.3, sheenTint: vec3(...st) })
  })
}

export function velvet(name: string, hexcol: string, o: { rough?: number; sheen?: number } = {}): THREE.Material {
  return cached(name, () => {
    const { rough = 0.5, sheen = 1.0 } = o
    const p = positionLocal
    const n = bnoise(p, 680.0, 4.0, 0.7)
    const n2 = bnoise(p, 3.0, 5.0, 0.5)
    const base = srgbTriple(hexcol)
    const d = base.map((c) => c * 0.7) as [number, number, number]
    const l = base.map((c) => Math.min(1, c * 1.25)) as [number, number, number]
    const col = mix(vec3(...d), vec3(...l), n2)
    const rim = rampF(layerWeightFacing(0.28), [
      [0.15, 0.0],
      [0.95, 1.0],
    ])
    const bright = base.map((c) => Math.min(1, c * 1.9 + 0.03)) as [number, number, number]
    const col2 = mix(col, vec3(...bright), rim)
    const bmp = bumpNormal(n, 0.16, 0.006)
    const st = base.map((c) => Math.min(1, c * 1.6)) as [number, number, number]
    return principled({ base: col2, rough, normal: bmp, sheen, spec: 0.2, sheenTint: vec3(...st) })
  })
}

// ================================================================== SPECIALS

/** Cabbage-rose chintz: clustered voronoi blossoms + leaf sprigs. */
export function floralChintz(
  name: string,
  o: {
    ground?: string
    petal?: string
    petal2?: string
    leaf?: string
    leaf2?: string
    scale?: number
    rough?: number
    ground2?: string
  } = {},
): THREE.Material {
  return cached(name, () => {
    const {
      ground = 'F2B915',
      petal = 'D8266A',
      petal2 = 'F2789F',
      leaf = '2C6B3F',
      leaf2 = '7FA85A',
      scale = 5.0,
      rough = 0.7,
      ground2,
    } = o
    const mp = mapping(positionLocal, [scale, scale, scale])
    const wn = bnoise3(mp, 2.0, 4.0, 0.55)
    const wv = add(mul(wn, vec3(0.07, 0.07, 0.07)), mp)
    const VSC = 2.1
    const vo = voronoi(wv, VSC, 1.0)
    const off = sub(wv, vo.position)
    const rlen = off.length()
    const dirn = off.normalize()
    const pv = voronoi(dirn, 2.4, 0.9)
    const R0 = 0.6 / VSC
    const rth = add(mul(pv.distance, -0.78 * R0), 1.24 * R0)
    const diff = sub(rth, rlen)
    const pmix = rampF(diff, [
      [0.0, 0.0],
      [0.012, 1.0],
    ])
    const petals = div(rlen, R0)
    // leaves: stretched cells
    const lstretch = mul(wv, vec3(1.0, 2.6, 1.0))
    const LSC = 3.4
    const lv = voronoi(lstretch, LSC, 1.0)
    const lmask = rampF(lv.distance, [
      [0.4 / LSC, 1.0],
      [0.49 / LSC, 0.0],
    ])
    const lcol = mix(srgb(leaf), srgb(leaf2), lum(lv.color))
    let gSrc: N = srgb(ground)
    if (ground2) {
      const gn = bnoise(mp, 1.3, 4.0, 0.5)
      gSrc = mix(srgb(ground), srgb(ground2), gn)
    }
    const pcol = ramp(petals, [
      [0.0, srgb(petal)],
      [0.22, srgb(petal2)],
      [0.48, srgb(petal)],
      [0.74, srgb(petal2)],
      [1.0, srgb(petal)],
    ])
    const c1 = mix(gSrc, lcol, lmask)
    const c2 = mix(c1, pcol, pmix)
    const wvv = wave(mp, { type: 'BANDS', profile: 'TRI', scale: 1400.0 })
    const bmp = bumpNormal(wvv, 0.14, 0.004)
    const st = srgbTriple(ground).map((c) => c * 0.85) as [number, number, number]
    return principled({ base: c2, rough, normal: bmp, sheen: 0.2, spec: 0.3, sheenTint: vec3(...st) })
  })
}

// ============================================================== BOTANICAL PLATE

export interface GeneratedBox {
  min: THREE.Vector3
  size: THREE.Vector3
}

/** A single pressed-flower plate for a picture frame.  Generated coords come
 * from the plate's own bounding box (set after placement via userData). */
export function botanical(
  name: string,
  o: {
    normal?: [number, number]
    seed?: number
    ground?: string
    stem?: string
    leafc?: [string, string]
    bloom?: [string, string]
    rough?: number
  } = {},
): THREE.Material {
  return cached(name, () => {
    const {
      normal = [-1, 0],
      ground = 'EFE8D2',
      stem = '5A6B3A',
      leafc = ['4C6B34', '7E9155'],
      bloom = ['C0728A', 'E2B0BC'],
      rough = 0.62,
    } = o
    const uMin = uniform(new THREE.Vector3(0, 0, 0))
    const uSize = uniform(new THREE.Vector3(1, 1, 1))
    const g = div(sub(positionLocal, vec3(uMin)), max(vec3(uSize), vec3(1e-6)))
    const uo: N = Math.abs(normal[0]) > 0.5 ? g.y : g.x
    const u = sub(uo, 0.5)
    const v = sub(g.z, 0.5)

    interface MaskCol {
      mask: N
      col: N
    }
    const masks: MaskCol[] = []

    // --- stem: a shallow parabola climbing the plate ------------------------
    const sq = mul(v, v)
    const bend = add(mul(sq, 0.42), -0.035)
    const sax = sub(u, bend).abs()
    const smask = rampF(sax, [
      [0.009, 1.0],
      [0.0125, 0.0],
    ])
    const vlo = rampF(v, [
      [-0.4, 0.0],
      [-0.36, 1.0],
    ])
    const vhi = rampF(v, [
      [0.24, 1.0],
      [0.28, 0.0],
    ])
    masks.push({ mask: mul(mul(smask, vlo), vhi), col: srgb(stem) })

    // --- leaves: alternate sides up the stem --------------------------------
    const LV: [number, number, number, number, number][] = [
      [-0.345, -1, 0.19, 0.068, -0.26],
      [-0.205, 1, 0.205, 0.074, 0.3],
      [-0.055, -1, 0.185, 0.066, -0.22],
      [0.075, 1, 0.15, 0.055, 0.28],
      [-0.275, 1, 0.135, 0.049, 0.5],
      [-0.125, -1, 0.128, 0.046, -0.52],
    ]
    LV.forEach(([vy, side, la, lb, ang], i) => {
      const cx = 0.42 * vy * vy - 0.035 + side * (la * 0.96)
      const dx = sub(u, cx)
      const dy = sub(v, vy)
      const ca = Math.cos(ang)
      const sa = Math.sin(ang)
      const rx = add(mul(dx, ca), mul(dy, sa))
      const ry = add(mul(dx, -sa), mul(dy, ca))
      const nx = div(rx, la)
      const ny = div(ry, lb)
      const s = add(nx.abs().pow(1.65), ny.abs().pow(1.65))
      const ay = ny.abs()
      const mk = rampF(s, [
        [0.97, 1.0],
        [1.03, 0.0],
      ])
      masks.push({ mask: mk, col: srgb(leafc[i % 2]) })
      const vn = rampF(ay, [
        [0.1, 1.0],
        [0.2, 0.0],
      ])
      masks.push({ mask: mul(vn, mk), col: srgb(leafc[(i + 1) % 2]) })
    })

    // --- blooms: rosettes at the crown --------------------------------------
    const BL: [number, number, number][] = [
      [0.045, 0.32, 0.105],
      [-0.105, 0.225, 0.08],
      [0.125, 0.17, 0.062],
    ]
    BL.forEach(([bx, by, R], i) => {
      const dx = sub(u, bx)
      const dy = sub(v, by)
      const ang = atan(dy, dx)
      const k = 5 + i
      const co = cos(mul(ang, k))
      const rth = add(mul(co, 0.26 * R), 0.8 * R)
      const rl = sqrt(add(mul(dx, dx), mul(dy, dy)))
      const d2 = sub(rth, rl)
      const mk = rampF(d2, [
        [0.0, 0.0],
        [0.006, 1.0],
      ])
      const rn = div(rl, R)
      const pc = ramp(rn, [
        [0.0, srgb(bloom[0])],
        [0.3, srgb(bloom[1])],
        [1.0, srgb(bloom[0])],
      ])
      masks.push({ mask: mk, col: pc })
    })

    // --- aged paper ground, then composite the specimen over it -------------
    const fox = bnoise(g, 9.0, 5.0, 0.7)
    const fx = ramp(fox, [
      [0.56, srgb(ground)],
      [0.78, srgb('DFD2AE')],
    ])
    let cur: N = fx
    for (const { mask, col } of masks) cur = mix(cur, col, mask)
    const m = principled({ base: cur, rough, spec: 0.28 })
    const gb: GeneratedBox = { min: uMin.value, size: uSize.value }
    m.userData.generatedBox = gb
    return m
  })
}

/** Living leaf: tone drift + fine mottle + translucency. */
export function foliage(
  name: string,
  o: { dark?: string; light?: string; translucent?: number; rough?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const { dark = '24501F', light = '5E8C3A', translucent = 0.38, rough = 0.44 } = o
    const p = positionLocal
    const n1 = bnoise(p, 7.0, 3.0, 0.5)
    const tone = ramp(n1, [
      [0.3, srgb(dark)],
      [0.72, srgb(light)],
    ])
    const n2 = bnoise(p, 90.0, 4.0, 0.6)
    const mot = ramp(n2, [
      [0.38, [0.86, 0.86, 0.86]],
      [0.66, [1.06, 1.06, 1.06]],
    ])
    const col = mul(tone, mot)
    const bmp = bumpNormal(n2, 0.12, 0.004)
    return principled({ base: col, rough, normal: bmp, spec: 0.42, coat: 0.18, translucent })
  })
}

export { srgb, srgbColor, srgbTriple }
export type { N }
