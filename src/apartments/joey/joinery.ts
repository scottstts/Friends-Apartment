/** Five-panel doors and double-hung windows from s_openings.py. */
import { MeshData, type Vec2 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import * as L from './layout'
import * as P from './props'
import { casingProfile, toWall } from './walls'

export interface DoorParts {
  lining: MeshData
  casing: MeshData
  leaf: MeshData
  hinges: MeshData
  knob?: MeshData
}

export interface WindowParts {
  frame: MeshData
  glass: MeshData
  casing: MeshData
  blind?: MeshData
}

export function raisedPanel(x0: number, z0: number, x1: number, z1: number, y0: number, y1: number, inset = 0.032, proud = 0.008): MeshData {
  const md = mlib.join([
    mlib.box(x0, y0, z0, x1, y1, z1),
    mlib.box(x0 + inset, y0 - proud, z0 + inset, x1 - inset, y1 + proud, z1 - inset),
  ])
  return mlib.bevel(md, proud * 0.9, 3)
}

export function panelDoor(
  width: number,
  height: number,
  thickness = 0.042,
  panels = 5,
  options: { stile?: number; topRail?: number; bottomRail?: number; middleRail?: number; sink?: number } = {},
): MeshData {
  const stile = options.stile ?? 0.112
  const topRail = options.topRail ?? 0.108
  const bottomRail = options.bottomRail ?? 0.216
  const middleRail = options.middleRail ?? 0.08
  const sink = options.sink ?? 0.01
  const innerHeight = height - topRail - bottomRail - middleRail * (panels - 1)
  const shares = Array.from({ length: panels }, (_, i) => (i === panels - 1 ? 1.36 : 1))
  const total = shares.reduce((sum, value) => sum + value, 0)
  const heights = shares.map((share) => (innerHeight * share) / total)
  const x0 = stile
  const x1 = width - stile
  const parts = [
    mlib.box(0, 0, 0, stile, thickness, height),
    mlib.box(width - stile, 0, 0, width, thickness, height),
    mlib.box(x0, 0, 0, x1, thickness, bottomRail),
    mlib.box(x0, 0, height - topRail, x1, thickness, height),
  ]
  let z = bottomRail
  heights.forEach((panelHeight, i) => {
    parts.push(raisedPanel(x0 - 0.006, z, x1 + 0.006, z + panelHeight, sink, thickness - sink))
    z += panelHeight
    if (i < panels - 1) {
      parts.push(mlib.box(x0, 0, z, x1, thickness, z + middleRail))
      z += middleRail
    }
  })
  return mlib.bevel(mlib.join(parts), 0.0018, 2)
}

export function doorHardware(width: number, thickness: number, hingeLeft = true, z = 1.02): MeshData {
  const parts: MeshData[] = []
  const x = hingeLeft ? width - 0.085 : 0.085
  for (const [y, direction] of [[0, -1], [thickness, 1]] as const) {
    const rose = P.lathe([[0, 0], [0.031, 0], [0.033, 0.006], [0.03, 0.011], [0, 0.012]], 24)
    const knob = P.lathe([[0, 0.011], [0.011, 0.013], [0.012, 0.031], [0.021, 0.046], [0.026, 0.063], [0.022, 0.077], [0.012, 0.084], [0, 0.086]], 24, 42)
    for (const md of [rose, knob]) {
      mlib.rotX(md, Math.PI * 0.5 * direction)
      mlib.translate(md, [x, y, z])
      parts.push(md)
    }
  }
  return mlib.bevel(mlib.join(parts), 0.0012, 2)
}

export function hinges(height: number, thickness: number, x: number): MeshData {
  const parts = [0.26, height * 0.52, height - 0.24].map((z) => mlib.box(x - 0.004, -0.006, z - 0.048, x + 0.004, thickness + 0.006, z + 0.048))
  return mlib.bevel(mlib.join(parts), 0.0015, 2)
}

function trimBottom(md: MeshData): MeshData {
  const keep = md.faces.map((face, index) => ({ face, index })).filter(({ face }) => face.some((vi) => md.verts[vi][2] >= -1e-5))
  md.faces = keep.map(({ face }) => face)
  if (md.uvs) md.uvs = keep.map(({ index }) => md.uvs![index])
  return md
}

export function casing(width: number, height: number, options: { casingWidth?: number; depth?: number; reveal?: number; cutBottom?: boolean } = {}): MeshData {
  const reveal = options.reveal ?? 0.006
  const md = mlib.sweepRectFrame(width + reveal * 2, height + reveal * 2, casingProfile(options.casingWidth ?? 0.115, options.depth ?? 0.021))
  mlib.translate(md, [width * 0.5, 0, height * 0.5])
  if (options.cutBottom !== false) trimBottom(md)
  return mlib.bevel(md, 0.0015, 2)
}

export function bothCasings(width: number, height: number, wallThickness: number, options: { casingWidth?: number; depth?: number } = {}): MeshData {
  const a = casing(width, height, { casingWidth: options.casingWidth, depth: options.depth })
  mlib.scaleMesh(a, [1, -1, 1])
  const b = casing(width, height, { casingWidth: options.casingWidth, depth: options.depth })
  mlib.translate(b, [0, wallThickness, 0])
  const md = mlib.join([a, b])
  mlib.recalcNormals(md)
  return md
}

export function makeDoor(
  p0: Vec2,
  p1: Vec2,
  u0: number,
  width: number,
  height: number,
  options: { thickness?: number; swing?: number; hingeLeft?: boolean; wallThickness?: number; knob?: boolean } = {},
): DoorParts {
  const thickness = options.thickness ?? 0.042
  const wallThickness = options.wallThickness ?? L.TW
  const hingeLeft = options.hingeLeft ?? true
  const withKnob = options.knob ?? true
  const liningThickness = wallThickness - 0.004
  const lining = mlib.bevel(mlib.join([
    mlib.box(u0, 0, 0, u0 + 0.022, liningThickness, height),
    mlib.box(u0 + width - 0.022, 0, 0, u0 + width, liningThickness, height),
    mlib.box(u0, 0, height - 0.022, u0 + width, liningThickness, height),
  ]), 0.002, 2)
  toWall(lining, p0, p1, 0, 0, true)

  const casingMd = bothCasings(width, height, wallThickness)
  mlib.translate(casingMd, [u0, 0, 0])
  toWall(casingMd, p0, p1, 0, 0, true)

  const leafWidth = width - 0.01
  const leafHeight = height - 0.012
  const leaf = panelDoor(leafWidth, leafHeight, thickness)
  const hingeMd = hinges(leafHeight, thickness, hingeLeft ? 0 : leafWidth)
  const knobMd = withKnob ? doorHardware(leafWidth, thickness, hingeLeft) : undefined
  const group = [leaf, hingeMd, ...(knobMd ? [knobMd] : [])]
  const swing = options.swing ?? 0
  const angle = hingeLeft ? swing : -swing
  const towardNegative = hingeLeft ? angle < 0 : angle > 0
  const y0 = (wallThickness - thickness) * 0.5
  const pivot: Vec2 = [hingeLeft ? 0 : leafWidth, towardNegative ? y0 : y0 + thickness]
  for (const md of group) {
    mlib.translate(md, [0, y0, 0.006])
    if (swing) mlib.rotateZ(md, angle, pivot)
    mlib.translate(md, [u0 + 0.005, 0, 0])
    toWall(md, p0, p1, 0, 0, true)
  }
  return { lining, casing: casingMd, leaf, hinges: hingeMd, knob: knobMd }
}

export function sashWindow(width: number, height: number, thickness: number, columns = 2, frame = 0.05, glazing = 0.02, meetingRail = 0.036): [MeshData, MeshData] {
  const parts: MeshData[] = []
  const glass: MeshData[] = []
  const liningThickness = thickness - 0.004
  parts.push(mlib.box(0, 0, 0, 0.022, liningThickness, height))
  parts.push(mlib.box(width - 0.022, 0, 0, width, liningThickness, height))
  parts.push(mlib.box(0, 0, height - 0.022, width, liningThickness, height))
  parts.push(mlib.box(-0.032, -0.055, -0.04, width + 0.032, liningThickness, 0))
  parts.push(mlib.box(0.014, -0.032, -0.15, width - 0.014, -0.004, -0.04))
  parts.push(mlib.prismXZ([[-0.02, 0], [width + 0.02, 0], [width + 0.02, -0.038], [-0.02, -0.058]], thickness - 0.006, thickness + 0.08))
  const sashHeight = (height - meetingRail) * 0.5
  const sashes: [number, number, number][] = [
    [0, sashHeight + meetingRail, thickness - 0.024 - glazing],
    [sashHeight, height - 0.022, thickness - 0.062 - glazing],
  ]
  sashes.forEach(([z0, z1, y], k) => {
    const sashWidth = width - 0.046
    const x0 = 0.023
    parts.push(mlib.box(x0, y, z0, x0 + frame, y + glazing, z1))
    parts.push(mlib.box(x0 + sashWidth - frame, y, z0, x0 + sashWidth, y + glazing, z1))
    parts.push(mlib.box(x0, y, z0, x0 + sashWidth, y + glazing, z0 + frame))
    parts.push(mlib.box(x0, y, z1 - frame, x0 + sashWidth, y + glazing, z1))
    const clearWidth = sashWidth - frame * 2
    for (let i = 1; i < columns; i++) {
      const x = x0 + frame + (clearWidth * i) / columns
      parts.push(mlib.box(x - 0.01, y + 0.004, z0 + frame, x + 0.01, y + glazing - 0.004, z1 - frame))
    }
    glass.push(mlib.box(x0 + frame * 0.62, y + glazing * 0.42, z0 + frame * 0.62, x0 + sashWidth - frame * 0.62, y + glazing * 0.58, z1 - frame * 0.62))
    void k
  })
  const frameMd = mlib.bevel(mlib.join(parts), 0.0016, 2)
  return [frameMd, mlib.join(glass)]
}

export function venetianBlind(width: number, height: number, options: { slat?: number; drop?: number; tilt?: number; y?: number } = {}): MeshData {
  const slat = options.slat ?? 0.048
  const drop = options.drop ?? 0.94
  const y = options.y ?? 0
  const pitch = slat * 0.82
  const count = Math.max(1, Math.floor((height * drop - 0.07) / pitch))
  const angle = ((options.tilt ?? 56) * Math.PI) / 180
  const profile: Vec2[] = [[-slat * 0.5, 0], [-slat * 0.24, -0.0058], [slat * 0.24, -0.0058], [slat * 0.5, 0], [slat * 0.24, 0.002], [-slat * 0.24, 0.002]]
  const parts: MeshData[] = []
  for (let i = 0; i < count; i++) {
    const z = height - 0.058 - i * pitch
    const points = profile.map(([u, v]) => [y + u * Math.sin(angle) + v * Math.cos(angle), z + u * Math.cos(angle) - v * Math.sin(angle)] as Vec2)
    parts.push(mlib.prismYZ(points, 0.012, width - 0.012))
  }
  parts.push(mlib.box(0, y - 0.032, height - 0.058, width, y + 0.032, height))
  const bottom = height - 0.058 - count * pitch
  parts.push(mlib.box(0.014, y - 0.021, bottom - 0.021, width - 0.014, y + 0.021, bottom))
  for (const x of [width * 0.22, width * 0.78]) parts.push(mlib.box(x - 0.0022, y - 0.0022, bottom, x + 0.0022, y + 0.0022, height - 0.058))
  const md = mlib.join(parts)
  mlib.smoothShade(md, 34)
  return md
}

export function makeWindow(
  p0: Vec2,
  p1: Vec2,
  u0: number,
  width: number,
  sill: number,
  head: number,
  options: { wallThickness?: number; columns?: number; blind?: boolean; blindDrop?: number; blindTilt?: number } = {},
): WindowParts {
  const wallThickness = options.wallThickness ?? L.TW
  const height = head - sill
  const [frame, glass] = sashWindow(width, height, wallThickness, options.columns ?? 2)
  for (const md of [frame, glass]) {
    mlib.translate(md, [u0, 0, sill])
    toWall(md, p0, p1, 0, 0, true)
  }
  const casingMd = bothCasings(width, height, wallThickness, { casingWidth: 0.098 })
  mlib.translate(casingMd, [u0, 0, sill])
  toWall(casingMd, p0, p1, 0, 0, true)
  let blind: MeshData | undefined
  if (options.blind !== false) {
    blind = venetianBlind(width - 0.034, height - 0.012, { drop: options.blindDrop ?? 0.94, tilt: options.blindTilt ?? 56, y: wallThickness - 0.085 })
    mlib.translate(blind, [u0 + 0.017, 0, sill])
    toWall(blind, p0, p1, 0, 0, true)
  }
  return { frame, glass, casing: casingMd, blind }
}
