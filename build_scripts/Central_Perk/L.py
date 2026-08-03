"""Layout constants for Central Perk (metres).

Everything here is derived from ref_images/floor_plan.png at a fixed
scale of PPM pixels per metre, then rounded to sensible construction
values.  The plan's own pixel coordinates are kept in the X()/Y()
helpers so any measurement can be re-checked against the drawing.

Origin  : the inside face of the WEST wall  x  the inside face of the
          SOUTH wall of the main room.
Axes    : +X east (towards the street windows), +Y north (towards the
          bathrooms), +Z up.
Datum   : the main room's concrete floor is z = 0.  The window bay is a
          step up at z = STEP.

The plan reads as five spaces:

    main room      the big L-shaped room: counter along the west wall,
                   four seating zones stacked south -> north
    window bay     the raised, tiled storefront bay on the east side,
                   open to the main room across its whole length
    kitchen        carved out of the south-west corner, chamfered
    lobby + WCs    the block north of the main room
    street         the pavement outside, wrapping the north-east corner
"""
import math

# --------------------------------------------------------------- plan scale
PPM = 70.0          # floor-plan pixels per metre
PX0, PY0 = 320.0, 1235.0


def X(px):
    return round((px - PX0) / PPM, 3)


def Y(px):
    return round((PY0 - px) / PPM, 3)


# --------------------------------------------------------------- heights
CZ = 3.70           # main ceiling (underside of the slab)
BEAM_Z = (3.28, CZ)  # exposed beams / soffits; also where the columns stop
STEP = 0.155        # the window bay's raised platform
DADO = 1.06         # top of the panelled dado in the main room
DADO_CAP = 0.055    # thickness of the dado's capping rail
BASE_H = 0.145      # skirting
CORNICE = 0.16      # picture rail / cornice band under the ceiling

TW = 0.24           # exterior wall thickness
TP = 0.16           # partition thickness
TB = 0.34           # brick pier thickness

# --------------------------------------------------------- placement rules
# Coplanar faces are not a rendering quirk to be nudged away one at a time,
# they are the result of two parts being modelled as though they occupied the
# same plane.  These four constants are the discipline that stops it, and
# audit.zfight() is the test that says whether it held.
# Each floor slab gets its own thickness.  Where two slabs run under the same
# wall they overlap, and if they shared an underside those two downward faces
# would be coplanar - invisible, but the same modelling error as any other.
SLAB_Z = -0.12      # main room
SLAB_Z2 = -0.13     # boards
SLAB_Z3 = -0.14     # kitchen
SLAB_Z4 = -0.15     # bay
SLAB_Z5 = -0.16     # lobby
SLAB_OVER = 0.12    # how far a slab runs on under the wall that sits on it
FOUND_Z = -0.06     # walls start here, INSIDE the slab, never level with it
FOUND_Z2 = -0.07    # partitions - a touch deeper, so where one runs into an
                    # exterior wall the two undersides are still not coplanar
TRIM_BED = 0.004    # skirting and dado are bedded this far into the plaster,
                    # so their backs are never level with the wall face
PLANK_T = 0.014     # the boarded floor stands this proud of the slab
RUG_T = 0.012       # and a rug this proud of whatever it lies on

DOOR_H = 2.12       # standard door height
CASE_H = 2.24       # cased-opening head
STORE_SILL = 0.46   # storefront sill
STORE_HEAD = 2.52   # head of the main storefront glazing
TRAN_BOT = 2.62     # transom band
TRAN_TOP = 3.28
BULK = 3.28         # storefront bulkhead starts here

# --------------------------------------------------------------- main room
WX = 0.0                    # west wall, inner face
SY = 0.0                    # south wall, inner face
EX = X(838)                 # 7.400  east wall / bay edge, inner face
NY = Y(421)                 # 11.629 on the plan
# The plan gives the north wall at 11.63, which leaves only 1.58 m of east
# wall between the entrance diagonal and the corner.  The set photographs
# show that stretch about twice as deep - it carries the north street window
# and the whole coat-rack corner beside the doors - so the wall is pushed
# 1.58 m north and the lavatory block behind it goes with it.
NY = 13.21

# The way through to the lavatories: in the NORTH wall, hard against the west
# end of it, so it lands directly behind the counter.  The x range is not a
# guess - it is read off frontal.avif, where the lit doorway spans image x
# 275..360 of 1280, projected back through the A_frontal camera onto the wall
# plane.  The floor plan puts it in the middle of that wall; the photograph
# puts it at the end, and the photograph wins.
LOBBY_DR = (0.85, 1.79)
LOBBY_H = 2.24

# --------------------------------------------------------------- window bay
BAY_E = X(1035)             # 10.214 east (street) wall, inner face
BAY_E = 10.21
BAY_S = Y(1049)             # 2.657  south wall, inner face
BAY_S = 2.66
BAY_N = 10.05               # where the diagonal meets the bay edge line
BAY_DIAG_E = 7.24           # y where the diagonal meets the street wall

# the bay is open to the main room between these two y values; north of it
# is the brick pier that carries the corner, south of it the bay's own wall
BAY_OPEN = (BAY_S, 9.30)
PIER = (9.30, BAY_N)        # brick pier, x from EX to EX + TB
# Where the east wall picks up again north of the entrance.  It has to start
# ON the pier, not clear of it: started north of the diagonal's own thickness
# it left a 0.37 m slot of daylight between the pier and the wall, the full
# height of the room, which is exactly the gap in the brickwork by the
# entrance corner.  The two do now share plan area, so the wall is given its
# own top (see build_shell) rather than stopping level with the diagonal.
E_N_START = BAY_N - 0.02

# the entrance doors sit on the diagonal, with a shop window beside them
DIAG_A = (EX, BAY_N)
DIAG_B = (BAY_E, BAY_DIAG_E)
DIAG_L = math.hypot(DIAG_B[0] - DIAG_A[0], DIAG_B[1] - DIAG_A[1])   # 3.974
ENTRY_U = (0.74, 2.64)      # door opening, measured along the diagonal
ENTRY_H = 2.36
DIAG_WIN = (2.84, 3.70)

# street windows in the bay's east wall (y ranges, inner face x = BAY_E)
BAY_WIN = ((2.92, 4.32), (4.56, 5.96), (6.20, 7.04))
TRAN_U = (0.26, 4.38)       # the transom band, in u along that wall

# windows in the main room's own east (street) wall, north and south of the bay
E_WIN_S = (0.70, 1.63)
E_WIN_N = (11.06, 12.20)

# --------------------------------------------------------------- kitchen
KIT_E = X(528)              # 2.971
KIT_E = 2.97
KIT_N = Y(1017)             # 3.114
KIT_N = 3.11
KIT_CH = ((KIT_E, 1.93), (2.33, KIT_N))   # the chamfered corner
KIT_DR = (0.86, 1.83)       # doorway in the kitchen's north wall
KIT_WIN = (0.74, 2.07)      # window in the south wall

# --------------------------------------------------------------- lobby + WCs
# The doorway is at the west end of the north wall, so the hallway runs north
# from it and the two lavatories open off its east side.  The whole block
# moves with the door - a hallway that starts anywhere else would not line up
# with the opening you actually walk through.
WC_S = NY + TP              # 11.79 inner face of the hallway's south wall
WC_N = Y(170)               # 15.214
WC_N = 16.79
WC_E = X(738)               # 5.971 east wall of the whole block, inner face
WC_E = 5.97
# You come through the doorway into a hallway that runs east along the front
# of the block; both lavatories are then on your left, off its north side.
HALL_N = 14.68              # the hallway's north wall, inner (south) face
WC_Y = (HALL_N + TP, WC_N)  # the lavatories themselves
GENTS = (0.0, 2.90)
LADIES = (3.06, WC_E)
WC_DOORS = ((1.02, 1.84), (3.86, 4.68))     # x ranges through HALL_N
WC_WIN = ((0.60, 1.60), (2.90, 3.90), (4.40, 5.40))   # x ranges, north wall

# --------------------------------------------------------------- structure
# Cast-iron columns.  One line stands on the bay's platform edge carrying the
# beam over the opening; the cross beam at BEAM_Y runs the width of the room
# and lands on a fourth column at COL_X_IN.
COL_R = 0.105               # shaft radius
# Where the cross beam goes, and it is not over the alcove.  In frontal.jpeg
# the SERVICE arrow and the three opal schoolhouse pendants all hang off one
# dark timber that crosses the room well in FRONT of the painting wall and
# dies into the brick pier at the entrance corner - which is why the sign
# reads as floating in the room rather than as something screwed to the
# plaster.  Aligning the beam with the entrance puts it on the pier's own
# centre line and on the third bay column, so it is carried at both ends
# instead of stopping in mid air.
BEAM_Y = 9.55
BEAM_W = 0.26               # the beam's width in plan
BEAM_DROP = 0.42            # and how far its soffit hangs below the ceiling
# The cross beam passes UNDER the bay beam where the two meet, so their two
# soffits are never the same plane.  Which one is lower is a real decision -
# the bay beam is carried on the columns and the cross beam is applied
# across them - and not a nudge to stop the render flickering.
BEAM_X_Z = BEAM_Z[0] - 0.048
COL_X = EX + 0.15           # 7.55, just inside the platform kerb
COL_X_IN = 3.30
# The four cast-iron columns, as positioned in the scene.  Two of them were
# set by hand in Blender and are transcribed here exactly, so a rebuild
# reproduces them rather than reverting them:
#
#   * the bay beam's south column moved from y 4.30 to y 2.907836 - measured
#     off the object, not rounded, because the value IS the edit;
#   * the column that stood on the bay line at (7.55, 9.55) was deleted and
#     replaced by one at x 6.956275 on the same cross-beam line.  That takes
#     it off the platform and onto the main floor, which is why its base
#     starts at -0.02 rather than at STEP - 0.02, and it also clears the
#     entrance pier, whose plan (x 7.42..7.74 over y 9.30..10.03) the old one
#     was standing inside.
#
# Both z ranges fall out of L.ground() unchanged, so nothing else moves.
COLS = [(COL_X, 2.907836), (COL_X, 7.00),
        (COL_X_IN, BEAM_Y), (6.956275, BEAM_Y)]

# --------------------------------------------------------------- the counter
# The back bar: one continuous run against the west wall, tall cupboards at
# each end and the working counter with the machines between them.
BACK_D = 0.58
BACK_Y = (4.21, 12.63)
BACK_H = 0.94
BACK_TALL_S = (4.21, 5.18)
BACK_TALL_N = (11.37, 12.63)
BACK_TALL_H = 2.18

# The service counter: a faceted island whose customer face steps out in the
# middle, exactly as the plan draws it.  SERVE_FRONT is that face; the body
# runs back to SERVE_BACK.
SERVE_BACK = 1.38
SERVE_H = 1.06
SERVE_FRONT = [
    (2.00, 10.04),
    (2.00, 9.36),
    (2.50, 8.86),
    (2.50, 7.64),
    (2.07, 7.18),
    (2.07, 6.00),
]
# The bar stools.  A stool's feet splay 215 mm from its centre, so the
# clearance that matters is to the counter's FRONT FACE and not to its
# centre line - pulled up at 0.30 m the legs went straight through the
# panelling.  Each of these stands 0.44 m off the face it belongs to.
STOOLS = [(2.60, 9.42), (3.06, 8.44), (3.05, 7.60), (2.62, 6.55)]
STOOL_H = 0.74

# --------------------------------------------------------------- furniture
# Every anchor below was read straight off the floor plan against a one-metre
# grid, so the numbers are the drawing's, not a guess.  Rotations are degrees:
# a piece at rot = 0 faces +Y, and rot is measured counter-clockwise from that.


def face(x, y, tx, ty, jitter=0.0):
    """The rotation that turns a piece at (x, y) towards (tx, ty).

    rot = 0 faces +Y and is measured counter-clockwise, so this is the angle
    off +Y of the vector to the target."""
    return round(math.degrees(math.atan2(x - tx, ty - y)) + jitter, 1)


def seat(x, y, tgt, jitter=0.0):
    """A chair at (x, y), turned towards the table at `tgt` and then knocked
    `jitter` degrees off square.

    Chairs in a room are never dead square to the table and never at a
    random angle either - somebody got up and pushed one back, and that is
    all.  Writing the rotations out by hand is what produced the first pass,
    where several chairs faced the wall; deriving them from the table they
    belong to makes that impossible, and the jitter is a written-down
    constant rather than a roll so the room is the same every build."""
    return (x, y, face(x, y, tgt[0], tgt[1], jitter))


# -- the main seating group ------------------------------------------------
SOFA_C = (4.77, 5.82)                   # the orange couch, back to the north
SOFA_L, SOFA_D, SOFA_H = 2.24, 0.92, 0.96
COFFEE_C = (4.79, 4.65)
COFFEE_WD = (1.57, 0.88)
COFFEE_H = 0.44
RECLINER_C = (6.50, 4.63)               # the olive wing chair, facing west
RECLINER_ROT = 90.0
SIDE_T_C = (3.18, 4.79)                 # round pedestal table, two chairs
SIDE_T_R = 0.30
CHAIR_A = seat(2.83, 5.44, SIDE_T_C, -11.0)
CHAIR_B = seat(2.86, 4.24, SIDE_T_C, 8.0)
RUG_MAIN = (4.80, 4.71, 3.89, 2.63)     # cx, cy, w, d
RUG_OVAL = (1.57, 4.70, 1.86, 1.68)     # the open floor south of the counter

# -- the tables zone between the couch and the north alcove ----------------
RUG_MID = (5.04, 7.84, 3.29, 2.18)
TABLE_1 = (4.48, 7.91)
TABLE_2 = (6.02, 7.91)
TABLE_MID_R = 0.30
TZ_CHAIRS = [seat(4.44, 8.56, TABLE_1, 7.0), seat(4.06, 7.36, TABLE_1, -9.0),
             seat(5.14, 7.52, TABLE_1, 12.0), seat(6.48, 8.42, TABLE_2, -8.0),
             seat(6.00, 7.20, TABLE_2, 6.0)]

# The Statue of Liberty canvas.  It is square - the artwork is, and so is the
# stretcher in every set photograph - and it is a big one, hung low: its
# bottom edge all but lands on the dado cap.
#
# The position is measured, not judged.  In frontal.jpeg the printed red
# field runs from image x 473 to 587 and from y 104 to 220.  Two landmarks
# fix that photograph's scale on this wall - the two cast-iron columns at
# x = 3.30 and 7.55 read 535 px apart, which is 125.9 px/m at their depth and
# so 85.1 px/m at the wall - and the dado cap reads at row 233.  That puts the
# canvas at x 3.03..4.37, z 1.21..2.58: centred a metre WEST of where the
# first pass put it and a good deal lower, which is what makes it sit over the
# settee instead of floating in the middle of the wall.
PAINTING = (3.66, 2.05, 1.80)           # x, centre height, size on the N wall

# -- the north alcove ------------------------------------------------------
# The whole group hangs off the painting, not off the room's centre line:
# the canvas is well west of centre and the settee is directly under it in
# every set photograph, so moving the picture moves the furniture with it.
# The whole group moved west with the picture.  ALC_DX is the shift, applied
# once here rather than typed into eight numbers, so the settee stays under
# the canvas and the two club chairs stay symmetrical about it - which is how
# top_view.webp has them - instead of the settee sliding sideways into the
# left-hand chair, which is what happened when only the painting moved.
ALC_DX = -0.60
RUG_N = (4.85 + ALC_DX, 12.03, 3.50, 2.39)
# 12.74, not 12.83: at 12.83 the 0.80 m deep settee's back finished at 13.23,
# which is 20 mm INSIDE the wall it is supposed to be standing against - and
# through the dado, which stands 34 mm proud of it on top of that.
SETTEE_C = (PAINTING[0], 12.71)         # against the wall, under the painting
SETTEE_L = 1.60
ARMCH_L = (2.98, 11.69, -90.0)          # the two red club chairs, facing in
ARMCH_R = (5.50, 11.69, 90.0)
OVAL_T = (4.78 + ALC_DX, 11.73)
OVAL_T_WD = (1.18, 0.64)
# west of the settee, not under it: the settee runs 2.86..4.46 and the pouf
# was at 3.02, i.e. inside it
POUF = (2.34, 12.46)
ROUND_T_N = (6.42 + ALC_DX, 12.72)
PLANT_N = (6.98 + ALC_DX, 12.52)

# -- the south zone --------------------------------------------------------
RUG_S = (5.20, 1.73, 2.94, 3.04)
SOFA_S = (5.28, 0.50)                   # the orange sofa against the S wall
SOFA_S_L = 2.05
TABLE_S = (5.25, 1.57)
TABLE_S_WD = (1.57, 0.79)
TS_CHAIRS = [seat(4.66, 2.62, TABLE_S, 6.0), seat(3.86, 1.92, TABLE_S, -5.0),
             seat(6.46, 2.36, TABLE_S, 9.0), seat(3.62, 1.02, TABLE_S, -7.0)]
SIDE_T_S = (7.00, 0.50)
PLANT_S = (6.84, 1.42)

# -- the window bay --------------------------------------------------------
BAY_RUG = (8.90, 4.90, 2.61, 3.31)
# clear of the flower urn at BAY_URN: a rug laid under it would put its own
# underside on exactly the plane the urn's base stands on
# The apron in front of the doors.  It has to stay INSIDE the entrance
# diagonal (x + y < 17.45): laid out square and 2.44 m across, its north-east
# corner ran a metre out through the doorway, so its top face finished up
# level with the door lining's foot - 50 cm2 of coplanar pair, and a rug
# lying half in the street.
BAY_RUG_N = (8.24, 7.44, 1.60, 1.24)
# 9.58: at 9.69 the 0.80 m deep settee's back reached x = 10.09 and the bay
# curtains hang at 10.06..10.16, so the drapes ran through the upholstery
BAY_SOFA = (9.58, 5.16)                 # the damask settee, off the glass
BAY_SOFA_L = 2.07
# 8.78, not 8.95: the low table's east edge overlapped the damask settee's
# front by 100 mm once the settee came off the glass
BAY_LOW_T = (8.78, 5.31)
BAY_LOW_WD = (0.67, 1.19)
BAY_ROUND_T = (8.95, 4.01)
# Three chairs, not five.  The bay in top_view.webp and entrance.webp is a
# settee, two iron pedestal tables and a handful of black-and-gold damask
# chairs pulled up to them - packing the platform out with a chair per
# table-side turns a corner you can walk through into a waiting room.
BAY_CH = [seat(8.24, 6.26, BAY_LOW_T, -13.0),
          seat(8.10, 4.60, BAY_LOW_T, 10.0),
          seat(9.06, 3.16, BAY_ROUND_T, -7.0)]
# The urn stands clear of the glass: at x 9.72 the arrangement on top of it
# grew straight through the third bay window's curtain.
BAY_URN = (9.42, 6.92)                  # the tall urn of flowers by the door
BAY_PLANT = (9.68, 3.55)

# -- fittings --------------------------------------------------------------
# The three opal schoolhouse lamps hang off the cross beam, in a row, and so
# does the SERVICE arrow between them: everything overhead in this part of
# the room is carried by that one timber.
#
# The three x values are not evenly spaced, and that is deliberate.  A pendant
# hangs 3.66 m in front of the painting, so from the couch it covers a piece
# of wall 1.48 times further off than itself: anything between x 3.40 and 4.62
# lands ON the canvas, and one of them was sitting squarely over the torch.
# These three read as a row and leave the picture clear, with the widest bay
# in the middle because that is where the arrow hangs.
PENDANTS = [(2.36, BEAM_Y), (4.98, BEAM_Y), (6.62, BEAM_Y)]
PENDANT_Z = 2.34                            # centre of the opal globe
CHANDELIER = (8.52, 7.86)                   # the antler chandelier by the door
# The arrow hangs off the same timber, ABOVE the globes rather than among
# them: its plate stops 25 mm clear of the highest point of any shade, so the
# two fittings never occupy the same air.  Width and height are the reference
# frame's own - 148 px across at 125.9 px/m on the beam line.
SERVICE_SIGN = (4.32, BEAM_Y, 2.76)
SERVICE_WH = (1.30, 0.36)

# --------------------------------------------------------------- palette
GREEN_IRON = '17372B'       # the cast-iron columns and joinery
GREEN_DADO = '2A4A35'
OCHRE = 'B0763C'            # the plaster above the dado
TERRA = '9E4B27'
BRICK = '8C4B36'
CONCRETE = '7C8179'         # the main floor
CREAM = 'D9CFB6'
GOLD = 'C8912F'
COUCH_ORANGE = 'C4642A'


def diag_dir():
    dx = DIAG_B[0] - DIAG_A[0]
    dy = DIAG_B[1] - DIAG_A[1]
    l = math.hypot(dx, dy)
    return (dx / l, dy / l), l


def diag_pt(u, off=0.0):
    """A point u metres along the entrance diagonal, off metres into the bay."""
    (dx, dy), _ = diag_dir()
    nx, ny = dy, -dx                       # into the bay (south-west)
    return (DIAG_A[0] + dx * u + nx * off, DIAG_A[1] + dy * u + ny * off)


# The boarded service zone in front of the counter.  It is CUT OUT of the
# concrete slab rather than laid on top of it - two floor finishes butting on
# a line, which is what they do in the building and which leaves the two slabs
# sharing an edge instead of a plane.
PLANK_ZONE = (0.0, 3.62, 3.40, NY)      # x0, x1, y0, y1


def plank_poly():
    a, b, c, d = PLANK_ZONE
    return [(a, c), (b, c), (b, d), (a, d)]


def ground(x, y):
    """The height a piece of furniture stands at.  Only the bay differs: it
    is a step up, and everything on it has to know that."""
    if x >= EX - 0.02 and BAY_S <= y <= BAY_N:
        return STEP
    return 0.0


def kitchen_outer():
    """The kitchen block's outline as the MAIN ROOM sees it - the far faces of
    its three walls, mitred properly at the chamfer.  Skirting and dado follow
    this, so they land on the wall instead of hovering off it."""
    d = (KIT_CH[1][0] - KIT_CH[0][0], KIT_CH[1][1] - KIT_CH[0][1])
    l = math.hypot(*d)
    d = (d[0] / l, d[1] / l)
    n = (d[1], -d[0])                      # north-east, out of the kitchen
    a = (KIT_CH[0][0] + n[0] * TP, KIT_CH[0][1] + n[1] * TP)
    t1 = ((KIT_E + TP) - a[0]) / d[0]
    t2 = ((KIT_N + TP) - a[1]) / d[1]
    return [(KIT_E + TP, SY),
            (KIT_E + TP, a[1] + d[1] * t1),
            (a[0] + d[0] * t2, KIT_N + TP),
            (WX, KIT_N + TP)]


def main_room_poly():
    """The main room's finished floor area, on the inner faces of its walls,
    less the kitchen block and less the boarded zone."""
    a, b, c, d = PLANK_ZONE
    return [(KIT_E, SY), (EX, SY), (EX, NY), (b, NY), (b, c), (a, c),
            (WX, KIT_N), (KIT_CH[1][0], KIT_N), (KIT_CH[0][0], KIT_CH[0][1])]


def main_slab_poly():
    """The slab itself: the same outline, but running SLAB_OVER on under every
    wall that stands on it, and exactly on the line where it butts the boards.
    Offsetting the whole outline instead - which is what a plain poly_offset
    does - pushes the butt joint into the boards and puts the two floors'
    top faces on the same plane."""
    o = SLAB_OVER
    a, b, c, d = PLANK_ZONE
    return [(KIT_E - o, SY - o), (EX + o, SY - o), (EX + o, NY + o),
            (b, NY + o), (b, c), (a - o, c),
            (a - o, KIT_N - o), (KIT_CH[1][0] - o, KIT_N - o),
            (KIT_E - o, KIT_CH[0][1] - o)]


def bay_poly():
    return [(EX, BAY_S), (BAY_E, BAY_S), (BAY_E, BAY_DIAG_E), (EX, BAY_N)]


def kitchen_poly():
    return [(WX, SY), (KIT_E, SY), (KIT_CH[0][0], KIT_CH[0][1]),
            (KIT_CH[1][0], KIT_N), (WX, KIT_N)]
