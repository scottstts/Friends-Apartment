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

EX = 8.55          # central wall, west face
EXW = 8.77         # central wall, east face
EXT_E = 11.80      # east exterior wall, inner face
NYW = 6.15         # north exterior wall, inner face
NY = 4.62          # kitchen's north wall / bathroom's south wall - NOT the bay

# The bathroom and the hallway sit in the flat's north-west corner, and that is
# an OUTSIDE corner of the building - so this block pushes north past the flat's
# own north wall rather than eating into the kitchen.  It buys two things at
# once: a bathroom with a real footprint instead of a cupboard with a bath in
# it, and enough hallway to walk down before you reach the green closet door.
NW_Y = 7.05        # north wall of the bathroom / hallway block

# --- the central wall, laid out north to south -----------------------------
# living_room.jpeg reads this wall as one sequence, so it is built as one: the
# alcove, a stand of wall carrying a sconce over a console, Monica's door, the
# long stretch with the Jouets poster and the credenza, Rachel's cased opening,
# then the stretch carrying the pair of framed prints.
#
# Sizing the parts and deriving the fourth wall from them - rather than fixing
# the fourth wall and squeezing the parts in behind it - is the only way these
# proportions come out right.  Both previous attempts fixed SY first and the
# error landed on whichever stretch was left over: the credenza bay ended up
# 1.61 m against the photo's roughly twice that, which is what made the whole
# east side feel cramped no matter what was moved around on it.
MD_WALL_W = 1.10               # sconce over console, alcove to Monica's door
MD_W = 0.95                    # Monica's door - same width as Rachel's opening

# AL_S is the window bay's south line - where the drape rod and the header sit.
# It is NOT the same as NY: NY is the kitchen's north wall and the bathroom's
# south wall, and must stay at 4.62.
#
# The bay used to be 1.53 m deep because the upper glazing raked 0.71 m into the
# room, which held the drapes 1.42 m off the glass and made everything between
# them dead space behind a curtain.  The glass is one near-vertical plane now,
# so the bay only needs to clear the drape's own fold depth.
AL_S = 5.62
MD_WALL = (AL_S - MD_WALL_W, AL_S)
MD_Y = (MD_WALL[0] - MD_W, MD_WALL[0])

# Everything south of Monica's door is pinned at the value it already had, so
# shortening the bay moves her door and the wall vignette north and NOTHING
# else: the credenza, Rachel's opening, the print wall and the fourth wall all
# stay exactly where they are.  These were derived off MD_Y and would otherwise
# have walked north with it.
CD_Y = (-1.48, -0.53)          # Rachel's cased opening
SY = -3.68                     # south ('back') wall, 9.83 m deep
# The credenza wall is simply what is left between the two bedroom openings -
# 4.10 m now that Monica's door has moved up to the window.
TV_WALL = (CD_Y[1], MD_Y[0])

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
# Starts at the hallway's east face, not 180 mm east of it: the wall that used
# to fill that gap is gone, so the bay simply runs on to the hallway.
AL_X = (HALL_X[1], EX)         # runs right up to the central wall
AL_Y = (AL_S, NYW)
AL_Z = 2.86
BW_X = (4.90, 7.98)
BW_SILL = 0.60
BW_HEAD = AL_Z                 # one window, sill to head - no separate rake
BW_TOP = BW_HEAD               # kept: older call sites still name it
BW_TILT = math.radians(6.0)    # "slanted just a tiny degree" - top leans in
# how far the head leans south of the sill plane
BW_LEAN = (BW_HEAD - BW_SILL) * math.tan(BW_TILT)      # 0.233
SEAT_H = 0.46
SEAT_D = 0.62

# --- doors through the central wall ---------------------------------------
# The openings themselves are sized at the top of this file, where the wall is
# laid out as a sequence.  AXIS is the flat's north-south centre line: the wall
# splitting the two bedrooms sits on it and the sofa faces straight down it.
# The credenza does *not* - it centres in its own bay (TV_WALL), which is what
# the photo shows and is no longer the same line.
AXIS = (SY + NYW) * 0.5        # 1.235
CD_H = 2.06
CD_TOP = 2.52
MD_H = 2.06
MD_TOP = 2.52                  # frosted transom over it, as over Rachel's

# --- bathroom --------------------------------------------------------------
BA_X = (1.02, 3.24)
BA_Y = (4.78, NW_Y)            # 2.22 x 2.27, was 2.22 x 1.25

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
RUG_W, RUG_D0, SOFA_L0 = 2.98, 4.20, 2.32       # sizes before the widening
GROW = SOFA_L0 / 3.0                            # 0.773

# SIT_N is the seating group's NORTH line - the rug's far edge, up towards the
# window.  It is the fixed datum here, so the widening below lands entirely on
# the fourth-wall side and nothing creeps back towards the window.
#
# The group used to be derived to hold that edge 0.27 m clear of Monica's door,
# so walking out of her room missed the rug.  That no longer holds: half a
# sofa-width north puts the edge at 3.56, inside her doorway's band
# (2.67..3.52), and the armchair with it.  The two cannot both be true - any
# move north beyond 0.27 crosses that line - and the window reading wins.
# Pinned, for the same reason TV_WALL and SY are: it used to hang off Monica's
# door, and moving her door north to the window would have dragged the whole
# seating group with it.
SIT_N = 3.56
SOFA_L = SOFA_L0 + GROW                         # 3.093
COFFEE_D = 1.20 + GROW                          # 1.973, the table's Y extent
RUG_WH = (RUG_W, RUG_D0 + GROW)                 # 2.98 x 4.973
# Rug, sofa and table were all centred on one line and all grow by the same
# amount, so one shared centre keeps all three north edges exactly where they
# were and pushes only their south ends out.
SIT_C = SIT_N - RUG_WH[1] * 0.5
SOFA_C = (4.42, SIT_C)         # cream sofa centre, faces +X
COFFEE_C = (5.72, SIT_C)
RUG_C = (5.82, SIT_C)
TV_C = (8.30, (TV_WALL[0] + TV_WALL[1]) * 0.5)   # centred in its own bay
# The sideboard runs the wall between the two bedroom openings, as in
# living_room.jpeg where it dominates that stretch rather than sitting as an
# island in it.  0.55 m is left clear at each end for the fern and the plant.
CRED_HW = (TV_WALL[1] - TV_WALL[0]) * 0.5 - 0.72      # 1.33, so 2.66 m long
# The set is not centred on the sideboard - it stands towards the south end,
# leaving the longer stretch for the vase, the bronze figures and the fern.  The
# poster and the crest hang on THIS line, not on the sideboard's centre.
TV_SET_Y = TV_C[1] - 0.26
TABLE_C = (2.48, 1.75)         # one chair-width south, 0.75 of one east
# The check-pillowed armchair belongs ON the rug, at its north-west corner just
# beyond the coffee table - not out on the boards north of Monica's door, where
# it stood square in the route from her room across to the bathroom hallway.
# That route is the reason the seating group is pushed south at all.
# Squared up on the coffee table's centre line, not nudged off it: at 5.48 its
# arm cleared the sofa's by 40 mm, which reads as the two pieces touching.
# Keyed to the rug's north edge, not to the group's centre: the chair is not one
# of the pieces being widened, and its back is meant to overhang that edge by
# about 60 mm.  0.504 is its own half-depth.
CHAIR_ARM_WIN = (5.72, SIT_N + 0.060 - 0.504)
# The slipper chair sits south of Rachel's opening, turned across the rug's
# corner, with its footstool in front (which follows via slipper_front).  Keyed
# off that opening rather than given a fixed y: twice now a resize has slid it
# back across her doorway because it was a literal.
CHAIR_SLIPPER = (7.95, CD_Y[0] - 0.75)
SLIPPER_ROT = 133.0
# Off the sofa's south end and squared up with it: the table's 604 mm footprint
# sits centred inside the sofa's depth band, with a 95 mm gap to the arm.  Both
# of these are derived off the sofa now, for the same reason as the chair.
GLASS_T = (SOFA_C[0], SOFA_C[1] - SOFA_L / 2 - 0.095 - 0.302)
STOOLS = (5.98, SIT_C - 1.37)  # the pair of stacked tapestry stools
CHANDELIER = (5.86, SIT_C)     # over the living room, i.e. over the seating

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
