"""Monica's and Rachel's bedrooms - the east block, laid out as the plan shows:
bed head against the east exterior wall under the window, a nightstand each
side, a chest of drawers on the inner wall.  Rachel's room is entered through
the cased opening in the central wall; Monica's through the door at the north
end of that wall, off the window alcove."""
import bpy, math, random
import mlib, mats, L, props as P
import f_living as FL

B = "Bedrooms"


def mk_mats():
    M = {}
    BOK = ('A8783C', '7E5426', '4E3216')
    BKK = dict(ring=14.0, warp=0.11, warp_scale=1.2, distort=1.6, blotch=0.16,
               bump=0.10, rough=(0.18, 0.30))
    M['oak'] = mats.wood('wood_bed_oak', BOK, axis='YZ', **BKK)
    M['oak_v'] = mats.wood('wood_bed_oak_v', BOK, axis='XY', **BKK)
    # drawer fronts want their grain running across, i.e. rings varying up the
    # face: 'YZ' put a 45-degree chevron on every one of them
    M['oak_h'] = mats.wood('wood_bed_oak_h', BOK, axis='Z', **BKK)
    M['white'] = mats.paint('paint_bed_white', 'E9E3D4', rough=0.28, coat=0.30)
    M['linen'] = mats.fabric('fabric_linen_white', 'D8D2C0', rough=0.84,
                             sheen=0.20, weave=520)
    # at scale ~2 the blossoms were 40 cm across and read as paint splashes
    M['quiltA'] = mats.floral_chintz('chintz_quilt_a', ground='BEC6CC',
                                     petal='AE7480', petal2='C69CA6',
                                     leaf='566B52', leaf2='87977A', scale=9.0)
    M['quiltB'] = mats.floral_chintz('chintz_quilt_b', ground='C9B084',
                                     petal='9C4A3C', petal2='C4795A',
                                     leaf='5A6238', leaf2='90A05E', scale=6.8)
    M['rug'] = mats.fabric('fabric_bed_rug', 'A88C6E', rough=0.9, sheen=0.1,
                           weave=340, bump=0.5)
    M['brass'] = mats.get('metal_brass')
    return M


def bedspread(name, cx, cy, ln, wd, ztop, drop, cname, seed=0):
    """A spread that goes *over* the mattress and hangs down its sides.

    A pad laid on the mattress top is a printed board - you only ever see its
    face, it has no edge, and the bed reads as a box with a picture on it.  What
    makes bedding read is the fall at the edge and the softness across the top,
    so this is a closed shell wider and longer than the mattress, standing proud
    of it and wrapping past its sides."""
    rng = random.Random(seed)
    s1, s2 = rng.uniform(0, math.tau), rng.uniform(0, math.tau)
    pts = mlib.rounded_rect(ln, wd, 0.115, seg=6)
    LEV = ((0.00, 0.94), (0.16, 0.99), (0.45, 1.0), (0.74, 1.0),
           (0.90, 0.985), (1.00, 0.93))
    rings = []
    for (t, s) in LEV:
        z = ztop - drop + drop * t
        row = []
        for (x, y) in pts:
            # crumple, strongest across the top face and dying out down the fall
            wr = (0.011 * math.sin(x * 5.7 + s1) + 0.009 * math.sin(y * 8.1 + s2)
                  + 0.006 * math.sin((x + y) * 10.6 + s1 * 1.7)) * (t ** 2)
            row.append((cx + x * s, cy + y * s, z + wr))
        rings.append(row)
    ob = mlib._loft(name, rings, close_u=False, close_v=True, cname=cname,
                    cap_start=True, cap_end=True)
    mlib.bevel(ob, 0.006, 2, 55)
    mlib.smooth_shade(ob, 48)
    return ob


def bed(name, cy, M, quilt, cname=B):
    """Bed with its head against the east wall (X = EXT_E)."""
    x1 = L.EXT_E - 0.03
    x0 = x1 - L.BED_L
    w = L.BED_W
    y0, y1 = cy - w / 2, cy + w / 2
    parts = []
    # headboard against the east wall
    hb = mlib.prism_yz(name + "_hb",
                       [(y0, 0.10), (y1, 0.10), (y1, 0.98), (y1 - 0.06, 1.04),
                        (y0 + 0.06, 1.04), (y0, 0.98)], x1 - 0.055, x1, cname)
    mlib.bevel(hb, 0.008, 2, 45)
    parts.append((hb, M['oak_v']))
    # frame rails + footboard
    for nm, a in ((name + "_rl", (x0, y0, 0.14, x1 - 0.05, y0 + 0.055, 0.40)),
                  (name + "_rr", (x0, y1 - 0.055, 0.14, x1 - 0.05, y1, 0.40)),
                  (name + "_fb", (x0, y0, 0.14, x0 + 0.055, y1, 0.60))):
        o = mlib.box(nm, a[0], a[1], a[2], a[3], a[4], a[5], cname)
        mlib.bevel(o, 0.006, 2, 45)
        parts.append((o, M['oak']))
    for (fx, fy) in ((x0 + 0.03, y0 + 0.03), (x0 + 0.03, y1 - 0.03),
                     (x1 - 0.05, y0 + 0.03), (x1 - 0.05, y1 - 0.03)):
        lg = mlib.revolve(name + "_lg", [(0.0, 0.0), (0.030, 0.006),
                                         (0.034, 0.030), (0.030, 0.14),
                                         (0.0, 0.14)], 14, cname=cname)
        mlib.translate(lg, (fx, fy, 0.0))
        mlib.smooth_shade(lg, 40)
        parts.append((lg, M['oak_v']))
    objs = []
    for o, mm in parts:
        mlib.set_mat(o, mm)
        objs.append(o)
    # mattress + duvet + pillows
    mat_ = mlib.cushion(name + "_mat", L.BED_L - 0.12, w - 0.10, 0.22, 0.06, cname)
    mlib.translate(mat_, ((x0 + x1) / 2 - 0.02, cy, 0.40))
    mlib.set_mat(mat_, M['linen'])
    # The spread has to hang PAST the mattress at the foot.  At BED_L - 0.26 its
    # foot fall landed within about 10 mm of the mattress's own bulged end face
    # (cushion() swells to 1.055 of its plan outline at mid height), and the two
    # surfaces z-fought along that edge on both beds.
    duv = bedspread(name + "_duv", (x0 + x1) / 2 - 0.12, cy, L.BED_L - 0.02,
                    w + 0.14, 0.665, 0.30, cname, seed=int(abs(cy) * 97) % 991)
    mlib.set_mat(duv, quilt)
    for s in (-1, 1):
        pw = mlib.cushion(name + "_pw%d" % (s + 1), 0.44, 0.62, 0.175, 0.085,
                          cname)
        mlib.rot_y(pw, math.radians(-21))
        mlib.rot_x(pw, math.radians(s * 3.5))
        mlib.translate(pw, (x1 - 0.34, cy + s * 0.325, 0.615))
        mlib.set_mat(pw, M['linen'])
    # nightstands flanking the head
    for s in (-1, 1):
        ns = []
        nx, ny = x1 - 0.24, cy + s * (w / 2 + 0.34)
        body = mlib.box(name + "_ns", nx - 0.22, ny - 0.22, 0.09, nx + 0.22,
                        ny + 0.22, 0.56, cname)
        mlib.bevel(body, 0.006, 2, 45)
        ns.append(body)
        top = mlib.box(name + "_nt", nx - 0.245, ny - 0.245, 0.56, nx + 0.245,
                       ny + 0.245, 0.60, cname)
        mlib.bevel(top, 0.005, 3, 40)
        ns.append(top)
        dw = mlib.box(name + "_nd", nx - 0.245, ny - 0.185, 0.20, nx - 0.222,
                      ny + 0.185, 0.44, cname)
        mlib.bevel(dw, 0.004, 2, 45)
        ns.append(dw)
        for o in ns:
            mlib.set_mat(o, M['oak_h'])
        kb = mlib.revolve(name + "_nk", [(0.0, 0.0), (0.016, 0.004),
                                         (0.018, 0.012), (0.010, 0.020),
                                         (0.0, 0.022)], 14, cname=cname)
        mlib.rot_y(kb, -math.pi / 2)
        mlib.translate(kb, (nx - 0.246, ny, 0.32))
        mlib.smooth_shade(kb, 40)
        mlib.set_mat(kb, M['brass'])
        FL.table_lamp(name + "_lamp%d" % (s + 1), nx, ny, 0.60, ML, cname,
                      energy=14.0, scale=0.78)
    return objs


def chest(name, cx, cy, rotz, M, cname=B, w=1.02, d=0.46, h=0.86):
    parts = []
    body = mlib.box(name + "_b", -d / 2, -w / 2, 0.075, d / 2, w / 2, h - 0.04,
                    cname)
    mlib.bevel(body, 0.008, 2, 45)
    parts.append(body)
    top = mlib.box(name + "_t", -d / 2 - 0.022, -w / 2 - 0.022, h - 0.04,
                   d / 2 + 0.022, w / 2 + 0.022, h, cname)
    mlib.bevel(top, 0.006, 3, 40)
    parts.append(top)
    for k in range(3):
        z = 0.10 + k * (h - 0.20) / 3
        dw = mlib.box(name + "_d%d" % k, -d / 2 - 0.020, -w / 2 + 0.03, z + 0.008,
                      -d / 2, w / 2 - 0.03, z + (h - 0.20) / 3 - 0.008, cname)
        mlib.bevel(dw, 0.004, 2, 45)
        parts.append(dw)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        lg = mlib.box(name + "_lg", sx * (d / 2 - 0.055) - 0.028,
                      sy * (w / 2 - 0.055) - 0.028, 0.0,
                      sx * (d / 2 - 0.055) + 0.028,
                      sy * (w / 2 - 0.055) + 0.028, 0.080, cname)
        mlib.bevel(lg, 0.005, 2, 45)
        parts.append(lg)
    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, M['oak'])
    knobs = []
    for k in range(3):
        z = 0.10 + k * (h - 0.20) / 3 + (h - 0.20) / 6
        for s in (-1, 1):
            kb = mlib.revolve(name + "_k", [(0.0, 0.0), (0.018, 0.006),
                                            (0.020, 0.016), (0.011, 0.026),
                                            (0.0, 0.028)], 14, cname=cname)
            mlib.rot_y(kb, -math.pi / 2)
            mlib.translate(kb, (-d / 2 - 0.021, s * 0.22, z))
            knobs.append(kb)
    ko = mlib.join(knobs, name + "_knobs", cname)
    mlib.smooth_shade(ko, 40)
    mlib.set_mat(ko, M['brass'])
    for o in (ob, ko):
        mlib.rotate_z(o, rotz)
        mlib.translate(o, (cx, cy, 0.0))
    return [ob, ko]


def area_rug(name, cx, cy, w, d, M, cname=B):
    ob = mlib.prism(name, mlib.rounded_rect(w, d, 0.03, 3), 0.0008, 0.0108, cname)
    mlib.bevel(ob, 0.003, 2, 40)
    mlib.set_mat(ob, M['rug'])
    ob.location = (cx, cy, 0.0)
    return ob


ML = None


def build():
    global ML
    M = mk_mats()
    ML = FL.mk_mats()
    gold = mats.get('paint_gilt') or mats.paint('paint_gilt', 'C9A24A', rough=0.30)

    # ------------------------------------------------------ Rachel's bedroom
    bed("RB_bed", L.RB_WIN_Y, M, M['quiltA'])
    chest("RB_chest", L.BED_X[0] + 0.28, L.RB_Y[0] + 0.95, 0.0, M)
    area_rug("RB_rug", 9.90, L.RB_WIN_Y - 0.10, 1.60, 2.10, M)
    # the picture and the sconce hang on the solid parts of the inner wall -
    # north of the cased opening and south of it, never across the void
    P.framed("RB_art", 0.40, 0.52, (L.EXW + 0.030,
                                    (L.CD_Y[1] + L.RB_Y[1]) * 0.5, 1.62),
             (1, 0), B, framemat=gold,
             artmat=mats.botanical('art_rb', normal=(1, 0), seed=11,
                                   ground='E7DEC0', stem='53642F',
                                   leafc=('40602C', '75894C'),
                                   bloom=('B4604A', 'E3B98E')))
    FL.sconce("RB_sconce", (L.EXW + 0.02, L.CD_Y[0] - 0.62, 1.80), (1, 0), ML, B,
              energy=16.0)

    # ------------------------------------------------------ Monica's bedroom
    bed("MB_bed", L.MB_WIN_Y, M, M['quiltB'])
    # Her doorway moved south down this wall, so the chest, the picture over it
    # and the sconce all key off the door's north jamb rather than off the room,
    # which is what kept putting the chest in the opening.
    chest("MB_chest", L.BED_X[0] + 0.28, L.MD_Y[1] + 0.68, 0.0, M)
    area_rug("MB_rug", 9.90, L.MB_WIN_Y + 0.10, 1.60, 2.10, M)
    P.framed("MB_art", 0.36, 0.46, (L.EXW + 0.030, L.MD_Y[1] + 0.68, 1.62),
             (1, 0), B, framemat=gold,
             artmat=mats.botanical('art_mb', normal=(1, 0), seed=19,
                                   ground='E2DCC4', stem='4C5C38',
                                   leafc=('44583A', '7A8A5A'),
                                   bloom=('8A6C92', 'C7B2CE')))
    FL.sconce("MB_sconce", (L.EXW + 0.02, L.MB_Y[1] - 0.85, 1.80), (1, 0), ML, B,
              energy=16.0)
    print("bedrooms built")


def _pan_ring(hw, yb, yf, z, n=44, waist=0.38):
    """One horizontal section through a china pan.  Not an ellipse and not a
    rounded rectangle: an egg.  The widest line sits back of centre (`waist` of
    the way from the back), the tail behind it is blunt and the nose in front of
    it is long and tapered, which is what makes a lavatory read as a lavatory
    rather than as a lathed bollard."""
    cy = yb + (yf - yb) * waist
    ring = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        c = math.cos(a)
        ring.append((hw * math.sin(a),
                     cy + (yf - cy) * c if c >= 0 else cy + (cy - yb) * c,
                     z))
    return ring


def water_closet(name, cx, cy, cname, wht, chrome, wall_y):
    """A close-coupled two-piece WC standing against a wall to the south.
    Local +Y is the way it faces.  The old one was a lathed bowl and a plain
    box - round in plan, which no lavatory is, and with the tank simply floating
    behind it.  This one is lofted from real sections: a flared foot, a waisted
    ankle, an egg-shaped bowl hollowed down to the trap, a squared casting shelf
    for the tank to bolt to, seat and lid, trip lever and supply."""
    # One vertical stack of numbers, so nothing can drift out of register:
    # rim -> seat -> lid -> the shelf the closed lid stops against -> tank.
    RIM = 0.395
    SEAT_T, LID_T = 0.019, 0.026
    SHELF_Z = RIM + SEAT_T + LID_T + 0.007      # 0.446
    TANK_Z, TLID_Z = SHELF_Z + 0.310, SHELF_Z + 0.340
    HW, YB, YF = 0.185, -0.118, 0.352           # rim, at its widest: 0.47 long
    SY = -0.254                                 # centre of tank/shelf in Y
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
    pan = mlib.loft(name + "_pan", rings, close_v=True, cname=cname,
                    cap_start=True, cap_end=True)
    mlib.smooth_shade(pan, 44)
    parts.append(pan)
    # The plinth the tank bolts down onto, lofted rather than boxed: narrow and
    # deep where it grows out of the skirt, spreading at the top.  As a plain
    # block it hung off the back of the pedestal.  It is deliberately narrower
    # than the tank, so the tank overhangs it the way a real one does and there
    # is somewhere underneath for the supply to land.
    shelf = mlib.loft(name + "_shelf", [
        # every ring flush with the tank's back face at -0.352, so the plinth
        # cannot creep out behind the tank and into the wall
        [(x, y - 0.250, 0.170) for (x, y) in mlib.rounded_rect(0.196, 0.204, 0.046, 4)],
        [(x, y - 0.246, 0.290) for (x, y) in mlib.rounded_rect(0.250, 0.212, 0.044, 4)],
        [(x, y - 0.257, 0.396) for (x, y) in mlib.rounded_rect(0.310, 0.190, 0.036, 4)],
        [(x, y - 0.264, SHELF_Z) for (x, y) in mlib.rounded_rect(0.330, 0.176, 0.030, 4)],
    ], close_v=True, cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(shelf, 0.008, 2, 52)
    mlib.smooth_shade(shelf, 46)
    parts.append(shelf)
    # ...and the low flat between the rim and the plinth that the seat's hinge
    # bolts pass through.  Without it the seat hinged onto thin air.
    flat = mlib.prism(name + "_hflat",
                      mlib.rounded_rect(0.320, 0.090, 0.026, 3), 0.320, RIM,
                      cname)
    mlib.translate(flat, (0.0, -0.150, 0.0))
    mlib.bevel(flat, 0.008, 2, 50)
    parts.append(flat)
    # tank, and its lid overhanging on every side
    tank = mlib.prism(name + "_tank",
                      mlib.rounded_rect(0.428, 0.196, 0.026, 4),
                      SHELF_Z - 0.006, TANK_Z, cname)
    mlib.translate(tank, (0.0, SY, 0.0))
    mlib.bevel(tank, 0.012, 3, 46)
    parts.append(tank)
    lid = mlib.prism(name + "_tanklid",
                     mlib.rounded_rect(0.452, 0.220, 0.030, 4), TANK_Z, TLID_Z,
                     cname)
    mlib.translate(lid, (0.0, SY, 0.0))
    mlib.bevel(lid, 0.009, 3, 46)
    parts.append(lid)
    body = mlib.join(parts, name, cname)
    mlib.set_mat(body, wht)

    # ------------------------------------------------------------ seat + lid
    # Both follow the rim's own outline, so they overhang it by a constant few
    # millimetres the whole way round instead of by an eyeballed offset.
    plan = [(v[0], v[1]) for v in _pan_ring(HW, YB, YF, 0.0)]
    cyw = YB + (YF - YB) * 0.38                 # the outline's own centre

    def ring2d(k, dy=0.0):
        return [(x * k, cyw + (y - cyw) * k + dy) for (x, y) in plan]

    # The seat only just stands proud of the china - at 1.026 it overhung far
    # enough to hide the rim, and seat, lid and rim then read as three stacked
    # discs of the same thickness.  The lid is lofted with a slight dome so its
    # edge tapers instead of showing as a second flat band under the first.
    seat = mlib.prism(name + "_seat", ring2d(1.008), RIM, RIM + SEAT_T, cname)
    hole = mlib.prism(name + "_seatcut", ring2d(0.660, 0.030), RIM - 0.02,
                      RIM + 0.06, cname)
    mlib.boolean(seat, hole)
    mlib.bevel(seat, 0.006, 3, 46)
    mlib.smooth_shade(seat, 40)
    slid = mlib.loft(name + "_lid", [
        [(x, y, RIM + SEAT_T) for (x, y) in ring2d(1.018)],
        [(x, y, RIM + SEAT_T + LID_T * 0.62) for (x, y) in ring2d(1.014)],
        [(x, y, RIM + SEAT_T + LID_T) for (x, y) in ring2d(0.930)],
    ], close_v=True, cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(slid, 0.008, 3, 52)
    mlib.smooth_shade(slid, 44)
    seatp = mlib.join([seat, slid], name + "_seat", cname)
    mlib.set_mat(seatp, wht)

    # ------------------------------------------------------- chrome fittings
    TKF = SY + 0.098                            # tank's front face
    fit = []
    # trip lever: escutcheon on the tank's left cheek and a lever raked down
    esc = mlib.revolve(name + "_esc", [(0.0, 0.0), (0.020, 0.0), (0.019, 0.014),
                                       (0.010, 0.020), (0.0, 0.020)], 14,
                       cname=cname)
    mlib.rot_x(esc, -math.pi / 2)
    mlib.translate(esc, (-0.128, TKF - 0.004, TANK_Z - 0.072))
    fit.append(esc)
    fit.append(mlib.tube_along(name + "_lever",
                               [(-0.128, TKF + 0.016, TANK_Z - 0.072),
                                (-0.128, TKF + 0.024, TANK_Z - 0.074),
                                (-0.052, TKF + 0.028, TANK_Z - 0.102)],
                               mlib.rounded_rect(0.022, 0.008, 0.004, 2), cname))
    # angle stop screwed to the wall behind, and the supply up to the tank.
    # It stands outboard of the tank lid so nothing is buried in the china.
    wy = wall_y - cy
    stop = mlib.revolve(name + "_stop",
                        [(0.0, 0.0), (0.022, 0.0), (0.022, 0.052),
                         (0.030, 0.058), (0.030, 0.070), (0.0, 0.070)], 14,
                        cname=cname)
    mlib.rot_x(stop, -math.pi / 2)          # flange on the plaster, body forward
    mlib.translate(stop, (-0.242, wy, 0.190))
    fit.append(stop)
    sup = mlib.bez((wy + 0.068, 0.190), (wy + 0.200, 0.198),
                   (wy + 0.160, 0.340), (wy + 0.076, SHELF_Z - 0.024), n=10)
    n = len(sup) - 1
    fit.append(mlib.tube_along(name + "_supply",
                               [(-0.242 + 0.057 * (i / n), q[0], q[1])
                                for i, q in enumerate(sup)],
                               mlib.circle(0.0095, 10), cname))
    nut = mlib.revolve(name + "_nut", [(0.0, 0.0), (0.021, 0.0), (0.021, 0.030),
                                       (0.0, 0.030)], 12, cname=cname)
    mlib.translate(nut, (-0.185, sup[-1][0], SHELF_Z - 0.034))
    fit.append(nut)
    # seat hinge: the two barrels that sit on the flat behind the seat
    for sx in (-0.076, 0.076):
        h = mlib.revolve(name + "_hg", [(0.0, 0.0), (0.013, 0.0), (0.013, 0.054),
                                        (0.0, 0.054)], 12, cname=cname)
        mlib.rot_y(h, math.pi / 2)
        mlib.translate(h, (sx - 0.027, -0.150, RIM + 0.013))
        fit.append(h)
    fo = mlib.join(fit, name + "_fittings", cname)
    mlib.smooth_shade(fo, 38)
    mlib.set_mat(fo, chrome)

    out = [body, seatp, fo]
    for o in out:
        mlib.translate(o, (cx, cy, 0.0))
    return out


def dress_hall():
    """The bathroom hallway dressing (unchanged), kept separate from the beds."""
    ML2 = FL.mk_mats()
    CH = "Hall"
    gold = mats.get('paint_gilt') or mats.paint('paint_gilt', 'C9A24A', rough=0.30)
    # Two, stacked - the third, offset to the side, was one too many for a wall
    # this narrow and broke the pair's symmetry.
    for i, (yy, zz, w, h) in enumerate(((4.36, 1.86, 0.24, 0.30),
                                        (4.36, 1.50, 0.24, 0.30))):
        P.framed("H_art%d" % i, w, h, (L.HALL_X[0] + 0.030, yy, zz), (1, 0), CH,
                 framemat=gold,
                 artmat=mats.botanical('art_hall_%d' % i, normal=(1, 0),
                                       seed=31 + i * 5, ground='E6DEC6',
                                       stem='5C6A40', leafc=('4E5E36', '86946A'),
                                       bloom=('A87A52', 'DCC69C')))
    tw, td, th = 0.44, 0.34, 0.72
    white = mats.paint('paint_white_table', 'E2D9C6', rough=0.34, coat=0.28)
    parts = []
    top = mlib.prism("H_tab_top", mlib.rounded_rect(td, tw, 0.05, 4), th - 0.026,
                     th, CH)
    mlib.bevel(top, 0.005, 3, 40)
    parts.append(top)
    # a shallow apron under the top.  Without it the top sits on four bare
    # sticks and the whole thing reads as wire rather than furniture.
    ap = mlib.prism("H_tab_ap", mlib.rounded_rect(td - 0.055, tw - 0.055, 0.03, 3),
                    th - 0.084, th - 0.026, CH)
    mlib.bevel(ap, 0.004, 2, 45)
    parts.append(ap)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        # the swept leg's end cap is angled, so holding it a full tube-radius up
        # left the table hovering 12 mm off the boards
        pts = mlib.bez((0.0, th - 0.03), (0.05, th - 0.28), (0.08, th - 0.52),
                       (0.025, 0.004), n=10)
        path = [(sx * (td / 2 - 0.055 + p[0] * 0.8),
                 sy * (tw / 2 - 0.055 + p[0] * 0.8), p[1]) for p in pts]
        parts.append(mlib.tube_along("H_tab_lg", path, mlib.circle(0.0185, 8), CH))
    tob = mlib.join(parts, "H_table", CH)
    mlib.smooth_shade(tob, 40)
    mlib.set_mat(tob, white)
    # Up at the head of the hallway.  At y = 5.10 it stood against the stretch of
    # east wall that has been taken out, so it was left facing open floor.
    HTY = L.NW_Y - 0.45
    mlib.translate(tob, (L.HALL_X[1] - 0.24, HTY, 0.0))
    FL.table_lamp("H_lamp", L.HALL_X[1] - 0.24, HTY, 0.72, ML2, CH, energy=16.0,
                  scale=0.85)
    # Centred over the pair of pictures and high enough to clear them.  At
    # y = 4.10 its south arm hung 88 mm past the end of this wall (which starts
    # at HALL_Y0 = 3.98), so from the room it read as a lamp cranked round the
    # corner and pointing back down the hallway instead of straight off the wall.
    FL.sconce("H_sconce", (L.HALL_X[0] + 0.02, 4.36, 2.16), (1, 0), ML2, CH,
              energy=11.0)

    # ------------------------------------------------------------ bathroom
    # The room is 2.22 x 1.25, so the tub has to run east-west along the north
    # wall - laid out north-south it overhung both partitions by a quarter of a
    # metre.  Everything here is hollowed for real rather than being a solid
    # block with a second block hidden inside it.
    B = "Bathroom"
    wht = mats.paint('porcelain', 'F2F0E8', rough=0.10, coat=0.6)
    chrome = mats.get('metal_chrome') or mats.metal('metal_chrome', 'D8DCE0',
                                                    rough=0.10, bump=0.02)
    TW_, TD_ = 1.50, 0.72
    TCX, TCY = L.BA_X[0] + 0.06 + TW_ / 2, L.BA_Y[1] - 0.03 - TD_ / 2
    tb = mlib.prism("BA_tub", mlib.rounded_rect(TW_, TD_, 0.22, 6), 0.0, 0.58, B)
    mlib.bevel(tb, 0.016, 2, 50)
    mlib.translate(tb, (TCX, TCY, 0.0))
    cut = mlib.prism("BA_tubcut", mlib.rounded_rect(TW_ - 0.12, TD_ - 0.12, 0.19, 6),
                     0.19, 0.80, B)
    mlib.translate(cut, (TCX, TCY, 0.0))
    mlib.boolean(tb, cut)
    mlib.smooth_shade(tb, 34)
    mlib.set_mat(tb, wht)
    # mixer, riser and shower rose on the tub's west end
    fit = []
    for dy in (-0.09, 0.09):
        fit.append(mlib.revolve("BA_h", [(0.0, 0.0), (0.026, 0.0), (0.020, 0.030),
                                         (0.030, 0.052), (0.030, 0.062),
                                         (0.0, 0.062)], 14, cname=B))
        mlib.rot_y(fit[-1], math.pi / 2)
        mlib.translate(fit[-1], (TCX - TW_ / 2 + 0.03, TCY + dy, 0.66))
    sp = mlib.tube_along("BA_spout", [(TCX - TW_ / 2 + 0.03, TCY, 0.64),
                                      (TCX - TW_ / 2 + 0.17, TCY, 0.64),
                                      (TCX - TW_ / 2 + 0.21, TCY, 0.61)],
                         mlib.circle(0.014, 10), B)
    fit.append(sp)
    fit.append(mlib.tube_along("BA_riser", [(TCX - TW_ / 2 + 0.03, TCY, 0.70),
                                            (TCX - TW_ / 2 + 0.03, TCY, 1.86),
                                            (TCX - TW_ / 2 + 0.13, TCY, 1.94)],
                               mlib.circle(0.011, 10), B))
    rose = mlib.revolve("BA_rose", [(0.0, 0.0), (0.055, 0.012), (0.058, 0.030),
                                    (0.026, 0.052), (0.0, 0.056)], 18, cname=B)
    mlib.rot_y(rose, math.radians(150))
    mlib.translate(rose, (TCX - TW_ / 2 + 0.15, TCY, 1.95))
    fit.append(rose)
    fo = mlib.join(fit, "BA_fittings", B)
    mlib.smooth_shade(fo, 38)
    mlib.set_mat(fo, chrome)
    # curtain rail round the two open sides of the tub, and the curtain
    rail = mlib.tube_along("BA_rail",
                           [(TCX - TW_ / 2 + 0.02, TCY - TD_ / 2 + 0.02, 1.98),
                            (TCX + TW_ / 2 - 0.02, TCY - TD_ / 2 + 0.02, 1.98),
                            (TCX + TW_ / 2 - 0.02, TCY + TD_ / 2 - 0.02, 1.98)],
                           mlib.circle(0.010, 10), B)
    mlib.smooth_shade(rail, 38)
    mlib.set_mat(rail, chrome)
    # drawn open and bunched at the east end, so the tub is not walled off
    # bunched to one end, so the cloth is at 3x fullness - but only six folds
    # across the 380 mm it occupies, or each fold is deeper than it is wide
    cur = P.curtain_panel("BA_curtain", TCX + TW_ / 2 - 0.40, TCX + TW_ / 2 - 0.02,
                          1.96, 0.22, depth=0.075, folds=6, cname=B,
                          mat=mats.paint('shower_curtain', 'DFE4E2', rough=0.34,
                                         coat=0.4),
                          gather=0.75, flare=1.0, seed=5, hem=0.022,
                          fullness=3.0)
    # hung a hand's width inside the tub: at the rail line the 75 mm of pleat
    # depth straddled the tub wall and the hem passed through the rim
    mlib.translate(cur, (0.0, TCY - TD_ / 2 + 0.10, 0.0))
    # pedestal basin, bowl hollowed out, in the north-east corner
    BX, BY = L.BA_X[1] - 0.35, L.BA_Y[1] - 0.26
    ped = mlib.revolve("BA_ped", [(0.0, 0.0), (0.115, 0.0), (0.100, 0.05),
                                  (0.072, 0.30), (0.085, 0.58), (0.140, 0.66),
                                  (0.0, 0.66)], 20, cname=B)
    mlib.smooth_shade(ped, 34)
    mlib.set_mat(ped, wht)
    bs = mlib.prism("BA_basin", mlib.rounded_rect(0.50, 0.40, 0.12, 5), 0.64, 0.80, B)
    mlib.bevel(bs, 0.012, 2, 50)
    bcut = mlib.prism("BA_bcut", mlib.rounded_rect(0.36, 0.26, 0.10, 5), 0.70, 0.95, B)
    mlib.boolean(bs, bcut)
    mlib.smooth_shade(bs, 40)
    mlib.set_mat(bs, wht)
    for o in (ped, bs):
        mlib.translate(o, (BX, BY, 0.0))
    btap = mlib.tube_along("BA_btap", [(BX, BY + 0.15, 0.80),
                                       (BX, BY + 0.15, 0.885),
                                       (BX, BY + 0.075, 0.90)],
                           mlib.circle(0.012, 10), B)
    mlib.smooth_shade(btap, 38)
    mlib.set_mat(btap, chrome)
    # mirrored cabinet over the basin
    mc = mlib.box("BA_cab", BX - 0.26, L.BA_Y[1] - 0.16, 1.12,
                  BX + 0.26, L.BA_Y[1] - 0.005, 1.66, B)
    mlib.bevel(mc, 0.005, 2, 45)
    mlib.set_mat(mc, wht)
    mg = mlib.box("BA_mirror", BX - 0.235, L.BA_Y[1] - 0.175, 1.15,
                  BX + 0.235, L.BA_Y[1] - 0.158, 1.63, B)
    mlib.set_mat(mg, mats.metal('mirror_glass', 'F0F2F4', rough=0.02, bump=0.0))
    # WC in the inner corner, tank to the south wall.  It stood out in the
    # middle of that wall before, marooned on open floor; a lavatory is always
    # pushed into the corner furthest from the door.  0.40 from the centreline
    # to the west wall is the tightest a real one is ever set.
    WX, WY = L.BA_X[0] + 0.40, L.BA_Y[0] + 0.376
    water_closet("BA_wc", WX, WY, B, wht, chrome, L.BA_Y[0])
    # bathroom overhead: a fitting, not a bare lamp floating under the ceiling
    P.flush_dome("BA_light", ((L.BA_X[0] + L.BA_X[1]) * 0.5,
                              (L.BA_Y[0] + L.BA_Y[1]) * 0.5, 2.62),
                 cname=B, r=0.115, energy=17.0,
                 colr=(1.0, 0.90, 0.80), drop=0.070)
    print("hall/bath dressed")
