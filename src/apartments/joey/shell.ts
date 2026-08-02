/** Apartment 19 shell: direct build_shell.py plan compilation. */
import type { Vec2 } from '../../lib/mesh'
import type * as THREE from 'three/webgpu'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import { buildParquet, type Region } from './floor'
import * as L from './layout'
import * as M from './materials'
import * as T from './tiles'
import * as W from './walls'

const PAD = 0.002

function along(p0: Vec2, p1: Vec2, point: Vec2): number {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  return ((point[0] - p0[0]) * dx + (point[1] - p0[1]) * dy) / length
}

function hole(p0: Vec2, p1: Vec2, a: Vec2, b: Vec2, z0: number, z1: number): W.Hole {
  const ua = along(p0, p1, a)
  const ub = along(p0, p1, b)
  return [Math.min(ua, ub) - PAD, z0 - PAD, Math.max(ua, ub) + PAD, z1 + PAD]
}

function offsetPolygon(poly: Vec2[], distance: number): Vec2[] {
  return poly.map((point, i) => {
    const a = poly[(i - 1 + poly.length) % poly.length]
    const b = poly[(i + 1) % poly.length]
    const t0: Vec2 = [point[0] - a[0], point[1] - a[1]]
    const t1: Vec2 = [b[0] - point[0], b[1] - point[1]]
    const l0 = Math.hypot(...t0) || 1
    const l1 = Math.hypot(...t1) || 1
    const n0: Vec2 = [t0[1] / l0, -t0[0] / l0]
    const n1: Vec2 = [t1[1] / l1, -t1[0] / l1]
    return [point[0] + distance * (n0[0] + n1[0]), point[1] + distance * (n0[1] + n1[1])] as Vec2
  })
}

function buildMaterials(): void {
  M.plaster('M_Wall', L.WALL, { rough: 0.88, bump: 0.36, patch: 0.055 })
  M.plaster('M_WallBed', M.shade(L.WALL, 1.04), { rough: 0.86, bump: 0.34, patch: 0.05 })
  M.plaster('M_WallBath', 'C8CEC2', { rough: 0.84, bump: 0.3, patch: 0.05 })
  M.ceilingPaint('M_Ceiling', L.CEIL)
  M.paint('M_Trim', L.TRIM, { rough: 0.3, coat: 0.12, brush: 0.6 })
  M.paint('M_TrimW', M.shade(L.TRIM, 1.03), { rough: 0.26, coat: 0.18, brush: 0.5 })
  M.wood('M_Parquet', ['D8C29E', 'BEA47E', '96805A'], {
    ring: 28,
    warp: 0.22,
    rough: [0.19, 0.42],
    coord: 'UV',
    axis: 'Y',
    bump: 0.07,
    pore: 1,
    tintAttr: 'ptint',
    scale: 1,
    aniso: 0.28,
    distort: 0.8,
    grainRelief: 0.05,
  })
  M.tile('M_BathFloorTile', 'C6B79E', '8E8271', { size: 0.152, joint: 0.009, rough: 0.24, relief: 0.5, plane: 'XY' })
  M.ceramic('M_BathTileGlaze', 'E7EAE3', { rough: 0.075, pitch: T.PITCH })
}

/** Register the wall body with gaps in exactly the same local-u coordinates
 * used by the manifold mesh. */
function collideWall(world: World, p0: Vec2, p1: Vec2, thickness: number, gaps: [number, number][] = []): void {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  const ux = dx / length
  const uy = dy / length
  const nx = uy
  const ny = -ux
  const spans: [number, number][] = []
  let cursor = 0
  for (const [start, end] of [...gaps].sort((a, b) => a[0] - b[0])) {
    if (start > cursor) spans.push([cursor, start])
    cursor = Math.max(cursor, end)
  }
  if (cursor < length) spans.push([cursor, length])
  for (const [start, end] of spans) {
    const middle = (start + end) * 0.5
    world.obb(p0[0] + ux * middle + nx * thickness * 0.5, p0[1] + uy * middle + ny * thickness * 0.5, (end - start) * 0.5, thickness * 0.5, Math.atan2(dy, dx))
  }
}

function addWall(world: World, p0: Vec2, p1: Vec2, thickness: number, z0: number, z1: number, material: THREE.Material, holes: W.Hole[] = [], gaps: [number, number][] = []): ReturnType<typeof W.wall> {
  const md = W.wall(p0, p1, thickness, z0, z1, holes)
  world.add(md, material)
  collideWall(world, p0, p1, thickness, gaps)
  return md
}

function buildBathroomTiles(world: World): void {
  const [x0, x1] = L.BA_X
  const [y0, y1] = L.BA_Y
  const count = T.courses(2.05)
  const material = M.get('M_BathTileGlaze')
  const runs: ReturnType<typeof T.field>[] = []
  const casing = 0.123
  const south: [Vec2, Vec2] = [[x0, y0], [x1, y0]]
  const east: [Vec2, Vec2] = [[x1, y0], [x1, y1]]
  const north: [Vec2, Vec2] = [[x1, y1], [x0, y1]]
  const west: [Vec2, Vec2] = [[x0, y1], [x0, y0]]
  runs.push(T.field(...south, 0, L.BD_X[0] - casing - x0, 0, count, { startU: 0 }))
  runs.push(T.field(...south, L.BD_X[1] + casing - x0, x1 - x0, 0, count, { startU: x1 - x0 }))
  runs.push(T.field(...east, 0, y1 - y0, 0, count, { startU: 0 }))
  runs.push(T.field(...north, 0, x1 - x0, 0, count, { startU: 0 }))
  runs.push(T.field(...west, 0, y1 - y0, 0, count, { startU: 0 }))
  world.add(mlib.join(runs.flat()), material)
}

export function build(world: World): void {
  buildMaterials()
  const wall = M.get('M_Wall')
  const wallBed = M.get('M_WallBed')
  const wallBath = M.get('M_WallBath')
  const trim = M.get('M_Trim')
  const outline = L.outline()
  const [south, east, kitchen, jog, north] = [
    [outline[0], outline[1]],
    [outline[1], outline[2]],
    [outline[2], outline[3]],
    [outline[3], outline[4]],
    [outline[4], outline[5]],
  ] as [Vec2, Vec2][]

  addWall(world, ...south, L.TW, 0, L.CZ, wall)
  const frontHole = hole(...east, [L.EX, L.FD_Y[0]], [L.EX, L.FD_Y[1]], 0, L.FD_H)
  addWall(world, ...east, L.TW, 0, L.CZ, wall, [frontHole], [[frontHole[0], frontHole[2]]])
  addWall(world, kitchen[0], [kitchen[1][0] + L.TW, kitchen[1][1]], L.TW, 0, L.CZ, wall)
  addWall(world, ...jog, L.TW, 0, L.CZ, wall)
  const northHoles = [
    hole(...north, [L.WIN_A[0], L.NY], [L.WIN_A[1], L.NY], L.WIN_SILL, L.WIN_HEAD),
    hole(...north, [L.WIN_B[0], L.NY], [L.WIN_B[1], L.NY], L.WIN_SILL, L.WIN_HEAD),
    hole(...north, [L.BD_X[0], L.NY], [L.BD_X[1], L.NY], 0, L.BD_H),
  ]
  const northMd = W.wall(...north, L.TW, 0, L.CZ, northHoles)
  W.faceMat(northMd, 1, (center, normal) => normal[1] > 0.9 && center[1] > L.NY + L.TW * 0.5)
  world.addMulti(northMd, [wall, wallBath])
  collideWall(world, ...north, L.TW, [[northHoles[2][0], northHoles[2][2]]])

  // Bedroom block.
  const bedEast: [Vec2, Vec2] = [[L.BED_E, L.JO_Y[0]], [L.BED_E, L.NY]]
  const joeyDoor = hole(...bedEast, [L.BED_E, L.JOEY_DOOR[0]], [L.BED_E, L.JOEY_DOOR[1]], 0, L.DOOR_TOP)
  const chandlerDoor = hole(...bedEast, [L.BED_E, L.CHAN_DOOR[0]], [L.BED_E, L.CHAN_DOOR[1]], 0, L.DOOR_TOP)
  const bedEastMd = W.wall(...bedEast, L.BW_TH, 0, L.CZ, [joeyDoor, chandlerDoor])
  W.faceMat(bedEastMd, 1, (center, normal) => normal[0] > 0.9 && center[0] > L.WX - 0.01)
  world.addMulti(bedEastMd, [wallBed, wall])
  collideWall(world, ...bedEast, L.BW_TH, [[joeyDoor[0], joeyDoor[2]], [chandlerDoor[0], chandlerDoor[2]]])

  const bedWest: [Vec2, Vec2] = [[L.BED_W, L.CH_Y[1] + L.TW], [L.BED_W, L.JO_Y[0] - L.TW]]
  const joeyWindow = hole(...bedWest, [L.BED_W, L.JO_WIN[0]], [L.BED_W, L.JO_WIN[1]], L.WIN_SILL, L.WIN_HEAD)
  addWall(world, ...bedWest, L.TW, 0, L.CZ, wallBed, [joeyWindow])
  const chandlerNorth: [Vec2, Vec2] = [[L.BED_E, L.CH_Y[1]], [L.BED_W, L.CH_Y[1]]]
  const chandlerWindows = L.CH_WIN.map(([a, b]) => hole(...chandlerNorth, [a, L.CH_Y[1]], [b, L.CH_Y[1]], L.WIN_SILL, L.WIN_HEAD))
  addWall(world, ...chandlerNorth, L.TW, 0, L.CZ, wallBed, chandlerWindows)
  addWall(world, [L.BED_W, L.JO_Y[0]], [L.BED_E, L.JO_Y[0]], L.TW, 0, L.CZ, wallBed)
  addWall(world, [L.BED_W, L.CH_Y[0]], [L.BED_E, L.CH_Y[0]], L.PARTY[1] - L.PARTY[0], 0, L.CZ, wallBed)

  // Bathroom exterior sides.
  const [bx0, bx1] = L.BA_X
  const [by0, by1] = L.BA_Y
  addWall(world, [bx0, by1 + L.TW], [bx0, by0], L.TW, 0, L.CZ, wallBath)
  addWall(world, [bx1, by1], [bx0, by1], L.TW, 0, L.CZ, wallBath)
  addWall(world, [bx1, L.NY], [bx1, by1 + L.TW], L.TW, 0, L.CZ, wallBath)
  if (bx1 > L.JX) addWall(world, [L.JX, by0], [bx1, by0], L.TW, 0, L.CZ, wallBath)

  // Convex-corner masonry closure.
  const cornerVoids: [number, number, number, number][] = [
    [L.WX - L.BW_TH, L.SY - L.TW, L.WX, L.SY],
    [L.WX - L.BW_TH, L.NY, L.WX, L.NY + L.TW],
    [L.EX, L.SY - L.TW, L.EX + L.TW, L.SY],
    [L.EX, L.NY2, L.EX + L.TW, L.NY2 + L.TW],
  ]
  world.add(mlib.join(cornerVoids.map(([x0, y0, x1, y1]) => mlib.box(x0, y0, 0, x1, y1, L.CZ))), wall)
  buildBathroomTiles(world)

  // Ceilings and cornices.
  const ceilingMat = M.get('M_Ceiling')
  const ceilingSpecs: [Vec2[], number][] = [
    [outline, L.CZ],
    [[[L.CH_X[0], L.CH_Y[0]], [L.CH_X[1], L.CH_Y[0]], [L.CH_X[1], L.CH_Y[1]], [L.CH_X[0], L.CH_Y[1]]], L.CZ],
    [[[L.JO_X[0], L.JO_Y[0]], [L.JO_X[1], L.JO_Y[0]], [L.JO_X[1], L.JO_Y[1]], [L.JO_X[0], L.JO_Y[1]]], L.CZ],
    [[[bx0, by0], [bx1, by0], [bx1, by1], [bx0, by1]], L.BA_CZ],
  ]
  for (const [poly, z] of ceilingSpecs) world.add(W.ceiling(offsetPolygon(poly, 0.065), z, 0.16), ceilingMat)
  const clockwise = [...outline].reverse()
  world.add(W.cornice([...clockwise, clockwise[0]], L.CZ), M.get('M_TrimW'))
  for (const [xr, yr] of [[L.CH_X, L.CH_Y], [L.JO_X, L.JO_Y]] as const) {
    const path: Vec2[] = [[xr[0], yr[0]], [xr[0], yr[1]], [xr[1], yr[1]], [xr[1], yr[0]], [xr[0], yr[0]]]
    world.add(W.cornice(path, L.CZ), M.get('M_TrimW'))
  }

  // Continuous parquet and bathroom threshold tile.
  const grow = 0.06
  const thresholds: Region[] = [
    [L.BED_E - 0.02, L.JOEY_DOOR[0] - 0.02, L.WX + 0.02, L.JOEY_DOOR[1] + 0.02],
    [L.BED_E - 0.02, L.CHAN_DOOR[0] - 0.02, L.WX + 0.02, L.CHAN_DOOR[1] + 0.02],
    [L.EX - 0.02, L.FD_Y[0] - 0.03, L.EX + L.TW - 0.04, L.FD_Y[1] + 0.03],
    [L.BD_X[0] - 0.02, L.NY - 0.02, L.BD_X[1] + 0.02, L.NY + L.TW + 0.04],
  ]
  const regions: Region[] = [
    [L.WX - grow, L.SY - grow, L.JX + grow, L.NY + grow],
    [L.JX - grow, L.SY - grow, L.EX + grow, L.NY2 + grow],
    [L.CH_X[0] - grow, L.CH_Y[0] - grow, L.CH_X[1] + grow, L.CH_Y[1] + grow],
    [L.JO_X[0] - grow, L.JO_Y[0] - grow, L.JO_X[1] + grow, L.JO_Y[1] + grow],
    ...thresholds,
  ]
  world.add(buildParquet(regions, 0, 7311, [0.03, 0.05]), M.get('M_Parquet'))
  const bathFloor = mlib.box(bx0 - grow, L.NY + L.TW - 0.03, -0.02, bx1 + grow, by1 + grow, 0.0145)
  mlib.bevel(bathFloor, 0.002, 1)
  world.add(bathFloor, M.get('M_BathFloorTile'))

  // Baseboards.
  const casing = 0.121
  const frontCasing = 0.138
  const runs: [Vec2[], number, number][] = [
    [[[L.WX, L.CHAN_DOOR[1]], [L.WX, L.NY], [L.BD_X[0], L.NY]], casing, casing],
    [[[L.BD_X[1], L.NY], [L.JX, L.NY], [L.JX, L.NY2], [L.EX, L.NY2], [L.EX, L.FD_Y[1]]], casing, frontCasing],
    [[[L.EX, L.FD_Y[0]], [L.EX, L.SY], [L.WX, L.SY], [L.WX, L.JOEY_DOOR[0]]], frontCasing, casing],
    [[[L.WX, L.JOEY_DOOR[1]], [L.WX, L.CHAN_DOOR[0]]], casing, casing],
    [[[L.BED_E, L.CHAN_DOOR[0]], [L.BED_E, L.CH_Y[0]], [L.CH_X[0], L.CH_Y[0]], [L.CH_X[0], L.CH_Y[1]], [L.BED_E, L.CH_Y[1]], [L.BED_E, L.CHAN_DOOR[1]]], casing, casing],
    [[[L.BED_E, L.JOEY_DOOR[0]], [L.BED_E, L.JO_Y[0]], [L.JO_X[0], L.JO_Y[0]], [L.JO_X[0], L.JO_Y[1]], [L.BED_E, L.JO_Y[1]], [L.BED_E, L.JOEY_DOOR[1]]], casing, casing],
  ]
  for (const [path, a, b] of runs) world.add(W.baseboard(W.trimRun(path, a, b)), trim)

  // Applied wall panels.
  const addPanels = (p0: Vec2, p1: Vec2, specs: readonly (readonly [number, number, number?, number?])[]): void => {
    for (const [center, width, z = 1.415, height = 2.1] of specs) world.add(W.wallPanel(p0, p1, center, z, width, height), trim)
  }
  addPanels(outline[0], outline[1], [[1, 1.6], [2.9, 1.6], [4.8, 1.6], [6.7, 1.6]])
  addPanels(outline[1], outline[2], [[1.55, 1.55], [5.15, 1.05]])
  const entertainmentU = L.NY - (L.ENT_Y[0] + L.ENT_Y[1]) * 0.5
  addPanels(outline[5], outline[0], [[0.95, 1.25], [entertainmentU, 3.1, 2.075, 0.8], [8.1, 0.72]])
  const jogWidth = L.NY - L.NY2
  addPanels(outline[3], outline[4], [[jogWidth * 0.5, jogWidth - 0.7]])
  addPanels([L.CH_X[0], L.CH_Y[0]], [L.CH_X[0], L.CH_Y[1]], [[1.9, 1.55]])
  addPanels([L.CH_X[1], L.CH_Y[0]], [L.CH_X[0], L.CH_Y[0]], [[1.05, 1.45], [2.7, 1.45]])
  addPanels([L.JO_X[0], L.JO_Y[1]], [L.JO_X[1], L.JO_Y[1]], [[1.05, 1.45], [2.7, 1.45]])
  addPanels([L.JO_X[1], L.JO_Y[0]], [L.JO_X[0], L.JO_Y[0]], [[1.05, 1.45], [2.7, 1.45]])
}
