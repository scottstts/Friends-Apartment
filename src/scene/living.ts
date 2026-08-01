/** Living room - port of build_scripts/f_living.py: slipcovered sofa and
 * armchair, slipper chair, velvet ottoman, coffee table, wrought-iron glass
 * table, Aubusson rug, waterfall credenza with the CRT and the Jouets poster,
 * window seat, drapes, lamps, plants. */
import * as THREE from 'three/webgpu'
import { abs, add, atan, clamp, cos, div, max, min, mix, mul, positionLocal, sin, sqrt, sub, texture, uv, vec3 } from 'three/tsl'
import * as L from '../lib/L'
import * as mlib from '../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../lib/mesh'
import { PyRandom } from '../lib/rng'
import * as mats from '../mats/mats'
import { principled } from '../mats/mats'
import { bnoise, bnoise3, bumpNormal, lum, ramp, rampF, srgb, voronoi } from '../mats/tsl'
import * as P from './props'
import type { MatSet } from './shell'
import type { World } from './world'

function rad(d: number): number {
  return (d * Math.PI) / 180
}

// ------------------------------------------------------------------ materials
export function mkMats(): MatSet {
  const M: MatSet = {}
  M.damask = mats.damask('fabric_damask_cream', { base: 'C3B795', motif: 'BEB290', scale: 2.4, rough: 0.8, sheen: 0.24 })
  M.cream = mats.fabric('fabric_cream_plain', 'C6BC9E', { rough: 0.82, sheen: 0.65, weave: 560, blotch: 0.05 })
  M.blush = mats.fabric('fabric_blush', 'D3AE9F', { rough: 0.84, sheen: 0.7, weave: 620 })
  M.velvet_g = mats.velvet('velvet_teal', '1B5240')
  M.throw = mats.floralChintz('chintz_throw', {
    ground: 'C6AC6A',
    petal: 'A8705E',
    petal2: 'D8BE8E',
    leaf: '6A6038',
    leaf2: '9C8A54',
    scale: 4.6,
    rough: 0.86,
    ground2: 'AE8C46',
  })
  M.drape = mats.floralChintz('chintz_drape', {
    ground: 'B8AE90',
    petal: '6B3543',
    petal2: '8E5750',
    leaf: '2E3A24',
    leaf2: '5A6438',
    scale: 4.4,
    rough: 0.86,
  })
  const LIM: [string, string, string] = ['997F55', '82683F', '65502F']
  const LK = { ring: 15.0, warp: 0.14, warpScale: 1.4, distort: 0.9, bump: 0.06, rough: [0.32, 0.52] as [number, number], grainRelief: 0.3 }
  M.limed = mats.wood('wood_limed_oak', LIM, { axis: 'YZ', ...LK })
  M.limed_y = mats.wood('wood_limed_oak_y', LIM, { axis: 'XZ', ...LK })
  M.limed_v = mats.wood('wood_limed_oak_v', LIM, { axis: 'XY', ...LK })
  const PIN: [string, string, string] = ['D3A76E', 'BC8B4E', '9A6C36']
  const PK = { ring: 17.0, warp: 0.2, warpScale: 1.3, distort: 1.6, bump: 0.07, rough: [0.3, 0.48] as [number, number] }
  M.pine = mats.wood('wood_pine_coffee', PIN, { axis: 'YZ', ...PK })
  M.pine_y = mats.wood('wood_pine_coffee_y', PIN, { axis: 'XZ', ...PK })
  M.pine_v = mats.wood('wood_pine_coffee_v', PIN, { axis: 'XY', ...PK })
  const WAL: [string, string, string] = ['987646', '806038', '5E4326']
  const WK = { ring: 13.0, warp: 0.19, warpScale: 2.4, distort: 1.1, blotch: 0.16, bump: 0.05, rough: [0.14, 0.26] as [number, number] }
  M.walnut = mats.wood('wood_walnut_fig', WAL, { axis: 'YZ', ...WK })
  M.walnut_v = mats.wood('wood_walnut_fig_v', WAL, { axis: 'XY', ...WK })
  M.honey = mats.wood('wood_honey_leg', ['A87C48', '7E5624', '4E3210'], {
    ring: 56.0,
    warp: 0.08,
    distort: 1.0,
    bump: 0.14,
    rough: [0.18, 0.32],
    axis: 'XY',
  })
  M.stool_tap = mats.floralChintz('chintz_stool', {
    ground: '7E4E44',
    petal: '9A6A5E',
    petal2: 'C09A82',
    leaf: '4E4436',
    leaf2: '7A6C4E',
    scale: 9.0,
    rough: 0.86,
  })
  M.bakelite = mats.paint('bakelite_dark', '2B211B', { rough: 0.22, coat: 0.5 })
  M.pewter = mats.metal('metal_pewter', '6E6A62', { rough: 0.46, bump: 0.28 })
  M.iron_pale = mats.paint('iron_pale', 'CFD2CC', { rough: 0.42, coat: 0.18, variation: 0.09 })
  M.brass = mats.get('metal_brass') ?? mats.metal('metal_brass', 'B08D3A')
  M.glass = mats.get('glass_clear') ?? mats.pane('glass_clear')
  M.crt = mats.paint('plastic_crt', '2A2724', { rough: 0.36, coat: 0.3 })
  M.crt_bez = mats.paint('plastic_crt_bez', '2E2723', { rough: 0.4, coat: 0.25 })
  M.screen = mats.paint('crt_screen', '15181C', { rough: 0.06, coat: 0.7 })
  M.shade = mats.fabric('shade_cream', 'E9DCBC', { rough: 0.72, sheen: 0.4, weave: 700 })
  M.leaf = mats.foliage('plant_leaf', { dark: '24501F', light: '5E8C3A' })
  M.terra = mats.paint('terracotta', 'A8613C', { rough: 0.62, variation: 0.05 })
  M.wicker = mats.wood('wicker_basket', ['D3B078', 'B08B4C', '80612C'], { ring: 900.0, warp: 0.03, bump: 0.5, rough: [0.5, 0.7] })
  M.rug = rugMat()
  M.poster = posterMat()
  M.pillow_r = mats.fabric('fabric_red_pillow', '9E2225', { rough: 0.78, sheen: 0.5 })
  M.pillow_y = mats.fabric('fabric_yellow_pillow', 'E0B426', { rough: 0.78, sheen: 0.5 })
  M.pillow_rust = mats.fabric('fabric_rust_pillow', 'B05A32', { rough: 0.8, sheen: 0.5 })
  M.gold = mats.fabric('fabric_champagne_pillow', 'C0AB7C', { rough: 0.74, sheen: 0.85, weave: 380, blotch: 0.09 })
  M.sage = mats.floralChintz('chintz_sage_pillow', {
    ground: 'CEC9B2',
    petal: '9AA882',
    petal2: 'B6BE9E',
    leaf: '5E6E4A',
    leaf2: '8C9A6E',
    scale: 6.0,
    rough: 0.84,
  })
  M.check = mats.gingham()
  return M
}

/** Aubusson rug: all drawing driven by the distance to the rug edge in the
 * rug's own object space (the rug mesh stays centred). */
function rugMat(name = 'rug_aubusson'): THREE.Material {
  const existing = mats.get(name)
  if (existing) return existing
  const [W, H] = L.RUG_WH
  const sp = positionLocal
  const ax = abs(sp.x)
  const ay = abs(sp.y)
  const dx = sub(W * 0.5, ax)
  const dy = sub(H * 0.5, ay)
  const d = min(dx, dy)
  const per = add(sp.x, sp.y)
  const sm = mul(sin(mul(per, 39.0)), 0.011)
  const sm2 = mul(sin(mul(per, 11.0)), 0.01)
  const lobes = add(sm, sm2)
  const jt = bnoise(sp, 7.0, 3.0, 0.5)
  const js = mul(sub(jt, 0.5), 0.022)
  const dmod = add(d, add(lobes, js))
  const navy = rampF(dmod, [
    [0.118, 0.0],
    [0.158, 1.0],
  ])
  const band = rampF(dmod, [
    [0.14, 0.0],
    [0.17, 1.0],
    [0.4, 1.0],
    [0.45, 0.0],
  ])
  const wn = bnoise3(sp, 2.2, 4.0, 0.55)
  const wv = add(mul(wn, vec3(0.14, 0.14, 0.14)), sp)
  const VSC = 6.4
  const vo = voronoi(wv, VSC, 1.0)
  const off = sub(wv, vo.position)
  const rl = off.length()
  const dn = off.normalize()
  const pv = voronoi(dn, 2.6, 0.9)
  const R0 = 0.52 / VSC
  const rth = add(mul(pv.distance, -0.8 * R0), 1.22 * R0)
  const fd = sub(rth, rl)
  const fl = rampF(fd, [
    [0.0, 0.0],
    [0.008, 1.0],
  ])
  const lfm = rampF(vo.distance, [
    [0.34, 1.0],
    [0.6, 0.0],
  ])
  const fcol = ramp(
    lum(vo.color),
    [
      [0.12, srgb('C4835A')],
      [0.34, srgb('93A078')],
      [0.55, srgb('C0A090')],
      [0.78, srgb('C6AC6A')],
    ],
    'CONSTANT',
  )
  const dm = bnoise(wv, 1.1, 3.0, 0.5)
  const scroll = rampF(dm, [
    [0.38, 0.0],
    [0.64, 1.0],
  ])
  let field = mix(srgb('D6CBA6'), srgb('CEC29D'), scroll)
  // central medallion and the line inside the garland
  const ex = div(sp.x, 1.0)
  const ey = div(sp.y, 1.45)
  const radx = sqrt(add(mul(ex, ex), mul(ey, ey)))
  const th = atan(ey, ex)
  const lobe = cos(mul(th, 8.0))
  const rm = add(mul(lobe, 0.15 * 0.62), 0.62)
  const md = sub(rm, radx)
  const mmask = rampF(md, [
    [0.0, 0.0],
    [0.02, 1.0],
  ])
  const ro = add(mul(lobe, 0.09 * 0.74), 0.74)
  const rabs = abs(sub(radx, ro))
  const oline = rampF(rabs, [
    [0.008, 1.0],
    [0.015, 0.0],
  ])
  const mband = rampF(rabs, [
    [0.03, 1.0],
    [0.075, 0.0],
  ])
  field = mix(field, srgb('C9C39A'), mmask)
  field = mix(field, srgb('9CAA84'), oline)
  const zone = clamp(max(band, mband), 0, 1)
  const lmask = clamp(mul(zone, lfm), 0, 1)
  const gmask = clamp(mul(zone, fl), 0, 1)
  const c0 = mix(field, srgb('9CAA84'), lmask)
  const c1 = mix(c0, fcol, gmask)
  const c2 = mix(srgb('141E2E'), c1, navy)
  const fz = bnoise(sp, 340.0, 4.0, 0.5)
  const hh = add(gmask, fz)
  const bmp = bumpNormal(hh, 0.45, 0.009)
  const m = principled({ base: c2, rough: 0.88, normal: bmp, sheen: 0.1, spec: 0.2 })
  m.name = name
  return m
}

let posterMaterial: THREE.Material | undefined

function posterMat(name = 'poster_jouets'): THREE.Material {
  if (posterMaterial) return posterMaterial
  const image = new THREE.TextureLoader().load('/poster.jpg')
  image.colorSpace = THREE.SRGBColorSpace
  image.wrapS = THREE.ClampToEdgeWrapping
  image.wrapT = THREE.ClampToEdgeWrapping
  image.minFilter = THREE.LinearMipmapLinearFilter
  image.magFilter = THREE.LinearFilter
  image.anisotropy = 8
  const m = principled({ base: texture(image, uv()), rough: 0.62, spec: 0.3 })
  m.name = name
  posterMaterial = m
  return m
}

// ---------------------------------------------------------------- upholstery
function walk(poly: Vec2[], step = 0.024): Vec2[] {
  const out: Vec2[] = []
  const n = poly.length
  for (let i = 0; i < n; i++) {
    const a = poly[i]
    const c = poly[(i + 1) % n]
    const d = Math.hypot(c[0] - a[0], c[1] - a[1])
    const k = Math.max(1, Math.round(d / step))
    for (let j = 0; j < k; j++) {
      const t = j / k
      out.push([a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t])
    }
  }
  return out
}

function skirt(poly0: Vec2[], ztop: number, zbot = 0.008, folds = 34, depth = 0.016): MeshData {
  const poly = walk(poly0)
  const n = poly.length
  const cx = poly.reduce((s, q) => s + q[0], 0) / n
  const cy = poly.reduce((s, q) => s + q[1], 0) / n
  const rings: Vec3[][] = []
  for (let i = 0; i <= n; i++) {
    const p = poly[i % n]
    const ph = (i / n) * folds * Math.PI * 2
    const amp = depth * (0.35 + 0.65 * (0.5 + 0.5 * Math.sin(ph)))
    const vx = p[0] - cx
    const vy = p[1] - cy
    const ll = Math.hypot(vx, vy) || 1.0
    rings.push([
      [p[0], p[1], ztop],
      [p[0] + (vx / ll) * amp * 0.5, p[1] + (vy / ll) * amp * 0.5, ztop - (ztop - zbot) * 0.55],
      [p[0] + (vx / ll) * amp, p[1] + (vy / ll) * amp, zbot],
    ])
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.006)
  mlib.smoothShade(ob, 55)
  return ob
}

function rollArm(aw: number, h: number, dep: number, r = 0.115): MeshData {
  const sec: Vec2[] = [
    [-dep * 0.5, 0.0],
    [dep * 0.5, 0.0],
    [dep * 0.5, h - r],
  ]
  for (let i = 1; i <= 16; i++) {
    const a = (Math.PI * i) / 16.0
    sec.push([dep * 0.5 * Math.cos(a), h - r + r * Math.sin(a) * 1.03])
  }
  sec.push([-dep * 0.5, h - r])
  const ob = mlib.prismXZ(sec, 0.0, aw)
  mlib.smoothShade(ob, 42)
  return ob
}

interface BodyGeom {
  x0: number
  x1: number
  y0: number
  y1: number
  seatZ: number
  armZ: number
  backZ: number
  aw: number
  backt: number
}

function upholBody(ln: number, dep: number, seatZ = 0.415, armZ = 0.63, backZ = 0.85, aw = 0.185, backt = 0.22): [MeshData[], BodyGeom] {
  const x0 = -dep / 2
  const x1 = dep / 2
  const y0 = -ln / 2
  const y1 = ln / 2
  const parts: MeshData[] = []
  const rings: Vec3[][] = (
    [
      [0.0, 0.0],
      [backZ - 0.215 - 0.1, 0.0],
      [backZ - 0.215 - 0.045, 0.012],
      [backZ - 0.215 - 0.012, 0.006],
      [backZ - 0.215, -0.03],
    ] as [number, number][]
  ).map(([dz, exx]) => [
    [x0 - exx, y0 - exx * 0.5, 0.215 + dz],
    [x0 + backt + exx, y0 - exx * 0.5, 0.215 + dz],
    [x0 + backt + exx, y1 + exx * 0.5, 0.215 + dz],
    [x0 - exx, y1 + exx * 0.5, 0.215 + dz],
  ] as Vec3[])
  const body = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(body, 42)
  parts.push(body)
  const deck = mlib.box(x0 + backt - 0.02, y0, 0.215, x1 - 0.03, y1, seatZ)
  mlib.bevel(deck, 0.014, 2)
  parts.push(deck)
  for (const yy of [y0, y1 - aw]) {
    const arm = rollArm(aw, armZ - 0.215, dep - 0.05, 0.105)
    mlib.translate(arm, [0.0, yy, 0.215])
    parts.push(arm)
  }
  const sk = skirt(
    [
      [x0, y0],
      [x1, y0],
      [x1, y1],
      [x0, y1],
    ],
    seatZ - 0.004,
    0.006,
    Math.max(20, Math.trunc(ln * 26)),
    0.034,
  )
  parts.push(sk)
  return [parts, { x0, x1, y0, y1, seatZ, armZ, backZ, aw, backt }]
}

const BACK_LEAN = rad(-6.0)

function backX(x0: number, backt: number, thick: number, h: number): number {
  return x0 + backt + thick * 0.5 * Math.cos(BACK_LEAN) + h * Math.abs(Math.sin(BACK_LEAN))
}

function sofa(w: World, cx: number, cy: number, M: MatSet, ln = 2.32, dep = 0.9): void {
  const [parts, g] = upholBody(ln, dep)
  const { x0, y0, y1, seatZ, backZ, aw, backt } = g
  const nseat = 3
  const inner = ln - 2 * aw
  const pitch = inner / nseat
  const seatTop = seatZ + 0.155
  for (let i = 0; i < nseat; i++) {
    const cw = pitch - 0.028
    const yy = y0 + aw + (i + 0.5) * pitch
    const cu = mlib.cushion(0.56, cw, 0.16, 0.105)
    mlib.translate(cu, [0.15, yy, seatZ])
    parts.push(cu)
    const bc = mlib.cushion(0.18, cw, 0.46, 0.115)
    mlib.rotY(bc, BACK_LEAN)
    mlib.translate(bc, [backX(x0, backt, 0.18, 0.46), yy, 0.5])
    parts.push(bc)
  }
  const ob = mlib.join(parts)
  mlib.translate(ob, [cx, cy, 0.0])
  w.add(ob, M.damask)
  w.box2(cx - dep / 2 - 0.05, cy - ln / 2 - 0.05, cx + dep / 2 + 0.05, cy + ln / 2 + 0.05)
  // chintz throw folded over the back rail at the near end
  const th = drapeOver(cx + x0 + backt * 0.5, cy - 0.52, backZ, 1.05, 0.62, 0.32, backt * 0.5 + 0.05)
  w.add(th, M.throw)
  // accent pillows: red at the near arm, rust in the middle, champagne far arm
  const corner = y1 - aw - 0.2
  const spec: [number, number, THREE.Material][] = [
    [-corner, 7.0, M.pillow_r],
    [0.15, 0.0, M.pillow_rust],
    [corner, -7.0, M.gold],
  ]
  for (const [dy, tilt, mm] of spec) {
    const pw = mlib.cushion(0.135, 0.37, 0.37, 0.095)
    mlib.rotY(pw, rad(-22))
    mlib.rotX(pw, rad(tilt))
    mlib.translate(pw, [cx + 0.19, cy + dy, seatTop - 0.014])
    w.add(pw, mm)
  }
}

function drapeOver(cx: number, cy: number, ztop: number, w0 = 1.2, front = 0.5, back = 0.3, t = 0.16): MeshData {
  const prof: Vec2[] = []
  const n = 10
  for (let i = n; i > 0; i--) {
    const tt = i / n
    prof.push([-t * 0.5 - 0.012 * Math.sin(tt * 3.0), ztop - back * tt])
  }
  for (let i = 0; i <= 10; i++) {
    const a = Math.PI * (1 - i / 10.0)
    prof.push([-t * 0.5 * Math.cos(a) * -1.0, ztop + 0.012 * Math.sin(a)])
  }
  for (let i = 1; i <= n; i++) {
    const tt = i / n
    prof.push([t * 0.5 + 0.016 * Math.sin(tt * 2.4), ztop - front * tt])
  }
  const rings: Vec3[][] = []
  for (let k = 0; k <= 10; k++) {
    const s = k / 10.0
    const yy = cy + (s - 0.5) * w0
    const wob = 1.0 + 0.14 * Math.sin(s * 8.0)
    rings.push(prof.map(([x, z]) => [cx + x * wob, yy, z] as Vec3))
  }
  const ob = mlib.loft(rings)
  mlib.solidify(ob, 0.008)
  mlib.smoothShade(ob, 52)
  return ob
}

function armchair(w: World, cx: number, cy: number, rot: number, M: MatSet, cw = 0.96, dep = 0.94): void {
  const [parts, g] = upholBody(cw, dep, 0.415, 0.63, 0.85, 0.175, 0.21)
  const { x0, seatZ, aw, backt } = g
  const cu = mlib.cushion(0.58, cw - 2 * aw - 0.02, 0.16, 0.05)
  mlib.translate(cu, [0.155, 0.0, seatZ])
  parts.push(cu)
  const bc = mlib.cushion(0.18, cw - 2 * aw - 0.02, 0.48, 0.055)
  mlib.rotY(bc, BACK_LEAN)
  mlib.translate(bc, [backX(x0, backt, 0.18, 0.48), 0.0, seatZ - 0.02])
  parts.push(bc)
  const ob = mlib.join(parts)
  mlib.rotateZ(ob, rot)
  mlib.translate(ob, [cx, cy, 0.0])
  w.add(ob, M.damask)
  w.obb(cx, cy, dep / 2 + 0.04, cw / 2 + 0.04, rot)
}

function slipperChair(w: World, cx: number, cy: number, rot: number, M: MatSet, cw = 0.63, dep = 0.72): void {
  const parts: MeshData[] = []
  const SEAT_T = 0.4
  const RAIL_Z = 0.235
  const pts = mlib.roundedRect(dep - 0.02, cw - 0.02, 0.045, 5)
  const railRings: Vec3[][] = (
    [
      [RAIL_Z, 0.955],
      [RAIL_Z + 0.02, 0.995],
      [SEAT_T - 0.02, 1.0],
      [SEAT_T, 0.985],
    ] as [number, number][]
  ).map(([zz, s]) => pts.map(([x, y]) => [x * s, y * s, zz] as Vec3))
  const rail = mlib.loft(railRings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(rail, 48)
  parts.push(rail)
  const cpts = mlib.roundedRect(dep - 0.03, cw - 0.028, 0.06, 6)
  const cushRings: Vec3[][] = (
    [
      [0.0, 0.94],
      [0.022, 1.0],
      [0.07, 1.02],
      [0.112, 1.0],
      [0.132, 0.93],
    ] as [number, number][]
  ).map(([dz, s]) => cpts.map(([x, y]) => [x * s, y * s, SEAT_T + dz] as Vec3))
  const cush = mlib.loft(cushRings, { closeV: true, capStart: true, capEnd: true })
  // Blender's bevel + smooth-by-angle keeps the broad top cap normal separate
  // from the rounded sides. The raw Three loft shares those vertices, causing
  // long cap triangles to interpolate side normals across the whole seat; one
  // triangle then faces almost completely away from the ceiling light and
  // reads as a black wedge at distance. Duplicate only the cap loop to create
  // the deliberate normal seam Blender produces without changing silhouette.
  const topCapIndex = cush.faces.length - 1
  cush.faces[topCapIndex] = cush.faces[topCapIndex].map((vi) => {
    cush.verts.push([...cush.verts[vi]] as Vec3)
    return cush.verts.length - 1
  })
  mlib.smoothShade(cush, 48)
  parts.push(cush)
  // back: a solid section swept across the width
  const x0 = -dep / 2 + 0.052
  const ztop = SEAT_T + 0.052
  const sec: Vec2[] = [
    [0.014, 0.0],
    [-0.004, 0.108],
    [-0.026, 0.222],
    [-0.042, 0.318],
    [-0.046, 0.384],
    [-0.034, 0.424],
    [-0.016, 0.446],
    [-0.042, 0.454],
    [-0.068, 0.444],
    [-0.084, 0.414],
    [-0.094, 0.358],
    [-0.1, 0.286],
    [-0.102, 0.188],
    [-0.098, 0.092],
    [-0.092, 0.0],
  ]
  const scx = sec.reduce((s, p) => s + p[0], 0) / sec.length
  const scz = sec.reduce((s, p) => s + p[1], 0) / sec.length
  const n = 30
  const backRings: Vec3[][] = []
  for (let i = 0; i <= n; i++) {
    const t = i / n
    const yy = (t - 0.5) * (cw - 0.03)
    const bow = 0.032 * (2.0 * Math.abs(t - 0.5)) ** 2.0
    const e = Math.max(0.0, Math.min(1.0, Math.min(t, 1.0 - t) / 0.055))
    const k = 0.62 + 0.38 * e ** 0.6
    backRings.push(sec.map(([dxx, dzz]) => [x0 + scx + (dxx - scx) * k + bow, yy, ztop + scz + (dzz - scz) * k] as Vec3))
  }
  const back = mlib.loft(backRings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(back, 50)
  parts.push(back)
  const ob = mlib.join(parts)
  mlib.rotateZ(ob, rot)
  mlib.translate(ob, [cx, cy, 0.0])
  w.add(ob, M.blush)
  w.obb(cx, cy, dep / 2 + 0.03, cw / 2 + 0.03, rot)
  // splayed blond dowel legs
  const legs: MeshData[] = []
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const lg = mlib.revolve(
      [
        [0.0, 0.0],
        [0.009, 0.004],
        [0.013, 0.055],
        [0.017, 0.13],
        [0.021, 0.205],
        [0.023, 0.238],
        [0.0, 0.244],
      ],
      14,
    )
    mlib.rotY(lg, -sx * rad(11))
    mlib.rotX(lg, sy * rad(11))
    mlib.translate(lg, [sx * (dep / 2 - 0.075), sy * (cw / 2 - 0.075), 0.0])
    legs.push(lg)
  }
  const lo = mlib.join(legs)
  mlib.smoothShade(lo, 40)
  mlib.rotateZ(lo, rot)
  mlib.translate(lo, [cx, cy, 0.0])
  w.add(lo, M.honey)
  // red and yellow scatter cushions, slumped against the back
  const spec: [number, THREE.Material, number, number][] = [
    [-0.128, M.pillow_r, -31.0, -9.0],
    [0.132, M.pillow_y, -22.0, 8.0],
  ]
  spec.forEach(([dy, mm, ry, rx], i) => {
    const pw = mlib.cushion(0.052, 0.31, 0.272, 0.086)
    mlib.rotY(pw, rad(ry))
    mlib.rotX(pw, rad(rx))
    mlib.translate(pw, [-dep / 2 + 0.196 + 0.012 * i, dy, SEAT_T + 0.108])
    mlib.rotateZ(pw, rot)
    mlib.translate(pw, [cx, cy, 0.0])
    w.add(pw, mm)
  })
}

function ottoman(w: World, cx: number, cy: number, rot: number, M: MatSet, cw = 0.56, dep = 0.4): void {
  const topZ = 0.345
  const pts = mlib.roundedRect(dep, cw, 0.085, 5)
  const rings: Vec3[][] = (
    [
      [0.0, 0.9],
      [0.018, 0.98],
      [0.075, 1.0],
      [0.13, 0.985],
      [0.16, 0.9],
      [0.175, 0.62],
    ] as [number, number][]
  ).map(([dz, s]) => pts.map(([x, y]) => [x * s, y * s, topZ - 0.175 + dz] as Vec3))
  const top = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(top, 50)
  mlib.rotateZ(top, rot)
  mlib.translate(top, [cx, cy, 0.0])
  w.add(top, M.velvet_g)
  w.obb(cx, cy, dep / 2 + 0.05, cw / 2 + 0.05, rot)
  const legs: MeshData[] = []
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const pts2 = mlib.bez([0.0, topZ - 0.155], [0.045, topZ - 0.235], [0.055, topZ - 0.3], [0.012, 0.019], 9)
    const path = pts2.map(([p, z]) => [sx * (dep / 2 - 0.075) + sx * p * 0.9, sy * (cw / 2 - 0.075) + sy * p * 0.9, z] as Vec3)
    legs.push(mlib.tubeAlong(path, mlib.circle(0.017, 9)))
    const pad = mlib.revolve(
      [
        [0.0, 0.0],
        [0.026, 0.006],
        [0.028, 0.018],
        [0.0, 0.026],
      ],
      12,
    )
    mlib.translate(pad, [path[path.length - 1][0], path[path.length - 1][1], 0.0])
    legs.push(pad)
  }
  const lo = mlib.join(legs)
  mlib.smoothShade(lo, 42)
  mlib.rotateZ(lo, rot)
  mlib.translate(lo, [cx, cy, 0.0])
  w.add(lo, M.honey)
}

// --------------------------------------------------------------------- tables
function credenzaFlowers(w: World, vx: number, vy: number, vz: number, M: MatSet, rng: PyRandom): void {
  const vase = mlib.revolve(
    [
      [0.0, 0.0],
      [0.05, 0.0],
      [0.058, 0.018],
      [0.074, 0.076],
      [0.07, 0.148],
      [0.048, 0.222],
      [0.039, 0.272],
      [0.046, 0.296],
      [0.041, 0.3],
      [0.034, 0.276],
      [0.034, 0.22],
      [0.0, 0.215],
    ],
    28,
  )
  mlib.smoothShade(vase, 34)
  mlib.translate(vase, [vx, vy, vz])
  w.add(vase, mats.paint('ceramic_teal', '5E7F6E', { rough: 0.22, coat: 0.55, variation: 0.09, noise: 34 }))
  const stems: MeshData[] = []
  const blooms: MeshData[] = []
  const leaves: MeshData[] = []
  for (let i = 0; i < 12; i++) {
    const a = rng.uniform(0, Math.PI * 2)
    const ln = rng.uniform(0.1, 0.26)
    const pts: Vec3[] = [[0.0, 0.0, 0.24]]
    for (let k = 1; k < 6; k++) {
      const t = k / 5.0
      pts.push([Math.cos(a) * 0.095 * t ** 1.5, Math.sin(a) * 0.095 * t ** 1.5, 0.3 + ln * t])
    }
    stems.push(mlib.tubeAlong(pts, mlib.circle(0.003, 5)))
    const rr = rng.uniform(0.85, 1.2)
    const hd = mlib.revolve(
      [
        [0.0, 0.0],
        [0.012 * rr, 0.004],
        [0.024 * rr, 0.014],
        [0.031 * rr, 0.03],
        [0.028 * rr, 0.044],
        [0.016 * rr, 0.053],
        [0.0, 0.055],
      ],
      18,
    )
    mlib.smoothShade(hd, 45)
    mlib.rotX(hd, rng.uniform(-0.35, 0.35))
    mlib.translate(hd, pts[pts.length - 1])
    blooms.push(hd)
    const lf = P.leafBlade(rng.uniform(0.08, 0.12), rng.uniform(0.02, 0.03), 5, 0.55, 0.42)
    mlib.rotateZ(lf, a + rng.uniform(-0.8, 0.8))
    mlib.rotX(lf, rng.uniform(-1.15, -0.55))
    mlib.translate(lf, pts[2])
    leaves.push(lf)
  }
  const groups: [MeshData[], THREE.Material][] = [
    [stems, M.leaf],
    [leaves, M.leaf],
    [blooms, mats.paint('bloom_cream', 'E8DEC0', { rough: 0.54, variation: 0.06 })],
  ]
  for (const [grp, mm] of groups) {
    const o = mlib.join(grp)
    mlib.smoothShade(o, 40)
    mlib.translate(o, [vx, vy, vz])
    w.add(o, mm)
  }
}

function coffeeTable(w: World, cx: number, cy: number, M: MatSet, cw = 0.88, d = 1.2, h = 0.435): void {
  const placed: [MeshData, THREE.Material][] = []
  const t = 0.055
  const fw = 0.085
  const top = mlib.panelWithHoles(cw, d, t, [
    [fw, fw, cw / 2 - 0.02, d - fw],
    [cw / 2 + 0.02, fw, cw - fw, d - fw],
  ])
  mlib.transform4(top, [
    [1, 0, 0, -cw / 2],
    [0, 0, 1, -d / 2],
    [0, 1, 0, h - t],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(top)
  placed.push([top, M.pine])
  for (const [a, bb] of [
    [fw, cw / 2 - 0.02],
    [cw / 2 + 0.02, cw - fw],
  ] as [number, number][]) {
    const pn = mlib.box(a - cw / 2 - 0.008, -d / 2 + fw - 0.008, h - 0.03, bb - cw / 2 + 0.008, d / 2 - fw + 0.008, h - 0.006)
    mlib.bevel(pn, 0.003, 2)
    placed.push([pn, M.pine])
  }
  const aprons: [number, number, number, number][] = [
    [-cw / 2 + 0.055, -d / 2, cw / 2 - 0.055, -d / 2 + 0.03],
    [-cw / 2 + 0.055, d / 2 - 0.03, cw / 2 - 0.055, d / 2],
    [-cw / 2, -d / 2 + 0.055, -cw / 2 + 0.03, d / 2 - 0.055],
    [cw / 2 - 0.03, -d / 2 + 0.055, cw / 2, d / 2 - 0.055],
  ]
  for (const [ax0, ay0, ax1, ay1] of aprons) {
    const ap = mlib.box(ax0, ay0, h - t - 0.075, ax1, ay1, h - t)
    mlib.bevel(ap, 0.004, 2)
    placed.push([ap, Math.abs(ax1 - ax0) > Math.abs(ay1 - ay0) ? M.pine : M.pine_y])
  }
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const lx = sx * (cw / 2 - 0.055)
    const ly = sy * (d / 2 - 0.055)
    const sec = mlib.roundedRect(0.088, 0.088, 0.008, 2)
    const rings: Vec3[][] = (
      [
        [0.0, 0.84],
        [0.02, 0.92],
        [0.045, 1.05],
        [0.07, 1.05],
        [0.095, 0.92],
        [0.115, 0.96],
        [0.135, 1.0],
        [h - t - 0.075, 1.0],
        [h - t, 1.0],
      ] as [number, number][]
    ).map(([zz, s]) => sec.map(([x, y]) => [x * s, y * s, zz] as Vec3))
    const lg = mlib.loft(rings, { closeU: false, closeV: true, capStart: true, capEnd: true })
    mlib.translate(lg, [lx, ly, 0.0])
    placed.push([lg, M.pine_v])
  }
  for (let i = 0; i < 5; i++) {
    const yy = -d / 2 + 0.115 + (i * (d - 0.23)) / 4.5
    const sl = mlib.box(-cw / 2 + 0.055, yy, 0.135, cw / 2 - 0.055, yy + (d - 0.23) / 5.6, 0.155)
    mlib.bevel(sl, 0.003, 2)
    placed.push([sl, M.pine])
  }
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [cx, cy, 0.0])
    w.add(ob, mm)
  }
  w.box2(cx - cw / 2, cy - d / 2, cx + cw / 2, cy + d / 2)
}

function glassTable(w: World, cx: number, cy: number, M: MatSet, cw = 0.6, d = 0.6, h = 0.575): void {
  const gt = mlib.prism(mlib.roundedRect(cw, d, 0.075, 6), h, h + 0.026)
  mlib.bevel(gt, 0.012, 3)
  const gm = mats.get('glass_thick') ?? mats.pane('glass_thick', { tint: 'C2DED0', rough: 0.02, baseAlpha: 0.34, edge: 0.9 })
  mlib.translate(gt, [cx, cy, 0.0])
  w.add(gt, gm)
  const ir = 0.011
  const ax = cw / 2 - 0.075
  const ay = d / 2 - 0.075
  const legs: MeshData[] = []
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const pts = mlib.bez([0.0, h - 0.055], [0.075, h - 0.24], [0.115, h - 0.4], [0.052, 0.022], 14)
    const path = pts.map(([p, z]) => [sx * (ax + p * 0.8), sy * (ay + p * 0.8), z] as Vec3)
    legs.push(mlib.tubeAlong(path, mlib.circle(ir, 9)))
    const [fx, fy] = [path[path.length - 1][0], path[path.length - 1][1]]
    const ux = sx / Math.SQRT2
    const uy = sy / Math.SQRT2
    const sc: Vec3[] = []
    for (let i = 0; i < 15; i++) {
      const t = i / 14.0
      const a = t * Math.PI * 1.75
      const rr = 0.046 * (1.0 - 0.62 * t)
      sc.push([fx + ux * rr * Math.sin(a) - ux * 0.046, fy + uy * rr * Math.sin(a) - uy * 0.046, 0.009 + rr * (1.0 - Math.cos(a)) * 0.3])
    }
    legs.push(mlib.tubeAlong(sc, mlib.circle(ir * 0.85, 8)))
  }
  const az = h - 0.055
  const ringPts = mlib.roundedRect(2 * ax, 2 * ay, 0.055, 5).map(([x, y]) => [x, y, az] as Vec3)
  legs.push(mlib.tubeAlong([...ringPts, ringPts[0]], mlib.circle(ir * 0.9, 8)))
  const volutes: [number, number, number, number][] = [
    [0.0, -ay, 1.0, 0.0],
    [0.0, ay, 1.0, 0.0],
    [-ax, 0.0, 0.0, 1.0],
    [ax, 0.0, 0.0, 1.0],
  ]
  for (const [mx, my, dxs, dys] of volutes) {
    for (const s of [-1, 1]) {
      const cs: Vec3[] = []
      for (let i = 0; i < 15; i++) {
        const t = i / 14.0
        const a = t * Math.PI * 1.4
        const rr = 0.023 * (1.0 - 0.45 * t)
        const u = s * (0.072 - rr * (1.0 - Math.cos(a)) * 1.15)
        const zz = az - 0.005 - rr * Math.sin(a) * 1.35
        cs.push([mx + dxs * u, my + dys * u, zz])
      }
      legs.push(mlib.tubeAlong(cs, mlib.circle(ir * 0.7, 7)))
    }
  }
  const lo = mlib.join(legs)
  mlib.smoothShade(lo, 40)
  mlib.translate(lo, [cx, cy, 0.0])
  w.add(lo, M.iron_pale)
  w.box2(cx - cw / 2, cy - d / 2, cx + cw / 2, cy + d / 2)
}

// ------------------------------------------------------------------- credenza
function credenza(w: World, M: MatSet): void {
  const x0 = 8.0
  const x1 = L.EX - 0.03
  const y0 = L.TV_C[1] - L.CRED_HW
  const y1 = L.TV_C[1] + L.CRED_HW
  const h = 0.9
  const ln = y1 - y0
  const placed: [MeshData, THREE.Material][] = []
  const pl = mlib.box(x0 + 0.02, y0 + 0.03, 0.0, x1, y1 - 0.03, 0.085)
  mlib.bevel(pl, 0.006, 2)
  placed.push([pl, M.walnut])
  placed.push([mlib.box(x0 + 0.045, y0, 0.085, x1, y1, h - 0.055), M.walnut])
  const sec: Vec2[] = [
    [x1, h - 0.055],
    [x1, h],
    [x0 + 0.1, h],
    [x0 + 0.055, h - 0.008],
    [x0 + 0.032, h - 0.026],
    [x0 + 0.026, h - 0.048],
    [x0 + 0.03, h - 0.055],
  ]
  const top = mlib.prismXZ(sec, y0 - 0.03, y1 + 0.03)
  mlib.smoothShade(top, 34)
  placed.push([top, M.walnut])
  const endw = 0.3
  const pilw = 0.075
  const cwid = ln - 2 * endw - 2 * pilw
  let yy = y0
  const fx = x0 + 0.03
  const kinds: [string, number][] = [
    ['door', endw],
    ['pil', pilw],
    ['drawers', cwid],
    ['pil', pilw],
    ['door', endw],
  ]
  for (const [kind, wid] of kinds) {
    if (kind === 'door') {
      const dr = mlib.box(fx - 0.024, yy + 0.008, 0.1, fx, yy + wid - 0.008, h - 0.07)
      mlib.bevel(dr, 0.004, 2)
      placed.push([dr, M.walnut_v])
      const pull = decoPull()
      mlib.translate(pull, [fx - 0.024, yy + wid * 0.5, 0.46])
      placed.push([pull, M.bakelite])
    } else if (kind === 'pil') {
      const rings: Vec3[][] = []
      for (let i = 0; i < 13; i++) {
        const a = (Math.PI * i) / 12.0
        const px = fx - 0.03 + 0.03 * Math.sin(a)
        const py = yy + wid * 0.5 - wid * 0.5 * Math.cos(a)
        rings.push([
          [px, py, 0.095],
          [px, py, h - 0.058],
        ])
      }
      const pilo = mlib.loft(rings)
      mlib.smoothShade(pilo, 40)
      placed.push([pilo, M.walnut_v])
    } else {
      for (let k = 0; k < 3; k++) {
        const dh = (h - 0.185) / 3
        const z = 0.105 + k * dh
        const dw = mlib.box(fx - 0.024, yy + 0.01, z + 0.006, fx, yy + wid - 0.01, z + dh - 0.006)
        mlib.bevel(dw, 0.004, 2)
        placed.push([dw, M.walnut])
        const pull = decoPull()
        mlib.translate(pull, [fx - 0.024, yy + wid * 0.5, z + dh * 0.5])
        placed.push([pull, M.bakelite])
      }
    }
    yy += wid
  }
  for (const [ob, mm] of placed) w.add(ob, mm)
  w.box2(x0 - 0.02, y0 - 0.04, x1, y1 + 0.04)
}

/** Elongated art-deco pull: a fan-shaped bar with a stepped centre. */
function decoPull(): MeshData {
  const sec: Vec2[] = [
    [0.0, -0.024],
    [0.01, -0.022],
    [0.016, -0.012],
    [0.018, 0.0],
    [0.016, 0.012],
    [0.01, 0.022],
    [0.0, 0.024],
  ]
  const rings: Vec3[][] = []
  for (let i = 0; i <= 10; i++) {
    const t = i / 10.0
    const s = 0.55 + 0.45 * Math.sin(Math.PI * t) ** 0.5
    rings.push(sec.map(([x, y]) => [-0.075 + 0.15 * t, y * s * 1.0, x * s] as Vec3))
  }
  const ob = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(ob, 40)
  mlib.rotateZ(ob, Math.PI / 2)
  return ob
}

function crtTv(w: World, cx: number, cy: number, cz: number, M: MatSet, cw = 0.6, d = 0.52, h = 0.5): void {
  const placed: [MeshData, THREE.Material][] = []
  const body = mlib.box(-d / 2, -cw / 2, 0.0, d / 2, cw / 2, h)
  mlib.bevel(body, 0.014, 3)
  placed.push([body, M.crt])
  const bez = mlib.panelWithHoles(cw - 0.04, h - 0.04, 0.03, [[0.048, 0.058, cw - 0.088, h - 0.082]])
  mlib.transform4(bez, [
    [0, 0, 1, -d / 2 - 0.028],
    [1, 0, 0, -cw / 2 + 0.02],
    [0, 1, 0, 0.02],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(bez)
  mlib.bevel(bez, 0.005, 2)
  placed.push([bez, M.crt_bez])
  for (const yy of [cw / 2 - 0.075, cw / 2 - 0.036]) {
    const kn = mlib.revolve(
      [
        [0.0, 0.0],
        [0.012, 0.003],
        [0.013, 0.01],
        [0.009, 0.016],
        [0.0, 0.018],
      ],
      14,
    )
    mlib.rotY(kn, -Math.PI / 2)
    mlib.smoothShade(kn, 40)
    mlib.translate(kn, [-d / 2 - 0.03, yy, 0.036])
    placed.push([kn, M.crt_bez])
  }
  const sw = cw - 0.19
  const sh = h - 0.23
  const pts = mlib.roundedRect(sw, sh, 0.055, 5)
  const scrRings: Vec3[][] = (
    [
      [0.0, 1.0],
      [-0.014, 0.94],
    ] as [number, number][]
  ).map(([dx, s]) => pts.map(([x, y]) => [-d / 2 - 0.01 + dx, x * s, h / 2 + y * s] as Vec3))
  const scr = mlib.loft(scrRings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(scr, 40)
  placed.push([scr, M.screen])
  for (let k = 0; k < 9; k++) {
    const zz = 0.1 + (k * (h - 0.2)) / 8
    placed.push([mlib.box(d / 2 - 0.004, -cw / 2 + 0.06, zz, d / 2 + 0.004, cw / 2 - 0.06, zz + 0.014), M.screen])
  }
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [cx, cy, cz])
    w.add(ob, mm)
  }
}

function speaker(w: World, cx: number, cy: number, M: MatSet, cw = 0.32, d = 0.4, h = 0.7): void {
  const placed: [MeshData, THREE.Material][] = []
  const veneer = mats.wood('wood_speaker', ['7A5028', '5A3418', '3A2008'], { ring: 44, warp: 0.05, bump: 0.28, axis: 'YZ' })
  const box = mlib.box(-d / 2, -cw / 2, 0.0, d / 2, cw / 2, h)
  mlib.bevel(box, 0.006, 2)
  placed.push([box, veneer])
  const baffle = mlib.box(-d / 2 - 0.01, -cw / 2 + 0.022, 0.026, -d / 2 + 0.004, cw / 2 - 0.022, h - 0.026)
  mlib.bevel(baffle, 0.003, 2)
  placed.push([baffle, M.bakelite])
  const surr = mats.paint('rubber_surround', '5E2018', { rough: 0.62 })
  const coneMat = mats.paint('driver_cone', '241E1A', { rough: 0.8 })
  for (const [zz, rr, hasSurround] of [
    [h * 0.34, 0.098, true],
    [h * 0.76, 0.036, false],
  ] as [number, number, boolean][]) {
    if (hasSurround) {
      const ring = mlib.revolve(
        [
          [rr * 0.62, 0.0],
          [rr, 0.012],
          [rr * 1.06, 0.026],
          [rr * 0.98, 0.034],
          [rr * 0.6, 0.02],
        ],
        26,
      )
      mlib.rotY(ring, -Math.PI / 2)
      mlib.translate(ring, [-d / 2 - 0.006, 0.0, zz])
      mlib.smoothShade(ring, 40)
      placed.push([ring, surr])
    }
    const scale = rr / 0.098
    const cone = mlib.revolve(
      [
        [0.0, -0.03 * scale],
        [rr * 0.28, -0.022 * scale],
        [rr * 0.62, 0.002],
        [rr * 0.7, 0.01],
      ],
      26,
    )
    mlib.rotY(cone, -Math.PI / 2)
    mlib.translate(cone, [-d / 2 - 0.006, 0.0, zz])
    mlib.smoothShade(cone, 40)
    placed.push([cone, coneMat])
    const cap = mlib.revolve(
      [
        [0.0, 0.0],
        [rr * 0.24, -0.004],
        [rr * 0.26, -0.018],
      ],
      20,
    )
    mlib.rotY(cap, -Math.PI / 2)
    mlib.translate(cap, [-d / 2 - 0.006 - 0.03 * scale, 0.0, zz])
    mlib.smoothShade(cap, 40)
    placed.push([cap, M.bakelite])
  }
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [cx, cy, 0.0])
    w.add(ob, mm)
  }
  w.box2(cx - d / 2, cy - cw / 2, cx + d / 2, cy + cw / 2)
}

// ------------------------------------------------------------------- the rug
function rug(w: World, M: MatSet): void {
  const [rw, d] = L.RUG_WH
  const [cx, cy] = L.RUG_C
  const pts: Vec2[] = []
  const n = 96
  for (let i = 0; i < n; i++) {
    const t = i / n
    let p: Vec2
    if (t < 0.25) {
      const u = t / 0.25
      p = [-rw / 2 + rw * u, -d / 2]
    } else if (t < 0.5) {
      const u = (t - 0.25) / 0.25
      p = [rw / 2, -d / 2 + d * u]
    } else if (t < 0.75) {
      const u = (t - 0.5) / 0.25
      p = [rw / 2 - rw * u, d / 2]
    } else {
      const u = (t - 0.75) / 0.25
      p = [-rw / 2, d / 2 - d * u]
    }
    const wob = 0.006 * Math.sin(t * 37.0)
    pts.push([p[0] * (1 + wob * 0.02) + wob, p[1] + wob])
  }
  const ob = mlib.prism(pts, 0.0008, 0.0128)
  mlib.bevel(ob, 0.003, 2)
  w.add(ob, M.rug, { at: [cx, cy, 0.0] })
}

// --------------------------------------------------------------- window seat
function windowSeat(w: World, M: MatSet): void {
  const x0 = L.BW_X[0] - 0.1
  const x1 = L.BW_X[1] + 0.1
  const y0 = L.AL_Y[1] - L.SEAT_D
  const y1 = L.AL_Y[1]
  const h = L.SEAT_H
  const placed: [MeshData, THREE.Material][] = []
  placed.push([mlib.box(x0, y0 + 0.05, 0.0, x1, y1, h - 0.055), M.limed])
  const kick = mlib.box(x0 + 0.02, y0, h - 0.055, x1 - 0.02, y1, h)
  mlib.bevel(kick, 0.006, 2)
  placed.push([kick, M.limed])
  for (let i = 0; i < 4; i++) {
    const pw = (x1 - x0 - 0.1) / 4
    const px = x0 + 0.05 + i * pw
    const pn = mlib.box(px + 0.03, y0 + 0.028, 0.075, px + pw - 0.03, y0 + 0.048, h - 0.085)
    mlib.bevel(pn, 0.004, 2)
    placed.push([pn, M.limed])
  }
  for (const [ob, mm] of placed) w.add(ob, mm)
  w.box2(x0, y0, x1, y1)
  const cu = mlib.cushion(x1 - x0 - 0.05, y1 - y0 - 0.05, 0.1, 0.055)
  mlib.translate(cu, [(x0 + x1) / 2, (y0 + y1) / 2, h])
  w.add(cu, M.cream)
  const rng = new PyRandom(6)
  for (let i = 0; i < 4; i++) {
    const px = x0 + 0.3 + (i * (x1 - x0 - 0.6)) / 3
    const pw = mlib.cushion(rng.uniform(0.34, 0.44), rng.uniform(0.34, 0.42), 0.13, 0.05)
    mlib.rotX(pw, rad(rng.uniform(62, 78)))
    mlib.rotateZ(pw, rng.uniform(-0.2, 0.2))
    mlib.translate(pw, [px, y1 - 0.2, h + 0.2])
    w.add(pw, [M.throw, M.drape, M.pillow_rust, M.damask][i % 4])
  }
}

function consoleTable(w: World, M: MatSet): void {
  const cx = (L.BW_X[0] + L.BW_X[1]) * 0.5
  const cy = L.AL_Y[1] - L.SEAT_D - 0.3
  const cw = 1.35
  const d = 0.42
  const h = 0.715
  const placed: [MeshData, THREE.Material][] = []
  const top = mlib.box(-cw / 2, -d / 2, h - 0.028, cw / 2, d / 2, h)
  mlib.bevel(top, 0.006, 3)
  placed.push([top, M.limed])
  const lip = mlib.box(-cw / 2 + 0.012, -d / 2 + 0.012, h - 0.046, cw / 2 - 0.012, d / 2 - 0.012, h - 0.028)
  mlib.bevel(lip, 0.004, 2)
  placed.push([lip, M.limed])
  const ix = cw / 2 - 0.058
  const iy = d / 2 - 0.04
  const railT = 0.026
  for (const [x0, y0, x1, y1] of [
    [-ix, iy - railT, ix, iy],
    [-ix, -iy, ix, -iy + railT],
    [-ix, -iy, -ix + railT, iy],
    [ix - railT, -iy, ix, iy],
  ] as [number, number, number, number][]) {
    const rail = mlib.box(x0, y0, h - 0.148, x1, y1, h - 0.046)
    mlib.bevel(rail, 0.003, 2)
    placed.push([rail, M.limed_y])
  }
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    const pts: Vec3[] = [
      [sx * (ix - railT * 0.5), sy * (iy - railT * 0.5), h - 0.046],
      [sx * (ix - 0.034), sy * (iy - 0.03), 0.0],
    ]
    placed.push([mlib.tubeAlong(pts, mlib.roundedRect(0.048, 0.044, 0.005, 2)), M.limed_v])
  }
  const sz0 = 0.188
  const sz1 = 0.214
  for (const sx of [-1, 1]) {
    const ends = [sx * (ix - 0.048), sx * (ix - 0.014)].sort((a, b) => a - b)
    const end = mlib.box(ends[0], -(iy - 0.026), sz0, ends[1], iy - 0.026, sz1)
    mlib.bevel(end, 0.003, 2)
    placed.push([end, M.limed_y])
  }
  const long = mlib.box(-(ix - 0.03), -0.017, sz0 + 0.002, ix - 0.03, 0.017, sz1 - 0.002)
  mlib.bevel(long, 0.003, 2)
  placed.push([long, M.limed])
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [cx, cy, 0.0])
    w.add(ob, mm)
  }
  w.box2(cx - cw / 2, cy - d / 2, cx + cw / 2, cy + d / 2)
}

/** Console, picture and sconce on the wall between Monica's door and the bay. */
function doorWall(w: World, M: MatSet): void {
  const cy = (L.MD_WALL[0] + L.MD_WALL[1]) * 0.5
  const cw = 0.78
  const d = 0.36
  const h = 0.725
  const cx = L.EX - d / 2 - 0.012
  const placed: [MeshData, THREE.Material][] = []
  const top = mlib.box(-d / 2, -cw / 2, h - 0.026, d / 2, cw / 2, h)
  mlib.bevel(top, 0.006, 3)
  placed.push([top, M.limed_y])
  const lip = mlib.box(-d / 2 + 0.01, -cw / 2 + 0.01, h - 0.04, d / 2 - 0.01, cw / 2 - 0.01, h - 0.026)
  mlib.bevel(lip, 0.004, 2)
  placed.push([lip, M.limed_y])
  const ix = d / 2 - 0.03
  const iy = cw / 2 - 0.03
  for (const [a, b] of [
    [[ix - 0.022, -iy], [ix, iy]],
    [[-ix, -iy], [-ix + 0.022, iy]],
    [[-ix, -iy], [ix, -iy + 0.022]],
    [[-ix, iy - 0.022], [ix, iy]],
  ] as [Vec2, Vec2][]) {
    const rail = mlib.box(a[0], a[1], h - 0.155, b[0], b[1], h - 0.04)
    mlib.bevel(rail, 0.003, 2)
    placed.push([rail, M.limed_y])
  }
  for (const [sx, sy] of [
    [-1, -1],
    [1, -1],
    [-1, 1],
    [1, 1],
  ] as [number, number][]) {
    placed.push([
      mlib.tubeAlong(
        [
          [sx * (ix - 0.022), sy * (iy - 0.022), h - 0.04],
          [sx * (ix - 0.03), sy * (iy - 0.03), 0.0],
        ],
        mlib.roundedRect(0.044, 0.044, 0.004, 2),
      ),
      M.limed_v,
    ])
  }
  const shelf = mlib.box(-ix + 0.03, -iy + 0.034, 0.175, ix - 0.03, iy - 0.034, 0.196)
  mlib.bevel(shelf, 0.004, 2)
  placed.push([shelf, M.limed_y])
  for (const [ob, mm] of placed) {
    mlib.translate(ob, [cx, cy, 0.0])
    w.add(ob, mm)
  }
  w.box2(cx - d / 2, cy - cw / 2, cx + d / 2, cy + cw / 2)
  const gilt = mats.get('paint_gilt') ?? mats.paint('paint_gilt', 'C9A24A', { rough: 0.3, coat: 0.4 })
  P.framed(
    w,
    0.34,
    0.42,
    [L.EX - 0.028, cy, 1.4],
    [-1, 0],
    gilt,
    mats.botanical('art_doorwall', {
      normal: [-1, 0],
      seed: 27,
      ground: 'E6DEC2',
      stem: '4A5C34',
      leafc: ['3F5730', '738650'],
      bloom: ['9C6A78', 'DCC0C6'],
    }),
    0.055,
  )
  sconce(w, [L.EX - 0.02, cy, 1.86], [-1, 0], M, 14.0)
}

// ----------------------------------------------------------------------- lamps
export function tableLamp(w: World, cx: number, cy: number, cz: number, M: MatSet, energy = 26.0, scale = 1.0): void {
  void energy // retained for authoritative build-call parity; emissive-only in raster
  const base = mlib.revolve(
    [
      [0.0, 0.0],
      [0.075, 0.0],
      [0.078, 0.012],
      [0.058, 0.03],
      [0.04, 0.052],
      [0.046, 0.082],
      [0.056, 0.11],
      [0.048, 0.15],
      [0.028, 0.18],
      [0.02, 0.215],
      [0.02, 0.3],
      [0.0, 0.3],
    ],
    24,
  )
  mlib.smoothShade(base, 34)
  mlib.scaleMesh(base, scale)
  mlib.translate(base, [cx, cy, cz])
  w.add(base, M.brass)
  const shadeMat = mats.get('shade_emis') ?? mats.emissive('shade_emis', 'FFE6BE', { strength: 1.6, base: 'EDDFBE' })
  const sh = P.pleatedShade(0.105, 0.175, 0.2, 24)
  mlib.translate(sh, [0, 0, 0.285])
  mlib.scaleMesh(sh, scale)
  mlib.translate(sh, [cx, cy, cz])
  w.add(sh, shadeMat)
  const bl = P.bulb(22.0)
  mlib.translate(bl.md, [0, 0, 0.315])
  mlib.scaleMesh(bl.md, scale)
  mlib.translate(bl.md, [cx, cy, cz])
  w.add(bl.md, bl.mat)
  // The shade/bulb provide the visible emissive practical. Do not add an
  // unshadowed point fill: additive light that ignores occluders erases the
  // dominant ceiling source's object silhouettes.
}

function ceilingLight(w: World, cx: number, cy: number, M: MatSet, energy = 350.0, drop = 0.3, r = 0.185, kelvin = 5500.0): void {
  const ztop = L.CZ
  const parts: MeshData[] = []
  const rimZ = ztop - drop
  parts.push(
    mlib.revolve(
      [
        [0.0, ztop - 0.004],
        [0.062, ztop - 0.008],
        [0.066, ztop - 0.024],
        [0.04, ztop - 0.038],
        [0.0, ztop - 0.04],
      ],
      22,
    ),
  )
  for (let k = 0; k < 3; k++) {
    const a = (Math.PI * 2 * k) / 3 + rad(30.0)
    const pts: Vec3[] = []
    for (let i = 0; i < 13; i++) {
      const t = i / 12.0
      const rr = 0.038 + (r - 0.03) * Math.sin(t * Math.PI * 0.5)
      const zz = ztop - 0.032 - drop * 0.86 * t ** 1.25
      pts.push([rr * Math.cos(a), rr * Math.sin(a), zz])
    }
    parts.push(mlib.tubeAlong(pts, mlib.circle(0.0062, 8)))
  }
  parts.push(
    mlib.revolve(
      [
        [r - 0.014, rimZ + 0.026],
        [r + 0.008, rimZ + 0.02],
        [r + 0.01, rimZ + 0.006],
        [r - 0.006, rimZ - 0.004],
        [r - 0.014, rimZ + 0.004],
      ],
      34,
    ),
  )
  parts.push(
    mlib.revolve(
      [
        [0.0, rimZ - 0.15],
        [0.016, rimZ - 0.138],
        [0.022, rimZ - 0.116],
        [0.014, rimZ - 0.098],
        [0.026, rimZ - 0.08],
        [0.02, rimZ - 0.062],
        [0.01, rimZ - 0.05],
        [0.0, rimZ - 0.048],
      ],
      18,
    ),
  )
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 38)
  mlib.translate(ob, [cx, cy, 0.0])
  // The analytic light sits inside this assembly. Keep its local brass shell
  // visible but out of the binary depth pass, otherwise cube-face seams from
  // fixture self-occlusion project a square pool onto the ceiling.
  const fixtureBrass = M.brass.clone()
  fixtureBrass.name = 'living_ceiling_brass'
  fixtureBrass.userData.noShadow = true
  w.add(ob, fixtureBrass)
  const prof: Vec2[] = []
  for (let i = 0; i < 15; i++) {
    const t = i / 14.0
    const ang = Math.PI * 0.52 * t
    prof.push([(r * Math.sin(ang)) / Math.sin(Math.PI * 0.52), rimZ + 0.02 - 0.115 * (1.0 - Math.cos(ang))])
  }
  const sh = mlib.revolve(prof, 34, { capStart: false, capEnd: false })
  mlib.solidify(sh, 0.006)
  mlib.smoothShade(sh, 48)
  mlib.translate(sh, [cx, cy, 0.0])
  w.add(sh, mats.get('opal_shade') ?? mats.emissive('opal_shade', 'FFF0D2', { strength: 2.2, base: 'F6EEDC' }))
  for (let k = 0; k < 2; k++) {
    const bl = P.bulb(26.0, 0.024)
    mlib.translate(bl.md, [0.055 * (k ? 1 : -1), 0.0, rimZ - 0.048])
    mlib.translate(bl.md, [cx, cy, 0.0])
    w.add(bl.md, bl.mat)
  }
  // Real-time visual override approved against the Cycles reference: the raw
  // Blender wattage/temperature washes out in this direct-light-only path.
  // Keep the authored arguments at the call site, but render the practical at
  // lower power and a warmer CCT, with a strong soft mask for room grounding.
  const visualEnergy = energy * 0.62
  const visualKelvin = Math.min(kelvin, 4100)
  w.pointLight([cx, cy, rimZ + 0.01], visualEnergy, P.blackbody(visualKelvin), 0.16, { shadowIntensity: 0.9 })
}

export function sconce(w: World, loc: Vec3, normal: Vec2, M: MatSet, energy = 13.0, shadow = false): void {
  const parts: MeshData[] = []
  const bp = mlib.revolve(
    [
      [0.0, 0.0],
      [0.052, 0.004],
      [0.056, 0.016],
      [0.03, 0.026],
      [0.0, 0.028],
    ],
    18,
  )
  mlib.rotX(bp, -Math.PI / 2)
  parts.push(bp)
  for (const s of [-1, 1]) {
    const arm: Vec3[] = []
    for (let i = 0; i < 13; i++) {
      const t = i / 12.0
      const a = Math.PI * 0.85 * t
      arm.push([s * 0.145 * Math.sin(a) ** 0.8, 0.055 + 0.055 * t, 0.03 + 0.115 * (1 - Math.cos(a)) * 0.6])
    }
    parts.push(mlib.tubeAlong(arm, mlib.circle(0.0075, 7)))
    const cd = mlib.revolve(
      [
        [0.0, 0.0],
        [0.024, 0.0],
        [0.024, 0.012],
        [0.013, 0.02],
        [0.013, 0.085],
        [0.0, 0.085],
      ],
      14,
    )
    mlib.translate(cd, [s * 0.145, 0.11, 0.145])
    parts.push(cd)
  }
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 38)
  const shades: P.Placed[] = []
  const shadeMat = mats.get('shade_emis') ?? mats.emissive('shade_emis', 'FFE6BE', { strength: 1.6, base: 'EDDFBE' })
  for (const s of [-1, 1]) {
    const sh = P.pleatedShade(0.042, 0.062, 0.075, 14)
    mlib.translate(sh, [s * 0.145, 0.11, 0.215])
    shades.push({ md: sh, mat: shadeMat })
    const bl = P.bulb(16.0, 0.016)
    mlib.scaleMesh(bl.md, 0.6)
    mlib.translate(bl.md, [s * 0.145, 0.11, 0.225])
    shades.push(bl)
  }
  const ang = Math.atan2(normal[1], normal[0]) - Math.PI / 2
  mlib.rotateZ(ob, ang)
  mlib.translate(ob, loc)
  w.add(ob, M.brass)
  for (const o of shades) {
    mlib.rotateZ(o.md, ang)
    mlib.translate(o.md, loc)
    w.add(o.md, o.mat)
  }
  // Never add a direct-light source that ignores occluders. The two authored
  // bedroom sconces request real maps; decorative hallway sconces retain
  // their emissive shades without a wall-leaking unshadowed fill.
  if (shadow) {
    w.pointLight(
      [loc[0] + normal[0] * 0.14, loc[1] + normal[1] * 0.14, loc[2] + 0.2],
      energy,
      [1.0, 0.74, 0.5],
      0.06,
    )
  }
}

// -------------------------------------------------------------------- poster
function jouetsPoster(w: World, M: MatSet): void {
  const pw = 1.24
  const ph = 0.74
  const cz = 1.81
  const gold = mats.paint('paint_poster_frame', 'C9A24A', { rough: 0.3, coat: 0.45 })
  P.framed(w, pw, ph, [L.EX - 0.028, L.TV_SET_Y, cz], [-1, 0], gold, M.poster, 0.0, 0.03, 0.024)
}

function carvedCrest(w: World): void {
  const cw = 0.7
  const h = 0.16
  const pts: Vec2[] = [[-cw / 2, 0.0]]
  const n = 26
  for (let i = 0; i <= n; i++) {
    const t = i / n
    const x = -cw / 2 + cw * t
    const z = h * Math.sin(Math.PI * t) ** 0.55 * (0.65 + 0.35 * Math.abs(Math.sin(t * 9.0)) ** 2)
    pts.push([x, z])
  }
  pts.push([cw / 2, 0.0])
  const ob = mlib.prismXZ(pts, 0.0, 0.055)
  mlib.smoothShade(ob, 44)
  mlib.rotateZ(ob, Math.PI / 2)
  mlib.translate(ob, [L.EX - 0.03, L.TV_SET_Y, 2.55])
  w.add(ob, mats.wood('wood_crest', ['6A4020', '452408', '2A1404'], { ring: 26, warp: 0.05, distort: 0.5, bump: 0.4, axis: 'YZ' }))
}

// ------------------------------------------------------------------ build all
export function build(w: World): MatSet {
  const M = mkMats()
  rug(w, M)
  sofa(w, L.SOFA_C[0], L.SOFA_C[1], M, L.SOFA_L)
  armchair(w, L.CHAIR_ARM_WIN[0], L.CHAIR_ARM_WIN[1], rad(-90), M)
  // red-and-white checked pillows on that armchair
  for (const dy of [-0.16, 0.16]) {
    const ck = mlib.cushion(0.12, 0.33, 0.34, 0.06)
    mlib.rotY(ck, rad(-20))
    mlib.translate(ck, [0.16, dy, 0.56])
    mlib.rotateZ(ck, rad(-90))
    mlib.translate(ck, [L.CHAIR_ARM_WIN[0], L.CHAIR_ARM_WIN[1], 0.0])
    w.add(ck, M.check)
  }
  // cast-iron radiator in the return between the bench's east end and the wall
  {
    const radParts: MeshData[] = []
    const rx0 = L.AL_X[1] - 0.42
    const rx1 = L.AL_X[1] - 0.06
    const n = 8
    for (let i = 0; i < n; i++) {
      const xx = rx0 + ((rx1 - rx0) * i) / (n - 1)
      const fin = mlib.revolve(
        [
          [0.0, 0.0],
          [0.03, 0.008],
          [0.034, 0.1],
          [0.03, 0.48],
          [0.02, 0.545],
          [0.0, 0.55],
        ],
        10,
      )
      mlib.scaleMesh(fin, [1.0, 1.9, 1.0])
      mlib.translate(fin, [xx, L.AL_Y[1] - 0.16, 0.06])
      radParts.push(fin)
    }
    radParts.push(mlib.box(rx0 - 0.05, L.AL_Y[1] - 0.22, 0.0, rx1 + 0.04, L.AL_Y[1] - 0.1, 0.075))
    const ro = mlib.join(radParts)
    mlib.smoothShade(ro, 40)
    w.add(ro, mats.paint('radiator_cream', 'BFB59A', { rough: 0.42, coat: 0.15, variation: 0.05 }), { collide: true })
  }
  slipperChair(w, L.CHAIR_SLIPPER[0], L.CHAIR_SLIPPER[1], rad(L.SLIPPER_ROT), M)
  const [ofx, ofy] = L.slipperFront(0.74)
  ottoman(w, ofx, ofy, rad(L.SLIPPER_ROT), M)
  coffeeTable(w, L.COFFEE_C[0], L.COFFEE_C[1], M, 0.88, L.COFFEE_D)
  glassTable(w, L.GLASS_T[0], L.GLASS_T[1], M)
  ceilingLight(w, L.CHANDELIER[0], L.CHANDELIER[1], M, 350.0, 0.3, 0.185, 5500.0)
  credenza(w, M)
  crtTv(w, 8.23, L.TV_SET_Y, 0.9, M, 0.8, 0.62, 0.64)
  speaker(w, 8.245, L.TV_C[1] - L.CRED_HW - 0.19, M)
  windowSeat(w, M)
  consoleTable(w, M)
  doorWall(w, M)
  jouetsPoster(w, M)
  carvedCrest(w)
  // the pair of gilt-framed botanicals south of Rachel's doorway
  const gilt = mats.get('paint_gilt') ?? mats.paint('paint_gilt', 'C9A24A', { rough: 0.3, coat: 0.4 })
  const botanY = (L.SY + L.CD_Y[0]) * 0.5
  const botanSpecs: [number, number, number][] = [
    [2.24, 0.38, 0.46],
    [1.6, 0.38, 0.46],
  ]
  botanSpecs.forEach(([zz, aw, ah], i) => {
    P.framed(
      w,
      aw,
      ah,
      [L.EX - 0.028, botanY, zz],
      [-1, 0],
      gilt,
      mats.botanical(`art_botan${i}`, {
        normal: [-1, 0],
        seed: 3 + i,
        ground: 'E9E1C6',
        stem: ['4A5C30', '55663A'][i],
        leafc: [
          ['3E5A2A', '6E8348'],
          ['4A6234', '7C8E56'],
        ][i] as [string, string],
        bloom: [
          ['B0705C', 'DFC3A4'],
          ['9A7C4E', 'E0D0A8'],
        ][i] as [string, string],
      }),
      0.075,
    )
  })
  // lamps
  tableLamp(w, (L.BW_X[0] + L.BW_X[1]) * 0.5 + 0.46, L.AL_Y[1] - L.SEAT_D - 0.3, 0.715, M, 24.0)
  sconce(w, [L.HALL_X[0] + 0.02, L.NW_Y - 0.5, 1.86], [1, 0], M)
  // Drapes now sit close to the glass and outside the window-seat ends.
  const drapeSpans: [number, number][] = [
    [L.AL_X[0] + 0.02, L.BW_X[0] - 0.12],
    [L.BW_X[1] + 0.12, L.AL_X[1] - 0.03],
  ]
  drapeSpans.forEach(([a, b2], k) => {
    const dp = P.curtainPanel(a, b2, L.AL_Z - 0.06, 0.004, 0.14, 4, 0.5, 1.35, 11 + k, 0.016, 2.4)
    mlib.translate(dp, [0, L.AL_S + 0.13, 0])
    w.add(dp, M.drape)
  })
  const sw = P.swag(L.AL_X[0] + 0.3, L.AL_X[1] - 0.3, L.AL_Z - 0.04, 0.22, 0.13, 8)
  mlib.translate(sw, [0, L.AL_S + 0.11, 0])
  w.add(sw, M.drape)
  // curtain rod
  const rod = mlib.revolve(
    [
      [0.0, 0.0],
      [0.016, 0.0],
      [0.016, L.AL_X[1] - L.AL_X[0]],
      [0.0, L.AL_X[1] - L.AL_X[0]],
    ],
    14,
  )
  mlib.rotY(rod, Math.PI / 2)
  mlib.translate(rod, [L.AL_X[0], L.AL_S + 0.16, L.AL_Z - 0.02])
  mlib.smoothShade(rod, 34)
  w.add(rod, mats.wood('wood_rod', ['5A3418', '3A1E0A', '221004'], { ring: 60, warp: 0.03, bump: 0.2, axis: 'YZ' }))
  // plants
  P.fern(w, [8.12, L.TV_C[1] + 1.02, 0.9 + 0.32 * 0.62], 0.32, 30, 3, true, M.leaf, M.terra)
  P.trailingPlant(w, [8.245, L.TV_C[1] - L.CRED_HW - 0.19, 0.824], 14, 6, M.leaf, M.wicker, 0.13)
  // two small bronze figures on the credenza top beside the vase
  const figs: [number, number, number][] = [
    [0.32, 0.155, 0.03],
    [0.44, 0.205, 0.023],
  ]
  figs.forEach(([dy, hh, tw], i) => {
    const prof: Vec2[] = [
      [0.0, 0.0],
      [tw * 1.5, 0.006],
      [tw * 1.6, 0.016],
      [tw * 0.62, 0.03],
      [tw * 0.5, hh * 0.42],
      [tw * 0.86, hh * 0.6],
      [tw * 0.66, hh * 0.78],
      [tw * 0.3, hh * 0.93],
      [0.0, hh],
    ]
    const fg = mlib.revolve(prof, 18)
    mlib.smoothShade(fg, 42)
    mlib.rotateZ(fg, 0.5 + i)
    mlib.translate(fg, [8.16 + 0.03 * i, L.TV_C[1] + dy, 0.9])
    w.add(fg, mats.metal('metal_bronze_fig', '6E5230', { rough: 0.42, bump: 0.09 }))
  })
  credenzaFlowers(w, 8.14, L.TV_C[1] + 0.56, 0.9, M, new PyRandom(23))
  dress(w, M)
  return M
}

function bookObj(w0: number, d: number, h: number, cover: THREE.Material, mag = false): P.Placed[] {
  const pgs = mats.get('book_pages') ?? mats.paint('book_pages', 'E4DDC8', { rough: 0.62, variation: 0.05 })
  const ct = mag ? 0.0022 : 0.0035
  const out: P.Placed[] = []
  const blk = mlib.box(-w0 / 2 + ct, -d / 2 + 0.005, ct, w0 / 2 - 0.006, d / 2 - 0.005, h - ct)
  mlib.bevel(blk, 0.0012, 2)
  out.push({ md: blk, mat: pgs })
  for (const [z0, z1] of [
    [0.0, ct],
    [h - ct, h],
  ] as [number, number][]) {
    const bd = mlib.box(-w0 / 2, -d / 2, z0, w0 / 2, d / 2, z1)
    mlib.bevel(bd, 0.0012, 2)
    out.push({ md: bd, mat: cover })
  }
  const sp = mlib.prism(
    [
      [-w0 / 2, -d / 2],
      [-w0 / 2 + ct * 2.2, -d / 2],
      [-w0 / 2 + ct * 2.2, d / 2],
      [-w0 / 2, d / 2],
    ],
    0.0,
    h,
  )
  mlib.bevel(sp, Math.min(0.004, h * 0.35), 3)
  out.push({ md: sp, mat: cover })
  return out
}

// ---------------------------------------------------------------- dressing
function dress(w: World, M: MatSet): void {
  const rng = new PyRandom(31)
  const pool = P.palette(55, 12)
  const [cx, cy] = L.COFFEE_C
  // magazines on the lower shelf and books on the top
  for (let i = 0; i < 4; i++) {
    const parts = bookObj(0.23, 0.3, rng.uniform(0.006, 0.011), rng.choice(pool), true)
    const rz = rng.uniform(-0.3, 0.3)
    const tx = cx + rng.uniform(-0.08, 0.08)
    const ty = cy + rng.uniform(-0.28, 0.28)
    for (const o of parts) {
      mlib.rotateZ(o.md, rz)
      mlib.translate(o.md, [tx, ty, 0.157 + i * 0.011])
      w.add(o.md, o.mat)
    }
  }
  const bookCols: number[] = [-0.34, 0.3]
  for (const dy of bookCols) {
    let z = 0.436
    const cnt = rng.randint(2, 3)
    for (let k = 0; k < cnt; k++) {
      const h = rng.uniform(0.021, 0.034)
      const parts = bookObj(0.21 - k * 0.012, 0.27 - k * 0.014, h, rng.choice(pool))
      const rz = rng.uniform(-0.3, 0.3)
      const tx = cx + rng.uniform(-0.08, 0.08)
      for (const o of parts) {
        mlib.rotateZ(o.md, rz)
        mlib.translate(o.md, [tx, cy + dy, z])
        w.add(o.md, o.mat)
      }
      z += h + 0.001
    }
  }
  // a shallow white dish + a candle on the coffee table
  for (const o of P.bowl(0.115, 0.038, mats.paint('bowl_white2', 'EAE3D2', { rough: 0.16, coat: 0.5 }))) {
    mlib.translate(o.md, [cx + 0.02, cy + 0.02, 0.437])
    w.add(o.md, o.mat)
  }
  const cnd = mlib.revolve(
    [
      [0.0, 0.0],
      [0.035, 0.0],
      [0.035, 0.115],
      [0.03, 0.125],
      [0.0, 0.128],
    ],
    18,
  )
  mlib.smoothShade(cnd, 40)
  mlib.translate(cnd, [cx - 0.2, cy - 0.1, 0.437])
  w.add(cnd, mats.paint('wax_cream', 'E4DBC0', { rough: 0.42 }))
  // phone + a tissue box on the glass table
  const body = mlib.box(-0.085, -0.055, 0.0, 0.085, 0.055, 0.038)
  mlib.bevel(body, 0.006, 2)
  const hs = mlib.prism(mlib.roundedRect(0.175, 0.045, 0.018, 4), 0.038, 0.07)
  mlib.bevel(hs, 0.008, 2)
  const po = mlib.join([body, hs])
  mlib.rotateZ(po, 0.4)
  mlib.translate(po, [L.GLASS_T[0] - 0.05, L.GLASS_T[1] + 0.11, 0.601])
  w.add(po, mats.paint('phone_black', '1E1C1A', { rough: 0.28, coat: 0.4 }))
  // two little round tapestry stools stacked beside the glass table
  const stools: [number, number][] = [
    [0.0, 0.145],
    [0.115, 0.135],
  ]
  for (const [dz, rr] of stools) {
    const st = mlib.revolve(
      [
        [0.0, 0.0],
        [rr, 0.01],
        [rr * 1.02, 0.055],
        [rr * 0.92, 0.1],
        [rr * 0.6, 0.112],
        [0.0, 0.114],
      ],
      24,
    )
    mlib.smoothShade(st, 40)
    mlib.translate(st, [L.STOOLS[0], L.STOOLS[1], dz])
    w.add(st, M.stool_tap)
  }
  w.obb(L.STOOLS[0], L.STOOLS[1], 0.16, 0.16, 0)
  // a jug of tulips on the window-seat console
  const ccx = (L.BW_X[0] + L.BW_X[1]) * 0.5
  const ccy = L.AL_Y[1] - L.SEAT_D - 0.3
  const jug = mlib.revolve(
    [
      [0.0, 0.0],
      [0.062, 0.0],
      [0.07, 0.02],
      [0.078, 0.075],
      [0.07, 0.13],
      [0.048, 0.16],
      [0.046, 0.18],
      [0.052, 0.192],
      [0.046, 0.196],
      [0.04, 0.182],
      [0.042, 0.16],
      [0.0, 0.155],
    ],
    24,
  )
  mlib.smoothShade(jug, 34)
  mlib.translate(jug, [ccx - 0.42, ccy, 0.715])
  w.add(jug, mats.paint('ceramic_pewter', '8E9084', { rough: 0.22, coat: 0.5 }))
  const stems: MeshData[] = []
  const blooms: MeshData[] = []
  for (let i = 0; i < 9; i++) {
    const a = rng.uniform(0, Math.PI * 2)
    const ln = rng.uniform(0.16, 0.28)
    const pts: Vec3[] = [[0, 0, 0.19]]
    for (let k = 1; k < 6; k++) {
      const t = k / 5.0
      pts.push([Math.cos(a) * 0.075 * t ** 1.6, Math.sin(a) * 0.075 * t ** 1.6, 0.19 + ln * t])
    }
    stems.push(mlib.tubeAlong(pts, mlib.circle(0.0032, 5)))
    const bl = mlib.revolve(
      [
        [0.0, 0.0],
        [0.02, 0.012],
        [0.026, 0.034],
        [0.022, 0.052],
        [0.0, 0.056],
      ],
      12,
    )
    mlib.translate(bl, pts[pts.length - 1])
    blooms.push(bl)
  }
  const so = mlib.join(stems)
  mlib.translate(so, [ccx - 0.42, ccy, 0.715])
  w.add(so, M.leaf)
  const bo2 = mlib.join(blooms)
  mlib.smoothShade(bo2, 40)
  mlib.translate(bo2, [ccx - 0.42, ccy, 0.715])
  w.add(bo2, mats.paint('tulip_yellow', 'D9AE22', { rough: 0.44 }))
}
