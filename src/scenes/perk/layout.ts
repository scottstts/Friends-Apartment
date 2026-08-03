/** Authoritative Central Perk dimensions from build_scripts/Central_Perk/L.py.
 *
 * Origin: inside face of the WEST wall x inside face of the SOUTH wall of the
 * main room.  +X = east (street windows), +Y = north (bathrooms), +Z = up.
 * The main room's concrete floor is z = 0; the window bay is a step up.
 */

// --------------------------------------------------------------- heights
export const CZ = 3.7
export const BEAM_Z: [number, number] = [3.28, CZ]
export const STEP = 0.155
export const DADO = 1.06
export const BASE_H = 0.145

export const TW = 0.24
export const TP = 0.16
export const TB = 0.34

// --------------------------------------------------------- placement rules
export const SLAB_Z = -0.12
export const SLAB_Z2 = -0.13
export const SLAB_Z3 = -0.14
export const SLAB_Z4 = -0.15
export const SLAB_Z5 = -0.16
export const SLAB_OVER = 0.12
export const FOUND_Z = -0.06
export const FOUND_Z2 = -0.07
export const TRIM_BED = 0.004
export const RUG_T = 0.012

export const DOOR_H = 2.12
export const STORE_SILL = 0.46
export const STORE_HEAD = 2.52
export const TRAN_BOT = 2.62
export const TRAN_TOP = 3.28

// --------------------------------------------------------------- main room
export const WX = 0
export const SY = 0
export const EX = 7.4
export const NY = 13.21

export const LOBBY_DR: [number, number] = [0.85, 1.79]
export const LOBBY_H = 2.24

// --------------------------------------------------------------- window bay
export const BAY_E = 10.21
export const BAY_S = 2.66
export const BAY_N = 10.05
export const BAY_DIAG_E = 7.24

export const PIER: [number, number] = [9.3, BAY_N]
export const E_N_START = BAY_N - 0.02

export const DIAG_A: [number, number] = [EX, BAY_N]
export const DIAG_B: [number, number] = [BAY_E, BAY_DIAG_E]
export const ENTRY_U: [number, number] = [0.74, 2.64]
export const ENTRY_H = 2.36
export const DIAG_WIN: [number, number] = [2.84, 3.7]

export const BAY_WIN: [number, number][] = [
  [2.92, 4.32],
  [4.56, 5.96],
  [6.2, 7.04],
]
export const TRAN_U: [number, number] = [0.26, 4.38]

export const E_WIN_S: [number, number] = [0.7, 1.63]
export const E_WIN_N: [number, number] = [11.06, 12.2]

// --------------------------------------------------------------- kitchen
export const KIT_E = 2.97
export const KIT_N = 3.11
export const KIT_CH: [[number, number], [number, number]] = [
  [KIT_E, 1.93],
  [2.33, KIT_N],
]
export const KIT_DR: [number, number] = [0.86, 1.83]
export const KIT_WIN: [number, number] = [0.74, 2.07]

// --------------------------------------------------------------- lobby + WCs
export const WC_S = NY + TP
export const WC_N = 16.79
export const WC_E = 5.97
export const HALL_N = 14.68
export const WC_Y: [number, number] = [HALL_N + TP, WC_N]
export const GENTS: [number, number] = [0, 2.9]
export const WC_DOORS: [number, number][] = [
  [1.02, 1.84],
  [3.86, 4.68],
]
export const WC_WIN: [number, number][] = [
  [0.6, 1.6],
  [2.9, 3.9],
  [4.4, 5.4],
]

// --------------------------------------------------------------- structure
export const COL_R = 0.105
export const BEAM_Y = 9.55
export const BEAM_W = 0.26
export const BEAM_X_Z = BEAM_Z[0] - 0.048
export const COL_X = EX + 0.15
export const COL_X_IN = 3.3
export const COLS: [number, number][] = [
  [COL_X, 2.907836],
  [COL_X, 7],
  [COL_X_IN, BEAM_Y],
  [6.956275, BEAM_Y],
]

// --------------------------------------------------------------- the counter
export const BACK_D = 0.58
export const BACK_H = 0.94
export const BACK_TALL_S: [number, number] = [4.21, 5.18]
export const BACK_TALL_N: [number, number] = [11.37, 12.63]
export const BACK_TALL_H = 2.18

export const SERVE_BACK = 1.38
export const SERVE_H = 1.06
export const SERVE_FRONT: [number, number][] = [
  [2, 10.04],
  [2, 9.36],
  [2.5, 8.86],
  [2.5, 7.64],
  [2.07, 7.18],
  [2.07, 6],
]
export const STOOLS: [number, number][] = [
  [2.6, 9.42],
  [3.06, 8.44],
  [3.05, 7.6],
  [2.62, 6.55],
]
export const STOOL_H = 0.74

// --------------------------------------------------------------- furniture

/** The rotation that turns a piece at (x, y) towards (tx, ty).
 * rot = 0 faces +Y and is measured counter-clockwise. */
export function face(x: number, y: number, tx: number, ty: number, jitter = 0): number {
  return Math.round(((Math.atan2(x - tx, ty - y) * 180) / Math.PI + jitter) * 10) / 10
}

/** A chair at (x, y), turned towards `tgt` and knocked `jitter` deg off square. */
export function seat(x: number, y: number, tgt: [number, number], jitter = 0): [number, number, number] {
  return [x, y, face(x, y, tgt[0], tgt[1], jitter)]
}

// -- the main seating group ------------------------------------------------
export const SOFA_C: [number, number] = [4.77, 5.82]
export const SOFA_L = 2.24
export const SOFA_D = 0.92
export const COFFEE_C: [number, number] = [4.79, 4.65]
export const COFFEE_WD: [number, number] = [1.57, 0.88]
export const COFFEE_H = 0.44
export const RECLINER_C: [number, number] = [6.5, 4.63]
export const RECLINER_ROT = 90
export const SIDE_T_C: [number, number] = [3.18, 4.79]
export const SIDE_T_R = 0.3
export const CHAIR_A = seat(2.83, 5.44, SIDE_T_C, -11)
export const CHAIR_B = seat(2.86, 4.24, SIDE_T_C, 8)
export const RUG_MAIN: [number, number, number, number] = [4.8, 4.71, 3.89, 2.63]
export const RUG_OVAL: [number, number, number, number] = [1.57, 4.7, 1.86, 1.68]

// -- the tables zone -------------------------------------------------------
export const RUG_MID: [number, number, number, number] = [5.04, 7.84, 3.29, 2.18]
export const TABLE_1: [number, number] = [4.48, 7.91]
export const TABLE_2: [number, number] = [6.02, 7.91]
export const TABLE_MID_R = 0.3
export const TZ_CHAIRS: [number, number, number][] = [
  seat(4.44, 8.56, TABLE_1, 7),
  seat(4.06, 7.36, TABLE_1, -9),
  seat(5.14, 7.52, TABLE_1, 12),
  seat(6.48, 8.42, TABLE_2, -8),
  seat(6, 7.2, TABLE_2, 6),
]

export const PAINTING: [number, number, number] = [3.66, 2.05, 1.8]

// -- the north alcove ------------------------------------------------------
export const ALC_DX = -0.6
export const RUG_N: [number, number, number, number] = [4.85 + ALC_DX, 12.03, 3.5, 2.39]
export const SETTEE_C: [number, number] = [PAINTING[0], 12.71]
export const SETTEE_L = 1.6
export const ARMCH_L: [number, number, number] = [2.98, 11.69, -90]
export const ARMCH_R: [number, number, number] = [5.5, 11.69, 90]
export const OVAL_T: [number, number] = [4.78 + ALC_DX, 11.73]
export const OVAL_T_WD: [number, number] = [1.18, 0.64]
export const POUF: [number, number] = [2.34, 12.46]
export const ROUND_T_N: [number, number] = [6.42 + ALC_DX, 12.72]
export const PLANT_N: [number, number] = [6.98 + ALC_DX, 12.52]

// -- the south zone --------------------------------------------------------
export const RUG_S: [number, number, number, number] = [5.2, 1.73, 2.94, 3.04]
export const SOFA_S: [number, number] = [5.28, 0.5]
export const SOFA_S_L = 2.05
export const TABLE_S: [number, number] = [5.25, 1.57]
export const TABLE_S_WD: [number, number] = [1.57, 0.79]
export const TS_CHAIRS: [number, number, number][] = [
  seat(4.66, 2.62, TABLE_S, 6),
  seat(3.86, 1.92, TABLE_S, -5),
  seat(6.46, 2.36, TABLE_S, 9),
  seat(3.62, 1.02, TABLE_S, -7),
]
export const SIDE_T_S: [number, number] = [7, 0.5]
export const PLANT_S: [number, number] = [6.84, 1.42]

// -- the window bay --------------------------------------------------------
export const BAY_RUG: [number, number, number, number] = [8.9, 4.9, 2.61, 3.31]
export const BAY_RUG_N: [number, number, number, number] = [8.24, 7.44, 1.6, 1.24]
export const BAY_SOFA: [number, number] = [9.58, 5.16]
export const BAY_SOFA_L = 2.07
export const BAY_LOW_T: [number, number] = [8.78, 5.31]
export const BAY_LOW_WD: [number, number] = [0.67, 1.19]
export const BAY_ROUND_T: [number, number] = [8.95, 4.01]
export const BAY_CH: [number, number, number][] = [
  seat(8.24, 6.26, BAY_LOW_T, -13),
  seat(8.1, 4.6, BAY_LOW_T, 10),
  seat(9.06, 3.16, BAY_ROUND_T, -7),
]
export const BAY_URN: [number, number] = [9.42, 6.92]
export const BAY_PLANT: [number, number] = [9.68, 3.55]

// -- fittings --------------------------------------------------------------
export const PENDANTS: [number, number][] = [
  [2.36, BEAM_Y],
  [4.98, BEAM_Y],
  [6.62, BEAM_Y],
]
export const PENDANT_Z = 2.34
export const CHANDELIER: [number, number] = [8.52, 7.86]
export const SERVICE_SIGN: [number, number, number] = [4.32, BEAM_Y, 2.76]
export const SERVICE_WH: [number, number] = [1.3, 0.36]

// --------------------------------------------------------------- palette
export const GREEN_IRON = '17372B'
export const GREEN_DADO = '2A4A35'
export const OCHRE = 'B0763C'
export const TERRA = '9E4B27'
export const CONCRETE = '7C8179'
export const CREAM = 'D9CFB6'

export function diagDir(): { d: [number, number]; l: number } {
  const dx = DIAG_B[0] - DIAG_A[0]
  const dy = DIAG_B[1] - DIAG_A[1]
  const l = Math.hypot(dx, dy)
  return { d: [dx / l, dy / l], l }
}

/** A point u metres along the entrance diagonal, off metres into the bay. */
export function diagPt(u: number, off = 0): [number, number] {
  const { d } = diagDir()
  const nx = d[1]
  const ny = -d[0]
  return [DIAG_A[0] + d[0] * u + nx * off, DIAG_A[1] + d[1] * u + ny * off]
}

/** The boarded service zone in front of the counter: x0, x1, y0, y1. */
export const PLANK_ZONE: [number, number, number, number] = [0, 3.62, 3.4, NY]

/** The height a piece of furniture stands at; only the bay is a step up. */
export function ground(x: number, y: number): number {
  if (x >= EX - 0.02 && y >= BAY_S && y <= BAY_N) return STEP
  return 0
}

/** The kitchen block's outline as the MAIN ROOM sees it. */
export function kitchenOuter(): [number, number][] {
  let dx = KIT_CH[1][0] - KIT_CH[0][0]
  let dy = KIT_CH[1][1] - KIT_CH[0][1]
  const l = Math.hypot(dx, dy)
  dx /= l
  dy /= l
  const nx = dy
  const ny = -dx
  const a: [number, number] = [KIT_CH[0][0] + nx * TP, KIT_CH[0][1] + ny * TP]
  const t1 = (KIT_E + TP - a[0]) / dx
  const t2 = (KIT_N + TP - a[1]) / dy
  return [
    [KIT_E + TP, SY],
    [KIT_E + TP, a[1] + dy * t1],
    [a[0] + dx * t2, KIT_N + TP],
    [WX, KIT_N + TP],
  ]
}

/** The slab: main-room outline running SLAB_OVER under every wall. */
export function mainSlabPoly(): [number, number][] {
  const o = SLAB_OVER
  const [a, b, c] = PLANK_ZONE
  return [
    [KIT_E - o, SY - o],
    [EX + o, SY - o],
    [EX + o, NY + o],
    [b, NY + o],
    [b, c],
    [a - o, c],
    [a - o, KIT_N - o],
    [KIT_CH[1][0] - o, KIT_N - o],
    [KIT_E - o, KIT_CH[0][1] - o],
  ]
}

export function bayPoly(): [number, number][] {
  return [
    [EX, BAY_S],
    [BAY_E, BAY_S],
    [BAY_E, BAY_DIAG_E],
    [EX, BAY_N],
  ]
}

export function kitchenPoly(): [number, number][] {
  return [
    [WX, SY],
    [KIT_E, SY],
    [KIT_CH[0][0], KIT_CH[0][1]],
    [KIT_CH[1][0], KIT_N],
    [WX, KIT_N],
  ]
}
