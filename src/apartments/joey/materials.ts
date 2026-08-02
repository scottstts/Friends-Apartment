/** Apartment 19 material library.
 *
 * Every cache key is apartment-prefixed so Joey's greige paint, honey parquet
 * and coated leather can never alias Monica's identically named Blender
 * datablocks. The node graphs preserve the causal bundles in mats.py: a
 * surface's colour, roughness and micro-normal come from the same field.
 */
import * as THREE from 'three/webgpu'
import { add, fract, max, mix, mul, positionLocal, sub, texture, uv, vec3 } from 'three/tsl'
import {
  emissive as sharedEmissive,
  fabric as sharedFabric,
  metal as sharedMetal,
  paint as sharedPaint,
  pane as sharedPane,
  plaster as sharedPlaster,
  principled,
  velvet as sharedVelvet,
  wood as sharedWood,
  type N,
} from '../../mats/mats'
import { bnoise, bumpNormal, layerWeightFacing, rampF, srgb, srgbTriple, wave } from '../../mats/tsl'

const mats = new Map<string, THREE.Material>()
const key = (name: string): string => `apt19:${name}`

function remember(name: string, material: THREE.Material): THREE.Material {
  mats.set(name, material)
  return material
}

function cached(name: string, build: () => THREE.Material): THREE.Material {
  const prior = mats.get(name)
  if (prior) return prior
  return remember(name, build())
}

export function get(name: string): THREE.Material {
  const material = mats.get(name)
  if (!material) throw new Error(`Apartment 19 material ${name} has not been built`)
  return material
}

export function shade(hex: string, scale: number): string {
  const h = hex.replace('#', '')
  const values = [0, 2, 4].map((i) => Math.max(0, Math.min(255, Math.floor(Number.parseInt(h.slice(i, i + 2), 16) * scale))))
  return values.map((v) => v.toString(16).padStart(2, '0')).join('').toUpperCase()
}

export function plaster(
  name: string,
  color = 'CFC3AE',
  options: { rough?: number; bump?: number; patch?: number; scale?: number } = {},
): THREE.Material {
  const scale = 26 * (options.scale ?? 1)
  return remember(name, sharedPlaster(key(name), color, { rough: options.rough ?? 0.86, bump: options.bump ?? 0.34, scale }))
}

export function ceilingPaint(name: string, color = 'E0DACD'): THREE.Material {
  return paint(name, color, { rough: 0.9, brush: 0.2, bump: 0.02 })
}

export function paint(
  name: string,
  color: string,
  options: { rough?: number; coat?: number; brush?: number; bump?: number; sheenLift?: number } = {},
): THREE.Material {
  return remember(
    name,
    sharedPaint(key(name), color, {
      rough: options.rough ?? 0.3,
      coat: options.coat ?? 0,
      bump: options.bump ?? 0.02,
      noise: 105 + (options.brush ?? 0.5) * 95,
      sheen: options.sheenLift ?? 0,
      variation: 0.018,
    }),
  )
}

export interface WoodOptions {
  ring?: number
  warp?: number
  rough?: [number, number]
  coord?: 'Object' | 'UV'
  axis?: 'X' | 'Y' | 'Z' | 'XY' | 'XZ' | 'YZ' | 'D'
  bump?: number
  pore?: number
  tintAttr?: string
  scale?: number
  aniso?: number
  distort?: number
  coat?: number
  grainRelief?: number
}

export function wood(name: string, colors: [string, string, string], options: WoodOptions = {}): THREE.Material {
  return remember(
    name,
    sharedWood(key(name), colors, {
      ring: options.ring,
      warp: options.warp,
      rough: options.rough,
      coord: options.coord,
      axis: options.axis,
      bump: options.bump,
      pore: options.pore,
      tintAttr: options.tintAttr,
      scale: options.scale,
      aniso: options.aniso,
      distort: options.distort,
      grainRelief: options.grainRelief,
    }),
  )
}

export function metal(
  name: string,
  color = 'C6C8CA',
  options: { rough?: number; aniso?: number; brush?: number; grime?: number; bump?: number } = {},
): THREE.Material {
  const brush = options.brush ?? 0
  return remember(
    name,
    sharedMetal(key(name), color, {
      rough: options.rough ?? 0.22,
      aniso: options.aniso ?? brush * 0.65,
      bump: options.bump ?? 0.03,
      scale: 120 + brush * 260,
      brush: brush > 0 ? [1, 1 + brush * 5, 1] : undefined,
    }),
  )
}

export function enamel(name: string, color = 'F2EDE2', options: { rough?: number; tint?: string } = {}): THREE.Material {
  return cached(name, () => principled({ color, rough: options.rough ?? 0.12, coat: 0.72, spec: 0.55 }))
}

export function fabric(
  name: string,
  color = '9A8F7A',
  options: { rough?: number; weave?: number; sheen?: number; bump?: number; fuzz?: number } = {},
): THREE.Material {
  return remember(
    name,
    sharedFabric(key(name), color, {
      rough: options.rough ?? 0.78,
      weave: options.weave ?? 340,
      sheen: options.sheen ?? 0.35,
      bump: options.bump ?? 0.4,
      blotch: 0.045,
    }),
  )
}

export function velvet(name: string, color = '0E4A44', options: { rough?: number; sheen?: number } = {}): THREE.Material {
  return remember(name, sharedVelvet(key(name), color, { rough: options.rough ?? 0.55, sheen: options.sheen ?? 0.9 }))
}

export function leather(
  name: string,
  color = '121214',
  options: { rough?: number; crease?: number; grain?: number; coat?: number; wear?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const p = positionLocal
    const crease = bnoise(p, 3.8, 5, 0.7)
    const grain = bnoise(p, 310, 4, 0.58)
    const base = srgbTriple(color)
    const worn = base.map((c) => Math.min(1, c * 1.18 + 0.012)) as [number, number, number]
    const wear = rampF(crease, [
      [0.3, 0],
      [0.78, options.wear ?? 0.12],
    ])
    const col = mix(vec3(...base), vec3(...worn), wear)
    const h = add(mul(crease, options.crease ?? 1), mul(grain, options.grain ?? 1))
    const normal = bumpNormal(h, 0.24, 0.0035)
    const rim = layerWeightFacing(0.18)
    const rough = mix(options.rough ?? 0.34, Math.min(0.72, (options.rough ?? 0.34) + 0.12), rim)
    return principled({ base: col, roughN: rough, normal, coat: options.coat ?? 0.35, sheen: 0.15, spec: 0.5 })
  })
}

function planar(plane: 'XY' | 'XZ' | 'YZ'): [N, N] {
  if (plane === 'XY') return [positionLocal.x, positionLocal.y]
  if (plane === 'YZ') return [positionLocal.y, positionLocal.z]
  return [positionLocal.x, positionLocal.z]
}

export function tile(
  name: string,
  color = 'EDE7DA',
  grout = 'B7AE9C',
  options: { size?: number; joint?: number; rough?: number; relief?: number; plane?: 'XY' | 'XZ' | 'YZ' } = {},
): THREE.Material {
  return cached(name, () => {
    const size = options.size ?? 0.152
    const joint = (options.joint ?? 0.01) / size
    const [a, b] = planar(options.plane ?? 'XZ')
    const ua = fract(a.div(size))
    const ub = fract(b.div(size))
    const edgeA = max(rampF(ua, [[0, 1], [joint, 0]]), rampF(ua, [[1 - joint, 0], [1, 1]]))
    const edgeB = max(rampF(ub, [[0, 1], [joint, 0]]), rampF(ub, [[1 - joint, 0], [1, 1]]))
    const joints = max(edgeA, edgeB)
    const mottled = bnoise(positionLocal, 1 / size, 3, 0.55)
    const colorNode = mix(mul(srgb(color), mix(0.94, 1.04, mottled)), srgb(grout), joints)
    const normal = bumpNormal(sub(1, joints), options.relief ?? 0.6, 0.006)
    return principled({ base: colorNode, roughN: mix(options.rough ?? 0.16, 0.72, joints), normal, coat: 0.35, spec: 0.55 })
  })
}

export function ceramic(name: string, color = 'E7EAE3', options: { rough?: number; pitch?: number; vary?: number } = {}): THREE.Material {
  return cached(name, () => {
    const pitch = options.pitch ?? 0.1088
    const n = bnoise(positionLocal, 1 / pitch, 3, 0.5)
    const base = mix(mul(srgb(color), 0.96), mul(srgb(color), 1.035), n)
    const normal = bumpNormal(bnoise(positionLocal, 260, 3, 0.5), 0.055, 0.002)
    return principled({ base, rough: options.rough ?? 0.08, normal, coat: 0.58, spec: 0.55 })
  })
}

export function clearGlass(name: string, tint = 'E9F1F2', options: { rough?: number; smear?: number } = {}): THREE.Material {
  return remember(name, sharedPane(key(name), { tint, rough: options.rough ?? 0.015, baseAlpha: 0.085, edge: 0.72, bumpn: options.smear ? 90 : 0 }))
}

export function emissive(name: string, color = 'FFF1D2', options: { strength?: number } = {}): THREE.Material {
  return remember(name, sharedEmissive(key(name), color, { strength: options.strength ?? 6, rough: 0.58 }))
}

export function plastic(
  name: string,
  color = 'E9E9E4',
  options: { rough?: number; coat?: number; bump?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const n = bnoise(positionLocal, 150, 3, 0.5)
    const normal = bumpNormal(n, options.bump ?? 0.06, 0.002)
    return principled({ color, rough: options.rough ?? 0.28, coat: options.coat ?? 0.25, normal, spec: 0.5 })
  })
}

export function rubber(name: string, color = '1A1A1C', options: { rough?: number } = {}): THREE.Material {
  return cached(name, () => principled({ color, rough: options.rough ?? 0.72, spec: 0.22 }))
}

export function stone(
  name: string,
  color = 'F1EEE6',
  options: { vein?: string; rough?: number; scale?: number; coat?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const scale = options.scale ?? 1
    const macro = bnoise(positionLocal, 1.8 * scale, 6, 0.64)
    const veins = wave(positionLocal, { type: 'BANDS', dir: 'X', profile: 'SIN', scale: 3.2 * scale, distortion: 5, detail: 4 })
    const veinMask = mul(rampF(veins, [[0.46, 0], [0.5, 1], [0.56, 0]]), rampF(macro, [[0.22, 0], [0.76, 1]]))
    const base = mix(srgb(color), srgb(options.vein ?? 'CBC2B0'), veinMask)
    const normal = bumpNormal(add(mul(veinMask, 0.55), bnoise(positionLocal, 190, 3, 0.5)), 0.12, 0.004)
    return principled({ base, rough: options.rough ?? 0.13, normal, coat: options.coat ?? 0.4, spec: 0.55 })
  })
}

export function carpet(
  name: string,
  color = 'DCD5C4',
  options: { rough?: number; pile?: number; scale?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const pile = options.pile ?? 1
    const n = bnoise(positionLocal, 330 * (options.scale ?? 1), 4, 0.7)
    const broad = bnoise(positionLocal, 4.2, 4, 0.6)
    const base = mix(mul(srgb(color), 0.88), mul(srgb(color), 1.08), broad)
    return principled({ base, rough: options.rough ?? 0.94, normal: bumpNormal(n, 0.32 * pile, 0.0035), sheen: 0.28, spec: 0.2 })
  })
}

export function paper(
  name: string,
  color = 'D8D2C4',
  options: { rough?: number; sheen?: number; gloss?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const tooth = bnoise(positionLocal, 520, 3, 0.5)
    return principled({ color, rough: options.rough ?? 0.58, normal: bumpNormal(tooth, 0.06, 0.0015), coat: options.gloss ?? 0, sheen: options.sheen ?? 0, spec: 0.45 })
  })
}

export function stripe(
  name: string,
  colors: readonly string[],
  options: { widths?: readonly number[]; scale?: number; rough?: number; weave?: number; bump?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const widths = options.widths ?? colors.map(() => 1)
    const total = widths.reduce((sum, value) => sum + value, 0)
    const u = fract(positionLocal.x.mul(options.scale ?? 8))
    let cursor = 0
    let colorNode: N = srgb(colors[0])
    for (let i = 0; i < colors.length; i++) {
      cursor += widths[i] / total
      colorNode = mix(colorNode, srgb(colors[i]), rampF(u, [[cursor - 0.006, 0], [cursor, 1]]))
    }
    const weave = wave(positionLocal, { type: 'BANDS', dir: 'X', profile: 'TRI', scale: options.weave ?? 360 })
    return principled({ base: colorNode, rough: options.rough ?? 0.76, normal: bumpNormal(weave, options.bump ?? 0.35, 0.004), sheen: 0.35, spec: 0.26 })
  })
}

export function diamond(
  name: string,
  color = 'C3AE85',
  options: { ink?: string; pitch?: number; rough?: number; weave?: number; bump?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const pitch = options.pitch ?? 0.115
    const u = positionLocal.x.add(positionLocal.z).div(pitch)
    const v = positionLocal.x.sub(positionLocal.z).div(pitch)
    const du = fract(u).sub(0.5).abs()
    const dv = fract(v).sub(0.5).abs()
    const lines = max(rampF(du, [[0.41, 0], [0.49, 1]]), rampF(dv, [[0.41, 0], [0.49, 1]]))
    const weave = bnoise(positionLocal, options.weave ?? 340, 3, 0.55)
    return principled({ base: mix(srgb(color), srgb(options.ink ?? '9C875C'), lines), rough: options.rough ?? 0.76, normal: bumpNormal(add(lines, weave), options.bump ?? 0.35, 0.004), sheen: 0.32, spec: 0.28 })
  })
}

export function picture(
  name: string,
  path: string,
  options: { rough?: number; gloss?: number; bump?: number } = {},
): THREE.Material {
  return cached(name, () => {
    const image = new THREE.TextureLoader().load(path)
    image.colorSpace = THREE.SRGBColorSpace
    image.wrapS = THREE.ClampToEdgeWrapping
    image.wrapT = THREE.ClampToEdgeWrapping
    const tooth = bnoise(positionLocal, 520, 3, 0.5)
    return principled({
      base: texture(image, uv()),
      rough: options.rough ?? 0.44,
      coat: options.gloss ?? 0.22,
      normal: bumpNormal(tooth, options.bump ?? 0.06, 0.0015),
      spec: 0.45,
    })
  })
}

export { srgb }
