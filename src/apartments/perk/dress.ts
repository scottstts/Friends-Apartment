/** Where everything goes: the f_layout.py port.  Rugs are laid first, every
 * piece is placed at its L.py anchor and settled onto whatever it stands on,
 * and each settled group registers one collision footprint.
 *
 * L.py rotations are "rot = 0 faces +Y"; the furniture modules are built with
 * the BACK at +Y, so R() converts between them. */
import { MeshData } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'
import * as FC from './counter'
import * as FP from './props'
import * as FS from './seating'
import * as FT from './tables'

const R = (a: number): number => a + 180
const rad = (d: number): number => (d * Math.PI) / 180

type Group = FS.Placed[]

/** every rug laid so far, as (x0, y0, x1, y1, top_z) */
const RUGS: [number, number, number, number, number][] = []

/** The height a piece stands at, given its plan bounding box: the floor under
 * its centre, or the top of any rug its footprint overlaps. */
function G(x0: number, y0: number, x1: number, y1: number): number {
  let z = L.ground((x0 + x1) * 0.5, (y0 + y1) * 0.5)
  for (const [rx0, ry0, rx1, ry1, top] of RUGS) {
    if (x0 < rx1 && x1 > rx0 && y0 < ry1 && y1 > ry0 && top > z) z = top
  }
  return z
}

function groupBounds(group: Group): [number, number, number, number, number, number] {
  let x0 = Infinity
  let y0 = Infinity
  let z0 = Infinity
  let x1 = -Infinity
  let y1 = -Infinity
  let z1 = -Infinity
  for (const { md } of group) {
    for (const v of md.verts) {
      x0 = Math.min(x0, v[0])
      y0 = Math.min(y0, v[1])
      z0 = Math.min(z0, v[2])
      x1 = Math.max(x1, v[0])
      y1 = Math.max(y1, v[1])
      z1 = Math.max(z1, v[2])
    }
  }
  return [x0, y0, x1, y1, z0, z1]
}

/** Lift one piece - possibly several meshes - onto its surface as a unit. */
function settle(group: Group): Group {
  const [x0, y0, x1, y1] = groupBounds(group)
  const z = G(x0, y0, x1, y1)
  if (z) for (const { md } of group) mlib.translate(md, [0, 0, z])
  return group
}

/** Register one collision footprint for a settled group.  `inset` shrinks
 * the bounding box: chairs and turned-leg pieces are mostly air at knee
 * height, and the raw box seals walkways the floor plan keeps open. */
function addGroup(world: World, group: Group, inset = 0): void {
  const [x0, y0, x1, y1, , z1] = groupBounds(group)
  const cx = (x0 + x1) / 2
  const cy = (y0 + y1) / 2
  const hw = Math.max(0.05, (x1 - x0) / 2 - inset)
  const hh = Math.max(0.05, (y1 - y0) / 2 - inset)
  world.box2(cx - hw, cy - hh, cx + hw, cy + hh, 0, z1)
  for (const { md, mat } of group) world.add(md, mat)
}

/** Move a piece to its anchor: position BEFORE settling, so the footprint
 * lands on the right rug. */
function place(world: World, group: Group, x: number, y: number, rot?: number, inset = 0): void {
  for (const { md } of group) {
    if (rot !== undefined) mlib.rotateZ(md, rad(rot))
    mlib.translate(md, [x, y, 0])
  }
  addGroup(world, settle(group), inset)
}

function placed(world: World, group: Group, inset = 0): void {
  addGroup(world, settle(group), inset)
}

// ---------------------------------------------------------------- the rugs

function rug(name: string, cx: number, cy: number, w: number, d: number, oval = false, pal: M.PersianOpts = {}): { md: MeshData; at: [number, number, number] } {
  const z = L.ground(cx, cy)
  let pts
  if (oval) {
    pts = Array.from({ length: 48 }, (_, i) => {
      const a = (i * Math.PI * 2) / 48
      return [w * 0.5 * Math.cos(a), d * 0.5 * Math.sin(a)] as [number, number]
    })
  } else {
    pts = mlib.roundedRect(w, d, 0.02, 3)
  }
  const md = mlib.prism(pts, 0, L.RUG_T)
  mlib.bevel(md, 0.004, 2)
  // a different slice of the same lattice for every rug in the room
  let ph = 0
  for (let i = 0; i < name.length; i++) ph += (i + 3) * name.charCodeAt(i)
  ph = (ph % 997) * 0.0173
  RUGS.push([cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2, z + L.RUG_T])
  void M.persian('rug_' + name, { ...pal, wd: [w, d], phase: ph })
  return { md, at: [cx, cy, z] }
}

function rugs(world: World): void {
  const lay = (name: string, spec: [number, number, number, number], oval = false, pal: M.PersianOpts = {}): void => {
    const r = rug(name, spec[0], spec[1], spec[2], spec[3], oval, pal)
    world.add(r.md, M.get('rug_' + name), { at: r.at })
  }
  lay('main', L.RUG_MAIN)
  lay('oval', L.RUG_OVAL, true, { ground: '7E3320', border: '30405E', motif: 'CFC098' })
  lay('mid', L.RUG_MID, false, { ground: '96361F', border: '23364F', motif: 'D6C49C' })
  lay('north', L.RUG_N, false, { ground: '8A2A20', border: '24405A', motif: 'D2C098' })
  lay('south', L.RUG_S, false, { ground: '922C1E', border: '2A3A54', motif: 'D8C69E' })
  lay('bay', L.BAY_RUG, false, { ground: '8E3524', border: '2E4258', motif: 'D4C29A', accent: '3A5C40' })
  lay('bay_n', L.BAY_RUG_N, false, { ground: '7E3020', border: '27395A', motif: 'CFBE96', accent: '355340' })
}

// ---------------------------------------------------------------- the rooms

function mainGroup(world: World): void {
  place(world, FS.heroCouch(L.SOFA_L, L.SOFA_D), L.SOFA_C[0], L.SOFA_C[1], undefined, 0.02)
  placed(world, FT.coffeeTable(L.COFFEE_C[0], L.COFFEE_C[1], L.COFFEE_WD[0], L.COFFEE_WD[1], L.COFFEE_H), 0.03)
  place(world, FS.recliner(), L.RECLINER_C[0], L.RECLINER_C[1], R(L.RECLINER_ROT), 0.08)
  placed(world, FT.pedTable(L.SIDE_T_C[0], L.SIDE_T_C[1], L.SIDE_T_R, 0.735), 0.03)
  for (const a of [L.CHAIR_A, L.CHAIR_B]) {
    place(world, FS.bistroChair(), a[0], a[1], R(a[2]), 0.07)
  }
}

function counterGroup(world: World): void {
  FC.build(world)
  for (const [x, y] of L.STOOLS) place(world, FS.barStool(L.STOOL_H), x, y, undefined, 0.05)
}

function tablesZone(world: World): void {
  for (const [x, y] of [L.TABLE_1, L.TABLE_2]) {
    placed(world, FT.pedTable(x, y, L.TABLE_MID_R, 0.735), 0.03)
  }
  for (const [x, y] of L.TZ_CHAIRS) place(world, FS.woodStool(), x, y, undefined, 0.05)
}

function northAlcove(world: World): void {
  place(
    world,
    FS.settee(L.SETTEE_L, 0.8, { cover: 'velvet_rust', nbu: 5, nbv: 2, fringe: true, cushions: 2 }),
    L.SETTEE_C[0],
    L.SETTEE_C[1],
    undefined,
    0.02,
  )
  for (const a of [L.ARMCH_L, L.ARMCH_R]) {
    place(world, FS.clubChair(0.84, 0.88, 0.9, 'velvet_red'), a[0], a[1], R(a[2]), 0.04)
  }
  placed(world, FT.lowTable(L.OVAL_T[0], L.OVAL_T[1], L.OVAL_T_WD[0], L.OVAL_T_WD[1], 0.42, 'table_mahog', true), 0.03)
  place(world, FS.pouf(), L.POUF[0], L.POUF[1], undefined, 0.02)
  placed(world, FT.pedTable(L.ROUND_T_N[0], L.ROUND_T_N[1], 0.28, 0.68), 0.03)
  FP.potted(world, L.PLANT_N[0], L.PLANT_N[1], 0, 0.24, 0.42, 1.05, G)
}

function southZone(world: World): void {
  place(
    world,
    FS.settee(L.SOFA_S_L, 0.86, { cover: 'velvet_orange', nbu: 6, nbv: 2, fringe: true, cushions: 2 }),
    L.SOFA_S[0],
    L.SOFA_S[1],
    R(0),
    0.02,
  )
  placed(world, FT.lowTable(L.TABLE_S[0], L.TABLE_S[1], L.TABLE_S_WD[0], L.TABLE_S_WD[1], 0.44, 'table_walnut'), 0.03)
  for (const a of L.TS_CHAIRS) place(world, FS.bistroChair(), a[0], a[1], R(a[2]), 0.07)
  placed(world, FT.pedTable(L.SIDE_T_S[0], L.SIDE_T_S[1], 0.3, 0.7), 0.03)
  FP.potted(world, L.PLANT_S[0], L.PLANT_S[1], 0, 0.21, 0.36, 0.86, G)
}

function bay(world: World): void {
  place(
    world,
    FS.settee(L.BAY_SOFA_L, 0.8, { cover: 'damask_gold', nbu: 6, nbv: 2, backH: 0.945 }),
    L.BAY_SOFA[0],
    L.BAY_SOFA[1],
    R(90),
    0.02,
  )
  placed(world, FT.lowTable(L.BAY_LOW_T[0], L.BAY_LOW_T[1], L.BAY_LOW_WD[0], L.BAY_LOW_WD[1], 0.42, 'table_mahog'), 0.03)
  placed(world, FT.pedTable(L.BAY_ROUND_T[0], L.BAY_ROUND_T[1], 0.33, 0.735), 0.03)
  for (const a of L.BAY_CH) place(world, FS.bistroChair(), a[0], a[1], R(a[2]), 0.07)
  const z = L.ground(...L.BAY_URN)
  FP.urnPlanter(world, L.BAY_URN[0], L.BAY_URN[1], z, 0.25, 0.62)
  FP.bouquet(world, L.BAY_URN[0], L.BAY_URN[1], z + 0.56, { r: 0.34, h: 0.4, nstem: 110 })
  FP.potted(world, L.BAY_PLANT[0], L.BAY_PLANT[1], 0, 0.22, 0.36, 0.8, G)
  // clear of the flower urn: leaned closer its neck went through the blooms
  FP.guitar(world, 9.62, 6.34, L.STEP, -150, 12)
}

// ---------------------------------------------------------------- fittings

/** The four fixtures that actually light the room, and how hard.  Everything
 * else glows without illuminating: thirty small sources cancel each other's
 * modelling out, so one real lamp per zone carries the room. */
const LAMPS: Record<string, number> = {
  Pendant_1: 300, // opal schoolhouse on the cross beam, mid room
  Pendant_ctr_a: 250, // green enamel cone over the counter
  Pendant_tiff: 300, // leaded amber shade over the couch group
  Chandelier: 240, // antler chandelier over the entrance and bay
}

function fittings(world: World): void {
  FP.mats()
  L.PENDANTS.forEach(([x, y], i) => {
    FP.schoolhouse(world, x, y, L.PENDANT_Z, L.BEAM_X_Z, LAMPS[`Pendant_${i}`] ?? 0)
  })
  FP.schoolhouse(world, 5.24, 7.6, 2.42, L.CZ, LAMPS['Pendant_mid'] ?? 0)
  FP.tiffanyPendant(world, 6.24, 5.1, 2.26, L.CZ, LAMPS['Pendant_tiff'] ?? 0)
  FP.conePendant(world, 2.05, 9.2, 2.06, L.CZ, LAMPS['Pendant_ctr_a'] ?? 0)
  FP.conePendant(world, 2.05, 6.85, 2.06, L.CZ, LAMPS['Pendant_ctr_b'] ?? 0)
  FP.antlerChandelier(world, L.CHANDELIER[0], L.CHANDELIER[1], 2.42, LAMPS['Chandelier'] ?? 0)
  // sconces on the brick, where the reference has them; the two on the west
  // wall sit above the back bar's top shelf
  const sconces: [number, number, [number, number]][] = [
    [0.055, 8.05, [1, 0]],
    [0.055, 10.6, [1, 0]],
    [L.EX - 0.02, 11.85, [-1, 0]],
    [0.055, 2.1, [1, 0]],
    [0.055, 5.05, [1, 0]],
    [L.EX - 0.02, 2.35, [-1, 0]],
  ]
  for (const [x, y, f] of sconces) {
    const z = x < 0.5 && y > 4.2 && y < 12.7 ? 2.34 : 1.86
    FP.sconce(world, x, y, z, f)
  }
  // the corridor: plain opal globes on the lobby ceiling, emissive only
  const globes: [number, number][] = [
    [1.32, L.NY + 0.62],
    [2.7, L.HALL_N - 0.7],
    [4.9, L.HALL_N - 0.7],
  ]
  for (const [gx, gy] of globes) FP.ceilingGlobe(world, gx, gy, 2.72)
  FP.tableLamp(world, L.BAY_ROUND_T[0] - 0.02, L.BAY_ROUND_T[1], L.STEP + 0.735)
  // neon: every word is bent tube out of the script alphabet
  FP.neonScript(world, 'latte', 'Latte', 0.1, 11.55, 2.46, 0.155, 'FF3D7A', [1, 0], 0.86)
  // the cup, on the pier's south face, sized to it
  FP.neonCup(world, L.EX + L.TB * 0.5 + 0.01, L.PIER[0] - 0.035, 2.3, 0.115, [0, -1])
  // Cappuccino and Espresso hang inside the transom band over the bay
  const tz = 2.86
  FP.neonScript(world, 'capp', 'Cappuccino', L.BAY_E - 0.115, 6.15, tz, 0.115, 'FF3244', [-1, 0], 1.24)
  FP.neonScript(world, 'esp', 'Espresso', L.BAY_E - 0.115, 4.3, tz, 0.115, 'FF3244', [-1, 0], 1.24)
  FP.serviceSign(world, L.SERVICE_SIGN[0], L.SERVICE_SIGN[1], L.SERVICE_SIGN[2], L.SERVICE_WH[0], L.SERVICE_WH[1], L.BEAM_X_Z)
  FP.painting(world, L.PAINTING[0], L.NY - 0.004, L.PAINTING[1], L.PAINTING[2], [0, -1], FP.ASSET_PAINTING)
  const bx = (L.BAY_WIN[1][0] + L.BAY_WIN[1][1]) * 0.5
  FP.decal(world, L.BAY_E - 0.012, bx, 1.66, 1.28, [-1, 0], FP.ASSET_DECAL)
}

function curtains(world: World): void {
  for (const [a, b] of L.BAY_WIN) {
    const sides: [number, [number, number]][] = [
      [0, [a - 0.1, a + 0.3]],
      [1, [b - 0.3, b + 0.1]],
    ]
    for (const [s, [u0, u1]] of sides) {
      FP.curtain(
        world,
        [L.BAY_E - 0.1, u0],
        [L.BAY_E - 0.1, u1],
        L.STORE_HEAD + 0.06,
        L.STEP + 0.02,
        4,
        0.048,
        s ? 'curtain_stripe' : 'curtain_stripe2',
      )
    }
  }
  const northSides: [number, [number, number]][] = [
    [0, [L.E_WIN_N[0] - 0.08, L.E_WIN_N[0] + 0.34]],
    [1, [L.E_WIN_N[1] - 0.34, L.E_WIN_N[1] + 0.08]],
  ]
  for (const [, [u0, u1]] of northSides) {
    FP.curtain(world, [L.EX - 0.1, u0], [L.EX - 0.1, u1], 2.52, 0.02, 4, 0.046, 'curtain_stripe')
  }
}

/** The clutter.  A set with nobody in it still has to look used. */
function dressing(world: World): void {
  const TOP = (x: number, y: number, h: number): number => G(x - 0.22, y - 0.22, x + 0.22, y + 0.22) + h
  const [cx, cy] = L.COFFEE_C
  const cz = TOP(cx, cy, L.COFFEE_H)
  FP.bouquet(world, cx + 0.44, cy - 0.1, cz, {
    r: 0.16,
    h: 0.2,
    nstem: 16,
    vase: [0.115, 0.105, null],
    colours: ['E2621F', 'E8A41C', 'D8324A'],
  })
  const cups: [number, number, string][] = [
    [-0.42, 0.14, 'EDE8DC'],
    [-0.18, -0.16, 'E8D24A'],
    [0.1, 0.18, 'D8E4C8'],
  ]
  cups.forEach(([dx, dy, col], i) => FP.cup(world, cx + dx, cy + dy, cz, col, true, i * 47))
  // a stack, not two books side by side on the same plane
  const books: [number, number, string, number][] = [
    [-0.05, -0.06, '2E4A7A', 8],
    [-0.03, -0.09, '9E3A24', -13],
    [-0.06, -0.05, 'C8B24A', 21],
  ]
  books.forEach(([dx, dy, col, rt], i) => FP.book(world, cx + dx, cy + dy, cz + i * 0.03, col, rt))
  const tableCups: [number, number, number][] = [
    [L.TABLE_1[0] + 0.1, L.TABLE_1[1], 0.735],
    [L.TABLE_2[0] - 0.08, L.TABLE_2[1] + 0.06, 0.735],
    [L.SIDE_T_C[0], L.SIDE_T_C[1] + 0.05, 0.735],
    [L.BAY_ROUND_T[0] + 0.19, L.BAY_ROUND_T[1] - 0.11, 0.735],
    [L.SIDE_T_S[0], L.SIDE_T_S[1], 0.7],
  ]
  tableCups.forEach(([x, y, h], i) => FP.cup(world, x, y, TOP(x, y, h), 'EDE8DC', true, i * 33))
  FP.bouquet(world, L.OVAL_T[0], L.OVAL_T[1], TOP(L.OVAL_T[0], L.OVAL_T[1], 0.42), {
    r: 0.15,
    h: 0.22,
    nstem: 14,
    vase: [0.11, 0.115, '6E5A3A'],
  })
  FP.bouquet(world, L.BAY_LOW_T[0], L.BAY_LOW_T[1], TOP(L.BAY_LOW_T[0], L.BAY_LOW_T[1], 0.42), {
    r: 0.14,
    h: 0.2,
    nstem: 12,
    vase: [0.105, 0.1, null],
  })
}

const tick = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0))

export async function build(world: World): Promise<void> {
  RUGS.length = 0
  rugs(world)
  await tick()
  mainGroup(world)
  await tick()
  counterGroup(world)
  await tick()
  tablesZone(world)
  northAlcove(world)
  await tick()
  southZone(world)
  bay(world)
  await tick()
  fittings(world)
  await tick()
  curtains(world)
  dressing(world)
}
