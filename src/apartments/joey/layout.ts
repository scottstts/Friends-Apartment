/** Authoritative apartment 19 dimensions from build_scripts/Joeys_apt/L.py.
 *
 * Origin: inside face of the west wall x inside face of the south wall.
 * +X = east (kitchen/front door), +Y = north (windows/couch), +Z = up.
 */

export const CZ = 3.15
export const BASE_H = 0.175
export const BASE_T = 0.022
export const RAIL_Z = 2.66
export const TW = 0.3
export const TP = 0.16

export const WX = 0
export const EX = 8.47
export const SY = -1.3
export const NY = 7.3
export const JX = 5
export const NY2 = 4.9

export const WIN_W = 0.77
export const WIN_SILL = 0.62
export const WIN_HEAD = 2.42
export const WIN_A: [number, number] = [0.52, 0.52 + WIN_W]
export const WIN_B: [number, number] = [1.87, 1.87 + WIN_W]
export const SCONCE_X = (WIN_A[1] + WIN_B[0]) * 0.5
export const SCONCE_Z = 1.82
export const BD_X: [number, number] = [3.58, 4.5]
export const BD_H = 2.12
export const DOOR_TOP = 2.12
export const ROD_X: [number, number] = [0.28, 2.9]
export const ROD_Z = 2.63

export const CTR_H = 0.92
export const CTR_D = 0.655
export const TOE_H = 0.095
export const TOE_IN = 0.075
export const PEN_X: [number, number] = [JX, JX + 0.72]
export const PEN_Y: [number, number] = [3.1, NY2]
export const K_SINK: [number, number] = [PEN_X[1], PEN_X[1] + 0.8]
export const K_STOVE: [number, number] = [K_SINK[1], K_SINK[1] + 1.1]
export const K_FRIDGE: [number, number] = [K_STOVE[1], EX]
export const K_FRIDGE_H = 1.84
export const UPPER_Z: [number, number] = [1.44, 2.3]
export const UPPER_D = 0.345
export const K_UPPER: [number, number] = [JX, 6.86]
export const K_MW: [number, number] = [6.86, 7.56]
export const K_MW_Z: [number, number] = [1.44, 1.78]
export const K_SHELF: [number, number] = [7.56, 8.42]
export const K_SHELF_Z: [number, number] = [1.9, 2.46]
export const SPLASH_X: [number, number] = [K_UPPER[0], 7.62]
export const SPLASH_Z: [number, number] = [CTR_H - 0.008, UPPER_Z[0]]

export const FD_Y: [number, number] = [2.03, 3.13]
export const FD_H = 2.2
export const PHONE_Y = 3.72

export const JOEY_DOOR: [number, number] = [-0.13, 0.77]
export const CHAN_DOOR: [number, number] = [4.45, 5.35]
export const ENT_Y: [number, number] = [1.01, 4.21]
export const ENT_D = 0.545
export const DOOR_OPEN = 86

export const BW_TH = 0.3
export const BED_W = -3.85
export const BED_E = -0.3
export const CH_X: [number, number] = [BED_W, BED_E]
export const CH_Y: [number, number] = [2.7, 6.5]
export const PARTY: [number, number] = [2.54, 2.7]
export const JO_X: [number, number] = [BED_W, BED_E]
export const JO_Y: [number, number] = [-1.3, PARTY[0]]
export const CH_WIN: [[number, number], [number, number]] = [
  [-2.96, -2.36],
  [-1.56, -0.94],
]
export const JO_WIN: [number, number] = [0.05, 0.9]
export const DART_AT = BED_E + (BW_TH + 0.042) * 0.5
export const DART_X = (JOEY_DOOR[0] + JOEY_DOOR[1]) * 0.5
export const DART_Z = 1.73

export const BA_X: [number, number] = [2.85, 5.6]
export const BA_Y: [number, number] = [NY + TW, NY + TW + 3.05]
export const BA_CZ = 2.62
export const BA_TUB_X: [number, number] = [BA_X[0], BA_X[0] + 1.55]
export const BA_TUB_Y: [number, number] = [BA_Y[1] - 0.72, BA_Y[1]]
export const BA_VAN_Y: [number, number] = [BA_Y[0] + 0.95, BA_Y[0] + 1.95]
export const BA_BASIN: [number, number] = [BA_X[1] - 0.3, (BA_VAN_Y[0] + BA_VAN_Y[1]) * 0.5]
export const BA_WC: [number, number] = [BA_X[1] - 0.3, BA_Y[0] + 0.68]

export const SOFA_C: [number, number] = [(WIN_A[0] + WIN_B[1]) * 0.5, NY - 0.47]
export const SOFA_L = 1.96
export const SOFA_D = 0.9
export const COFFEE_C: [number, number] = [1.42, NY - 1.42]
export const REC_A: [number, number] = [2.45, 3.73]
export const REC_B: [number, number] = [2.45, 2.01]
export const REC_ROT_A = 24
export const REC_ROT_B = -23
export const GLASS_T: [number, number] = [2.12, 2.87]
export const RUG_C: [number, number] = [2.4, 2.84]
export const RUG_WH: [number, number] = [2.2, 3.5]
export const STOOL_A: [number, number] = [PEN_X[0] - 0.3, 3.58]
export const STOOL_B: [number, number] = [PEN_X[0] - 0.3, 4.26]
export const STOOL_H = 0.7
export const DOG: [number, number] = [0.34, 6.46]
export const DOG_ROT = 90
export const DOG_SCALE = 1.02
export const FOOS_C: [number, number] = [7.2, 1.12]
export const FOOS_ROT = 104
export const FOOS_L = 1.42
export const FOOS_W = 0.76
export const FOOS_H = 0.9
export const BENCH_C: [number, number] = [3.4, 0.3]
export const SHELF_C: [number, number] = [5.72, 0.26]

export const WALL = 'C9C2B2'
export const WALL_UP = 'D6CCB8'
export const TRIM = 'DED6C4'
export const DOOR_GREY = 'CFC8BC'
export const CAB_CREAM = 'E4DAC4'
export const ISL_PUTTY = 'C4B49A'
export const YELLOW = 'E8CE1C'
export const CURTAIN = 'C3AE85'
export const CEIL = 'E0DACD'

export const rodLength = (): number => ROD_X[1] - ROD_X[0]

/** Main-room footprint, walked counter-clockwise exactly as build_shell.py. */
export const outline = (): [number, number][] => [
  [WX, SY],
  [EX, SY],
  [EX, NY2],
  [JX, NY2],
  [JX, NY],
  [WX, NY],
]
