/** Extra dressing - port of f_extra.py: kitchen small appliances, dish rack,
 * paper towel, knife block, the door-wall hook and strap-hung frame. */
import type * as THREE from 'three/webgpu'
import * as L from '../lib/L'
import * as mlib from '../lib/mlib'
import { MeshData, type Vec2, type Vec3 } from '../lib/mesh'
import * as mats from '../mats/mats'
import type { World } from './world'

const CTR_H = L.CTR_H

function rad(d: number): number {
  return (d * Math.PI) / 180
}

function coffeeMaker(w: World, loc: Vec3, rotz = 0.0): void {
  const blk = mats.paint('appl_black', '232323', { rough: 0.3, coat: 0.35 })
  const chr = mats.get('metal_chrome')!
  const gl = mats.get('glass_thick') ?? mats.pane('glass_thick')
  const placed: [MeshData, THREE.Material][] = []
  const body = mlib.prism(mlib.roundedRect(0.155, 0.19, 0.03, 4), 0.0, 0.135)
  mlib.bevel(body, 0.006, 2)
  placed.push([body, blk])
  const tower = mlib.prism(mlib.roundedRect(0.15, 0.105, 0.026, 4), 0.135, 0.36)
  mlib.bevel(tower, 0.008, 2)
  mlib.translate(tower, [0, 0.042, 0])
  placed.push([tower, blk])
  const plate = mlib.revolve(
    [
      [0.0, 0.0],
      [0.062, 0.0],
      [0.062, 0.006],
      [0.0, 0.006],
    ],
    20,
  )
  mlib.translate(plate, [0, -0.035, 0.135])
  placed.push([plate, chr])
  const carafe = mlib.revolve(
    [
      [0.0, 0.0],
      [0.058, 0.004],
      [0.062, 0.02],
      [0.06, 0.13],
      [0.052, 0.15],
      [0.048, 0.16],
      [0.044, 0.158],
      [0.046, 0.135],
      [0.0, 0.13],
    ],
    22,
  )
  mlib.smoothShade(carafe, 34)
  mlib.translate(carafe, [0, -0.035, 0.141])
  placed.push([carafe, gl])
  for (const [ob, mm] of placed) {
    mlib.rotateZ(ob, rotz)
    mlib.translate(ob, loc)
    w.add(ob, mm)
  }
}

function standMixer(w: World, loc: Vec3, rotz = 0.0): void {
  const body = mats.paint('appl_cream', 'E4DFD2', { rough: 0.16, coat: 0.55 })
  const chr = mats.get('metal_chrome')!
  const placed: [MeshData, THREE.Material][] = []
  const base = mlib.revolve(
    [
      [0.0, 0.0],
      [0.09, 0.004],
      [0.094, 0.02],
      [0.086, 0.05],
      [0.07, 0.062],
      [0.0, 0.064],
    ],
    24,
  )
  mlib.smoothShade(base, 34)
  placed.push([base, body])
  const col = mlib.prism(mlib.roundedRect(0.07, 0.085, 0.026, 4), 0.06, 0.245)
  mlib.bevel(col, 0.01, 2)
  mlib.translate(col, [-0.052, 0, 0])
  placed.push([col, body])
  const head = mlib.prism(mlib.roundedRect(0.24, 0.082, 0.036, 4), 0.2, 0.29)
  mlib.bevel(head, 0.014, 2)
  mlib.translate(head, [0.026, 0, 0])
  placed.push([head, body])
  const bowl = mlib.revolve(
    [
      [0.0, 0.0],
      [0.048, 0.0],
      [0.072, 0.04],
      [0.086, 0.1],
      [0.09, 0.14],
      [0.086, 0.14],
      [0.082, 0.1],
      [0.068, 0.042],
      [0.044, 0.006],
      [0.0, 0.006],
    ],
    26,
  )
  mlib.smoothShade(bowl, 32)
  mlib.translate(bowl, [0.052, 0, 0.058])
  placed.push([bowl, chr])
  const beat = mlib.revolve(
    [
      [0.0, 0.0],
      [0.026, 0.03],
      [0.03, 0.07],
      [0.01, 0.09],
      [0.01, 0.11],
      [0.0, 0.11],
    ],
    12,
  )
  mlib.translate(beat, [0.052, 0, 0.09])
  placed.push([beat, chr])
  for (const [ob, mm] of placed) {
    mlib.rotateZ(ob, rotz)
    mlib.translate(ob, loc)
    w.add(ob, mm)
  }
}

function dishRack(w: World, loc: Vec3, rotz = 0.0, n = 7): void {
  const wire = mats.metal('metal_wire', 'B8BCC0', { rough: 0.24, bump: 0.05 })
  const parts: MeshData[] = []
  const rw = 0.34
  const d = 0.26
  const h = 0.115
  for (const s of [-1, 1]) {
    parts.push(
      mlib.tubeAlong(
        [
          [-rw / 2, (s * d) / 2, 0.0],
          [rw / 2, (s * d) / 2, 0.0],
        ],
        mlib.circle(0.0035, 6),
      ),
    )
    parts.push(
      mlib.tubeAlong(
        [
          [-rw / 2, (s * d) / 2, h],
          [rw / 2, (s * d) / 2, h],
        ],
        mlib.circle(0.0035, 6),
      ),
    )
  }
  for (let i = 0; i < n; i++) {
    const xx = -rw / 2 + 0.03 + (i * (rw - 0.06)) / (n - 1)
    parts.push(
      mlib.tubeAlong(
        [
          [xx, -d / 2, 0.0],
          [xx, -d / 2 + 0.03, h],
          [xx, d / 2 - 0.03, h],
          [xx, d / 2, 0.0],
        ],
        mlib.circle(0.0032, 6),
      ),
    )
  }
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 40)
  mlib.rotateZ(ob, rotz)
  mlib.translate(ob, loc)
  w.add(ob, wire)
  // plates standing in the rack
  const pm = mats.paint('plate_white', 'EFEADC', { rough: 0.14, coat: 0.55 })
  for (let i = 0; i < 4; i++) {
    const pl = mlib.revolve(
      [
        [0.0, 0.0],
        [0.052, 0.0],
        [0.09, 0.006],
        [0.108, 0.014],
        [0.108, 0.019],
        [0.086, 0.012],
        [0.048, 0.005],
        [0.0, 0.005],
      ],
      22,
    )
    mlib.rotY(pl, Math.PI / 2)
    mlib.smoothShade(pl, 32)
    mlib.translate(pl, [-0.09 + i * 0.055, 0.0, 0.1])
    mlib.rotateZ(pl, rotz)
    mlib.translate(pl, loc)
    w.add(pl, pm)
  }
}

function knifeBlock(w: World, loc: Vec3, rotz = 0.0): void {
  const wd = mats.wood('wood_block', ['CDA062', 'A0742E', '6C4A18'], { ring: 22, warp: 0.1, warpScale: 1.4, distort: 1.4, bump: 0.16, axis: 'XY' })
  const placed: [MeshData, THREE.Material][] = []
  const b = mlib.prismXZ(
    [
      [-0.055, 0.0],
      [0.055, 0.0],
      [0.055, 0.235],
      [-0.02, 0.29],
      [-0.055, 0.27],
    ],
    -0.055,
    0.055,
  )
  mlib.bevel(b, 0.005, 2)
  placed.push([b, wd])
  const hMat = mats.paint('handle_black', '1C1A18', { rough: 0.32 })
  for (let i = 0; i < 4; i++) {
    const hl = mlib.prismXZ(
      [
        [-0.006, 0.0],
        [0.006, 0.0],
        [0.008, 0.095],
        [-0.008, 0.095],
      ],
      -0.011,
      0.011,
    )
    mlib.rotY(hl, rad(11))
    mlib.translate(hl, [0.006 - i * 0.004, -0.036 + i * 0.024, 0.268])
    placed.push([hl, hMat])
  }
  for (const [ob, mm] of placed) {
    mlib.rotateZ(ob, rotz)
    mlib.translate(ob, loc)
    w.add(ob, mm)
  }
}

function paperTowel(w: World, loc: Vec3): void {
  const pm = mats.paint('paper_white', 'F0EDE4', { rough: 0.62 })
  const rod = mlib.revolve(
    [
      [0.0, 0.0],
      [0.008, 0.0],
      [0.008, 0.3],
      [0.0, 0.3],
    ],
    10,
  )
  mlib.rotX(rod, -Math.PI / 2)
  mlib.translate(rod, loc)
  w.add(rod, mats.get('metal_chrome')!)
  const roll = mlib.revolve(
    [
      [0.024, 0.0],
      [0.058, 0.0],
      [0.058, 0.245],
      [0.024, 0.245],
    ],
    24,
  )
  mlib.rotX(roll, -Math.PI / 2)
  mlib.translate(roll, [0, 0.028, 0])
  mlib.smoothShade(roll, 24)
  mlib.translate(roll, loc)
  w.add(roll, pm)
}

function toaster(w: World, loc: Vec3, rotz = 0.0): void {
  const chr = mats.get('metal_chrome')!
  const body = mlib.prism(mlib.roundedRect(0.135, 0.235, 0.04, 5), 0.01, 0.165)
  mlib.bevel(body, 0.01, 2)
  mlib.smoothShade(body, 40)
  mlib.rotateZ(body, rotz)
  mlib.translate(body, loc)
  w.add(body, chr)
  const slotMat = mats.paint('slot_dark', '191817', { rough: 0.5 })
  for (const s of [-1, 1]) {
    const sl = mlib.box(-0.03, s * 0.045 - 0.014, 0.155, 0.03, s * 0.045 + 0.014, 0.168)
    mlib.rotateZ(sl, rotz)
    mlib.translate(sl, loc)
    w.add(sl, slotMat)
  }
}

/** Black wrought double hook on the wall beside the door. */
function coatHook(w: World, loc: Vec3): void {
  const parts: MeshData[] = []
  parts.push(
    mlib.prismYZ(
      [
        [-0.016, -0.052],
        [0.016, -0.052],
        [0.021, -0.03],
        [0.021, 0.03],
        [0.016, 0.052],
        [-0.016, 0.052],
        [-0.021, 0.03],
        [-0.021, -0.03],
      ],
      0.0,
      0.01,
    ),
  )
  const arms: [number, number, number][] = [
    [0.032, 0.068, 0.04],
    [-0.028, 0.092, -0.046],
  ]
  for (const [z0, reach, tip] of arms) {
    const pts: Vec3[] = []
    for (let i = 0; i < 13; i++) {
      const t = i / 12.0
      pts.push([0.008 + reach * Math.sin(t * 1.35), 0.0, z0 + tip * (1.0 - Math.cos(t * 2.05)) * 0.62 - reach * 0.22 * t * t])
    }
    const arm = mlib.tubeAlong(pts, mlib.circle(0.0058, 8), { up: [0, 1, 0] })
    mlib.smoothShade(arm, 40)
    parts.push(arm)
  }
  const ob = mlib.join(parts)
  mlib.translate(ob, loc)
  w.add(ob, mats.paint('iron_hook_black', '1A1A1C', { rough: 0.42, bump: 0.1, noise: 300 }))
}

/** Small dark frame slung from a leather strap up to a single nail, with a
 * pair of bullion tassels off its lower edge. */
function strapFrame(w: World, loc: Vec3, fw = 0.205, fh = 0.145): void {
  const placed: [MeshData, THREE.Material][] = []
  const prof: Vec2[] = [
    [0.0, 0.0],
    [0.0, 0.02],
    [0.006, 0.026],
    [0.014, 0.026],
    [0.018, 0.02],
    [0.018, 0.0],
  ]
  const fr = mlib.sweepRectFrame(fw, fh, prof)
  placed.push([
    fr,
    mats.wood('wood_frame_dark', ['4A3220', '3A2616', '281809'], { ring: 30.0, warp: 0.02, distort: 0.3, bump: 0.1, rough: [0.3, 0.46], axis: 'XZ' }),
  ])
  const pane = mlib.box(-fw / 2 + 0.02, 0.008, -fh / 2 + 0.02, fw / 2 - 0.02, 0.013, fh / 2 - 0.02)
  placed.push([pane, mats.paint('frame_mount_pale', 'D9D6CA', { rough: 0.42 })])
  const NAIL: Vec3 = [0.0, 0.006, fh / 2 + 0.135]
  const lea = mats.paint('leather_strap', '6B4A2C', { rough: 0.62, bump: 0.14, noise: 340 })
  for (const s of [-1, 1]) {
    const a: Vec3 = [s * (fw / 2 - 0.016), 0.004, fh / 2 - 0.006]
    const st = mlib.tubeAlong(
      [a, [(a[0] + NAIL[0]) * 0.5, 0.005, (a[2] + NAIL[2]) * 0.5], NAIL],
      mlib.roundedRect(0.011, 0.0035, 0.0015, 2),
      { up: [0, 1, 0] },
    )
    mlib.smoothShade(st, 40)
    placed.push([st, lea])
  }
  const gold = mats.metal('metal_tassel_gold', 'B9922F', { rough: 0.42, bump: 0.06 })
  for (const s of [-1, 1]) {
    const tx = s * fw * 0.24
    const cd = mlib.tubeAlong(
      [
        [tx, 0.006, -fh / 2 + 0.004],
        [tx, 0.006, -fh / 2 - 0.03],
      ],
      mlib.circle(0.0022, 6),
    )
    placed.push([cd, gold])
    const hd = mlib.revolve(
      [
        [0.0, 0.0],
        [0.011, -0.006],
        [0.013, -0.016],
        [0.009, -0.024],
        [0.0, -0.026],
      ],
      14,
    )
    mlib.translate(hd, [tx, 0.006, -fh / 2 - 0.028])
    mlib.smoothShade(hd, 40)
    placed.push([hd, gold])
    const sk = mlib.revolve(
      [
        [0.01, 0.0],
        [0.015, -0.02],
        [0.016, -0.044],
        [0.012, -0.056],
        [0.0, -0.058],
      ],
      16,
    )
    mlib.translate(sk, [tx, 0.006, -fh / 2 - 0.048])
    mlib.smoothShade(sk, 44)
    placed.push([sk, gold])
  }
  for (const [ob, mm] of placed) {
    mlib.rotateZ(ob, -Math.PI / 2)
    mlib.translate(ob, loc)
    w.add(ob, mm)
  }
}

export function build(w: World): void {
  const { dir, len: cl } = L.chamferDir()
  const [dxc, dyc] = dir
  const inw = Math.atan2(-dxc, dyc)
  // north-run counter: coffee maker, mixer, toaster, knife block
  coffeeMaker(w, [1.28, L.NY - 0.34, CTR_H], rad(4))
  standMixer(w, [1.72, L.NY - 0.34, CTR_H], rad(-14))
  toaster(w, [2.06, L.NY - 0.32, CTR_H], rad(8))
  const kp = L.chamferPt(0.3, 0.3)
  knifeBlock(w, [kp[0], kp[1], CTR_H], inw + rad(10))
  // chamfer counter beside the sink: dish rack + paper towel
  const p = L.chamferPt(cl - 0.3, 0.34)
  dishRack(w, [p[0], p[1], CTR_H + 0.002], inw + rad(-8))
  paperTowel(w, [0.095, L.KIT_WEDGE[0] + 0.3, 1.395])
  // the lavender wall north of the front door: coat hook and hanging frame
  const my = (L.FD_Y[1] + L.W_PLASTER[1]) * 0.5
  coatHook(w, [0.02, my + 0.012, 1.8])
  strapFrame(w, [0.02, my, 1.385], 0.136, 0.104)
}
