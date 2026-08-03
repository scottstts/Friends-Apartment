/** Everything you sit on, from f_seating.py.  The hero couch is a Victorian
 * camelback with real diamond buttoning (displaced geometry off the button
 * lattice), swept scroll arms and a bullion fringe of individual cords.
 * Local frame: +X along the length, +Y toward the BACK, standing on z = 0. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import * as G from './geo'
import * as M from './materials'

const TAU = Math.PI * 2

export interface Placed {
  md: MeshData
  mat: THREE.Material
}

function mats(): void {
  // the hero couch is a GOLDEN ochre velvet; the redness in the photographs
  // is the tungsten
  M.velvet('velvet_orange', 'BC7328', 0.42, 1)
  M.velvet('velvet_rust', '8E3A16', 0.46, 0.8)
  M.velvet('velvet_red', '8E2318', 0.44, 0.9)
  M.damask('damask_gold', { ground: '96331A', motif: 'C08A2E', sheenC: 'E6BE6C', scale: [4.6, 3.55] })
  M.damask('damask_black', { ground: '1A1610', motif: 'B58A2E', sheenC: 'D8B468', scale: [11.5, 8.9] })
  M.tapestry('tapestry_floral')
  M.tapestry('tapestry_floral2', { ground: '3A2A1E', a: '9E3524', b: '4A5C3A', c: 'CFA85E', scale: 8.5 })
  M.leather('leather_recliner', '7C6A46', 0.5)
  M.wood('wood_walnut', { light: '8A5C33', dark: '47290F', ring: 26, scale: 1.4 })
  M.wood('wood_oak', { light: 'A87B47', dark: '5A3A1C', ring: 30, scale: 1.1 })
  // real chromed tube in a dim room is a dark object with one bright line
  M.chrome('chrome_stool', 0.22, 'B6BCC0')
  M.metal('brass_trim', 'B8892E', { rough: 0.26, tarnish: 0.5 })
  M.fabric('fringe_bullion', 'A86323', { rough: 0.8, sheen: 0.55, scale: 90 })
}

// ------------------------------------------------------------------ tufting

/** Distance to the NEAREST button: creases land on the Voronoi boundaries of
 * the lattice, which is what makes the diamonds diamonds.  Metres. */
function tuftField(u: number, v: number, buttons: [number, number][], sigma: number, amp: number): number {
  let best = Infinity
  for (const [bu, bv] of buttons) {
    const d = (u - bu) ** 2 + (v - bv) ** 2
    if (d < best) best = d
  }
  const t = Math.min(1, Math.sqrt(best) / sigma)
  return amp * t ** 0.62
}

function buttonLattice(nu: number, nv: number, u0 = 0.1, u1 = 0.9, v0 = 0.16, v1 = 0.8): [number, number][] {
  const out: [number, number][] = []
  for (let j = 0; j < nv; j++) {
    const v = v0 + (v1 - v0) * (j / Math.max(1, nv - 1))
    const n = j % 2 === 0 ? nu : nu - 1
    for (let i = 0; i < n; i++) {
      const u = u0 + (u1 - u0) * ((i + (j % 2 ? 0.5 : 0)) / Math.max(1, nu - 1))
      out.push([u, v])
    }
  }
  return out
}

interface TuftOpts {
  lean?: number
  bow?: number
  nbu?: number
  nbv?: number
  tuft?: number
  nu?: number
  nv?: number
  seatZ?: number
  border?: number
  chan?: number
}

/** The buttoned inside of a sofa back as one closed solid.
 *
 * The crest is a ROLL, not a lid.  Capping the top ring fan-triangulated an
 * n-gon 115 mm out of plane, and that fan, shaded across a curved crest, read
 * as a crease running the length of the back.  So the buttoned panel stops
 * one roll-radius short of the crest line and a run of rings arcs over the
 * top, front face to back face, closing on the ridge.  Same at the bottom,
 * where the cover tucks under the rail.  Nothing is capped; every face in
 * the piece is a quad or a ridge triangle. */
function tuftedBack(ln: number, hEnd: number, hMid: number, yIn: number, thick: number, o: TuftOpts = {}): { md: MeshData; buttons: [number, number][] } {
  const { lean = 0.09, bow = 0.028, nbu = 7, nbv = 3, tuft = 0.052, nu = 97, nv = 33, seatZ = 0.3, border = 0.055, chan = 0 } = o
  const buttons = buttonLattice(nbu, nbv)
  const rr = thick * 0.5
  // the panel's real extent, so the button lattice can be measured in metres
  const bh = hMid - rr - seatZ
  const bm: [number, number][] = buttons.map(([bu, bv]) => [bu * ln, bv * bh])
  const pu = (0.8 * ln) / Math.max(1, nbu - 1)
  const pv = nbv > 1 ? (0.64 * bh) / Math.max(1, nbv - 1) : pu
  const sigma = Math.min(pu, pv) * 0.68
  const rings: Vec3[][] = []
  let lvlLo: [Vec3[], Vec3[]] = [[], []]
  let lvlHi: [Vec3[], Vec3[]] = [[], []]
  for (let j = 0; j < nv; j++) {
    const v = j / (nv - 1)
    const front: Vec3[] = []
    const back: Vec3[] = []
    for (let i = 0; i < nu; i++) {
      const u = i / (nu - 1)
      const x = (u - 0.5) * ln
      const crest = hEnd + (hMid - hEnd) * Math.sin(Math.PI * u) ** 0.55
      const z = seatZ + v * (crest - rr - seatZ)
      const ybase = yIn + lean * v * v + bow * Math.sin(Math.PI * u)
      const eu = border ? Math.min(u, 1 - u) / border : 1
      const ev = border ? Math.min(v / border, (1 - v) / (border * 1.6)) : 1
      let k = Math.max(0, Math.min(1, Math.min(eu, ev)))
      k = k * k * (3 - 2 * k)
      let d = tuftField(u * ln, v * bh, bm, sigma, tuft) * k
      // channels modulate the tufting: a button sucks its tube flat
      if (chan) {
        const ph = (((u - 0.1) * 2 * (nbu - 1)) / 0.8) * TAU * 0.5
        d *= 1 - chan + 2 * chan * (0.5 + 0.5 * Math.cos(ph * 2))
      }
      front.push([x, ybase - d, z])
      const swell = 0.016 * Math.sin(Math.PI * v)
      back.push([x, ybase + thick + swell, z])
    }
    if (j === 0) lvlLo = [front.slice(), back.slice()]
    if (j === nv - 1) lvlHi = [front.slice(), back.slice()]
    rings.push([...front, ...back.reverse()])
  }
  /** Arc the section from its two faces round onto its own centre line.  At
   * the levels the tufting is damped to nothing by the border, so the faces
   * sit exactly `thick` apart and the arc is a true half-round of radius rr.
   * The last ring closes on the ridge; cleanMesh welds that into one edge
   * loop rather than a zero-width strip. */
  const wrap = (level: [Vec3[], Vec3[]], up: number, n: number): Vec3[][] => {
    const [f0, b0] = level
    const out: Vec3[][] = []
    for (let k = 1; k <= n; k++) {
      const a = (k / n) * (Math.PI / 2)
      const ca = Math.cos(a)
      const sa = Math.sin(a)
      const fr: Vec3[] = []
      const bk: Vec3[] = []
      for (let i = 0; i < nu; i++) {
        const yc = 0.5 * (f0[i][1] + b0[i][1])
        const r = 0.5 * (b0[i][1] - f0[i][1])
        const z = f0[i][2] + up * r * sa
        fr.push([f0[i][0], yc - r * ca, z])
        bk.push([b0[i][0], yc + r * ca, z])
      }
      out.push([...fr, ...bk.reverse()])
    }
    return out
  }
  // 6 rings is 15 degrees a step, well inside the 46 degree smooth angle, so
  // the roll shades as a round rather than as facets
  const md = mlib.loft([...wrap(lvlLo, -1, 3).reverse(), ...rings, ...wrap(lvlHi, 1, 6)], { closeV: true })
  mlib.cleanMesh(md)
  mlib.smoothShade(md, 46)
  return { md, buttons }
}

/** `crestR` is tuftedBack's roll radius and must be the same number: the
 * buttons are placed by re-evaluating that surface's own equation, so if the
 * panel stops short of the crest and the buttons do not, the top row floats
 * off the cover. */
function buttonsOn(
  buttons: [number, number][],
  ln: number,
  hEnd: number,
  hMid: number,
  yIn: number,
  lean: number,
  bow: number,
  seatZ = 0.3,
  r = 0.021,
  crestR = 0,
): MeshData[] {
  const out: MeshData[] = []
  for (const [u, v] of buttons) {
    const x = (u - 0.5) * ln
    const crest = hEnd + (hMid - hEnd) * Math.sin(Math.PI * u) ** 0.55
    const z = seatZ + v * (crest - crestR - seatZ)
    const y = yIn + lean * v * v + bow * Math.sin(Math.PI * u)
    const b = mlib.revolve(
      [
        [0, 0],
        [r * 0.55, 0.001],
        [r, 0.006],
        [r * 0.92, 0.012],
        [r * 0.45, 0.016],
        [0, 0.016],
      ],
      14,
    )
    mlib.rotX(b, Math.PI / 2)
    mlib.translate(b, [x, y + 0.002, z])
    mlib.smoothShade(b, 50)
    out.push(b)
  }
  return out
}

// -------------------------------------------------------------------- arms

/** English scroll arm from its silhouette: one closed YZ section lofted
 * across the arm's width with the end sections inset. */
function scrollArm(xIn: number, xOut: number, yBack: number, yFront: number, z0: number, zTop: number, roll = 0.155): { md: MeshData; cy: number; cz: number } {
  const cy = yFront + roll
  const cz = zTop - roll
  let sec: Vec2[] = [
    [yBack, z0],
    [yBack, zTop - 0.055],
    [cy + roll * 0.62, zTop],
  ]
  sec = sec.concat(G.arcPts(cy, cz, roll, Math.PI / 2, (283 * Math.PI) / 180, 18, true))
  sec.push([cy + roll * 0.7, z0])
  sec = G.ccw(sec)
  const steps: [number, number][] = [
    [0, -0.058],
    [0.012, -0.032],
    [0.035, -0.013],
    [0.075, -0.002],
    [0.925, -0.002],
    [0.965, -0.013],
    [0.988, -0.032],
    [1, -0.058],
  ]
  const rings: Vec3[][] = []
  for (const [t, ins] of steps) {
    const poly = ins ? G.polyOffset(sec, ins) : sec
    const x = xIn + (xOut - xIn) * t
    rings.push(poly.map((p) => [x, p[0], p[1]] as Vec3))
  }
  const md = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(md, 44)
  return { md, cy, cz }
}

/** The carved wooden scroll on the face of an arm: a tapering spiral bead. */
function carvedVolute(cx: number, cy: number, cz: number, r = 0.105, depth = 0.035, turns = 1.6, flip = false): MeshData {
  const pts: Vec3[] = []
  const n = 40
  for (let i = 0; i <= n; i++) {
    const t = i / n
    const a = TAU * turns * t
    const rr = r * (1 - 0.68 * t)
    pts.push([0, rr * Math.cos(a), rr * Math.sin(a)])
  }
  const md = mlib.tubeAlong(pts, mlib.circle(depth * 0.5, 8), { up: [1, 0, 0] })
  mlib.smoothShade(md, 40)
  if (flip) {
    mlib.scaleMesh(md, [1, -1, 1])
    mlib.recalcNormals(md)
  }
  mlib.translate(md, [cx, cy, cz])
  return md
}

// ------------------------------------------------------------------ fringe

/** Bullion fringe: a twisted cord per 13 mm of hem, each with its own lean. */
function bullion(poly: Vec2[], ztop: number, length = 0.115, pitch = 0.0072, r = 0.0034, jitter = 0.3): MeshData {
  const walk: [number, number, number][] = []
  const n = poly.length
  for (let i = 0; i < n; i++) {
    const a = poly[i]
    const b = poly[(i + 1) % n]
    const seg = Math.hypot(b[0] - a[0], b[1] - a[1])
    const k = Math.max(1, Math.round(seg / pitch))
    for (let j = 0; j < k; j++) {
      const t = j / k
      walk.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, Math.atan2(b[1] - a[1], b[0] - a[0])])
    }
  }
  const cords: MeshData[] = []
  walk.forEach(([x, y, ang], idx) => {
    const s = Math.sin(idx * 2.399) * 0.5 + Math.sin(idx * 0.77) * 0.5
    const ln = length * (1 + jitter * 0.3 * s)
    const ox = Math.sin(ang)
    const oy = -Math.cos(ang)
    const sway = 0.016 * jitter * s
    const pts: Vec3[] = [
      [x, y, ztop],
      [x + ox * sway * 0.4, y + oy * sway * 0.4, ztop - ln * 0.45],
      [x + ox * sway, y + oy * sway, ztop - ln * 0.88],
      [x + ox * sway * 1.1, y + oy * sway * 1.1, ztop - ln],
    ]
    const rad = [r * 0.85, r, r * 0.95, r * 0.55]
    const rings: Vec3[][] = pts.map((p, pi) =>
      Array.from({ length: 6 }, (_, k2) => {
        const a2 = (k2 * TAU) / 6
        return [p[0] + rad[pi] * Math.cos(a2), p[1] + rad[pi] * Math.sin(a2), p[2]] as Vec3
      }),
    )
    cords.push(mlib.loft(rings, { closeV: true, capStart: true, capEnd: true }))
  })
  const md = mlib.join(cords)
  mlib.smoothShade(md, 40)
  return md
}

// ------------------------------------------------------------- the hero couch

/** A stuffed cushion with a welt sewn round its seam. */
function plump(poly: Vec2[], z0: number, h: number, welt = 0.006): MeshData {
  const levels: [number, number, number][] = [
    [0, 0.9, 0],
    [0.12, 1.005, 0],
    [0.46, 1.02, welt],
    [0.54, 1.02, welt],
    [0.88, 1.005, 0],
    [1, 0.88, 0],
  ]
  const cx = poly.reduce((s, p) => s + p[0], 0) / poly.length
  const cy = poly.reduce((s, p) => s + p[1], 0) / poly.length
  const rings: Vec3[][] = []
  for (const [t, s, w] of levels) {
    rings.push(
      poly.map(([x, y]) => {
        const vx = x - cx
        const vy = y - cy
        const ll = Math.hypot(vx, vy) || 1
        return [cx + vx * s + (vx / ll) * w, cy + vy * s + (vy / ll) * w, z0 + t * h] as Vec3
      }),
    )
  }
  const md = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(md, 48)
  return md
}

/** The orange couch.  Everything else in the room is dressed around it. */
export function heroCouch(ln = 2.24, dp = 0.92): Placed[] {
  mats()
  const pv: MeshData[] = []
  const pw: MeshData[] = []
  const yb = dp * 0.5
  const yf = -dp * 0.5
  const seatZ = 0.3
  const armTop = 0.615
  const aw = 0.205
  const inner = ln - 2 * aw

  const fr = mlib.prism(
    [
      [-ln / 2, yf],
      [ln / 2, yf],
      [ln / 2, yb],
      [-ln / 2, yb],
    ],
    0.13,
    0.242,
  )
  mlib.bevel(fr, 0.012, 2)
  pw.push(fr)
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const ft = mlib.revolve(
        [
          [0, 0],
          [0.03, 0.004],
          [0.034, 0.02],
          [0.026, 0.052],
          [0.036, 0.086],
          [0.03, 0.12],
          [0.042, 0.14],
          [0, 0.14],
        ],
        16,
      )
      mlib.smoothShade(ft, 40)
      mlib.translate(ft, [sx * (ln / 2 - 0.085), sy * (dp / 2 - 0.085), 0])
      pw.push(ft)
    }
  }

  const dk = mlib.box(-inner / 2 - 0.015, yf + 0.055, 0.238, inner / 2 + 0.015, yb - 0.055, seatZ)
  mlib.bevel(dk, 0.01, 2)
  pv.push(dk)
  const ap = mlib.prism(
    [
      [-ln / 2 + 0.012, yf + 0.012],
      [ln / 2 - 0.012, yf + 0.012],
      [ln / 2 - 0.012, yb - 0.012],
      [-ln / 2 + 0.012, yb - 0.012],
    ],
    0.232,
    0.302,
  )
  mlib.bevel(ap, 0.016, 2)
  pv.push(ap)

  const lean = 0.112
  const bow = 0.03
  const tuft = 0.098
  const yIn = yb - 0.225
  const back = tuftedBack(inner + 0.04, 0.845, 0.96, yIn, 0.16, {
    lean,
    bow,
    nbu: 7,
    nbv: 3,
    tuft,
    seatZ: 0.3,
    chan: 0.17,
    nu: 121,
    nv: 41,
  })
  pv.push(back.md)
  pv.push(...buttonsOn(back.buttons, inner + 0.04, 0.845, 0.96, yIn, lean, bow, 0.3, 0.026, 0.16 * 0.5))

  for (const s of [-1, 1]) {
    const arm = scrollArm(s * (inner / 2 - 0.004), s * (ln / 2), yb - 0.05, yf + 0.048, 0.24, armTop + 0.042, 0.166)
    pv.push(arm.md)
    pw.push(carvedVolute(s * (ln / 2 + 0.006), arm.cy, arm.cz, 0.108, 0.042, 1.6, s < 0))
  }

  const cu = plump(mlib.roundedRect(inner + 0.012, dp - 0.205, 0.06, 6), seatZ - 0.008, 0.158, 0.012)
  mlib.translate(cu, [0, -0.03, 0])
  pv.push(cu)

  const hem: Vec2[] = [
    [-ln / 2 + 0.006, yf + 0.006],
    [ln / 2 - 0.006, yf + 0.006],
    [ln / 2 - 0.006, yb - 0.006],
    [-ln / 2 + 0.006, yb - 0.006],
  ]
  const fg = bullion(hem, 0.248, 0.178)

  return [
    { md: mlib.join(pv), mat: M.get('velvet_orange') },
    { md: mlib.join(pw), mat: M.get('wood_walnut') },
    { md: fg, mat: M.get('fringe_bullion') },
  ]
}

// ---------------------------------------------------------------- settees

export interface SetteeOpts {
  cover?: string
  frame?: string
  seatH?: number
  backH?: number
  nbu?: number
  nbv?: number
  fringe?: boolean
  cushions?: number
}

/** The smaller sofas: same construction as the hero couch, lighter scale. */
export function settee(ln = 1.62, dp = 0.78, o: SetteeOpts = {}): Placed[] {
  mats()
  const { cover = 'damask_gold', frame = 'wood_walnut', seatH = 0.415, backH = 0.925, nbu = 5, nbv = 2, fringe = false, cushions = 2 } = o
  const pv: MeshData[] = []
  const pw: MeshData[] = []
  const yb = dp / 2
  const yf = -dp / 2
  const aw = 0.165
  const inner = ln - 2 * aw
  const seatZ = seatH - 0.115

  const fr = mlib.prism(
    [
      [-ln / 2, yf],
      [ln / 2, yf],
      [ln / 2, yb],
      [-ln / 2, yb],
    ],
    0.115,
    0.225,
  )
  mlib.bevel(fr, 0.01, 2)
  pw.push(fr)
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const ft = mlib.revolve(
        [
          [0, 0],
          [0.026, 0.004],
          [0.03, 0.018],
          [0.022, 0.048],
          [0.032, 0.076],
          [0.038, 0.115],
          [0, 0.115],
        ],
        14,
      )
      mlib.smoothShade(ft, 40)
      mlib.translate(ft, [sx * (ln / 2 - 0.075), sy * (dp / 2 - 0.075), 0])
      pw.push(ft)
    }
  }

  const dk = mlib.box(-inner / 2 - 0.012, yf + 0.05, 0.22, inner / 2 + 0.012, yb - 0.065, seatZ)
  mlib.bevel(dk, 0.01, 2)
  pv.push(dk)
  const ap = mlib.prism(
    [
      [-ln / 2 + 0.01, yf + 0.01],
      [ln / 2 - 0.01, yf + 0.01],
      [ln / 2 - 0.01, yb - 0.01],
      [-ln / 2 + 0.01, yb - 0.01],
    ],
    0.215,
    0.29,
  )
  mlib.bevel(ap, 0.016, 2)
  pv.push(ap)

  const lean = 0.075
  const bow = 0.022
  const tuft = 0.04
  const yIn = yb - 0.185
  const back = tuftedBack(inner + 0.03, backH - 0.055, backH, yIn, 0.13, {
    lean,
    bow,
    nbu,
    nbv,
    tuft,
    seatZ: seatZ - 0.045,
    nu: 57,
    nv: 25,
  })
  pv.push(back.md)
  pv.push(...buttonsOn(back.buttons, inner + 0.03, backH - 0.055, backH, yIn, lean, bow, seatZ - 0.045, 0.014, 0.13 * 0.5))

  for (const s of [-1, 1]) {
    const arm = scrollArm(s * (inner / 2 - 0.004), s * (ln / 2), yb - 0.045, yf + 0.042, 0.22, seatH + 0.17, 0.128)
    pv.push(arm.md)
  }

  const pitch = (inner - 0.01) / cushions
  for (let i = 0; i < cushions; i++) {
    const cu = plump(mlib.roundedRect(pitch - 0.022, dp - 0.205, 0.05, 5), seatZ - 0.005, 0.13, 0.006)
    mlib.translate(cu, [-inner / 2 + (i + 0.5) * pitch, -0.022, 0])
    pv.push(cu)
  }

  const out: Placed[] = [
    { md: mlib.join(pv), mat: M.get(cover) },
    { md: mlib.join(pw), mat: M.get(frame) },
  ]
  if (fringe) {
    const hem: Vec2[] = [
      [-ln / 2 + 0.005, yf + 0.005],
      [ln / 2 - 0.005, yf + 0.005],
      [ln / 2 - 0.005, yb - 0.005],
      [-ln / 2 + 0.005, yb - 0.005],
    ]
    out.push({ md: bullion(hem, 0.128, 0.1), mat: M.get('fringe_bullion') })
  }
  return out
}

/** The two red club chairs: low, square, deep-seated, plain rolled back. */
export function clubChair(w = 0.82, dp = 0.86, h = 0.9, cover = 'velvet_dk'): Placed[] {
  mats()
  const coverName = cover === 'velvet_dk' ? 'velvet_rust' : cover
  const pv: MeshData[] = []
  const pw: MeshData[] = []
  const yb = dp / 2
  const aw = 0.155
  const rings: Vec3[][] = []
  const tubLevels: [number, number, number][] = [
    [0, 0, 0],
    [0.55, 0.17, -0.012],
    [1, 0.23, -0.02],
  ]
  for (const [, dz, inset] of tubLevels) {
    const poly = mlib.roundedRect(w - inset, dp - inset, 0.075, 5)
    rings.push(poly.map(([x, y]) => [x, y, 0.15 + dz] as Vec3))
  }
  const tub = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(tub, 44)
  pv.push(tub)
  const bk = mlib.prism(mlib.roundedRect(w - 0.01, 0.215, 0.07, 5), 0.32, h)
  mlib.bevel(bk, 0.045, 3)
  mlib.smoothShade(bk, 44)
  mlib.translate(bk, [0, yb - 0.115, 0])
  pv.push(bk)
  for (const s of [-1, 1]) {
    const ar = mlib.prism(mlib.roundedRect(aw, dp - 0.09, 0.055, 5), 0.36, 0.585)
    mlib.bevel(ar, 0.045, 3)
    mlib.smoothShade(ar, 44)
    mlib.translate(ar, [(s * (w - aw)) / 2, -0.015, 0])
    pv.push(ar)
  }
  const cu = plump(mlib.roundedRect(w - 2 * aw + 0.02, dp - 0.245, 0.05, 5), 0.375, 0.135, 0.006)
  mlib.translate(cu, [0, -0.045, 0])
  pv.push(cu)
  const bc = plump(mlib.roundedRect(w - 2 * aw + 0.01, 0.155, 0.05, 5), 0.48, 0.33, 0.005)
  mlib.rotX(bc, (-7 * Math.PI) / 180)
  mlib.translate(bc, [0, yb - 0.255, 0])
  pv.push(bc)
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const ft = mlib.revolve(
        [
          [0, 0],
          [0.028, 0.006],
          [0.024, 0.06],
          [0.036, 0.1],
          [0.04, 0.15],
          [0, 0.15],
        ],
        14,
      )
      mlib.smoothShade(ft, 40)
      mlib.translate(ft, [sx * (w / 2 - 0.075), sy * (dp / 2 - 0.075), 0])
      pw.push(ft)
    }
  }
  return [
    { md: mlib.join(pv), mat: M.get(coverName) },
    { md: mlib.join(pw), mat: M.get('wood_walnut') },
  ]
}

/** The taupe channel-tufted recliner: lofted bolster channels, not bumps. */
export function recliner(w = 0.94, dp = 1.02, h = 0.98): Placed[] {
  mats()
  const pv: MeshData[] = []
  const pw: MeshData[] = []
  const yb = dp / 2
  const yf = -dp / 2
  const aw = 0.185
  const nch = 5
  const inner = w - 2 * aw

  const nu = 16 * nch + 1
  const nv = 26
  const rings: Vec3[][] = []
  for (let j = 0; j < nv; j++) {
    const v = j / (nv - 1)
    const front: Vec3[] = []
    const back: Vec3[] = []
    for (let i = 0; i < nu; i++) {
      const u = i / (nu - 1)
      let endk = Math.min(1, Math.min(u, 1 - u) / 0.06)
      endk = endk * endk * (3 - 2 * endk)
      const x = (u - 0.5) * inner
      const ph = (u * nch - 0.5) * TAU
      const ch = 0.052 * (0.5 - 0.5 * Math.cos(ph)) ** 0.75
      const lean = 0.115 * v * v - 0.145 * Math.max(0, (v - 0.68) / 0.32) ** 2
      const z = 0.4 + v * (h - 0.4)
      const y = yb - 0.235 + lean
      const taper = Math.sin(Math.PI * Math.min(1, 0.06 + v * 1.02)) ** 0.35
      front.push([x, y - (ch * taper + 0.022) * endk, z])
      back.push([x, y + 0.115 + 0.02 * Math.sin(Math.PI * v), z])
    }
    rings.push([...front, ...back.reverse()])
  }
  const bk = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(bk, 46)
  pv.push(bk)

  const dk = mlib.box(-inner / 2 - 0.012, yf + 0.06, 0.19, inner / 2 + 0.012, yb - 0.11, 0.395)
  mlib.bevel(dk, 0.012, 2)
  pv.push(dk)
  const srings: Vec3[][] = []
  const nsv = 18
  for (let j = 0; j < nsv; j++) {
    const v = j / (nsv - 1)
    const top: Vec3[] = []
    const bot: Vec3[] = []
    for (let i = 0; i < nu; i++) {
      const u = i / (nu - 1)
      let endk = Math.min(1, Math.min(u, 1 - u) / 0.05)
      endk = endk * endk * (3 - 2 * endk)
      const x = (u - 0.5) * (inner + 0.02)
      const ph = (u * nch - 0.5) * TAU
      const ch = 0.04 * (0.5 - 0.5 * Math.cos(ph)) ** 0.75
      const y = yf + 0.07 + v * (dp - 0.255)
      const dome = Math.sin(Math.PI * Math.min(1, Math.max(0, 0.1 + v * 0.86))) ** 0.45
      top.push([x, y, 0.392 + (0.052 + ch) * dome * endk])
      bot.push([x, y, 0.386 - 0.01 * dome * endk])
    }
    srings.push([...top, ...bot.reverse()])
  }
  const st = mlib.loft(srings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(st, 46)
  pv.push(st)

  // arms: fat rolled bolsters standing from the deck to elbow height
  const az0 = 0.19
  const az1 = 0.628
  const arR = 0.108
  for (const s of [-1, 1]) {
    let sec: Vec2[] = [
      [yb - 0.055, az0],
      [yb - 0.055, az1 - arR],
    ]
    sec = sec.concat(G.arcPts(yb - 0.055 - arR, az1 - arR, arR, 0, Math.PI / 2, 7, true))
    sec = sec.concat(G.arcPts(yf + 0.055 + arR, az1 - arR, arR, Math.PI / 2, Math.PI, 7, true))
    sec.push([yf + 0.055, az0])
    sec = G.ccw(sec)
    const steps: [number, number][] = [
      [0, -0.062],
      [0.02, -0.03],
      [0.06, -0.008],
      [0.94, -0.008],
      [0.98, -0.03],
      [1, -0.062],
    ]
    const arings: Vec3[][] = []
    const x0 = s * (inner / 2 + 0.002)
    const x1 = s * (w / 2)
    for (const [t, ins] of steps) {
      const poly = ins ? G.polyOffset(sec, ins) : sec
      const xx = x0 + (x1 - x0) * t
      arings.push(poly.map((p) => [xx, p[0], p[1]] as Vec3))
    }
    const ar = mlib.loft(arings, { closeV: true, capStart: true, capEnd: true })
    mlib.smoothShade(ar, 46)
    pv.push(ar)
  }

  const pl = mlib.prism(mlib.roundedRect(w - 0.13, dp - 0.2, 0.045, 4), 0, 0.195)
  mlib.bevel(pl, 0.014, 2)
  pw.push(pl)
  return [
    { md: mlib.join(pv), mat: M.get('leather_recliner') },
    { md: mlib.join(pw), mat: M.get('wood_walnut') },
  ]
}

// ------------------------------------------------------------- side chairs

/** The black-and-gold damask side chairs: turned-leg frame, shaped crest
 * rail, drop-in upholstered seat. */
export function bistroChair(w = 0.455, dp = 0.475, seatH = 0.455, back = 0.925, cover = 'damask_black'): Placed[] {
  mats()
  const pw: MeshData[] = []
  const pv: MeshData[] = []
  const hw = w / 2
  const hd = dp / 2
  for (const s of [-1, 1]) {
    const path: Vec3[] = [
      [s * (hw - 0.03), hd - 0.03, 0],
      [s * (hw - 0.03), hd - 0.032, seatH],
      [s * (hw - 0.042), hd - 0.05, back - 0.075],
      [s * (hw - 0.048), hd - 0.062, back],
    ]
    pw.push(mlib.tubeAlong(path, mlib.roundedRect(0.034, 0.034, 0.012, 3), { up: [0, 1, 0] }))
    const fl = mlib.revolve(
      [
        [0, 0],
        [0.024, 0.004],
        [0.02, 0.03],
        [0.026, 0.07],
        [0.017, 0.13],
        [0.023, 0.19],
        [0.016, 0.3],
        [0.022, 0.36],
        [0.018, seatH - 0.055],
        [0.024, seatH],
        [0, seatH],
      ],
      14,
    )
    mlib.smoothShade(fl, 40)
    mlib.translate(fl, [s * (hw - 0.03), -(hd - 0.03), 0])
    pw.push(fl)
  }
  const railPairs: [Vec2, Vec2][] = [
    [[-hw, -hd], [hw, -hd]],
    [[-hw, hd], [hw, hd]],
    [[-hw, -hd], [-hw, hd]],
    [[hw, -hd], [hw, hd]],
  ]
  for (const [a, bp] of railPairs) {
    pw.push(
      mlib.tubeAlong(
        [
          [a[0], a[1], seatH - 0.048],
          [bp[0], bp[1], seatH - 0.048],
        ],
        mlib.roundedRect(0.03, 0.052, 0.008, 2),
      ),
    )
  }
  for (const yy of [-hd + 0.035, hd - 0.035]) {
    pw.push(
      mlib.tubeAlong(
        [
          [-hw + 0.03, yy, 0.115],
          [hw - 0.03, yy, 0.115],
        ],
        mlib.circle(0.011, 8),
      ),
    )
  }
  const crest = mlib.prismXZ(
    [
      [-hw + 0.02, back - 0.115],
      [hw - 0.02, back - 0.115],
      [hw - 0.02, back - 0.02],
      [0, back + 0.012],
      [-hw + 0.02, back - 0.02],
    ],
    hd - 0.078,
    hd - 0.04,
  )
  pw.push(crest)
  const splat = mlib.prismXZ(
    [
      [-hw + 0.03, seatH + 0.052],
      [hw - 0.03, seatH + 0.052],
      [hw - 0.03, seatH + 0.092],
      [-hw + 0.03, seatH + 0.092],
    ],
    hd - 0.076,
    hd - 0.046,
  )
  pw.push(splat)
  const sq = plump(mlib.roundedRect(w - 0.045, dp - 0.05, 0.03, 5), seatH - 0.05, 0.078, 0.005)
  pv.push(sq)
  // the back pad reaches down to the lumbar, not just across the shoulders
  const b0 = seatH + 0.098
  const b1 = back - 0.122
  const bp2 = plump(mlib.roundedRect(w - 0.072, 0.072, 0.022, 4), b0, 0.075, 0.004)
  mlib.rotX(bp2, (4 * Math.PI) / 180)
  mlib.scaleMesh(bp2, [1, 1, (b1 - b0) / 0.075], [0, 0, b0])
  mlib.translate(bp2, [0, hd - 0.058, 0])
  pv.push(bp2)
  return [
    { md: mlib.join(pw), mat: M.get('wood_walnut') },
    { md: mlib.join(pv), mat: M.get(cover) },
  ]
}

/** Chrome-legged tapestry bar stool. */
export function barStool(h = 0.735, r = 0.185): Placed[] {
  mats()
  const pm: MeshData[] = []
  const pv: MeshData[] = []
  for (let i = 0; i < 4; i++) {
    const a = ((45 + i * 90) * Math.PI) / 180
    const x0 = 0.055 * Math.cos(a)
    const y0 = 0.055 * Math.sin(a)
    const x1 = 0.215 * Math.cos(a)
    const y1 = 0.215 * Math.sin(a)
    const lg = mlib.tubeAlong(
      [
        [x0, y0, h - 0.075],
        [x0 * 1.4, y0 * 1.4, h - 0.3],
        [x1, y1, 0.02],
        [x1 * 1.02, y1 * 1.02, 0],
      ],
      mlib.circle(0.0125, 10),
    )
    mlib.smoothShade(lg, 40)
    pm.push(lg)
  }
  const ring = mlib.tubeAlong(
    Array.from({ length: 24 }, (_, t) => [0.15 * Math.cos((t * TAU) / 24), 0.15 * Math.sin((t * TAU) / 24), 0.215] as Vec3),
    mlib.circle(0.0095, 8),
    { closePath: true },
  )
  mlib.smoothShade(ring, 40)
  pm.push(ring)
  const plate = mlib.revolve(
    [
      [0, h - 0.085],
      [0.075, h - 0.085],
      [0.078, h - 0.072],
      [0, h - 0.072],
    ],
    20,
  )
  mlib.smoothShade(plate, 40)
  pm.push(plate)
  const seatMd = mlib.revolve(
    [
      [0, h - 0.072],
      [r * 0.92, h - 0.07],
      [r, h - 0.048],
      [r * 0.995, h - 0.02],
      [r * 0.86, h + 0.004],
      [r * 0.45, h + 0.016],
      [0, h + 0.018],
    ],
    32,
  )
  mlib.smoothShade(seatMd, 46)
  pv.push(seatMd)
  return [
    { md: mlib.join(pm), mat: M.get('chrome_stool') },
    { md: mlib.join(pv), mat: M.get('damask_black') },
  ]
}

/** The taller wooden stools: splayed turned legs, padded tapestry top. */
export function woodStool(h = 0.7, r = 0.175): Placed[] {
  mats()
  const pw: MeshData[] = []
  const pv: MeshData[] = []
  for (let i = 0; i < 4; i++) {
    const a = ((45 + i * 90) * Math.PI) / 180
    const x0 = 0.085 * Math.cos(a)
    const y0 = 0.085 * Math.sin(a)
    const x1 = 0.205 * Math.cos(a)
    const y1 = 0.205 * Math.sin(a)
    pw.push(
      mlib.tubeAlong(
        [
          [x0, y0, h - 0.055],
          [x0 * 1.3, y0 * 1.3, h - 0.22],
          [x1 * 0.94, y1 * 0.94, 0.13],
          [x1, y1, 0],
        ],
        mlib.roundedRect(0.03, 0.03, 0.011, 3),
      ),
    )
  }
  const zz = 0.235
  const rr = 0.168
  for (let i = 0; i < 4; i++) {
    const a0 = ((45 + i * 90) * Math.PI) / 180
    const a1 = ((135 + i * 90) * Math.PI) / 180
    pw.push(
      mlib.tubeAlong(
        [
          [rr * Math.cos(a0), rr * Math.sin(a0), zz],
          [rr * Math.cos(a1), rr * Math.sin(a1), zz],
        ],
        mlib.circle(0.01, 7),
      ),
    )
  }
  const frame = mlib.revolve(
    [
      [0, h - 0.06],
      [r * 0.96, h - 0.06],
      [r * 0.99, h - 0.03],
      [0, h - 0.03],
    ],
    24,
  )
  mlib.smoothShade(frame, 40)
  pw.push(frame)
  const top = mlib.revolve(
    [
      [0, h - 0.032],
      [r * 0.99, h - 0.03],
      [r * 1.01, h - 0.004],
      [r * 0.94, h + 0.02],
      [r * 0.5, h + 0.032],
      [0, h + 0.034],
    ],
    28,
  )
  mlib.smoothShade(top, 46)
  pv.push(top)
  return [
    { md: mlib.join(pw), mat: M.get('wood_oak') },
    { md: mlib.join(pv), mat: M.get('tapestry_floral2') },
  ]
}

/** Round buttoned pouf in the north alcove. */
export function pouf(r = 0.33, h = 0.42): Placed[] {
  mats()
  const body = mlib.revolve(
    [
      [0, 0.055],
      [r * 0.86, 0.05],
      [r, 0.14],
      [r * 0.99, h - 0.08],
      [r * 0.72, h - 0.01],
      [r * 0.3, h + 0.012],
      [0, h + 0.016],
    ],
    32,
  )
  mlib.smoothShade(body, 46)
  const parts = [body]
  for (let i = 0; i < 6; i++) {
    const a = (i * TAU) / 6
    const b = mlib.revolve(
      [
        [0, 0],
        [0.013, 0.004],
        [0.011, 0.01],
        [0, 0.011],
      ],
      10,
    )
    mlib.translate(b, [r * 0.52 * Math.cos(a), r * 0.52 * Math.sin(a), h + 0.002])
    parts.push(b)
  }
  const fe: MeshData[] = []
  for (let i = 0; i < 4; i++) {
    const a = ((45 + i * 90) * Math.PI) / 180
    const f = mlib.revolve(
      [
        [0, 0],
        [0.028, 0.004],
        [0.022, 0.038],
        [0.03, 0.058],
        [0, 0.058],
      ],
      12,
    )
    mlib.translate(f, [r * 0.72 * Math.cos(a), r * 0.72 * Math.sin(a), 0])
    fe.push(f)
  }
  return [
    { md: mlib.join(parts), mat: M.get('damask_gold') },
    { md: mlib.join(fe), mat: M.get('wood_walnut') },
  ]
}
