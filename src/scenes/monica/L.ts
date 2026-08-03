/** Layout constants for Monica's apartment (metres).
 * Origin: the inside face of the west (front-door) wall x the old datum line.
 * +X = east (towards the bedrooms), +Y = north (towards the big window), +Z = up.
 * The 'back wall' (marked NOT SHOWN on the plan) sits at Y = SY.
 *
 * 1:1 port of build_scripts/L.py.
 */

export const CZ = 3.26 // main ceiling
export const RAIL = 2.73 // picture-rail height: lavender below, cream above
export const BASE_H = 0.155 // baseboard
export const TW = 0.26 // exterior wall thickness
export const TP = 0.16 // partition thickness

export const EX = 8.55 // central wall, west face
export const EXW = 8.77 // central wall, east face
export const EXT_E = 11.8 // east exterior wall, inner face
export const NYW = 6.15 // north exterior wall, inner face
export const NY = 4.62 // kitchen north wall / bathroom south wall
export const NW_Y = 7.05 // north wall of the bathroom / hallway block

// --- central wall, laid out north to south -------------------------------
export const MD_WALL_W = 1.1
export const MD_W = 0.95
export const AL_S = 5.62 // south line of the window bay
export const MD_WALL: [number, number] = [AL_S - MD_WALL_W, AL_S]
export const MD_Y: [number, number] = [MD_WALL[0] - MD_W, MD_WALL[0]]
export const CD_Y: [number, number] = [-1.48, -0.53]
export const SY = -3.68 // south ('back') wall, 9.83 m deep
export const TV_WALL: [number, number] = [CD_Y[1], MD_Y[0]]

// --- west wall -------------------------------------------------------------
export const WX = 0.0
export const W_PLASTER: [number, number] = [SY, 0.66] // y range of the lavender front-door wall
export const FD_Y: [number, number] = [-0.55, 0.47] // front door rough opening (1.02 wide)
export const FD_H = 2.06
export const FD_TOP = 2.52
export const W_BRICK: [number, number] = [0.66, 3.62] // y range of brick west wall

// --- kitchen run along the west wall --------------------------------------
export const KIT_PEN: [number, number] = [0.66, 1.26] // free-standing turquoise open unit
export const KIT_STOVE: [number, number] = [1.26, 2.08] // pro range
export const KIT_CTR: [number, number] = [2.08, 3.62] // counter + base cabinets
export const KIT_SHELF: [number, number] = [1.38, 3.62] // big turquoise open shelf unit above
export const KIT_WEDGE: [number, number] = [0.7, 1.34] // shallow bottle shelf over the peninsula
export const CTR_H = 0.915
export const CTR_D = 0.655
export const TOE = 0.095

// --- chamfer (kitchen window over the sink) --------------------------------
export const CH_A: [number, number] = [0.0, 3.62]
export const CH_B: [number, number] = [1.02, 4.62]
export const KW_U: [number, number] = [0.245, 1.195]
export const KW_Z: [number, number] = [0.99, 2.34]

// --- north wall ------------------------------------------------------------
export const N_BRICK: [number, number] = [1.02, 3.24]
export const FRIDGE_X: [number, number] = [2.36, 3.1]

// --- hallway to the bathroom / closet --------------------------------------
export const HALL_X: [number, number] = [3.4, 4.44]
export const HALL_WW: [number, number] = [3.24, 3.4]
export const HALL_EW: [number, number] = [4.44, 4.62]
export const HALL_Y0 = 3.98
export const BD_Y: [number, number] = [4.82, 5.62]
export const BD_H = 2.06
export const CL_X: [number, number] = [3.52, 4.36]
export const CL_H = 2.06

// --- exposed timber: one dropped beam dividing kitchen from living room ----
export const BEAM_X: [number, number] = [3.44, 3.68] // runs north-south, clear of the hall wall
export const BEAM_Z: [number, number] = [2.54, 2.94]
export const BEAM_Y: [number, number] = [SY, 4.05]
export const POST_X: [number, number] = [3.46, 3.66]

// --- window alcove ---------------------------------------------------------
export const AL_X: [number, number] = [HALL_X[1], EX] // runs from the hall to the central wall
export const AL_Y: [number, number] = [AL_S, NYW]
export const AL_Z = 2.86
export const BW_X: [number, number] = [4.9, 7.98]
export const BW_SILL = 0.6
export const BW_HEAD = AL_Z
export const BW_TOP = BW_HEAD
export const BW_TILT = (6.0 * Math.PI) / 180
export const BW_LEAN = (BW_HEAD - BW_SILL) * Math.tan(BW_TILT)
export const SEAT_H = 0.46
export const SEAT_D = 0.62

// --- doors through the central wall ---------------------------------------
export const AXIS = (SY + NYW) * 0.5
export const CD_H = 2.06
export const CD_TOP = 2.52
export const MD_H = 2.06
export const MD_TOP = 2.52

// --- bathroom --------------------------------------------------------------
export const BA_X: [number, number] = [1.02, 3.24]
export const BA_Y: [number, number] = [4.78, NW_Y]

// --- bedrooms (east block, split by a wall as on the plan) -----------------
export const BED_X: [number, number] = [EXW, EXT_E]
export const BED_DIV: [number, number] = [AXIS - TP / 2, AXIS + TP / 2] // centred: both rooms 3.72 m deep
export const RB_Y: [number, number] = [SY, BED_DIV[0]] // Rachel's bedroom (south)
export const MB_Y: [number, number] = [BED_DIV[1], 6.15] // Monica's bedroom (north)
export const RB_WIN_Y = (RB_Y[0] + RB_Y[1]) * 0.5 // centre of the window behind each bed
export const MB_WIN_Y = (MB_Y[0] + MB_Y[1]) * 0.5
export const BED_W = 1.42 // bed width (along Y)
export const BED_L = 2.0 // bed length (along X), head against the east wall

// --- furniture anchors -----------------------------------------------------
export const RUG_W = 2.98
export const RUG_D0 = 4.2
export const SOFA_L0 = 2.32
export const GROW = SOFA_L0 / 3
export const SIT_N = 3.56
export const SOFA_L = SOFA_L0 + GROW
export const COFFEE_D = 1.2 + GROW
export const RUG_WH: [number, number] = [RUG_W, RUG_D0 + GROW]
export const SIT_C = SIT_N - RUG_WH[1] * 0.5
export const SOFA_C: [number, number] = [4.42, SIT_C]
export const COFFEE_C: [number, number] = [5.72, SIT_C]
export const RUG_C: [number, number] = [5.82, SIT_C]
export const TV_C: [number, number] = [8.3, (TV_WALL[0] + TV_WALL[1]) * 0.5]
export const CRED_HW = (TV_WALL[1] - TV_WALL[0]) * 0.5 - 0.72
export const TV_SET_Y = TV_C[1] - 0.26
export const TABLE_C: [number, number] = [2.48, 1.75]
export const CHAIR_ARM_WIN: [number, number] = [5.72, SIT_N + 0.06 - 0.504]
export const CHAIR_SLIPPER: [number, number] = [7.95, CD_Y[0] - 0.75]
export const SLIPPER_ROT = 133.0
export const GLASS_T: [number, number] = [SOFA_C[0], SOFA_C[1] - SOFA_L / 2 - 0.095 - 0.302]
export const STOOLS: [number, number] = [5.98, SIT_C - 1.37]
export const CHANDELIER: [number, number] = [5.86, SIT_C]

// palette ------------------------------------------------------------------
export const LAV = '9E98C4'
export const LAV_TRIM = 'A7A1CB'
export const CREAM = 'DDD2AA'
export const DOOR_PURPLE = '9089CE'
export const TURQ = '35A8B6'
export const GREEN_DADO = '1D6244'
export const GREEN_DOOR = '2D7550'
export const GOLD = 'E3AC33'

export function chamferDir(): { dir: [number, number]; len: number } {
  const dx = CH_B[0] - CH_A[0]
  const dy = CH_B[1] - CH_A[1]
  const l = Math.hypot(dx, dy)
  return { dir: [dx / l, dy / l], len: l }
}

export function chamferPt(u: number, off = 0.0): [number, number] {
  const { dir } = chamferDir()
  const [dx, dy] = dir
  const nx = dy,
    ny = -dx // into the room (south-east)
  return [CH_A[0] + dx * u + nx * off, CH_A[1] + dy * u + ny * off]
}

export function slipperFront(d = 0.78): [number, number] {
  const a = (SLIPPER_ROT * Math.PI) / 180
  return [CHAIR_SLIPPER[0] + Math.cos(a) * d, CHAIR_SLIPPER[1] + Math.sin(a) * d]
}
