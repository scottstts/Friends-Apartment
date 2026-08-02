"""f_beds - the two bedrooms and the bathroom.

None of these rooms appears in a reference photograph; all three are seen
through an open door from the living room, which decides how they are built.
What has to be right is the SILHOUETTE in a doorway and the tone of the light
coming back out of it - a bed, a lamp with a bulb in it, a window behind - so
the pieces are properly made but not detailed past what a doorway can show.
"""
import bpy, math, random
from mathutils import Vector
import mlib, mats, props, L

C = "Rooms"


def materials():
    mats.wood("M_BedWood", ['6A4526', '8C6236', '4A2C16'], ring=26.0, axis='X',
              rough=(0.26, 0.48), coat=0.26, grain_relief=0.10, scale=1.4)
    mats.wood("M_BedWood2", ['3E2A1C', '5C4026', '281810'], ring=30.0, axis='Y',
              rough=(0.28, 0.50), coat=0.22, grain_relief=0.10, scale=1.4)
    mats.fabric("M_Duvet1", '39506E', rough=0.76, weave=280.0, sheen=0.40)
    mats.fabric("M_Duvet2", '6E4A3A', rough=0.78, weave=260.0, sheen=0.35)
    mats.fabric("M_Sheet", 'E2DED0', rough=0.80, weave=340.0, sheen=0.45)
    mats.fabric("M_Mattress", 'D8D2C2', rough=0.84, weave=380.0, sheen=0.30)
    mats.enamel("M_Sanitary", 'F4F3EE', rough=0.055, tint='E6E6E0')
    mats.metal("M_BathChrome", 'DCE0E4', rough=0.06, grime=0.35)
    # silvered glass: a metal at almost no roughness, so the screen-space
    # trace gives it a real reflection instead of a flat grey plate
    mats.metal("M_MirrorGlass", 'F4F6F7', rough=0.015, grime=0.10)
    mats.paint("M_VanityPaint", 'D8D2C2', rough=0.30, coat=0.22)
    mats.stone("M_VanityTop", 'EDEAE0', vein='C6BEB0', rough=0.14, scale=2.0)
    mats.plastic("M_ShowerCurtain", 'DCE4E2', rough=0.42, coat=0.10, bump=0.14)
    mats.plastic("M_LampBase", '2A2622', rough=0.42)
    mats.paint("M_ShadeCream", 'E8E0CC', rough=0.62)
    mats.carpet("M_BedRug", '7A6A52', rough=0.94)
    mats.carpet("M_BedRug2", '4E5A66', rough=0.94)
    mats.carpet("M_BathMat", 'C8D2CE', rough=0.95, pile=1.3)
    mats.fabric("M_Towel", 'DCE4E2', rough=0.92, weave=240.0, sheen=0.30,
                bump=0.75, fuzz=1.2)
    mats.fabric("M_Towel2", '8AA8B4', rough=0.92, weave=240.0, sheen=0.30,
                bump=0.75, fuzz=1.2)
    mats.fabric("M_Clothes", '6A4A3C', rough=0.80, weave=300.0, sheen=0.35)
    mats.fabric("M_Clothes2", '3E5266', rough=0.80, weave=300.0, sheen=0.35)
    mats.wood("M_ChairWood", ['7A5230', '9C7044', '54351C'], ring=12.0,
              axis='Z', warp=0.8, rough=(0.26, 0.48), coat=0.24,
              grain_relief=0.07)
    mats.plastic("M_BinPlastic", '2A2C30', rough=0.44, coat=0.15)
    mats.plastic("M_BottleA", '2E6E6A', rough=0.18, coat=0.55)
    mats.plastic("M_BottleB", 'B8607A', rough=0.18, coat=0.55)
    mats.plastic("M_BottleC", 'D8C24E', rough=0.18, coat=0.55)
    mats.paper("M_PosterA", '9C4A34', rough=0.34, gloss=0.45)
    mats.paper("M_PosterB", '2E5A7A', rough=0.34, gloss=0.45)
    mats.plastic("M_DuckYellow", 'E8B71A', rough=0.28, coat=0.45)
    mats.plastic("M_DuckBill", 'E07A16', rough=0.32, coat=0.40)
    mats.plastic("M_DuckEye", '18140E', rough=0.22, coat=0.55)


def M(n):
    return mats.get(n)


# ================================================================== beds

def bed(name, cx, cy, rot, w=1.42, ln=2.02, duvet="M_Duvet1"):
    """A bed built facing +X (head at -X), then spun.  The duvet is a lofted
    surface with a turned-back top sheet, not a rounded box - the fall over the
    side is the only part of a made bed that reads from a doorway."""
    out = []
    hw = w * 0.5
    head = mlib.rounded_box(name + "_hb", -ln * 0.5 - 0.055, -hw - 0.030, 0.0,
                            -ln * 0.5 + 0.010, hw + 0.030, 0.860, r=0.024,
                            cname=C)
    mlib.bevel(head, 0.005, 3, 40)
    mlib.smooth_shade(head, 34)
    mlib.set_mat(head, M("M_BedWood"))
    out.append(head)
    foot = mlib.rounded_box(name + "_fb", ln * 0.5 - 0.010, -hw - 0.030, 0.0,
                            ln * 0.5 + 0.055, hw + 0.030, 0.430, r=0.024,
                            cname=C)
    mlib.bevel(foot, 0.005, 3, 40)
    mlib.smooth_shade(foot, 34)
    mlib.set_mat(foot, M("M_BedWood"))
    out.append(foot)
    rail = mlib.box(name + "_rl", -ln * 0.5, -hw - 0.028, 0.170, ln * 0.5,
                    hw + 0.028, 0.300, C)
    mlib.bevel(rail, 0.004, 2, 42)
    mlib.set_mat(rail, M("M_BedWood"))
    out.append(rail)

    matt = mlib.rounded_box(name + "_mt", -ln * 0.5 + 0.010, -hw, 0.300,
                            ln * 0.5 - 0.010, hw, 0.520, r=0.045, cname=C)
    mlib.bevel(matt, 0.006, 3, 40)
    mlib.smooth_shade(matt, 34)
    mlib.set_mat(matt, M("M_Mattress"))
    out.append(matt)

    # duvet: a slab over the mattress that falls past it on three sides
    lv = [(-ln * 0.5 + 0.16, hw + 0.010, 0.560),
          (-ln * 0.5 + 0.30, hw + 0.030, 0.585),
          (0.10, hw + 0.045, 0.575),
          (ln * 0.5 - 0.10, hw + 0.045, 0.565),
          (ln * 0.5 + 0.030, hw + 0.030, 0.520)]
    rings = []
    for (xx, ry, zz) in lv:
        # a 230 mm section, so the duvet FALLS over the side of the mattress
        # instead of sitting on it as a slab - that fall is the only part of a
        # made bed that reads from a doorway
        rings.append([(xx, a, zz + b) for (a, b) in
                      mlib.rounded_rect(ry * 2, 0.230, 0.072, 6)])
    dv = mlib.loft(name + "_dv", rings, close_u=False, close_v=True, cname=C,
                   cap_start=True, cap_end=True)
    mlib.bevel(dv, 0.006, 2, 46)
    mlib.smooth_shade(dv, 42)
    mlib.set_mat(dv, M(duvet))
    out.append(dv)
    turn = mlib.rounded_box(name + "_tn", -ln * 0.5 + 0.16, -hw - 0.012, 0.520,
                            -ln * 0.5 + 0.34, hw + 0.012, 0.585, r=0.028,
                            cname=C)
    mlib.bevel(turn, 0.005, 3, 40)
    mlib.smooth_shade(turn, 34)
    mlib.set_mat(turn, M("M_Sheet"))
    out.append(turn)

    for s in (-1, 1):
        pw = props.pillow(name + "_pw%d" % (s > 0), 0.62, 0.40, 0.150, cname=C)
        mlib.rot_x(pw, math.radians(12.0))
        mlib.rotate_z(pw, math.pi * 0.5)
        mlib.translate(pw, (-ln * 0.5 + 0.28, s * hw * 0.45, 0.545))
        mlib.set_mat(pw, M("M_Sheet"))
        out.append(pw)

    grp = mlib.join(out, name, C)
    mlib.rotate_z(grp, math.radians(rot))
    # 10 mm up: the bed stands ON its rug, and left at floor level its own
    # base plane is coplanar with the rug's underside
    mlib.translate(grp, (cx, cy, 0.024))
    return [grp]


def nightstand(name, cx, cy, rot=0.0, lamp=True):
    out = []
    w, d, h = 0.46, 0.40, 0.585
    body = mlib.box(name + "_b", -w * 0.5, -d * 0.5, 0.095, w * 0.5, d * 0.5,
                    h, C)
    mlib.bevel(body, 0.004, 2, 42)
    mlib.set_mat(body, M("M_BedWood2"))
    out.append(body)
    for i in range(2):
        z = 0.125 + i * 0.225
        dr = mlib.box(name + "_d%d" % i, -w * 0.5 + 0.020, -d * 0.5 - 0.018, z,
                      w * 0.5 - 0.020, -d * 0.5 + 0.002, z + 0.195, C)
        mlib.bevel(dr, 0.004, 3, 40)
        mlib.set_mat(dr, M("M_BedWood2"))
        out.append(dr)
        pl = props.bar_pull(name + "_p%d" % i, 0.14, cname=C, r=0.0055,
                            stand=0.026)
        mlib.translate(pl, (0.0, -d * 0.5 - 0.018, z + 0.098))
        mlib.set_mat(pl, M("M_BathChrome"))
        out.append(pl)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        lg = mlib.box(name + "_l", sx * (w * 0.5 - 0.035) - 0.018,
                      sy * (d * 0.5 - 0.035) - 0.018, 0.0,
                      sx * (w * 0.5 - 0.035) + 0.018,
                      sy * (d * 0.5 - 0.035) + 0.018, 0.100, C)
        mlib.bevel(lg, 0.003, 2, 42)
        mlib.set_mat(lg, M("M_BedWood2"))
        out.append(lg)
    if lamp:
        base = props.lathe(name + "_lb", [(0.0, 0.0), (0.072, 0.0),
                                          (0.068, 0.014), (0.030, 0.040),
                                          (0.024, 0.055), (0.036, 0.150),
                                          (0.028, 0.210), (0.0, 0.212)], 20, C)
        mlib.translate(base, (0.0, 0.0, h))
        mlib.set_mat(base, M("M_LampBase"))
        out.append(base)
        # An EMPIRE shade: WIDE AT THE BOTTOM, narrowing to the top ring.  The
        # first pass had the taper the other way up, which on a table lamp is
        # not a style, it is a shade put on upside down.
        sh = props.lathe(name + "_ls", [(0.0, 0.0), (0.130, 0.0), (0.128, 0.006),
                                        (0.092, 0.186), (0.090, 0.192),
                                        (0.126, 0.010), (0.0, 0.010)], 26, C)
        mlib.translate(sh, (0.0, 0.0, h + 0.190))
        mlib.set_mat(sh, M("M_ShadeCream"))
        out.append(sh)
    grp = mlib.join(out, name, C)
    if rot:
        mlib.rotate_z(grp, math.radians(rot))
    mlib.translate(grp, (cx, cy, 0.0))
    return [grp]


def dresser(name, cx, cy, rot, w=1.16, d=0.48, h=0.82, drawers=3):
    out = []
    body = mlib.box(name + "_b", -w * 0.5, -d * 0.5, 0.090, w * 0.5, d * 0.5,
                    h, C)
    mlib.bevel(body, 0.004, 2, 42)
    mlib.set_mat(body, M("M_BedWood2"))
    out.append(body)
    tp = props.worktop(name + "_t", -w * 0.5 - 0.018, -d * 0.5 - 0.018,
                       w * 0.5 + 0.018, d * 0.5 + 0.018, h + 0.026, th=0.026,
                       r=0.008, cname=C)
    mlib.set_mat(tp, M("M_BedWood"))
    out.append(tp)
    span = (h - 0.135) / drawers
    for i in range(drawers):
        z = 0.115 + i * span
        dr = mlib.box(name + "_d%d" % i, -w * 0.5 + 0.022, -d * 0.5 - 0.018, z,
                      w * 0.5 - 0.022, -d * 0.5 + 0.002, z + span - 0.014, C)
        mlib.bevel(dr, 0.004, 3, 40)
        mlib.set_mat(dr, M("M_BedWood2"))
        out.append(dr)
        for s in (-1, 1):
            pl = props.bar_pull(name + "_p%d%d" % (i, s > 0), 0.16, cname=C,
                                r=0.006, stand=0.030)
            mlib.translate(pl, (s * w * 0.24, -d * 0.5 - 0.018,
                                z + (span - 0.014) * 0.5))
            mlib.set_mat(pl, M("M_BathChrome"))
            out.append(pl)
    plin = mlib.box(name + "_pl", -w * 0.5 + 0.030, -d * 0.5 + 0.030, 0.0,
                    w * 0.5 - 0.030, d * 0.5, 0.092, C)
    mlib.bevel(plin, 0.003, 2, 42)
    mlib.set_mat(plin, M("M_BedWood2"))
    out.append(plin)
    grp = mlib.join(out, name, C)
    mlib.rotate_z(grp, math.radians(rot))
    mlib.translate(grp, (cx, cy, 0.0))
    return [grp]


def bedrooms():
    out = []
    # Joey - bed head against the west wall, dresser on the south wall
    out += bed("R_JoeyBed", L.JO_X[0] + 1.12, 0.62, 0.0, w=1.44, ln=2.02,
               duvet="M_Duvet2")
    out += nightstand("R_JoeyNs", L.JO_X[0] + 0.30, 1.72, rot=-90.0)
    # dresser() puts the drawer fronts on its -Y face, so a chest standing
    # against a SOUTH wall has to be spun through 180 and one against a NORTH
    # wall left at zero.  Both were the wrong way round, which is why the photo
    # frame standing on each one leaned out into the room instead of back
    # against the wall - the tray is built leaning back and was then turned
    # round with the chest.
    out += dresser("R_JoeyDr", L.JO_X[0] + 1.55, L.JO_Y[0] + 0.28, 180.0)
    # Chandler - the same arrangement mirrored north
    out += bed("R_ChanBed", L.CH_X[0] + 1.12, 4.55, 0.0, w=1.44, ln=2.02,
               duvet="M_Duvet1")
    out += nightstand("R_ChanNs", L.CH_X[0] + 0.30, 3.42, rot=-90.0)
    out += dresser("R_ChanDr", L.CH_X[0] + 1.70, L.CH_Y[1] - 0.30, 0.0)

    # ---- dressing, so a doorway view has something in it besides a bed ----
    # beside the bed, not under it - the bed head is against the west wall and
    # the mattress runs 2 m east, so the only floor a rug can be SEEN on is the
    # strip at its foot
    out += bed_rug("R_JoeyRug", -1.05, 0.62, 1.10, 1.85, "M_BedRug")
    out += bed_rug("R_ChanRug", -1.05, 4.55, 1.10, 1.85, "M_BedRug2")
    out += chair("R_JoeyChair", L.JO_X[1] - 0.52, L.JO_Y[0] + 0.62, rot=-118.0,
                 clothes="M_Clothes")
    # chair() puts the back at +Y, so it faces -Y at rot 0.  132 turned its
    # back on the room; -48 is the same angle spun through 180.
    out += chair("R_ChanChair", L.CH_X[1] - 0.52, L.CH_Y[1] - 0.62, rot=-48.0,
                 clothes="M_Clothes2")
    out += bin_can("R_JoeyBin", L.JO_X[0] + 0.36, L.JO_Y[0] + 0.34)
    out += bin_can("R_ChanBin", L.CH_X[0] + 0.36, L.CH_Y[1] - 0.34)
    out += dresser_top("R_JoeyTop", L.JO_X[0] + 1.55, L.JO_Y[0] + 0.28, 0.848,
                       rot=180.0)
    out += dresser_top("R_ChanTop", L.CH_X[0] + 1.70, L.CH_Y[1] - 0.30, 0.848)
    # clear of JO_WIN (y 0.05..0.90) - at 0.92 the frame overlapped the glass
    out += wall_poster("R_JoeyPost", 1.78, 1.62, 'W', L.JO_X[0], 0.62, 0.88,
                       "M_PosterA")
    out += wall_poster("R_ChanPost", 5.42, 1.62, 'W', L.CH_X[0], 0.62, 0.88,
                       "M_PosterB")
    return out


def chair(name, cx, cy, rot=0.0, clothes=None):
    """A plain side chair - four tapered legs, a seat with an eased edge, and a
    back with two slats.  With something thrown over the back it does more to
    make a bedroom read as lived in than any amount of extra furniture."""
    out = []
    sw, sd, sh = 0.420, 0.400, 0.450
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        lx, ly = sx * (sw * 0.5 - 0.030), sy * (sd * 0.5 - 0.030)
        top = sh if sy > 0 else sh
        lg = props.taper_leg(name + "_lg", top, top=0.038, bot=0.026, cname=C,
                             r=0.004)
        mlib.translate(lg, (lx, ly, 0.0))
        mlib.set_mat(lg, M("M_ChairWood"))
        out.append(lg)
    seat = props.worktop(name + "_st", -sw * 0.5, -sd * 0.5, sw * 0.5,
                         sd * 0.5, sh + 0.032, th=0.032, r=0.014, cname=C)
    mlib.set_mat(seat, M("M_ChairWood"))
    out.append(seat)
    for s_ in (-1, 1):
        st = props.taper_leg(name + "_bk", 0.470, top=0.030, bot=0.036, cname=C,
                             r=0.004)
        mlib.translate(st, (s_ * (sw * 0.5 - 0.032), sd * 0.5 - 0.030,
                            sh + 0.030))
        mlib.set_mat(st, M("M_ChairWood"))
        out.append(st)
    for zz in (0.300, 0.412):
        sl = mlib.box(name + "_sl", -sw * 0.5 + 0.024, sd * 0.5 - 0.046,
                      sh + 0.030 + zz, sw * 0.5 - 0.024, sd * 0.5 - 0.018,
                      sh + 0.030 + zz + 0.062, C)
        mlib.bevel(sl, 0.004, 2, 42)
        mlib.set_mat(sl, M("M_ChairWood"))
        out.append(sl)
    if clothes:
        cl = props.drape(name + "_cl", -sw * 0.5 + 0.05, sw * 0.5 - 0.05,
                         sd * 0.5 - 0.030, sh - 0.16, sh + 0.470,
                         folds=5, amp=0.030, cname=C, nz=10, seed=23, th=0.006)
        mlib.set_mat(cl, M(clothes))
        out.append(cl)
    grp = mlib.join(out, name, C)
    if rot:
        mlib.rotate_z(grp, math.radians(rot))
    mlib.translate(grp, (cx, cy, 0.0))
    return [grp]


def bin_can(name, cx, cy, r=0.135, h=0.400):
    ob = props.lathe(name, [(0.0, 0.0), (r * 0.86, 0.0), (r * 0.90, 0.012),
                            (r, h - 0.020), (r * 1.04, h), (r * 0.98, h),
                            (r * 0.94, h - 0.020), (r * 0.82, 0.014),
                            (0.0, 0.010)], 24, C)
    mlib.translate(ob, (cx, cy, 0.0))
    mlib.set_mat(ob, M("M_BinPlastic"))
    return [ob]


def dresser_top(name, cx, cy, z, rot=0.0):
    """A tray of bottles, a photo frame and a stack of books - what the top of
    a chest of drawers actually carries."""
    out = []
    rnd = random.Random(51)
    for i, mat in enumerate(("M_BottleA", "M_BottleB", "M_BottleC")):
        b = props.bottle(name + "_bt%d" % i, cx - 0.20 + i * 0.085, cy + 0.02,
                         z, r=0.028, h=rnd.uniform(0.115, 0.165), neck=0.010,
                         cname=C)
        mlib.set_mat(b, M(mat))
        out.append(b)
    fr = props.frame_art(name + "_fr", 0.150, 0.195, depth=0.018, cname=C,
                         moulding=0.018, standoff=0.0)
    mlib.set_mat(fr[0], M("M_BedWood2"))
    mlib.set_mat(fr[1], M("M_PosterB"))
    for o in fr:
        mlib.rot_x(o, math.radians(-14.0))
        mlib.translate(o, (cx + 0.12, cy + 0.06, z + 0.100))
        out.append(o)
    for i in range(3):
        bk = mlib.box(name + "_bk%d" % i, cx + 0.24, cy - 0.09, z + i * 0.028,
                      cx + 0.40, cy + 0.09, z + i * 0.028 + 0.026, C)
        mlib.bevel(bk, 0.002, 2, 44)
        mlib.rotate_z(bk, rnd.uniform(-0.15, 0.15), (cx + 0.32, cy))
        mlib.set_mat(bk, M(["M_Duvet1", "M_Duvet2", "M_Sheet"][i]))
        out.append(bk)
    grp = mlib.join(out, name, C)
    if rot:
        mlib.rotate_z(grp, math.radians(rot), (cx, cy))
    return [grp]


def wall_poster(name, u, z, wall, at, w, h, mat):
    a = props.frame_art(name, w, h, depth=0.024, cname=C, moulding=0.026,
                        standoff=0.019)
    mlib.set_mat(a[0], M("M_BedWood2"))
    mlib.set_mat(a[1], M(mat))
    props.wall_place(a, wall, u, z, at)
    return a


def bed_rug(name, cx, cy, w, d, mat, rot=0.0):
    def reg(u, v):
        return 1 if (u < 0.055 or u > 0.945 or v < 0.075 or v > 0.925) else 0
    return [props.rug(name, cx, cy, w, d, reg,
                      [M(mat), M("M_BedRug2" if mat == "M_BedRug" else "M_BedRug")],
                      cname=C, cell=0.035, th=0.012, rot=rot, z0=0.012)]


# ================================================================== bathroom

# The wall tiling stands 13 mm proud of the plaster, so nothing hung on a
# bathroom wall may be placed on the wall LINE - it lands behind the tiles.
TILE_F = 0.013
BFL = 0.0145       # the bathroom floor tile's top - this room's datum
TUBH = 0.560       # the bath's rim, above its OWN underside


def _slab_with_hole(name, x0, y0, x1, y1, z0, z1, cx, cy, ax, ay, n=56,
                    cname=C):
    """A rectangular slab with an OVAL hole through it, as one manifold solid.

    The cut-out has to be the shape of the thing dropped into it.  A round
    basin over a rectangular hole leaves the hole's four corners sticking out
    past the rim, and they read as four black notches round the bowl - which
    is exactly what they did.

    Built as a radial ring: for every angle, the inner point is on the ellipse
    and the outer point is where that ray leaves the rectangle, so the top and
    bottom faces are one clean band of quads.  The four corner angles are
    forced into the sample list, so the slab's own corners stay square instead
    of being chamfered off by whichever sample happened to land near them.
    """
    cor = [math.atan2(b - cy, a - cx)
           for (a, b) in ((x1, y1), (x0, y1), (x0, y0), (x1, y0))]
    angs = sorted(set([math.tau * k / n for k in range(n)]
                      + [(t + math.tau) % math.tau for t in cor]))
    outer, inner = [], []
    for t in angs:
        c, s = math.cos(t), math.sin(t)
        k = 1e9
        if abs(c) > 1e-9:
            k = min(k, ((x1 - cx) if c > 0 else (x0 - cx)) / c)
        if abs(s) > 1e-9:
            k = min(k, ((y1 - cy) if s > 0 else (y0 - cy)) / s)
        outer.append((cx + c * k, cy + s * k))
        inner.append((cx + ax * c, cy + ay * s))
    m = len(angs)
    verts = ([(p[0], p[1], z0) for p in outer] + [(p[0], p[1], z0) for p in inner]
             + [(p[0], p[1], z1) for p in outer] + [(p[0], p[1], z1) for p in inner])
    O0, I0, O1, I1 = 0, m, 2 * m, 3 * m
    faces = []
    for k in range(m):
        k2 = (k + 1) % m
        faces.append((O0 + k, O0 + k2, I0 + k2, I0 + k))    # bottom ring
        faces.append((O1 + k, I1 + k, I1 + k2, O1 + k2))    # top ring
        faces.append((O0 + k, O1 + k, O1 + k2, O0 + k2))    # outer edge
        faces.append((I0 + k, I0 + k2, I1 + k2, I1 + k))    # hole wall
    ob = mlib.mesh_obj(name, verts, faces, cname)
    mlib.recalc_normals(ob)
    mlib.bevel(ob, 0.004, 3, 40)
    mlib.smooth_shade(ob, 34)
    return ob


def vanity():
    """The vanity unit: an open carcass with two doors, a stone top with a hole
    cut in it, and a self-rimming basin dropped through the hole.

    The basin used to be a bowl parked on the counter's front-left corner with
    a third of it hanging over the edge, which is what it looked like."""
    out = []
    vx1, vx0 = L.BA_X[1], L.BA_X[1] - 0.560
    vy0, vy1 = L.BA_VAN_Y
    S = 0.018
    # A carcass, not a solid block - the basin hangs 140 mm below the counter
    # and there has to be somewhere for it to hang.
    car = mlib.join([
        mlib.box("R_Van_l", vx0, vy0, 0.100, vx1, vy0 + S, 0.840, C),
        mlib.box("R_Van_r", vx0, vy1 - S, 0.100, vx1, vy1, 0.840, C),
        mlib.box("R_Van_bk", vx1 - S, vy0 + S, 0.100, vx1, vy1 - S, 0.840, C),
        mlib.box("R_Van_bt", vx0, vy0 + S, 0.100, vx1 - S, vy1 - S, 0.118, C),
        mlib.box("R_Van_rl", vx0, vy0 + S, 0.790, vx0 + S, vy1 - S, 0.840, C),
    ], "R_Vanity", C)
    mlib.bevel(car, 0.003, 2, 42)
    mlib.set_mat(car, M("M_VanityPaint"))
    out.append(car)
    dw = (vy1 - vy0) * 0.5 - 0.020
    for i in range(2):
        a = vy0 + 0.012 + i * ((vy1 - vy0) * 0.5)
        d = props.cab_door("R_VanDoor%d" % i, dw, 0.640, th=0.019, rail=0.052,
                           inset=0.014, proud=0.007, cname=C)
        # front face points along local -Y; -90 takes that to -X, which is the
        # way this run faces, and the door then grows back INTO the carcass
        mlib.rotate_z(d, -math.pi * 0.5)
        mlib.translate(d, (vx0 - 0.004, a + dw, 0.150))
        mlib.set_mat(d, M("M_VanityPaint"))
        out.append(d)
        kb = props.knob("R_VanKnob%d" % i, r=0.014, cname=C, stem=0.012)
        # face_x puts the knob's BASE at `at`, so that is the door's front face
        # (a hair inside it), not a point out in front of the door
        props.face_x(kb, -1.0, (vx0 - 0.002, a + (0.045 if i else dw - 0.045),
                                0.700))
        mlib.set_mat(kb, M("M_BathChrome"))
        out.append(kb)

    bx, by = L.BA_BASIN
    ZT = 0.876
    # the cut-out is an ellipse a few millimetres bigger than the widest part
    # of the bowl below the rim, so the bowl passes through and the rim laps it
    vt = _slab_with_hole("R_VanTop", vx0 - 0.020, vy0 - 0.020, vx1,
                         vy1 + 0.020, ZT - 0.036, ZT, bx, by, 0.176, 0.141)
    mlib.set_mat(vt, M("M_VanityTop"))
    out.append(vt)

    # Self-rimming basin: the bowl necks in to 168 so it passes through a 174
    # hole, then the rim flares out to 212 and laps the stone.  Nothing under
    # the rim is wider than the hole, which is what "drop-in" means.
    basin = props.lathe("R_Basin", [
        (0.0, 0.0), (0.060, 0.004), (0.115, 0.040), (0.150, 0.086),
        (0.163, 0.116), (0.168, 0.128), (0.212, 0.134), (0.213, 0.146),
        (0.204, 0.150), (0.164, 0.140), (0.158, 0.126), (0.144, 0.086),
        (0.106, 0.040), (0.052, 0.014), (0.0, 0.012)], 36, C)
    mlib.scale_mesh(basin, (1.0, 0.80, 1.0))
    mlib.translate(basin, (bx, by, ZT - 0.134 - 0.004))
    mlib.set_mat(basin, M("M_Sanitary"))
    out.append(basin)
    plug = props.lathe("R_BasinPlug", [(0.0, 0.0), (0.022, 0.0), (0.022, 0.004),
                                       (0.0, 0.004)], 18, C)
    mlib.translate(plug, (bx, by, ZT - 0.126))
    mlib.set_mat(plug, M("M_BathChrome"))
    out.append(plug)

    tx = vx1 - 0.058
    tapb = props.lathe("R_BasinTap", [(0.0, 0.0), (0.036, 0.0), (0.034, 0.010),
                                      (0.019, 0.026), (0.018, 0.098),
                                      (0.024, 0.106), (0.0, 0.108)], 20, C)
    mlib.translate(tapb, (tx, by, ZT))
    mlib.set_mat(tapb, M("M_BathChrome"))
    out.append(tapb)
    tapn = mlib.tube_along("R_BasinSpout", [
        (tx, by, ZT + 0.104), (tx - 0.062, by, ZT + 0.126),
        (tx - 0.118, by, ZT + 0.092)],
        mlib.circle(0.014, 12), cname=C)
    mlib.smooth_shade(tapn, 48)
    mlib.set_mat(tapn, M("M_BathChrome"))
    out.append(tapn)
    for s_ in (-1, 1):
        hd = props.lathe("R_BasinHd%d" % (s_ > 0), [
            (0.0, 0.0), (0.026, 0.0), (0.024, 0.008), (0.010, 0.014),
            (0.009, 0.038), (0.020, 0.046), (0.019, 0.056), (0.0, 0.058)],
            16, C)
        mlib.translate(hd, (tx, by + s_ * 0.086, ZT))
        mlib.set_mat(hd, M("M_BathChrome"))
        out.append(hd)

    # Hung PROUD of the tiling, not on the wall line - let into the plaster it
    # sits behind 13 mm of ceramic and the tile grid prints straight over it.
    mir = props.frame_art("R_Mirror", 1.00, 0.78, depth=0.030, cname=C,
                          moulding=0.038, standoff=TILE_F + 0.006)
    mlib.set_mat(mir[0], M("M_VanityPaint"))
    mlib.set_mat(mir[1], M("M_MirrorGlass"))
    props.wall_place(mir, 'E', by, 1.520, L.BA_X[1])
    out += mir
    mirror_probe(by, 1.520, L.BA_X[1] - TILE_F - 0.010)
    return out


def mirror_probe(u, z, at):
    """A planar reflection probe over the mirror.

    A metal at 0.015 roughness has nothing to reflect but the screen, and where
    the screen trace finds nothing EEVEE falls back to the WORLD - so the
    mirror came back as a panel of gradient sky hanging on a bathroom wall.  A
    reflection plane gives it the room instead, which is the only thing that
    makes a mirror read as a mirror."""
    bpy.ops.object.lightprobe_add(type='PLANE', location=(at, u, z))
    pr = bpy.context.object
    pr.name = "R_MirrorProbe"
    # the default plane's normal is +Z; Ry(-90) takes that to -X, which is the
    # way this wall faces
    pr.rotation_euler = (0.0, -math.pi * 0.5, 0.0)
    pr.scale = (0.86, 1.06, 1.0)
    pr.data.influence_distance = 0.55
    mlib.put(pr, C)
    return pr


def _pan_ring(hw, yb, yf, z, n=44, waist=0.38):
    """One horizontal section through a china pan.  Not an ellipse and not a
    rounded rectangle: an EGG.  The widest line sits back of centre (`waist` of
    the way from the back), the tail behind it is blunt and the nose in front of
    it is long and tapered, which is what makes a lavatory read as a lavatory
    rather than as a lathed bollard."""
    cy = yb + (yf - yb) * waist
    ring = []
    for i in range(n):
        a = math.tau * i / n
        c = math.cos(a)
        ring.append((hw * math.sin(a),
                     cy + (yf - cy) * c if c >= 0 else cy + (cy - yb) * c,
                     z))
    return ring


def wc():
    """A close-coupled two-piece WC.

    Built facing +Y with its tank at -Y, then turned a quarter turn so it faces
    the room with the tank against the tiled east wall.  The previous one was
    lofted from rounded rectangles, which is round-cornered-oblong in plan - and
    no lavatory is either an oblong or a circle.  This one is lofted from real
    egg sections: a flared foot, a waisted ankle, an egg-shaped bowl hollowed
    down to the trap, a squared casting shelf for the tank to bolt to, seat and
    lid following the rim's own outline, trip lever and supply.
    """
    # One vertical stack of numbers, so nothing can drift out of register:
    # rim -> seat -> lid -> the shelf the closed lid stops against -> tank.
    RIM = 0.395
    SEAT_T, LID_T = 0.019, 0.026
    SHELF_Z = RIM + SEAT_T + LID_T + 0.007      # 0.447
    TANK_Z, TLID_Z = SHELF_Z + 0.310, SHELF_Z + 0.340
    HW, YB, YF = 0.185, -0.118, 0.352           # rim, at its widest: 0.47 long
    SY = -0.254                                 # centre of tank/shelf in Y
    WALL = -0.364                               # the tile face, in this frame
    parts = []
    rings = [
        # skirt -> waisted ankle -> bowl.  The rim's outline sits forward of the
        # skirt's, so the china tucks back under itself towards the wall the way
        # a cast trapway does instead of standing on a straight lathed column.
        _pan_ring(0.118, -0.290, 0.150, 0.000),
        _pan_ring(0.112, -0.288, 0.144, 0.024),
        _pan_ring(0.090, -0.280, 0.110, 0.130),
        _pan_ring(0.100, -0.276, 0.138, 0.208),
        _pan_ring(0.140, -0.240, 0.226, 0.284),
        _pan_ring(0.174, -0.172, 0.314, 0.356),
        # the top ring is repeated so the lip reads as a hard edge rather than
        # rolling over into the flare below it
        _pan_ring(HW, YB, YF, RIM - 0.014),
        _pan_ring(HW, YB, YF, RIM),
        # ...and back down the inside to the trap outlet
        _pan_ring(0.152, YB + 0.022, 0.282, RIM - 0.004),
        _pan_ring(0.132, YB + 0.038, 0.252, 0.347),
        _pan_ring(0.102, YB + 0.064, 0.192, 0.282),
        _pan_ring(0.064, YB + 0.098, 0.118, 0.228),
        _pan_ring(0.032, YB + 0.122, 0.062, 0.202),
    ]
    pan = mlib.loft("R_WcPan", rings, close_v=True, cname=C,
                    cap_start=True, cap_end=True)
    mlib.smooth_shade(pan, 44)
    parts.append(pan)
    # The plinth the tank bolts down onto, lofted rather than boxed: narrow and
    # deep where it grows out of the skirt, spreading at the top.  Deliberately
    # narrower than the tank, so the tank overhangs it the way a real one does
    # and there is somewhere underneath for the supply to land.
    shelf = mlib.loft("R_WcShelf", [
        # every ring flush with the tank's back face, so the plinth cannot
        # creep out behind the tank and into the wall
        [(x, y - 0.250, 0.170) for (x, y) in mlib.rounded_rect(0.196, 0.204, 0.046, 4)],
        [(x, y - 0.246, 0.290) for (x, y) in mlib.rounded_rect(0.250, 0.212, 0.044, 4)],
        [(x, y - 0.257, 0.396) for (x, y) in mlib.rounded_rect(0.310, 0.190, 0.036, 4)],
        [(x, y - 0.264, SHELF_Z) for (x, y) in mlib.rounded_rect(0.330, 0.176, 0.030, 4)],
    ], close_v=True, cname=C, cap_start=True, cap_end=True)
    mlib.bevel(shelf, 0.008, 2, 52)
    mlib.smooth_shade(shelf, 46)
    parts.append(shelf)
    # ...and the low flat between the rim and the plinth that the seat's hinge
    # bolts pass through.  Without it the seat hinges onto thin air.
    flat = mlib.prism("R_WcHFlat", mlib.rounded_rect(0.320, 0.090, 0.026, 3),
                      0.320, RIM, C)
    mlib.translate(flat, (0.0, -0.150, 0.0))
    mlib.bevel(flat, 0.008, 2, 50)
    parts.append(flat)
    # tank, and its lid overhanging on every side
    tank = mlib.prism("R_WcTank", mlib.rounded_rect(0.428, 0.196, 0.026, 4),
                      SHELF_Z - 0.006, TANK_Z, C)
    mlib.translate(tank, (0.0, SY, 0.0))
    mlib.bevel(tank, 0.012, 3, 46)
    parts.append(tank)
    tlid = mlib.prism("R_WcTankLid",
                      mlib.rounded_rect(0.452, 0.220, 0.030, 4), TANK_Z,
                      TLID_Z, C)
    mlib.translate(tlid, (0.0, SY, 0.0))
    mlib.bevel(tlid, 0.009, 3, 46)
    parts.append(tlid)
    body = mlib.join(parts, "R_Wc", C)
    mlib.set_mat(body, M("M_Sanitary"))

    # ------------------------------------------------------------ seat + lid
    # Both follow the rim's OWN outline, so they overhang it by a constant few
    # millimetres the whole way round instead of by an eyeballed offset.
    plan = [(v[0], v[1]) for v in _pan_ring(HW, YB, YF, 0.0)]
    cyw = YB + (YF - YB) * 0.38                 # the outline's own centre

    def ring2d(k, dy=0.0):
        return [(x * k, cyw + (y - cyw) * k + dy) for (x, y) in plan]

    # The seat only just stands proud of the china - overhang it far enough to
    # hide the rim and seat, lid and rim read as three stacked discs of the same
    # thickness.  The lid is lofted with a slight dome so its edge tapers
    # instead of showing as a second flat band under the first.
    seat = mlib.prism("R_WcSeat", ring2d(1.008), RIM, RIM + SEAT_T, C)
    hole = mlib.prism("R_WcSeatCut", ring2d(0.660, 0.030), RIM - 0.02,
                      RIM + 0.06, C)
    mlib.boolean(seat, hole)
    mlib.bevel(seat, 0.006, 3, 46)
    mlib.smooth_shade(seat, 40)
    slid = mlib.loft("R_WcLid", [
        [(x, y, RIM + SEAT_T) for (x, y) in ring2d(1.018)],
        [(x, y, RIM + SEAT_T + LID_T * 0.62) for (x, y) in ring2d(1.014)],
        [(x, y, RIM + SEAT_T + LID_T) for (x, y) in ring2d(0.930)],
    ], close_v=True, cname=C, cap_start=True, cap_end=True)
    mlib.bevel(slid, 0.008, 3, 52)
    mlib.smooth_shade(slid, 44)
    seatp = mlib.join([seat, slid], "R_WcSeatLid", C)
    mlib.set_mat(seatp, M("M_Sanitary"))

    # ------------------------------------------------------- chrome fittings
    TKF = SY + 0.098                            # tank's front face
    fit = []
    # trip lever: escutcheon on the tank's left cheek and a lever raked down
    esc = mlib.revolve("R_WcEsc", [(0.0, 0.0), (0.020, 0.0), (0.019, 0.014),
                                   (0.010, 0.020), (0.0, 0.020)], 14, cname=C)
    mlib.rot_x(esc, -math.pi / 2)
    mlib.translate(esc, (-0.128, TKF - 0.004, TANK_Z - 0.072))
    fit.append(esc)
    fit.append(mlib.tube_along("R_WcLever",
                               [(-0.128, TKF + 0.016, TANK_Z - 0.072),
                                (-0.128, TKF + 0.024, TANK_Z - 0.074),
                                (-0.052, TKF + 0.028, TANK_Z - 0.102)],
                               mlib.rounded_rect(0.022, 0.008, 0.004, 2), C))
    # angle stop screwed to the wall behind, and the supply up to the tank.
    # It stands outboard of the tank lid so nothing is buried in the china.
    stop = mlib.revolve("R_WcStop",
                        [(0.0, 0.0), (0.022, 0.0), (0.022, 0.052),
                         (0.030, 0.058), (0.030, 0.070), (0.0, 0.070)], 14,
                        cname=C)
    mlib.rot_x(stop, -math.pi / 2)          # flange on the plaster, body forward
    mlib.translate(stop, (-0.242, WALL, 0.190))
    fit.append(stop)
    sup = mlib.bez((WALL + 0.068, 0.190), (WALL + 0.200, 0.198),
                   (WALL + 0.160, 0.340), (WALL + 0.076, SHELF_Z - 0.024), n=10)
    n = len(sup) - 1
    fit.append(mlib.tube_along("R_WcSupply",
                               [(-0.242 + 0.057 * (i / n), q[0], q[1])
                                for i, q in enumerate(sup)],
                               mlib.circle(0.0095, 10), C))
    nut = mlib.revolve("R_WcNut", [(0.0, 0.0), (0.021, 0.0), (0.021, 0.030),
                                   (0.0, 0.030)], 12, cname=C)
    mlib.translate(nut, (-0.185, sup[-1][0], SHELF_Z - 0.034))
    fit.append(nut)
    # seat hinge: the two barrels that sit on the flat behind the seat
    for sx in (-0.076, 0.076):
        h = mlib.revolve("R_WcHinge", [(0.0, 0.0), (0.013, 0.0), (0.013, 0.054),
                                       (0.0, 0.054)], 12, cname=C)
        mlib.rot_y(h, math.pi / 2)
        mlib.translate(h, (sx - 0.027, -0.150, RIM + 0.013))
        fit.append(h)
    fo = mlib.join(fit, "R_WcFittings", C)
    mlib.smooth_shade(fo, 38)
    mlib.set_mat(fo, M("M_BathChrome"))

    # A quarter turn puts local +Y (the way it faces) onto world -X, which is
    # into the room, and local -Y onto the east wall.  cx is set off the tank
    # LID's back, not the tank's - the lid overhangs the cistern by 12 mm and
    # it is the lid that would end up buried in the tiling.
    face = L.BA_X[1] - TILE_F
    cx, cy = face - 0.366, L.BA_WC[1]
    out = [body, seatp, fo]
    for o in out:
        mlib.rotate_z(o, math.pi * 0.5)
        mlib.translate(o, (cx, cy, BFL))
    return out


def _duck_ring(px, pz, tx, tz, hw, dn, up, n=30):
    """One section through the duck, held PERPENDICULAR to a curved spine.

    The section is a true ellipse whose centre is offset off the spine, so it
    reaches `up` above and `dn` below it while staying smooth all the way
    round.  Splitting the radius at the equator - an egg - creases along the
    flank, which shows badly on moulded rubber.

    Holding the section square to the spine is what lets one surface run from
    the tail through the breast and up the neck into the head.  Built as three
    solids butted together, the neck is a cylinder with its cap ring showing as
    a hard collar between two lumps, which is exactly how it looked.
    """
    ux, uz = tz, -tx                       # spine tangent turned up
    o, h = (up - dn) * 0.5, (up + dn) * 0.5
    ring = []
    for i in range(n):
        a = math.tau * i / n
        d = o + h * math.cos(a)
        ring.append((px + ux * d, hw * math.sin(a), pz + uz * d))
    return ring


def duck(cx, cy, cz, rot=0.0):
    """The rubber duck, on the cistern lid.

    Body, neck and head are ONE lofted surface following a spine that runs
    along the body and then turns up through the breast - which is the only way
    the neck reads as part of the animal rather than as a pipe between two
    balls.  The bill stays separate because it is a different colour, and a
    seam is correct there.
    """
    out = []
    # (spine x, spine z, half width, below the spine, above it)
    # A rubber duck's tail is a short blunt flick, not a fin: run it out to
    # 64 mm on a 4 mm tip and the body finishes in a long swept blade.
    prof = [(0.050, 0.058, 0.007, 0.007, 0.006),     # tail tip
            (0.041, 0.051, 0.019, 0.016, 0.013),
            (0.028, 0.041, 0.030, 0.025, 0.021),
            (0.014, 0.033, 0.037, 0.030, 0.024),
            (-0.006, 0.030, 0.040, 0.028, 0.025),    # beam, at the waterline
            (-0.024, 0.033, 0.038, 0.027, 0.024),
            (-0.038, 0.043, 0.032, 0.023, 0.022),    # breast, turning up
            (-0.046, 0.059, 0.025, 0.020, 0.019),
            (-0.050, 0.075, 0.022, 0.018, 0.018),    # neck
            (-0.053, 0.089, 0.026, 0.024, 0.024),    # head swelling out
            (-0.055, 0.101, 0.029, 0.028, 0.027),
            (-0.055, 0.112, 0.022, 0.020, 0.020),
            (-0.054, 0.120, 0.009, 0.008, 0.008)]    # crown
    rings = []
    for k, (px, pz, hw, dn, up) in enumerate(prof):
        a = prof[max(k - 1, 0)]
        b = prof[min(k + 1, len(prof) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, tz) or 1.0
        rings.append(_duck_ring(px, pz, tx / ln, tz / ln, hw, dn, up))
    body = mlib.loft("R_Duck", rings, close_v=True, cname=C,
                     cap_start=True, cap_end=True)
    mlib.smooth_shade(body, 70)
    mlib.set_mat(body, M("M_DuckYellow"))
    out.append(body)
    # the bill: FLAT and wide, not a cone - rounded rectangles on their side
    bill_prof = [(-0.068, 0.031, 0.017, 0.006, 0.0985),
                 (-0.086, 0.037, 0.014, 0.005, 0.0968),
                 (-0.100, 0.035, 0.011, 0.004, 0.0952),
                 (-0.112, 0.026, 0.009, 0.004, 0.0940),
                 (-0.119, 0.011, 0.006, 0.002, 0.0933)]
    bill = mlib.loft("R_DuckBill", [
        [(x, a, zc + b) for (a, b) in mlib.rounded_rect(w, h, r, 4)]
        for (x, w, h, r, zc) in bill_prof],
        close_v=True, cname=C, cap_start=True, cap_end=True)
    mlib.bevel(bill, 0.0012, 2, 52)
    mlib.smooth_shade(bill, 58)
    mlib.set_mat(bill, M("M_DuckBill"))
    out.append(bill)
    for s_ in (-1, 1):
        ey = props.lathe("R_DuckEye%d" % (s_ > 0), [
            (0.0, 0.0), (0.0035, 0.0), (0.0055, 0.003), (0.0050, 0.006),
            (0.0, 0.007)], 12, C)
        props.face_y(ey, s_ * 1.0, (-0.058, s_ * 0.024, 0.105))
        mlib.set_mat(ey, M("M_DuckEye"))
        out.append(ey)
    for o in out:
        mlib.rotate_z(o, math.radians(rot))
        mlib.translate(o, (cx, cy, cz))
    return out


def bathroom():
    out = []
    tx0, tx1 = L.BA_TUB_X
    ty0, ty1 = L.BA_TUB_Y
    # the tub runs along the north wall; BA_TUB_Y is only its own depth, so it
    # is squared up against the wall here
    ty0, ty1 = L.BA_Y[1] - 0.735, L.BA_Y[1]
    # Everything in this room stands on the bathroom's TILE, which is 14.5 mm
    # proud of the parquet datum the rest of the flat is set out from.  Left on
    # z = 0 - the number every other room uses for its floor - the bath's foot
    # and the WC's skirt sink into the tiling by its own thickness.
    top = TUBH + BFL

    # The bath, lofted from its foot up over the rim and back down into the
    # well as one surface.  It used to be a solid rounded box with a SECOND
    # solid rounded box buried inside it - so the tub had no inside at all,
    # and the inner block was geometry nothing could ever see.
    cx, cy = (tx0 + tx1) * 0.5, (ty0 + ty1) * 0.5
    W, D = tx1 - tx0, ty1 - ty0
    tub_prof = [(W - 0.052, D - 0.052, 0.048, 0.000),
                (W - 0.006, D - 0.010, 0.058, 0.086),
                (W, D, 0.066, 0.296),
                (W, D, 0.066, TUBH - 0.012),
                (W - 0.003, D - 0.003, 0.066, TUBH),
                (W - 0.150, D - 0.146, 0.100, TUBH - 0.010),
                (W - 0.172, D - 0.166, 0.110, TUBH - 0.082),
                (W - 0.240, D - 0.216, 0.140, 0.222),
                (W - 0.370, D - 0.296, 0.150, 0.132),
                (W - 0.530, D - 0.376, 0.150, 0.112)]
    rings = [[(cx + a, cy + b, zz + BFL)
              for (a, b) in mlib.rounded_rect(ww, dd, r, 6)]
             for (ww, dd, r, zz) in tub_prof]
    shell = mlib.loft("R_TubBody", rings, close_u=False, close_v=True, cname=C,
                      cap_start=True, cap_end=True)
    mlib.bevel(shell, 0.005, 2, 44)
    mlib.smooth_shade(shell, 44)
    mlib.set_mat(shell, M("M_Sanitary"))
    out.append(shell)
    wst = props.lathe("R_TubWaste", [(0.0, 0.0), (0.026, 0.0), (0.026, 0.004),
                                     (0.0, 0.004)], 18, C)
    mlib.translate(wst, (tx0 + 0.24, cy, 0.114 + BFL))
    mlib.set_mat(wst, M("M_BathChrome"))
    out.append(wst)

    mix = props.lathe("R_TubMix", [(0.0, 0.0), (0.040, 0.0), (0.038, 0.014),
                                   (0.020, 0.030), (0.019, 0.090),
                                   (0.026, 0.098), (0.0, 0.100)], 18, C)
    # the tap block stands on the RIM, not out over the well
    mlib.translate(mix, (tx0 + 0.24, ty1 - 0.036, top - 0.006))
    mlib.set_mat(mix, M("M_BathChrome"))
    out.append(mix)
    spout = mlib.tube_along("R_TubSpout", [
        (tx0 + 0.24, ty1 - 0.036, top + 0.078),
        (tx0 + 0.24, ty1 - 0.130, top + 0.086),
        (tx0 + 0.24, ty1 - 0.180, top + 0.052)],
        mlib.circle(0.017, 10), cname=C)
    mlib.smooth_shade(spout, 48)
    mlib.set_mat(spout, M("M_BathChrome"))
    out.append(spout)
    riser = mlib.tube_along("R_TubRiser", [
        (tx0 + 0.24, ty1 - 0.030, top + 0.050),
        (tx0 + 0.24, ty1 - 0.030, 1.960),
        (tx0 + 0.24, ty1 - 0.150, 2.020)],
        mlib.circle(0.012, 10), cname=C)
    mlib.smooth_shade(riser, 48)
    mlib.set_mat(riser, M("M_BathChrome"))
    out.append(riser)
    head = props.lathe("R_Shower", [(0.0, 0.0), (0.028, -0.010), (0.056, -0.030),
                                    (0.058, -0.042), (0.030, -0.050),
                                    (0.0, -0.052)], 20, C)
    mlib.rot_x(head, math.radians(28.0))
    mlib.translate(head, (tx0 + 0.24, ty1 - 0.205, 2.022))
    mlib.set_mat(head, M("M_BathChrome"))
    out.append(head)

    rail = mlib.tube_along("R_CurtRail", [(tx0 - 0.010, ty0 + 0.030, 2.060),
                                          (tx1 + 0.010, ty0 + 0.030, 2.060)],
                           mlib.circle(0.013, 12), cname=C)
    mlib.smooth_shade(rail, 46)
    mlib.set_mat(rail, M("M_BathChrome"))
    out.append(rail)
    cur = props.drape("R_ShowerCurt", tx0 + 0.02, tx1 - 0.02, ty0 + 0.030,
                      0.320, 2.030, folds=9, amp=0.038, cname=C, nz=14,
                      seed=13)
    mlib.set_mat(cur, M("M_ShowerCurtain"))
    out.append(cur)

    out += vanity()
    out += wc()
    # on the cistern lid, turned along it - the lid is only 220 deep and the
    # duck is 170 long, so across the lid it would overhang both edges
    out += duck(L.BA_X[1] - TILE_F - 0.145, L.BA_WC[1] + 0.080, 0.787,
                rot=104.0)

    # ---- soft goods.  A bathroom without towels reads as a showroom -------
    # The rail goes on the WEST wall beside the bath, not on the door wall -
    # on the door wall it sits behind every camera that looks in here.
    ry0, ry1 = L.BA_Y[0] + 0.72, L.BA_Y[0] + 1.60
    rail = mlib.tube_along("R_TowelRail", [(L.BA_X[0] + 0.058, ry0, 1.180),
                                           (L.BA_X[0] + 0.058, ry1, 1.180)],
                           mlib.circle(0.011, 12), cname=C)
    mlib.smooth_shade(rail, 46)
    mlib.set_mat(rail, M("M_BathChrome"))
    out.append(rail)
    for s_ in (0, 1):
        br = props.lathe("R_TowelBr%d" % s_, [
            (0.0, 0.0), (0.030, 0.0), (0.028, 0.010), (0.013, 0.020),
            (0.013, 0.058), (0.0, 0.060)], 14, C)
        props.face_x(br, 1.0, (L.BA_X[0], (ry0 if s_ == 0 else ry1), 1.180))
        mlib.set_mat(br, M("M_BathChrome"))
        out.append(br)
    for i, (a, b, mt) in enumerate(((ry0 + 0.05, ry0 + 0.38, "M_Towel"),
                                    (ry0 + 0.46, ry0 + 0.82, "M_Towel2"))):
        tw = props.drape("R_Towel%d" % i, a, b, L.BA_X[0] + 0.070, 0.610,
                         1.176, folds=4, amp=0.028, cname=C, nz=11,
                         seed=31 + i * 7, th=0.011, taper=0.85, flare=1.03,
                         axis='Y')
        mlib.set_mat(tw, M(mt))
        out.append(tw)
    # one over the end of the bath
    tb = props.drape("R_TubTowel", tx1 - 0.44, tx1 - 0.10, ty0 - 0.020, 0.240,
                     top + 0.030, folds=4, amp=0.024, cname=C, nz=10, seed=45,
                     th=0.010, taper=0.85, flare=1.02)
    mlib.set_mat(tb, M("M_Towel2"))
    out.append(tb)

    mat_ = props.rug("R_BathMat", (tx0 + tx1) * 0.5, ty0 - 0.42, 0.78, 0.52,
                     lambda u, v: 0, [M("M_BathMat")], cname=C, cell=0.030,
                     th=0.016, pile=0.0022, z0=0.017)
    out.append(mat_)

    # Bottles STANDING ON THE RIM.  The old numbers were written for a bath
    # that was a solid box: y = ty1 - 0.085 is 8 mm inside the well now, and
    # z = top - 0.030 is 30 mm below the rim, so the three of them hung in the
    # air over the water with their bases buried in the tub wall.  The flat of
    # the rim runs 10.577..10.637 once the tiling is allowed for - 60 mm - so
    # they are also slimmer than they were.
    ry = ty1 - 0.044
    rnd = random.Random(67)
    for i, mt in enumerate(("M_BottleA", "M_BottleB", "M_BottleC")):
        bt = props.bottle("R_TubBot%d" % i, tx1 - 0.46 + i * 0.076,
                          ry, top - 0.009, r=0.024,
                          h=rnd.uniform(0.120, 0.175), neck=0.009, cname=C)
        mlib.set_mat(bt, M(mt))
        out.append(bt)

    # Toilet roll on a chrome holder, SOUTH of the cistern - hung level with it
    # the roll runs straight through the tank.
    hx = L.BA_X[1] - TILE_F
    hy = L.BA_WC[1] - 0.300
    hb = mlib.box("R_RollBr", hx - 0.104, hy - 0.012, 0.660, hx, hy + 0.012,
                  0.712, C)
    mlib.bevel(hb, 0.003, 2, 40)
    mlib.set_mat(hb, M("M_BathChrome"))
    out.append(hb)
    roll = props.lathe("R_Roll", [(0.021, 0.0), (0.058, 0.0), (0.060, 0.010),
                                  (0.060, 0.100), (0.058, 0.110),
                                  (0.021, 0.110)], 22, C)
    props.face_y(roll, 1.0, (hx - 0.075, hy - 0.055, 0.686))
    mlib.set_mat(roll, M("M_Towel"))
    out.append(roll)
    return out


# ================================================================== build

def build():
    mlib.purge("R_")
    mlib.coll(C)
    materials()
    bedrooms()
    bathroom()
    return len([o for o in bpy.data.objects if o.name.startswith("R_")])
