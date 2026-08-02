/** Apartment 19 kitchen, ported from build_scripts/Joeys_apt/f_kitchen.py. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'
import * as P from './props'
import * as T from './tiles'

const YB = L.NY2
const YF = L.NY2 - L.CTR_D
const YA = L.NY2 - 0.7
const YU = L.NY2 - L.UPPER_D

const add = (world: World, md: MeshData, material: THREE.Material, collide = false): MeshData => world.add(md, material, { collide })
const rounded = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, radius = 0.012): MeshData =>
  mlib.bevel(mlib.box(x0, y0, z0, x1, y1, z1), radius, 3)

function buildMaterials(): void {
  M.paint('M_CabCream', L.CAB_CREAM, { rough: 0.3, coat: 0.2, brush: 0.7 })
  M.paint('M_IslePutty', L.ISL_PUTTY, { rough: 0.34, coat: 0.12, brush: 0.6 })
  M.stone('M_Counter', 'F3F0E8', { vein: 'CEC6B5', rough: 0.12, scale: 1.4 })
  M.enamel('M_Appliance', 'F6F3EA', { rough: 0.1, tint: 'E9E4D6' })
  M.paint('M_Porcelain', 'EFEDE4', { rough: 0.17, coat: 0.32, brush: 0.2 })
  M.metal('M_Chrome', 'DCE0E4', { rough: 0.055, grime: 0.3, bump: 0.03 })
  M.metal('M_SteelBrush', 'BEC2C6', { rough: 0.26, brush: 0.85, grime: 0.35 })
  M.metal('M_SinkSteel', 'C4C8CC', { rough: 0.17, brush: 0.22, grime: 0.16 })
  M.metal('M_CastIron', '2A2A2E', { rough: 0.6, grime: 0.55, bump: 0.16 })
  M.metal('M_BrassK', 'B08D3F', { rough: 0.24, grime: 0.35 })
  M.plastic('M_BlackPl', '17171A', { rough: 0.34, coat: 0.3 })
  M.plastic('M_DarkGlass', '101014', { rough: 0.1, coat: 0.55 })
  M.ceramic('M_SplashTile', 'EFEDE3', { rough: 0.075, pitch: T.PITCH })
  M.velvet('M_StoolVel', '11453C', { rough: 0.52, sheen: 0.95 })
  M.wood('M_BlockWood', ['46301E', '644428', '2E1E0E'], { ring: 11, axis: 'Z', warp: 0.35, rough: [0.26, 0.46], coat: 0.3, grainRelief: 0.05 })
  M.wood('M_StoolWood', ['5E2A1C', '8E4028', '451B11'], { ring: 34, axis: 'Z', rough: [0.2, 0.42], coat: 0.42, grainRelief: 0.09, scale: 2.2 })
  M.stripe('M_SinkSkirt', ['EDE6D4', 'B4463C', 'EDE6D4', '2E6B62', 'D9A93E', 'B4463C'], { scale: 19.23, rough: 0.82 })
  const packs: [string, string][] = [['Red', 'B8342C'], ['Blue', '2A4E90'], ['Yellow', 'E0A81E'], ['Green', '2F7A46'], ['Orange', 'D8641E'], ['Purple', '5A3480'], ['Cream', 'DCD3BC']]
  for (const [name, color] of packs) M.paper(`M_Pack${name}`, color, { rough: 0.42, gloss: 0.3 })
  M.plastic('M_DartRed', 'A8241F', { rough: 0.36 })
  M.plastic('M_DartGreen', '15613A', { rough: 0.36 })
  M.plastic('M_DartBlack', '18181A', { rough: 0.44 })
  M.plastic('M_DartCream', 'DFD3AE', { rough: 0.4 })
}

function buildSink(world: World, x0: number, y0: number, x1: number, y1: number, top: number): void {
  const width = x1 - x0
  const depth = y1 - y0
  const cx = (x0 + x1) * 0.5
  const cy = (y0 + y1) * 0.5
  const levels: [number, number, number, number][] = [
    [width + 0.034, depth + 0.034, 0.028, top + 0.008], [width + 0.036, depth + 0.036, 0.028, top - 0.002],
    [width + 0.014, depth + 0.014, 0.026, top - 0.011], [width - 0.008, depth - 0.008, 0.03, top - 0.02],
    [width - 0.024, depth - 0.024, 0.038, top - 0.06], [width - 0.048, depth - 0.048, 0.052, top - 0.118],
    [width - 0.078, depth - 0.078, 0.07, top - 0.166], [width - 0.116, depth - 0.116, 0.086, top - 0.192],
    [width - 0.15, depth - 0.15, 0.09, top - 0.198],
  ]
  const rings = levels.map(([w, d, r, z]) => mlib.roundedRect(w, d, r, 5).map(([x, y]) => [cx + x, cy + y, z] as Vec3))
  const bowl = mlib.loft(rings, { closeV: true, capEnd: true })
  mlib.smoothShade(bowl, 40)
  add(world, bowl, M.get('M_SinkSteel'))

  const wx = cx
  const wy = cy + depth * 0.2
  add(world, mlib.translate(P.lathe([[0, 0], [0.046, 0], [0.048, 0.005], [0.042, 0.01], [0.038, 0.011], [0.038, 0.026], [0.03, 0.03], [0, 0.03]], 22), [wx, wy, top - 0.199]), M.get('M_Chrome'))
  for (let i = 0; i < 8; i++) {
    const slot = mlib.box(-0.0045, 0.02, 0, 0.0045, 0.036, 0.006)
    mlib.rotateZ(slot, Math.PI * 2 * i / 8)
    add(world, mlib.translate(slot, [wx, wy, top - 0.196]), M.get('M_BlackPl'))
  }
  add(world, mlib.translate(P.lathe([[0, 0], [0.019, 0], [0.019, 0.006], [0.006, 0.009], [0.006, 0.024], [0.012, 0.028], [0, 0.03]], 18), [wx, wy, top - 0.19]), M.get('M_Chrome'))

  const bx = cx
  const by = y1 + 0.075
  const base = P.lathe([[0, 0], [0.04, 0], [0.04, 0.012], [0.03, 0.02], [0.026, 0.055], [0.024, 0.07], [0, 0.072]], 20)
  add(world, mlib.translate(base, [bx, by, top]), M.get('M_Chrome'))
  add(world, mlib.tubeAlong([[bx, by, top + 0.055], [bx, by, top + 0.175], [bx, by - 0.03, top + 0.238], [bx, by - 0.105, top + 0.252], [bx, by - 0.168, top + 0.226], [bx, by - 0.176, top + 0.192]], mlib.circle(0.0135, 14)), M.get('M_Chrome'))
  for (const side of [-1, 1]) {
    const hb = P.lathe([[0, 0], [0.022, 0], [0.02, 0.024], [0.009, 0.03], [0.009, 0.052], [0.014, 0.058], [0, 0.06]], 14)
    add(world, mlib.translate(hb, [bx + side * 0.082, by, top]), M.get('M_Chrome'))
    const cross = mlib.bevel(mlib.join([mlib.box(-0.03, -0.0055, 0, 0.03, 0.0055, 0.009), mlib.box(-0.0055, -0.03, 0, 0.0055, 0.03, 0.009)]), 0.002, 2)
    add(world, mlib.translate(cross, [bx + side * 0.082, by, top + 0.058]), M.get('M_Chrome'))
  }
}

function peninsulaDressing(world: World, top: number): void {
  const cx = (L.PEN_X[0] + L.PEN_X[1]) * 0.5
  add(world, rounded(cx - 0.225, YB - 0.375, top, cx + 0.225, YB - 0.045, top + 0.268, 0.014), M.get('M_Appliance'))
  add(world, rounded(cx - 0.194, YB - 0.399, top + 0.042, cx + 0.062, YB - 0.387, top + 0.226, 0.003), M.get('M_DarkGlass'))
  add(world, rounded(cx + 0.112, YB - 0.385, top + 0.02, cx + 0.22, YB - 0.375, top + 0.248, 0.003), M.get('M_BlackPl'))
  const cy = YB - 0.56
  add(world, rounded(cx - 0.098, cy - 0.115, top, cx + 0.098, cy + 0.115, top + 0.335, 0.022), M.get('M_Appliance'))
  add(world, rounded(cx - 0.086, cy - 0.126, top + 0.012, cx + 0.086, cy - 0.02, top + 0.19, 0.004), M.get('M_BlackPl'))
  add(world, mlib.translate(P.lathe([[0, 0], [0.058, 0], [0.062, 0.014], [0.062, 0.12], [0.054, 0.14], [0.056, 0.15], [0.05, 0.152], [0.05, 0.014], [0, 0.012]], 22), [cx, cy - 0.07, top + 0.02]), M.get('M_DarkGlass'))
  add(world, rounded(cx - 0.11, YB - 1.72, top, cx + 0.11, YB - 1.65, top + 0.032, 0.014), M.get('M_BlackPl'))
  add(world, P.mug(cx + 0.2, YB - 1.42, top, 0.042, 0.098, true, 1.1), M.get('M_Porcelain'))
}

function buildCounter(world: World): void {
  const [px0, px1] = L.PEN_X
  const [py0, py1] = L.PEN_Y
  const [sx0, sx1] = L.K_SINK
  const top = L.CTR_H
  const deck = top - 0.038
  const band0 = deck - 0.026
  add(world, P.plinth(px0 + 0.045, py0 + 0.045, px1 - 0.045, py1 - 0.03, 0, 0.098), M.get('M_IslePutty'), true)
  // The plinth stops below the player's 250 mm collision threshold. The
  // cabinet body owns the peninsula's real blocking footprint and height.
  add(world, rounded(px0, py0, 0.092, px1, py1, band0, 0.003), M.get('M_IslePutty'), true)

  const profile: [number, number][] = [[0, -0.002], [0.03, -0.002], [0.03, 0.006], [0.021, 0.013], [0.008, 0.014], [0, 0.01]]
  const cz = (0.092 + band0) * 0.5
  const ph = band0 - 0.092 - 0.15
  const panels: ['E' | 'N' | 'W', number, number, number][] = [
    ['E', px0, py0 + (py1 - py0) * 0.28, (py1 - py0) * 0.5], ['E', px0, py0 + (py1 - py0) * 0.76, (py1 - py0) * 0.38],
    ['N', py0, (px0 + px1) * 0.5, px1 - px0], ['W', px1, py0 + (YF - py0) * 0.5, YF - py0],
  ]
  for (const [wall, at, u, span] of panels) {
    const md = mlib.bevel(mlib.sweepRectFrame(span - 0.19, ph, profile), 0.0018, 2)
    P.wallPlace([md], wall, u, cz, at)
    add(world, md, M.get('M_IslePutty'))
  }
  add(world, P.worktop(px0 - 0.03, py0 - 0.03, px1 + 0.03, YB, top, { thickness: 0.038, radius: 0.016, radii: [0.016, 0.016, 0, 0] }), M.get('M_Counter'))

  const yBack = YB - 0.03
  add(world, P.carcass(sx0, YF, sx1, yBack, L.TOE_H, deck - 0.004, { backAt: 'y1', side: 0.018, top: 0.018, lid: false }), M.get('M_CabCream'), true)
  add(world, P.plinth(sx0 + 0.012, YF + L.TOE_IN, sx1 - 0.012, yBack, 0, L.TOE_H), M.get('M_BlackPl'))
  const face = mlib.join([
    mlib.box(sx0, YF - 0.016, L.TOE_H, sx0 + 0.052, YF + 0.004, deck),
    mlib.box(sx1 - 0.052, YF - 0.016, L.TOE_H, sx1, YF + 0.004, deck),
    mlib.box(sx0, YF - 0.016, deck - 0.062, sx1, YF + 0.004, deck - 0.002),
  ])
  add(world, mlib.bevel(face, 0.003, 2), M.get('M_CabCream'))
  add(world, P.skirt(sx0 + 0.056, sx1 - 0.056, YF - 0.02, 0.055, deck - 0.066, 8, 0.024), M.get('M_SinkSkirt'))

  const hx0 = sx0 + 0.07
  const hx1 = sx0 + 0.53
  const hy0 = YF + 0.09
  const hy1 = YF + 0.47
  // Four slabs preserve the real through-cut sink aperture while keeping the joined counter continuous.
  const tx0 = px1 + 0.03
  const tx1 = sx1
  add(world, mlib.join([
    mlib.box(tx0, YF - 0.022, top - 0.038, tx1, hy0, top),
    mlib.box(tx0, hy1, top - 0.038, tx1, YB, top),
    mlib.box(tx0, hy0, top - 0.038, hx0, hy1, top),
    mlib.box(hx1, hy0, top - 0.038, tx1, hy1, top),
  ]), M.get('M_Counter'))
  buildSink(world, hx0, hy0, hx1, hy1, top)
  peninsulaDressing(world, top)
}

function burnerGrate(cx: number, cy: number, z: number): MeshData {
  const parts = [P.torus(0.098, 0.0085, 22, 8, [cx, cy, z])]
  for (let i = 0; i < 4; i++) {
    const a = Math.PI * 0.25 + Math.PI * 0.5 * i
    parts.push(P.rod([cx + 0.014 * Math.cos(a), cy + 0.014 * Math.sin(a), z - 0.004], [cx + 0.104 * Math.cos(a), cy + 0.104 * Math.sin(a), z], 0.0072, 8))
  }
  return mlib.join(parts)
}

function buildRange(world: World): void {
  const [x0, x1] = L.K_STOVE
  const yBack = YB - 0.02
  const yFront = YA
  const deck = 0.905
  for (const [dx, dy] of [[0.055, 0.055], [x1 - x0 - 0.055, 0.055], [0.055, yBack - yFront - 0.055], [x1 - x0 - 0.055, yBack - yFront - 0.055]]) {
    add(world, mlib.translate(P.lathe([[0, 0], [0.03, 0], [0.028, 0.012], [0.018, 0.028], [0.017, 0.1], [0.024, 0.104], [0, 0.104]], 14), [x0 + dx, yFront + dy, 0]), M.get('M_Chrome'))
  }
  add(world, rounded(x0, yFront, 0.098, x1, yBack, deck, 0.026), M.get('M_Appliance'), true)
  for (const [z0, z1, glass] of [[0.412, 0.836, 1], [0.126, 0.382, 0]] as const) {
    const door = rounded(x0 + 0.035, yFront - 0.03, z0, x1 - 0.035, yFront + 0.01, z1, 0.01)
    add(world, door, M.get('M_Appliance'))
    add(world, rounded(x0 + 0.076, yFront - 0.041, z0 + 0.041, x1 - 0.076, yFront - 0.028, z1 - 0.041, 0.008), M.get('M_Chrome'))
    if (glass) add(world, rounded((x0 + x1) * 0.5 - 0.318, yFront - 0.044, (z0 + z1) * 0.5 - 0.118, (x0 + x1) * 0.5 + 0.318, yFront - 0.038, (z0 + z1) * 0.5 + 0.118, 0.002), M.get('M_DarkGlass'))
  }
  for (const [z, length] of [[0.874, x1 - x0 - 0.15], [0.41, x1 - x0 - 0.15]]) {
    add(world, P.rod([(x0 + x1 - length) * 0.5, yFront - 0.082, z], [(x0 + x1 + length) * 0.5, yFront - 0.082, z], 0.0085, 14), M.get('M_Chrome'))
  }
  add(world, P.worktop(x0 - 0.004, yFront - 0.01, x1 + 0.004, yBack, deck + 0.022, { thickness: 0.022, radius: 0.02, radii: [0.02, 0.02, 0.006, 0.006] }), M.get('M_Appliance'))
  for (const [bx, by] of [[x0 + 0.185, yFront + 0.185], [x0 + 0.185, yFront + 0.475], [x0 + 0.46, yFront + 0.185], [x0 + 0.46, yFront + 0.475]]) {
    add(world, mlib.translate(P.lathe([[0, 0], [0.098, 0], [0.104, 0.01], [0.1, 0.014], [0.055, 0.006], [0.03, 0.004], [0, 0.004]], 22), [bx, by, deck + 0.022]), M.get('M_Chrome'))
    add(world, mlib.translate(P.lathe([[0, 0], [0.044, 0.002], [0.046, 0.016], [0.04, 0.024], [0.026, 0.026], [0, 0.022]], 20), [bx, by, deck + 0.03]), M.get('M_CastIron'))
    add(world, burnerGrate(bx, by, deck + 0.05), M.get('M_CastIron'))
  }
  add(world, rounded(x0 + 0.77, yFront + 0.165, deck + 0.022, x0 + 1, yFront + 0.495, deck + 0.04, 0.014), M.get('M_CastIron'))
  add(world, rounded(x0, yBack - 0.094, deck + 0.022, x1, yBack, 1.208, 0.005), M.get('M_Appliance'))
  add(world, rounded(x0 + 0.04, yBack - 0.108, 1.012, x1 - 0.04, yBack - 0.092, 1.128, 0.003), M.get('M_Chrome'))
  for (let i = 0; i < 6; i++) {
    const knob = P.knob(0.026, 0.02)
    P.faceY(knob, -1, [x0 + 0.098 + i * (x1 - x0 - 0.196) / 5, yBack - 0.108, 1.07])
    add(world, knob, M.get(i % 2 ? 'M_BlackPl' : 'M_Chrome'))
  }
  const dial = P.lathe([[0, 0], [0.038, 0], [0.038, 0.004], [0, 0.004]], 24)
  P.faceY(dial, -1, [(x0 + x1) * 0.5, yBack - 0.124, 1.166])
  add(world, dial, M.get('M_BlackPl'))
}

function buildFridge(world: World): void {
  const [x0, x1] = L.K_FRIDGE
  const height = L.K_FRIDGE_H
  const yBack = YB - 0.02
  const yFront = YA
  add(world, rounded(x0 + 0.03, yFront + 0.06, 0, x1 - 0.03, yBack, 0.088, 0.003), M.get('M_BlackPl'))
  add(world, rounded(x0, yFront + 0.052, 0.086, x1, yBack, height, 0.042), M.get('M_Appliance'), true)
  for (const [z0, z1] of [[1.212, height - 0.03], [0.108, 1.188]]) {
    add(world, rounded(x0 + 0.007, yFront, z0, x1 - 0.007, yFront + 0.055, z1, 0.04), M.get('M_Appliance'))
    const handle = P.handleBar((z1 - z0) * 0.56, 0.01, 0.046, 0.03)
    mlib.rotY(handle, Math.PI * 0.5)
    add(world, mlib.translate(handle, [x0 + 0.082, yFront, (z0 + z1) * 0.5]), M.get('M_Chrome'))
  }
  add(world, rounded((x0 + x1) * 0.5 - 0.085, yFront - 0.006, 1.055, (x0 + x1) * 0.5 + 0.085, yFront + 0.004, 1.086, 0.002), M.get('M_Chrome'))
  const jarX = x1 - 0.24
  const jarY = yBack - 0.3
  add(world, mlib.translate(P.lathe([[0, 0], [0.06, 0], [0.078, 0.03], [0.084, 0.078], [0.074, 0.118], [0.056, 0.14], [0.056, 0.15], [0, 0.152]], 24), [jarX, jarY, height]), M.get('M_Porcelain'))
  add(world, mlib.translate(P.lathe([[0, 0.088], [0.062, 0.006], [0.064, 0], [0, 0]], 22), [jarX, jarY, height + 0.15]), M.get('M_PackRed'))
}

function buildWallUnits(world: World): void {
  const [x0, x1] = L.K_UPPER
  const [z0, z1] = L.UPPER_Z
  add(world, P.carcass(x0, YU, x1, YB, z0, z1, { backAt: 'y1', side: 0.017, top: 0.017 }), M.get('M_CabCream'))
  const gap = 0.004
  const width = (x1 - x0 - gap * 2) / 3
  for (let i = 0; i < 3; i++) {
    const dx = x0 + i * (width + gap)
    add(world, mlib.translate(P.cabinetDoor(width, z1 - z0 - 0.006, 0.02, 0.058, 0.015, 0.008), [dx, YU - 0.02, z0 + 0.003]), M.get('M_CabCream'))
    const knob = P.knob(0.016)
    P.faceY(knob, -1, [dx + (i < 2 ? width - 0.052 : 0.052), YU - 0.02, z0 + 0.105])
    add(world, knob, M.get('M_BrassK'))
  }
  add(world, rounded(x0, YU - 0.024, z0 - 0.03, x1 + 0.01, YU + 0.002, z0 + 0.002, 0.003), M.get('M_CabCream'))
  const rng = new PyRandom(5)
  for (let i = 0; i < 5; i++) {
    const hx = x0 + 0.6 + i * 0.17
    const hy = YU - 0.062
    add(world, mlib.tubeAlong([[hx, hy, z0 - 0.004], [hx, hy, z0 - 0.028], [hx, hy + 0.016, z0 - 0.042], [hx, hy + 0.034, z0 - 0.036], [hx, hy + 0.038, z0 - 0.022]], mlib.circle(0.0024, 6)), M.get('M_Chrome'))
    add(world, P.mug(hx, hy - 0.038, z0 - 0.117, 0.041, 0.094, true, Math.PI * 0.5 + rng.uniform(-0.1, 0.1)), M.get('M_Porcelain'))
  }

  const [mx0, mx1] = L.K_MW
  const [mz0, mz1] = L.K_MW_Z
  add(world, rounded(mx0, YB - 0.36, mz0, mx1, YB, mz1, 0.016), M.get('M_Appliance'))
  add(world, rounded(mx0 + 0.038, YB - 0.382, mz0 + 0.048, mx1 - 0.18, YB - 0.372, mz1 - 0.048, 0.003), M.get('M_DarkGlass'))
  add(world, rounded(mx1 - 0.144, YB - 0.372, mz0 + 0.022, mx1 - 0.014, YB - 0.362, mz1 - 0.022, 0.003), M.get('M_BlackPl'))
  add(world, rounded(mx1 - 0.176, YB - 0.408, mz0 + 0.04, mx1 - 0.156, YB - 0.372, mz1 - 0.04, 0.004), M.get('M_Chrome'))
  add(world, P.carcass(mx0, YU, mx1, YB, mz1, z1, { backAt: 'y1', side: 0.017, top: 0.017 }), M.get('M_CabCream'))
  add(world, mlib.translate(P.cabinetDoor(mx1 - mx0, z1 - mz1 - 0.006, 0.02, 0.055, 0.015, 0.008), [mx0, YU - 0.02, mz1 + 0.003]), M.get('M_CabCream'))

  const [sx0, sx1] = L.K_SHELF
  const [sz0, sz1] = L.K_SHELF_Z
  const mid = (sz0 + sz1) * 0.5
  add(world, P.carcass(sx0, YB - 0.3, sx1, YB, sz0, sz1, { backAt: 'y1', side: 0.018, top: 0.018, shelves: [mid] }), M.get('M_CabCream'))
  const packMats = ['M_PackRed', 'M_PackBlue', 'M_PackYellow', 'M_PackGreen', 'M_PackOrange', 'M_PackPurple', 'M_PackCream']
  const shelfRng = new PyRandom(19)
  for (const zz of [sz0 + 0.018, mid + 0.009]) {
    for (const y of [YB - 0.075, YB - 0.205]) {
      let x = sx0 + 0.034
      while (x < sx1 - 0.07) {
        const kind = shelfRng.random()
        const width = kind < 0.62 ? shelfRng.uniform(0.058, 0.094) : kind < 0.84 ? 0.066 : 0.098
        const prop = kind < 0.62
          ? P.boxProp(x + width * 0.5, y, zz, width, shelfRng.uniform(0.048, 0.068), shelfRng.uniform(0.185, 0.275), shelfRng.uniform(-0.22, 0.22))
          : kind < 0.84 ? P.can(x + width * 0.5, y, zz, 0.032, shelfRng.uniform(0.098, 0.132))
            : P.jar(x + width * 0.5, y, zz, 0.047, shelfRng.uniform(0.115, 0.165))
        add(world, prop, M.get(shelfRng.choice(packMats)))
        x += width + shelfRng.uniform(0.004, 0.018)
      }
    }
  }
}

function buildSplashback(world: World): void {
  const count = T.courses(L.SPLASH_Z[1] - L.SPLASH_Z[0])
  const u = (x: number): number => L.EX - x
  const field = T.field([L.EX, L.NY2], [L.JX, L.NY2], u(L.SPLASH_X[1]), u(L.SPLASH_X[0]), L.SPLASH_Z[0], count, { startU: u(L.SPLASH_X[0]) })
  add(world, mlib.join(field), M.get('M_SplashTile'))
  add(world, T.stopBead([L.EX, L.NY2], [L.JX, L.NY2], u(L.SPLASH_X[0]) - 0.021, L.SPLASH_Z[0], L.SPLASH_Z[0] + T.height(count) + 0.021), M.get('M_SplashTile'))
}

function buildDressing(world: World): void {
  const cx = (L.PEN_X[0] + L.PEN_X[1]) * 0.5
  add(world, rounded(cx - 0.13, L.PEN_Y[0] + 0.22, L.CTR_H, cx + 0.13, L.PEN_Y[0] + 0.42, L.CTR_H + 0.185, 0.03), M.get('M_SteelBrush'))
  for (const side of [-1, 1]) add(world, mlib.box(cx - 0.096, L.PEN_Y[0] + 0.32 + side * 0.03 - 0.013, L.CTR_H + 0.18, cx + 0.096, L.PEN_Y[0] + 0.32 + side * 0.03 + 0.013, L.CTR_H + 0.192), M.get('M_BlackPl'))
  const blockX = cx + 0.075
  const blockY = L.PEN_Y[0] + 0.96
  add(world, mlib.bevel(mlib.prismYZ([[blockY - 0.078, L.CTR_H], [blockY + 0.078, L.CTR_H], [blockY + 0.078, L.CTR_H + 0.245], [blockY - 0.078, L.CTR_H + 0.15]], blockX - 0.062, blockX + 0.062), 0.005, 3), M.get('M_BlockWood'))
  for (let i = 0; i < 4; i++) {
    const t = 0.3 + i * 0.13
    const y = blockY - 0.078 + 0.156 * t
    const z = L.CTR_H + 0.15 + 0.095 * t
    add(world, P.rod([blockX - 0.04 + i * 0.027, y, z], [blockX - 0.04 + i * 0.027, y + 0.03, z + 0.088], 0.0085, 8), M.get('M_BlackPl'))
  }
  const paperX = L.K_SINK[0] + 0.075
  const paperY = YB - 0.1
  add(world, P.rod([paperX, paperY, L.CTR_H], [paperX, paperY, L.CTR_H + 0.32], 0.01, 10), M.get('M_Chrome'))
  add(world, mlib.translate(P.lathe([[0, 0], [0.072, 0], [0.07, 0.008], [0.02, 0.014], [0, 0.014]], 20), [paperX, paperY, L.CTR_H]), M.get('M_Chrome'))
  add(world, mlib.translate(P.lathe([[0.02, 0], [0.058, 0], [0.06, 0.012], [0.06, 0.23], [0.058, 0.242], [0.02, 0.242]], 24), [paperX, paperY, L.CTR_H + 0.03]), M.get('M_PackCream'))
  for (let i = 0; i < 2; i++) add(world, P.jar(L.K_SINK[1] - 0.2 + i * 0.12, YB - 0.108, L.CTR_H, 0.054, 0.17 + i * 0.035), M.get('M_Porcelain'))
  add(world, mlib.translate(P.lathe([[0, 0], [0.086, 0.004], [0.098, 0.028], [0.096, 0.088], [0.07, 0.122], [0.044, 0.132], [0.042, 0.146], [0.03, 0.15], [0, 0.15]], 24), [L.K_STOVE[0] + 0.46, YA + 0.475, 0.982]), M.get('M_SteelBrush'))
  const dx = L.K_SINK[1] - 0.135
  const dy = YF + 0.285
  add(world, rounded(dx - 0.114, dy - 0.15, L.CTR_H, dx + 0.114, dy + 0.15, L.CTR_H + 0.02, 0.004), M.get('M_BlackPl'))
  for (let i = 0; i < 7; i++) add(world, mlib.tubeAlong([[dx - 0.096, dy - 0.12 + i * 0.04, L.CTR_H + 0.02], [dx - 0.068, dy - 0.12 + i * 0.04, L.CTR_H + 0.1], [dx + 0.068, dy - 0.12 + i * 0.04, L.CTR_H + 0.1], [dx + 0.096, dy - 0.12 + i * 0.04, L.CTR_H + 0.02]], mlib.circle(0.0025, 6)), M.get('M_Chrome'))
  add(world, mlib.translate(P.lathe([[0, 0], [0.145, 0], [0.15, 0.014], [0.162, 0.5], [0.168, 0.52], [0.162, 0.536], [0.12, 0.548], [0, 0.552]], 26), [L.EX - L.BASE_T - 0.168, 1.05, 0]), M.get('M_SteelBrush'), true)
  add(world, P.bowl(cx, L.PEN_Y[0] + 0.64, L.CTR_H, 0.13, 0.076), M.get('M_Porcelain'))
  const fruitMats = ['M_PackRed', 'M_PackOrange', 'M_PackGreen', 'M_PackYellow', 'M_PackRed']
  for (let i = 0; i < 5; i++) {
    const a = Math.PI * 2 * i / 5
    const fruit = P.lathe([[0, 0], [0.028, 0.01], [0.034, 0.032], [0.026, 0.052], [0, 0.058]], 14)
    add(world, mlib.translate(fruit, [cx + 0.05 * Math.cos(a), L.PEN_Y[0] + 0.64 + 0.05 * Math.sin(a), L.CTR_H + 0.03]), M.get(fruitMats[i]))
  }
}

function buildStool(world: World, cx: number, cy: number): void {
  const seatZ = L.STOOL_H - 0.135
  for (let i = 0; i < 4; i++) {
    const angle = Math.PI * 0.25 + Math.PI * 0.5 * i
    const p0: Vec3 = [cx + 0.205 * Math.cos(angle), cy + 0.205 * Math.sin(angle), 0]
    const p1: Vec3 = [cx + 0.118 * Math.cos(angle), cy + 0.118 * Math.sin(angle), seatZ + 0.01]
    const spine: Vec3[] = [p0, [p0[0] * 0.72 + p1[0] * 0.28, p0[1] * 0.72 + p1[1] * 0.28, p0[2] * 0.72 + p1[2] * 0.28], [p0[0] * 0.34 + p1[0] * 0.66, p0[1] * 0.34 + p1[1] * 0.66, p0[2] * 0.34 + p1[2] * 0.66], p1]
    add(world, P.sweepVar(spine, [[0.0175, 0.0175], [0.0215, 0.0215], [0.018, 0.018], [0.0205, 0.0205]], 12), M.get('M_StoolWood'))
  }
  add(world, P.torus(0.176, 0.0085, 28, 8, [cx, cy, 0.215]), M.get('M_Chrome'))
  add(world, mlib.translate(P.lathe([[0, 0], [0.15, 0], [0.154, 0.01], [0.15, 0.018], [0, 0.018]], 26), [cx, cy, seatZ - 0.018]), M.get('M_StoolWood'))
  add(world, mlib.translate(P.lathe([[0, 0], [0.17, 0], [0.186, 0.02], [0.192, 0.048], [0.19, 0.092], [0.176, 0.12], [0.14, 0.134], [0.078, 0.14], [0, 0.141]], 30), [cx, cy, seatZ]), M.get('M_StoolVel'), true)
  add(world, P.torus(0.1885, 0.0075, 30, 8, [cx, cy, seatZ + 0.024]), M.get('M_StoolVel'))
}

function houndRing(x: number, zc: number, width: number, up: number, down: number, count = 28): Vec3[] {
  return Array.from({ length: count }, (_, i) => {
    const angle = Math.PI * 2 * i / count
    const c = Math.cos(angle)
    const s = Math.sin(angle)
    const power = 1 / 1.25
    const cc = Math.sign(c) * Math.abs(c) ** power
    const ss = Math.sign(s) * Math.abs(s) ** power
    return [x, width * cc, zc + (s >= 0 ? up : down) * ss] as Vec3
  })
}

function buildDog(world: World): void {
  const stations: [number, number, number, number, number][] = [
    [-0.622,0.792,0.012,0.011,0.013],[-0.598,0.793,0.024,0.021,0.026],[-0.556,0.798,0.034,0.028,0.038],[-0.508,0.808,0.038,0.032,0.044],[-0.47,0.824,0.043,0.04,0.048],[-0.44,0.843,0.05,0.045,0.052],[-0.406,0.861,0.056,0.048,0.055],[-0.372,0.864,0.055,0.046,0.058],[-0.342,0.856,0.052,0.044,0.066],[-0.302,0.834,0.053,0.046,0.082],[-0.256,0.802,0.059,0.052,0.1],[-0.208,0.76,0.067,0.058,0.116],[-0.16,0.714,0.075,0.062,0.128],[-0.114,0.676,0.085,0.065,0.136],[-0.062,0.654,0.09,0.069,0.148],[-0.006,0.642,0.09,0.07,0.156],[0.052,0.638,0.083,0.07,0.146],[0.108,0.634,0.072,0.068,0.124],[0.164,0.632,0.058,0.062,0.092],[0.212,0.634,0.053,0.06,0.076],[0.262,0.642,0.06,0.064,0.072],[0.312,0.65,0.07,0.068,0.074],[0.362,0.65,0.078,0.068,0.08],[0.412,0.64,0.079,0.064,0.084],[0.456,0.622,0.068,0.056,0.078],[0.494,0.598,0.05,0.042,0.056],[0.516,0.584,0.032,0.028,0.034],[0.53,0.578,0.014,0.013,0.015],
  ]
  const parts: MeshData[] = [mlib.loft(stations.map((s) => houndRing(...s)), { closeV: true, capStart: true, capEnd: true })]
  for (const side of [-1, 1]) {
    parts.push(P.sweepVar([[-0.098,side*0.046,0.678],[-0.094,side*0.058,0.566],[-0.088,side*0.064,0.478],[-0.084,side*0.066,0.382],[-0.084,side*0.066,0.272],[-0.086,side*0.066,0.162],[-0.086,side*0.066,0.076],[-0.074,side*0.066,0.026],[-0.058,side*0.066,0.011]], [[0.036,0.06],[0.031,0.053],[0.026,0.043],[0.021,0.031],[0.017,0.024],[0.016,0.021],[0.017,0.023],[0.021,0.026],[0.024,0.014]], 18))
    parts.push(P.sweepVar([[0.398,side*0.042,0.656],[0.376,side*0.058,0.578],[0.35,side*0.07,0.502],[0.322,side*0.076,0.428],[0.348,side*0.076,0.352],[0.404,side*0.074,0.284],[0.41,side*0.072,0.196],[0.404,side*0.072,0.098],[0.392,side*0.072,0.03],[0.372,side*0.072,0.011]], [[0.032,0.072],[0.045,0.086],[0.048,0.082],[0.038,0.064],[0.028,0.042],[0.021,0.03],[0.017,0.023],[0.017,0.023],[0.02,0.025],[0.024,0.014]], 18))
    parts.push(P.sweepVar([[-0.398,side*0.04,0.888],[-0.376,side*0.052,0.898],[-0.352,side*0.058,0.892],[-0.33,side*0.054,0.876],[-0.314,side*0.044,0.86],[-0.306,side*0.036,0.85]], [[0.009,0.014],[0.013,0.022],[0.014,0.024],[0.012,0.02],[0.008,0.013],[0.004,0.006]], 14))
  }
  parts.push(P.sweepVar([[0.462,0,0.616],[0.508,0.002,0.584],[0.552,0.008,0.528],[0.596,0.016,0.45],[0.612,0.024,0.364],[0.594,0.032,0.292],[0.556,0.038,0.248],[0.512,0.04,0.234],[0.482,0.04,0.242]], [[0.03,0.034],[0.027,0.03],[0.022,0.024],[0.017,0.018],[0.013,0.014],[0.01,0.011],[0.008,0.009],[0.006,0.007],[0.004,0.004]], 14))
  const dog = mlib.join(parts)
  mlib.smoothShade(dog, 76)
  mlib.scaleMesh(dog, L.DOG_SCALE)
  mlib.rotateZ(dog, L.DOG_ROT * Math.PI / 180)
  mlib.translate(dog, [L.DOG[0], L.DOG[1], 0.002])
  add(world, dog, M.get('M_Porcelain'))
}

function buildDartboard(world: World): void {
  const radius=0.2175
  const sectorCount=20
  const surfaceY=0.03
  const bands:[number,number,'body'|'ring'][]=[
    [0.0159,0.0955,'body'],[0.0955,0.1069,'ring'],
    [0.1069,0.162,'body'],[0.162,0.17,'ring'],
  ]
  const vertices:Vec3[]=[]
  const faces:number[][]=[]
  const slots:number[]=[]
  const angle=(index:number):number=>Math.PI*0.5+Math.PI/sectorCount+index*Math.PI*2/sectorCount
  for(let sectorIndex=0;sectorIndex<sectorCount;sectorIndex++){
    const a0=angle(sectorIndex),a1=angle(sectorIndex+1),dark=sectorIndex%2===0
    for(const [r0,r1,kind] of bands){
      const start=vertices.length
      for(const [r,a] of [[r0,a0],[r1,a0],[r1,a1],[r0,a1]] as const)vertices.push([r*Math.cos(a),surfaceY,r*Math.sin(a)])
      faces.push([start+3,start+2,start+1,start])
      slots.push(kind==='ring'?(dark?0:1):(dark?2:3))
    }
  }
  for(const [r0,r1,slot] of [[0,0.0064,0],[0.0064,0.0159,1],[0.17,radius,2]] as const){
    const start=vertices.length
    for(let i=0;i<48;i++){
      const a=Math.PI*2*i/48
      vertices.push([r0*Math.cos(a),surfaceY,r0*Math.sin(a)],[r1*Math.cos(a),surfaceY,r1*Math.sin(a)])
    }
    for(let i=0;i<48;i++){
      const a=2*i,b=2*((i+1)%48)
      faces.push([start+b,start+b+1,start+a+1,start+a])
      slots.push(slot)
    }
  }
  const face=MeshData.from(vertices,faces)
  face.faceMat=slots

  // The face is the visible side of Blender's centred 32 mm solidify. A
  // separate backing supplies that thickness without putting a black cap on
  // the same plane as the colored slots.
  const backing=mlib.prismXZ(mlib.circle(radius,60),-0.002,surfaceY-0.0015)
  const wires:MeshData[]=[]
  for(let i=0;i<sectorCount;i++){
    const a=angle(i)
    wires.push(P.rod([0.0159*Math.cos(a),surfaceY+0.0025,0.0159*Math.sin(a)],[0.17*Math.cos(a),surfaceY+0.0025,0.17*Math.sin(a)],0.0011,6))
  }
  for(const r of [0.0159,0.0955,0.1069,0.162,0.17]){
    const ring=P.torus(r,0.0011,44,6)
    mlib.rotX(ring,Math.PI*0.5)
    mlib.translate(ring,[0,surfaceY+0.0025,0])
    wires.push(ring)
  }
  const spider=mlib.join(wires)
  const pieces:MeshData[]=[backing,face,spider]
  P.wallPlace(pieces,'W',L.DART_X,L.DART_Z,L.DART_AT)
  const pivot: [number, number] = [L.BED_E + (L.BW_TH - 0.042) * 0.5, L.JOEY_DOOR[0] + 0.005]
  for (const piece of pieces) mlib.rotateZ(piece, L.DOOR_OPEN * Math.PI / 180, pivot)
  add(world,backing,M.get('M_DartBlack'))
  world.addMulti(face,[M.get('M_DartRed'),M.get('M_DartGreen'),M.get('M_DartBlack'),M.get('M_DartCream')])
  add(world,spider,M.get('M_Chrome'))
}

export function build(world: World): void {
  buildMaterials()
  buildCounter(world)
  buildRange(world)
  buildFridge(world)
  buildWallUnits(world)
  buildSplashback(world)
  buildDressing(world)
  buildStool(world, ...L.STOOL_A)
  buildStool(world, ...L.STOOL_B)
  buildDog(world)
  buildDartboard(world)
}
