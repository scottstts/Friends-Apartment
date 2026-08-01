/** Architectural shell - port of build_scripts/build_shell.py:
 * floor, walls, ceilings, mouldings, the exposed kitchen timber.
 * Wall colliders are registered here alongside the geometry so every doorway
 * stays exactly as passable as the built wall is.
 */
import type * as THREE from 'three/webgpu'
import * as L from '../lib/L'
import type { Vec2 } from '../lib/mesh'
import * as mlib from '../lib/mlib'
import * as mats from '../mats/mats'
import * as W from './walls'
import { buildParquet } from './floor'
import type { World } from './world'

export type MatSet = Record<string, THREE.Material>

function pointInPoly(x: number, y: number, poly: Vec2[]): boolean {
  let inside = false
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i]
    const [xj, yj] = poly[j]
    const ex = xi - xj
    const ey = yi - yj
    const px = x - xj
    const py = y - yj
    if (Math.abs(ex * py - ey * px) < 1e-9 && px * ex + py * ey >= 0 && px * ex + py * ey <= ex * ex + ey * ey) return true
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside
  }
  return inside
}

function rect(x0: number, y0: number, x1: number, y1: number): Vec2[] {
  return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
}

/** Plan footprint of W.wall(): the inner face is p0->p1 and thickness grows
 * to the left of travel. This lets the parquet trim retain boards under walls
 * exactly as the Blender shell ray test does. */
function wallFootprint(p0: Vec2, p1: Vec2, thickness: number): Vec2[] {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const ln = Math.hypot(dx, dy)
  const nx = -dy / ln
  const ny = dx / ln
  return [p0, p1, [p1[0] + nx * thickness, p1[1] + ny * thickness], [p0[0] + nx * thickness, p0[1] + ny * thickness]]
}

export function buildMats(): MatSet {
  const M: MatSet = {}
  M.parquet = mats.wood('parquet_oak', ['C8AC80', 'AB8C61', '866A42'], {
    ring: 62.0,
    warp: 0.06,
    warpScale: 1.0,
    distort: 0.7,
    blotch: 0.12,
    coord: 'UV',
    axis: 'X',
    bump: 0.22,
    pore: 1.0,
    tintAttr: 'ptint',
    rough: [0.16, 0.34],
    aniso: 0.4,
  })
  M.lav = mats.plaster('wall_lavender', L.LAV, { rough: 0.68, bump: 0.26, scale: 30 })
  M.cream = mats.plaster('wall_cream', L.CREAM, { rough: 0.74, bump: 0.3, scale: 26 })
  M.ceil = mats.plaster('ceiling_cream', 'EFE6CB', { rough: 0.82, bump: 0.34, scale: 20 })
  M.brick = mats.brickWall('brick_kitchen')
  M.tile = mats.subwayTile('tile_kitchen', { size: 0.084, stack: true })
  M.bathtile = mats.subwayTile('tile_bath', { size: 0.075, hexcol: 'EFEFE8', grout: 'BFBCAE', stack: false })
  M.green = mats.paint('paint_green_dado', L.GREEN_DADO, { rough: 0.28, coat: 0.22 })
  M.trim = mats.paint('paint_lav_trim', L.LAV_TRIM, { rough: 0.26, coat: 0.25 })
  // Near-uniform on purpose: the beams read by colour and rough surface.
  const BEAMC: [string, string, string] = ['85613D', '805C3A', '7B5737']
  const BK = {
    ring: 11.0,
    warp: 0.018,
    warpScale: 1.1,
    distort: 0.15,
    blotch: 0.32,
    bump: 0.34,
    rough: [0.34, 0.58] as [number, number],
    aniso: 0.18,
    grainRelief: 0.06,
  }
  M.beam = mats.wood('wood_beam', BEAMC, { axis: 'YZ', ...BK })
  M.beam_y = mats.wood('wood_beam_y', BEAMC, { axis: 'XZ', ...BK })
  M.beam_v = mats.wood('wood_beam_v', BEAMC, { axis: 'XY', ...BK })
  M.beam_z = mats.wood('wood_beam_z', BEAMC, { axis: 'Z', ...BK })
  M.corr = mats.plaster('wall_corridor', 'C09258', { rough: 0.62, bump: 0.22 })
  M.corrwood = mats.wood('wood_corridor', ['9C6A38', '73441F', '43250F'], { ring: 16.0, warp: 0.6, bump: 0.25 })
  M.stone = mats.plaster('stone_sill', '8D897E', { rough: 0.62, bump: 0.5, scale: 48 })
  return M
}

export function build(w: World): MatSet {
  const M = buildMats()
  const CZ = L.CZ
  const RAIL = L.RAIL
  const TW = L.TW
  const TP = L.TP

  const mainPoly: Vec2[] = [
    [0, L.SY],
    [0, L.CH_A[1]],
    L.CH_B,
    [L.N_BRICK[1], L.NY],
    [L.HALL_WW[0], L.HALL_Y0],
    [L.HALL_X[0], L.HALL_Y0],
    [L.HALL_X[0], L.NW_Y],
    [L.HALL_X[1], L.NW_Y],
    [L.HALL_X[1], L.AL_S],
    [L.EX, L.AL_S],
    [L.EX, L.SY],
  ]
  const floorCover: Vec2[][] = [
    mainPoly,
    rect(L.BA_X[0], L.BA_Y[0], L.BA_X[1], L.BA_Y[1]),
    rect(L.AL_X[0], L.AL_S, L.AL_X[1], L.NYW),
    rect(L.BED_X[0], L.RB_Y[0], L.BED_X[1], L.RB_Y[1]),
    rect(L.BED_X[0], L.MB_Y[0], L.BED_X[1], L.MB_Y[1]),
    wallFootprint([0, L.SY], [0, L.CH_A[1]], TW),
    wallFootprint(L.CH_A, L.CH_B, TW),
    wallFootprint([L.N_BRICK[0], L.NY], [L.N_BRICK[1], L.NY], TP),
    wallFootprint([L.HALL_X[0], L.HALL_Y0], [L.HALL_X[0], L.NW_Y], L.HALL_X[0] - L.HALL_WW[0]),
    wallFootprint([L.HALL_X[0], L.NW_Y], [L.HALL_X[1], L.NW_Y], 0.3),
    wallFootprint([L.HALL_X[1], L.NW_Y], [L.HALL_X[1], L.NYW], L.HALL_EW[1] - L.HALL_EW[0]),
    wallFootprint([L.HALL_EW[1], L.NYW], [L.AL_X[1], L.NYW], TW),
    wallFootprint([L.EX, L.NYW], [L.EX, L.SY], L.EXW - L.EX),
    wallFootprint([L.EXT_E, L.SY], [0, L.SY], TW),
    wallFootprint([L.BA_X[0], L.BA_Y[1]], [L.BA_X[1], L.BA_Y[1]], TW),
    wallFootprint([L.BA_X[0], L.BA_Y[0]], [L.BA_X[0], L.BA_Y[1]], TW),
    wallFootprint([L.BED_X[0], L.BED_DIV[0]], [L.BED_X[1], L.BED_DIV[0]], L.BED_DIV[1] - L.BED_DIV[0]),
    wallFootprint([L.EXT_E, L.NYW], [L.EXT_E, L.SY], TW),
    wallFootprint([L.BED_X[0], L.NYW], [L.BED_X[1], L.NYW], TW),
  ]
  const floorCovered = (x: number, y: number): boolean => floorCover.some((poly) => pointInPoly(x, y, poly))

  // ---------------------------------------------------------------- floor
  // Keep every opaque architectural surface in the caster set. Even though
  // the parquet is the lowest visible surface, raised seams and thresholds
  // still contribute to local occlusion in the reference.
  const subMat = mats.paint('subfloor_dark', '2A1F16', { rough: 0.8 })
  const sub = mlib.box(-0.32, L.SY - 0.32, -0.02, 11.95, 7.15, 0.0035)
  w.add(sub, subMat)
  // 0.52 m module: the set's parquet reads big
  const par = buildParquet(-0.45, L.SY - 0.45, 12.3, L.NW_Y + 0.55, 0.52, 0.0014, 0.0095, Math.PI / 4, floorCovered)
  w.add(par, M.parquet)

  // ---------------------------------------------------------------- walls
  // -- west: lavender front-door wall (split at the picture rail)
  w.add(
    W.wall([0, L.SY], [0, L.W_PLASTER[1]], 0, RAIL, TW, [
      [L.FD_Y[0] - L.SY, 0, L.FD_Y[1] - L.SY, L.FD_TOP],
    ]),
    M.lav,
  )
  w.add(W.wall([0, L.SY], [0, L.W_PLASTER[1]], RAIL, CZ, TW), M.cream)
  // -- west: brick
  w.add(W.wall([0, L.W_BRICK[0]], [0, L.W_BRICK[1]], 0, CZ, TW), M.brick)
  // -- chamfer with the kitchen window
  w.add(
    W.wall(L.CH_A, L.CH_B, 0, CZ, TW, [[L.KW_U[0], L.KW_Z[0], L.KW_U[1], L.KW_Z[1]]]),
    M.brick,
  )
  // -- north brick (counter run + fridge nook); body forms the bathroom's south wall
  w.add(W.wall([L.N_BRICK[0], L.NY], [L.N_BRICK[1], L.NY], 0, CZ, TP), M.brick)
  // -- hallway west wall: split at the picture rail so the hallway face is
  //    lavender below and cream above; the kitchen face remains brick.
  {
    const xm = (L.HALL_WW[0] + L.HALL_X[0]) * 0.5
    const lo = W.wall(
      [L.HALL_X[0], L.HALL_Y0],
      [L.HALL_X[0], L.NW_Y],
      0,
      RAIL,
      L.HALL_X[0] - L.HALL_WW[0],
      [[L.BD_Y[0] - L.HALL_Y0, 0, L.BD_Y[1] - L.HALL_Y0, L.BD_H]],
    )
    W.faceMat(lo, 1, (c) => c[0] < xm - 0.01)
    w.addMulti(lo, [M.lav, M.brick])
    const hi = W.wall(
      [L.HALL_X[0], L.HALL_Y0],
      [L.HALL_X[0], L.NW_Y],
      RAIL,
      CZ,
      L.HALL_X[0] - L.HALL_WW[0],
    )
    W.faceMat(hi, 1, (c) => c[0] < xm - 0.01)
    w.addMulti(hi, [M.cream, M.brick])
  }
  // -- hallway north wall (exterior) with the green closet door + dado
  w.add(
    W.wall([L.HALL_X[0], L.NW_Y], [L.HALL_X[1], L.NW_Y], 0, 1.1, 0.3, [
      [L.CL_X[0] - L.HALL_X[0], 0, L.CL_X[1] - L.HALL_X[0], 1.1],
    ]),
    M.green,
  )
  w.add(
    W.wall([L.HALL_X[0], L.NW_Y], [L.HALL_X[1], L.NW_Y], 1.1, CZ, 0.3, [
      [L.CL_X[0] - L.HALL_X[0], 1.1, L.CL_X[1] - L.HALL_X[0], L.CL_H],
    ]),
    M.cream,
  )
  // closet cavity behind the green door
  w.add(
    mlib.box(L.HALL_X[0] + 0.02, L.NW_Y + 0.3, 0.0, L.HALL_X[1] - 0.02, L.NW_Y + 0.34, L.CL_H + 0.2),
    mats.paint('closet_dark', '3B342C', { rough: 0.8 }),
  )
  for (const zz of [0.55, 1.05, 1.55]) {
    w.add(
      mlib.box(L.HALL_X[0] + 0.03, L.NW_Y + 0.2, zz, L.HALL_X[1] - 0.03, L.NW_Y + 0.3, zz + 0.02),
      M.trim,
    )
  }
  // -- hallway east wall: only the north exterior-closing stretch remains.
  {
    const he = W.wall([L.HALL_X[1], L.NW_Y], [L.HALL_X[1], L.NYW], 0, CZ, L.HALL_EW[1] - L.HALL_EW[0])
    const xe = (L.HALL_EW[0] + L.HALL_EW[1]) * 0.5
    W.faceMat(he, 1, (c) => c[0] < xe - 0.01 && c[2] > 1.1)
    W.faceMat(he, 2, (c, n) => c[0] > xe + 0.01 || n[1] < -0.5)
    w.addMulti(he, [M.green, M.cream, M.lav])
  }
  // -- north exterior wall of the alcove: huge window, wall stops at BW_TOP
  const AWX = L.HALL_EW[1]
  w.add(
    W.wall([AWX, L.AL_Y[1]], [L.AL_X[1], L.AL_Y[1]], 0, L.BW_TOP, TW, [
      [L.BW_X[0] - AWX, L.BW_SILL, L.BW_X[1] - AWX, L.BW_TOP],
    ]),
    M.lav,
  )
  // -- header over the alcove opening
  const alcoveHeaderDepth = 0.22
  w.add(W.wall([L.AL_X[0], L.AL_S], [L.AL_X[1], L.AL_S], L.AL_Z, CZ, alcoveHeaderDepth), M.cream)
  // -- west downstand closing the lower alcove ceiling against the main one
  w.add(W.wall([L.AL_X[0], L.AL_S], [L.AL_X[0], L.NYW], L.AL_Z, CZ, 0.1), M.cream)
  // -- central wall: Rachel's doorway at the south, Monica's door at the north
  const u = (y: number) => L.NYW - y
  {
    const lo = W.wall([L.EX, L.NYW], [L.EX, L.SY], 0, RAIL, L.EXW - L.EX, [
      [u(L.CD_Y[1]), 0, u(L.CD_Y[0]), L.CD_TOP],
      [u(L.MD_Y[1]), 0, u(L.MD_Y[0]), L.MD_TOP],
    ])
    w.addMulti(lo, [M.lav, M.cream])
    w.add(W.wall([L.EX, L.NYW], [L.EX, L.SY], RAIL, CZ, L.EXW - L.EX), M.cream)
  }
  // -- south (fourth) wall, running the full width including the bedrooms
  w.add(W.wall([L.EXT_E, L.SY], [0, L.SY], 0, RAIL, TW), M.lav)
  w.add(W.wall([L.EXT_E, L.SY], [0, L.SY], RAIL, CZ, TW), M.cream)

  // ---------------------------------------------------------- bathroom shell
  w.add(W.wall([L.BA_X[0], L.BA_Y[1]], [L.BA_X[1], L.BA_Y[1]], 0, L.AL_Z, TW), M.bathtile)
  w.add(W.wall([L.BA_X[0], L.BA_Y[0]], [L.BA_X[0], L.BA_Y[1]], 0, L.AL_Z, TW), M.bathtile)
  w.add(
    mlib.box(L.BA_X[0], L.BA_Y[0] + 0.002, 0.0, L.BA_X[1], L.BA_Y[0] + 0.014, L.AL_Z),
    M.bathtile,
  )
  // east liner carries the hall wall's door void with it
  const ex0 = L.BA_X[1] - 0.014
  const ex1 = L.BA_X[1] - 0.002
  for (const [y0, y1, z0] of [
    [L.BA_Y[0], L.BD_Y[0], 0.0],
    [L.BD_Y[1], L.BA_Y[1], 0.0],
    [L.BD_Y[0], L.BD_Y[1], L.BD_H],
  ] as [number, number, number][]) {
    w.add(mlib.box(ex0, y0, z0, ex1, y1, L.AL_Z), M.bathtile)
  }
  w.add(mlib.box(L.BA_X[0], L.BA_Y[0], L.AL_Z, L.BA_X[1], L.BA_Y[1], L.AL_Z + 0.08), M.ceil)

  // ------------------------------------------------- bedroom block (east)
  {
    const dv = W.wall([L.BED_X[0], L.BED_DIV[0]], [L.BED_X[1], L.BED_DIV[0]], 0, CZ, L.BED_DIV[1] - L.BED_DIV[0])
    W.faceMat(dv, 1, (c) => c[2] > RAIL)
    w.addMulti(dv, [M.lav, M.cream])
  }
  const wz: [number, number] = [0.86, 2.24]
  const holes: W.Hole[] = []
  for (const cy of [L.RB_WIN_Y, L.MB_WIN_Y]) {
    holes.push([L.NYW - (cy + 0.62), wz[0], L.NYW - (cy - 0.62), wz[1]])
  }
  w.add(W.wall([L.EXT_E, L.NYW], [L.EXT_E, L.SY], 0, RAIL, TW, holes), M.lav)
  w.add(W.wall([L.EXT_E, L.NYW], [L.EXT_E, L.SY], RAIL, CZ, TW), M.cream)
  {
    const bn = W.wall([L.BED_X[0], L.NYW], [L.BED_X[1], L.NYW], 0, CZ, TW)
    W.faceMat(bn, 1, (c) => c[2] > RAIL)
    w.addMulti(bn, [M.lav, M.cream])
  }
  for (const [y0, y1] of [
    [L.RB_Y[0], L.RB_Y[1]],
    [L.MB_Y[0], L.MB_Y[1]],
  ] as [number, number][]) {
    w.add(mlib.box(L.BED_X[0], y0, CZ, L.BED_X[1], y1, CZ + 0.1), M.ceil)
  }

  // ------------------------------------------------------------- ceilings
  w.add(mlib.prism(mainPoly, CZ, CZ + 0.1), M.ceil)
  // Start behind the header instead of overlapping its lower front face; the
  // shared coplanar band was flickering above the living-room window.
  w.add(mlib.box(L.AL_X[0], L.AL_S + alcoveHeaderDepth, L.AL_Z, L.AL_X[1], L.NYW, L.AL_Z + 0.1), M.ceil)

  // ---------------------------------------------------------------- trim
  const per: [number, number][] = [
    [L.EX, L.AL_S],
    [L.EX, L.SY],
    [0, L.SY],
    [0, L.CH_A[1]],
    L.CH_B,
    [L.N_BRICK[1], L.NY],
    [L.HALL_WW[0], L.HALL_Y0],
    [L.HALL_X[0], L.HALL_Y0],
    [L.HALL_X[0], L.NW_Y],
    [L.HALL_X[1], L.NW_Y],
    [L.HALL_X[1], L.AL_S],
    [L.EX, L.AL_S],
  ]
  w.add(W.runMolding(per, W.CROWN_PROF), M.ceil)
  w.add(W.runMolding([[L.AL_X[0], L.AL_S], [L.AL_X[0], L.NYW]], W.ALCOVE_CROWN), M.ceil)
  w.add(W.runMolding([[L.AL_X[1], L.NYW], [L.AL_X[1], L.AL_S]], W.ALCOVE_CROWN), M.ceil)
  w.add(
    W.runMolding(
      [
        [L.EX, L.CD_Y[1] + 0.06],
        [L.EX, L.SY],
        [0, L.SY],
        [0, L.W_PLASTER[1]],
      ],
      W.RAIL_PROF,
    ),
    M.beam,
  )
  w.add(W.runMolding([[L.EX, L.AL_S], [L.EX, L.MD_Y[1] + 0.06]], W.RAIL_PROF), M.beam)
  w.add(W.runMolding([[L.EX, L.MD_Y[0] - 0.06], [L.EX, L.CD_Y[1] + 0.06]], W.RAIL_PROF, true), M.beam)
  w.add(
    W.runMolding([[L.HALL_X[0], L.HALL_Y0], [L.HALL_X[0], L.NW_Y]], W.RAIL_PROF),
    M.beam,
  )
  // baseboards (broken at door openings and at brickwork)
  const basePaths: [number, number][][] = [
    [
      [L.EX, L.CD_Y[0]],
      [L.EX, L.SY],
      [0, L.SY],
      [0, L.FD_Y[0]],
    ],
    [
      [0, L.FD_Y[1]],
      [0, L.W_PLASTER[1]],
    ],
    [
      [L.EX, L.AL_S],
      [L.EX, L.MD_Y[1]],
    ],
    [
      [L.EX, L.MD_Y[0]],
      [L.EX, L.CD_Y[1]],
    ],
    [
      [L.HALL_X[0], L.BD_Y[0]],
      [L.HALL_X[0], L.HALL_Y0],
    ],
    [
      [L.HALL_X[0], L.NW_Y],
      [L.HALL_X[0], L.BD_Y[1]],
    ],
    [
      [L.HALL_X[1], L.NW_Y],
      [L.HALL_X[1], L.NYW],
    ],
    [
      [L.HALL_EW[1], L.NYW],
      [L.AL_X[1], L.NYW],
    ],
  ]
  for (const p of basePaths) w.add(W.runMolding(p, W.BASE_PROF), M.trim)
  // chair rail capping the green dado in the hallway
  const CHAIR: [number, number][] = [
    [1.078, 0.0012],
    [1.078, 0.023],
    [1.098, 0.0265],
    [1.11, 0.0195],
    [1.11, 0.0012],
  ]
  w.add(W.runMolding([[L.HALL_X[0], L.NW_Y], [L.CL_X[0], L.NW_Y]], CHAIR), M.green)
  w.add(W.runMolding([[L.CL_X[1], L.NW_Y], [L.HALL_X[1], L.NW_Y]], CHAIR), M.green)
  w.add(W.runMolding([[L.HALL_X[1], L.NW_Y], [L.HALL_X[1], L.NYW]], CHAIR), M.green)

  // ------------------------------------------------- wall panel mouldings
  const PAN_Z0 = 0.6
  const PAN_Z1 = 2.52
  const PAN_CZ = (PAN_Z0 + PAN_Z1) / 2
  const PAN_H = PAN_Z1 - PAN_Z0

  const panelRun = (a: number, b: number, normal: [number, number], at: number, horiz: 'x' | 'y', want = 1.3, margin = 0.34): void => {
    const span = b - a
    const n = Math.max(1, Math.round((span - margin) / (want + margin)))
    const pw = (span - (n + 1) * margin) / n
    if (pw < 0.42) return
    for (let i = 0; i < n; i++) {
      const c = a + margin + pw * 0.5 + i * (pw + margin)
      const [cx, cy] = horiz === 'x' ? [c, at] : [at, c]
      w.add(W.panelMoulding(cx, cy, PAN_CZ, pw, PAN_H, normal), M.trim)
    }
  }
  // south ('back') wall - broken by the timber post that carries the beam
  panelRun(0.0, L.POST_X[0], [0, 1], L.SY, 'x')
  panelRun(L.POST_X[1], L.EX, [0, 1], L.SY, 'x')
  // east wall - south of Rachel's opening, plus the wall vignette north of
  // Monica's doorway. The credenza/poster bay remains undecorated.
  panelRun(L.SY, L.CD_Y[0], [-1, 0], L.EX, 'y')
  panelRun(L.MD_WALL[0], L.MD_WALL[1], [-1, 0], L.EX, 'y', 0.6, 0.2)

  // ------------------------------------------------------- kitchen timber
  const [bz0, bz1] = L.BEAM_Z
  const [bx0, bx1] = L.BEAM_X
  const [by0, by1] = L.BEAM_Y
  const [px0, px1] = L.POST_X
  const beams: [ReturnType<typeof mlib.box>, THREE.Material][] = []
  beams.push([mlib.box(bx0, by0 - TW, bz0, bx1, by1, bz1), M.beam_y])
  beams.push([mlib.box(0.0, L.W_BRICK[0], bz0, 0.135, L.CH_A[1], bz1), M.beam_y])
  beams.push([mlib.box(L.N_BRICK[0], L.NY - 0.135, bz0, L.HALL_WW[0], L.NY, bz1), M.beam])
  const cp = [L.chamferPt(0.0, 0.0), L.chamferPt(1.44, 0.0), L.chamferPt(1.44, 0.135), L.chamferPt(0.0, 0.135)]
  beams.push([mlib.prism(cp, bz0, bz1), M.beam_z])
  for (const [b, mm] of beams) {
    mlib.bevel(b, 0.007, 2)
    w.add(b, mm)
  }
  // post at the beam's north end
  const post = mlib.box(px0, by1 - 0.2, 0.0, px1, by1, bz0 + 0.002)
  mlib.bevel(post, 0.008, 2)
  w.add(post, M.beam_v, { collide: true })
  // 45-degree knee brace in the plane of the beam.
  {
    const d = 0.5
    const wsec = 0.14
    const ya = by1 - 0.2
    const za = bz0 - d
    const q = wsec / Math.SQRT2
    const br = mlib.prismYZ(
      [
        [ya, za],
        [ya + q, za + q],
        [ya + q - d, za + q + d],
        [ya - d, za + d],
      ],
      bx0 + 0.024,
      bx1 - 0.024,
    )
    mlib.bevel(br, 0.006, 2)
    w.add(br, M.beam_y)
  }

  // ------------------------------------------ kitchen tile splash + sills
  w.add(mlib.box(0.0015, L.W_BRICK[0], 0.86, 0.0135, L.CH_A[1], 1.52), M.tile)
  w.add(mlib.box(L.N_BRICK[0], L.NY - 0.0135, 0.86, L.FRIDGE_X[0], L.NY - 0.0015, 1.52), M.tile)
  for (const [u0, u1, z0, z1] of [
    [0.02, 1.4, 0.86, L.KW_Z[0]],
    [0.02, L.KW_U[0] + 0.004, L.KW_Z[0], 1.52],
    [L.KW_U[1] - 0.004, 1.4, L.KW_Z[0], 1.52],
  ] as [number, number, number, number][]) {
    w.add(
      mlib.prism(
        [L.chamferPt(u0, 0.0015), L.chamferPt(u1, 0.0015), L.chamferPt(u1, 0.0135), L.chamferPt(u0, 0.0135)],
        z0,
        z1,
      ),
      M.tile,
    )
  }

  // ------------------------------------------------------ wall colliders
  w.wallCollider([0, L.SY], [0, 3.62], TW) // west (front door stays closed)
  w.wallCollider([0, 3.62], [1.02, 4.62], TW) // chamfer
  w.wallCollider([1.02, 4.62], [3.24, 4.62], TP) // north brick / bath south
  w.wallCollider([L.HALL_X[0], L.HALL_Y0], [L.HALL_X[0], L.NW_Y], 0.16, [
    [L.BD_Y[0] - L.HALL_Y0, L.BD_Y[1] - L.HALL_Y0], // bathroom doorway
  ])
  w.wallCollider([L.HALL_X[0], L.NW_Y], [L.HALL_X[1], L.NW_Y], 0.3) // closet (door closed)
  w.wallCollider([L.HALL_X[1], L.NW_Y], [L.HALL_X[1], L.NYW], 0.18) // remaining hall east wall
  w.wallCollider([AWX, L.AL_Y[1]], [L.AL_X[1], L.AL_Y[1]], TW) // alcove north (sill below window)
  w.wallCollider([L.EX, L.NYW], [L.EX, L.SY], L.EXW - L.EX, [
    [L.NYW - L.MD_Y[1], L.NYW - L.MD_Y[0]], // Monica's doorway
    [L.NYW - L.CD_Y[1], L.NYW - L.CD_Y[0]], // Rachel's cased opening
  ])
  w.wallCollider([L.EXT_E, L.SY], [0, L.SY], TW) // south
  w.wallCollider([L.BA_X[0], L.BA_Y[1]], [L.BA_X[1], L.BA_Y[1]], TW) // bath north
  w.wallCollider([L.BA_X[0], L.BA_Y[0]], [L.BA_X[0], L.BA_Y[1]], TW) // bath west
  w.wallCollider([L.BED_X[0], L.BED_DIV[0]], [L.BED_X[1], L.BED_DIV[0]], TP) // bedroom divider
  w.wallCollider([L.EXT_E, L.NYW], [L.EXT_E, L.SY], TW) // east exterior
  w.wallCollider([L.BED_X[0], L.NYW], [L.BED_X[1], L.NYW], TW) // bedroom north
  return M
}
