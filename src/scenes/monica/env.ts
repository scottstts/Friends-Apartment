/** Exterior world (only ever seen through the windows) + sky/sun.
 * Port of build_scripts/build_env.py.
 *
 * The Nishita world texture is evaluated on the CPU into an equirect HDR
 * texture (single-scattering Rayleigh+Mie with Blender's air/aerosol
 * densities) used for both background and environment light, at the same
 * strength.  The KW skylight panel becomes a shadow-casting spot aimed at the
 * kitchen window: three's rect light cannot shadow, and an unshadowed panel
 * would pour light through the walls, which is the one thing the build's
 * lighting rules forbid.
 */
import * as THREE from 'three/webgpu'
import * as L from './L'
import * as mlib from '../../lib/mlib'
import { MeshData, type Vec3 } from '../../lib/mesh'
import { PyRandom } from '../../lib/rng'
import * as mats from '../../mats/mats'
import { backlight } from '../../mats/mats'
import * as P from './props'
import type { World } from '../../core/world'

// ------------------------------------------------------------------ sky maths

const RAYLEIGH = [5.802e-6, 13.558e-6, 33.1e-6]
const MIE = 3.996e-6
const MIE_G = 0.76
const R_EARTH = 6360e3
const R_ATMO = 6420e3
const H_RAY = 8000
const H_MIE = 1200

function densities(h: number, air: number, aerosol: number): [number, number] {
  return [air * Math.exp(-h / H_RAY), aerosol * Math.exp(-h / H_MIE)]
}

function atmoDist(o: [number, number, number], d: [number, number, number]): number {
  const b = o[0] * d[0] + o[1] * d[1] + o[2] * d[2]
  const c = o[0] * o[0] + o[1] * o[1] + o[2] * o[2] - R_ATMO * R_ATMO
  const disc = b * b - c
  return -b + Math.sqrt(Math.max(0, disc))
}

/** Single-scattering sky radiance for a view ray. */
function skyRadiance(dir: [number, number, number], sunDir: [number, number, number], air: number, aerosol: number, altitude: number): [number, number, number] {
  const o: [number, number, number] = [0, 0, R_EARTH + Math.max(1, altitude)]
  if (dir[2] < -0.06) {
    // below horizon: dim ground haze
    return [0.02 * air, 0.022 * air, 0.024 * air]
  }
  const d: [number, number, number] = [dir[0], dir[1], Math.max(dir[2], 0.0)]
  const dl = Math.hypot(...d) || 1
  d[0] /= dl
  d[1] /= dl
  d[2] /= dl
  const len = atmoDist(o, d)
  const NS = 16
  const seg = len / NS
  const mu = d[0] * sunDir[0] + d[1] * sunDir[1] + d[2] * sunDir[2]
  const phaseR = (3 / (16 * Math.PI)) * (1 + mu * mu)
  const g = MIE_G
  const phaseM = ((3 / (8 * Math.PI)) * ((1 - g * g) * (1 + mu * mu))) / ((2 + g * g) * Math.pow(1 + g * g - 2 * g * mu, 1.5))
  let tR = 0
  let tM = 0
  const sumR = [0, 0, 0]
  const sumM = [0, 0, 0]
  for (let i = 0; i < NS; i++) {
    const t = (i + 0.5) * seg
    const p: [number, number, number] = [o[0] + d[0] * t, o[1] + d[1] * t, o[2] + d[2] * t]
    const h = Math.hypot(...p) - R_EARTH
    const [dR, dM] = densities(h, air, aerosol)
    tR += dR * seg
    tM += dM * seg
    // light path to sun
    const lLen = atmoDist(p, sunDir)
    const LS = 8
    const lseg = lLen / LS
    let ltR = 0
    let ltM = 0
    let blocked = false
    for (let j = 0; j < LS; j++) {
      const lt = (j + 0.5) * lseg
      const q: [number, number, number] = [p[0] + sunDir[0] * lt, p[1] + sunDir[1] * lt, p[2] + sunDir[2] * lt]
      const qh = Math.hypot(...q) - R_EARTH
      if (qh < 0) {
        blocked = true
        break
      }
      const [ldR, ldM] = densities(qh, air, aerosol)
      ltR += ldR * lseg
      ltM += ldM * lseg
    }
    if (blocked) continue
    for (let c = 0; c < 3; c++) {
      const tau = RAYLEIGH[c] * (tR + ltR) + MIE * 1.1 * (tM + ltM)
      const att = Math.exp(-tau)
      sumR[c] += att * dR * seg
      sumM[c] += att * dM * seg
    }
  }
  const SUN = 20.0
  return [0, 1, 2].map((c) => SUN * (sumR[c] * RAYLEIGH[c] * phaseR + sumM[c] * MIE * phaseM)) as [number, number, number]
}

export interface SkyResult {
  texture: THREE.DataTexture
  sunDir: [number, number, number]
  avg: [number, number, number]
}

/** Blender sky_and_sun defaults carried over: az 289, el 23, air 1.4,
 * aerosol 2.4, altitude 60, no sun disc. */
export function makeSky(az = 289.0, el = 23.0): SkyResult {
  const a = (az * Math.PI) / 180
  const e = (el * Math.PI) / 180
  const sunDir: [number, number, number] = [Math.sin(a) * Math.cos(e), -Math.cos(a) * Math.cos(e), Math.sin(e)]
  const W = 128
  const H = 64
  const data = new Uint16Array(W * H * 4)
  const toHalf = THREE.DataUtils.toHalfFloat
  const avg = [0, 0, 0]
  let avgWeight = 0
  for (let y = 0; y < H; y++) {
    // Three's equirectangular convention is Y-up even though this scene (and
    // Blender) is Z-up. Pack each texel by Three's sampling direction, then
    // evaluate the sky in the apartment's real XYZ frame. The old Z-up image
    // layout made Three sample the horizon for a +Z ray, rotating daylight and
    // diffuse IBL ninety degrees away from the modeled sun and windows.
    const v = (y + 0.5) / H
    const latitude = Math.PI * (v - 0.5)
    const dy = Math.sin(latitude)
    const ring = Math.cos(latitude)
    for (let x = 0; x < W; x++) {
      const longitude = 2 * Math.PI * ((x + 0.5) / W - 0.5)
      const dx = Math.cos(longitude) * ring
      const dz = Math.sin(longitude) * ring
      const [r, g, b] = skyRadiance([dx, dy, dz], sunDir, 1.4, 2.4, 60)
      const i = (y * W + x) * 4
      data[i] = toHalf(r)
      data[i + 1] = toHalf(g)
      data[i + 2] = toHalf(b)
      data[i + 3] = toHalf(1)
      if (dz > 0.02) {
        // Rows near the equirectangular poles cover less solid angle.
        avg[0] += r * ring
        avg[1] += g * ring
        avg[2] += b * ring
        avgWeight += ring
      }
    }
  }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat, THREE.HalfFloatType)
  tex.mapping = THREE.EquirectangularReflectionMapping
  tex.magFilter = THREE.LinearFilter
  tex.minFilter = THREE.LinearFilter
  tex.needsUpdate = true
  tex.colorSpace = THREE.LinearSRGBColorSpace
  return {
    texture: tex,
    sunDir,
    avg: [avg[0] / avgWeight, avg[1] / avgWeight, avg[2] / avgWeight] as [number, number, number],
  }
}

/** World sky + SUN lamp.  strength/sun_energy exactly as build_all passes. */
export function skyAndSun(w: World, strength = 0.145, sunEnergy = 2.4): void {
  const sky = makeSky()
  w.scene.environment = sky.texture
  w.scene.environmentIntensity = strength
  w.scene.background = sky.texture
  w.scene.backgroundIntensity = strength
  const d = sky.sunDir
  const sun = new THREE.DirectionalLight(new THREE.Color(1.0, 0.86, 0.68), sunEnergy)
  sun.position.set(d[0] * 40 + 3, d[1] * 40 + 3, d[2] * 40)
  sun.target.position.set(3, 3, 0)
  sun.castShadow = true
  sun.shadow.mapSize.set(2048, 2048)
  const cam = sun.shadow.camera
  cam.left = -14
  cam.right = 14
  cam.top = 14
  cam.bottom = -14
  cam.near = 8
  cam.far = 80
  sun.shadow.bias = -0.0004
  sun.shadow.normalBias = 0.02
  sun.shadow.radius = 12
  // Cycles' 1.6-degree sun has a broad penumbra; PCF cannot reproduce its
  // distance-dependent softness, so blend the otherwise hard raster mask.
  sun.shadow.intensity = 0.65
  w.addLight(sun)
  w.scene.add(sun.target)
  // feed the thin-surface translucency approximation
  backlight.dirToSun.value.set(d[0], d[1], d[2])
  backlight.sunColor.value.setRGB(1.0 * sunEnergy * 0.3, 0.86 * sunEnergy * 0.3, 0.68 * sunEnergy * 0.3)
  backlight.skyAmb.value.setRGB(sky.avg[0] * strength * 0.5, sky.avg[1] * strength * 0.5, sky.avg[2] * strength * 0.5)
}

// ------------------------------------------------------------------- facades

function facade(
  w: World,
  x0: number,
  x1: number,
  z0: number,
  z1: number,
  y: number,
  t = 0.42,
  cols = 8,
  rows = 6,
  mat?: THREE.Material,
  glass?: THREE.Material,
  lit?: THREE.Material,
  seed = 3,
  post?: (md: MeshData) => void,
): void {
  const width = x1 - x0
  const h = z1 - z0
  const holes: [number, number, number, number][] = []
  const ww = (width / cols) * 0.42
  const wh = (h / rows) * 0.46
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < rows; j++) {
      const cx = (width * (i + 0.5)) / cols
      const cz = (h * (j + 0.42)) / rows
      holes.push([cx - ww / 2, cz - wh / 2, cx + ww / 2, cz + wh / 2])
    }
  }
  const ob = mlib.panelWithHoles(width, h, t, holes)
  mlib.transform4(ob, [
    [1, 0, 0, x0],
    [0, 1, 0, y],
    [0, 0, 1, z0],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(ob)
  if (post) post(ob)
  if (mat) w.add(ob, mat)
  // panes
  const litFaces = new MeshData()
  const darkFaces = new MeshData()
  const rng2 = new PyRandom(seed + 7)
  for (const [a, b, c, dd] of holes) {
    const px0 = x0 + a
    const px1 = x0 + c
    const pz0 = z0 + b
    const pz1 = z0 + dd
    const yy = y + t * 0.72
    const isLit = rng2.random() < 0.45
    const tgt = isLit ? litFaces : darkFaces
    const base = tgt.verts.length
    tgt.verts.push([px0, yy, pz0], [px1, yy, pz0], [px1, yy, pz1], [px0, yy, pz1])
    tgt.faces.push([base, base + 1, base + 2, base + 3])
  }
  for (const md of [litFaces, darkFaces]) {
    mlib.recalcNormals(md)
    if (post) post(md)
  }
  if (lit) w.add(litFaces, lit)
  w.add(darkFaces, glass ?? lit!)
}

export interface EnvOpts {
  /** The sky-panel standing in for the sky through the kitchen window.
   * Defaults to build_env.py's sunlit light well; the night build passes a
   * dim cool skyglow instead (night.KW_SKYGLOW). */
  kwSkylight?: { energy: number; color: [number, number, number] }
}

export function build(w: World, opts: EnvOpts = {}): void {
  const mb = mats.brickWall('brick_exterior', { c1: '7C4636', c2: '5A3128', mortar: '8E8577' })
  const mLit = mats.emissive('win_lit', 'FFD9A0', { strength: 5.0, base: '2A2015' })
  const mDark = mats.paint('win_dark', '15161C', { rough: 0.16, coat: 0.5 })
  const mConc = mats.plaster('concrete_ext', '7E7A70', { rough: 0.75, bump: 0.55, scale: 38 })
  const mSteel = mats.metal('metal_dark_ext', '2E2C2A', { rough: 0.5, bump: 0.15 })

  // brick veneer on the outside of the alcove north wall
  const VX = L.HALL_EW[1]
  const ven = mlib.panelWithHoles(L.AL_X[1] - VX, L.BW_TOP, 0.03, [
    [L.BW_X[0] - VX, L.BW_SILL, L.BW_X[1] - VX, L.BW_TOP],
  ])
  mlib.transform4(ven, [
    [1, 0, 0, VX],
    [0, 1, 0, L.AL_Y[1] + L.TW + 0.002],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(ven)
  w.add(ven, mb)

  // narrow setback ledge outside the window with a low masonry parapet
  const TX = L.HALL_EW[1] + 0.13
  w.add(mlib.box(TX, L.AL_Y[1] + L.TW, -0.1, 13.0, 7.0, 0.02), mConc)
  const par = mlib.box(TX, 6.8, -0.05, 13.0, 7.0, 0.88)
  mlib.bevel(par, 0.02, 2)
  w.add(par, mConc)
  const cap = mlib.box(TX - 0.04, 6.76, 0.88, 13.04, 7.04, 0.945)
  mlib.bevel(cap, 0.012, 2)
  w.add(cap, mConc)
  // fire-escape rail rising past the window
  const rails: MeshData[] = []
  for (const x of [5.35, 7.55]) {
    const r = mlib.revolve(
      [
        [0.0, 0.0],
        [0.022, 0.0],
        [0.022, 1.15],
        [0.0, 1.15],
      ],
      12,
    )
    mlib.translate(r, [x, 6.62, 0.02])
    rails.push(r)
  }
  rails.push(mlib.box(5.35, 6.598, 1.1, 7.55, 6.642, 1.142))
  w.add(mlib.join(rails), mSteel)

  // building across the street
  facade(w, -8.0, 10.0, -12.0, 14.0, 11.0, 0.6, 7, 10, mb, mDark, mLit, 5)
  facade(w, 10.0, 24.0, -12.0, 11.0, 10.2, 0.6, 6, 9, mb, mDark, mLit, 11)
  // building opposite the bedroom windows, to the east
  facade(w, -6.0, 12.0, -12.0, 12.0, 16.6, 0.6, 7, 9, mb, mDark, mLit, 23, (md) => {
    mlib.rotateZ(md, -Math.PI / 2)
    mlib.translate(md, [L.EXT_E + 9.6, 1.2, 0.0])
  })
  // street level
  w.add(mlib.box(-12.0, 7.2, -12.06, 26.0, 11.0, -12.0), mats.plaster('asphalt', '3A3A3C', { rough: 0.8, bump: 0.4, scale: 60 }))

  // sunlit light-well wall opposite the kitchen window
  const mStucco = mats.plaster('stucco_lightwell', 'C9C0AC', { rough: 0.72, bump: 0.4, scale: 30 })
  w.add(
    mlib.prism(
      [
        [-4.2, 5.0],
        [0.6, 9.8],
        [0.16, 10.24],
        [-4.64, 5.44],
      ],
      -12.0,
      9.5,
    ),
    mStucco,
  )
  w.add(mlib.box(-5.0, 2.0, -12.0, -4.2, 6.2, 9.5), mStucco)
  // KW_skylight: the sky-panel standing in for daylight through the kitchen
  // window, aimed at the window it stands for.
  {
    const kw = opts.kwSkylight ?? { energy: 260.0, color: [1.0, 0.95, 0.86] as [number, number, number] }
    const kp = L.chamferPt(0.72, -1.45)
    const wc = L.chamferPt(0.72, 0.0)
    const from = new THREE.Vector3(kp[0], kp[1], 2.1)
    const to = new THREE.Vector3(wc[0], wc[1], (L.KW_Z[0] + L.KW_Z[1]) * 0.5)
    const spot = new THREE.SpotLight(new THREE.Color(...kw.color), kw.energy / Math.PI)
    spot.position.copy(from)
    spot.target.position.copy(to)
    spot.angle = 0.62
    spot.penumbra = 0.7
    spot.decay = 2
    spot.castShadow = true
    spot.shadow.mapSize.set(1024, 1024)
    spot.shadow.camera.near = 0.3
    spot.shadow.camera.far = 16
    spot.shadow.bias = -0.0008
    spot.shadow.normalBias = 0.02
    spot.shadow.intensity = 0.72
    w.addLight(spot)
    w.scene.add(spot.target)
  }

  // -- the landing outside the front door (Monica/Chandler's hallway) --------
  const mHall = mats.plaster('landing_wall', '7E6EA8', { rough: 0.6, bump: 0.22 })
  const mHwood = mats.wood('landing_wood', ['8A5A30', '5F3A1A', '3A2010'], {
    ring: 16,
    warp: 0.12,
    warpScale: 1.5,
    distort: 1.6,
    bump: 0.3,
    axis: 'Z',
  })
  const lx0 = -2.4
  const lx1 = -L.TW
  const ly0 = L.SY - 0.2
  const ly1 = 1.1
  const boxes: [Vec3, Vec3, THREE.Material][] = [
    [[lx0 - 0.22, ly0, 0], [lx0, ly1, L.CZ], mHall],
    [[lx0 - 0.22, ly0 - 0.22, 0], [lx1, ly0, L.CZ], mHall],
    [[lx0 - 0.22, ly1, 0], [lx1, ly1 + 0.22, L.CZ], mHall],
    [[lx0 - 0.22, ly0 - 0.22, L.CZ], [lx1, ly1 + 0.22, L.CZ + 0.1], mHall],
    [[lx0 - 0.22, ly0 - 0.22, -0.02], [lx1, ly1 + 0.22, 0.004], mHwood],
  ]
  for (const [a, b, mm] of boxes) {
    w.add(mlib.box(a[0], a[1], a[2], b[0], b[1], b[2]), mm)
  }
  // A fitting on the landing ceiling, behind the transom's glow.
  P.flushDome(w, [-1.15, 0.1, L.CZ - 0.01], 0.125, 26.0, [1.0, 0.78, 0.55], 0.085)
}
