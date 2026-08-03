/** Central Perk shell: direct build_shell.py compilation.  Floors, walls,
 * ceilings, the raised bay platform, the cast-iron columns and beams, plus
 * the swept skirting/dado chains.  Every wall registers its collision body
 * with pass-through gaps only where a doorway actually is. */
import type * as THREE from 'three/webgpu'
import type { Vec2, Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import * as G from './geo'
import * as L from './layout'
import * as M from './materials'

function makeMaterials(): void {
  M.concrete('floor_concrete', L.CONCRETE)
  M.plankFloor('floor_plank')
  M.dotTile('tile_bay')
  M.brick('brick_wall')
  // the entrance pier is a warmer, more varied stock than the field walls
  M.brick('brick_pier', { face: '875033', face2: '5E3324', mortar: '8E8171', spread: 1.2 })
  M.plaster('plaster_ochre', L.OCHRE, 0.78)
  M.plaster('plaster_cream', L.CREAM, 0.8, 0.35, 22, 0.1)
  M.plaster('plaster_ceiling', 'CFC6B2', 0.86, 0.35, 12, 0.07)
  M.paint('paint_green_dado', L.GREEN_DADO, { rough: 0.3, coat: 0.12 })
  M.iron('iron_green', L.GREEN_IRON)
  M.paint('paint_joinery', L.GREEN_IRON, { rough: 0.26, coat: 0.2 })
  M.wood('wood_dark', { light: '8A5A2C', dark: '3C2110', ring: 30 })
  M.glass('glass_window', 'F2F6F4', 0.004)
  // The ceiling reads dark in every set photograph - above the lamps nothing
  // lights it but bounce; the cross beam is a much darker stained timber.
  M.paint('paint_tin_ceiling', '6E6455', { rough: 0.56, coat: 0.05 })
  M.wood('wood_beam', { light: '4C3A28', dark: '231A11', ring: 8, rough: [0.62, 0.8] })
}

// ------------------------------------------------------------------ floors

function floors(world: World): void {
  const concrete = M.get('floor_concrete')
  const tile = M.get('tile_bay')
  world.add(mlib.prism(G.ccw(L.mainSlabPoly()), L.SLAB_Z, 0), concrete)

  const [a, b, c, d] = L.PLANK_ZONE
  const o = L.SLAB_OVER
  world.add(
    mlib.prism(
      [
        [a - o, c],
        [b, c],
        [b, d + o],
        [a - o, d + o],
      ],
      L.SLAB_Z2,
      0,
    ),
    M.get('floor_plank'),
  )

  world.add(mlib.prism(G.ccw(G.polyOffset(L.kitchenPoly(), L.SLAB_OVER - 0.02)), L.SLAB_Z3, 0.004), tile)

  // hallway finished like the shop; only the lavatories at the end are tiled
  const hs = L.NY + L.SLAB_OVER
  world.add(
    mlib.prism(
      [
        [-L.TW - 0.1, hs],
        [L.WC_E + L.TW + 0.1, hs],
        [L.WC_E + L.TW + 0.1, L.HALL_N + L.TP + L.SLAB_OVER],
        [-L.TW - 0.1, L.HALL_N + L.TP + L.SLAB_OVER],
      ],
      L.SLAB_Z5,
      0,
    ),
    concrete,
  )
  world.add(
    mlib.prism(
      [
        [-L.TW - 0.14, L.HALL_N - 0.1],
        [L.WC_E + L.TW + 0.14, L.HALL_N - 0.1],
        [L.WC_E + L.TW + 0.14, L.WC_N + L.TW + 0.14],
        [-L.TW - 0.14, L.WC_N + L.TW + 0.14],
      ],
      L.SLAB_Z5 + 0.022,
      0.004,
    ),
    tile,
  )

  // the window bay: a step up, with a kerb that has a real top face
  world.add(mlib.prism(G.ccw(G.polyOffset(G.ccw(L.bayPoly()), L.SLAB_OVER)), L.SLAB_Z4, L.STEP), tile)
  const kerb = mlib.prism(
    [
      [L.EX - L.SLAB_OVER - 0.05, L.BAY_S],
      [L.EX + 0.03, L.BAY_S],
      [L.EX + 0.03, L.BAY_N],
      [L.EX - L.SLAB_OVER - 0.05, L.BAY_N],
    ],
    -0.04,
    L.STEP + 0.006,
  )
  mlib.bevel(kerb, 0.006, 2)
  world.add(kerb, M.get('paint_joinery'))
}

// ------------------------------------------------------------------ walls

/** Wall collision body offset to the built side, with pass-through gaps. */
function collideWall(world: World, p0: Vec2, p1: Vec2, t: number, side: number, gaps: [number, number][] = []): void {
  const dx = p1[0] - p0[0]
  const dy = p1[1] - p0[1]
  const length = Math.hypot(dx, dy) || 1
  const ux = dx / length
  const uy = dy / length
  const nx = -uy * side
  const ny = ux * side
  const spans: [number, number][] = []
  let cursor = 0
  for (const [g0, g1] of [...gaps].sort((x, y) => x[0] - y[0])) {
    if (g0 > cursor) spans.push([cursor, g0])
    cursor = Math.max(cursor, g1)
  }
  if (cursor < length) spans.push([cursor, length])
  for (const [s0, s1] of spans) {
    const mid = (s0 + s1) * 0.5
    world.obb(
      p0[0] + ux * mid + (nx * t) / 2,
      p0[1] + uy * mid + (ny * t) / 2,
      (s1 - s0) / 2,
      t / 2,
      Math.atan2(dy, dx),
    )
  }
}

function addWall(
  world: World,
  material: THREE.Material,
  p0: Vec2,
  p1: Vec2,
  t: number,
  z0: number,
  z1: number,
  holes: G.Hole[] = [],
  side = 1,
  gaps: [number, number][] = [],
): void {
  world.add(G.wallRun(p0, p1, t, z0, z1, holes, side), material)
  collideWall(world, p0, p1, t, side, gaps)
}

function walls(world: World): void {
  const brickWall = M.get('brick_wall')
  const ochre = M.get('plaster_ochre')
  const cream = M.get('plaster_cream')
  const T = L.TW
  const Z = L.CZ

  addWall(world, brickWall, [0, 0], [0, L.WC_N], T, L.FOUND_Z, Z)
  addWall(world, brickWall, [L.EX, 0], [0, 0], T, L.FOUND_Z, Z, [
    [L.EX - L.KIT_WIN[1], L.EX - L.KIT_WIN[0], 1.05, 2.3],
  ])
  addWall(world, brickWall, [L.EX, -T], [L.EX, L.BAY_S - L.TP], T, L.FOUND_Z, Z, [
    [T + L.E_WIN_S[0], T + L.E_WIN_S[1], L.STORE_SILL, L.STORE_HEAD],
  ], -1)
  // runs down ONTO the entrance pier, with its own top and underside
  addWall(world, brickWall, [L.EX, L.E_N_START], [L.EX, L.NY + L.TP], T, L.FOUND_Z2, Z + 0.05, [
    [L.E_WIN_N[0] - L.E_N_START, L.E_WIN_N[1] - L.E_N_START, L.STORE_SILL, L.STORE_HEAD],
  ], -1)

  // the painting wall, with the way through to the lavatories at its west end
  addWall(
    world,
    ochre,
    [0, L.NY],
    [L.EX, L.NY],
    L.TP,
    L.FOUND_Z2,
    Z + 0.06,
    [[L.LOBBY_DR[0], L.LOBBY_DR[1], L.FOUND_Z, L.LOBBY_H]],
    1,
    [[L.LOBBY_DR[0], L.LOBBY_DR[1]]],
  )

  // the window bay
  addWall(world, cream, [L.BAY_E + T, L.BAY_S], [L.EX, L.BAY_S], L.TP, L.FOUND_Z2, Z + 0.06)
  addWall(
    world,
    brickWall,
    [L.BAY_E, L.BAY_S],
    [L.BAY_E, L.BAY_DIAG_E],
    T,
    L.FOUND_Z,
    Z,
    [
      ...L.BAY_WIN.map(([a, b]) => [a - L.BAY_S, b - L.BAY_S, L.STEP + L.STORE_SILL, L.STORE_HEAD] as G.Hole),
      [L.TRAN_U[0], L.TRAN_U[1], L.TRAN_BOT, L.TRAN_TOP],
    ],
    -1,
  )
  // the diagonal, carrying the entrance doors and their transom
  addWall(
    world,
    brickWall,
    L.DIAG_A,
    L.DIAG_B,
    T,
    L.FOUND_Z,
    Z,
    [
      [L.ENTRY_U[0], L.ENTRY_U[1], L.FOUND_Z, L.ENTRY_H],
      [L.ENTRY_U[0], L.ENTRY_U[1], L.TRAN_BOT, L.TRAN_TOP],
      [L.DIAG_WIN[0], L.DIAG_WIN[1], L.STEP + L.STORE_SILL, L.STORE_HEAD],
      [L.DIAG_WIN[0], L.DIAG_WIN[1], L.TRAN_BOT, L.TRAN_TOP],
    ],
    1,
    [[L.ENTRY_U[0], L.ENTRY_U[1]]],
  )
  // the brick pier at the bay's north-west corner
  const pier = mlib.prism(
    [
      [L.EX + 0.02, L.PIER[0]],
      [L.EX + L.TB, L.PIER[0]],
      [L.EX + L.TB, L.PIER[1] - L.TB],
      [L.EX + 0.02, L.PIER[1] - 0.02],
    ],
    L.FOUND_Z,
    L.CZ + 0.06,
  )
  mlib.bevel(pier, 0.012, 2)
  world.add(pier, M.get('brick_pier'), { collide: true })

  // kitchen block: mitred quads on the layout lines kitchenOuter() computes
  const KO = L.kitchenOuter()
  const A = L.KIT_CH[0]
  const B = L.KIT_CH[1]
  const So = KO[1]
  const No = KO[2]
  const LAP = 0.005
  world.add(
    mlib.prism(
      G.ccw([
        [L.KIT_E, -0.06],
        [L.KIT_E + L.TP, -0.06],
        [So[0], So[1] + LAP],
        [A[0], A[1] + LAP],
      ]),
      L.FOUND_Z2,
      Z + 0.06,
    ),
    ochre,
  )
  world.box2(L.KIT_E, -0.06, L.KIT_E + L.TP, So[1] + LAP)
  world.add(
    mlib.prism(
      G.ccw([
        [A[0], A[1]],
        [So[0], So[1]],
        [No[0] - LAP, No[1]],
        [B[0] - LAP, B[1]],
      ]),
      L.FOUND_Z2 - 0.012,
      Z + 0.048,
    ),
    ochre,
  )
  {
    const dx = No[0] - So[0]
    const dy = No[1] - So[1]
    const len = Math.hypot(dx, dy)
    world.obb((A[0] + No[0]) / 2, (A[1] + No[1]) / 2, len / 2 + 0.04, L.TP / 2 + 0.02, Math.atan2(dy, dx))
  }
  const kn0 = No[0]
  addWall(
    world,
    ochre,
    [kn0, L.KIT_N],
    [0, L.KIT_N],
    L.TP,
    L.FOUND_Z2 - 0.024,
    Z + 0.072,
    [[kn0 - L.KIT_DR[1], kn0 - L.KIT_DR[0], L.FOUND_Z, L.DOOR_H]],
    -1,
    [[kn0 - L.KIT_DR[1], kn0 - L.KIT_DR[0]]],
  )

  // lobby + WCs
  addWall(
    world,
    brickWall,
    [L.WC_E, L.WC_N],
    [0, L.WC_N],
    T,
    L.FOUND_Z,
    Z,
    L.WC_WIN.map(([w0, w1]) => [L.WC_E - w1, L.WC_E - w0, 1.35, 2.35] as G.Hole),
    -1,
  )
  addWall(world, brickWall, [L.WC_E, L.WC_N], [L.WC_E, L.WC_S], T, L.FOUND_Z, Z)
  addWall(
    world,
    ochre,
    [0, L.HALL_N],
    [L.WC_E, L.HALL_N],
    L.TP,
    L.FOUND_Z,
    Z,
    L.WC_DOORS.map(([a, b]) => [a, b, L.FOUND_Z, L.DOOR_H] as G.Hole),
    1,
    L.WC_DOORS.map(([a, b]) => [a, b] as [number, number]),
  )
  addWall(world, cream, [L.GENTS[1], L.WC_N], [L.GENTS[1], L.WC_Y[0]], L.TP, L.FOUND_Z2, Z + 0.06)
}

// ------------------------------------------------------------------ ceilings

function ceilings(world: World): void {
  const o = 0.1
  const poly: Vec2[] = [
    [-L.TW - o, -L.TW - o],
    [L.EX, -L.TW - o],
    [L.EX, L.BAY_S],
    [L.BAY_E + L.TW + o, L.BAY_S],
    [L.BAY_E + L.TW + o, L.BAY_DIAG_E],
    [L.EX, L.BAY_N],
    [L.EX + L.TB, L.BAY_N],
    [L.EX + L.TB, L.NY + L.TP + o],
    [-L.TW - o, L.NY + L.TP + o],
  ]
  world.add(mlib.prism(G.ccw(poly), L.CZ, L.CZ + 0.22), M.get('paint_tin_ceiling'))
  world.add(
    mlib.prism(
      [
        [-L.TW + 0.09, L.NY + 0.07],
        [L.WC_E + L.TW - 0.09, L.NY + 0.07],
        [L.WC_E + L.TW - 0.09, L.WC_N + L.TW - 0.09],
        [-L.TW + 0.09, L.WC_N + L.TW - 0.09],
      ],
      2.74,
      2.96,
    ),
    M.get('plaster_ceiling'),
  )
}

// ------------------------------------------------------------------ structure

/** Cast-iron column: moulded base, entasised shaft, astragal, flared cap. */
function column(world: World, x: number, y: number, z0: number, z1: number): void {
  const r = L.COL_R
  const prof: Vec2[] = [[0, z0]]
  prof.push(
    [r * 1.85, z0],
    [r * 1.85, z0 + 0.035],
    [r * 1.62, z0 + 0.055],
    [r * 1.62, z0 + 0.1],
    [r * 1.34, z0 + 0.135],
    [r * 1.24, z0 + 0.2],
    [r * 1.1, z0 + 0.245],
  )
  const h0 = z0 + 0.245
  const h1 = z1 - 0.3
  for (let i = 0; i <= 10; i++) {
    const t = i / 10
    const z = h0 + (h1 - h0) * t
    const swell = 1 + 0.045 * Math.sin(Math.PI * Math.min(1, t * 1.12)) - 0.06 * t
    prof.push([r * swell, z])
  }
  prof.push(
    [r * 0.97, z1 - 0.285],
    [r * 1.12, z1 - 0.255],
    [r * 1.12, z1 - 0.225],
    [r * 0.96, z1 - 0.2],
    [r * 1.3, z1 - 0.115],
    [r * 1.55, z1 - 0.045],
    [r * 1.62, z1 - 0.012],
    [r * 1.62, z1],
    [0, z1],
  )
  const md = mlib.revolve(prof, 40)
  mlib.smoothShade(md, 34)
  mlib.translate(md, [x, y, 0])
  world.add(md, M.get('iron_green'))
  world.box2(x - r * 1.9, y - r * 1.9, x + r * 1.9, y + r * 1.9)
}

function structure(world: World): void {
  const tin = M.get('paint_tin_ceiling')
  const beamWood = M.get('wood_beam')
  const b1 = mlib.prism(
    [
      [L.COL_X - 0.14, L.BAY_S - 0.08],
      [L.COL_X + 0.14, L.BAY_S - 0.08],
      [L.COL_X + 0.14, L.BAY_N],
      [L.COL_X - 0.14, L.BAY_N],
    ],
    L.BEAM_Z[0],
    L.CZ + 0.1,
  )
  mlib.bevel(b1, 0.012, 2)
  world.add(b1, tin)

  // the dark cross timber carrying the SERVICE sign and the pendants
  const hw = L.BEAM_W * 0.5
  const bx = L.EX + L.TB - 0.06
  const b2 = mlib.prism(
    [
      [-0.02, L.BEAM_Y - hw],
      [bx, L.BEAM_Y - hw],
      [bx, L.BEAM_Y + hw],
      [-0.02, L.BEAM_Y + hw],
    ],
    L.BEAM_X_Z,
    L.CZ + 0.055,
  )
  mlib.bevel(b2, 0.014, 2)
  world.add(b2, beamWood)
  for (const s of [-1, 1]) {
    const f = mlib.prism(
      G.ccw([
        [-0.02, L.BEAM_Y + s * hw],
        [bx, L.BEAM_Y + s * hw],
        [bx, L.BEAM_Y + s * (hw + 0.035)],
        [-0.02, L.BEAM_Y + s * (hw + 0.035)],
      ]),
      L.BEAM_X_Z + 0.028,
      L.BEAM_X_Z + 0.088,
    )
    mlib.bevel(f, 0.008, 2)
    world.add(f, beamWood)
  }

  for (const [x, y] of L.COLS) column(world, x, y, L.ground(x, y) - 0.02, L.BEAM_Z[0] + 0.02)
}

// ------------------------------------------------------------------ trim

const CASE = 0.095
const B = -L.TRIM_BED

const SKIRT_PROF: Vec2[] = [
  [B, -0.012],
  [0.03, -0.012],
  [0.03, L.BASE_H - 0.03],
  [0.022, L.BASE_H - 0.022],
  [0.022, L.BASE_H - 0.01],
  [0.008, L.BASE_H],
  [B, L.BASE_H],
]

const DADO_PROF: Vec2[] = [
  [B, L.BASE_H],
  [0.018, L.BASE_H],
  [0.018, L.DADO - 0.075],
  [0.03, L.DADO - 0.062],
  [0.034, L.DADO - 0.03],
  [0.03, L.DADO - 0.008],
  [0.014, L.DADO],
  [B, L.DADO],
]

function trim(world: World): void {
  const green = M.get('paint_green_dado')
  const KO = L.kitchenOuter()
  const KD0 = L.KIT_DR[0] - CASE
  const KD1 = L.KIT_DR[1] + CASE
  const KY = L.KIT_N + L.TP
  const runs: Vec2[][] = [
    [[L.EX, L.BAY_S - 0.04], [L.EX, 0], ...KO.slice(0, 3), [KD1, KY]],
    [
      [KD0, KY],
      [0, KY],
      [0, L.NY],
      [L.LOBBY_DR[0] - CASE, L.NY],
    ],
    [
      [L.LOBBY_DR[1] + CASE, L.NY],
      [L.EX + 0.04, L.NY],
    ],
    [
      [L.WC_DOORS[1][1] + CASE, L.HALL_N],
      [L.WC_E, L.HALL_N],
      [L.WC_E, L.WC_S],
      [L.LOBBY_DR[1] + CASE, L.WC_S],
    ],
    [
      [L.LOBBY_DR[0] - CASE, L.WC_S],
      [0, L.WC_S],
      [0, L.HALL_N],
      [L.WC_DOORS[0][0] - CASE, L.HALL_N],
    ],
    [
      [L.WC_DOORS[0][1] + CASE, L.HALL_N],
      [L.WC_DOORS[1][0] - CASE, L.HALL_N],
    ],
  ]
  for (const pts of runs) {
    const p3 = G.densify(pts.map((p) => [p[0], p[1], 0] as Vec3), 0.05)
    world.add(G.tubeAlongMiter(p3, SKIRT_PROF, { miter: true }), green)
    world.add(G.tubeAlongMiter(p3, DADO_PROF, { miter: true }), green)
  }
  // the bay stands on its platform, so its skirting starts a step higher
  const bay: Vec2[] = [
    [L.BAY_E + 0.04, L.BAY_DIAG_E],
    [L.BAY_E, L.BAY_S],
    [L.EX - 0.04, L.BAY_S],
  ]
  const p3 = G.densify(bay.map((p) => [p[0], p[1], L.STEP] as Vec3), 0.05)
  world.add(G.tubeAlongMiter(p3, SKIRT_PROF, { miter: true }), M.get('paint_joinery'))
}

export function build(world: World): void {
  makeMaterials()
  floors(world)
  walls(world)
  ceilings(world)
  structure(world)
  trim(world)
}
