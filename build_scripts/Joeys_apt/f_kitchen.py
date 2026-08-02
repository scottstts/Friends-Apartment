"""f_kitchen - the alcove: counter run, the vintage range, the fridge, the wall
units, the splashback, and the island with its two stools.

The whole kitchen sits in a shallow alcove whose back wall is 2.40 m south of
the window wall, and everything in it is measured off that one line (`YB`).
Three depths matter and they are deliberately different: the counter face
(`YF`), the appliance face (`YA`, 45 mm PROUD of the counter, because a
free-standing range always is), and the wall-unit face, half the counter's
depth.  Getting those three flush is the single most common way a modelled
kitchen stops reading as one.
"""
import bpy, math, random
from mathutils import Vector
import mlib, mats, props, L, s_tile

C = "Kitchen"

YB = L.NY2                      # the alcove wall, inner face
YF = L.NY2 - L.CTR_D            # counter face          (4.245)
YA = L.NY2 - 0.70               # appliance face        (4.200)
YU = L.NY2 - L.UPPER_D          # wall-unit face        (4.565)
WALL_P0, WALL_P1 = (L.EX, L.NY2), (L.JX, L.NY2)     # CCW, so u runs west


def u_of(x):
    """The alcove wall is walked east -> west, so wall coordinates count back
    from the east wall."""
    return L.EX - x


# ================================================================== materials

def materials():
    mats.paint("M_CabCream", L.CAB_CREAM, rough=0.30, coat=0.20, brush=0.70)
    mats.paint("M_IslePutty", L.ISL_PUTTY, rough=0.34, coat=0.12, brush=0.60)
    mats.stone("M_Counter", 'F3F0E8', vein='CEC6B5', rough=0.12, scale=1.4)
    mats.enamel("M_Appliance", 'F6F3EA', rough=0.10, tint='E9E4D6')
    mats.paint("M_Porcelain", 'EFEDE4', rough=0.17, coat=0.32, brush=0.20)
    mats.metal("M_Chrome", 'DCE0E4', rough=0.055, grime=0.30, bump=0.03)
    mats.metal("M_SteelBrush", 'BEC2C6', rough=0.26, brush=0.85, grime=0.35)
    # The sink bowl gets its own, much calmer steel.  A heavy brush pattern on
    # a lofted bowl has no consistent direction to run in, so it breaks up into
    # speckle and the bowl reads as granite rather than as pressed stainless.
    mats.metal("M_SinkSteel", 'C4C8CC', rough=0.17, brush=0.22, grime=0.16)
    mats.metal("M_CastIron", '2A2A2E', rough=0.60, grime=0.55, bump=0.16)
    mats.metal("M_BrassK", 'B08D3F', rough=0.24, grime=0.35)
    mats.plastic("M_BlackPl", '17171A', rough=0.34, coat=0.30)
    mats.plastic("M_DarkGlass", '101014', rough=0.10, coat=0.55)
    mats.ceramic("M_SplashTile", 'EFEDE3', rough=0.075, pitch=s_tile.PITCH)
    mats.velvet("M_StoolVel", '11453C', rough=0.52, sheen=0.95)
    mats.wood("M_BlockWood", ['46301E', '644428', '2E1E0E'], ring=11.0,
              axis='Z', warp=0.35, rough=(0.26, 0.46), coat=0.30,
              grain_relief=0.05)
    mats.wood("M_StoolWood", ['5E2A1C', '8E4028', '451B11'], ring=34.0, axis='Z',
              rough=(0.20, 0.42), coat=0.42, grain_relief=0.09, scale=2.2)
    mats.stripe("M_SinkSkirt",
                ('EDE6D4', 'B4463C', 'EDE6D4', '2E6B62', 'D9A93E', 'B4463C'),
                pitch=0.052, axis='Z', rough=0.82)
    # a handful of carton colours for the junk-food shelf
    for i, (nm, col) in enumerate((('Red', 'B8342C'), ('Blue', '2A4E90'),
                                   ('Yellow', 'E0A81E'), ('Green', '2F7A46'),
                                   ('Orange', 'D8641E'), ('Purple', '5A3480'),
                                   ('Cream', 'DCD3BC'))):
        mats.paper("M_Pack" + nm, col, rough=0.42, gloss=0.30)


def M(n):
    return mats.get(n)


# ================================================================== counter run

def counter_run():
    """The counter is an L, not a straight run with a free-standing island.

    Both photographs show the same thing once the perspective is read
    correctly: a PENINSULA running north-south, joined at its north end to a
    short counter that continues east along the alcove wall to the range.  In
    kitchen.jpg the peninsula presents its west face to the camera and recedes
    away to the north-east; in living_room.webp the camera is further east and
    looks square onto that same west face, which is why the two barstools sit
    side by side there and one behind the other here.  Built as an island in
    the middle of the floor - the obvious first reading - the whole kitchen
    loses its corner and the room reads twice as empty as the set.

    One continuous worktop covers both legs, so it is built as two butted
    solids rather than one prism: the leg with the sink in it needs a real hole
    through the vertex grid, and the peninsula needs a rounded nose on three
    exposed edges and a square butt on the fourth.
    """
    out = []
    px0, px1 = L.PEN_X
    py0, py1 = L.PEN_Y
    sx0, sx1 = L.K_SINK
    top = L.CTR_H
    deck = top - 0.038
    band0 = deck - 0.026

    # ---------------------------------------------------------- peninsula
    # stopped 30 mm short of the wall line: the baseboard runs behind this and
    # the plinth's own north face would otherwise sit in the same plane as the
    # carcase above it
    pl = props.plinth("K_PenPlinth", px0 + 0.045, py0 + 0.045, px1 - 0.045,
                      py1 - 0.030, 0.0, 0.098, cname=C)
    mlib.set_mat(pl, M("M_IslePutty"))
    out.append(pl)
    body = mlib.box("K_PenBody", px0, py0, 0.092, px1, py1, band0, C)
    mlib.bevel(body, 0.003, 2, 44)
    mlib.set_mat(body, M("M_IslePutty"))
    out.append(body)

    prof = [(0.0, -0.002), (0.030, -0.002), (0.030, 0.006),
            (0.021, 0.013), (0.008, 0.014), (0.0, 0.010)]
    cz = (0.092 + band0) * 0.5
    ph = band0 - 0.092 - 0.150
    faces = [('E', px0, py0 + (py1 - py0) * 0.28, (py1 - py0) * 0.50),
             ('E', px0, py0 + (py1 - py0) * 0.76, (py1 - py0) * 0.38),
             ('N', py0, (px0 + px1) * 0.5, px1 - px0),
             ('W', px1, py0 + (L.NY2 - L.CTR_D - py0) * 0.5,
              L.NY2 - L.CTR_D - py0)]
    for i, (wall, at, u, span) in enumerate(faces):
        fr = mlib.sweep_rect_frame("K_PenPanel%d" % i, span - 0.190, ph, prof, C)
        mlib.bevel(fr, 0.0018, 2, 40)
        props.wall_place([fr], wall, u, cz, at)
        mlib.set_mat(fr, M("M_IslePutty"))
        out.append(fr)

    # capping band round the three exposed sides only - it must not wrap the
    # north end, which butts the counter
    band = mlib.sweep_loop("K_PenBand", [(px0, py1), (px0, py0), (px1, py0),
                                         (px1, L.NY2 - L.CTR_D)],
                           [(-0.002, 0.0), (0.013, 0.003), (0.015, 0.014),
                            (0.008, 0.026), (-0.002, 0.026)], cname=C,
                           close=False)
    mlib.translate(band, (0, 0, band0))
    mlib.smooth_shade(band, 44)
    mlib.set_mat(band, M("M_IslePutty"))
    out.append(band)

    # ---------------------------------------------------------- sink leg
    ybk = YB - 0.030
    case = props.carcass("K_SinkCase", sx0, YF, sx1, ybk, L.TOE_H, deck - 0.004,
                         cname=C, back_at='y1', side=0.018, top=0.018, lid=False)
    mlib.set_mat(case, M("M_CabCream"))
    out.append(case)
    toe = props.plinth("K_SinkToe", sx0 + 0.012, YF + L.TOE_IN, sx1 - 0.012,
                       ybk, 0.0, L.TOE_H, cname=C)
    mlib.set_mat(toe, M("M_BlackPl"))
    out.append(toe)

    ff = []
    for (a, b) in ((sx0, sx0 + 0.052), (sx1 - 0.052, sx1)):
        ff.append(mlib.box("K_SinkFF", a, YF - 0.016, L.TOE_H, b, YF + 0.004,
                           deck, C))
    ff.append(mlib.box("K_SinkFFh", sx0, YF - 0.016, deck - 0.062, sx1,
                       YF + 0.004, deck - 0.002, C))
    frame = mlib.join(ff, "K_SinkFace", C)
    mlib.bevel(frame, 0.003, 2, 40)
    mlib.set_mat(frame, M("M_CabCream"))
    out.append(frame)
    curt = props.skirt("K_SinkSkirt", sx0 + 0.056, sx1 - 0.056, YF - 0.020,
                       0.055, deck - 0.066, folds=8, amp=0.024, cname=C)
    mlib.set_mat(curt, M("M_SinkSkirt"))
    out.append(curt)

    # ---------------------------------------------------------- worktop
    ptop = props.worktop("K_PenTop", px0 - 0.030, py0 - 0.030, px1 + 0.030,
                         YB, top, th=0.038, r=0.016, cname=C,
                         radii=[0.016, 0.016, 0.0, 0.0])
    mlib.set_mat(ptop, M("M_Counter"))
    out.append(ptop)

    # The cut-out sits towards the WEST end of its cabinet, which leaves 270 mm
    # of clear worktop on the east side for the dish rack to stand on.  Centred
    # in the run there is nowhere on this leg to put anything down, and the
    # rack and the towel stand ended up standing over the hole.
    hx0, hx1 = sx0 + 0.07, sx0 + 0.53
    hy0, hy1 = YF + 0.09, YF + 0.47
    w = sx1 - (px1 + 0.030) + 0.010
    d = YB - (YF - 0.022)
    tp = mlib.panel_with_holes("K_Worktop", w, d, 0.038,
                               [(hx0 - (px1 + 0.030), hy0 - (YF - 0.022),
                                 hx1 - (px1 + 0.030), hy1 - (YF - 0.022))], C)
    mlib.rot_x(tp, -math.pi * 0.5)
    mlib.translate(tp, (px1 + 0.030, YF - 0.022, top))
    mlib.bevel(tp, 0.005, 3, 40)
    mlib.set_mat(tp, M("M_Counter"))
    out.append(tp)

    out += sink(hx0, hy0, hx1, hy1, top)
    out += peninsula_dressing(top)
    return out


def peninsula_dressing(top):
    """The microwave, the coffee maker and the phone that stand on the
    peninsula's north end in both photographs."""
    out = []
    cx = (L.PEN_X[0] + L.PEN_X[1]) * 0.5
    mb = mlib.rounded_box("K_IsMw", cx - 0.225, YB - 0.375, top,
                          cx + 0.225, YB - 0.045, top + 0.268, r=0.014, cname=C)
    mlib.bevel(mb, 0.003, 2, 44)
    mlib.smooth_shade(mb, 34)
    mlib.set_mat(mb, M("M_Appliance"))
    out.append(mb)
    dr = mlib.box("K_IsMwDoor", cx - 0.218, YB - 0.391, top + 0.018,
                  cx + 0.098, YB - 0.371, top + 0.250, C)
    mlib.bevel(dr, 0.004, 3, 40)
    mlib.set_mat(dr, M("M_Appliance"))
    out.append(dr)
    wn = mlib.box("K_IsMwWin", cx - 0.194, YB - 0.399, top + 0.042,
                  cx + 0.062, YB - 0.387, top + 0.226, C)
    mlib.bevel(wn, 0.003, 2, 40)
    mlib.set_mat(wn, M("M_DarkGlass"))
    out.append(wn)
    pn = mlib.box("K_IsMwPan", cx + 0.112, YB - 0.385, top + 0.020,
                  cx + 0.220, YB - 0.375, top + 0.248, C)
    mlib.bevel(pn, 0.003, 2, 40)
    mlib.set_mat(pn, M("M_BlackPl"))
    out.append(pn)

    cy = YB - 0.560
    cb = mlib.rounded_box("K_Coffee", cx - 0.098, cy - 0.115, top,
                          cx + 0.098, cy + 0.115, top + 0.335, r=0.022, cname=C)
    mlib.bevel(cb, 0.003, 2, 44)
    mlib.smooth_shade(cb, 34)
    mlib.set_mat(cb, M("M_Appliance"))
    out.append(cb)
    notch = mlib.box("K_CoffeeCut", cx - 0.086, cy - 0.126, top + 0.012,
                     cx + 0.086, cy - 0.020, top + 0.190, C)
    mlib.bevel(notch, 0.004, 2, 40)
    mlib.set_mat(notch, M("M_BlackPl"))
    out.append(notch)
    carafe = props.lathe("K_Carafe", [(0.0, 0.0), (0.058, 0.0), (0.062, 0.014),
                                      (0.062, 0.120), (0.054, 0.140),
                                      (0.056, 0.150), (0.050, 0.152),
                                      (0.050, 0.014), (0.0, 0.012)], 22, C)
    mlib.translate(carafe, (cx, cy - 0.070, top + 0.020))
    mlib.set_mat(carafe, M("M_DarkGlass"))
    out.append(carafe)

    ph = mlib.rounded_box("K_Phone", cx - 0.110, YB - 1.72, top,
                          cx + 0.110, YB - 1.65, top + 0.032, r=0.014, cname=C)
    mlib.bevel(ph, 0.003, 2, 44)
    mlib.smooth_shade(ph, 34)
    mlib.set_mat(ph, M("M_BlackPl"))
    out.append(ph)
    mg = props.mug("K_IsMug", cx + 0.20, YB - 1.42, top, cname=C, rotz=1.1)
    mlib.set_mat(mg, M("M_Porcelain"))
    out.append(mg)
    return out


def sink(x0, y0, x1, y1, top):
    """A pressed stainless bowl hanging under the cut-out, plus the mixer.

    Two things make a sink read as a sink from above rather than as a panel
    let into the worktop.  The first is a ROLLED rim - a bead standing proud
    of the stone with a shadow under it - and the second is that the bowl
    TAPERS: walls dropped dead vertical from the rim are edge-on to every
    camera looking down at them, so the eye gets no surface to read depth
    from and the whole thing collapses into the counter.  This bowl loses
    55 mm a side on the way down and the corner radius opens out as it goes,
    which is also what a real pressed bowl does.

    The waste is set back from centre, with a real strainer in it.
    """
    out = []
    W, D = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    # (width, depth, corner radius, z)
    lv = [(W + 0.034, D + 0.034, 0.028, top + 0.008),
          (W + 0.036, D + 0.036, 0.028, top - 0.002),
          (W + 0.014, D + 0.014, 0.026, top - 0.011),
          (W - 0.008, D - 0.008, 0.030, top - 0.020),
          (W - 0.024, D - 0.024, 0.038, top - 0.060),
          (W - 0.048, D - 0.048, 0.052, top - 0.118),
          (W - 0.078, D - 0.078, 0.070, top - 0.166),
          (W - 0.116, D - 0.116, 0.086, top - 0.192),
          (W - 0.150, D - 0.150, 0.090, top - 0.198)]
    rings = [[(cx + a, cy + b, z)
              for (a, b) in mlib.rounded_rect(ww, dd, r, 5)]
             for (ww, dd, r, z) in lv]
    # cap_end only.  cap_start closes the FIRST ring, which here is the rim -
    # so the sink came out with a lid welded over it and read as a flat panel
    # let into the worktop.
    bowl = mlib.loft("K_SinkBowl", rings, close_u=False, close_v=True, cname=C,
                     cap_start=False, cap_end=True)
    mlib.bevel(bowl, 0.0025, 2, 44)
    mlib.smooth_shade(bowl, 40)
    mlib.set_mat(bowl, M("M_SinkSteel"))
    out.append(bowl)
    wx, wy = cx, cy + D * 0.20
    dr = props.lathe("K_SinkDrain", [(0.0, 0.0), (0.046, 0.0), (0.048, 0.005),
                                     (0.042, 0.010), (0.038, 0.011),
                                     (0.038, 0.026), (0.030, 0.030),
                                     (0.0, 0.030)], 22, C)
    mlib.translate(dr, (wx, wy, top - 0.199))
    mlib.set_mat(dr, M("M_Chrome"))
    out.append(dr)
    # the strainer: a disc on a stem with slots showing round it
    for k in range(8):
        a = math.tau * k / 8
        sl = mlib.box("K_SinkSl%d" % k, -0.0045, 0.020, 0.0, 0.0045, 0.036,
                      0.006, C)
        mlib.rotate_z(sl, a)
        mlib.translate(sl, (wx, wy, top - 0.196))
        mlib.set_mat(sl, M("M_BlackPl"))
        out.append(sl)
    st = props.lathe("K_SinkStr", [(0.0, 0.0), (0.019, 0.0), (0.019, 0.006),
                                   (0.006, 0.009), (0.006, 0.024),
                                   (0.012, 0.028), (0.0, 0.030)], 18, C)
    mlib.translate(st, (wx, wy, top - 0.190))
    mlib.set_mat(st, M("M_Chrome"))
    out.append(st)

    # mixer: a swan-neck spout on a deck plate, with two cross handles
    bx, by = cx, y1 + 0.075
    base = props.lathe("K_TapBase", [(0.0, 0.0), (0.040, 0.0), (0.040, 0.012),
                                     (0.030, 0.020), (0.026, 0.055),
                                     (0.024, 0.070), (0.0, 0.072)], 20, C)
    mlib.translate(base, (bx, by, top))
    path = [(bx, by, top + 0.055), (bx, by, top + 0.175),
            (bx, by - 0.030, top + 0.238), (bx, by - 0.105, top + 0.252),
            (bx, by - 0.168, top + 0.226), (bx, by - 0.176, top + 0.192)]
    neck = mlib.tube_along("K_TapNeck", path, mlib.circle(0.0135, 14), cname=C)
    mlib.smooth_shade(neck, 50)
    tap = [base, neck]
    for s in (-1, 1):
        hb = props.lathe("K_TapH", [(0.0, 0.0), (0.022, 0.0), (0.020, 0.024),
                                    (0.009, 0.030), (0.009, 0.052),
                                    (0.014, 0.058), (0.0, 0.060)], 14, C)
        mlib.translate(hb, (bx + s * 0.082, by, top))
        cross = mlib.join([
            mlib.box("K_TapX", -0.030, -0.0055, 0.0, 0.030, 0.0055, 0.009, C),
            mlib.box("K_TapY", -0.0055, -0.030, 0.0, 0.0055, 0.030, 0.009, C)],
            "K_TapCross", C)
        mlib.bevel(cross, 0.002, 2, 40)
        mlib.translate(cross, (bx + s * 0.082, by, top + 0.058))
        tap += [hb, cross]
    for o in tap:
        mlib.set_mat(o, M("M_Chrome"))
    return out + tap


# ================================================================== the range

def range_():
    """A 1950s gas range: enamel body, chrome cooktop trim, cast-iron grates,
    and a backguard carrying the controls.  The knobs go on the FRONT of the
    backguard, not on the body - that is the detail that dates it."""
    out = []
    x0, x1 = L.K_STOVE
    yb, yf = YB - 0.020, YA
    deck = 0.905

    for (dx, dy) in ((0.055, 0.055), (x1 - x0 - 0.055, 0.055),
                     (0.055, yb - yf - 0.055), (x1 - x0 - 0.055, yb - yf - 0.055)):
        lg = props.lathe("K_RgLeg", [(0.0, 0.0), (0.030, 0.0), (0.028, 0.012),
                                     (0.018, 0.028), (0.017, 0.100),
                                     (0.024, 0.104), (0.0, 0.104)], 14, C)
        mlib.translate(lg, (x0 + dx, yf + dy, 0.0))
        mlib.set_mat(lg, M("M_Chrome"))
        out.append(lg)

    body = mlib.rounded_box("K_RangeBody", x0, yf, 0.098, x1, yb, deck,
                            r=0.026, seg=4, cname=C)
    mlib.bevel(body, 0.004, 2, 44)
    mlib.smooth_shade(body, 34)
    mlib.set_mat(body, M("M_Appliance"))
    out.append(body)

    # Oven door and broiler drawer.  Both get a REBATE and a chrome surround
    # rather than being plain slabs: on a white enamel body under white light
    # an unbroken panel has no edge to catch, and the front of the range turns
    # into one soft lump - which is exactly what the first pass did.
    for (nm, z0, z1, win) in (("K_RgOven", 0.412, 0.836, True),
                              ("K_RgDrw", 0.126, 0.382, False)):
        cx, cz = (x0 + x1) * 0.5, (z0 + z1) * 0.5
        pts = [(cx + a, cz + b)
               for (a, b) in mlib.rounded_rect(x1 - x0 - 0.070, z1 - z0, 0.010, 3)]
        d = mlib.prism_xz(nm, pts, yf - 0.030, yf + 0.010, C)
        mlib.bevel(d, 0.0022, 2, 44)
        mlib.set_mat(d, M("M_Appliance"))
        out.append(d)
        ins = mlib.prism_xz(nm + "_r",
                            [(cx + a, cz + b) for (a, b) in
                             mlib.rounded_rect(x1 - x0 - 0.152, z1 - z0 - 0.082,
                                               0.010, 3)],
                            yf - 0.041, yf - 0.028, C)
        mlib.bevel(ins, 0.0022, 2, 44)
        mlib.set_mat(ins, M("M_Chrome"))
        out.append(ins)
        if win:
            gl = mlib.box(nm + "_g", cx - 0.318, yf - 0.044, cz - 0.118,
                          cx + 0.318, yf - 0.038, cz + 0.118, C)
            mlib.bevel(gl, 0.002, 2, 40)
            mlib.set_mat(gl, M("M_DarkGlass"))
            out.append(gl)

    # slim chrome handles on square standoffs - the fat cast standoff read as
    # a blob at every distance the camera ever gets to
    for (nm, z, ln) in (("K_RgOvH", 0.874, x1 - x0 - 0.150),
                        ("K_RgDrH", 0.410, x1 - x0 - 0.150)):
        parts = [mlib.tube_along(nm + "_b",
                                 [(-ln * 0.5, -0.052, 0.0), (ln * 0.5, -0.052, 0.0)],
                                 mlib.circle(0.0085, 14), cname=C)]
        for s in (-1, 1):
            parts.append(mlib.box(nm + "_s", s * ln * 0.5 - 0.011, -0.052,
                                  -0.013, s * ln * 0.5 + 0.011, 0.006, 0.013, C))
        h = mlib.join(parts, nm, C)
        mlib.bevel(h, 0.0022, 2, 42)
        mlib.smooth_shade(h, 46)
        mlib.translate(h, ((x0 + x1) * 0.5, yf - 0.030, z))
        mlib.set_mat(h, M("M_Chrome"))
        out.append(h)

    # a chrome kick strip and two corner posts, which is what actually reads as
    # "1950s range" from across the room
    kick = mlib.box("K_RgKick", x0 + 0.010, yf - 0.014, 0.098, x1 - 0.010,
                    yf + 0.010, 0.120, C)
    mlib.bevel(kick, 0.003, 2, 40)
    mlib.set_mat(kick, M("M_Chrome"))
    out.append(kick)
    for s in (0, 1):
        px = x0 + 0.006 if s == 0 else x1 - 0.030
        post = mlib.box("K_RgPost%d" % s, px, yf - 0.014, 0.120, px + 0.024,
                        yf + 0.030, deck, C)
        mlib.bevel(post, 0.003, 2, 40)
        mlib.set_mat(post, M("M_Chrome"))
        out.append(post)

    # cooktop: an enamel deck with a chrome nosing swept round it
    ck = props.worktop("K_RgTop", x0 - 0.004, yf - 0.010, x1 + 0.004, yb, deck + 0.022,
                       th=0.022, r=0.020, cname=C, radii=[0.020, 0.020, 0.006, 0.006])
    mlib.set_mat(ck, M("M_Appliance"))
    out.append(ck)
    path = [(x0 - 0.004, yf - 0.010), (x1 + 0.004, yf - 0.010),
            (x1 + 0.004, yb), (x0 - 0.004, yb)]
    trim = mlib.sweep_loop("K_RgNose", path,
                           [(-0.004, 0.0), (0.009, 0.0), (0.010, 0.008),
                            (0.006, 0.014), (-0.004, 0.014)], cname=C)
    mlib.translate(trim, (0, 0, deck + 0.009))
    mlib.smooth_shade(trim, 42)
    mlib.set_mat(trim, M("M_Chrome"))
    out.append(trim)

    # four burners in a square, a griddle plate to the right
    for (bx, by) in ((x0 + 0.185, yf + 0.185), (x0 + 0.185, yf + 0.475),
                     (x0 + 0.460, yf + 0.185), (x0 + 0.460, yf + 0.475)):
        pan = props.lathe("K_RgPan", [(0.0, 0.0), (0.098, 0.0), (0.104, 0.010),
                                      (0.100, 0.014), (0.055, 0.006),
                                      (0.030, 0.004), (0.0, 0.004)], 22, C)
        mlib.translate(pan, (bx, by, deck + 0.022))
        mlib.set_mat(pan, M("M_Chrome"))
        out.append(pan)
        cap = props.lathe("K_RgCap", [(0.0, 0.0), (0.044, 0.002), (0.046, 0.016),
                                      (0.040, 0.024), (0.026, 0.026), (0.0, 0.022)],
                          20, C)
        mlib.translate(cap, (bx, by, deck + 0.030))
        mlib.set_mat(cap, M("M_CastIron"))
        out.append(cap)
        grate = _grate("K_RgGrate", bx, by, deck + 0.050)
        out.append(grate)
    gx, gy = x0 + 0.885, yf + 0.330
    gr = mlib.rounded_box("K_RgGriddle", gx - 0.115, gy - 0.165, deck + 0.022,
                          gx + 0.115, gy + 0.165, deck + 0.040, r=0.014, cname=C)
    mlib.bevel(gr, 0.003, 2, 44)
    mlib.smooth_shade(gr, 34)
    mlib.set_mat(gr, M("M_CastIron"))
    out.append(gr)

    # Backguard.  Low and flat, with the controls on its FRONT face where the
    # camera can see them - a deep overhanging hood put the whole panel in its
    # own shadow and lost every knob on the range.
    gz0, gz1 = deck + 0.022, 1.208
    bg = mlib.box("K_RgGuard", x0, yb - 0.094, gz0, x1, yb, gz1, C)
    mlib.bevel(bg, 0.005, 3, 40)
    mlib.set_mat(bg, M("M_Appliance"))
    out.append(bg)
    cap = mlib.box("K_RgGuardCap", x0 - 0.010, yb - 0.116, gz1, x1 + 0.010, yb,
                   gz1 + 0.020, C)
    mlib.bevel(cap, 0.005, 3, 38)
    mlib.set_mat(cap, M("M_Chrome"))
    out.append(cap)
    cp = mlib.box("K_RgPanel", x0 + 0.040, yb - 0.108, 1.012, x1 - 0.040,
                  yb - 0.092, 1.128, C)
    mlib.bevel(cp, 0.003, 2, 40)
    mlib.set_mat(cp, M("M_Chrome"))
    out.append(cp)
    for i in range(6):
        kx = x0 + 0.098 + i * (x1 - x0 - 0.196) / 5.0
        kn = props.knob("K_RgKnob", 0.026, C, stem=0.020)
        props.face_y(kn, -1.0, (kx, yb - 0.108, 1.070))
        mlib.set_mat(kn, M("M_BlackPl") if i % 2 else M("M_Chrome"))
        out.append(kn)
    cl = props.lathe("K_RgClock", [(0.0, 0.0), (0.050, 0.0), (0.052, 0.009),
                                   (0.044, 0.015), (0.0, 0.015)], 24, C)
    props.face_y(cl, -1.0, ((x0 + x1) * 0.5, yb - 0.108, 1.166))
    mlib.set_mat(cl, M("M_Chrome"))
    out.append(cl)
    dial = props.lathe("K_RgDial", [(0.0, 0.0), (0.038, 0.0), (0.038, 0.004),
                                    (0.0, 0.004)], 24, C)
    props.face_y(dial, -1.0, ((x0 + x1) * 0.5, yb - 0.124, 1.166))
    mlib.set_mat(dial, M("M_BlackPl"))
    out.append(dial)
    return out


def _grate(name, cx, cy, z):
    """A cast-iron burner grate: a ring with four ribs, all one swept solid."""
    parts = [props.torus(name + "_r", 0.098, 0.0085, 22, 8, C, cz=z)]
    for i in range(4):
        a = math.pi * 0.25 + math.pi * 0.5 * i
        p0 = (cx + 0.014 * math.cos(a), cy + 0.014 * math.sin(a), z - 0.004)
        p1 = (cx + 0.104 * math.cos(a), cy + 0.104 * math.sin(a), z)
        parts.append(mlib.tube_along(name + "_a%d" % i, [p0, p1],
                                     mlib.circle(0.0072, 8), cname=C))
    mlib.translate(parts[0], (cx, cy, 0.0))
    ob = mlib.join(parts, name, C)
    mlib.smooth_shade(ob, 50)
    mlib.set_mat(ob, M("M_CastIron"))
    return ob


# ================================================================== the fridge

def fridge():
    out = []
    x0, x1 = L.K_FRIDGE
    h = L.K_FRIDGE_H
    yb, yf = YB - 0.020, YA

    base = mlib.box("K_FrPlinth", x0 + 0.030, yf + 0.060, 0.0, x1 - 0.030, yb,
                    0.088, C)
    mlib.bevel(base, 0.003, 2, 40)
    mlib.set_mat(base, M("M_BlackPl"))
    out.append(base)

    body = mlib.rounded_box("K_FrBody", x0, yf + 0.052, 0.086, x1, yb, h,
                            r=0.042, seg=5, cname=C)
    mlib.bevel(body, 0.005, 2, 44)
    mlib.smooth_shade(body, 34)
    mlib.set_mat(body, M("M_Appliance"))
    out.append(body)

    # freezer above, cold food below; both doors proud of the carcase and let
    # 3 mm into it, so nothing anywhere is flush
    for (nm, z0, z1) in (("K_FrDoorF", 1.212, h - 0.030),
                         ("K_FrDoorM", 0.108, 1.188)):
        cz = (z0 + z1) * 0.5
        pts = [((x0 + x1) * 0.5 + a, cz + b)
               for (a, b) in mlib.rounded_rect(x1 - x0 - 0.014, z1 - z0, 0.040, 5)]
        d = mlib.prism_xz(nm, pts, yf, yf + 0.055, C)
        mlib.bevel(d, 0.006, 3, 38)
        mlib.smooth_shade(d, 34)
        mlib.set_mat(d, M("M_Appliance"))
        out.append(d)
        # chrome lever handle down the opening edge
        hl = props.handle_bar(nm + "_h", (z1 - z0) * 0.56, cname=C, r=0.010,
                              stand=0.046, plate=0.030)
        mlib.rot_y(hl, math.pi * 0.5)
        mlib.translate(hl, (x0 + 0.082, yf, cz))
        mlib.set_mat(hl, M("M_Chrome"))
        out.append(hl)
    badge = mlib.box("K_FrBadge", (x0 + x1) * 0.5 - 0.085, yf - 0.006, 1.055,
                     (x0 + x1) * 0.5 + 0.085, yf + 0.004, 1.086, C)
    mlib.bevel(badge, 0.002, 2, 40)
    mlib.set_mat(badge, M("M_Chrome"))
    out.append(badge)

    # the clown cookie jar that lives on top of it
    jarb = props.lathe("K_Cookie", [(0.0, 0.0), (0.060, 0.0), (0.078, 0.030),
                                    (0.084, 0.078), (0.074, 0.118),
                                    (0.056, 0.140), (0.056, 0.150),
                                    (0.0, 0.152)], 24, C)
    mlib.translate(jarb, (x1 - 0.24, yb - 0.30, h))
    mlib.set_mat(jarb, M("M_Porcelain"))
    out.append(jarb)
    hat = props.lathe("K_CookieHat", [(0.0, 0.088), (0.062, 0.006), (0.064, 0.0),
                                      (0.0, 0.0)], 22, C)
    mlib.translate(hat, (x1 - 0.24, yb - 0.30, h + 0.150))
    mlib.set_mat(hat, M("M_PackRed"))
    out.append(hat)
    return out


# ================================================================== wall units

def wall_units():
    out = []
    ux0, ux1 = L.K_UPPER
    z0, z1 = L.UPPER_Z

    box = props.carcass("K_UpCase", ux0, YU, ux1, YB, z0, z1, cname=C,
                        back_at='y1', side=0.017, top=0.017)
    mlib.set_mat(box, M("M_CabCream"))
    out.append(box)

    # THREE doors, not four.  kitchen.jpg has three broad raised-panel doors
    # across this run and the knobs down near their bottom rails; four narrow
    # ones read as a bank of lockers.
    n = 3
    gap = 0.004
    w = (ux1 - ux0 - gap * (n - 1)) / n
    for i in range(n):
        dx = ux0 + i * (w + gap)
        d = props.cab_door("K_UpDoor%d" % i, w, z1 - z0 - 0.006, th=0.020, inset=0.015, proud=0.008,
                           rail=0.058, cname=C)
        mlib.translate(d, (dx, YU - 0.020, z0 + 0.003))
        mlib.set_mat(d, M("M_CabCream"))
        out.append(d)
        kx = dx + (w - 0.052 if i < n - 1 else 0.052)
        kn = props.knob("K_UpKnob%d" % i, 0.016, C)
        props.face_y(kn, -1.0, (kx, YU - 0.020, z0 + 0.105))
        mlib.set_mat(kn, M("M_BrassK"))
        out.append(kn)

    # A light cornice and a valance board under the front edge.  Both are cut
    # FLUSH at the west end - that end dies into the wall's own corner, and the
    # 14 mm return they used to carry hung out past it into the living room.
    corn = mlib.sweep_loop("K_UpCorn",
                           [(ux0, YU - 0.020), (ux1 + 0.014, YU - 0.020),
                            (ux1 + 0.014, YB), (ux0, YB)],
                           [(-0.002, 0.0), (0.006, 0.004), (0.010, 0.020),
                            (0.004, 0.036), (-0.002, 0.040)], cname=C, close=True)
    mlib.translate(corn, (0, 0, z1))
    mlib.smooth_shade(corn, 44)
    mlib.set_mat(corn, M("M_CabCream"))
    out.append(corn)

    val = mlib.box("K_UpValance", ux0, YU - 0.024, z0 - 0.030,
                   ux1 + 0.010, YU + 0.002, z0 + 0.002, C)
    mlib.bevel(val, 0.003, 2, 40)
    mlib.set_mat(val, M("M_CabCream"))
    out.append(val)

    # cup hooks screwed up into the carcase bottom, with mugs hanging off them
    rnd = random.Random(5)
    for i in range(5):
        hx = ux0 + 0.60 + i * 0.170
        hy = YU - 0.062
        hk = mlib.tube_along("K_Hook%d" % i, [
            (hx, hy, z0 - 0.004), (hx, hy, z0 - 0.028),
            (hx, hy + 0.016, z0 - 0.042), (hx, hy + 0.034, z0 - 0.036),
            (hx, hy + 0.038, z0 - 0.022)],
            mlib.circle(0.0024, 6), cname=C)
        mlib.smooth_shade(hk, 50)
        mlib.set_mat(hk, M("M_Chrome"))
        out.append(hk)
        # The handle has to sit ON the hook's bend, not near it.  props.mug
        # puts the handle at +X, so rotz = pi/2 turns it to +Y (towards the
        # wall) and the body then hangs below and out into the room.
        mg = props.mug("K_Mug%d" % i, hx, hy - 0.038, z0 - 0.117, r=0.041,
                       h=0.094, cname=C,
                       rotz=math.pi * 0.5 + rnd.uniform(-0.10, 0.10))
        mlib.set_mat(mg, M("M_Porcelain"))
        out.append(mg)
    return out


def over_range_micro():
    """The white microwave slung under the cabinets, and the cupboard above
    it."""
    out = []
    x0, x1 = L.K_MW
    z0, z1 = L.K_MW_Z
    body = mlib.rounded_box("K_MwBody", x0, YB - 0.360, z0, x1, YB, z1,
                            r=0.016, cname=C)
    mlib.bevel(body, 0.003, 2, 44)
    mlib.smooth_shade(body, 34)
    mlib.set_mat(body, M("M_Appliance"))
    out.append(body)
    door = mlib.box("K_MwDoor", x0 + 0.008, YB - 0.376, z0 + 0.020,
                    x1 - 0.150, YB - 0.356, z1 - 0.020, C)
    mlib.bevel(door, 0.004, 3, 40)
    mlib.set_mat(door, M("M_Appliance"))
    out.append(door)
    win = mlib.box("K_MwWin", x0 + 0.038, YB - 0.382, z0 + 0.048,
                   x1 - 0.180, YB - 0.372, z1 - 0.048, C)
    mlib.bevel(win, 0.003, 2, 40)
    mlib.set_mat(win, M("M_DarkGlass"))
    out.append(win)
    pan = mlib.box("K_MwPanel", x1 - 0.144, YB - 0.372, z0 + 0.022,
                   x1 - 0.014, YB - 0.362, z1 - 0.022, C)
    mlib.bevel(pan, 0.003, 2, 40)
    mlib.set_mat(pan, M("M_BlackPl"))
    out.append(pan)
    hdl = mlib.box("K_MwHandle", x1 - 0.176, YB - 0.408, z0 + 0.040,
                   x1 - 0.156, YB - 0.372, z1 - 0.040, C)
    mlib.bevel(hdl, 0.004, 3, 40)
    mlib.set_mat(hdl, M("M_Chrome"))
    out.append(hdl)

    cz0, cz1 = z1, L.UPPER_Z[1]
    cab = props.carcass("K_MwCase", x0, YU, x1, YB, cz0, cz1, cname=C,
                        back_at='y1', side=0.017, top=0.017)
    mlib.set_mat(cab, M("M_CabCream"))
    out.append(cab)
    d = props.cab_door("K_MwDoorU", x1 - x0, cz1 - cz0 - 0.006, th=0.020, inset=0.015, proud=0.008,
                       rail=0.055, cname=C)
    mlib.translate(d, (x0, YU - 0.020, cz0 + 0.003))
    mlib.set_mat(d, M("M_CabCream"))
    out.append(d)
    kn = props.knob("K_MwKnob", 0.016, C)
    props.face_y(kn, -1.0, (x0 + 0.050, YU - 0.020, cz0 + 0.110))
    mlib.set_mat(kn, M("M_BrassK"))
    out.append(kn)
    return out


def food_shelf():
    """Open shelving over the fridge, stacked with cereal and cans - the one
    piece of the kitchen that is never tidy in any episode."""
    out = []
    x0, x1 = L.K_SHELF
    z0, z1 = L.K_SHELF_Z
    mid = (z0 + z1) * 0.5
    yfr = YB - 0.300
    sh = props.carcass("K_ShCase", x0, yfr, x1, YB, z0, z1, cname=C,
                       back_at='y1', side=0.018, top=0.018, shelves=(mid,))
    mlib.set_mat(sh, M("M_CabCream"))
    out.append(sh)

    rnd = random.Random(19)
    packs = ["M_PackRed", "M_PackBlue", "M_PackYellow", "M_PackGreen",
             "M_PackOrange", "M_PackPurple", "M_PackCream"]

    # Packed tight and to the back, with a few boxes turned or laid over.  A
    # shelf of evenly spaced upright cartons reads as a display; what makes it
    # read as a cupboard is that things are jammed in at angles and the row is
    # full right to the ends.
    for (zz, back) in ((z0 + 0.018, True), (mid + 0.009, True)):
        for row, ydepth in ((0, YB - 0.075), (1, YB - 0.205)):
            x = x0 + 0.034 + row * 0.022
            guard = 0
            while x < x1 - 0.070 and guard < 40:
                guard += 1
                kind = rnd.random()
                if kind < 0.46:
                    w = rnd.uniform(0.058, 0.094)
                    ob = props.boxprop("K_Pack", x + w * 0.5, ydepth, zz, w,
                                       rnd.uniform(0.048, 0.068),
                                       rnd.uniform(0.185, 0.275), C,
                                       rotz=rnd.uniform(-0.22, 0.22))
                elif kind < 0.58:
                    # one on its side, on top of its neighbour
                    w = rnd.uniform(0.180, 0.245)
                    ob = props.boxprop("K_PackLay", x + w * 0.5, ydepth,
                                       zz + 0.196, rnd.uniform(0.050, 0.068),
                                       rnd.uniform(0.056, 0.074), w, C,
                                       rotz=rnd.uniform(-0.10, 0.10))
                    mlib.rot_y(ob, math.pi * 0.5,
                               (x + w * 0.5, ydepth, zz + 0.196))
                    w = 0.062
                elif kind < 0.80:
                    w = 0.066
                    ob = props.can("K_Can", x + w * 0.5, ydepth, zz, r=0.032,
                                   h=rnd.uniform(0.098, 0.132), cname=C)
                else:
                    w = 0.098
                    ob = props.jar("K_Jar", x + w * 0.5, ydepth, zz, r=0.047,
                                   h=rnd.uniform(0.115, 0.165), cname=C)
                mlib.set_mat(ob, M(packs[rnd.randrange(len(packs))]))
                out.append(ob)
                x += w + rnd.uniform(0.004, 0.018)
            if not back:
                break
    return out


def splashback():
    x0, x1 = L.SPLASH_X
    n = s_tile.courses(L.SPLASH_Z[1] - L.SPLASH_Z[0])
    out = s_tile.field("K_Splash", WALL_P0, WALL_P1, u_of(x1), u_of(x0),
                       L.SPLASH_Z[0], n, cname=C, start_u=u_of(x0))
    # the bead closes the run's west end, so it sits INSIDE the run - placed at
    # u_of(x0) it grows past the wall's own corner into the living room
    out.append(s_tile.stop_bead("K_SplashEnd", WALL_P0, WALL_P1, u_of(x0) - 0.021,
                                L.SPLASH_Z[0], L.SPLASH_Z[0] + s_tile.height(n)
                                + 0.021, cname=C))
    for o in out:
        mlib.set_mat(o, M("M_SplashTile"))
    return out


def counter_dressing():
    """The small stuff.  The set kitchen is DENSE, and the gap between it and a
    rendered one is almost entirely toasters, blocks, jars and a towel roll -
    they cost nothing and they are what the eye reads as "lived in"."""
    out = []
    px0, px1 = L.PEN_X
    pcx = (px0 + px1) * 0.5
    yc = YF + 0.20

    # on the peninsula, at its south end where the stools are
    tb = mlib.rounded_box("K_Toaster", pcx - 0.130, L.PEN_Y[0] + 0.22,
                          L.CTR_H, pcx + 0.130, L.PEN_Y[0] + 0.42,
                          L.CTR_H + 0.185, r=0.030, cname=C)
    mlib.bevel(tb, 0.004, 2, 44)
    mlib.smooth_shade(tb, 34)
    mlib.set_mat(tb, M("M_SteelBrush"))
    out.append(tb)
    for s_ in (-1, 1):
        sl = mlib.box("K_ToastSlot", pcx - 0.096, L.PEN_Y[0] + 0.32 + s_ * 0.030 - 0.013,
                      L.CTR_H + 0.180, pcx + 0.096,
                      L.PEN_Y[0] + 0.32 + s_ * 0.030 + 0.013, L.CTR_H + 0.192, C)
        mlib.set_mat(sl, M("M_BlackPl"))
        out.append(sl)

    # A slant-topped BLOCK.  Swept as a tapering ellipse it came out a red
    # wedge that read as an unidentifiable object rather than as a knife block,
    # and the red-brown barstool timber was the wrong wood for it too.
    bkx, bky = pcx + 0.075, L.PEN_Y[0] + 0.96
    blk = mlib.prism_yz("K_KnifeBlock",
                        [(bky - 0.078, L.CTR_H), (bky + 0.078, L.CTR_H),
                         (bky + 0.078, L.CTR_H + 0.245),
                         (bky - 0.078, L.CTR_H + 0.150)],
                        bkx - 0.062, bkx + 0.062, C)
    mlib.bevel(blk, 0.005, 3, 40)
    mlib.set_mat(blk, M("M_BlockWood"))
    out.append(blk)
    for i in range(4):
        hx = bkx - 0.040 + i * 0.027
        t0 = 0.30 + i * 0.13
        z0 = L.CTR_H + 0.150 + 0.095 * t0
        y0 = bky - 0.078 + 0.156 * t0
        hd = mlib.tube_along("K_Knife%d" % i,
                             [(hx, y0, z0), (hx, y0 + 0.030, z0 + 0.088)],
                             mlib.circle(0.0085, 8), cname=C)
        mlib.smooth_shade(hd, 46)
        mlib.set_mat(hd, M("M_BlackPl"))
        out.append(hd)

    # The paper-towel stand goes in the INSIDE CORNER of the L, tight to the
    # splashback and behind the sink cut-out.  Standing where it used to, at
    # the sink's east lip, its 144 mm foot sat half over the hole with nothing
    # under it.
    px, py = L.K_SINK[0] + 0.075, YB - 0.100
    post = mlib.tube_along("K_TowelPost", [(px, py, L.CTR_H),
                                           (px, py, L.CTR_H + 0.320)],
                           mlib.circle(0.010, 10), cname=C)
    mlib.smooth_shade(post, 46)
    mlib.set_mat(post, M("M_Chrome"))
    out.append(post)
    foot = props.lathe("K_TowelFoot", [(0.0, 0.0), (0.072, 0.0), (0.070, 0.008),
                                       (0.020, 0.014), (0.0, 0.014)], 20, C)
    mlib.translate(foot, (px, py, L.CTR_H))
    mlib.set_mat(foot, M("M_Chrome"))
    out.append(foot)
    roll = props.lathe("K_TowelRoll", [(0.020, 0.0), (0.058, 0.0), (0.060, 0.012),
                                       (0.060, 0.230), (0.058, 0.242),
                                       (0.020, 0.242)], 24, C)
    mlib.translate(roll, (px, py, L.CTR_H + 0.030))
    mlib.set_mat(roll, M("M_PackCream"))
    out.append(roll)

    # Canisters at the BACK OF THE DRAINER, not behind the bowl - behind the
    # bowl is where the mixer stands, and three 108 mm jars parked there swallow
    # the tap whole.
    rnd = random.Random(41)
    for i in range(2):
        jx = L.K_SINK[1] - 0.200 + i * 0.120
        j = props.jar("K_CtrJar%d" % i, jx, YB - 0.108, L.CTR_H, r=0.054,
                      h=rnd.uniform(0.150, 0.215), cname=C)
        mlib.set_mat(j, M("M_Porcelain"))
        out.append(j)

    # kettle on the back burner and a dish rack by the sink
    ket = props.lathe("K_Kettle", [(0.0, 0.0), (0.086, 0.004), (0.098, 0.028),
                                   (0.096, 0.088), (0.070, 0.122),
                                   (0.044, 0.132), (0.042, 0.146),
                                   (0.030, 0.150), (0.0, 0.150)], 24, C)
    mlib.translate(ket, (L.K_STOVE[0] + 0.460, YA + 0.475, 0.982))
    mlib.set_mat(ket, M("M_SteelBrush"))
    out.append(ket)
    spt = mlib.tube_along("K_KettleSpout", [
        (L.K_STOVE[0] + 0.550, YA + 0.475, 1.047),
        (L.K_STOVE[0] + 0.600, YA + 0.475, 1.072),
        (L.K_STOVE[0] + 0.615, YA + 0.475, 1.099)],
        mlib.circle(0.011, 8), cname=C)
    mlib.smooth_shade(spt, 48)
    mlib.set_mat(spt, M("M_SteelBrush"))
    out.append(spt)
    hnd = mlib.tube_along("K_KettleH", [
        (L.K_STOVE[0] + 0.400, YA + 0.475, 1.102),
        (L.K_STOVE[0] + 0.460, YA + 0.475, 1.135),
        (L.K_STOVE[0] + 0.520, YA + 0.475, 1.102)],
        mlib.circle(0.008, 8), cname=C)
    mlib.smooth_shade(hnd, 48)
    mlib.set_mat(hnd, M("M_BlackPl"))
    out.append(hnd)

    # The dish rack stands on the DRAINER - the clear worktop east of the sink -
    # turned through ninety degrees so its 300 mm length runs front-to-back and
    # it fits.  It used to stand in the middle of the bowl with its tray
    # floating at counter level over the hole.
    dx, dy = L.K_SINK[1] - 0.135, YF + 0.285
    tray = mlib.box("K_Rack", dx - 0.114, dy - 0.150, L.CTR_H,
                    dx + 0.114, dy + 0.150, L.CTR_H + 0.020, C)
    mlib.bevel(tray, 0.004, 2, 42)
    mlib.set_mat(tray, M("M_BlackPl"))
    out.append(tray)
    for i in range(7):
        wy = dy - 0.120 + i * 0.040
        w = mlib.tube_along("K_RackW%d" % i, [
            (dx - 0.096, wy, L.CTR_H + 0.020),
            (dx - 0.068, wy, L.CTR_H + 0.100),
            (dx + 0.068, wy, L.CTR_H + 0.100),
            (dx + 0.096, wy, L.CTR_H + 0.020)],
            mlib.circle(0.0025, 6), cname=C)
        mlib.smooth_shade(w, 50)
        mlib.set_mat(w, M("M_Chrome"))
        out.append(w)
    for i in range(3):
        pl = props.lathe("K_Plate%d" % i, [(0.0, 0.0), (0.086, 0.006),
                                           (0.080, 0.013), (0.076, 0.015),
                                           (0.0, 0.007)], 24, C)
        mlib.rot_x(pl, math.radians(84.0))
        mlib.rotate_z(pl, math.pi * 0.5)
        mlib.translate(pl, (dx, dy - 0.080 + i * 0.078, L.CTR_H + 0.100))
        mlib.set_mat(pl, M("M_Porcelain"))
        out.append(pl)

    bin_ = props.lathe("K_Bin", [(0.0, 0.0), (0.145, 0.0), (0.150, 0.014),
                                 (0.162, 0.500), (0.168, 0.520),
                                 (0.162, 0.536), (0.120, 0.548),
                                 (0.0, 0.552)], 26, C)
    # The bin lives against the east wall UNDER THE POSTER, by the front door,
    # not in the kitchen alcove.  x is set off the baseboard's face, which
    # stands 22 mm proud of the plaster, so the can touches the skirting rather
    # than the wall behind it.
    mlib.translate(bin_, (L.EX - L.BASE_T - 0.168, 1.05, 0.0))
    mlib.set_mat(bin_, M("M_SteelBrush"))
    out.append(bin_)

    fb = props.bowl("K_FruitBowl", pcx, L.PEN_Y[0] + 0.64, L.CTR_H, r=0.130,
                    h=0.076, cname=C)
    mlib.set_mat(fb, M("M_Porcelain"))
    out.append(fb)
    for i in range(5):
        a = math.tau * i / 5
        fr = props.lathe("K_Fruit%d" % i, [(0.0, 0.0), (0.028, 0.010),
                                           (0.034, 0.032), (0.026, 0.052),
                                           (0.0, 0.058)], 14, C)
        mlib.translate(fr, (pcx + 0.050 * math.cos(a),
                            L.PEN_Y[0] + 0.64 + 0.050 * math.sin(a),
                            L.CTR_H + 0.030))
        mlib.set_mat(fr, M(["M_PackRed", "M_PackOrange", "M_PackGreen",
                            "M_PackYellow", "M_PackRed"][i]))
        out.append(fr)
    return out


def stool(name, cx, cy):
    """Turned legs splaying out of a velvet drum, with a chrome foot ring."""
    out = []
    h = L.STOOL_H
    seat_z = h - 0.135
    for i in range(4):
        a = math.pi * 0.25 + math.pi * 0.5 * i
        r0, r1 = 0.205, 0.118
        p0 = (cx + r0 * math.cos(a), cy + r0 * math.sin(a), 0.0)
        p1 = (cx + r1 * math.cos(a), cy + r1 * math.sin(a), seat_z + 0.010)
        lg = props.sweep_var(name + "_l%d" % i,
                             [p0,
                              tuple(0.72 * Vector(p0) + 0.28 * Vector(p1)),
                              tuple(0.34 * Vector(p0) + 0.66 * Vector(p1)),
                              p1],
                             [(0.0175, 0.0175), (0.0215, 0.0215),
                              (0.0180, 0.0180), (0.0205, 0.0205)], 12, C)
        mlib.set_mat(lg, M("M_StoolWood"))
        out.append(lg)
    ring = props.torus(name + "_ring", 0.176, 0.0085, 28, 8, C, cx=cx, cy=cy,
                       cz=0.215)
    mlib.set_mat(ring, M("M_Chrome"))
    out.append(ring)
    for i in range(4):
        a = math.pi * 0.25 + math.pi * 0.5 * i
        st = mlib.tube_along(name + "_st%d" % i,
                             [(cx + 0.176 * math.cos(a), cy + 0.176 * math.sin(a), 0.215),
                              (cx + 0.152 * math.cos(a), cy + 0.152 * math.sin(a), 0.300)],
                             mlib.circle(0.0055, 8), cname=C)
        mlib.smooth_shade(st, 50)
        mlib.set_mat(st, M("M_Chrome"))
        out.append(st)

    plate = props.lathe(name + "_pl", [(0.0, 0.0), (0.150, 0.0), (0.154, 0.010),
                                       (0.150, 0.018), (0.0, 0.018)], 26, C)
    mlib.translate(plate, (cx, cy, seat_z - 0.018))
    mlib.set_mat(plate, M("M_StoolWood"))
    out.append(plate)

    drum = props.lathe(name + "_seat",
                       [(0.0, 0.0), (0.170, 0.0), (0.186, 0.020), (0.192, 0.048),
                        (0.190, 0.092), (0.176, 0.120), (0.140, 0.134),
                        (0.078, 0.140), (0.0, 0.141)], 30, C)
    mlib.translate(drum, (cx, cy, seat_z))
    mlib.set_mat(drum, M("M_StoolVel"))
    out.append(drum)
    pipe = props.torus(name + "_pipe", 0.1885, 0.0075, 30, 8, C, cx=cx, cy=cy,
                       cz=seat_z + 0.024)
    mlib.set_mat(pipe, M("M_StoolVel"))
    out.append(pipe)
    return out


# ================================================================== the dog

def _hound_ring(x, zc, w, up, dn, n=28, k=1.25):
    """One cross-section of the hound, in the YZ plane at station x.

    A dog is not elliptical in section: the back is a shallow arch and the
    brisket is a deep narrow keel, so `up` and `dn` are given separately.  `k`
    squares the section off a little towards the flanks, which is what keeps a
    rib cage from reading as a balloon.
    """
    pts = []
    for i in range(n):
        t = math.tau * i / n
        c, s = math.cos(t), math.sin(t)
        r = up if s >= 0.0 else dn
        cc = math.copysign(abs(c) ** (1.0 / k), c) if abs(c) > 1e-9 else 0.0
        ss = math.copysign(abs(s) ** (1.0 / k), s) if abs(s) > 1e-9 else 0.0
        pts.append((x, w * cc, zc + r * ss))
    return pts


def dog():
    """Pat - the oversized white ceramic greyhound, standing in the corner
    behind the couch.

    Built as a LOFT of real cross-sections rather than a swept tube.  A tube
    has one radius per station, so a dog made of one gives a round sausage
    where the animal has a shallow arched back over a deep narrow keel of a
    chest - and no amount of grading the radius fixes that, because the fault
    is that the section is the wrong SHAPE, not the wrong size.  With the top
    and bottom of every section set independently the topline, the brisket and
    the tuck-up are all under control, and the silhouette from the side and
    the silhouette from the front can be right at the same time.

    The stations run nose to tail:  a long lean head with a real stop, a neck
    that arches out of high withers, the deepest point of the chest behind the
    elbow, a waist narrow enough to see daylight under, the roached loin a
    running hound carries, and a croup falling away to the tail set.
    """
    out = []
    # (x, z of the section centre, half width, above centre, below centre)
    body = [
        (-0.622, 0.792, 0.012, 0.011, 0.013),   # nose
        (-0.598, 0.793, 0.024, 0.021, 0.026),
        (-0.556, 0.798, 0.034, 0.028, 0.038),   # muzzle
        (-0.508, 0.808, 0.038, 0.032, 0.044),
        (-0.470, 0.824, 0.043, 0.040, 0.048),   # stop
        (-0.440, 0.843, 0.050, 0.045, 0.052),
        (-0.406, 0.861, 0.056, 0.048, 0.055),   # skull
        (-0.372, 0.864, 0.055, 0.046, 0.058),
        # A crested neck, not a tube.  The reference statue's neck is thick
        # where it leaves the shoulder and arches hard up to the head; graded
        # straight it reads as a swan and the head looks stuck on the end.
        (-0.342, 0.856, 0.052, 0.044, 0.066),   # occiput / throat latch
        (-0.302, 0.834, 0.053, 0.046, 0.082),
        (-0.256, 0.802, 0.059, 0.052, 0.100),   # crest
        (-0.208, 0.760, 0.067, 0.058, 0.116),
        (-0.160, 0.714, 0.075, 0.062, 0.128),
        (-0.114, 0.676, 0.085, 0.065, 0.136),   # withers
        (-0.062, 0.654, 0.090, 0.069, 0.148),   # shoulder
        (-0.006, 0.642, 0.090, 0.070, 0.156),   # deepest brisket
        (0.052, 0.638, 0.083, 0.070, 0.146),
        (0.108, 0.634, 0.072, 0.068, 0.124),    # last rib
        (0.164, 0.632, 0.058, 0.062, 0.092),
        (0.212, 0.634, 0.053, 0.060, 0.076),    # waist / tuck-up
        (0.262, 0.642, 0.060, 0.064, 0.072),
        (0.312, 0.650, 0.070, 0.068, 0.074),    # roached loin
        (0.362, 0.650, 0.078, 0.068, 0.080),
        (0.412, 0.640, 0.079, 0.064, 0.084),    # croup
        (0.456, 0.622, 0.068, 0.056, 0.078),
        (0.494, 0.598, 0.050, 0.042, 0.056),    # tail set
        (0.516, 0.584, 0.032, 0.028, 0.034),
        (0.530, 0.578, 0.014, 0.013, 0.015)]
    rings = [_hound_ring(x, zc, w, up, dn) for (x, zc, w, up, dn) in body]
    out.append(mlib.smooth_shade(
        mlib.loft("K_Dog", rings, close_u=False, close_v=True, cname=C,
                  cap_start=True, cap_end=True), 80))

    # muzzle and eyes: three small solids, but they are the difference between
    # a head and a cone
    nose = props.lathe("K_DogNose", [(0.0, 0.0), (0.014, 0.002), (0.016, 0.010),
                                     (0.012, 0.017), (0.0, 0.019)], 18, C)
    props.face_x(nose, -1.0, (-0.618, 0.0, 0.796))
    out.append(nose)
    for s in (-1, 1):
        ey = props.lathe("K_DogEye%d" % (s > 0), [
            (0.0, 0.0), (0.013, 0.001), (0.014, 0.006), (0.010, 0.011),
            (0.0, 0.013)], 16, C)
        props.face_y(ey, s * 1.0, (-0.452, s * 0.036, 0.844))
        out.append(ey)
        br = props.sweep_var("K_DogBrow%d" % (s > 0), [
            (-0.470, s * 0.030, 0.856), (-0.446, s * 0.040, 0.862),
            (-0.424, s * 0.044, 0.860)],
            [(0.010, 0.007), (0.013, 0.009), (0.010, 0.007)], 12, C, smooth=76)
        out.append(br)

    for s in (-1, 1):
        # foreleg: shoulder blade, elbow, then a straight column to the pastern
        # The top of the leg has to stay INSIDE the ribcage.  Run wider than
        # the body is at that station and it breaks the silhouette as a flat
        # slab hanging off the shoulder, which is what it was doing.
        out.append(props.sweep_var("K_DogFL%d" % (s > 0), [
            (-0.098, s * 0.046, 0.678), (-0.094, s * 0.058, 0.566),
            (-0.088, s * 0.064, 0.478), (-0.084, s * 0.066, 0.382),
            (-0.084, s * 0.066, 0.272), (-0.086, s * 0.066, 0.162),
            (-0.086, s * 0.066, 0.076), (-0.074, s * 0.066, 0.026),
            (-0.058, s * 0.066, 0.011)],
            [(0.036, 0.060), (0.031, 0.053), (0.026, 0.043), (0.021, 0.031),
             (0.017, 0.024), (0.016, 0.021), (0.017, 0.023), (0.021, 0.026),
             (0.024, 0.014)], 18, C, smooth=76))
        # hind leg: the greyhound's long angulation - stifle forward under the
        # loin, hock well back, then a straight cannon down to the foot
        # The thigh starts SMALL and HIGH, well inside the pelvis, and only
        # reaches its full width once it is clear of the flank.  Started at
        # full width level with the hip it cut a hard crescent across the body
        # where it came out, and the whole haunch read as a lump stuck on.
        out.append(props.sweep_var("K_DogHL%d" % (s > 0), [
            (0.398, s * 0.042, 0.656), (0.376, s * 0.058, 0.578),
            (0.350, s * 0.070, 0.502), (0.322, s * 0.076, 0.428),
            (0.348, s * 0.076, 0.352), (0.404, s * 0.074, 0.284),
            (0.410, s * 0.072, 0.196), (0.404, s * 0.072, 0.098),
            (0.392, s * 0.072, 0.030), (0.372, s * 0.072, 0.011)],
            [(0.032, 0.072), (0.045, 0.086), (0.048, 0.082), (0.038, 0.064),
             (0.028, 0.042), (0.021, 0.030), (0.017, 0.023), (0.017, 0.023),
             (0.020, 0.025), (0.024, 0.014)], 18, C, smooth=76))
        # rose ear: small, folded back flat against the skull
        out.append(props.sweep_var("K_DogEar%d" % (s > 0), [
            (-0.398, s * 0.040, 0.888), (-0.376, s * 0.052, 0.898),
            (-0.352, s * 0.058, 0.892), (-0.330, s * 0.054, 0.876),
            (-0.314, s * 0.044, 0.860), (-0.306, s * 0.036, 0.850)],
            [(0.009, 0.014), (0.013, 0.022), (0.014, 0.024), (0.012, 0.020),
             (0.008, 0.013), (0.004, 0.006)], 14, C, smooth=76))

    # Tail: low set, sweeping down and back with the slight upward hook at the
    # tip that every greyhound has.  It STARTS INSIDE THE CROUP, two stations
    # forward of where the body tapers away - begun at the body's own tail-end
    # its 26 mm root was wider than the 14 mm the body had left there, so it
    # bulged out of the tip as a separate blob.
    out.append(props.sweep_var("K_DogTail", [
        (0.462, 0.0, 0.616), (0.508, 0.002, 0.584), (0.552, 0.008, 0.528),
        (0.596, 0.016, 0.450), (0.612, 0.024, 0.364), (0.594, 0.032, 0.292),
        (0.556, 0.038, 0.248), (0.512, 0.040, 0.234), (0.482, 0.040, 0.242)],
        [(0.030, 0.034), (0.027, 0.030), (0.022, 0.024), (0.017, 0.018),
         (0.013, 0.014), (0.010, 0.011), (0.008, 0.009), (0.006, 0.007),
         (0.004, 0.004)], 14, C, smooth=76))

    grp = mlib.join(out, "K_DogStatue", C)
    mlib.scale_mesh(grp, L.DOG_SCALE)
    mlib.translate(grp, (0.0, 0.0, 0.002))
    mlib.rotate_z(grp, math.radians(L.DOG_ROT))
    mlib.translate(grp, (L.DOG[0], L.DOG[1], 0.0))
    mlib.set_mat(grp, M("M_Porcelain"))
    return [grp]


# ================================================================== dartboard

def dartboard():
    """A real segmented board: twenty radial sectors, six concentric bands,
    each face given the slot its number and ring say it should have.

    It hangs on JOEY'S BEDROOM DOOR.  It used to be on the kitchen return
    between the wall's turn and the cabinet run, which is a strip of wall the
    cabinets should be filling; and a door is where a dartboard goes anyway.
    Joey's leaf is therefore the one interior door in the flat that stands
    SHUT - hung open at 86 degrees the board is edge-on to the whole room.
    """
    out = []
    R = 0.2175
    bands = [(0.0, 0.0064, 'wire'), (0.0064, 0.0159, 'bull'),
             (0.0159, 0.0955, 'body'), (0.0955, 0.1069, 'ring'),
             (0.1069, 0.1620, 'body'), (0.1620, 0.1700, 'ring')]
    verts, faces, slot = [], [], []
    NS = 20
    FACE_Y = 0.014          # the sheet is solidified symmetrically about this

    def ang(k):
        return math.pi * 0.5 + math.pi / NS + k * (math.tau / NS)

    def quad(n0):
        # wound so the surface normal comes OUT of the wall (+Y), which is what
        # decides which way solidify grows and which way the board faces
        faces.append((n0 + 3, n0 + 2, n0 + 1, n0))

    for si in range(NS):
        a0, a1 = ang(si), ang(si + 1)
        dark = si % 2 == 0
        for (r0, r1, kind) in bands:
            if kind in ('wire', 'bull'):
                continue
            n0 = len(verts)
            for (rr, aa) in ((r0, a0), (r1, a0), (r1, a1), (r0, a1)):
                verts.append((rr * math.cos(aa), FACE_Y, rr * math.sin(aa)))
            quad(n0)
            slot.append((0 if dark else 1) if kind == 'ring'
                        else (2 if dark else 3))
    for (r0, r1, mi) in ((0.0, 0.0064, 0), (0.0064, 0.0159, 1), (0.170, R, 2)):
        n0 = len(verts)
        for k in range(48):
            a = math.tau * k / 48
            verts.append((r0 * math.cos(a), FACE_Y, r0 * math.sin(a)))
            verts.append((r1 * math.cos(a), FACE_Y, r1 * math.sin(a)))
        for k in range(48):
            a, b = 2 * k, 2 * ((k + 1) % 48)
            faces.append((n0 + b, n0 + b + 1, n0 + a + 1, n0 + a))
            slot.append(mi)

    face = mlib.mesh_obj("K_DartFace", verts, faces, C)
    mlib.assign_mats(face, [M("M_DartRed"), M("M_DartGreen"),
                            M("M_DartBlack"), M("M_DartCream")])
    for p, mi in zip(face.data.polygons, slot):
        p.material_index = mi
    face.data.update()
    # centred solidify, so the board spans -2 mm (into the plaster) to +30 mm
    # whichever way the winding came out
    mlib.solidify(face, 0.032, offset=0)
    mlib.apply_all(face)
    out.append(face)

    # the spider: a wire on every sector boundary and round each ring
    wires = []
    for si in range(NS):
        a = ang(si)
        wires.append(mlib.tube_along("K_DartW", [
            (0.0159 * math.cos(a), 0.0325, 0.0159 * math.sin(a)),
            (0.170 * math.cos(a), 0.0325, 0.170 * math.sin(a))],
            mlib.circle(0.0011, 6), cname=C))
    for rr in (0.0159, 0.0955, 0.1069, 0.1620, 0.170):
        t = props.torus("K_DartR", rr, 0.0011, 44, 6, C)
        mlib.rot_x(t, math.pi * 0.5)
        mlib.translate(t, (0, 0.0325, 0))
        wires.append(t)
    sp = mlib.join(wires, "K_DartWire", C)
    mlib.set_mat(sp, M("M_Chrome"))
    out.append(sp)

    # Hung on the leaf as if the door were shut, then SWUNG WITH IT - the leaf
    # stands open at DOOR_OPEN like the other two, and a board screwed to a
    # door has to travel with the door.
    #
    # make_door pivots the leaf about its hinge stile in the door's own frame,
    # and to_wall then maps that frame onto the wall with a reflection (door x
    # becomes world y, door y becomes world x), which flips the sense of the
    # rotation.  So the world swing is +DOOR_OPEN where the leaf's own is
    # -DOOR_OPEN, about the hinge line at the middle of the reveal.
    props.wall_place(out, 'W', L.DART_X, L.DART_Z, L.DART_AT)
    piv = (L.BED_E + (L.BW_TH - 0.042) * 0.5, L.JOEY_DOOR[0] + 0.005)
    for o in out:
        mlib.rotate_z(o, math.radians(L.DOOR_OPEN), piv)
    return out


def dart_mats():
    mats.plastic("M_DartRed", 'A8241F', rough=0.36)
    mats.plastic("M_DartGreen", '15613A', rough=0.36)
    mats.plastic("M_DartBlack", '18181A', rough=0.44)
    mats.plastic("M_DartCream", 'DFD3AE', rough=0.40)


# ================================================================== build

def build():
    mlib.purge("K_")
    mlib.coll(C)
    materials()
    dart_mats()
    counter_run()
    range_()
    fridge()
    wall_units()
    over_range_micro()
    food_shelf()
    splashback()
    counter_dressing()
    stool("K_StoolA", *L.STOOL_A)
    stool("K_StoolB", *L.STOOL_B)
    dog()
    dartboard()
    return len([o for o in bpy.data.objects if o.name.startswith("K_")])
