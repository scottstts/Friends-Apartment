"""Layout constants for Monica's apartment (metres).
Origin: the inside face of the west (front-door) wall x the old datum line.
+X = east (towards the bedrooms), +Y = north (towards the big window), +Z = up.
The 'back wall' (marked NOT SHOWN on the plan) sits at Y = SY.
"""
import math

CZ = 3.26          # main ceiling
RAIL = 2.73        # picture-rail height: lavender below, cream above
BASE_H = 0.155     # baseboard
TW = 0.26          # exterior wall thickness
TP = 0.16          # partition thickness

SY = -1.45         # south ('back') wall inner face
EX = 8.55          # central wall, west face
EXW = 8.77         # central wall, east face
EXT_E = 11.80      # east exterior wall, inner face
NYW = 6.15         # north exterior wall, inner face

# --- west wall -------------------------------------------------------------
WX = 0.0
W_PLASTER = (SY, 0.66)         # y range of the lavender front-door wall
FD_Y = (-0.55, 0.47)           # front door rough opening (1.02 wide)
FD_H = 2.06
FD_TOP = 2.52
W_BRICK = (0.66, 3.62)         # y range of brick west wall

# --- kitchen run along the west wall --------------------------------------
KIT_PEN = (0.66, 1.26)         # free-standing turquoise open unit
KIT_STOVE = (1.26, 2.08)       # pro range
KIT_CTR = (2.08, 3.62)         # counter + base cabinets
KIT_SHELF = (1.38, 3.62)       # big turquoise open shelf unit above
KIT_WEDGE = (0.70, 1.34)       # shallow bottle shelf over the peninsula
CTR_H = 0.915
CTR_D = 0.655
TOE = 0.095

# --- chamfer (kitchen window over the sink) --------------------------------
CH_A = (0.00, 3.62)
CH_B = (1.02, 4.62)
KW_U = (0.245, 1.195)
KW_Z = (0.99, 2.34)

# --- north wall ------------------------------------------------------------
NY = 4.62
N_BRICK = (1.02, 3.24)
FRIDGE_X = (2.36, 3.10)

# --- hallway to the bathroom / closet --------------------------------------
HALL_X = (3.40, 4.44)
HALL_WW = (3.24, 3.40)
HALL_EW = (4.44, 4.62)
HALL_Y0 = 3.98
BD_Y = (4.82, 5.62)
BD_H = 2.06
CL_X = (3.52, 4.36)
CL_H = 2.06

# --- exposed timber: one dropped beam dividing kitchen from living room ----
BEAM_X = (3.44, 3.68)          # runs north-south, clear of the hall wall
BEAM_Z = (2.54, 2.94)
BEAM_Y = (SY, 4.05)
POST_X = (3.46, 3.66)

# --- window alcove ---------------------------------------------------------
AL_X = (4.62, EX)              # runs right up to the central wall
AL_Y = (4.62, NYW)
AL_Z = 2.86
BW_X = (4.90, 7.98)
BW_SILL = 0.60
BW_TOP = 1.92
RAKE_Y = 5.40
SEAT_H = 0.46
SEAT_D = 0.62

# --- doors through the central wall ---------------------------------------
# AXIS is the flat's north-south centre line: the wall that splits the two
# bedrooms sits on it, the TV/credenza is centred on it from the living-room
# side, and the sofa faces straight down it.
AXIS = (SY + 6.15) * 0.5       # 2.35
CD_Y = (0.32, 1.24)            # cased opening -> Rachel's bedroom
CD_H = 2.06
CD_TOP = 2.52
MD_Y = (5.14, 5.96)            # door -> Monica's bedroom (from the alcove)
MD_H = 2.06

# --- bathroom --------------------------------------------------------------
BA_X = (1.02, 3.24)
BA_Y = (4.78, 6.03)

# --- bedrooms (east block, split by a wall as on the plan) -----------------
BED_X = (EXW, EXT_E)
BED_DIV = (AXIS - TP / 2, AXIS + TP / 2)   # centred: both rooms 3.72 m deep
RB_Y = (SY, BED_DIV[0])        # Rachel's bedroom (south)
MB_Y = (BED_DIV[1], 6.15)      # Monica's bedroom (north)
RB_WIN_Y = (RB_Y[0] + RB_Y[1]) * 0.5   # centre of the window behind each bed
MB_WIN_Y = (MB_Y[0] + MB_Y[1]) * 0.5
BED_W = 1.42                   # bed width (along Y)
BED_L = 2.00                   # bed length (along X), head against the east wall

# --- furniture anchors -----------------------------------------------------
# everything in the seating group is hung off AXIS so the sofa, the coffee
# table, the rug, the chandelier and the TV all share one centre line.
SOFA_C = (4.42, AXIS)          # cream sofa centre, faces +X
COFFEE_C = (5.72, AXIS)
RUG_C = (5.82, AXIS)
RUG_WH = (2.98, 4.20)
TV_C = (8.30, AXIS)
CRED_HW = 0.70                 # half-length of the waterfall credenza
TABLE_C = (2.14, 2.20)         # round kitchen table
CHAIR_ARM_WIN = (5.60, 4.14)   # armchair below the alcove
# The slipper chair sits at the rug's south-east corner, turned across it, with
# its footstool in front.  Pushed down towards the corner of the two walls: at
# y = 0.10 the chair reached y = 0.545 and the footstool y = 0.94, both of them
# standing inside Rachel's doorway band (CD_Y = 0.32 to 1.24) and blocking the
# way out of her room.  The footstool follows via slipper_front().
CHAIR_SLIPPER = (7.95, -0.58)
SLIPPER_ROT = 133.0
# Off the sofa's south end and squared up with it: the table's 604 mm footprint
# sits centred inside the sofa's 3.94-4.90 depth band, with a 95 mm gap to the
# arm.  Set diagonally off the corner it read as a table adrift in the room.
GLASS_T = (4.42, 0.76)         # wrought-iron glass table off the sofa's south arm
STOOLS = (5.98, 0.98)          # the pair of stacked tapestry stools
CHANDELIER = (5.86, AXIS)      # over the living room

# palette ------------------------------------------------------------------
LAV = '9E98C4'
LAV_TRIM = 'A7A1CB'
CREAM = 'DDD2AA'
DOOR_PURPLE = '9089CE'
TURQ = '35A8B6'
GREEN_DADO = '1D6244'
GREEN_DOOR = '2D7550'
GOLD = 'E3AC33'


def chamfer_dir():
    dx = CH_B[0] - CH_A[0]
    dy = CH_B[1] - CH_A[1]
    l = math.hypot(dx, dy)
    return (dx / l, dy / l), l


def chamfer_pt(u, off=0.0):
    (dx, dy), l = chamfer_dir()
    nx, ny = dy, -dx          # into the room (south-east)
    return (CH_A[0] + dx * u + nx * off, CH_A[1] + dy * u + ny * off)


def slipper_front(d=0.78):
    """Point in front of the slipper chair, where its footstool belongs."""
    a = math.radians(SLIPPER_ROT)
    return (CHAIR_SLIPPER[0] + math.cos(a) * d, CHAIR_SLIPPER[1] + math.sin(a) * d)
