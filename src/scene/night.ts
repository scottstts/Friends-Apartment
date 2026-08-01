/** Night exterior: NYC night sky + distant-city ambience.
 *
 * A user-directed deviation from build_env.py, whose sky_and_sun is a daytime
 * Nishita world (that port stays in env.ts as the parity baseline).  Every
 * exterior the ground truth models — facades, lit panes, parapet, street —
 * is untouched and becomes the near field of the night view; this module
 * supplies only what lies beyond it, as cheaply as possible:
 *
 * - background: one procedural shader on the renderer's sky sphere.  A
 *   light-pollution gradient (sodium glow pooled toward Midtown, north-east
 *   of the flat), a sparse footprint-aware star field, a small moon with a
 *   haze halo, and two hashed skyline layers whose lit windows are the only
 *   bright marks.  No geometry, no textures; it costs background pixels only.
 * - environment: the same gradient baked once on the CPU into a small
 *   equirect (the day port's frame convention), so interior fill and glazing
 *   reflections agree with what the windows show.
 * - mid-ground: a ring of dummy blocks at 55-160 m between the modeled set
 *   and the matte, so looking down from the fifth floor lands on rooftops
 *   instead of empty haze.  One merged unlit draw, windows in the same
 *   language as the painted layers.
 * - MOON replaces SUN one-for-one: same rig, same shadow budget, lunar
 *   energy.  The KW skylight panel drops to skyglow via env.build's
 *   kwSkylight option.
 *
 * All hashes are seeded constants, so the sky is deterministic frame to
 * frame and run to run.
 */
import * as THREE from 'three/webgpu'
import {
  abs,
  add,
  asin,
  atan2,
  clamp,
  cos,
  dot,
  exp,
  float,
  floor,
  fract,
  fwidth,
  hash,
  length,
  max,
  min,
  mix,
  mul,
  mx_noise_float,
  normalWorld,
  normalWorldGeometry,
  positionWorld,
  pow,
  select,
  smoothstep,
  sub,
  vec2,
  vec3,
} from 'three/tsl'
import * as mlib from '../lib/mlib'
import { PyRandom } from '../lib/rng'
import { backlight } from '../mats/mats'
import type { N } from '../mats/tsl'
import type { World } from './world'

type V3 = [number, number, number]

// ------------------------------------------------------------------ palette
// Scene-linear radiance, placed against the filmic view's hierarchy:
// practicals ~0.2-0.8 >> lit windows ~0.5-2 > horizon glow ~0.09 >
// zenith ~0.003 ~ silhouettes.  Bloom threshold is 0.5, so only the moon
// and the brightest windows glare.
const ZENITH: V3 = [0.0026, 0.004, 0.009]
const GLOW: V3 = [0.085, 0.047, 0.019] // 90s sodium-vapour amber
const GROUND: V3 = [0.01, 0.008, 0.0062]
const GLOW_H = 0.14 // glow scale height, in sin-elevation
const GLOW_LOBE = 0.75 // extra glow toward Midtown
const LOBE_AZ = 0.6 // rad east of north

// Moon ESE at 26 deg: high enough to clear EXT_facade_e's roofline into the
// bedroom windows — the only glazing with open sky, since the big window
// faces the facade across the street, exactly as in the show.
const MOON_AZ = 104.0
const MOON_EL = 26.0
const MOON_DIR: V3 = (() => {
  const a = (MOON_AZ * Math.PI) / 180
  const e = (MOON_EL * Math.PI) / 180
  return [Math.sin(a) * Math.cos(e), -Math.cos(a) * Math.cos(e), Math.sin(e)]
})()
const MOON_SINR = 0.00524 // 0.30 deg disc, a touch over the real 0.26
const MOON_B = 4.2
const MOON_COL: V3 = [1.0, 0.96, 0.87]
const HALO_W = 0.014 // haze halo 1/e width, sin-angle
const HALO_B = 0.05
const MOONLIGHT = 0.055 // directional intensity vs the day sun's 2.4
const MOONLIGHT_COL: V3 = [0.7, 0.79, 1.0]

const STAR_SCALE = 42 // direction-space cells of ~1.4 deg
const STAR_P = 0.03 // occupancy: a washed-out city sky, not a desert's
const STAR_R = 0.05 // core radius in cell units (~0.0012 rad, ~1.5 px)

/** Skylight stand-in through the kitchen window at night: dim cool skyglow
 * in place of the sunlit light well (day: 260 W warm). */
export const KW_SKYGLOW: { energy: number; color: V3 } = { energy: 6.0, color: [0.55, 0.66, 0.92] }

// ------------------------------------------------------- sky gradient (CPU)

function smoothstepN(e0: number, e1: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)))
  return t * t * (3 - 2 * t)
}

/** CPU mirror of atmoNode, for the IBL bake.  Keep the two in lockstep. */
function atmoCpu(x: number, y: number, z: number): V3 {
  const az = Math.atan2(x, y)
  const lobe = 1 + GLOW_LOBE * (0.5 + 0.5 * Math.cos(az - LOBE_AZ)) ** 2
  const hz = Math.exp(-Math.max(z, 0) / GLOW_H)
  const below = 0.85 * smoothstepN(0, 0.22, -z)
  const out: V3 = [0, 0, 0]
  for (let c = 0; c < 3; c++) {
    const sky = ZENITH[c] + (GLOW[c] * lobe - ZENITH[c]) * hz
    out[c] = sky + (GROUND[c] * lobe - sky) * below
  }
  return out
}

// ------------------------------------------------------- sky gradient (TSL)

function atmoNode(dir: N): N {
  const az = atan2(dir.x, dir.y)
  const lobe = add(1, mul(GLOW_LOBE, pow(add(0.5, mul(0.5, cos(sub(az, LOBE_AZ)))), 2)))
  const hz = exp(mul(max(dir.z, 0), -1 / GLOW_H))
  const sky = mix(vec3(...ZENITH), mul(vec3(...GLOW), lobe), hz)
  const below = mul(smoothstep(0, 0.22, mul(dir.z, -1)), 0.85)
  return mix(sky, mul(vec3(...GROUND), lobe), below)
}

// ------------------------------------------------------------------ skyline
// Two matte layers painted in (azimuth, elevation): hashed column heights,
// hashed lit windows.  At 60-plus metres a facade is texture, not geometry,
// so this is strictly cheaper than more EXT_facade boxes and reads the same
// through glass.

interface SkyLayer {
  colW: number // building column width, rad
  hMin: number // roofline range, rad above horizon
  hMax: number
  haze: number // aerial perspective: how far towards the sky the silhouette sits
  sil: V3 // silhouette base colour
  winW: number // window cell size, rad
  winH: number
  litP: number // fraction of windows lit
  winB: number // lit-window radiance scale
  seed: number
  towers?: { az: [number, number]; p: number; hAdd: number } // Midtown cluster
}

const FAR: SkyLayer = {
  colW: 0.028,
  hMin: 0.008,
  hMax: 0.055,
  haze: 0.52,
  sil: [0.0045, 0.0046, 0.006],
  winW: 0.0042,
  winH: 0.003,
  litP: 0.1,
  winB: 0.85,
  seed: 17.0,
  towers: { az: [0.87, 1.66], p: 0.3, hAdd: 0.075 },
}

const NEAR: SkyLayer = {
  colW: 0.055,
  hMin: 0.014,
  hMax: 0.09,
  haze: 0.22,
  sil: [0.0028, 0.0029, 0.004],
  winW: 0.0075,
  winH: 0.0052,
  litP: 0.13,
  winB: 1.4,
  seed: 53.0,
}

function layerNode(az: N, el: N, atmo: N, o: SkyLayer): { m: N; col: N } {
  const ci = floor(az.div(o.colW))
  const ch = hash(add(mul(ci, 133.71), o.seed))
  let h: N = add(o.hMin, mul(pow(ch, 1.35), o.hMax - o.hMin))
  let crown: N = float(0)
  if (o.towers) {
    const [a0, a1] = o.towers.az
    const inBand = mul(smoothstep(a0 - 0.06, a0, az), smoothstep(a1, a1 + 0.06, az).oneMinus())
    const gate = select(hash(add(mul(ci, 77.31), o.seed + 9.1)).lessThan(o.towers.p), float(1), float(0))
    const th = hash(add(mul(ci, 51.77), o.seed + 4.7))
    h = add(h, mul(mul(gate, inBand), mul(pow(th, 2), o.towers.hAdd)))
    // the tall cluster gets faint warm crown lighting near its rooflines
    crown = mul(mul(gate, inBand), smoothstep(mul(h, 0.86), mul(h, 0.97), el))
  }
  const aa = fwidth(el)
  const m = mul(
    smoothstep(sub(h, aa), add(h, aa), el).oneMinus(),
    // silhouettes dissolve into street haze looking down between the blocks
    smoothstep(-0.14, -0.1, el),
  )
  const silCol = mix(vec3(...o.sil), atmo, o.haze)
  // windows: a global (az, el) grid; lit cells are hashed, edges take a
  // derivative-wide apron so sub-pixel cells average instead of shimmering
  const wu = az.div(o.winW)
  const wv = el.div(o.winH)
  const cu = floor(wu)
  const cv = floor(wv)
  const litG = select(hash(add(add(mul(cu, 917.13), mul(cv, 271.71)), o.seed + 31)).lessThan(o.litP), float(1), float(0))
  const wb = hash(add(add(mul(cu, 391.51), mul(cv, 683.29)), o.seed + 57))
  const warm = hash(add(add(mul(cu, 137.93), mul(cv, 457.13)), o.seed + 83))
  const au = min(fwidth(wu), 0.5)
  const av = min(fwidth(wv), 0.5)
  const bx = mul(smoothstep(sub(0.26, au), add(0.26, au), fract(wu)), smoothstep(sub(0.74, au), add(0.74, au), fract(wu)).oneMinus())
  const by = mul(smoothstep(sub(0.3, av), add(0.3, av), fract(wv)), smoothstep(sub(0.7, av), add(0.7, av), fract(wv)).oneMinus())
  const wcol = mix(vec3(1.0, 0.78, 0.52), vec3(0.85, 0.9, 1.0), pow(warm, 3))
  const wI = mul(mul(litG, mul(bx, by)), mul(add(0.3, mul(pow(wb, 2), 1.2)), o.winB))
  const col = add(add(silCol, mul(vec3(0.95, 0.86, 0.62), mul(crown, 0.25))), mul(wcol, wI))
  return { m, col }
}

// ------------------------------------------------------- mid-ground masses
// The matte skyline is painted at infinity, so from a fifth-floor eye the
// band under it is otherwise empty haze and the towers float.  Dummy blocks
// with real parallax fill the downward view: two stratified rings outside
// everything build_env.py models (all of which sits within ~45 m), unlit —
// at night these are silhouette, window grid and street glow, nothing a
// light rig would add.  Deterministic via PyRandom, like the facade panes.

const MID_SIL: V3 = [0.0022, 0.0023, 0.0032]
const MID_STREET_GLOW: V3 = [0.0075, 0.0042, 0.0016] // sodium wash climbing from street level
const MID_HAZE: V3 = [0.042, 0.024, 0.01]
const MID_WIN_W = 1.9 // metres, window cell
const MID_WIN_H = 1.45
const MID_LIT_P = 0.09

function midgroundMat(): THREE.MeshBasicNodeMaterial {
  const m = new THREE.MeshBasicNodeMaterial()
  // mlib.box winding is normally corrected by lit shading; unlit boxes keep
  // both sides so no face can vanish on the cheap
  m.side = THREE.DoubleSide
  const p = positionWorld
  const isX = abs(normalWorld.x).greaterThan(0.5)
  const isRoof = abs(normalWorld.z).greaterThan(0.5)
  const hc = select(isX, p.y, p.x)
  const plane = select(isX, p.x, p.y) // constant per facade: decorrelates the grid
  const wu = hc.div(MID_WIN_W)
  const wv = p.z.add(12).div(MID_WIN_H)
  const cu = floor(wu)
  const cv = floor(wv)
  const fk = mul(floor(plane.div(2.7)), 53.77)
  const litG = select(hash(add(add(mul(cu, 917.13), mul(cv, 271.71)), fk)).lessThan(MID_LIT_P), float(1), float(0))
  const wb = hash(add(add(mul(cu, 391.51), mul(cv, 683.29)), fk))
  const warm = hash(add(add(mul(cu, 137.93), mul(cv, 457.13)), fk))
  const au = min(fwidth(wu), 0.5)
  const av = min(fwidth(wv), 0.5)
  const bx = mul(smoothstep(sub(0.3, au), add(0.3, au), fract(wu)), smoothstep(sub(0.7, au), add(0.7, au), fract(wu)).oneMinus())
  const by = mul(smoothstep(sub(0.32, av), add(0.32, av), fract(wv)), smoothstep(sub(0.68, av), add(0.68, av), fract(wv)).oneMinus())
  const wcol = mix(vec3(1.0, 0.78, 0.52), vec3(0.85, 0.9, 1.0), pow(warm, 3))
  const wI = mul(mul(litG, mul(bx, by)), mul(add(0.3, mul(pow(wb, 2), 1.2)), 1.1))
  const body = add(vec3(...MID_SIL), mul(vec3(...MID_STREET_GLOW), exp(mul(p.z.add(12), -1 / 6.5))))
  const faceCol = add(body, mul(wcol, mul(wI, select(isRoof, float(0), float(1)))))
  const col = select(isRoof, mul(vec3(...MID_SIL), 0.7), faceCol)
  // the far ring breathes toward the glow: aerial perspective, and it seats
  // the geometric masses against the painted layers behind them
  const hz = mul(smoothstep(60, 170, length(sub(p.xy, vec2(5, 1)))), 0.35)
  m.colorNode = mix(col, vec3(...MID_HAZE), hz)
  m.userData.noShadow = true
  return m
}

function midground(w: World): void {
  const rng = new PyRandom(2201)
  const mat = midgroundMat()
  const bands = [
    { n: 16, r0: 55, r1: 95, z0: -5, z1: 7, tallP: 0.18, tallAdd: 9, off: 0 },
    { n: 14, r0: 100, r1: 160, z0: -3, z1: 5, tallP: 0.12, tallAdd: 7, off: 0.5 },
  ]
  for (const b of bands) {
    for (let i = 0; i < b.n; i++) {
      // stratified full circle with jitter; the second ring is phase-offset
      // so its blocks stand in the first ring's street gaps
      const az = ((i + b.off + 0.15 + 0.7 * rng.random()) / b.n) * Math.PI * 2
      const r = b.r0 + rng.random() * (b.r1 - b.r0)
      const cx = 5 + Math.sin(az) * r
      const cy = 1 + Math.cos(az) * r
      const hw = 6 + rng.random() * 8
      const hd = 6 + rng.random() * 8
      let rz = b.z0 + rng.random() * (b.z1 - b.z0)
      if (rng.random() < b.tallP) rz += 4 + rng.random() * b.tallAdd
      w.add(mlib.box(cx - hw, cy - hd, -12, cx + hw, cy + hd, rz), mat)
    }
  }
}

// ----------------------------------------------------------------- assembly

function nightSkyNode(): N {
  const dir = normalWorldGeometry.normalize().toVar()
  const az = atan2(dir.x, dir.y).toVar()
  const el = asin(clamp(dir.z, -1, 1)).toVar()
  const atmo = atmoNode(dir).toVar()

  // moon disc + haze halo (sin-angle keeps float precision honest near mu=1)
  const mdir = vec3(...MOON_DIR)
  const mu = dot(dir, mdir).toVar()
  const sinT = length(sub(dir, mul(mdir, mu))).toVar()
  const aaM = fwidth(sinT)
  const disc = smoothstep(sub(float(MOON_SINR), aaM), add(float(MOON_SINR), aaM), sinT).oneMinus()
  const rr = sinT.div(MOON_SINR)
  const limb = sub(1, mul(0.32, mul(rr, rr)))
  const maria = add(0.8, mul(0.2, smoothstep(-0.4, 0.5, mx_noise_float(mul(dir, 210)))))
  const front = smoothstep(0.0, 0.02, mu) // kill the antipodal mirror image
  const halo = mul(HALO_B, min(exp(sub(float(MOON_SINR), sinT).div(HALO_W)), 1))
  const moon = mul(add(mul(mul(vec3(...MOON_COL), MOON_B), mul(disc, mul(limb, maria))), mul(vec3(0.95, 0.93, 0.99), halo)), front)

  // stars: one per direction-space cell, kept off cell borders so a single
  // lookup suffices; when a core falls below a pixel its energy spreads over
  // the derivative footprint instead of aliasing
  const p = mul(dir, STAR_SCALE).toVar()
  const cell = floor(p).toVar()
  const h3 = vec3(
    hash(dot(cell, vec3(127.1, 311.7, 74.7))),
    hash(dot(cell, vec3(269.5, 183.3, 246.1))),
    hash(dot(cell, vec3(113.5, 271.9, 124.6))),
  ).toVar()
  const d = length(sub(p, add(cell, add(0.25, mul(h3, 0.5)))))
  const fw = max(fwidth(d), 1e-4)
  const rEff = max(float(STAR_R), fw)
  const core = smoothstep(mul(rEff, 0.3), rEff, d).oneMinus()
  const conserve = pow(float(STAR_R).div(rEff), 2)
  const eGate = select(hash(dot(cell, vec3(311.7, 127.1, 74.7))).lessThan(STAR_P), float(1), float(0))
  const bright = add(0.18, mul(pow(h3.z, 6), 1.4))
  const scol = mix(vec3(0.72, 0.8, 1.0), vec3(1.0, 0.9, 0.76), h3.y)
  const svis = mul(
    smoothstep(0.06, 0.35, dir.z), // pollution swallows the low sky
    smoothstep(0.9985, 0.9998, mu).oneMinus(), // and the halo outshines its own
  )
  const stars = mul(scol, mul(mul(eGate, bright), mul(mul(core, conserve), svis)))

  const open = add(atmo, add(stars, moon)).toVar()
  const far = layerNode(az, el, atmo, FAR)
  const near = layerNode(az, el, atmo, NEAR)
  return mix(mix(open, far.col, far.m), near.col, near.m)
}

// ---------------------------------------------------------------------- IBL

/** Bake the gradient into a small equirect for environment lighting and
 * reflections.  Same texel-direction convention as env.makeSky: pack by
 * Three's Y-up sampling direction, whose components are already scene-frame
 * (x, y, z) — the up axis of this scene lands in dz. */
function bakeIbl(): { texture: THREE.DataTexture; avg: V3 } {
  const W = 64
  const H = 32
  const data = new Uint16Array(W * H * 4)
  const toHalf = THREE.DataUtils.toHalfFloat
  const avg = [0, 0, 0]
  let avgWeight = 0
  for (let y = 0; y < H; y++) {
    const v = (y + 0.5) / H
    const latitude = Math.PI * (v - 0.5)
    const dy = Math.sin(latitude)
    const ring = Math.cos(latitude)
    for (let x = 0; x < W; x++) {
      const longitude = 2 * Math.PI * ((x + 0.5) / W - 0.5)
      const dx = Math.cos(longitude) * ring
      const dz = Math.sin(longitude) * ring
      const [r, g, b] = atmoCpu(dx, dy, dz)
      const i = (y * W + x) * 4
      data[i] = toHalf(r)
      data[i + 1] = toHalf(g)
      data[i + 2] = toHalf(b)
      data[i + 3] = toHalf(1)
      if (dz > 0.02) {
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
  return { texture: tex, avg: [avg[0] / avgWeight, avg[1] / avgWeight, avg[2] / avgWeight] }
}

// -------------------------------------------------------------------- build

export function build(w: World): void {
  // backgroundNode is runtime API not yet in the type declarations
  ;(w.scene as THREE.Scene & { backgroundNode: N }).backgroundNode = nightSkyNode()
  w.scene.backgroundIntensity = 1.0 // the node carries real radiance
  const ibl = bakeIbl()
  w.scene.environment = ibl.texture
  w.scene.environmentIntensity = 1.0
  midground(w)

  // MOON replaces SUN one-for-one: env.skyAndSun's rig and shadow budget,
  // lunar energy.  Shadow lightening drops (0.65 -> 0.8): the night sky
  // supplies far less of the indirect fill Cycles would return.
  const d = MOON_DIR
  const moon = new THREE.DirectionalLight(new THREE.Color(...MOONLIGHT_COL), MOONLIGHT)
  moon.position.set(d[0] * 40 + 3, d[1] * 40 + 3, d[2] * 40)
  moon.target.position.set(3, 3, 0)
  moon.castShadow = true
  moon.shadow.mapSize.set(2048, 2048)
  const cam = moon.shadow.camera
  cam.left = -14
  cam.right = 14
  cam.top = 14
  cam.bottom = -14
  cam.near = 8
  cam.far = 80
  moon.shadow.bias = -0.0004
  moon.shadow.normalBias = 0.02
  moon.shadow.radius = 12
  moon.shadow.intensity = 0.8
  w.addLight(moon)
  w.scene.add(moon.target)

  // thin-surface translucency: moon through the blinds, night sky ambience
  backlight.dirToSun.value.set(d[0], d[1], d[2])
  backlight.sunColor.value.setRGB(
    MOONLIGHT_COL[0] * MOONLIGHT * 0.3,
    MOONLIGHT_COL[1] * MOONLIGHT * 0.3,
    MOONLIGHT_COL[2] * MOONLIGHT * 0.3,
  )
  backlight.skyAmb.value.setRGB(ibl.avg[0] * 0.5, ibl.avg[1] * 0.5, ibl.avg[2] * 0.5)
}
