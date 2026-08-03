/** Central Perk tables from f_tables.py: cast-iron pub pedestals with a
 * turned baluster and scalloped foot, and the reclaimed-pine coffee table on
 * bobbin legs.  Local frame: modelled on z = 0 at the origin, moved to their
 * anchors by the caller. */
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
  M.iron('table_iron', '1C1E1C', 0.46)
  M.wood('table_pine', { light: 'C9A971', dark: '8A7444', ring: 18, scale: 0.55, rough: [0.4, 0.62] })
  M.wood('table_pine_green', { light: 'C6A96E', dark: '8A7A48', ring: 16, scale: 0.5, rough: [0.44, 0.66] })
  M.wood('table_walnut', { light: '6E4826', dark: '2A1608', ring: 28, scale: 1 })
  M.wood('table_mahog', { light: '7A3A22', dark: '34160C', ring: 32, scale: 0.9 })
}

// ------------------------------------------------------------- cast-iron base

/** Pub-table pedestal: scalloped foot, knopped baluster, spider top.  The
 * scallop squeezes the revolve's radius with a cosine of the sweep angle. */
function ironBase(h = 0.7, foot = 0.21): MeshData {
  const prof: Vec2[] = [
    [0, 0],
    [foot, 0],
    [foot * 0.97, 0.02],
    [foot * 0.72, 0.036],
    [foot * 0.55, 0.055],
    [foot * 0.42, 0.058],
    [0.07, 0.085],
    [0.058, 0.105],
    [0.07, 0.12],
    [0.052, 0.15],
    [0.044, 0.2],
    [0.062, 0.24],
    [0.07, 0.268],
    [0.058, 0.3],
    [0.036, 0.36],
    [0.031, h - 0.17],
    [0.044, h - 0.13],
    [0.038, h - 0.105],
    [0.03, h - 0.07],
    [0.105, h - 0.03],
    [0.112, h - 0.014],
    [0, h - 0.012],
  ]
  const seg = 48
  const rings: Vec3[][] = []
  for (let s = 0; s < seg; s++) {
    const a = (TAU * s) / seg
    const lobeK = 1 + 0.3 * Math.cos(4 * a)
    rings.push(
      prof.map(([r, z]) => {
        const k = z < 0.075 && r > 0.09 ? lobeK : 1
        return [r * k * Math.cos(a), r * k * Math.sin(a), z] as Vec3
      }),
    )
  }
  const md = mlib.loft(rings, { closeU: true, weldPoles: true, capStart: true, capEnd: true })
  mlib.smoothShade(md, 38)
  return md
}

/** Round pedestal table; the top is a real slab with a moulded edge. */
export function pedTable(cx: number, cy: number, r = 0.34, h = 0.735, top: 'table_walnut' | 'table_mahog' = 'table_walnut', thick = 0.036): Placed[] {
  mats()
  const base = ironBase(h - thick)
  const tp = mlib.revolve(
    [
      [0, 0],
      [r - 0.014, 0],
      [r - 0.004, 0.006],
      [r, 0.016],
      [r - 0.003, thick - 0.008],
      [r - 0.012, thick],
      [0, thick],
    ],
    44,
  )
  mlib.smoothShade(tp, 36)
  mlib.translate(tp, [0, 0, h - thick])
  for (const o of [base, tp]) mlib.translate(o, [cx, cy, 0])
  return [
    { md: base, mat: M.get('table_iron') },
    { md: tp, mat: M.get(top) },
  ]
}

// ------------------------------------------------------------- coffee table

/** A turned leg; the bobbin profile is the coffee table's. */
export function turnedLeg(h: number, r = 0.048, style: 'bobbin' | 'taper' = 'bobbin'): MeshData {
  let prof: Vec2[]
  if (style === 'bobbin') {
    prof = [
      [0, 0],
      [r * 0.7, 0],
      [r * 0.62, 0.016],
      [r * 0.4, 0.03],
      [r * 0.52, 0.048],
      [r * 0.86, 0.09],
      [r * 0.94, 0.128],
      [r * 0.62, 0.168],
      [r * 0.5, 0.186],
      [r * 0.68, 0.206],
      [r * 0.98, 0.25],
      [r * 1.02, 0.292],
      [r * 0.66, 0.336],
      [r * 0.52, 0.356],
      [r * 0.7, 0.378],
      [r * 0.96, 0.42],
      [r * 0.92, h - 0.075],
      [r * 0.72, h - 0.07],
      [r * 0.78, h - 0.06],
    ]
  } else {
    prof = [
      [0, 0],
      [r * 0.75, 0],
      [r * 0.7, 0.02],
      [r * 0.45, 0.055],
      [r * 0.85, 0.115],
      [r * 0.72, 0.18],
      [r * 0.56, h * 0.62],
      [r * 0.7, h - 0.09],
      [r * 0.8, h - 0.07],
    ]
  }
  prof = prof.filter((p) => p[1] <= h)
  prof.push([r * 1.02, h - 0.06], [r * 1.02, h], [0, h])
  const md = mlib.revolve(prof, 22)
  mlib.smoothShade(md, 40)
  return md
}

/** A tabletop made of separate boards with a real gap between them. */
function plankTop(w: number, d: number, t: number, nplank: number, gap = 0.004, z = 0): MeshData[] {
  const out: MeshData[] = []
  const pitch = d / nplank
  for (let i = 0; i < nplank; i++) {
    const y0 = -d / 2 + i * pitch + gap * 0.5
    const y1 = -d / 2 + (i + 1) * pitch - gap * 0.5
    const cup = 0.0016 * (i % 2 ? 1 : -1)
    const b = mlib.box(-w / 2, y0, z, w / 2, y1, z + t)
    mlib.bevel(b, 0.0035, 2)
    mlib.translate(b, [0, 0, cup])
    out.push(b)
  }
  return out
}

/** The pine table in front of the couch: boards on a chunky apron, turned
 * bobbin legs, a lower shelf stretcher. */
export function coffeeTable(cx: number, cy: number, w = 1.57, d = 0.88, h = 0.44): Placed[] {
  mats()
  const parts: MeshData[] = []
  const t = 0.052
  parts.push(...plankTop(w, d, t, 4, 0.004, h - t))
  const ax = w / 2 - 0.075
  const ay = d / 2 - 0.075
  const rails: [Vec2, Vec2][] = [
    [[-ax, -ay], [ax, -ay]],
    [[-ax, ay], [ax, ay]],
    [[-ax, -ay], [-ax, ay]],
    [[ax, -ay], [ax, ay]],
  ]
  for (const [p0, p1] of rails) {
    parts.push(
      mlib.tubeAlong(
        [
          [p0[0], p0[1], h - t - 0.055],
          [p1[0], p1[1], h - t - 0.055],
        ],
        mlib.roundedRect(0.026, 0.09, 0.006, 2),
      ),
    )
  }
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const lg = turnedLeg(h - t, 0.05)
      mlib.translate(lg, [sx * ax, sy * ay, 0])
      parts.push(lg)
    }
  }
  for (const sy of [-1, 1]) {
    parts.push(
      mlib.tubeAlong(
        [
          [-ax, sy * ay, 0.145],
          [ax, sy * ay, 0.145],
        ],
        mlib.roundedRect(0.03, 0.048, 0.006, 2),
      ),
    )
  }
  parts.push(
    mlib.tubeAlong(
      [
        [0, -ay, 0.145],
        [0, ay, 0.145],
      ],
      mlib.roundedRect(0.03, 0.048, 0.006, 2),
    ),
  )
  const md = mlib.join(parts)
  mlib.translate(md, [cx, cy, 0])
  return [{ md, mat: M.get('table_pine_green') }]
}

/** The oval/rectangular low tables: moulded top on turned legs. */
export function lowTable(
  cx: number,
  cy: number,
  w: number,
  d: number,
  h = 0.42,
  woodName: 'table_walnut' | 'table_mahog' = 'table_walnut',
  oval = false,
): Placed[] {
  mats()
  const parts: MeshData[] = []
  const t = 0.034
  const pts: Vec2[] = oval
    ? Array.from({ length: 44 }, (_, i) => {
        const a = (TAU * i) / 44
        return [w * 0.5 * Math.cos(a), d * 0.5 * Math.sin(a)] as Vec2
      })
    : mlib.roundedRect(w, d, 0.055, 5)
  const levels: [number, number][] = [
    [-0.01, 0],
    [0, 0.008],
    [0.002, t - 0.008],
    [-0.01, t],
  ]
  const rings = levels.map(([o, dz]) => G.polyOffset(pts, o).map(([x, y]) => [x, y, h - t + dz] as Vec3))
  const top = mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
  mlib.smoothShade(top, 34)
  parts.push(top)
  const ax = w / 2 - 0.11
  const ay = d / 2 - 0.085
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      const lg = turnedLeg(h - t, 0.04, 'taper')
      mlib.translate(lg, [sx * ax, sy * ay, 0])
      parts.push(lg)
    }
  }
  for (const sy of [-1, 1]) {
    parts.push(
      mlib.tubeAlong(
        [
          [-ax, sy * ay, h - t - 0.045],
          [ax, sy * ay, h - t - 0.045],
        ],
        mlib.roundedRect(0.022, 0.06, 0.005, 2),
      ),
    )
  }
  const md = mlib.join(parts)
  mlib.translate(md, [cx, cy, 0])
  return [{ md, mat: M.get(woodName) }]
}
