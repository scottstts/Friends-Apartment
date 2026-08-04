/** Assemble every door and window into the shell - port of build_openings.py. */
import type * as THREE from 'three/webgpu'
import * as L from './L'
import * as mlib from '../../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mats from '../../mats/mats'
import * as O from './sopenings'
import type { MatSet } from './shell'
import type { World } from '../../core/world'

function rad(d: number): number {
  return (d * Math.PI) / 180
}

function swingLeaf(
  w: World,
  width: number,
  h: number,
  hinge: [number, number],
  closedDir: [number, number],
  angle: number,
  M: MatSet,
  leafMat: THREE.Material,
  t = 0.042,
  rows: number[] = [0.3, 0.3, 0.2, 0.2],
): void {
  const leaf = O.panelDoor(width, h, t, rows, 0.11, 0.12, 0.082)
  mlib.rotateZ(leaf, Math.PI / 2)
  mlib.translate(leaf, [0.0, width / 2, 0.01])
  const knobs: MeshData[] = []
  for (const [sx, ang] of [
    [0.004, Math.PI / 2],
    [-t - 0.004, -Math.PI / 2],
  ] as [number, number][]) {
    const kn = O.knobSet()
    mlib.rotateZ(kn, ang)
    mlib.translate(kn, [sx, width - 0.125, 1.0])
    knobs.push(kn)
  }
  const base = Math.atan2(closedDir[1], closedDir[0]) - Math.PI / 2
  const theta = base - rad(angle)
  mlib.rotateZ(leaf, theta)
  mlib.translate(leaf, [hinge[0], hinge[1], 0.0])
  w.add(leaf, leafMat)
  for (const kn of knobs) {
    mlib.rotateZ(kn, theta)
    mlib.translate(kn, [hinge[0], hinge[1], 0.0])
    w.add(kn, M.brass)
  }
  // collider for the standing-open leaf
  const ax = -Math.sin(theta)
  const ay = Math.cos(theta)
  w.obb(hinge[0] + (ax * width) / 2, hinge[1] + (ay * width) / 2, width / 2, t / 2 + 0.01, Math.atan2(ay, ax))
}

export function mkMats(): MatSet {
  const M: MatSet = {}
  M.door_purple = mats.paint('paint_door_purple', L.DOOR_PURPLE, { rough: 0.3, coat: 0.3, variation: 0.02 })
  M.trim = mats.get('paint_lav_trim') ?? mats.paint('paint_lav_trim', L.LAV_TRIM)
  M.turq = mats.paint('paint_turquoise', L.TURQ, { rough: 0.3, coat: 0.22 })
  M.green_door = mats.paint('paint_green_door', L.GREEN_DOOR, { rough: 0.28, coat: 0.25 })
  M.gold = mats.paint('paint_gold_frame', L.GOLD, { rough: 0.34, coat: 0.3 })
  M.brass = mats.metal('metal_brass', 'B08D3A', { rough: 0.22, bump: 0.05 })
  M.chrome = mats.metal('metal_chrome', 'D8DCE0', { rough: 0.1, bump: 0.02 })
  M.steel_dk = mats.metal('metal_steel_dark', '3A322C', { rough: 0.34, bump: 0.06 })
  M.glass = mats.pane('glass_clear', { rough: 0.018, baseAlpha: 0.05, edge: 0.62 })
  M.glass_frost = mats.pane('glass_frosted', { tint: 'E4E8E2', rough: 0.5, baseAlpha: 0.8, edge: 0.18, bumpn: 280.0 })
  M.glass_dark = mats.pane('glass_dark', { tint: '2C2F36', rough: 0.06, baseAlpha: 0.62, edge: 0.34 })
  M.stone = mats.plaster('stone_sill', '8D897E', { rough: 0.62, bump: 0.5, scale: 48 })
  M.blind = mats.wood('blind_matchstick', ['DCC096', 'D3B78C', 'C9AC82'], {
    ring: 24.0,
    warp: 0.004,
    warpScale: 3.0,
    distort: 0.04,
    blotch: 0.16,
    bump: 0.2,
    rough: [0.52, 0.7],
    aniso: 0.0,
    axis: 'YZ',
    translucent: 0.34,
    grainRelief: 0.05,
  })
  return M
}

/** Radius of the superellipse |x/a|^n + |z/b|^n = 1 along a ray. */
function supR(th: number, a: number, b: number, n: number): number {
  const c = Math.cos(th)
  const s = Math.sin(th)
  return (Math.abs(c / a) ** n + Math.abs(s / b) ** n) ** (-1.0 / n)
}

// ---- the peephole surround, measured off ref_images/decoration.png ------
// Everything here is in REFERENCE PIXELS of that image with the origin at the
// centre of the opening, +X right, +Z up: outer 341 x 361, opening 188 x 223.
const PF_AW = 96.0 // opening half-width / half-height
const PF_AH = 114.0
const PF_APN = 7.0 // opening is a superellipse: straight sides
const PF_CMAX = 0.5 ** (1.0 / PF_APN) // ...so this is |x|/AW on its diagonal
// How far the moulding stands out from the opening, round the loop: widest at
// the middle of each side, cut back towards the diagonals where the curls
// take the outline over.  Cutting on min(|x|/AW, |z|/AH) rather than on the
// polar angle keeps the sides' bulge broad and flat the way the reference's
// is, and it has to bite hard enough that the rail's outer edge actually
// falls away towards a corner - a gentler taper leaves the outline widening
// all the way in and the whole thing comes out a circle.  40 at 1.7 holds
// each side flat and then pinches, which squares the outline off and opens
// the notch in front of each curl.
const PF_BW_TB = 69.5 // 69.5 top and bottom, 74 at the sides
const PF_BW_EX = 4.5
const PF_BW_CUT = 38.0
const PF_BW_CP = 1.7
// min() of the two has a kink exactly on the diagonal, and since the whole
// section is scaled by the rail's width that kink draws a dead-straight
// crease diagonally across each corner.  Round the min off over this much.
const PF_BW_SM = 0.3
// The rail's section, in fractions of its width.  It is ONE solid band with
// a flat top, a crown over each of its three lobes, and narrow grooves cut
// into it - not three rolls laid side by side: built up out of rolls the
// rail comes out as thin separate arcs with bare bed showing between them.
// Three grooves, four lobes - the reference's middle crease is the shallow
// one.  The crowns are deliberately slight next to the grooves' depth: the
// rail has to read as a flat drapery creased by fold lines, not a row of
// tubes with the silhouette rolling over far too softly.
const PF_BAND_H = 14.5 // height, and how flat the top is
const PF_BAND_P = 8.0
// The folds are not evenly spaced: they bunch towards the outer edge, so the
// lobe against the opening is the broad one and they narrow outwards.
// Spacing them evenly reads as knitting rather than gathered drapery.
const PF_LOBES: [number, number, number][] = [
  [0.15, 0.15, 2.0],
  [0.43, 0.13, 2.2],
  [0.66, 0.1, 2.2],
  [0.885, 0.115, 2.0],
]
const PF_GROOVES: [number, number, number][] = [
  [0.3, 0.055, 7.0],
  [0.565, 0.05, 6.0],
  [0.76, 0.05, 6.5],
]
const PF_GROOVE_P = 0.7 // narrow and steep-sided, not a dish
const PF_BLEND = 2.0 // px the curls run into the rails over
// Keep that small.  Widened, the rounding piles up where the rail and BOTH
// curls of a corner are all in play at once and raises a flat wedge there.
// The eight curls.  Every one is the same size, and the two on a corner are
// each other reflected in that corner's axis, so a corner reads symmetrically
// however the frame's own proportions fall.  The axis is a degree or two off
// the true diagonal because the frame is taller than it is wide: that is
// what lands the pair's reach on 0.945, the outer proportion the reference
// has.  They stand a little proud of the rails at both extremes, so each
// corner reads as its own bump.  Same idea as the rail: a solid domed lobe
// with a spiral groove cut across it, which leaves the rolled ribbon between
// the wraps standing - a raised spiral instead just reads as wire on a blob.
const PF_VOL_AXIS = 132.7 // deg, the top-left corner's axis
const PF_VOL_MID = 186.0 // the pair's centre, out along that axis
const PF_VOL_SEP = 23.0 // and half their step across it
const PF_VOL_R = 32.0
const PF_VOL_END = -10.0 // where the rail runs into the curl
//                        turns  r0   rmax  gw   GD   CR   HB    re   Ae
const PF_VOL_CUT = [1.25, 4.0, 26.0, 4.2, 8.0, 3.5, 16.0, 6.5, 4.5] as const

/** The gold rococo surround round the peephole on Monica's door.
 *
 * Built the way the prop is actually made - as ONE moulded piece.  It is not
 * an assembly of tubes: on the reference each side and the two curls at its
 * ends are a single continuous mass, and the ridges running along it are
 * creases in that mass, not gaps between separate rods.
 *
 * So the shape is described as a relief - a height above the door face - and
 * then meshed in one go as a single quad ring:
 *
 *   - round the opening, a solid band with a flat top and a rolled edge at
 *     either side, crowned over three lobes and cut with two grooves.  It is
 *     widest at the middle of each side and pinched towards the corners,
 *     which both bulges the outline between the corners and squares it off.
 *   - at each corner a pair of volutes, one ending each rail: a domed lobe
 *     with an Archimedean spiral groove cut across it and a boss in its eye,
 *     so what stands proud is the rolled ribbon between the wraps.
 *
 * The mass is the upper envelope of all of that, so nothing is a seam.
 * Built in XZ with +Y out of the door, matching what place() expects.
 * w x h is the outer size. */
function peepholeFrame(w: number, h: number): MeshData {
  const TAU = Math.PI * 2
  const pmod = (x: number, m: number): number => ((x % m) + m) % m

  const bandW = (th: number): number => {
    const r = supR(th, PF_AW, PF_AH, PF_APN)
    const u = Math.abs(r * Math.cos(th)) / PF_AW
    const v = Math.abs(r * Math.sin(th)) / PF_AH
    const e = Math.max(0.0, 1.0 - Math.abs(u - v) / PF_BW_SM)
    const c = (Math.min(u, v) - 0.25 * PF_BW_SM * e * e) / PF_CMAX
    return PF_BW_TB + PF_BW_EX * Math.cos(th) ** 2 - PF_BW_CUT * Math.max(c, 0.0) ** PF_BW_CP
  }

  /** The moulding, measured out from the opening along the ray.  Radial
   * rather than normal to the opening: on a superellipse this near a
   * rectangle the two differ by under a degree, and doing it the other way
   * costs a search per sample. */
  const railH = (r: number, th: number): number => {
    const bw = bandW(th)
    const t = (r - supR(th, PF_AW, PF_AH, PF_APN)) / bw
    if (t <= 0.0 || t >= 1.0) return 0.0
    const k = bw / 71.0 // the section thins with the rail
    let y = PF_BAND_H * Math.sqrt(1.0 - (2.0 * t - 1.0) ** PF_BAND_P)
    for (const [c, hw, amp] of PF_LOBES) {
      const q = (t - c) / hw
      if (q > -1.0 && q < 1.0) y += amp * Math.sqrt(1.0 - q * q)
    }
    for (const [c, hw, d] of PF_GROOVES) {
      const q = (t - c) / hw
      if (q > -1.0 && q < 1.0) y -= d * (1.0 - q * q) ** PF_GROOVE_P
    }
    return Math.max(y, 0.0) * k
  }

  // the curls: one pair built on the top-left corner's axis, then mirrored
  // out to the other three.  Reflecting a spiral turns it over, so the
  // handedness and the start angle travel with it - which is also how the
  // second curl of each pair is made from the first.
  const ax = rad(PF_VOL_AXIS)
  const ux = Math.cos(ax)
  const uz = Math.sin(ax)
  const qx = Math.sin(ax)
  const qz = -Math.cos(ax)
  const [turns, r0, rmax, gw, GD, CR, HB, re, Ae] = PF_VOL_CUT
  const K = (rmax - r0) / turns
  const U = TAU * turns
  const R = PF_VOL_R
  const vols: [number, number, number, number][] = []
  for (const sgn of [1.0, -1.0]) {
    const ex = PF_VOL_MID * ux + sgn * PF_VOL_SEP * qx
    const ez = PF_VOL_MID * uz + sgn * PF_VOL_SEP * qz
    let te = rad(PF_VOL_END)
    let hand = 1.0
    if (sgn < 0.0) {
      // the side rail's curl, mirrored
      te = 2.0 * ax - te
      hand = -hand
    }
    for (const sx of [-1.0, 1.0]) {
      for (const sz of [-1.0, 1.0]) {
        let t = te
        let hd = hand
        if (sx > 0.0) {
          // mirrored in X off the top-left
          t = Math.PI - t
          hd = -hd
        }
        if (sz < 0.0) {
          // ...and in Z
          t = -t
          hd = -hd
        }
        vols.push([sx * Math.abs(ex), sz * Math.abs(ez), t - hd * U, hd])
      }
    }
  }

  const volH = (x: number, z: number, V: [number, number, number, number]): number => {
    const [ex, ez, th0, hd] = V
    const dx = x - ex
    const dz = z - ez
    const d2 = dx * dx + dz * dz
    if (d2 >= R * R) return 0.0
    const d = Math.sqrt(d2)
    let y = HB * Math.sqrt(1.0 - (d / R) ** 3)
    // Where this point sits on the spiral: g counts wraps out from the eye,
    // so it lands on a whole number exactly on a groove and halfway between
    // two of them at the middle of a ribbon.  Working in that coordinate
    // crowns the ribbon as well as cutting the groove, which is what makes a
    // curl read as coiled rope instead of a flat disc with a scratch in it.
    // psi's wrap shifts g by exactly one turn, so its fraction - all the
    // section depends on - runs on through.
    const psi = pmod(hd * (Math.atan2(dz, dx) - th0), TAU)
    const g = (d - r0) / K - psi / TAU
    let f = Math.min((g + 0.3) / 0.4, (turns + 0.3 - g) / 0.4) // fade at the ends
    if (f > 0.0) {
      f = Math.min(f, 1.0)
      const fr = g - Math.floor(g)
      y += f * CR * Math.sin(Math.PI * fr) ** 1.4
      const dd = Math.min(fr, 1.0 - fr) * K
      if (dd < gw) y -= f * GD * (1.0 - (dd / gw) ** 2) ** PF_GROOVE_P
    }
    if (d < re) y += Ae * Math.sqrt(1.0 - (d / re) ** 2) // the boss in the eye
    return Math.max(y, 0.0)
  }

  const field = (x: number, z: number): number => {
    const r = Math.hypot(x, z)
    let y = r > 1e-6 ? railH(r, Math.atan2(z, x)) : 0.0
    for (const V of vols) {
      const v = volH(x, z, V)
      // A rounded max, not a plain one: taken flat it leaves a hard crease
      // everywhere a curl crosses its rail, and on the reference the two run
      // into one another.  The grooves are cut by subtraction rather than by
      // this, so rounding here softens the joins without touching them.
      // The rounding width has to fall away with the smaller of the two, or
      // it adds height out where BOTH are zero and the whole silhouette
      // inflates into a disc.
      const k = Math.min(PF_BLEND, v, y)
      const d = k > 0.0 ? k - Math.abs(v - y) : 0.0
      y = Math.max(v, y) + (d > 0.0 ? (d * d) / (4.0 * k) : 0.0)
    }
    return y
  }

  // ---- mesh it as one ring ------------------------------------------
  // For each ray out of the centre, find where the mass ends, then lay a row
  // of samples from the opening out to there.  The relief is zero at both,
  // so the ring closes onto the door of its own accord.
  const NU = 864
  const NV = 48
  const EPS = 0.05
  const cols: [number, number, number, number][] = []
  for (let i = 0; i < NU; i++) {
    const th = (TAU * i) / NU
    const ct = Math.cos(th)
    const st = Math.sin(th)
    const rIn = supR(th, PF_AW, PF_AH, PF_APN)
    const step = 2.0
    let lo = rIn
    let r = rIn + 2.0
    while (r < 240.0) {
      // last radius still carrying mass
      if (field(r * ct, r * st) > EPS) lo = r
      r += step
    }
    let hi = lo + step
    for (let b = 0; b < 20; b++) {
      // then close on the edge
      const m = 0.5 * (lo + hi)
      if (field(m * ct, m * st) > EPS) lo = m
      else hi = m
    }
    cols.push([ct, st, rIn, lo])
  }
  // Smooth the outline before laying rows on it.  Every row runs radially
  // from the opening out to this boundary, so wherever the boundary steps -
  // and it steps by 40-odd px where a curl's arc gives way to the rail's
  // edge - neighbouring rows are stretched by very different amounts and the
  // shear between them shows as a straight crease running inwards.
  // Spreading the step over a handful of columns takes that out; it costs a
  // little of the notch in front of each curl, which is worth it.
  let outs = cols.map((c) => c[3])
  for (let p = 0; p < 3; p++) {
    const prev = outs
    outs = prev.map(
      (_, i) =>
        0.0625 * prev[(i - 2 + NU) % NU] +
        0.25 * prev[(i - 1 + NU) % NU] +
        0.375 * prev[i] +
        0.25 * prev[(i + 1) % NU] +
        0.0625 * prev[(i + 2) % NU],
    )
  }

  const grid: [number, number, number][][] = []
  for (let i = 0; i < NU; i++) {
    const [ct, st, rIn] = cols[i]
    const rOut = outs[i]
    const col: [number, number, number][] = []
    for (let j = 0; j <= NV; j++) {
      const r = rIn + ((rOut - rIn) * j) / NV
      const x = r * ct
      const z = r * st
      col.push([x, z, field(x, z)])
    }
    col[0][2] = 0.0
    col[NV][2] = 0.0
    grid.push(col)
  }
  // take the edge off - a straight envelope is a shade too crisp for
  // something cast in a mould and then painted.
  const relief = grid.map((col) => col.map((c) => c[2]))
  for (let i = 0; i < NU; i++) {
    const a = grid[(i - 1 + NU) % NU]
    const b = grid[(i + 1) % NU]
    for (let j = 1; j < NV; j++) {
      relief[i][j] = 0.72 * grid[i][j][2] + 0.07 * (a[j][2] + b[j][2]) + 0.07 * (grid[i][j - 1][2] + grid[i][j + 1][2])
    }
  }
  for (let i = 0; i < NU; i++) for (let j = 1; j < NV; j++) grid[i][j][2] = relief[i][j]

  // Scale off what actually got built rather than off a nominal outer size:
  // the curls set the silhouette, and they move whenever their placement is
  // touched.
  let ox = 0.0
  let oz = 0.0
  for (const col of grid) {
    for (const c of col) {
      ox = Math.max(ox, Math.abs(c[0]))
      oz = Math.max(oz, Math.abs(c[1]))
    }
  }
  const SX = (0.5 * w) / ox
  const SZ = (0.5 * h) / oz
  const SY = 0.5 * (SX + SZ)
  const verts: Vec3[] = []
  const faces: number[][] = []
  for (const col of grid) for (const [x, z, y] of col) verts.push([x * SX, y * SY, z * SZ])
  const W = NV + 1
  for (let i = 0; i < NU; i++) {
    const i2 = (i + 1) % NU
    for (let j = 0; j < NV; j++) faces.push([i * W + j, i2 * W + j, i2 * W + j + 1, i * W + j + 1])
    // the back, flat on the door and never seen
    faces.push([i2 * W, i * W, i * W + NV, i2 * W + NV])
  }
  const ob = MeshData.from(verts, faces)
  mlib.recalcNormals(ob)
  // 70, not the usual 32: the grooves' flanks are steeper than that and get
  // marked sharp, which draws a hard line down the middle of every crease.
  // Only the silhouette, where the relief meets its own back at a right
  // angle, should stay sharp.
  mlib.smoothShade(ob, 70)
  return ob
}

/** A back plate lying flat on a face: outline in (x, z), standing off in Y. */
function lockPlate(pw: number, ph: number, r: number, y0: number, y1: number, seg = 4): MeshData {
  return mlib.prismXZ(mlib.roundedRect(pw, ph, r, seg), y0, y1)
}

/** Anything turned - a knob, a collar, a screw head - with its axis out of
 * the face it is mounted on. */
function lockTurn(prof: Vec2[], at: Vec3, seg = 20): MeshData {
  const ob = mlib.revolve(prof, seg)
  mlib.rotX(ob, -Math.PI / 2)
  mlib.translate(ob, at)
  return ob
}

/** A barrel bolt lying across the stile: back plate, two guide straps, the
 * bolt running through them towards the door edge, and a thumb tab on it.
 * The old one was a bare rounded slab with no bolt on it at all. */
function surfaceBolt(mat: THREE.Material): [MeshData, THREE.Material][] {
  const P: MeshData[] = [lockPlate(0.1, 0.032, 0.007, 0.0, 0.005)]
  for (const gx of [-0.03, 0.024]) {
    // the two guide straps
    const g = lockPlate(0.013, 0.026, 0.004, 0.005, 0.0165, 2)
    mlib.translate(g, [gx, 0.0, 0.0])
    P.push(g)
  }
  // the bolt, shot to within a few mm of the leaf's edge
  P.push(
    mlib.tubeAlong(
      [
        [-0.064, 0.0107, 0.0],
        [0.036, 0.0107, 0.0],
      ],
      mlib.circle(0.0055, 14),
      { up: [0, 0, 1] },
    ),
  )
  // a flat lug to throw it by - a turned knob here reads as a third lock
  P.push(lockPlate(0.011, 0.019, 0.005, 0.015, 0.0194, 3))
  const screw: Vec2[] = [
    [0.0, 0.0],
    [0.003, 0.0],
    [0.003, 0.0012],
    [0.0017, 0.0021],
    [0.0, 0.0023],
  ]
  for (const [sx, sz] of [
    [-0.043, 0.0],
    [0.043, 0.0],
  ] as [number, number][]) {
    P.push(lockTurn(screw, [sx, 0.005, sz], 10))
  }
  const ob = mlib.join(P)
  mlib.smoothShade(ob, 34)
  return [[ob, mat]]
}

/** The door half of a security chain: the track its ball-end runs in, with
 * the round pocket at the open end that the ball drops into. */
function chainSlide(mat: THREE.Material, dark: THREE.Material): [MeshData, THREE.Material][] {
  const P: MeshData[] = [lockPlate(0.086, 0.024, 0.011, 0.0, 0.0048)]
  const screw: Vec2[] = [
    [0.0, 0.0],
    [0.0028, 0.0],
    [0.0028, 0.0011],
    [0.0016, 0.002],
    [0.0, 0.0022],
  ]
  for (const sx of [-0.036, 0.036]) P.push(lockTurn(screw, [sx, 0.0048, 0.0], 10))
  const ob = mlib.join(P)
  mlib.smoothShade(ob, 34)
  // the slot, and the pocket at the door-edge end of it
  const sl = mlib.prismXZ(mlib.roundedRect(0.05, 0.008, 0.004, 3), 0.0, 0.0052)
  mlib.translate(sl, [0.008, 0.0, 0.0])
  const pk = mlib.prismXZ(mlib.circle(0.0072, 14), 0.0, 0.0052)
  mlib.translate(pk, [-0.02, 0.0, 0.0])
  const slot = mlib.join([sl, pk])
  return [
    [ob, mat],
    [slot, dark],
  ]
}

/** One link, lying in a plane that contains the vertical so it hangs, and
 * turned across its neighbours the way a chain actually runs. */
function chainLink(c: Vec3, R: number, r: number, across: boolean): MeshData {
  const angles = Array.from({ length: 12 }, (_, k) => (Math.PI * 2 * k) / 12)
  let path: Vec3[]
  let up: Vec3
  if (across) {
    path = angles.map((t) => [c[0], c[1] + R * Math.cos(t), c[2] + R * Math.sin(t)] as Vec3)
    up = [1.0, 0.0, 0.0]
  } else {
    path = angles.map((t) => [c[0] + R * Math.cos(t), c[1], c[2] + R * Math.sin(t)] as Vec3)
    up = [0.0, 1.0, 0.0]
  }
  return mlib.tubeAlong(path, mlib.circle(r, 6), { closePath: true, up })
}

/** The jamb half: the anchor plate, and the chain hanging slack off it with
 * its ball-end swinging free - the door is shut but not chained, which is
 * how the set photo has it.  The old chain was one smooth bent tube. */
function chainAnchor(mat: THREE.Material, links = 12): [MeshData, THREE.Material][] {
  const P: MeshData[] = [lockPlate(0.026, 0.052, 0.007, 0.0, 0.005, 3)]
  const screw: Vec2[] = [
    [0.0, 0.0],
    [0.0028, 0.0],
    [0.0028, 0.0011],
    [0.0016, 0.002],
    [0.0, 0.0022],
  ]
  for (const sz of [-0.018, 0.018]) P.push(lockTurn(screw, [0.0, 0.005, sz], 10))
  const R = 0.0062
  const r = 0.0017
  const pitch = 0.0088
  const x0 = 0.0
  const y0 = 0.0088
  const z0 = -0.022
  for (let k = 0; k < links; k++) {
    const t = k / (links - 1)
    P.push(chainLink([x0, y0 + 0.006 * t, z0 - pitch * k], R, r, k % 2 === 1))
  }
  // the ball on the free end that runs in the track
  const bl = mlib.revolve(
    [
      [0.0, -0.0072],
      [0.0042, -0.006],
      [0.0058, -0.0022],
      [0.0058, 0.0022],
      [0.0042, 0.006],
      [0.0, 0.0072],
    ],
    12,
  )
  mlib.translate(bl, [x0, y0 + 0.006, z0 - pitch * (links - 0.6)])
  P.push(bl)
  const ob = mlib.join(P)
  mlib.smoothShade(ob, 40)
  return [[ob, mat]]
}

export function build(w: World, M?: MatSet): MatSet {
  M = M ?? mkMats()

  // ============================================================ FRONT DOOR
  {
    const width = L.FD_Y[1] - L.FD_Y[0]
    const top = L.FD_TOP
    const cy = (L.FD_Y[0] + L.FD_Y[1]) * 0.5
    const jambT = 0.024
    const ln = O.lining(width, top, L.TW, jambT)
    O.place(ln, [0.0, cy, 0.0], [0, 1], [-1, 0])
    w.add(ln, M.trim)
    const cs = O.casing(width, top, 0.1, 0.026)
    O.place(cs, [0.0, cy, 0.0], [0, 1], [1, 0])
    w.add(cs, M.trim)
    const cs2 = O.casing(width, top, 0.07, 0.016)
    O.place(cs2, [-L.TW, cy, 0.0], [0, 1], [-1, 0])
    w.add(cs2, M.trim)
    // transom: head rail + sash
    // ...between the linings, not across the whole rough opening: full width
    // it sits inside both jambs and the shared faces flicker at the two top
    // corners.  The transom above already sizes itself this way.
    const hw = width / 2 - jambT
    const hr = mlib.box(-hw, 0.0, L.FD_H, hw, L.TW, L.FD_H + 0.075)
    O.place(hr, [0.0, cy, 0.0], [0, 1], [-1, 0])
    w.add(hr, M.trim)
    // ...and clear of the head lining as well as the jambs.  Run to the full
    // height of the rough opening its top rail sits inside the lining's head,
    // and the shared faces flicker in a stripe right across the transom.
    const [tf, tg] = O.steelWindow(width - 2 * jambT, top - jambT - L.FD_H - 0.085, [1], 1, {
      frameW: 0.048,
      frameD: 0.055,
      colsPerBay: 1,
      glassBack: 0.008,
    })
    for (const [o, mm] of [
      [tf, M.trim],
      [tg, M.glass_dark],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.FD_H + 0.085])
      O.place(o, [0.0, cy, 0.0], [0, 1], [-1, 0])
      w.add(o, mm)
    }
    // leaf
    const lw = width - 0.055
    const lh = L.FD_H - 0.03
    const leaf = O.flushDoor(lw, lh, 0.044)
    mlib.translate(leaf, [0, 0.075, 0.012])
    O.place(leaf, [0.0, cy, 0.0], [0, 1], [-1, 0])
    w.add(leaf, M.door_purple)
    // the yellow frame + peephole boss + hardware (all on the leaf face)
    const fx = -0.075
    // The gold frame is the one thing everyone knows about this door, and a
    // mitred rectangle is not it.  The prop is a moulded rococo surround with
    // a pair of volutes on every corner and a reeded rail between them; see
    // peepholeFrame.  300 x 318 is the reference's own outer proportion.
    const fr = peepholeFrame(0.3, 0.3178)
    O.place(fr, [fx, cy, 1.545], [0, 1], [1, 0])
    w.add(fr, M.gold)
    // ...and the spyhole belongs in the middle of it.  It was moved out above
    // the frame back when the frame was a plain rectangle with nothing to say
    // about where it sat; the frame is hung *around* the spyhole on the set.
    const ph = mlib.revolve(
      [
        [0.0, 0.0],
        [0.009, 0.0],
        [0.009, 0.006],
        [0.005, 0.008],
        [0.0, 0.008],
      ],
      16,
    )
    mlib.rotX(ph, -Math.PI / 2)
    O.place(ph, [fx, cy, 1.545], [0, 1], [1, 0])
    w.add(ph, M.brass)
    // knocker: back-plate and ring
    const kp = mlib.revolve(
      [
        [0.0, 0.0],
        [0.034, 0.0],
        [0.034, 0.007],
        [0.026, 0.013],
        [0.0, 0.015],
      ],
      24,
    )
    mlib.rotX(kp, -Math.PI / 2)
    mlib.smoothShade(kp, 40)
    O.place(kp, [fx, cy, 1.29], [0, 1], [1, 0])
    w.add(kp, M.brass)
    const ring = mlib.tubeAlong(
      Array.from({ length: 20 }, (_, k) => {
        const a = (k * Math.PI * 2) / 20
        return [0.03 * Math.cos(a), 0.03 * Math.sin(a), 0.0] as [number, number, number]
      }),
      mlib.circle(0.0055, 8),
      { closePath: true },
    )
    mlib.rotX(ring, -Math.PI / 2)
    mlib.translate(ring, [0.0, 0.0, -0.036])
    mlib.smoothShade(ring, 38)
    O.place(ring, [fx + 0.013, cy, 1.29], [0, 1], [1, 0])
    w.add(ring, M.brass)
    const kn = O.knobSet()
    O.place(kn, [fx, L.FD_Y[0] + 0.11, 1.0], [0, 1], [1, 0])
    w.add(kn, M.brass)
    // Three fittings up the latch stile and no more, top to bottom: the
    // security chain, the bolt, and the knob - which is exactly what the set
    // photo has.  Only ONE of them is a knob you turn; every escutcheon added
    // beyond these just puts another brass disc on the stile.
    const ly = L.FD_Y[0]
    for (const [ob, mm] of chainSlide(M.chrome, M.steel_dk)) {
      O.place(ob, [fx, ly + 0.08, 1.585], [0, 1], [1, 0])
      w.add(ob, mm)
    }
    // ...the chain itself hangs off the reveal, not off the leaf: a chain
    // with both ends on the door is the thing that made this stack read as
    // nonsense.  On the lining's face, not on the rough opening - the reveal
    // is lined, so the jamb you can actually screw into is a jambT in.  Hung
    // off ly it ends up buried inside the lining and invisible.
    for (const [ob, mm] of chainAnchor(M.chrome)) {
      O.place(ob, [-0.045, ly + jambT, 1.585], [1, 0], [0, 1])
      w.add(ob, mm)
    }
    for (const [ob, mm] of surfaceBolt(M.brass)) {
      O.place(ob, [fx, ly + 0.085, 1.265], [0, 1], [1, 0])
      w.add(ob, mm)
    }
  }

  // ========================================================= KITCHEN WINDOW
  {
    const { dir, len: cl } = L.chamferDir()
    const [dxc, dyc] = dir
    const kw = L.KW_U[1] - L.KW_U[0]
    const kh = L.KW_Z[1] - L.KW_Z[0]
    const kc = L.chamferPt((L.KW_U[0] + L.KW_U[1]) * 0.5, 0.0)
    const inw: [number, number] = [dyc, -dxc]
    const kl = O.lining(kw, kh, L.TW, 0.022)
    O.place(kl, [kc[0], kc[1], L.KW_Z[0]], [dxc, dyc], [-inw[0], -inw[1]])
    w.add(kl, M.turq)
    const kcs = O.casing(kw, kh, 0.105, 0.022, 4)
    mlib.translate(kcs, [0, 0, -kh * 0.5])
    O.place(kcs, [kc[0], kc[1], L.KW_Z[0] + kh * 0.5], [dxc, dyc], inw)
    w.add(kcs, M.turq)
    const [kf, kg] = O.steelWindow(kw - 0.03, kh - 0.03, [1], 4, {
      frameW: 0.05,
      frameD: 0.062,
      munW: 0.026,
      munD: 0.03,
      colsPerBay: 2,
      glassBack: 0.014,
    })
    for (const [o, mm] of [
      [kf, M.turq],
      [kg, M.glass],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.KW_Z[0] + 0.015])
      O.place(o, [kc[0], kc[1], 0.0], [dxc, dyc], [-inw[0], -inw[1]])
      w.add(o, mm)
    }
    const sl = mlib.box(-kw / 2 - 0.05, 0.0, -0.05, kw / 2 + 0.05, 0.18, 0.0)
    mlib.bevel(sl, 0.006, 2)
    O.place(sl, [kc[0], kc[1], L.KW_Z[0]], [dxc, dyc], [-inw[0], -inw[1]])
    w.add(sl, M.stone)
    void cl
  }

  // ============================================================ HUGE WINDOW
  {
    const bw = L.BW_X[1] - L.BW_X[0]
    const bcx = (L.BW_X[0] + L.BW_X[1]) * 0.5
    const slopeLen = (L.BW_HEAD - L.BW_SILL) / Math.cos(L.BW_TILT)
    const [bf, bg] = O.steelWindow(bw - 0.02, slopeLen - 0.01, [1, 1.15, 1], 7, {
      frameW: 0.068,
      frameD: 0.075,
      mullW: 0.055,
      munW: 0.026,
      munD: 0.032,
      colsPerBay: 2,
      glassBack: 0.018,
    })
    for (const [o, mm] of [
      [bf, M.steel_dk],
      [bg, M.glass],
    ] as [MeshData, THREE.Material][]) {
      // One continuous near-vertical window; its head leans south into the room.
      mlib.rotX(o, L.BW_TILT)
      O.place(o, [bcx, 0.0, 0.0], [1, 0], [0, 1])
      mlib.translate(o, [0, L.AL_Y[1] - 0.008, L.BW_SILL + 0.006])
      w.add(o, mm)
    }
    // Triangular plaster reveals close the leaned glazing at each jamb.
    for (const [a, b] of [
      [L.BW_X[0] - 0.075, L.BW_X[0] + 0.012],
      [L.BW_X[1] - 0.012, L.BW_X[1] + 0.075],
    ] as [number, number][]) {
      w.add(
        mlib.prismYZ(
          [
            [L.NYW, L.BW_SILL],
            [L.NYW, L.BW_HEAD],
            [L.NYW - L.BW_LEAN, L.BW_HEAD],
          ],
          a,
          b,
        ),
        mats.get('wall_lavender')!,
      )
    }
    // stone sill inside + out
    const si = mlib.box(L.BW_X[0] - 0.06, L.AL_Y[1] - 0.02, L.BW_SILL - 0.055, L.BW_X[1] + 0.06, L.AL_Y[1] + L.TW + 0.1, L.BW_SILL)
    mlib.bevel(si, 0.008, 2)
    w.add(si, M.stone)
    // Matchstick blinds hang down the upper half of the single leaned window.
    const PITCH = 0.0175
    const SLAT = 0.0128
    const THK = 0.0075
    const spans: [number, number][] = [
      [L.BW_X[0] + 0.03, L.BW_X[0] + bw / 3 - 0.02],
      [L.BW_X[0] + bw / 3 + 0.02, L.BW_X[0] + (2 * bw) / 3 - 0.02],
      [L.BW_X[0] + (2 * bw) / 3 + 0.02, L.BW_X[1] - 0.03],
    ]
    spans.forEach(([a, b], i) => {
      const t = i !== 1 ? 0.5 : 0.58
      const uy = Math.sin(L.BW_TILT)
      const uz = -Math.cos(L.BW_TILT)
      const ny = uz
      const nz = -uy
      const y0 = L.NYW - L.BW_LEAN + ny * 0.055
      const z0 = L.BW_HEAD - 0.055
      const run = slopeLen * t
      const slats: MeshData[] = []
      const n = Math.max(2, Math.floor(run / PITCH))
      for (let k = 0; k < n; k++) {
        const s0 = k * PITCH
        const s1 = Math.min(s0 + SLAT, run)
        const quad: [number, number][] = []
        for (const [s, o] of [
          [s0, -THK / 2],
          [s1, -THK / 2],
          [s1, THK / 2],
          [s0, THK / 2],
        ] as [number, number][]) {
          quad.push([y0 + uy * s + ny * o, z0 + uz * s + nz * o])
        }
        slats.push(mlib.prismYZ(quad, a, b))
      }
      for (const [s, hh] of [
        [-0.012, 0.026],
        [run + 0.004, 0.03],
      ] as [number, number][]) {
        const quad: [number, number][] = [
          [y0 + uy * s + ny * -0.011, z0 + uz * s + nz * -0.011],
          [y0 + uy * (s + hh) + ny * -0.011, z0 + uz * (s + hh) + nz * -0.011],
          [y0 + uy * (s + hh) + ny * 0.011, z0 + uz * (s + hh) + nz * 0.011],
          [y0 + uy * s + ny * 0.011, z0 + uz * s + nz * 0.011],
        ]
        slats.push(mlib.prismYZ(quad, a, b))
      }
      w.add(mlib.join(slats), M.blind)
    })
  }

  // ================= BATHROOM DOOR (hallway west wall, faces east) ========
  {
    const bdw = L.BD_Y[1] - L.BD_Y[0]
    const bdc = (L.BD_Y[0] + L.BD_Y[1]) * 0.5
    const bl = O.lining(bdw, L.BD_H, 0.16, 0.022)
    O.place(bl, [L.HALL_X[0], bdc, 0.0], [0, -1], [-1, 0])
    w.add(bl, M.trim)
    const bcs = O.casing(bdw, L.BD_H, 0.09, 0.022)
    O.place(bcs, [L.HALL_X[0], bdc, 0.0], [0, -1], [1, 0])
    w.add(bcs, M.trim)
    // Pivot on the jamb arris so the leaf can stand back against its own wall;
    // 165 degrees leaves clearance behind the knob and keeps the basin clear.
    swingLeaf(w, bdw - 0.05, L.BD_H - 0.028, [L.HALL_WW[0] - 0.006, L.BD_Y[1] - 0.024], [0.0, -1.0], 165.0, M, M.trim, 0.04)
  }

  // ============ CLOSET DOOR (green, head of the hallway, faces south) =====
  {
    const clw = L.CL_X[1] - L.CL_X[0]
    const clc = (L.CL_X[0] + L.CL_X[1]) * 0.5
    const cll = O.lining(clw, L.CL_H, 0.3, 0.022)
    O.place(cll, [clc, L.NW_Y, 0.0], [1, 0], [0, 1])
    w.add(cll, M.green_door)
    const clcs = O.casing(clw, L.CL_H, 0.092, 0.024)
    O.place(clcs, [clc, L.NW_Y, 0.0], [1, 0], [0, -1])
    w.add(clcs, M.green_door)
    const cld = O.panelDoor(clw - 0.05, L.CL_H - 0.028, 0.04, [0.28, 0.28, 0.22, 0.22], 0.108, 0.118, 0.082)
    mlib.translate(cld, [0, 0.04, 0.01])
    O.place(cld, [clc, L.NW_Y, 0.0], [1, 0], [0, 1])
    w.add(cld, M.green_door)
    const kn3 = O.knobSet()
    O.place(kn3, [L.CL_X[1] - 0.13, L.NW_Y - 0.04, 1.0], [1, 0], [0, -1])
    w.add(kn3, M.brass)
  }

  // ============ RACHEL'S DOORWAY: cased opening + transom =================
  {
    const TWALL = L.EXW - L.EX
    const cdw = L.CD_Y[1] - L.CD_Y[0]
    const cdc = (L.CD_Y[0] + L.CD_Y[1]) * 0.5
    const cl2 = O.lining(cdw, L.CD_TOP, TWALL, 0.024)
    O.place(cl2, [L.EX, cdc, 0.0], [0, -1], [1, 0])
    w.add(cl2, M.trim)
    const ccs = O.casing(cdw, L.CD_TOP, 0.1, 0.026)
    O.place(ccs, [L.EX, cdc, 0.0], [0, -1], [-1, 0])
    w.add(ccs, M.trim)
    const ccs2 = O.casing(cdw, L.CD_TOP, 0.075, 0.018)
    O.place(ccs2, [L.EXW, cdc, 0.0], [0, -1], [1, 0])
    w.add(ccs2, M.trim)
    const hr2 = mlib.box(-cdw / 2, 0.0, L.CD_H, cdw / 2, TWALL, L.CD_H + 0.075)
    O.place(hr2, [L.EX, cdc, 0.0], [0, -1], [1, 0])
    w.add(hr2, M.trim)
    const [tf2, tg2] = O.steelWindow(cdw - 0.048, L.CD_TOP - L.CD_H - 0.085, [1], 1, {
      frameW: 0.046,
      frameD: 0.05,
      colsPerBay: 1,
      glassBack: 0.008,
    })
    for (const [o, mm] of [
      [tf2, M.trim],
      [tg2, M.glass_frost],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.CD_H + 0.085])
      O.place(o, [L.EX, cdc, 0.0], [0, -1], [1, 0])
      w.add(o, mm)
    }
    // Rachel's leaf, standing open into her room (hinged on the north jamb)
    swingLeaf(w, cdw - 0.055, L.CD_H - 0.03, [L.EX + 0.052, L.CD_Y[1] - 0.028], [0.0, -1.0], -104.0, M, M.trim)
  }

  // ===== MONICA'S BEDROOM DOOR: south of the alcove, with frosted transom ===
  {
    const TWALL = L.EXW - L.EX
    const mdw = L.MD_Y[1] - L.MD_Y[0]
    const mdc = (L.MD_Y[0] + L.MD_Y[1]) * 0.5
    const ml2 = O.lining(mdw, L.MD_TOP, TWALL, 0.024)
    O.place(ml2, [L.EX, mdc, 0.0], [0, -1], [1, 0])
    w.add(ml2, M.trim)
    const mcs = O.casing(mdw, L.MD_TOP, 0.095, 0.024)
    O.place(mcs, [L.EX, mdc, 0.0], [0, -1], [-1, 0])
    w.add(mcs, M.trim)
    const mcs2 = O.casing(mdw, L.MD_TOP, 0.08, 0.02)
    O.place(mcs2, [L.EXW, mdc, 0.0], [0, -1], [1, 0])
    w.add(mcs2, M.trim)
    const hr3 = mlib.box(-mdw / 2, 0.0, L.MD_H, mdw / 2, TWALL, L.MD_H + 0.075)
    O.place(hr3, [L.EX, mdc, 0.0], [0, -1], [1, 0])
    w.add(hr3, M.trim)
    const [tf3, tg3] = O.steelWindow(mdw - 0.048, L.MD_TOP - L.MD_H - 0.085, [1], 1, {
      frameW: 0.046,
      frameD: 0.05,
      colsPerBay: 1,
      glassBack: 0.008,
    })
    for (const [o, mm] of [
      [tf3, M.trim],
      [tg3, M.glass_frost],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.MD_H + 0.085])
      O.place(o, [L.EX, mdc, 0.0], [0, -1], [1, 0])
      w.add(o, mm)
    }
    // left standing open, swinging east into the bedroom (hinged south jamb)
    swingLeaf(w, mdw - 0.055, L.MD_H - 0.03, [L.EX + 0.052, L.MD_Y[0] + 0.028], [0.0, 1.0], 104.0, M, M.trim)
  }

  // ============================= bedroom windows ==========================
  for (const cy of [L.RB_WIN_Y, L.MB_WIN_Y]) {
    const bw = 1.24
    const bh = 1.38
    const wl = O.lining(bw, bh, L.TW, 0.022)
    mlib.translate(wl, [0, 0, 0.86])
    O.place(wl, [L.EXT_E, cy, 0.0], [0, 1], [1, 0])
    w.add(wl, M.trim)
    const wcs = O.casing(bw, bh, 0.09, 0.02, 4)
    mlib.translate(wcs, [0, 0, 0.86 + bh * 0.5])
    O.place(wcs, [L.EXT_E, cy, 0.0], [0, 1], [-1, 0])
    w.add(wcs, M.trim)
    const [wf, wg] = O.steelWindow(bw - 0.03, bh - 0.03, [1], 3, {
      frameW: 0.048,
      frameD: 0.06,
      munW: 0.024,
      munD: 0.028,
      colsPerBay: 2,
      glassBack: 0.014,
    })
    for (const [o, mm] of [
      [wf, M.trim],
      [wg, M.glass],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, 0.875])
      O.place(o, [L.EXT_E, cy, 0.0], [0, 1], [1, 0])
      w.add(o, mm)
    }
    const sl2 = mlib.box(-bw / 2 - 0.06, -0.02, -0.055, bw / 2 + 0.06, 0.2, 0.0)
    mlib.bevel(sl2, 0.006, 2)
    mlib.translate(sl2, [0, 0, 0.86])
    O.place(sl2, [L.EXT_E, cy, 0.0], [0, 1], [1, 0])
    w.add(sl2, M.stone)
  }
  return M
}
