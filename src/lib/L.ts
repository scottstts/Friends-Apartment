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

export const SY = -1.45 // south ('back') wall inner face
export const EX = 8.55 // central wall, west face
export const EXW = 8.77 // central wall, east face
export const EXT_E = 11.8 // east exterior wall, inner face
export const NYW = 6.15 // north exterior wall, inner face

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
export const NY = 4.62
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
export const AL_X: [number, number] = [4.62, EX] // runs right up to the central wall
export const AL_Y: [number, number] = [4.62, NYW]
export const AL_Z = 2.86
export const BW_X: [number, number] = [4.9, 7.98]
export const BW_SILL = 0.6
export const BW_TOP = 1.92
export const RAKE_Y = 5.4
export const SEAT_H = 0.46
export const SEAT_D = 0.62

// --- doors through the central wall ---------------------------------------
// AXIS is the flat's north-south centre line: the wall that splits the two
// bedrooms sits on it, the TV/credenza is centred on it from the living-room
// side, and the sofa faces straight down it.
export const AXIS = (SY + 6.15) * 0.5 // 2.35
export const CD_Y: [number, number] = [0.32, 1.24] // cased opening -> Rachel's bedroom
export const CD_H = 2.06
export const CD_TOP = 2.52
export const MD_Y: [number, number] = [5.14, 5.96] // door -> Monica's bedroom (from the alcove)
export const MD_H = 2.06

// --- bathroom --------------------------------------------------------------
export const BA_X: [number, number] = [1.02, 3.24]
export const BA_Y: [number, number] = [4.78, 6.03]

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
// everything in the seating group is hung off AXIS so the sofa, the coffee
// table, the rug, the chandelier and the TV all share one centre line.
export const SOFA_C: [number, number] = [4.42, AXIS] // cream sofa centre, faces +X
export const COFFEE_C: [number, number] = [5.72, AXIS]
export const RUG_C: [number, number] = [5.82, AXIS]
export const RUG_WH: [number, number] = [2.98, 4.2]
export const TV_C: [number, number] = [8.3, AXIS]
export const CRED_HW = 0.7 // half-length of the waterfall credenza
export const TABLE_C: [number, number] = [2.14, 2.2] // round kitchen table
export const CHAIR_ARM_WIN: [number, number] = [5.6, 4.14] // armchair below the alcove
// The slipper chair sits at the rug's south-east corner, turned across it, with
// its footstool in front.
export const CHAIR_SLIPPER: [number, number] = [7.95, -0.58]
export const SLIPPER_ROT = 133.0
// Off the sofa's south end and squared up with it.
export const GLASS_T: [number, number] = [4.42, 0.76] // wrought-iron glass table off the sofa's south arm
export const STOOLS: [number, number] = [5.98, 0.98] // the pair of stacked tapestry stools
export const CHANDELIER: [number, number] = [5.86, AXIS] // over the living room

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
