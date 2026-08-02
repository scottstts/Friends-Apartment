"""f_living - the seating half of the room.

The two black leather recliners are the hero furniture of this set and they are
the hardest thing in the flat to get right, because everything that makes a
BarcaLounger read as one is ROUNDNESS: the arms are fat rolls, the back is
three stacked bolsters, and the only straight lines on the whole chair are the
plinth and the seat frame.  Modelled as boxes with a chamfer they look like
office furniture, so almost every part here is a swept ellipse.
"""
import bpy, math, random, os
from mathutils import Vector
import mlib, mats, props, L

C = "Living"


def materials():
    # Grain amplitude and clearcoat both come well down from the first pass.
    # A 120-per-metre pebble at full bump strength puts a facet every 8 mm, and
    # every one of those facets catches the specular lobe - which on black
    # leather under a warm key reads as glitter, not as hide.
    mats.leather("M_YellowLeather", 'E3C41C', rough=0.42, crease=0.85,
                 grain=0.50, coat=0.26, scale=0.9, sheen=0.10)
    mats.leather("M_BlackLeather", '15151A', rough=0.44, crease=1.05,
                 grain=0.42, coat=0.16, scale=0.7)
    # `axis` is the direction the RINGS vary along, so a board whose grain runs
    # east-west wants axis='Y'.  Set to the length of the board instead and the
    # rings run across it at one per 45 mm, which is corduroy.
    mats.wood("M_TableWood", ['9A6634', 'B98A4E', '6E421F'], ring=8.0,
              axis='Y', warp=0.85, rough=(0.24, 0.46), coat=0.30,
              grain_relief=0.07, scale=1.0)
    mats.wood("M_DarkWood", ['4A2C18', '6B4224', '331C0E'], ring=9.0,
              axis='Z', warp=0.45, rough=(0.26, 0.48), coat=0.22,
              grain_relief=0.06, scale=1.0)
    # The wall unit is PALE natural wood, like everything else on this set -
    # the deep rosewood the first pass gave it is the one dark mass in a room
    # of creams and it drags the whole west wall down.  The grain is calmed
    # right off too: ring=6 with warp under 0.5 gives long straight figure
    # instead of the cathedral waves that read as printed veneer.
    mats.wood("M_EntWood", ['C6A876', 'DCC79E', 'AA8A54'], ring=7.5,
              axis='Z', warp=0.26, rough=(0.24, 0.44), coat=0.26,
              grain_relief=0.045, scale=0.9)
    mats.wood("M_EntBack", ['B49A70', 'C6B08A', '9A8058'], ring=5.0,
              axis='Z', warp=0.35, rough=(0.30, 0.50), coat=0.10,
              grain_relief=0.04, scale=0.9)
    mats.metal("M_Steel", 'B9BDC2', rough=0.20, brush=0.5, grime=0.30)
    mats.metal("M_Bronze", '4A3E30', rough=0.36, grime=0.45)
    # the coffee table's grey top and its white corner blocks
    mats.paint("M_TableSlate", '74787A', rough=0.46, coat=0.10, brush=0.30)
    mats.plastic("M_TableCap", 'EAE4D6', rough=0.36, coat=0.22)
    mats.plastic("M_TVCase", '232326', rough=0.42, coat=0.20)
    mats.plastic("M_Screen", '20242A', rough=0.07, coat=0.70)
    mats.plastic("M_TVBezel", '3A3A3E', rough=0.44, coat=0.20)
    mats.wood("M_EntTop", ['CCAE7C', 'DEC69A', 'B08C58'], ring=6.0,
              axis='Y', warp=0.40, rough=(0.22, 0.42), coat=0.32,
              grain_relief=0.05)
    mats.clear_glass("M_TableGlass", 'E8F0F1', rough=0.02)
    mats.diamond("M_Curtain", 'C9B084', ink='A38F62', pitch=0.128, rough=0.76,
                 line=0.11)
    mats.fabric("M_Cushion1", '6E5E86', rough=0.72, weave=300.0, sheen=0.45)
    mats.fabric("M_Cushion2", 'B8B2A2', rough=0.78, weave=320.0, sheen=0.35)
    mats.fabric("M_Cushion3", '3C4A5E', rough=0.74, weave=310.0, sheen=0.40)
    mats.carpet("M_RugCream", 'DCD4C0', rough=0.94)
    mats.carpet("M_RugOrange", 'AE7440', rough=0.94)
    mats.carpet("M_RugMaroon", '7A3A32', rough=0.94)
    mats.carpet("M_RugGrey", '9A9384', rough=0.94)
    mats.carpet("M_RugDark", '5A4E42', rough=0.94)
    mats.carpet("M_MatWhite", 'E4E0D6', rough=0.94)
    mats.carpet("M_MatRed", 'AE2B26', rough=0.94)
    mats.paint("M_LampShade", 'E6E2D6', rough=0.55)
    ASSETS = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "assets")
    mats.picture("M_ArtLaurel",
                 os.path.join(ASSETS, "Laurel_and_Hardy_poster.jpeg"),
                 rough=0.40, gloss=0.28)
    mats.picture("M_ArtVendetta",
                 os.path.join(ASSETS, "Vendetta_poster.jpg"),
                 rough=0.36, gloss=0.34)
    mats.picture("M_ArtDieHard",
                 os.path.join(ASSETS, "die_hard.jpeg"),
                 rough=0.38, gloss=0.30)
    mats.paper("M_ArtA", '2A2622', rough=0.34, gloss=0.45)
    mats.paper("M_ArtB", 'B0A48C', rough=0.40, gloss=0.35)
    mats.paper("M_PosterArt", 'C8B840', rough=0.32, gloss=0.55)
    mats.paper("M_MagA", 'B8503A', rough=0.30, gloss=0.60)
    mats.paper("M_MagB", '2E6E8A', rough=0.30, gloss=0.60)
    mats.fabric("M_PlantGreen", '3C6E3A', rough=0.62, weave=180.0, sheen=0.55,
                bump=0.30)
    for nm, col in (("M_ToyRed", 'C0342A'), ("M_ToyBlue", '2A56A0'),
                    ("M_ToyGreen", '2E7A44'), ("M_ToyYellow", 'D8A81E')):
        mats.plastic(nm, col, rough=0.24, coat=0.45)
    mats.fabric("M_PengBlack", '1C1C22', rough=0.88, weave=420.0,
                sheen=0.55, fuzz=1.0)
    mats.fabric("M_PengWhite", 'E4E0D4', rough=0.88, weave=420.0,
                sheen=0.55, fuzz=1.0)
    mats.fabric("M_PengBeak", 'D8901E', rough=0.72, weave=380.0, sheen=0.4)
    mats.plastic("M_PengEye", '141014', rough=0.14, coat=0.65)


def M(n):
    return mats.get(n)


# ================================================================== the couch

def couch():
    """A low yellow leather two-seater.  Everything is one hide, so the piece
    only reads at all through its seams and the roll on the arms and back."""
    out = []
    cx, cy = L.SOFA_C
    hl, hd = L.SOFA_L * 0.5, L.SOFA_D * 0.5

    body = mlib.rounded_box("V_SofaBase", -hl, -hd, 0.115, hl, hd, 0.292,
                            r=0.030, seg=4, cname=C)
    mlib.bevel(body, 0.006, 3, 40)
    mlib.smooth_shade(body, 34)
    out.append(body)

    # arms: a fat roll swept front-to-back, on a flat side panel
    for s in (-1, 1):
        ax = s * (hl - 0.105)
        arm = props.sweep_var("V_SofaArm%d" % (s > 0), [
            (ax, -hd + 0.010, 0.492), (ax, -hd + 0.055, 0.492),
            (ax, 0.0, 0.494), (ax, hd - 0.055, 0.492),
            (ax, hd - 0.010, 0.492)],
            [(0.070, 0.034), (0.098, 0.070), (0.104, 0.076),
             (0.098, 0.070), (0.070, 0.034)], 18, C)
        out.append(arm)
        side = mlib.rounded_box("V_SofaSide%d" % (s > 0),
                                ax - 0.104, -hd, 0.272, ax + 0.104, hd, 0.500,
                                r=0.026, cname=C)
        mlib.bevel(side, 0.005, 3, 40)
        mlib.smooth_shade(side, 34)
        out.append(side)

    # back: an upright pad with a rolled top edge
    back = props.sweep_var("V_SofaBack", [
        (-hl + 0.150, hd - 0.115, 0.726), (-hl + 0.205, hd - 0.115, 0.726),
        (0.0, hd - 0.115, 0.730), (hl - 0.205, hd - 0.115, 0.726),
        (hl - 0.150, hd - 0.115, 0.726)],
        [(0.056, 0.050), (0.078, 0.066), (0.082, 0.070),
         (0.078, 0.066), (0.056, 0.050)], 18, C)
    out.append(back)
    bs = mlib.rounded_box("V_SofaBackSlab", -hl + 0.150, hd - 0.190, 0.268,
                          hl - 0.150, hd - 0.040, 0.740, r=0.024, cname=C)
    mlib.bevel(bs, 0.005, 3, 40)
    mlib.smooth_shade(bs, 34)
    out.append(bs)

    # Two loose seat cushions and a FIXED back - couch.jpg has no loose back
    # cushions on this sofa, which is most of why it reads so low and flat.
    for s in (-1, 1):
        seat = mlib.cushion("V_SofaSeat%d" % (s > 0), 0.762, 0.660, 0.150,
                            r=0.058, cname=C, seg=6, plump=1.07)
        mlib.translate(seat, (s * 0.384, -0.048, 0.280))
        out.append(seat)

    for o in out:
        mlib.set_mat(o, M("M_YellowLeather"))

    for (dx, dy) in ((-hl + 0.11, -hd + 0.10), (hl - 0.11, -hd + 0.10),
                     (-hl + 0.11, hd - 0.10), (hl - 0.11, hd - 0.10)):
        ft = props.lathe("V_SofaFoot", [(0.0, 0.0), (0.021, 0.0), (0.024, 0.020),
                                        (0.026, 0.108), (0.0, 0.115)], 14, C)
        mlib.translate(ft, (dx, dy, 0.0))
        mlib.set_mat(ft, M("M_Steel"))
        out.append(ft)

    # Scatter cushions.  They stand well proud of the back, which looks wrong
    # until you check the photograph - on a sofa this low they always do.
    for (nm, sz, lean, yaw, dx, mat) in (
            ("V_Pill1", 0.36, 66.0, -12.0, -0.60, "M_Cushion2"),
            ("V_Pill2", 0.33, 72.0, 9.0, -0.26, "M_Cushion3")):
        p = props.pillow(nm, sz, sz, 0.135, cname=C)
        mlib.rot_x(p, math.radians(lean))
        mlib.rotate_z(p, math.radians(yaw))
        mlib.translate(p, (dx, 0.176, 0.430 + sz * 0.5 * math.sin(math.radians(lean))))
        mlib.set_mat(p, M(mat))
        out.append(p)
    bol = props.bolster("V_Bolster", 0.44, 0.086, cname=C)
    mlib.rot_y(bol, math.radians(90.0))
    mlib.translate(bol, (-0.22, 0.0, 0.0))
    mlib.rot_x(bol, math.radians(58.0))
    mlib.rotate_z(bol, math.radians(-24.0))
    mlib.translate(bol, (0.50, 0.150, 0.530))
    mlib.set_mat(bol, M("M_Cushion1"))
    out.append(bol)

    for o in out:
        mlib.translate(o, (cx, cy, 0.0))
    return out


# ================================================================== recliners

def recliner(name, cx, cy, rot):
    """A big overstuffed leather recliner, built facing -X and then spun, so a
    rotation of zero already looks at the television on the west wall.

    The proportions are the whole job and the first pass had one badly wrong:
    the seat cushion topped out 35 mm below the arm roll, so the chair read as
    a padded box with a lip round it.  On a real lounger the seat is 420 mm and
    the arm is 630 - a fall of nearly 200 mm - and that gap is what makes the
    arms read as arms.  Everything here hangs off that:

        0.000  floor
        0.140  plinth (wood)
        0.300  skirt
        0.340  seat platform
        0.440  TOP OF SEAT CUSHION
        0.630  top of arm roll
        1.045  top of back

    The back is four overlapping bolsters rather than three spaced ones.  Space
    them and you get sausages with daylight between; overlap them and they read
    as channelled upholstery, which is what the photographs show.
    """
    out = []
    XF, XB = -0.545, 0.470          # front and back of the chair
    AY = 0.372                      # arm centreline

    plinth = mlib.rounded_box(name + "_pl", -0.470, -0.400, 0.0, 0.420, 0.400,
                              0.140, r=0.028, cname=C)
    mlib.bevel(plinth, 0.005, 3, 40)
    mlib.smooth_shade(plinth, 34)
    mlib.set_mat(plinth, M("M_DarkWood"))
    out.append(plinth)

    skirt = mlib.rounded_box(name + "_sk", -0.500, -0.442, 0.130, 0.450, 0.442,
                             0.300, r=0.032, cname=C)
    mlib.bevel(skirt, 0.005, 3, 40)
    mlib.smooth_shade(skirt, 34)
    out.append(skirt)

    deck = mlib.rounded_box(name + "_dk", -0.480, -0.310, 0.288, 0.340, 0.310,
                            0.345, r=0.026, cname=C)
    mlib.bevel(deck, 0.005, 3, 40)
    mlib.smooth_shade(deck, 34)
    out.append(deck)

    front = mlib.rounded_box(name + "_fp", XF, -0.300, 0.140, -0.462, 0.300,
                             0.436, r=0.030, cname=C)
    mlib.bevel(front, 0.005, 3, 40)
    mlib.smooth_shade(front, 34)
    out.append(front)

    # arms: a fat roll that scrolls over at the front, on a flat side panel
    for s in (-1, 1):
        ay = s * AY
        arm = props.sweep_var(name + "_arm%d" % (s > 0), [
            (XF, ay, 0.502), (XF + 0.048, ay, 0.512), (XF + 0.126, ay, 0.518),
            (0.100, ay, 0.520), (0.380, ay, 0.522), (XB - 0.006, ay, 0.514)],
            [(0.060, 0.060), (0.088, 0.098), (0.100, 0.108),
             (0.100, 0.108), (0.098, 0.108), (0.072, 0.086)], 20, C)
        out.append(arm)
        panel = mlib.rounded_box(name + "_ap%d" % (s > 0), -0.492, ay - 0.098,
                                 0.286, XB - 0.010, ay + 0.098, 0.474,
                                 r=0.024, cname=C)
        mlib.bevel(panel, 0.005, 3, 40)
        mlib.smooth_shade(panel, 34)
        out.append(panel)

    # The cushion runs 60 mm DEEPER than the seat frame and the lowest back
    # roll drops to overlap it.  Sized to the frame and stacked edge to edge
    # they leave a slot between cushion and back you can see the floor through;
    # real upholstery always has the back sitting ON the seat.
    seat = mlib.cushion(name + "_seat", 0.760, 0.605, 0.122, r=0.062, cname=C,
                        seg=7, plump=1.13)
    mlib.translate(seat, (-0.055, 0.0, 0.318))
    out.append(seat)

    # four OVERLAPPING back bolsters, leaning further back as they rise
    for i, (z, xb, rz) in enumerate(((0.516, 0.300, 0.098),
                                     (0.684, 0.328, 0.098),
                                     (0.852, 0.356, 0.098),
                                     (1.000, 0.378, 0.086))):
        roll = props.sweep_var(name + "_bk%d" % i, [
            (xb, -0.336, z), (xb, -0.286, z), (xb, 0.0, z),
            (xb, 0.286, z), (xb, 0.336, z)],
            [(0.086, rz * 0.60), (0.108, rz * 0.94), (0.112, rz),
             (0.108, rz * 0.94), (0.086, rz * 0.60)], 20, C)
        out.append(roll)
    backslab = mlib.rounded_box(name + "_bs", 0.258, -0.348, 0.322, XB,
                                0.348, 1.048, r=0.032, cname=C)
    mlib.bevel(backslab, 0.005, 3, 40)
    mlib.smooth_shade(backslab, 34)
    out.append(backslab)

    for o in out[1:]:
        mlib.set_mat(o, M("M_BlackLeather"))

    lever = mlib.tube_along(name + "_lv", [(0.28, 0.462, 0.400),
                                           (0.33, 0.556, 0.418)],
                            mlib.circle(0.010, 8), cname=C)
    mlib.smooth_shade(lever, 46)
    knobend = props.lathe(name + "_lk", [(0.0, 0.0), (0.026, 0.004),
                                         (0.028, 0.026), (0.0, 0.034)], 14, C)
    mlib.rot_x(knobend, math.radians(-72.0))
    mlib.translate(knobend, (0.33, 0.556, 0.418))
    for o in (lever, knobend):
        mlib.set_mat(o, M("M_DarkWood"))
        out.append(o)

    grp = mlib.join(out, name, C)
    mlib.rotate_z(grp, math.radians(rot))
    # 11 mm up, because the chair stands ON the rug.  Left on the floor its
    # base plane is coplanar with the rug's underside over most of a square
    # metre, which is the largest z-fight in the whole flat.
    mlib.translate(grp, (cx, cy, 0.025))
    return [grp]


# ================================================================== tables

def coffee_table():
    """The long low table in couch.jpg.

    It is a slate-grey top in a rosewood case, and it stands on four chunky
    WHITE corner blocks with a pair of thin dark wires splaying out of each -
    those blocks are the whole character of the piece.  Without them the wires
    have nothing to come out of and read as loose bent rod under a plank,
    which is what the first pass looked like.  There is no lower shelf in the
    photograph either; the earlier one was invented.
    """
    out = []
    cx, cy = L.COFFEE_C
    w, d = 1.16, 0.52
    ZT = 0.405                      # the grey top's surface
    case = mlib.box("V_CoffCase", -w * 0.5, -d * 0.5, ZT - 0.110,
                    w * 0.5, d * 0.5, ZT - 0.014, C)
    mlib.bevel(case, 0.004, 2, 42)
    mlib.set_mat(case, M("M_TableWood"))
    out.append(case)
    top = props.worktop("V_CoffTop", -w * 0.5 - 0.011, -d * 0.5 - 0.011,
                        w * 0.5 + 0.011, d * 0.5 + 0.011, ZT, th=0.017,
                        r=0.007, cname=C)
    mlib.set_mat(top, M("M_TableSlate"))
    out.append(top)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        px, py = sx * (w * 0.5 - 0.014), sy * (d * 0.5 - 0.008)
        cap = mlib.rounded_box("V_CoffCap", px - 0.050, py - 0.044, 0.262,
                               px + 0.050, py + 0.044, ZT - 0.020, r=0.016,
                               seg=4, cname=C)
        mlib.bevel(cap, 0.004, 3, 40)
        mlib.smooth_shade(cap, 34)
        mlib.set_mat(cap, M("M_TableCap"))
        out.append(cap)
        # two wires per block, splaying apart along the two edges they sit on
        for (ex, ey) in ((sx * 0.088, sy * 0.014), (sx * 0.014, sy * 0.088)):
            path = [(px, py, 0.272),
                    (px + ex * 0.24, py + ey * 0.24, 0.196),
                    (px + ex * 0.60, py + ey * 0.60, 0.104),
                    (px + ex * 0.91, py + ey * 0.91, 0.028),
                    (px + ex, py + ey, 0.005)]
            lg = mlib.tube_along("V_CoffWire", path, mlib.circle(0.0058, 8),
                                 cname=C)
            mlib.smooth_shade(lg, 46)
            mlib.set_mat(lg, M("M_Bronze"))
            out.append(lg)
            ft = props.lathe("V_CoffFoot", [(0.0, 0.0), (0.011, 0.0),
                                            (0.010, 0.008), (0.0, 0.009)],
                             12, C)
            mlib.translate(ft, (px + ex, py + ey, 0.0))
            mlib.set_mat(ft, M("M_TableCap"))
            out.append(ft)
    for o in out:
        mlib.translate(o, (cx, cy, 0.0))
    return out


def glass_table():
    """The little round glass table that lives between the two recliners."""
    out = []
    cx, cy = L.GLASS_T
    for (r, z) in ((0.235, 0.505), (0.205, 0.235)):
        pl = props.lathe("V_GtPlate", [(0.0, 0.0), (r - 0.006, 0.0),
                                       (r, 0.005), (r - 0.006, 0.010),
                                       (0.0, 0.010)], 36, C)
        mlib.translate(pl, (cx, cy, z))
        mlib.set_mat(pl, M("M_TableGlass"))
        out.append(pl)
    for i in range(3):
        a = math.tau * i / 3 + 0.4
        p0 = (cx + 0.185 * math.cos(a), cy + 0.185 * math.sin(a), 0.0)
        p1 = (cx + 0.135 * math.cos(a), cy + 0.135 * math.sin(a), 0.505)
        lg = mlib.tube_along("V_GtLeg%d" % i, [p0, p1], mlib.circle(0.011, 10),
                             cname=C)
        mlib.smooth_shade(lg, 46)
        mlib.set_mat(lg, M("M_Steel"))
        out.append(lg)
    rng = props.torus("V_GtRing", 0.152, 0.008, 30, 8, C, cx=cx, cy=cy, cz=0.235)
    mlib.set_mat(rng, M("M_Steel"))
    out.append(rng)
    rem = mlib.rounded_box("V_Remote", cx - 0.095, cy - 0.028, 0.515,
                           cx + 0.095, cy + 0.028, 0.536, r=0.010, cname=C)
    mlib.rotate_z(rem, 0.5, (cx, cy))
    mlib.bevel(rem, 0.003, 2, 44)
    mlib.smooth_shade(rem, 34)
    mlib.set_mat(rem, M("M_TVCase"))
    out.append(rem)
    return out


def side_table():
    """The white two-tier round table at the couch's east end."""
    out = []
    cx, cy = L.SIDE_T
    for (r, z) in ((0.245, 0.560), (0.215, 0.290)):
        t = props.lathe("V_SideTop", [(0.0, 0.0), (r - 0.014, 0.0),
                                      (r, 0.008), (r - 0.006, 0.019),
                                      (0.0, 0.019)], 32, C)
        mlib.translate(t, (cx, cy, z))
        mlib.set_mat(t, M("M_LampShade"))
        out.append(t)
    col = props.lathe("V_SideCol", [(0.0, 0.0), (0.075, 0.0), (0.072, 0.014),
                                    (0.030, 0.040), (0.028, 0.540),
                                    (0.036, 0.560), (0.0, 0.562)], 20, C)
    mlib.translate(col, (cx, cy, 0.0))
    mlib.set_mat(col, M("M_Steel"))
    out.append(col)
    return out


# ================================================================== rugs

def rugs():
    out = []

    def region(u, v):
        if u < 0.035 or u > 0.965 or v < 0.022 or v > 0.978:
            return 4
        if 0.06 <= u <= 0.46 and 0.60 <= v <= 0.885:
            return 1
        if 0.54 <= u <= 0.94 and 0.055 <= v <= 0.285:
            return 2
        if 0.10 <= u <= 0.52 and 0.085 <= v <= 0.320:
            return 3
        if 0.58 <= u <= 0.93 and 0.615 <= v <= 0.775:
            return 3
        return 0

    out.append(props.rug("V_Rug", L.RUG_C[0], L.RUG_C[1], L.RUG_WH[0],
                         L.RUG_WH[1], region,
                         [M("M_RugCream"), M("M_RugOrange"), M("M_RugMaroon"),
                          M("M_RugGrey"), M("M_RugDark")],
                         cname=C, cell=0.032, th=0.013, z0=0.012))

    # the small white mat with the red chevrons, in front of the couch
    def chev(u, v):
        if u < 0.06 or u > 0.94 or v < 0.09 or v > 0.91:
            return 0
        f = (u * 7.0) % 1.0
        band = int(v * 5.0)
        t = abs(f - 0.5) * 2.0
        return 1 if t > 0.55 and band % 2 == 0 else 0

    out.append(props.rug("V_Mat", 1.30, L.NY - 1.66, 1.22, 0.80, chev,
                         [M("M_MatWhite"), M("M_MatRed")],
                         cname=C, cell=0.020, th=0.011, z0=0.012))
    return out


# ================================================================== west wall

def entertainment():
    """The entertainment centre.

    A composite unit, not a sideboard with a set standing on it: two towers
    flanking a deep centre bay, with the television INSIDE the bay, the video
    under it and cupboards at the base.  It stops just above the bay - the two
    extra tiers the first pass carried above that took it to 1.9 m and turned
    it into a bookcase, which is not what the room has.  The right-hand bay is
    a closed cupboard with a wooden door rather than open shelving, so the
    piece is asymmetric the way real built-up units are.

    It is also sized to sit cleanly between the two bedroom doors; the very
    wide version that blocks them belongs to the one episode where Joey builds
    it, not to the room as it normally stands.
    """
    out = []
    y0, y1 = L.ENT_Y
    x0 = L.WX + 0.026
    x1 = x0 + L.ENT_D
    T = 0.020                        # carcass thickness
    # The roof sits well ABOVE the top of the set, not just clear of it: the
    # television is 1.195 at its highest and the underside of the roof is at
    # 1.540, so the bay carries a real 345 mm of air over the screen.  Tight to
    # the set it looks like a slot cut to fit rather than a shelf the set was
    # put into.
    ZB, ZM, ZT = 0.100, 0.615, 1.560  # base, mid deck, top
    ya, yb = y0 + 0.660, y1 - 0.600   # the centre bay's cheeks

    parts = []
    for yy in (y0, ya, yb, y1 - T):
        parts.append(mlib.box("V_EntDiv", x0, yy, ZB, x1, yy + T, ZT, C))
    for zz in (ZB, ZM, ZT - T):
        parts.append(mlib.box("V_EntDeck", x0 + 0.016, y0, zz, x1, y1,
                              zz + T, C))
    # open shelving in the LEFT tower only
    for zz in (0.865, 1.110, 1.330):
        parts.append(mlib.box("V_EntSh", x0 + 0.016, y0 + T, zz - 0.009,
                              x1, ya, zz + 0.009, C))
    # the right tower is a cupboard, so it gets one internal shelf behind its door
    for zz in (0.925, 1.245):
        parts.append(mlib.box("V_EntShR", x0 + 0.016, yb + T, zz - 0.009, x1,
                              y1 - T, zz + 0.009, C))
    case = mlib.join(parts, "V_EntCase", C)
    mlib.bevel(case, 0.0025, 2, 44)
    mlib.set_mat(case, M("M_EntWood"))
    out.append(case)
    back = mlib.box("V_EntBack", x0 + 0.003, y0 + 0.004, ZB + 0.004,
                    x0 + 0.019, y1 - 0.004, ZT - 0.004, C)
    mlib.bevel(back, 0.002, 2, 44)
    mlib.set_mat(back, M("M_EntBack"))
    out.append(back)
    pel = mlib.box("V_EntPelmet", x0 + 0.010, y0 - 0.014, ZT, x1 + 0.020,
                   y1 + 0.014, ZT + 0.042, C)
    mlib.bevel(pel, 0.005, 3, 40)
    mlib.set_mat(pel, M("M_EntWood"))
    out.append(pel)
    plin = mlib.box("V_EntPlinth", x0 + 0.006, y0 + 0.026, 0.0, x1 - 0.060,
                    y1 - 0.026, 0.104, C)
    mlib.bevel(plin, 0.003, 2, 40)
    mlib.set_mat(plin, M("M_TVCase"))
    out.append(plin)

    # doors: both base cupboards, plus the whole right-hand upper bay
    doors = [("b0", y0 + T + 0.005, ya - 0.005, ZB + 0.035, ZM - 0.020),
             ("b1", yb + T + 0.005, y1 - T - 0.005, ZB + 0.035, ZM - 0.020),
             ("u1", yb + T + 0.005, y1 - T - 0.005, ZM + 0.017, ZT - T - 0.016)]
    for (tag, a, b, za, zb) in doors:
        d = mlib.prism_yz("V_EntDoor_" + tag,
                          [((a + b) * 0.5 + p, (za + zb) * 0.5 + q)
                           for (p, q) in mlib.rounded_rect(b - a, zb - za,
                                                           0.008, 3)],
                          x1, x1 + 0.019, C)
        mlib.bevel(d, 0.0025, 2, 44)
        mlib.set_mat(d, M("M_EntWood"))
        out.append(d)
        pull = mlib.box("V_EntPull_" + tag, x1 + 0.019, a + 0.028, zb - 0.044,
                        x1 + 0.026, b - 0.028, zb - 0.022, C)
        mlib.bevel(pull, 0.003, 2, 40)
        mlib.set_mat(pull, M("M_TVCase"))
        out.append(pull)

    # Dressing: the left tower's shelves, which are the only open ones left.
    #
    # Everything stands at the FRONT of the shelf, spines out.  These bays are
    # 545 deep and a book is 180, so anything pushed to the back sits a third
    # of a metre inside the case where no light reaches it - which read as
    # books buried in the wall rather than books on a shelf.
    rnd = random.Random(31)
    FRONT = x1 - 0.016
    for zz in (ZM + T, 0.884, 1.129, 1.349):
        y = y0 + T + 0.040
        while y < ya - 0.11:
            k = rnd.random()
            if k < 0.66:
                bw = rnd.uniform(0.026, 0.044)
                ob = mlib.box("V_EntBook", FRONT - rnd.uniform(0.15, 0.21), y,
                              zz, FRONT, y + bw,
                              zz + rnd.uniform(0.15, 0.20), C)
                mlib.bevel(ob, 0.0015, 2, 44)
            else:
                bw = 0.10
                ob = props.boxprop("V_EntBox", FRONT - 0.085, y + 0.05, zz,
                                   0.17, 0.10, rnd.uniform(0.085, 0.130), C)
            mlib.set_mat(ob, M(["M_Cushion1", "M_Cushion3", "M_ArtB",
                                "M_MagA", "M_MagB", "M_LampShade"][
                                    rnd.randrange(6)]))
            out.append(ob)
            y += bw + rnd.uniform(0.010, 0.026)

    # 4:3, which is what a 1990s set is - 780 x 575 in a 910 bay
    out += television(x0 + 0.030, (ya + yb) * 0.5, ZM + 0.020, w=0.780,
                      hh=0.575, d=0.480)
    out += vcr(x0 + 0.055, (ya + yb) * 0.5, ZB + 0.028)
    out += unit_top(x0, y0, y1, ZT + 0.042)
    return out


def unit_top(x0, y0, y1, z):
    """The top of the unit is a shelf like any other and it is never empty:
    full_set.jpg has a model boat, framed pictures leaning on the wall, and a
    row of small things along it.  A bare cap reads as a rendering that stopped
    rather than as a piece of furniture in a lived-in room."""
    out = []
    rnd = random.Random(83)

    # two framed photographs LEANING back against the wall
    for i, (u, w, h, mat) in enumerate(((y0 + 0.30, 0.220, 0.280, "M_ArtB"),
                                        (y0 + 0.56, 0.180, 0.235, "M_MagB"))):
        fr = props.frame_art("V_TopFrame%d" % i, w, h, depth=0.020, cname=C,
                             moulding=0.022, standoff=0.0)
        mlib.set_mat(fr[0], M("M_DarkWood"))
        mlib.set_mat(fr[1], M(mat))
        props.wall_place(fr, 'W', u, z + h * 0.5, x0 + 0.070)
        for o in fr:
            # rot_y(+7) about the base takes the top INTO the room, which is
            # which way a picture propped on a shelf actually leans
            mlib.rot_y(o, math.radians(7.0), (x0 + 0.070, u, z))
            out.append(o)

    # a stoneware jug
    jug = props.lathe("V_TopJug", [(0.0, 0.0), (0.052, 0.0), (0.058, 0.016),
                                   (0.076, 0.078), (0.070, 0.132),
                                   (0.046, 0.168), (0.040, 0.196),
                                   (0.046, 0.206), (0.040, 0.210),
                                   (0.034, 0.200), (0.0, 0.198)], 24, C)
    mlib.translate(jug, (x0 + 0.180, y0 + 0.88, z))
    mlib.set_mat(jug, M("M_LampShade"))
    out.append(jug)

    # a flat stack of books
    for i in range(3):
        bk = mlib.box("V_TopBook%d" % i, x0 + 0.075, y0 + 1.12,
                      z + i * 0.030, x0 + 0.075 + rnd.uniform(0.22, 0.27),
                      y0 + 1.12 + rnd.uniform(0.150, 0.185),
                      z + i * 0.030 + 0.028, C)
        mlib.bevel(bk, 0.002, 2, 44)
        mlib.rotate_z(bk, rnd.uniform(-0.13, 0.13),
                      (x0 + 0.19, y0 + 1.20))
        mlib.set_mat(bk, M(["M_Cushion1", "M_MagA", "M_Cushion3"][i]))
        out.append(bk)

    # a turned figure, and a lidded box
    fig = props.lathe("V_TopFig", [(0.0, 0.0), (0.048, 0.0), (0.046, 0.014),
                                   (0.022, 0.030), (0.020, 0.086),
                                   (0.036, 0.120), (0.034, 0.152),
                                   (0.020, 0.170), (0.026, 0.186),
                                   (0.014, 0.198), (0.0, 0.200)], 22, C)
    mlib.translate(fig, (x0 + 0.190, y0 + 1.56, z))
    mlib.set_mat(fig, M("M_Bronze"))
    out.append(fig)

    bx = props.boxprop("V_TopBox", x0 + 0.185, y0 + 1.86, z, 0.26, 0.175,
                       0.115, C, rotz=0.09)
    mlib.set_mat(bx, M("M_DarkWood"))
    out.append(bx)
    lid = props.boxprop("V_TopBoxLid", x0 + 0.185, y0 + 1.86, z + 0.115,
                        0.276, 0.190, 0.022, C, rotz=0.09)
    mlib.set_mat(lid, M("M_DarkWood"))
    out.append(lid)

    # a small potted plant at the far end
    pot = props.lathe("V_TopPot", [(0.0, 0.0), (0.048, 0.0), (0.052, 0.010),
                                   (0.066, 0.098), (0.070, 0.108),
                                   (0.062, 0.112), (0.058, 0.104),
                                   (0.044, 0.014), (0.0, 0.012)], 22, C)
    mlib.translate(pot, (x0 + 0.175, y1 - 0.16, z))
    mlib.set_mat(pot, M("M_MagA"))
    out.append(pot)
    for i in range(7):
        a = math.tau * i / 7 + 0.3
        lean = 0.055 + 0.035 * ((i * 7) % 5) / 4.0
        lf = props.sweep_var("V_TopLeaf%d" % i, [
            (x0 + 0.175, y1 - 0.16, z + 0.100),
            (x0 + 0.175 + lean * 0.5 * math.cos(a),
             y1 - 0.16 + lean * 0.5 * math.sin(a), z + 0.172),
            (x0 + 0.175 + lean * math.cos(a),
             y1 - 0.16 + lean * math.sin(a), z + 0.212),
            (x0 + 0.175 + lean * 1.32 * math.cos(a),
             y1 - 0.16 + lean * 1.32 * math.sin(a), z + 0.196)],
            [(0.008, 0.006), (0.030, 0.007), (0.034, 0.006), (0.006, 0.003)],
            8, C, smooth=50)
        mlib.set_mat(lf, M("M_PlantGreen"))
        out.append(lf)
    return out


def television(x0, cy, z0, w=0.72, hh=0.585, d=0.545):
    """A 1990s CRT: a deep tapered case, a recessed bezel, and a slightly proud
    screen behind it.  `x0` is the BACK of the set, so it can be dropped into a
    cabinet bay by its back plane."""
    out = []
    rings = [
        (x0 + d, 0.5 * w, 0.5 * hh), (x0 + 0.10, 0.5 * w, 0.5 * hh),
        (x0 + 0.055, 0.44 * w, 0.44 * hh), (x0, 0.40 * w, 0.40 * hh)]
    lof = []
    for (xx, ry, rz) in rings:
        lof.append([(xx, cy + a, z0 + hh * 0.5 + b)
                    for (a, b) in mlib.rounded_rect(ry * 2, rz * 2, 0.045, 5)])
    case = mlib.loft("V_TV", lof, close_u=False, close_v=True, cname=C,
                     cap_start=True, cap_end=True)
    mlib.bevel(case, 0.005, 3, 40)
    mlib.smooth_shade(case, 34)
    mlib.set_mat(case, M("M_TVCase"))
    out.append(case)
    bez = mlib.prism_yz("V_TVBezel",
                        [(cy + a, z0 + hh * 0.5 + 0.026 + b) for (a, b) in
                         mlib.rounded_rect(w - 0.062, hh - 0.126, 0.044, 5)],
                        x0 + d - 0.020, x0 + d + 0.008, C)
    mlib.bevel(bez, 0.005, 3, 40)
    mlib.smooth_shade(bez, 34)
    mlib.set_mat(bez, M("M_TVBezel"))
    out.append(bez)
    scr = mlib.prism_yz("V_TVScreen",
                        [(cy + a, z0 + hh * 0.5 + 0.026 + b) for (a, b) in
                         mlib.rounded_rect(w - 0.104, hh - 0.168, 0.038, 5)],
                        x0 + d - 0.026, x0 + d + 0.002, C)
    mlib.bevel(scr, 0.004, 3, 40)
    mlib.smooth_shade(scr, 34)
    mlib.set_mat(scr, M("M_Screen"))
    out.append(scr)
    flap = mlib.box("V_TVFlap", x0 + d - 0.024, cy - w * 0.5 + 0.045,
                    z0 + 0.026, x0 + d - 0.010, cy + w * 0.5 - 0.180,
                    z0 + 0.072, C)
    mlib.bevel(flap, 0.003, 2, 40)
    mlib.set_mat(flap, M("M_Screen"))
    out.append(flap)
    return out


def vcr(x0, cy, z0):
    out = []
    body = mlib.rounded_box("V_Vcr", x0, cy - 0.215, z0, x0 + 0.36,
                            cy + 0.215, z0 + 0.092, r=0.010, cname=C)
    mlib.bevel(body, 0.003, 2, 44)
    mlib.smooth_shade(body, 34)
    mlib.set_mat(body, M("M_TVCase"))
    out.append(body)
    fasc = mlib.box("V_VcrF", x0 + 0.356, cy - 0.200, z0 + 0.014,
                    x0 + 0.368, cy + 0.200, z0 + 0.078, C)
    mlib.bevel(fasc, 0.003, 2, 40)
    mlib.set_mat(fasc, M("M_Screen"))
    out.append(fasc)
    return out


# ================================================================== curtains

def curtains():
    """Three panels on one rod across both windows, with rings.

    They cannot be one continuous drape: the set hangs a panel outside each
    window and one over the pier between them, and that gap is what lets the
    blinds show, which is most of what the window wall looks like."""
    out = []
    z0, z1 = 0.030, L.ROD_Z - 0.070
    yw = L.NY - 0.115
    panels = ((0.185, 0.665), (1.250, 1.905), (2.520, 3.010))
    for i, (a, b) in enumerate(panels):
        d = props.drape("V_Curtain%d" % i, a, b, yw, z0, z1,
                        folds=max(4, int((b - a) / 0.115)), amp=0.052,
                        cname=C, nz=16, seed=7 + i * 5)
        mlib.set_mat(d, M("M_Curtain"))
        out.append(d)

    rod = mlib.tube_along("V_Rod", [(L.ROD_X[0] - 0.10, L.NY - 0.130, L.ROD_Z),
                                    (L.ROD_X[1] + 0.10, L.NY - 0.130, L.ROD_Z)],
                          mlib.circle(0.0145, 14), cname=C)
    mlib.smooth_shade(rod, 46)
    mlib.set_mat(rod, M("M_Bronze"))
    out.append(rod)
    for s, x in ((0, L.ROD_X[0] - 0.10), (1, L.ROD_X[1] + 0.10)):
        fin = props.lathe("V_Finial%d" % s, [(0.0, 0.0), (0.020, 0.004),
                                             (0.030, 0.026), (0.026, 0.050),
                                             (0.014, 0.062), (0.0, 0.066)],
                          18, C)
        props.face_x(fin, 1.0 if s else -1.0, (x, L.NY - 0.130, L.ROD_Z))
        mlib.set_mat(fin, M("M_Bronze"))
        out.append(fin)
    for bx in (0.30, 1.58, 2.86):
        br = mlib.tube_along("V_RodBr", [(bx, L.NY - 0.012, L.ROD_Z),
                                         (bx, L.NY - 0.130, L.ROD_Z)],
                             mlib.circle(0.009, 10), cname=C)
        mlib.smooth_shade(br, 46)
        mlib.set_mat(br, M("M_Bronze"))
        out.append(br)
    for (a, b) in panels:
        n = max(3, int((b - a) / 0.115))
        for k in range(n + 1):
            rx = a + (b - a) * k / n
            rg = props.torus("V_Ring", 0.024, 0.0042, 16, 6, C,
                             cx=rx, cy=L.NY - 0.130, cz=L.ROD_Z)
            mlib.rot_y(rg, math.pi * 0.5, (rx, L.NY - 0.130, L.ROD_Z))
            mlib.set_mat(rg, M("M_Bronze"))
            out.append(rg)
    return out


# ================================================================== wall goods

def art():
    """The two posters from couch.jpg, on the walls they are actually on.

    Both are real images on real UVs rather than procedural stand-ins: a poster
    is the one thing in a room that a procedural texture cannot fake, because
    what it IS is the picture.  Everything about the surface round it - the
    paper tooth, the varnish, the frame - stays procedural.
    """
    out = []
    # Laurel and Hardy, landscape, on the wall above the entertainment unit.
    # 1258 x 826, so 1.523:1 - the frame is sized to the image, never the
    # other way round, or the print ends up stretched.
    a = props.frame_art("V_ArtLaurel", 0.920, 0.604, depth=0.032, cname=C,
                        moulding=0.044, standoff=0.019)
    mlib.set_mat(a[0], M("M_DarkWood"))
    mlib.set_mat(a[1], M("M_ArtLaurel"))
    props.wall_place(a, 'W', (L.ENT_Y[0] + L.ENT_Y[1]) * 0.5, 2.285, L.WX)
    out += a

    # Die Hard, on the east wall over the foosball end.  1336 x 1900, so
    # 0.7032:1 PORTRAIT, and 690 x 981 is that ratio to a tenth of a
    # millimetre.  frame_art's w and h ARE the visible picture - the moulding
    # grows outward from them - so this is the print, not the frame.  A slim
    # 30 mm moulding, which is what a film poster is framed in.
    b = props.frame_art("V_ArtB", 0.690, 0.981, depth=0.026,
                        cname=C, moulding=0.030, rebate=0.006, standoff=0.019)
    mlib.set_mat(b[0], M("M_DarkWood"))
    mlib.set_mat(b[1], M("M_ArtDieHard"))
    props.wall_place(b, 'E', 1.05, 1.615, L.EX)
    out += b
    return out


def penguin(cx, cy, cz, rot=0.0):
    """Hugsy.  A plush penguin, built facing -X before it is spun.

    A penguin has no neck, so the head has to grow out of the body in ONE
    continuous teardrop - a visible join is the give-away of a badly built one.
    The white front is a separate shell standing proud of the black rather than
    a colour change, because on a soft toy it is a sewn-on panel with a seam
    round it.
    """
    out = []
    body = props.sweep_var("V_Peng", [
        (0.000, 0.0, 0.008), (0.012, 0.0, 0.060), (0.016, 0.0, 0.140),
        (0.010, 0.0, 0.225), (-0.002, 0.0, 0.295), (-0.008, 0.0, 0.345),
        (-0.004, 0.0, 0.392), (0.006, 0.0, 0.426), (0.000, 0.0, 0.444)],
        [(0.055, 0.045), (0.102, 0.096), (0.122, 0.118), (0.116, 0.112),
         (0.096, 0.092), (0.082, 0.080), (0.082, 0.080), (0.060, 0.058),
         (0.016, 0.016)], 22, C, smooth=70)
    mlib.set_mat(body, M("M_PengBlack"))
    out.append(body)

    front = props.sweep_var("V_PengFront", [
        (-0.070, 0.0, 0.062), (-0.098, 0.0, 0.140), (-0.102, 0.0, 0.215),
        (-0.086, 0.0, 0.278), (-0.066, 0.0, 0.312)],
        [(0.060, 0.026), (0.078, 0.032), (0.074, 0.032), (0.058, 0.026),
         (0.038, 0.018)], 18, C, smooth=70)
    mlib.set_mat(front, M("M_PengWhite"))
    out.append(front)
    face = props.sweep_var("V_PengFace", [
        (-0.062, 0.0, 0.336), (-0.076, 0.0, 0.372), (-0.066, 0.0, 0.406)],
        [(0.050, 0.020), (0.056, 0.024), (0.040, 0.018)], 16, C, smooth=70)
    mlib.set_mat(face, M("M_PengWhite"))
    out.append(face)

    beak = props.sweep_var("V_PengBeak", [
        (-0.072, 0.0, 0.374), (-0.104, 0.0, 0.366), (-0.128, 0.0, 0.358)],
        [(0.026, 0.017), (0.017, 0.011), (0.005, 0.004)], 12, C, smooth=70)
    mlib.set_mat(beak, M("M_PengBeak"))
    out.append(beak)

    for s in (-1, 1):
        fl = props.sweep_var("V_PengFlip%d" % (s > 0), [
            (0.004, s * 0.104, 0.258), (0.006, s * 0.132, 0.196),
            (0.002, s * 0.138, 0.132), (-0.008, s * 0.124, 0.086),
            (-0.014, s * 0.104, 0.066)],
            [(0.034, 0.016), (0.042, 0.015), (0.038, 0.013), (0.026, 0.010),
             (0.012, 0.006)], 14, C, smooth=70)
        mlib.set_mat(fl, M("M_PengBlack"))
        out.append(fl)
        ft = props.sweep_var("V_PengFoot%d" % (s > 0), [
            (-0.022, s * 0.046, 0.016), (-0.070, s * 0.050, 0.012),
            (-0.110, s * 0.052, 0.009)],
            [(0.034, 0.014), (0.040, 0.011), (0.030, 0.008)], 12, C, smooth=70)
        mlib.set_mat(ft, M("M_PengBeak"))
        out.append(ft)
        ey = props.lathe("V_PengEye%d" % (s > 0), [
            (0.0, 0.0), (0.012, 0.002), (0.013, 0.009), (0.008, 0.014),
            (0.0, 0.016)], 14, C)
        mlib.rot_y(ey, math.radians(-96.0))
        mlib.translate(ey, (-0.066, s * 0.034, 0.392))
        mlib.set_mat(ey, M("M_PengEye"))
        out.append(ey)

    grp = mlib.join(out, "V_Penguin", C)
    if rot:
        mlib.rotate_z(grp, math.radians(rot))
    mlib.translate(grp, (cx, cy, cz))
    return [grp]


def couch_dressing():
    """The poster by the couch and the magazines on the coffee table - the two
    things the reference frame has that an undressed room does not."""
    out = []
    # Vendetta - 1911 x 2985, so 0.640:1 portrait.  On the west wall beside
    # the couch, which is the wall it hangs on in couch.jpg.
    pz = props.frame_art("V_Poster", 0.600, 0.937, depth=0.026, cname=C,
                         moulding=0.028, standoff=0.019)
    mlib.set_mat(pz[0], M("M_TVCase"))
    mlib.set_mat(pz[1], M("M_ArtVendetta"))
    props.wall_place(pz, 'W', 6.34, 1.620, L.WX)
    out += pz

    cx, cy = L.COFFEE_C
    for i, (dx, dy, rz, mat) in enumerate((
            (-0.30, -0.06, 0.18, "M_MagA"), (-0.16, 0.05, -0.30, "M_MagB"),
            (0.24, -0.03, 0.42, "M_MagA"))):
        # each magazine is lifted onto the one before, so no two lie in the
        # same plane where they overlap
        m = mlib.box("V_Mag%d" % i, -0.105, -0.140, i * 0.007, 0.105, 0.140,
                     i * 0.007 + 0.006, C)
        mlib.bevel(m, 0.0015, 2, 44)
        mlib.rotate_z(m, rz)
        mlib.translate(m, (cx + dx, cy + dy, 0.405))
        mlib.set_mat(m, M(mat))
        out.append(m)

    bowl = props.bowl("V_CoffBowl", cx + 0.02, cy + 0.06, 0.405, r=0.095,
                      h=0.055, cname=C)
    mlib.set_mat(bowl, M("M_LampShade"))
    out.append(bowl)

    for i, (dx, dy, h) in enumerate(((-0.06, 0.03, 0.115), (0.07, -0.04, 0.145))):
        b = props.bottle("V_SideBot%d" % i, 2.86 + dx, L.NY - 0.62 + dy, 0.579,
                         r=0.032, h=h, neck=0.012, cname=C)
        mlib.set_mat(b, M("M_TableGlass"))
        out.append(b)
    return out


def window_wall():
    """A bag slung over the curtain rod on the pier between the windows -
    couch.jpg has something hanging there in every frame.

    It hangs IN FRONT of the drape, off the rod, not screwed to the plaster
    behind it.  The middle panel covers that pier completely, so anything hung
    on the wall there can only push through the fabric - and the cap and bag
    the first pass put there did exactly that, surfacing as two coloured lumps
    apparently growing out of the curtain.
    """
    out = []
    x = L.SCONCE_X
    yr, zr = L.NY - 0.130, L.ROD_Z          # the rod
    # The drape hangs on y = NY - 0.115 and its folds swing 52 mm either side,
    # so its nearest surface is at NY - 0.167.  Everything here sits 100 mm
    # clear of that.
    yf = L.NY - 0.268
    strap = mlib.tube_along("V_Strap", [
        (x, yr + 0.026, zr - 0.004), (x, yr + 0.006, zr + 0.022),
        (x, yr - 0.022, zr + 0.012), (x, yf + 0.034, zr - 0.130),
        (x, yf, zr - 0.286)],
        mlib.rounded_rect(0.028, 0.006, 0.002, 2), cname=C)
    mlib.smooth_shade(strap, 46)
    mlib.set_mat(strap, M("M_Cushion3"))
    out.append(strap)
    bag = props.sweep_var("V_Bag", [
        (x, yf, zr - 0.282), (x, yf - 0.004, zr - 0.356),
        (x, yf - 0.006, zr - 0.446), (x, yf, zr - 0.502)],
        [(0.032, 0.022), (0.088, 0.054), (0.100, 0.062), (0.078, 0.046)],
        16, C, smooth=60)
    mlib.set_mat(bag, M("M_Cushion1"))
    out.append(bag)
    return out


def toy(cx, cy, z):
    """The bead-maze toy on the coffee table in couch.jpg: wires on a base with
    beads threaded on them."""
    out = []
    base = mlib.rounded_box("V_ToyBase", cx - 0.115, cy - 0.075, z,
                            cx + 0.115, cy + 0.075, z + 0.022, r=0.010, cname=C)
    mlib.bevel(base, 0.003, 2, 42)
    mlib.set_mat(base, M("M_ToyRed"))
    out.append(base)
    cols = ["M_ToyRed", "M_ToyBlue", "M_ToyGreen", "M_ToyYellow"]
    for i, (x0, x1, hh, tw) in enumerate(((-0.082, 0.020, 0.130, 0.045),
                                          (-0.020, 0.086, 0.165, -0.038),
                                          (0.030, -0.060, 0.105, 0.020))):
        pth = [(cx + x0, cy + tw * 0.4, z + 0.020),
               (cx + x0 * 0.4, cy + tw, z + hh * 0.75),
               (cx + x1 * 0.5, cy - tw * 0.6, z + hh),
               (cx + x1, cy - tw * 0.2, z + hh * 0.55),
               (cx + x1 * 0.9, cy + tw * 0.3, z + 0.020)]
        w = mlib.tube_along("V_ToyW%d" % i, pth, mlib.circle(0.0028, 6), cname=C)
        mlib.smooth_shade(w, 50)
        mlib.set_mat(w, M("M_ToyBlue"))
        out.append(w)
        for j, k in enumerate((1, 2, 3)):
            px = pth[k]
            b = props.lathe("V_ToyB%d%d" % (i, j), [
                (0.0, 0.0), (0.016, 0.004), (0.018, 0.014),
                (0.014, 0.024), (0.0, 0.026)], 12, C)
            mlib.translate(b, (px[0], px[1], px[2] - 0.013))
            mlib.set_mat(b, M(cols[(i + j) % 4]))
            out.append(b)
    return out


def floor_lamp():
    """A slim uplighter beside the couch - and, once the lighting pass runs, a
    real source with a fixture to justify it."""
    out = []
    cx, cy = L.FLOOR_LAMP
    base = props.lathe("V_LampBase", [(0.0, 0.0), (0.135, 0.0), (0.138, 0.010),
                                      (0.120, 0.020), (0.026, 0.030),
                                      (0.024, 0.050), (0.0, 0.052)], 24, C)
    mlib.translate(base, (cx, cy, 0.0))
    mlib.set_mat(base, M("M_Steel"))
    out.append(base)
    pole = mlib.tube_along("V_LampPole", [(cx, cy, 0.040), (cx, cy, 1.640)],
                           mlib.circle(0.0145, 12), cname=C)
    mlib.smooth_shade(pole, 46)
    mlib.set_mat(pole, M("M_Steel"))
    out.append(pole)
    # An EMPIRE shade - wide at the bottom, narrow at the top.  The first pass
    # flared it the other way, which is a torchiere: correct as a fixture, but
    # on a slim pole beside a sofa it just reads as a lampshade put on upside
    # down, which is exactly how it looked.
    shade = props.lathe("V_LampShade", [(0.0, 0.0), (0.154, 0.0), (0.152, 0.007),
                                        (0.113, 0.198), (0.111, 0.205),
                                        (0.150, 0.011), (0.0, 0.011)], 30, C)
    mlib.translate(shade, (cx, cy, 1.500))
    mlib.set_mat(shade, M("M_LampShade"))
    out.append(shade)
    return out


# ================================================================== build

def build():
    mlib.purge("V_")
    mlib.coll(C)
    materials()
    couch()
    recliner("V_ReclA", L.REC_A[0], L.REC_A[1], L.REC_ROT_A)
    recliner("V_ReclB", L.REC_B[0], L.REC_B[1], L.REC_ROT_B)
    coffee_table()
    glass_table()
    side_table()
    rugs()
    entertainment()
    curtains()
    art()
    couch_dressing()
    window_wall()
    toy(L.COFFEE_C[0] + 0.40, L.COFFEE_C[1] + 0.02, 0.405)
    penguin(L.SOFA_C[0] - 0.70, L.SOFA_C[1] - 0.06, 0.428, rot=136.0)
    floor_lamp()
    return len([o for o in bpy.data.objects if o.name.startswith("V_")])
