"""Layout constants for Chandler & Joey's apartment (Apt 19), in metres.

Origin: the inside face of the west wall x the inside face of the south
("fourth") wall, at floor level.  +X = east (towards the kitchen and the front
door), +Y = north (towards the windows and the yellow couch), +Z = up.

The plan the reference floor plan describes, and which every set photograph
agrees with once the perspective is accounted for, is a wide room with a STEP
in its north wall: the couch/window wall runs at NY, and at x = JX the wall
jogs 1.20 m south to NY2, where the kitchen sits in a shallow alcove.

That step is not decoration.  In kitchen.jpg the range reads about 1.6x larger
per metre than the couch does, which is only possible if the kitchen run stands
appreciably nearer the camera than the window wall.  Built flush - the obvious
reading of the photographs - the range lands three metres too far away and the
whole east side collapses.
"""
import math

# ---------------------------------------------------------------- shell
CZ = 3.15           # ceiling
BASE_H = 0.175      # baseboard height
BASE_T = 0.022      # baseboard projection
RAIL_Z = 2.66
TW = 0.30           # exterior wall thickness
TP = 0.16           # partition thickness

WX = 0.00           # west wall, inner face
EX = 8.47           # east wall, inner face
# The kitchen counter has to fill the alcove wall EXACTLY and turn the corner
# where the WALL turns - the peninsula's west face lands on the jog wall's own
# line at x = JX, and the fridge dies into the east wall.  The counter sizes
# are fixed by what they hold, so it is the wall that gives: 3.47 m of run
# (720 peninsula + 800 sink + 1100 range + 850 fridge) sets EX at JX + 3.47.
# The first pass left 580 mm of bare wall in the middle of the kitchen, which
# is what made the corner read as missing.
SY = -1.30          # south ("fourth") wall, inner face
# The pier between the two bedroom doors - the one the entertainment unit
# stands against - was 2.45 m, which is not enough wall for the unit the room
# actually has.  Widened to 3.68 (1.5x) by moving JOEY'S DOOR south rather than
# Chandler's, which means the fourth wall has to move south with it to keep a
# pier below the door.  Everything centred on that stretch of wall - the unit,
# the picture over it, the rug, both chairs and the little glass table - moves
# with the new centre at y = 2.61.
NY = 7.30           # north wall, inner face - the couch/window wall
JX = 5.00           # the jog: N-S wall facing east, from NY2 up to NY
NY2 = 4.90          # kitchen wall, inner face - 2.40 m SOUTH of the couch wall

# JOG = NY - NY2 = 2.40 m.  The floor plan draws 1.20, which is far too little:
# at that depth the jog reads as a sliver from every angle and its panel
# moulding is squeezed to a sixth of its neighbours' width.  3.00 overshot the
# other way.  2.40 also settles a second measurement that is easier to check
# than the jog itself - the pier between the front door and the kitchen corner,
# the one carrying the wall telephone in living_room.webp.  That pier is what
# is left of the east wall north of the door, so it moves one-for-one with
# NY2: shortening the jog by 600 mm lengthens it from 1.17 to 1.77, which is
# the 1.5x the photograph asks for.  One number, two corrections.

# ---------------------------------------------------------------- north wall
# west -> east: corner, window, sconce pier, window, a real stretch of wall,
# the bathroom door, then the jog.
#
# That stretch between the second window and the door used to be 340 mm, which
# read as the door being jammed into the curtain.  The set photographs show a
# proper piece of wall there - somewhere to lean the hockey sticks - and the
# only way to get one is for the room to be wider, which is why EX and NY both
# grew by roughly a door's width over the first pass.
WIN_W = 0.77
WIN_SILL = 0.62
WIN_HEAD = 2.42
WIN_A = (0.52, 0.52 + WIN_W)          # 0.52 .. 1.29
WIN_B = (1.87, 1.87 + WIN_W)          # 1.87 .. 2.64
SCONCE_X = (WIN_A[1] + WIN_B[0]) * 0.5
SCONCE_Z = 1.82

BD_X = (3.58, 4.50)     # bathroom door, 0.92 wide - 940 mm clear of window B
BD_H = 2.12
DOOR_TOP = 2.12

ROD_X = (0.28, 2.90)    # one curtain rod across both windows
ROD_Z = 2.63

# ---------------------------------------------------------------- kitchen run
CTR_H = 0.92
CTR_D = 0.655
TOE_H = 0.095
TOE_IN = 0.075

# The kitchen is an L.  A PENINSULA runs north-south out into the room and is
# joined at its north end by a short counter that continues east along the
# alcove wall to the range and then the fridge.  Read as a straight run with a
# free-standing island - which is what both photographs look like at first -
# the kitchen loses its corner, the barstools end up facing the wrong way, and
# the floor between the recliners and the counter doubles in area.
PEN_X = (JX, JX + 0.72)        # peninsula, turning on the wall's corner
PEN_Y = (3.10, NY2)            # ... 1.80 long, running back to the alcove wall
K_SINK = (PEN_X[1], PEN_X[1] + 0.80)
K_STOVE = (K_SINK[1], K_SINK[1] + 1.10)      # the vintage range
K_FRIDGE = (K_STOVE[1], EX)                  # retro fridge, 850
K_FRIDGE_H = 1.84

UPPER_Z = (1.44, 2.30)
UPPER_D = 0.345
# The wall cabinet starts AT THE WALL'S TURNING POINT and runs east: in
# kitchen.jpg its left stile lands on the corner itself, with three WIDE doors
# filling the return.  Started 360 mm east of the corner, as it was, it left a
# bare strip of plaster beside it with nothing to explain it.
# The turning point is JX, not JX+TW: the jog wall's south end cap is in the
# same plane as the kitchen back wall, so the wall face at NY2 runs unbroken
# from x = JX all the way east.
K_UPPER = (JX, 6.86)           # three cabinet doors, 618 each
K_MW = (6.86, 7.56)            # over-the-range microwave, and a cupboard over it
K_MW_Z = (1.44, 1.78)
# The open junk-food shelf has to clear the top of the fridge, which is why it
# starts 300 mm higher than the door cabinets rather than running level with
# them: in both set photographs the fridge stands INTO the shelf run, its top
# roughly level with the lower tier.
K_SHELF = (7.56, 8.42)
K_SHELF_Z = (1.90, 2.46)
SPLASH_X = (K_UPPER[0], 7.62)
SPLASH_Z = (CTR_H - 0.008, UPPER_Z[0])

# ---------------------------------------------------------------- east wall
# The front door is NOT tucked into the kitchen corner: living_room.webp puts
# a clear stretch of wall - the one carrying the wall telephone - between the
# fridge and the door casing, and a much longer stretch south of it.  Sitting
# at about three fifths of the way up the wall is what the photographs show.
FD_Y = (2.03, 3.13)            # 1.10 wide, centred at 60% of the wall
FD_H = 2.20
PHONE_Y = 3.72

# ---------------------------------------------------------------- west wall
# Joey's door was 550 mm off the south-west corner, which left 430 mm of wall
# once the architrave was on it - not enough to read as a pier at all.  Doubled.
JOEY_DOOR = (-0.13, 0.77)
CHAN_DOOR = (4.45, 5.35)
ENT_Y = (1.01, 4.21)           # the wall unit, 3.20 wide, on the new centre
ENT_D = 0.545
DOOR_OPEN = 86.0               # every interior door in the flat stands open

# ---------------------------------------------------------------- bedrooms
# The west block, read off the floor plan against a metre grid pinned to this
# origin.  Neither bedroom lines up with the living room: Chandler's north wall
# stops short of the window wall and Joey's room runs PAST the fourth wall to
# the south.  That is not sloppiness in the plan - it is what an old walk-up
# carved into apartments looks like, and squaring the block off would lose the
# one thing that makes the footprint read as a building.
BW_TH = 0.30                   # wall between the bedrooms and the living room
BED_W = -3.85
BED_E = -0.30

CH_X = (BED_W, BED_E)          # Chandler - 3.55 x 3.80
CH_Y = (2.70, 6.50)
PARTY = (2.54, 2.70)           # party wall between the two rooms
JO_X = (BED_W, BED_E)          # Joey - 3.55 x 3.84
JO_Y = (-1.30, PARTY[0])

CH_WIN = ((-2.96, -2.36), (-1.56, -0.94))
JO_WIN = (0.05, 0.90)

# The dartboard hangs on JOEY'S BEDROOM DOOR, not on the kitchen return - that
# strip of wall belongs to the cabinet run.  DART_AT is the face of the closed
# leaf: the leaf is centred in a 300 mm reveal and is 42 thick, so its
# living-room side stands 129 mm in from the wall's own face.
DART_AT = BED_E + (BW_TH + 0.042) * 0.5
DART_X = (JOEY_DOOR[0] + JOEY_DOOR[1]) * 0.5
DART_Z = 1.730                  # regulation: the bull is 5 ft 8 off the floor

# ---------------------------------------------------------------- bathroom
# Widened EAST, towards the front door.  Taking the extra width off the west
# side put the bathroom's own west wall over the living room's second window -
# you stood at the basin looking at the back of a window that belongs to
# another room.  The west wall now stays on the line it always had and the
# room grows the other way, which is also the only direction with nothing
# behind it.
BA_X = (2.85, 5.60)
BA_Y = (NY + TW, NY + TW + 3.05)      # 2.75 x 3.05
BA_CZ = 2.62
BA_TUB_X = (BA_X[0], BA_X[0] + 1.55)
BA_TUB_Y = (BA_Y[1] - 0.72, BA_Y[1])
# The basin sits in the MIDDLE of its vanity, not off the front corner of it -
# 0.30 back from the counter's front lip and centred on the cabinet's width.
BA_VAN_Y = (BA_Y[0] + 0.95, BA_Y[0] + 1.95)
BA_BASIN = (BA_X[1] - 0.30, (BA_VAN_Y[0] + BA_VAN_Y[1]) * 0.5)
# far enough south that the cistern clears the vanity's end
BA_WC = (BA_X[1] - 0.30, BA_Y[0] + 0.68)

# ---------------------------------------------------------------- furniture
SOFA_C = ((WIN_A[0] + WIN_B[1]) * 0.5, NY - 0.47)
SOFA_L = 1.96
SOFA_D = 0.90
COFFEE_C = (1.42, NY - 1.42)
SIDE_T = (2.86, NY - 0.62)     # the white two-tier table, 245 top radius
# The floor lamp stands EAST of that table, clear of it.  At (3.02, NY-0.44)
# the two centres were 241 apart and the table's own top is 245, so the lamp's
# pole ran straight up through both of its tiers.
FLOOR_LAMP = (3.34, NY - 0.74)
REC_A = (2.45, 3.73)           # north recliner  - both face west
REC_B = (2.45, 2.01)           # south recliner
# Yaw applied to a chair modelled facing -X (its back slab is at +X), so ZERO
# is already due west - which is where the television is.  Setting 180 here on
# the assumption the chair faced +X turned both of them round to stare at the
# kitchen.  They splay about 15 degrees towards each other.
# Aimed at the television, which also turns them in towards each other and the
# glass table between them.  Splayed the other way they face out of the room.
REC_ROT_A = 24.0
REC_ROT_B = -23.0
GLASS_T = (2.12, 2.87)
RUG_C = (2.40, 2.84)
RUG_WH = (2.20, 3.50)

# The stools stand against the peninsula's WEST face, so they read side by
# side from the living room and one behind the other from the couch.
STOOL_A = (PEN_X[0] - 0.30, 3.58)
STOOL_B = (PEN_X[0] - 0.30, 4.26)
STOOL_H = 0.700
# The ceramic greyhound stands in the CORNER BY THE COUCH, not out in the
# kitchen walkway where it blocks the aisle and reads as an obstacle.
# Standing in the north-west corner beside the couch, nose to the window, so
# it is clear of every walkway and of the camera line to the sofa.
DOG = (0.34, 6.46)
DOG_ROT = 90.0     # nose south, into the apartment
DOG_SCALE = 1.02

FOOS_C = (7.20, 1.12)          # clear of the peninsula's south-east corner
FOOS_ROT = 104.0
FOOS_L, FOOS_W, FOOS_H = 1.42, 0.76, 0.90

BENCH_C = (3.40, 0.30)
SHELF_C = (5.72, 0.26)

# ---------------------------------------------------------------- palette
WALL = 'C9C2B2'
WALL_UP = 'D6CCB8'
TRIM = 'DED6C4'
DOOR_GREY = 'CFC8BC'
CAB_CREAM = 'E4DAC4'
ISL_PUTTY = 'C4B49A'
YELLOW = 'E8CE1C'
CURTAIN = 'C3AE85'
CEIL = 'E0DACD'


def rod_len():
    return ROD_X[1] - ROD_X[0]
