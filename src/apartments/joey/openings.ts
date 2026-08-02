/** Apartment 19 doors and windows, placed on the shell's exact wall lines. */
import type { Vec2 } from '../../lib/mesh'
import type * as THREE from 'three/webgpu'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import * as J from './joinery'
import * as L from './layout'
import * as M from './materials'
import * as P from './props'
import { toWall } from './walls'

interface OpeningMaterials {
  trim: THREE.Material
  door: THREE.Material
  brass: THREE.Material
  glass: THREE.Material
  blind: THREE.Material
}

function buildMaterials(): OpeningMaterials {
  M.paint('M_Door', L.DOOR_GREY, { rough: 0.3, coat: 0.14, brush: 0.7 })
  M.paint('M_DoorFront', M.shade(L.TRIM, 1.02), { rough: 0.34, coat: 0.1, brush: 0.8 })
  M.metal('M_Brass', 'B08A3E', { rough: 0.24, brush: 0.25, grime: 0.35 })
  M.metal('M_Nickel', 'C9CBCC', { rough: 0.18, brush: 0.35, grime: 0.3 })
  M.clearGlass('M_Glass', 'EAF1F2', { rough: 0.012 })
  M.paint('M_Blind', 'E6E2D6', { rough: 0.42, coat: 0.05, brush: 0.25 })
  M.plastic('M_BoardBlue', '1F7FD0', { rough: 0.28, coat: 0.35 })
  M.plastic('M_BoardFace', 'F2F3F0', { rough: 0.16, coat: 0.45 })
  return { trim: M.get('M_Trim'), door: M.get('M_Door'), brass: M.get('M_Brass'), glass: M.get('M_Glass'), blind: M.get('M_Blind') }
}

function along(p0: Vec2, p1: Vec2, point: Vec2): number {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  return ((point[0] - p0[0]) * dx + (point[1] - p0[1]) * dy) / length
}

function addDoor(world: World, parts: J.DoorParts, materials: OpeningMaterials): void {
  world.add(parts.lining, materials.trim)
  world.add(parts.casing, materials.trim)
  world.add(parts.leaf, materials.door)
  world.add(parts.hinges, materials.brass)
  if (parts.knob) world.add(parts.knob, materials.brass)
  // All three leaves stand at 86 degrees, so their world AABB is effectively
  // the authored leaf OBB and prevents walking through the visible panel.
  world.colliderFromMesh(parts.leaf, 0.01)
}

function addWindow(world: World, parts: J.WindowParts, materials: OpeningMaterials): void {
  world.add(parts.frame, materials.trim)
  world.add(parts.casing, materials.trim)
  world.add(parts.glass, materials.glass)
  if (parts.blind) world.add(parts.blind, materials.blind)
}

function frontDoor(world: World, p0: Vec2, p1: Vec2, u0: number, width: number, height: number, wallThickness: number, materials: OpeningMaterials): void {
  const liningThickness = wallThickness - 0.004
  const lining = mlib.bevel(mlib.join([
    mlib.box(u0, 0, 0, u0 + 0.026, liningThickness, height),
    mlib.box(u0 + width - 0.026, 0, 0, u0 + width, liningThickness, height),
    mlib.box(u0, 0, height - 0.026, u0 + width, liningThickness, height),
  ]), 0.002, 2)
  toWall(lining, p0, p1, 0, 0, true)
  world.add(lining, materials.trim)

  const casing = J.bothCasings(width, height, wallThickness, { casingWidth: 0.132, depth: 0.024 })
  mlib.translate(casing, [u0, 0, 0])
  toWall(casing, p0, p1, 0, 0, true)
  world.add(casing, materials.trim)

  const leafWidth = width - 0.012
  const leafHeight = height - 0.014
  const thickness = 0.048
  const stile = 0.145
  const topRail = 0.13
  const bottomRail = 0.24
  const middleRail = 0.15
  const split = leafHeight * 0.665
  const leaf = mlib.bevel(mlib.join([
    mlib.box(0, 0, 0, stile, thickness, leafHeight),
    mlib.box(leafWidth - stile, 0, 0, leafWidth, thickness, leafHeight),
    mlib.box(stile, 0, 0, leafWidth - stile, thickness, bottomRail),
    mlib.box(stile, 0, leafHeight - topRail, leafWidth - stile, thickness, leafHeight),
    mlib.box(stile, 0, split, leafWidth - stile, thickness, split + middleRail),
    J.raisedPanel(stile - 0.007, bottomRail, leafWidth - stile + 0.007, split, 0.011, thickness - 0.011, 0.042, 0.009),
    J.raisedPanel(stile - 0.007, split + middleRail, leafWidth - stile + 0.007, leafHeight - topRail, 0.011, thickness - 0.011, 0.042, 0.009),
  ]), 0.002, 2)
  const hardware = J.doorHardware(leafWidth, thickness, false, 1.04)
  const hinges = J.hinges(leafHeight, thickness, leafWidth)

  // Reachable deadbolt, latch, chain and peephole from build_openings.py.
  const iron: ReturnType<typeof mlib.join>[] = []
  const keyX = 0.094
  const rose = (x: number, z: number, radius = 0.03): ReturnType<typeof P.lathe> => P.faceY(P.lathe([[0, 0], [radius, 0], [radius, 0.0033], [radius * 0.82, 0.006], [0, 0.007]], 26), -1, [x, 0, z])
  const lock = (z: number, radius = 0.031): void => {
    iron.push(rose(keyX, z, radius))
    iron.push(P.faceY(P.lathe([[0, 0], [0.021, 0], [0.021, 0.016], [0.016, 0.021], [0, 0.021]], 24), -1, [keyX, -0.005, z]))
    iron.push(mlib.bevel(mlib.box(keyX - 0.008, -0.049, z - 0.03, keyX + 0.008, -0.04, z + 0.03), 0.0035, 3))
  }
  lock(1.2)
  lock(1.455, 0.027)
  iron.push(mlib.bevel(mlib.box(0.052, -0.011, 1.688, 0.168, 0, 1.716), 0.004, 3))
  for (let i = 0; i < 8; i++) {
    const t = i / 7
    const x = 0.062 + 0.026 * Math.sin(t * 2.4)
    const z = 1.686 - t * 0.128
    const link = P.torus(0.009, 0.0021, 14, 6, [x, -0.018, z])
    mlib.rotX(link, Math.PI * 0.5, [x, -0.018, z])
    if (i % 2) mlib.rotY(link, Math.PI * 0.5, [x, -0.018, z])
    iron.push(link)
  }
  iron.push(rose(leafWidth * 0.5, 1.545, 0.019))
  const ironwork = mlib.bevel(mlib.join(iron), 0.0015, 2)
  const board = mlib.bevel(mlib.box(leafWidth * 0.52 - 0.155, -0.016, 1.62, leafWidth * 0.52 + 0.155, 0, 1.86), 0.005, 3)
  const boardFace = mlib.box(leafWidth * 0.52 - 0.126, -0.018, 1.645, leafWidth * 0.52 + 0.126, -0.014, 1.835)

  for (const md of [leaf, hardware, hinges, ironwork, board, boardFace]) {
    mlib.translate(md, [u0 + 0.006, (wallThickness - thickness) * 0.5, 0.007])
    toWall(md, p0, p1, 0, 0, true)
  }
  world.add(leaf, M.get('M_DoorFront'))
  world.add(hardware, materials.brass)
  world.add(hinges, materials.brass)
  world.add(ironwork, materials.brass)
  world.add(board, M.get('M_BoardBlue'))
  world.add(boardFace, M.get('M_BoardFace'))
  // The apartment front door remains closed; the interaction sits on its
  // interior side and returns to the hallway without making the leaf porous.
  const centerU = u0 + width * 0.5
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  const ux = dx / length
  const uy = dy / length
  const wx = p0[0] + ux * centerU
  const wy = p0[1] + uy * centerU
  world.obb(wx, wy, width * 0.5, thickness * 0.5 + 0.012, Math.atan2(uy, ux), 0, height)
}

export function build(world: World): void {
  const materials = buildMaterials()
  const north0: Vec2 = [L.JX, L.NY]
  const north1: Vec2 = [L.WX, L.NY]
  const east0: Vec2 = [L.EX, L.SY]
  const east1: Vec2 = [L.EX, L.NY2]
  const bed0: Vec2 = [L.BED_E, L.JO_Y[0]]
  const bed1: Vec2 = [L.BED_E, L.NY]
  const west0: Vec2 = [L.BED_W, L.CH_Y[1] + L.TW]
  const west1: Vec2 = [L.BED_W, L.JO_Y[0] - L.TW]
  const chandler0: Vec2 = [L.BED_E, L.CH_Y[1]]
  const chandler1: Vec2 = [L.BED_W, L.CH_Y[1]]

  for (const [a, b] of [L.WIN_A, L.WIN_B]) {
    const u0 = Math.min(along(north0, north1, [a, L.NY]), along(north0, north1, [b, L.NY]))
    addWindow(world, J.makeWindow(north0, north1, u0, b - a, L.WIN_SILL, L.WIN_HEAD, { wallThickness: L.TW, columns: 2, blindDrop: 0.95, blindTilt: 54 }), materials)
  }

  const open = (L.DOOR_OPEN * Math.PI) / 180
  let u0 = Math.min(along(north0, north1, [L.BD_X[0], L.NY]), along(north0, north1, [L.BD_X[1], L.NY]))
  addDoor(world, J.makeDoor(north0, north1, u0, L.BD_X[1] - L.BD_X[0], L.BD_H, { wallThickness: L.TW, swing: open, hingeLeft: false }), materials)
  u0 = Math.min(along(bed0, bed1, [L.BED_E, L.JOEY_DOOR[0]]), along(bed0, bed1, [L.BED_E, L.JOEY_DOOR[1]]))
  addDoor(world, J.makeDoor(bed0, bed1, u0, L.JOEY_DOOR[1] - L.JOEY_DOOR[0], L.DOOR_TOP, { wallThickness: L.BW_TH, swing: -open, hingeLeft: true }), materials)
  u0 = Math.min(along(bed0, bed1, [L.BED_E, L.CHAN_DOOR[0]]), along(bed0, bed1, [L.BED_E, L.CHAN_DOOR[1]]))
  addDoor(world, J.makeDoor(bed0, bed1, u0, L.CHAN_DOOR[1] - L.CHAN_DOOR[0], L.DOOR_TOP, { wallThickness: L.BW_TH, swing: -open, hingeLeft: false }), materials)

  for (const [a, b] of L.CH_WIN) {
    const windowU = Math.min(along(chandler0, chandler1, [a, L.CH_Y[1]]), along(chandler0, chandler1, [b, L.CH_Y[1]]))
    addWindow(world, J.makeWindow(chandler0, chandler1, windowU, b - a, L.WIN_SILL, L.WIN_HEAD, { wallThickness: L.TW, columns: 2, blindDrop: 0.55, blindTilt: 72 }), materials)
  }
  const [a, b] = L.JO_WIN
  const windowU = Math.min(along(west0, west1, [L.BED_W, a]), along(west0, west1, [L.BED_W, b]))
  addWindow(world, J.makeWindow(west0, west1, windowU, b - a, L.WIN_SILL, L.WIN_HEAD, { wallThickness: L.TW, columns: 2, blindDrop: 0.4, blindTilt: 76 }), materials)

  u0 = Math.min(along(east0, east1, [L.EX, L.FD_Y[0]]), along(east0, east1, [L.EX, L.FD_Y[1]]))
  frontDoor(world, east0, east1, u0, L.FD_Y[1] - L.FD_Y[0], L.FD_H, L.TW, materials)
}
