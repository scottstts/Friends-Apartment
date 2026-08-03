"""The service counter, the back bar, and everything standing on them.

The counter is the second thing every camera in the room sees, and unlike
the couch it is joinery: fluted pilasters, fielded panels, a bullnosed stone
top with a real overhang.  Those three details are what make it read as a
1930s shopfitting rather than as a kitchen island, so they are modelled and
not implied.
"""
import bpy, math, importlib
import mlib as M
import mats as T
import L

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C = "Counter"
TAU = math.tau
MAT = {}

# The menu board sits at the SOUTH end of the west elevation, on its own -
# main_couch.webp looks north-west and shows it clear to the left of the urn.
CHALK_Y = (5.35, 7.05)
CHALK_Z = (1.55, 2.66)

# The retail display, hollowed out of the counter's front on the straight run
# of it.  In frontal.jpeg it is a tall recess of three shelves packed edge to
# edge with upright cartons, its stiles flush with the counter face.
CASE_Y = (6.16, 7.10)
CASE_Z = (0.180, 0.430, 0.680)          # shelf tops


def mats():
    if MAT:
        return MAT
    MAT['oak'] = T.wood('cw_oak', light='7A5228', dark='341C0C', ring=24.0,
                        scale=1.2, )
    MAT['oak_dk'] = T.wood('cw_oak_dk', light='5A3A1C', dark='24130A',
                           ring=22.0, scale=1.0)
    # A quieter stone.  At vein2 = DCCCA8 the light vein was near white and
    # 1.7 cells/m put it in hand-sized patches, so the counter top read as a
    # cow rather than as the brown-and-grey marble in main_couch.webp.
    MAT['stone'] = T.marble('cw_marble', base='8E7C63', vein='4A3826',
                            vein2='B4A484', scale=2.6)
    MAT['brass'] = T.metal('cw_brass', 'B08A32', rough=0.24, tarnish=0.42)
    MAT['copper'] = T.metal('cw_copper', 'A85C2E', rough=0.28,
                            patina='3E5A4A', tarnish=0.5)
    MAT['chrome'] = T.chrome('cw_chrome', rough=0.07)
    MAT['steel'] = T.metal('cw_steel', 'B4B8BA', rough=0.30, patina='4A4E50',
                           tarnish=0.25)
    MAT['black'] = T.flat('cw_black', '15161A', rough=0.34)
    MAT['chalk'] = T.chalkboard('cw_chalk', '17281F')
    MAT['glass'] = T.glass('cw_glass', tint='EEF4F0', rough=0.02, alpha=0.06)
    MAT['green'] = T.paint('cw_green', L.GREEN_IRON, rough=0.34, coat=0.15)
    MAT['card'] = T.flat('cw_card', 'C8B48A', rough=0.72)
    return MAT


# ------------------------------------------------------------------ joinery

def fluted(name, x, y0, y1, z0, z1, w=0.075, d=0.030, flutes=3, axis='y',
           cname=C):
    """A pilaster with vertical flutes cut in its face.  Modelled as a solid
    with a scalloped section rather than as a box plus grooves - the grooves
    would be coplanar with the face they sit in."""
    sec = []
    n = 9
    for i in range(flutes):
        u0 = -w / 2 + w * (i + 0.14) / flutes
        u1 = -w / 2 + w * (i + 0.86) / flutes
        if i == 0:
            sec.append((-w / 2, d))
            sec.append((u0, d))
        for k in range(n + 1):
            t = k / n
            u = u0 + (u1 - u0) * t
            sec.append((u, d - 0.010 * math.sin(math.pi * t)))
        nxt = -w / 2 + w * (i + 1 + 0.14) / flutes
        sec.append((min(nxt, w / 2), d))
    sec.append((w / 2, d))
    sec.append((w / 2, 0.0))
    sec.append((-w / 2, 0.0))
    if axis == 'y':
        poly = [(y0 + (y1 - y0) * 0.5 + u, x + v) for (u, v) in sec]
    else:
        poly = [(x + v, y0 + (y1 - y0) * 0.5 + u) for (u, v) in sec]
    ob = M.prism(name, M.ccw(poly), z0, z1, cname)
    return ob


def panel_bay(name, p0, p1, nx, z0, z1, depth=0.022, cname=C, bead=0.020):
    """One fielded panel between two pilasters: the field is set back and its
    edge is chamfered, which is the only way a panel catches light."""
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    ll = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ll, uy / ll
    out = []
    levels = [(0.0, 0.0), (bead, -depth * 0.55), (bead * 1.9, -depth)]
    rings = []
    for (ins, dp) in levels:
        a = (p0[0] + ux * ins + nx[0] * dp, p0[1] + uy * ins + nx[1] * dp)
        b = (p1[0] - ux * ins + nx[0] * dp, p1[1] - uy * ins + nx[1] * dp)
        rings.append([(a[0], a[1], z0 + ins), (b[0], b[1], z0 + ins),
                      (b[0], b[1], z1 - ins), (a[0], a[1], z1 - ins)])
    # last ring closed off by a flat field
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=False, cap_end=True)
    return ob


def bullnose_top(name, poly, z0, z1, over=0.045, cname=C):
    """Stone slab with a bullnosed lip: three rings so the edge is a true
    half-round rather than a bevel."""
    rings = []
    for (o, dz) in ((-0.004, 0.0), (over * 0.72, 0.006), (over, (z1 - z0) * 0.5),
                    (over * 0.72, z1 - z0 - 0.006), (-0.004, z1 - z0)):
        p = M.poly_offset(poly, o)
        rings.append([(x, y, z0 + dz) for (x, y) in p])
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)
    M.smooth_shade(ob, 34)
    return ob


# ------------------------------------------------------------ service counter

def service_counter(cname=C):
    """The faceted counter the stools stand at.  Its front line comes
    straight from the layout; everything else is worked off that."""
    m = mats()
    wood, stone, brass = [], [], []
    front = list(L.SERVE_FRONT)
    back = [(L.SERVE_BACK, p[1]) for p in reversed(front)]
    poly = M.ccw(front + back)
    H = L.SERVE_H

    # plinth, carcass, then the pilaster/panel rhythm on the public face
    pl = M.prism("Counter_plinth", M.poly_offset(poly, -0.022), 0.0, 0.115,
                 cname)
    M.bevel(pl, 0.006, 2, 50); wood.append(pl)

    # The retail case is HOLLOWED OUT OF THE COUNTER, not stood in front of
    # it.  In frontal.jpeg it is a tall three-shelf recess let into the
    # panelling on the straight run of the front, packed edge to edge with
    # upright cartons, and its stiles are flush with the counter face.  Built
    # as a separate box in front - which is what the last two attempts did -
    # it reads as a crate someone left leaning against the counter.
    #
    # Hollowing means the carcass itself has to stop: it is built as two
    # prisms with the recess between them and a back slab closing it, rather
    # than as one solid with a lining stuck on.
    CY0, CY1, CD = CASE_Y[0], CASE_Y[1], 0.285
    CX = 2.07                       # the face this stretch of counter runs on
    body = M.poly_offset(poly, -0.030)
    BK = L.SERVE_BACK + 0.030
    ys = [p[1] for p in body]
    zt = H - 0.062
    for tag, y0, y1 in (("n", CY1, max(ys)), ("s", min(ys), CY0)):
        sub = [p for p in body if y0 - 1e-6 <= p[1] <= y1 + 1e-6]
        if len(sub) < 3:
            continue
        # close the sub-polygon off across the cut, on the counter's own lines
        sub = M.ccw(sub + [(CX - 0.030, y1), (BK, y1), (BK, y0),
                           (CX - 0.030, y0)])
        car = M.prism("Counter_body_" + tag, sub, 0.100, zt, cname)
        wood.append(car)
    back = M.prism("Counter_body_bk",
                   M.ccw([(BK, CY0), (CX - CD, CY0), (CX - CD, CY1), (BK, CY1)]),
                   0.100, zt, cname)
    wood.append(back)
    # the reveal: two stiles flush with the face, a head, and three shelves
    for nm, (a, b, c, d, e, f) in (
            ("stL", (CX - CD, CY0, 0.100, CX, CY0 + 0.030, zt)),
            ("stR", (CX - CD, CY1 - 0.030, 0.100, CX, CY1, zt)),
            ("hd", (CX - CD, CY0, zt - 0.032, CX, CY1, zt)),
            ("kick", (CX - CD, CY0, 0.100, CX, CY1, 0.135))):
        p = M.box("Counter_case_" + nm, a, b, c, d, e, f, cname)
        M.bevel(p, 0.004, 2, 50); wood.append(p)
    for k, z in enumerate(CASE_Z):
        sl = M.box("Counter_shelf%d" % k, CX - CD + 0.004, CY0 + 0.030, z,
                   CX - 0.012, CY1 - 0.030, z + 0.020, cname)
        M.bevel(sl, 0.003, 2, 50); wood.append(sl)

    # walk the front line, dropping a pilaster every ~620 mm and a panel between
    seg = []
    for i in range(len(front) - 1):
        a, b = front[i], front[i + 1]
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(round(ln / 0.62)))
        for k in range(n):
            seg.append((a, b, k / n, (k + 1) / n, ln / n))
    for idx, (a, b, t0, t1, ln) in enumerate(seg):
        ux, uy = (b[0] - a[0]), (b[1] - a[1])
        dd = math.hypot(ux, uy) or 1.0
        ux, uy = ux / dd, uy / dd
        nx = (uy, -ux)          # outward, into the room
        p0 = (a[0] + ux * dd * t0, a[1] + uy * dd * t0)
        p1 = (a[0] + ux * dd * t1, a[1] + uy * dd * t1)
        # no panel where the display case is let in
        if (CASE_Y[0] - 0.12 < (p0[1] + p1[1]) * 0.5 < CASE_Y[1] + 0.12
                and abs(p0[0] - 2.07) < 0.02):
            continue
        pb = panel_bay("Counter_pan%02d" % idx,
                       (p0[0] + ux * 0.055, p0[1] + uy * 0.055),
                       (p1[0] - ux * 0.055, p1[1] - uy * 0.055),
                       nx, 0.150, H - 0.115, depth=0.026, cname=cname)
        wood.append(pb)
        for pp in ((p0, 0), (p1, 1)):
            if pp[1] == 1 and idx != len(seg) - 1:
                continue
            q = pp[0]
            pil = M.prism("Counter_pil%02d_%d" % (idx, pp[1]),
                          M.ccw([(q[0] - ux * 0.042 + nx[0] * 0.030,
                                  q[1] - uy * 0.042 + nx[1] * 0.030),
                                 (q[0] + ux * 0.042 + nx[0] * 0.030,
                                  q[1] + uy * 0.042 + nx[1] * 0.030),
                                 (q[0] + ux * 0.042 - nx[0] * 0.020,
                                  q[1] + uy * 0.042 - nx[1] * 0.020),
                                 (q[0] - ux * 0.042 - nx[0] * 0.020,
                                  q[1] - uy * 0.042 - nx[1] * 0.020)]),
                          0.100, H - 0.070, cname)
            M.bevel(pil, 0.004, 2, 55)
            wood.append(pil)

    top = bullnose_top("Counter_top", poly, H - 0.055, H, over=0.048,
                       cname=cname)
    stone.append(top)

    # The retail case that stands out in front of the counter, stacked with
    # boxes - it is in every wide shot of the room.
    #
    # It was a SOLID box with two shelf boards buried inside it, so every
    # packet on those shelves was half swallowed by the carcass and the whole
    # thing read as a blank lump growing out of the counter.  A display case
    # is a carcass: two ends, a back, a top and a plinth, with the front open.
    # It also has to stay on the stretch of counter face that runs at x 2.07
    # - the face steps out to 2.50 at y 7.18, and the case was running
    # straight through that step.
    ow = M.join(wood, "Counter_joinery", cname); M.set_mat(ow, m['oak'])
    os_ = M.join(stone, "Counter_stone", cname); M.set_mat(os_, m['stone'])
    return [ow, os_]


# --------------------------------------------------------------- back bar

def back_bar(cname=C):
    """The run along the west wall: base cupboards, a working top, open
    shelves above, and a tall dresser closing each end."""
    m = mats()
    wood, stone, glassp, brassp = [], [], [], []
    y0, y1 = L.BACK_TALL_S[1], L.BACK_TALL_N[0]
    D = L.BACK_D
    H = L.BACK_H

    base = M.prism("Back_base", [(0.0, y0), (D, y0), (D, y1), (0.0, y1)],
                   0.095, H - 0.045, cname)
    wood.append(base)
    plinth = M.prism("Back_plinth", [(0.0, y0), (D - 0.045, y0),
                                     (D - 0.045, y1), (0.0, y1)], 0.0, 0.100,
                     cname)
    M.bevel(plinth, 0.005, 2, 50); wood.append(plinth)
    # doors and drawers along the run
    n = max(1, int(round((y1 - y0) / 0.58)))
    pitch = (y1 - y0) / n
    for i in range(n):
        yy = y0 + i * pitch
        dr = panel_bay("Back_dr%02d" % i, (D, yy + 0.022), (D, yy + pitch - 0.022),
                       (1, 0), 0.115, H - 0.060, depth=0.020, cname=cname)
        wood.append(dr)
        kn = M.revolve("Back_kn%02d" % i,
                       [(0.0, 0.0), (0.012, 0.004), (0.016, 0.016),
                        (0.010, 0.026), (0.0, 0.028)], segments=12, cname=cname)
        M.rot_y(kn, math.pi / 2)
        M.translate(kn, (D + 0.004, yy + pitch * 0.5, H - 0.20))
        M.smooth_shade(kn, 40)
        brassp.append(kn)
    top = bullnose_top("Back_top", [(0.0, y0), (D + 0.02, y0), (D + 0.02, y1),
                                    (0.0, y1)], H - 0.045, H, over=0.030,
                       cname=cname)
    stone.append(top)

    # Open shelves above, on shaped brackets.  They start north of the menu
    # board rather than running the whole wall: in the set photographs the
    # board occupies the south end of this elevation on its own.
    y0s = CHALK_Y[1] + 0.30
    for k, z in enumerate((1.36, 1.72, 2.08)):
        sl = M.box("Back_sh%d" % k, -0.005, y0s + 0.02, z, 0.30, y1 - 0.02,
                   z + 0.026, cname)
        M.bevel(sl, 0.004, 2, 50); wood.append(sl)
        for i in range(int((y1 - y0s) / 0.92) + 1):
            yy = min(y1 - 0.10, y0s + 0.12 + i * 0.92)
            br = M.prism_xz("Back_br%d_%d" % (k, i),
                            [(-0.005, z), (0.275, z), (-0.005, z - 0.16)],
                            yy, yy + 0.022, cname)
            wood.append(br)

    # the tall dressers at each end
    for nm, (a, bq) in (("S", L.BACK_TALL_S), ("N", L.BACK_TALL_N)):
        d = M.prism("Back_tall_" + nm, [(0.0, a), (0.46, a), (0.46, bq),
                                        (0.0, bq)], 0.095, L.BACK_TALL_H, cname)
        wood.append(d)
        pl2 = M.prism("Back_tallpl_" + nm, [(0.0, a), (0.42, a), (0.42, bq),
                                            (0.0, bq)], 0.0, 0.100, cname)
        wood.append(pl2)
        cor = M.prism("Back_tallcor_" + nm,
                      [(0.0, a - 0.018), (0.50, a - 0.018), (0.50, bq + 0.018),
                       (0.0, bq + 0.018)], L.BACK_TALL_H, L.BACK_TALL_H + 0.055,
                      cname)
        M.bevel(cor, 0.008, 2, 50); wood.append(cor)
        # glazed upper doors, solid below
        for k in range(2):
            z0 = 1.15 if k else 0.16
            z1 = L.BACK_TALL_H - 0.09 if k else 1.05
            pb = panel_bay("Back_tallp_%s%d" % (nm, k), (0.46, a + 0.03),
                           (0.46, bq - 0.03), (1, 0), z0, z1, depth=0.020,
                           cname=cname)
            wood.append(pb)
            if k:
                gl = M.box("Back_tallg_%s" % nm, 0.452, a + 0.075, z0 + 0.045,
                           0.462, bq - 0.075, z1 - 0.045, cname)
                glassp.append(gl)
        for i in range(2):
            sl = M.box("Back_tallsh_%s%d" % (nm, i), 0.02, a + 0.02,
                       1.30 + i * 0.34, 0.44, bq - 0.02, 1.32 + i * 0.34, cname)
            wood.append(sl)

    ow = M.join(wood, "Back_joinery", cname); M.set_mat(ow, m['oak_dk'])
    os_ = M.join(stone, "Back_stone", cname); M.set_mat(os_, m['stone'])
    og = M.join(glassp, "Back_glass", cname); M.set_mat(og, m["glass"])
    ob2 = M.join(brassp, "Back_brass", cname); M.set_mat(ob2, m["brass"])
    return [ow, os_, og, ob2]


# ------------------------------------------------------------------ machines

def espresso(name, cx, cy, cz, rot=0.0, cname=C):
    """A lever espresso machine: stepped body, domed top, two group heads and
    a pair of steam wands.  It is the brightest thing behind the counter and
    the eye goes to it, so it gets real shape."""
    """It read as a photocopier: one pale slab with a dome and two coins on
    the front.  A lever machine is a CHROME box with a raised hood, dark
    cheeks each side, two group heads that stand out of the front with
    portafilters hanging off them, a wand and a knob at each end, gauges, a
    drip tray with a grid, and a rail of inverted cups warming on the top.
    Every one of those is a silhouette event, and a machine with none of them
    has nothing for the eye to catch."""
    m = mats()
    steel, blk, brs, wht = [], [], [], []
    W, D = 0.72, 0.46
    # drip tray on a plinth, then the body, then the hood
    pl = M.prism(name + "_pl", M.rounded_rect(W - 0.03, D - 0.03, 0.020, seg=4),
                 0.0, 0.055, cname)
    M.bevel(pl, 0.006, 2, 50); blk.append(pl)
    body = M.prism(name + "_body",
                   M.rounded_rect(W, D, 0.055, seg=5), 0.050, 0.300, cname)
    M.bevel(body, 0.012, 2, 50); steel.append(body)
    hood = M.prism(name + "_hood",
                   M.rounded_rect(W - 0.10, D - 0.07, 0.045, seg=5),
                   0.292, 0.392, cname)
    M.bevel(hood, 0.014, 2, 50); steel.append(hood)
    dome = M.revolve(name + "_dome",
                     [(0.0, 0.386), (0.24, 0.382), (0.255, 0.402),
                      (0.225, 0.452), (0.140, 0.486), (0.0, 0.496)],
                     segments=28, cname=cname)
    M.scale_mesh(dome, (1.28, 0.80, 1.0)); M.smooth_shade(dome, 40)
    steel.append(dome)
    fin = M.revolve(name + "_fin",
                    [(0.0, 0.490), (0.022, 0.494), (0.026, 0.512),
                     (0.014, 0.526), (0.0, 0.530)], segments=14, cname=cname)
    M.smooth_shade(fin, 40); brs.append(fin)
    # dark cheeks, so the chrome is not one unbroken sheet
    for s in (-1, 1):
        ck = M.prism(name + "_ck%d" % s,
                     M.rounded_rect(0.055, D - 0.10, 0.020, seg=4),
                     0.085, 0.272, cname)
        M.translate(ck, (s * (W / 2 - 0.020), 0.0, 0.0))
        M.bevel(ck, 0.005, 2, 50); blk.append(ck)
    # the working front: two groups with portafilters, wands, knobs, gauges
    for s in (-1, 1):
        gh = M.revolve(name + "_grp%d" % s,
                       [(0.0, 0.0), (0.046, 0.0), (0.042, 0.048),
                        (0.056, 0.062), (0.056, 0.082), (0.030, 0.094),
                        (0.0, 0.096)], segments=18, cname=cname)
        M.translate(gh, (s * 0.19, -D / 2 - 0.030, 0.098))
        M.smooth_shade(gh, 40); steel.append(gh)
        # portafilter: a shallow basket on a spout, with a black handle
        pf = M.revolve(name + "_pf%d" % s,
                       [(0.0, 0.0), (0.040, 0.004), (0.042, 0.026),
                        (0.030, 0.030), (0.022, 0.012), (0.0, 0.010)],
                       segments=16, cname=cname)
        M.translate(pf, (s * 0.19, -D / 2 - 0.030, 0.070))
        steel.append(pf)
        hnd = M.tube_along(name + "_ph%d" % s,
                           [(s * 0.19, -D / 2 - 0.062, 0.076),
                            (s * 0.19, -D / 2 - 0.150, 0.062)],
                           M.circle(0.014, 10), cname=cname, up=(0, 0, 1))
        M.smooth_shade(hnd, 40); blk.append(hnd)
        wd = M.tube_along(name + "_wand%d" % s,
                          [(s * (W / 2 - 0.035), -0.09, 0.235),
                           (s * (W / 2 - 0.012), -0.20, 0.185),
                           (s * (W / 2 - 0.010), -0.235, 0.095)],
                          M.circle(0.008, 8), cname=cname, up=(0, 0, 1))
        M.smooth_shade(wd, 40); steel.append(wd)
        kn = M.revolve(name + "_kn%d" % s,
                       [(0.0, 0.0), (0.026, 0.004), (0.024, 0.022),
                        (0.0, 0.026)], segments=12, cname=cname)
        M.rot_x(kn, math.radians(-90))
        M.translate(kn, (s * (W / 2 - 0.045), -D / 2 - 0.006, 0.235))
        blk.append(kn)
        g = M.revolve(name + "_gauge%d" % s,
                      [(0.0, 0.0), (0.036, 0.0), (0.040, 0.006),
                       (0.036, 0.014), (0.0, 0.015)], segments=18, cname=cname)
        M.rot_x(g, math.radians(-90))
        M.translate(g, (s * 0.085, -D / 2 - 0.004, 0.215))
        brs.append(g)
        gf = M.revolve(name + "_gf%d" % s,
                       [(0.0, 0.0), (0.030, 0.0), (0.030, 0.004), (0.0, 0.004)],
                       segments=18, cname=cname)
        M.rot_x(gf, math.radians(-90))
        M.translate(gf, (s * 0.085, -D / 2 - 0.014, 0.215))
        wht.append(gf)
    # drip grid: real bars, so the tray is not a flat lip
    for i in range(9):
        bar = M.box(name + "_gr%d" % i, -0.30 + i * 0.0725, -D / 2 - 0.020,
                    0.066, -0.276 + i * 0.0725, -0.06, 0.074, cname)
        steel.append(bar)
    # cups warming on the hood
    for i in range(5):
        cp = M.revolve(name + "_cp%d" % i,
                       [(0.0, 0.0), (0.036, 0.002), (0.033, 0.052),
                        (0.036, 0.056), (0.031, 0.056), (0.028, 0.006),
                        (0.0, 0.004)], segments=14, cname=cname)
        M.smooth_shade(cp, 44)
        # on the FRONT half of the hood: pushed to the back they ended up
        # inside the shelving on the wall behind the machine
        M.translate(cp, (-0.24 + i * 0.12, -0.020 - 0.055 * (i % 2), 0.392))
        wht.append(cp)
    out = []
    for lst, mat, sfx in ((steel, m['chrome'], "_steel"),
                          (blk, m['black'], "_blk"),
                          (wht, m['card'], "_cups"),
                          (brs, m['brass'], "_brass")):
        if lst:
            o = M.join(lst, name + sfx, cname); M.set_mat(o, mat); out.append(o)
    for o in out:
        if rot:
            M.rotate_z(o, math.radians(rot))
        M.translate(o, (cx, cy, cz))
    return out


def urn(name, cx, cy, cz, h=0.86, rot=0.0, cname=C):
    """The big brass coffee urn.  Body, gallery, spigot, and the glass
    cylinder of beans beside it - the whole silhouette in main_couch.webp."""
    m = mats()
    brs, glassp, blk = [], [], []
    body = M.revolve(name + "_body",
                     [(0.0, 0.0), (0.135, 0.0), (0.138, 0.030),
                      (0.118, 0.055), (0.150, 0.115), (0.163, 0.255),
                      (0.150, 0.400), (0.128, 0.470), (0.140, 0.492),
                      (0.120, 0.512), (0.070, 0.545), (0.086, 0.575),
                      (0.052, 0.600), (0.030, 0.640), (0.044, 0.665),
                      (0.0, 0.690)], segments=32, cname=cname)
    M.smooth_shade(body, 42); brs.append(body)
    for i in range(3):
        a = math.radians(20 + i * 120)
        lg = M.revolve(name + "_lg%d" % i,
                       [(0.0, 0.0), (0.022, 0.004), (0.016, 0.040),
                        (0.024, 0.070), (0.0, 0.075)], segments=12, cname=cname)
        M.translate(lg, (0.115 * math.cos(a), 0.115 * math.sin(a), -0.075))
        brs.append(lg)
    spig = M.tube_along(name + "_spig",
                        [(0.14, 0.0, 0.16), (0.215, 0.0, 0.155),
                         (0.222, 0.0, 0.105)], M.circle(0.013, 10),
                        cname=cname, up=(0, 0, 1))
    M.smooth_shade(spig, 40); brs.append(spig)
    tap = M.revolve(name + "_tap",
                    [(0.0, 0.0), (0.030, 0.006), (0.024, 0.016), (0.0, 0.018)],
                    segments=12, cname=cname)
    M.rot_y(tap, math.radians(90)); M.translate(tap, (0.222, 0.0, 0.175))
    blk.append(tap)
    ob = M.join(brs, name + "_brass", cname); M.set_mat(ob, m['brass'])
    ok = M.join(blk, name + "_blk", cname); M.set_mat(ok, m['black'])
    out = [ob, ok]
    for o in out:
        if rot:
            M.rotate_z(o, math.radians(rot))
        M.translate(o, (cx, cy, cz + 0.075))
    return out


def bean_cylinder(name, cx, cy, cz, h=0.52, r=0.085, cname=C):
    """Glass bean jar.  It stands on a small foot rather than flat on the
    counter: a flat disc laid straight onto the stone shares its plane."""
    m = mats()
    tube = M.revolve(name + "_g",
                     [(r - 0.020, 0.006), (r - 0.004, 0.014), (r, 0.026),
                      (r, h - 0.02), (r - 0.006, h), (r - 0.012, h),
                      (r - 0.012, 0.030), (r - 0.020, 0.018),
                      (r - 0.020, 0.006)], segments=24, cname=cname)
    M.smooth_shade(tube, 42); M.set_mat(tube, m['glass'])
    beans = M.revolve(name + "_b", [(0.0, 0.0), (r - 0.014, 0.0),
                                    (r - 0.014, h * 0.78), (0.0, h * 0.80)],
                      segments=24, cname=cname)
    M.smooth_shade(beans, 40)
    M.set_mat(beans, T.wood('cw_beans', light='6B3A18', dark='2A1408',
                            ring=180.0, scale=0.06))
    cap = M.revolve(name + "_c", [(0.0, h), (r + 0.006, h), (r + 0.004, h + 0.03),
                                  (0.0, h + 0.045)], segments=24, cname=cname)
    M.set_mat(cap, m['brass'])
    out = [tube, beans, cap]
    for o in out:
        M.translate(o, (cx, cy, cz))
    return out


def cake_dome(name, cx, cy, cz, r=0.17, cname=C):
    """Footed glass cake stand with a domed cover, on the counter top."""
    m = mats()
    stand = M.revolve(name + "_s",
                      [(0.0, 0.0), (0.062, 0.004), (0.058, 0.014),
                       (0.020, 0.030), (0.017, 0.075), (0.030, 0.092),
                       (r, 0.100), (r, 0.112), (0.0, 0.112)],
                      segments=28, cname=cname)
    M.smooth_shade(stand, 40); M.set_mat(stand, m['glass'])
    dome = M.revolve(name + "_d",
                     [(r - 0.002, 0.112), (r - 0.002, 0.150)]
                     + [(  (r - 0.004) * math.cos(math.radians(a)),
                           0.150 + (r * 1.05) * math.sin(math.radians(a)))
                        for a in range(0, 91, 9)],
                     segments=28, cname=cname, cap_start=False, cap_end=False)
    M.solidify(dome, 0.004, offset=0)
    M.smooth_shade(dome, 44); M.set_mat(dome, m['glass'])
    knob = M.revolve(name + "_k",
                     [(0.0, 0.0), (0.016, 0.004), (0.020, 0.018),
                      (0.012, 0.030), (0.0, 0.032)], segments=14, cname=cname)
    M.translate(knob, (0, 0, 0.150 + r * 1.05)); M.set_mat(knob, m['glass'])
    cake = M.revolve(name + "_c", [(0.0, 0.114), (r * 0.66, 0.114),
                                   (r * 0.64, 0.175), (0.0, 0.180)],
                     segments=24, cname=cname)
    M.set_mat(cake, T.paint('cw_cake', 'D9B36A', rough=0.62, bump=0.25))
    out = [stand, dome, knob, cake]
    for o in out:
        M.translate(o, (cx, cy, cz))
    return out


def register(name, cx, cy, cz, rot=0.0, cname=C):
    """Brass National-style till."""
    """It is the one bright object on the customer side of the counter and it
    sat there as a plain slab with a hexagon on top - a yellow box.  A
    National is all relief: a moulded plinth, a panelled and scrolled case, a
    cast crest with an arched top, a glazed price window with a white flag
    behind it, six banks of keys on a stepped keyboard, and a drawer with a
    pull.  All of that is silhouette and shadow line, which is what makes
    brass read as brass rather than as yellow paint."""
    m = mats()
    brs, blk, wht = [], [], []
    w, d = 0.34, 0.36
    # moulded plinth, panelled case, top rail - three courses, not one box
    for (sw, sd, z0, z1, bv) in ((w, d, 0.0, 0.035, 0.010),
                                 (w - 0.028, d - 0.028, 0.030, 0.052, 0.006),
                                 (w - 0.046, d - 0.046, 0.048, 0.238, 0.010),
                                 (w - 0.020, d - 0.020, 0.232, 0.262, 0.008)):
        p = M.prism(name + "_b%d" % int(z0 * 1000),
                    M.rounded_rect(sw, sd, 0.026, seg=4), z0, z1, cname)
        M.bevel(p, bv, 2, 50); brs.append(p)
    # the case is panelled on both cheeks: a sunk field with a bolection
    for s in (-1, 1):
        pn = M.prism(name + "_pn%d" % s,
                     M.rounded_rect(w - 0.100, d - 0.100, 0.022, seg=4),
                     0.072, 0.212, cname)
        M.scale_mesh(pn, (1.0, 1.0, 1.0))
        M.translate(pn, (0.0, s * 0.006, 0.0))
        M.bevel(pn, 0.005, 2, 50); brs.append(pn)
    # the crest: an arched cast top on a neck, not a flat hexagon
    neck = M.prism_xz(name + "_nk",
                      [(-0.128, 0.258), (0.128, 0.258), (0.118, 0.296),
                       (-0.118, 0.296)], -0.072, 0.072, cname)
    M.bevel(neck, 0.005, 2, 50); brs.append(neck)
    arc = [(-0.150, 0.292), (0.150, 0.292)]
    arc += [(0.150 * math.cos(a), 0.292 + 0.150 * math.sin(a) * 0.92)
            for a in [math.radians(t) for t in range(6, 175, 12)]]
    crown = M.prism_xz(name + "_c", M.ccw(arc), -0.052, 0.052, cname)
    M.bevel(crown, 0.006, 2, 50); brs.append(crown)
    # the price window, glazed, with a white flag standing behind it
    for s, mat in ((-1, blk), (1, blk)):
        fr = M.prism_xz(name + "_wf%d" % s,
                        [(-0.112, 0.306), (0.112, 0.306), (0.112, 0.416),
                         (-0.112, 0.416)], s * 0.056, s * 0.062, cname)
        mat.append(fr)
    flag = M.prism_xz(name + "_fl",
                      [(-0.098, 0.318), (0.098, 0.318), (0.098, 0.404),
                       (-0.098, 0.404)], -0.010, 0.010, cname)
    wht.append(flag)
    # keyboard: six banks of nine keys on a stepped bed, on their own apron
    bed = M.prism_xz(name + "_kb",
                     [(-0.150, 0.058), (0.150, 0.058), (0.150, 0.196),
                      (-0.150, 0.196)], -0.148, -0.070, cname)
    M.bevel(bed, 0.006, 2, 50); brs.append(bed)
    for r in range(5):
        for c in range(6):
            k = M.revolve(name + "_k%d%d" % (r, c),
                          [(0.0, 0.0), (0.011, 0.003), (0.010, 0.014),
                           (0.0, 0.015)], segments=10, cname=cname)
            M.rot_x(k, math.radians(-74))
            M.translate(k, (-0.125 + c * 0.05, -0.152 + r * 0.016,
                            0.072 + r * 0.030))
            (wht if (r + c) % 4 == 0 else blk).append(k)
    # the drawer, with a pull
    dr = M.prism_xz(name + "_dr",
                    [(-0.132, 0.056), (0.132, 0.056), (0.132, 0.122),
                     (-0.132, 0.122)], -0.196, -0.152, cname)
    M.bevel(dr, 0.006, 2, 50); brs.append(dr)
    pull = M.tube_along(name + "_pl",
                        [(-0.052, -0.206, 0.090), (0.052, -0.206, 0.090)],
                        M.circle(0.007, 8), cname=cname, up=(0, 0, 1))
    M.smooth_shade(pull, 40); brs.append(pull)
    ob = M.join(brs, name + "_brass", cname); M.set_mat(ob, m['brass'])
    ok = M.join(blk, name + "_blk", cname); M.set_mat(ok, m['black'])
    ow = M.join(wht, name + "_flag", cname); M.set_mat(ow, m['card'])
    out = [ob, ok, ow]
    for o in out:
        if rot:
            M.rotate_z(o, math.radians(rot))
        M.translate(o, (cx, cy, cz))
    return out


def chalkboard(name, x, y0, y1, z0, z1, cname=C):
    """The menu board over the back bar, in its heavy green frame."""
    m = mats()
    # the slate is REBATED into the frame - sharing the frame back plane put
    # two same-facing faces on it, which is the definition of a z-fight
    slate = M.box(name + "_s", x + 0.007, y0 + 0.065, z0 + 0.065, x + 0.029,
                  y1 - 0.065, z1 - 0.065, cname)
    M.set_mat(slate, m['chalk'])
    fr = []
    for (a, b, c, d) in ((y0, y1, z1 - 0.075, z1), (y0, y1, z0, z0 + 0.075),
                         (y0, y0 + 0.075, z0, z1), (y1 - 0.075, y1, z0, z1)):
        p = M.box(name + "_f%d" % len(fr), x, a, c, x + 0.046, b, d, cname)
        M.bevel(p, 0.005, 2, 50)
        fr.append(p)
    of = M.join(fr, name + "_frame", cname); M.set_mat(of, m['green'])
    return [slate, of]


def small_gear(cname=C):
    """The working clutter along the back counter: grinder, brewer, toaster,
    stacked cups.  Blocked in as real objects because the counter reads as
    abandoned without them."""
    m = mats()
    out = []
    D = L.BACK_D
    z = L.BACK_H
    # burr grinder
    g = []
    g.append(M.prism("Gr_base", M.rounded_rect(0.16, 0.18, 0.02, seg=4),
                     0.0, 0.20, cname))
    hop = M.revolve("Gr_hop", [(0.0, 0.20), (0.055, 0.22), (0.075, 0.30),
                               (0.078, 0.42), (0.070, 0.44), (0.0, 0.44)],
                    segments=20, cname=cname)
    M.smooth_shade(hop, 40)
    og = M.join(g, "Gr_body", cname); M.set_mat(og, m['steel'])
    M.set_mat(hop, m['glass'])
    for o in (og, hop):
        M.translate(o, (0.30, 5.95, z))
    out += [og, hop]
    # filter brewer with two glass jugs
    br = M.prism("Brew_b", M.rounded_rect(0.30, 0.22, 0.02, seg=4), 0.0, 0.11,
                 cname)
    top = M.prism("Brew_t", M.rounded_rect(0.30, 0.22, 0.02, seg=4), 0.34, 0.46,
                  cname)
    col = M.box("Brew_c", -0.15, -0.11, 0.11, -0.09, 0.11, 0.34, cname)
    ob2 = M.join([br, top, col], "Brew", cname); M.set_mat(ob2, m['black'])
    M.translate(ob2, (0.26, 6.55, z))
    out.append(ob2)
    for i in range(2):
        jug = M.revolve("Brew_j%d" % i,
                        [(0.0, 0.0), (0.070, 0.0), (0.074, 0.020),
                         (0.072, 0.135), (0.082, 0.150), (0.078, 0.165),
                         (0.070, 0.165), (0.070, 0.155), (0.0, 0.155)],
                        segments=20, cname=cname)
        M.smooth_shade(jug, 40); M.set_mat(jug, m['glass'])
        M.translate(jug, (0.26, 6.44 + i * 0.22, z + 0.115))
        out.append(jug)
    # stacked cups and saucers
    for k in range(3):
        st = []
        for i in range(4):
            c = M.revolve("Cupst%d_%d" % (k, i),
                          [(0.0, 0.0), (0.036, 0.004), (0.041, 0.052),
                           (0.038, 0.056), (0.034, 0.010), (0.0, 0.008)],
                          segments=16, cname=cname)
            M.translate(c, (0, 0, i * 0.032))
            st.append(c)
        o = M.join(st, "Cupstack%d" % k, cname)
        M.set_mat(o, T.paint('cw_cupwhite', 'E4E0D6', rough=0.16, coat=0.5))
        M.smooth_shade(o, 40)
        M.translate(o, (0.22 + (k % 2) * 0.13, 9.30 + k * 0.19, z))
        out.append(o)
    return out


def build():
    M.coll(C)
    m = mats()
    out = []
    out += service_counter()
    out += back_bar()
    # the machines, on the back-bar top
    z = L.BACK_H
    # rot=+90, not -90: the group heads, the drip tray and the steam wands are
    # all modelled on the machine's -Y side, and a quarter turn the other way
    # pointed the working face of it at the wall
    out += espresso("Espresso", 0.36, 8.30, z, rot=90)
    out += urn("Urn", 0.26, 7.30, z, rot=-90)
    out += bean_cylinder("Beans", 0.30, 7.72, z)
    out += chalkboard("Chalk", -0.004, CHALK_Y[0], CHALK_Y[1],
                      CHALK_Z[0], CHALK_Z[1])
    out += chalk_menu("Menu", 0.018, CHALK_Y[0], CHALK_Y[1],
                      CHALK_Z[0], CHALK_Z[1])
    out += small_gear()
    out += stock()
    # on the customer counter
    # Three things on one counter top, and none of them may hang over an
    # edge or sit on another.  The usable strip is x 1.42 (back, plus a
    # margin) out to the front line LESS the top's 48 mm overhang, and
    # the front line is not constant: x 2.00 north of y 9.36, splaying
    # out to 2.50 between 9.36 and 8.86.  So:
    #   till    0.40 across  at (1.68, 9.80)  -> x 1.48..1.88  y 9.60..10.00
    #   dome A  0.32 across  at (1.70, 9.20)  -> x 1.54..1.86  y 9.04..9.36
    #   dome B  0.29 across  at (2.02, 8.72)  -> x 1.88..2.17  y 8.58..8.87
    # every one inside the top, and 240 mm and 170 mm of clear counter
    # between them.
    out += cake_dome("Cake_a", 1.70, 9.20, L.SERVE_H)
    out += cake_dome("Cake_b", 2.02, 8.72, L.SERVE_H, r=0.145)
    out += register("Till", 1.68, 9.80, L.SERVE_H, rot=-96)
    print("counter:", len([o for o in bpy.data.objects
                           if o.users_collection and
                           o.users_collection[0].name == C]))
    return out


# --------------------------------------------------------------- chalk menu

MENU = [
    ("CENTRAL PERK", 0.115, 'F2EFE6'),
    ("", 0.0, None),
    ("HOUSE BLEND      1.50", 0.062, 'E8E4D6'),
    ("CAFE AU LAIT     1.75", 0.062, 'E8E4D6'),
    ("CAPPUCCINO       2.25", 0.062, 'F0C86A'),
    ("ESPRESSO         1.95", 0.062, 'E8E4D6'),
    ("LATTE            2.25", 0.062, 'E88A9C'),
    ("MOCHA            2.50", 0.062, 'E8E4D6'),
    ("MUFFIN . SCONE . PIE", 0.055, 'A8D08A'),
]


def chalk_menu(name, x, y0, y1, z0, z1, cname=C):
    """The menu written on the board.

    The board is the biggest single flat surface any camera sees and an
    empty one reads as a green rectangle - in main_couch.webp it is dense
    handwritten chalk and that texture is most of what the wall gives back.
    Text objects converted to mesh, sitting a couple of millimetres proud of
    the slate so there is no coplanar pair."""
    m = mats()
    ph, pv = 0.075, 0.055
    # Fit the block to the SLATE, not to a fixed line pitch.  At a hard
    # 105 mm the ten lines of this menu ran 50 mm past the bottom of the
    # slate and the last one - MUFFIN . SCONE . PIE - was written across the
    # frame.  The slate is rebated 65 mm inside the frame on every side (see
    # chalkboard()), so that is the box the text has to live in.
    s_top, s_bot = z1 - 0.065, z0 + 0.065
    units = sum(0.6 if not b else 1.0 for (b, s, c) in MENU) - 1.0
    last = next(s for (b, s, c) in reversed(MENU) if b)
    avail = (s_top - s_bot) - 2 * pv - last
    pitch = min(0.105, avail / max(1e-6, units))
    top = s_top - pv
    out = []
    line = 0
    for i, (body, size, col) in enumerate(MENU):
        if not body:
            line += 0.6
            continue
        cu = bpy.data.curves.new("%s_c%d" % (name, i), type='FONT')
        cu.body = body
        cu.size = size
        cu.extrude = 0.0016
        cu.align_x = 'LEFT'
        cu.align_y = 'TOP'
        cu.space_character = 1.06
        ob = bpy.data.objects.new("%s_l%d" % (name, i), cu)
        M.put(ob, cname)
        M.active(ob)
        bpy.ops.object.convert(target='MESH')
        ob = bpy.context.object
        M.rot_x(ob, math.radians(90))
        M.rotate_z(ob, math.radians(90))
        M.translate(ob, (x + 0.026, y0 + ph, top - line * pitch))
        M.set_mat(ob, T.paint("chalkink_" + (col or 'F2EFE6'), col or 'F2EFE6',
                              rough=0.90, bump=0.30, scale=200.0))
        out.append(ob)
        line += 1.0 if size < 0.10 else 1.5
    return out


# --------------------------------------------------------------- shop stock

def _jar(name, x, y, z, r=0.048, h=0.155, cname=C):
    m = mats()
    g = M.revolve(name + "_g",
                  [(r * 0.72, 0.0), (r, 0.020), (r, h - 0.030),
                   (r * 0.82, h - 0.004), (r * 0.80, h + 0.014),
                   (r * 0.74, h + 0.016), (r * 0.74, h - 0.006),
                   (r * 0.94, h - 0.030), (r * 0.94, 0.024),
                   (r * 0.66, 0.008)], segments=18, cname=cname)
    M.smooth_shade(g, 42); M.set_mat(g, m['glass'])
    fill = M.revolve(name + "_f", [(0.0, 0.010), (r * 0.90, 0.010),
                                   (r * 0.90, h * 0.72), (0.0, h * 0.74)],
                     segments=18, cname=cname)
    M.set_mat(fill, T.wood(name + "_fm", light='6B4522', dark='2A1608',
                           ring=140.0, scale=0.05))
    lid = M.revolve(name + "_l", [(0.0, h + 0.012), (r * 0.80, h + 0.010),
                                  (r * 0.84, h + 0.030), (0.0, h + 0.034)],
                    segments=18, cname=cname)
    M.set_mat(lid, m['brass'])
    out = [g, fill, lid]
    for o in out:
        M.translate(o, (x, y, z))
    return out


def _carton(name, x, y, z, w=0.070, d=0.072, h=0.170, colour='7A2A20',
            label='C8B48A', rot=0.0, cname=C):
    """A retail carton standing on a shelf, face out.

    A printed box is a box plus a label panel, and the panel is what makes a
    shelf of them read as a shop: without it they are a row of coloured
    blocks.  The panel stands 1.5 mm proud of the face, so it is a surface in
    its own right and not a decal on a coplanar pair."""
    body = M.box(name + "_b", -w / 2, -d / 2, 0.0, w / 2, d / 2, h, cname)
    M.bevel(body, 0.004, 2, 55)
    M.set_mat(body, T.flat(name + "_m", colour, rough=0.62))
    # the panel is REBATED into the face; sitting on it, its back plane and
    # the carton's front were the same plane - a z-fight per box
    pan = M.box(name + "_p", -w / 2 + 0.006, d / 2 - 0.005, h * 0.24,
                w / 2 - 0.006, d / 2 + 0.0032, h * 0.86, cname)
    M.set_mat(pan, T.flat(name + "_l", label, rough=0.55))
    out = [body, pan]
    for o in out:
        if rot:
            M.rotate_z(o, math.radians(rot))
        M.translate(o, (x, y, z))
    return out


def _bag(name, x, y, z, w=0.10, d=0.065, h=0.20, colour='7A2A20', rot=0.0,
         cname=C):
    """A retail coffee bag: gusseted sides, folded top, so it does not read
    as a brick."""
    rings = []
    for (t, sw, sd) in ((0.0, 0.98, 0.98), (0.10, 1.02, 1.02),
                        (0.62, 1.0, 1.0), (0.86, 0.94, 0.72),
                        (0.97, 0.88, 0.30), (1.0, 0.86, 0.16)):
        # the corner radius has to shrink with the ring: a fixed one is larger
        # than the folded top is wide, and the corners fold through each other
        poly = M.rounded_rect(w * sw, d * sd, min(w * sw, d * sd) * 0.30, seg=3)
        rings.append([(px, py, z + h * t) for (px, py) in poly])
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)
    M.bevel(ob, 0.003, 1, 60)
    M.set_mat(ob, T.paint("bag_" + colour, colour, rough=0.52, coat=0.12,
                          bump=0.14))
    if rot:
        M.rotate_z(ob, math.radians(rot))
    M.translate(ob, (x, y, 0.0))
    return [ob]


def _tin(name, x, y, z, r=0.045, h=0.115, colour='2A5A46', cname=C):
    m = mats()
    ob = M.revolve(name, [(0.0, 0.0), (r, 0.0), (r, h - 0.008),
                          (r * 0.96, h - 0.004), (r * 0.96, h),
                          (r * 0.90, h + 0.006), (0.0, h + 0.006)],
                   segments=20, cname=cname)
    M.smooth_shade(ob, 40)
    M.set_mat(ob, T.paint("tin_" + colour, colour, rough=0.30, coat=0.35))
    M.translate(ob, (x, y, z))
    return [ob]


# What is actually on those shelves is coffee: glass jars of beans, kraft
# bags, and a few painted tins.  The first palette was eight fully saturated
# hues on rotation, which turned the back bar into a row of skittles and made
# it the brightest thing in a room whose brightest thing should be the
#storefront - so this is mostly brown and unbleached paper, with two accents.
COLOURS = ['5E3A22', '4A2E1C', '6E4A2A', '7A5A3A', '3A4A34', '8A5A24',
           '5A4632', '7A2A20', '2E4258']


def stock(cname=C):
    """Fill the shelves and the retail display.  A shop with nothing on its
    shelves reads as a set that has not been dressed, which is exactly what
    this is trying not to be."""
    out = []
    y0s = CHALK_Y[1] + 0.30
    y1 = L.BACK_TALL_N[0]
    k = 0
    # three open shelves over the back bar
    for si, z in enumerate((1.386, 1.746, 2.106)):
        y = y0s + 0.12
        while y < y1 - 0.16:
            k += 1
            pick = (k * 2) % 5          # jars two shelf-slots in five
            if pick in (0, 1):
                out += _jar("Jar%d" % k, 0.135, y + 0.055, z,
                            r=0.044 + 0.008 * ((k % 3) / 2.0),
                            h=0.135 + 0.05 * ((k % 4) / 3.0), cname=cname)
                y += 0.125
            elif pick in (2, 3):
                out += _bag("Bag%d" % k, 0.130, y + 0.052, z, w=0.098,
                            d=0.062, h=0.175 + 0.04 * ((k % 3) / 2.0),
                            colour=COLOURS[k % len(COLOURS)],
                            rot=(k * 13) % 25 - 12, cname=cname)
                y += 0.118
            else:
                out += _tin("Tin%d" % k, 0.128, y + 0.050, z,
                            r=0.040 + 0.006 * ((k % 2)),
                            h=0.095 + 0.04 * ((k % 3) / 2.0),
                            colour=COLOURS[(k + 3) % len(COLOURS)],
                            cname=cname)
                y += 0.110
    # The retail display, IN the counter now.  Upright cartons packed edge to
    # edge and facing the room, which is what the reference holds - the tins
    # and bags that stood here read as a jumble of cylinders on a ledge.
    for si, z in enumerate(CASE_Z):
        y = CASE_Y[0] + 0.046
        while y < CASE_Y[1] - 0.105:
            k += 1
            bw = 0.058 + 0.030 * ((k * 3) % 4) / 3.0
            bh = 0.150 + 0.060 * ((k * 5) % 3) / 2.0
            out += _carton("RBox%d" % k, 1.945, y + bw * 0.5, z + 0.020,
                           w=bw, d=0.072, h=bh,
                           colour=COLOURS[k % len(COLOURS)],
                           label=COLOURS[(k + 4) % len(COLOURS)],
                           rot=((k * 11) % 9) - 4, cname=cname)
            y += bw + 0.007
    # and a row along the back-bar top behind the machines
    for i in range(4):
        out += _jar("TJar%d" % i, 0.20, 10.05 + i * 0.16, L.BACK_H,
                    r=0.050, h=0.185, cname=cname)
    return out
