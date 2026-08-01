"""Round pedestal table with a glass top, plus the mismatched chairs."""
import bpy, math, random
from mathutils import Matrix, Vector
import mlib, mats, L, props as P

C = "Dining"


def mk_mats():
    M = {}
    # low contrast between early and late wood - a wide tonal spread turns every
    # growth ring into a hard black line, which is what read as corduroy
    # the table reads mid-brown in the set photo; the old values bleached
    # out to near-white once the ramp was pulled back towards its mean
    # A 60% swing from early to late wood reads as painted stripes once the
    # rings are 8 cm apart, which is what a turned pedestal shows: hold the
    # spread to about a fifth and the colour comes from the timber, not the ring
    # Flattening the ring *bump* changed nothing here - the banding was pure
    # colour, proved by holding the ramp at one tone, which wiped it out
    # entirely.  The set's table is near enough plain warm oak, so the early to
    # late wood swing is held to about a tenth rather than a fifth.
    OAKC = ('A17A4E', '9A7449', '8E6A40')
    # 110 rings/metre is 9 mm apart - at table scale that reads as corduroy.
    # Real cathedral grain on a top like this is a handful of wide arcs.
    # ~13 rings/m is one grain line every 8 cm - about what you actually see
    # across a table top; anything near 30 reads as corduroy at this scale
    # 13 rings/m is one grain line every 8 cm: across a 1.2 m top that is a
    # dozen broad bands, which reads as a painted swirl however low the
    # contrast.  26 gives a grain line every 4 cm, about what oak actually does.
    OAKK = dict(ring=26.0, warp=0.22, warp_scale=1.3, distort=2.2, bump=0.05,
                rough=(0.28, 0.46))
    # the top needs straight plank grain running across it - 'XY' put concentric
    # rings on the disc and made it read as a polished brass tray
    M['oak_top'] = mats.wood('wood_oak_table_top', OAKC, axis='YZ', **OAKK)
    M['oak'] = mats.wood('wood_oak_table', OAKC, axis='XY', **OAKK)
    M['oak_z'] = mats.wood('wood_oak_table_z', OAKC, axis='Z', **OAKK)
    M['chair'] = mats.wood('wood_chair_honey', ('D2A05E', 'B98844', '96682C'),
                           ring=20.0, warp=0.18, warp_scale=1.2, distort=1.6,
                           bump=0.05, rough=(0.18, 0.32), axis='XY')
    M['bentwood'] = mats.wood('wood_bentwood', ('68391F', '552C15', '41200D'),
                              ring=24.0, warp=0.16, distort=1.4, bump=0.06,
                              rough=(0.16, 0.30), axis='XY')
    M['glass'] = mats.get('glass_clear') or mats.pane('glass_clear')
    # The seat cushions are a dusty tapestry print, and small: at scale 6.5 one
    # blossom filled a third of the pad and it read as a child's beach ball.
    M['tapestry'] = mats.floral_chintz('chintz_tapestry', ground='7C8593',
                                       petal='8A6570', petal2='90696E',
                                       leaf='4E5A48', leaf2='63705A', scale=21.0,
                                       rough=0.84)
    M['cushpurple'] = mats.velvet('velvet_purple_seat', '4A2E5E')
    M['piping'] = mats.fabric('fabric_white_pipe', 'EFEAE0', rough=0.7)
    return M


def round_table(name, cx, cy, M, r=0.60, h=0.755, cname=C):
    parts = []
    # top: moulded edge profile, revolved
    tp = [(0.0, h - 0.052), (r - 0.030, h - 0.052), (r - 0.010, h - 0.046),
          (r, h - 0.034), (r, h - 0.020), (r - 0.008, h - 0.010),
          (r - 0.004, h - 0.004), (r - 0.014, h), (0.0, h)]
    top = mlib.revolve(name + "_top", tp, 56, cname=cname)
    mlib.smooth_shade(top, 26)
    parts.append((top, M['oak_top']))
    # apron band under the top
    ap = [(0.0, h - 0.115), (r - 0.055, h - 0.115), (r - 0.040, h - 0.100),
          (r - 0.036, h - 0.070), (r - 0.026, h - 0.056), (0.0, h - 0.052)]
    apr = mlib.revolve(name + "_apron", ap, 48, cname=cname)
    mlib.smooth_shade(apr, 30)
    parts.append((apr, M['oak_z']))
    # turned baluster pedestal
    pd = [(0.0, 0.075), (0.150, 0.075), (0.155, 0.090), (0.140, 0.110),
          (0.098, 0.135), (0.086, 0.160), (0.096, 0.190), (0.130, 0.235),
          (0.158, 0.290), (0.166, 0.345), (0.150, 0.400), (0.112, 0.448),
          (0.082, 0.482), (0.072, 0.520), (0.080, 0.552), (0.104, 0.575),
          (0.100, 0.596), (0.078, 0.612), (0.076, h - 0.115), (0.0, h - 0.115)]
    ped = mlib.revolve(name + "_ped", pd, 40, cname=cname)
    mlib.smooth_shade(ped, 30)
    # rings vary across the log, not along it: a turned column is cut with the
    # grain running up its axis, so 'Z' drew contour bands round the baluster
    parts.append((ped, M['oak']))
    # cross base: four shaped feet
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        prof = [(0.055, 0.0), (0.48, 0.0), (0.50, 0.016), (0.47, 0.046),
                (0.34, 0.062), (0.22, 0.076), (0.13, 0.086), (0.055, 0.088)]
        vs, fs = [], []
        n = len(prof)
        half = 0.062
        for (rr, zz) in prof:
            vs.append((rr, -half * (0.45 + 0.55 * (1 - rr / 0.5)), zz))
        for (rr, zz) in prof:
            vs.append((rr, half * (0.45 + 0.55 * (1 - rr / 0.5)), zz))
        for i in range(n - 1):
            fs.append((i, i + 1, n + i + 1, n + i))
        fs.append(tuple(range(n)))
        fs.append(tuple(range(2 * n - 1, n - 1, -1)))
        foot = mlib.mesh_obj(name + "_ft%d" % k, vs, fs, cname)
        mlib.recalc_normals(foot)
        mlib.bevel(foot, 0.006, 2, 40)
        mlib.rotate_z(foot, a)
        parts.append((foot, M['oak']))
        # pad foot at the tip
        pf = mlib.revolve(name + "_pf%d" % k, [(0.0, 0.0), (0.050, 0.006),
                                               (0.054, 0.026), (0.040, 0.044),
                                               (0.0, 0.048)], 16, cname=cname)
        mlib.translate(pf, (0.455 * math.cos(a), 0.455 * math.sin(a), 0.0))
        mlib.smooth_shade(pf, 40)
        parts.append((pf, M['oak']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, 0.0))
        objs.append(ob)
    return objs


# ------------------------------------------------------------------- chairs
def turned_leg(name, h, r0, taper=0.62, rings=((0.18, 1.25), (0.55, 0.85)),
               cname=C):
    prof = [(0.0, 0.0), (r0 * 0.9, 0.0), (r0 * 0.95, 0.010)]
    steps = 26
    for i in range(1, steps + 1):
        t = i / steps
        rr = r0 * (1.0 - (1.0 - taper) * t)
        for (pos, amp) in rings:
            d = abs(t - pos)
            if d < 0.055:
                rr *= 1.0 + (amp - 1.0) * math.cos(d / 0.055 * math.pi * 0.5) ** 2
        prof.append((rr, h * t))
    prof.append((0.0, h))
    ob = mlib.revolve(name, prof, 16, cname=cname)
    mlib.smooth_shade(ob, 34)
    return ob


def _aim(ob, a, b2):
    """Place an object built along +Z from the origin so it runs from a to b2."""
    d = Vector(b2) - Vector(a)
    ln = d.length
    d = d / ln
    phi = math.asin(max(-1.0, min(1.0, d.x)))
    c = math.sqrt(max(1e-9, 1.0 - d.x * d.x))
    psi = math.atan2(-d.y / c, d.z / c)
    mlib.rot_y(ob, phi)
    mlib.rot_x(ob, psi)
    mlib.translate(ob, a)
    return ob


def _turned(name, ln, prof, cname=C, seg=14):
    """Turned member of length `ln` along +Z.  prof is a list of (t, r) with
    t in 0..1 along the length; the ends are closed on the axis."""
    p = [(0.0, 0.0)]
    for (t, r) in prof:
        p.append((r, t * ln))
    p.append((0.0, ln))
    ob = mlib.revolve(name, p, seg, cname=cname)
    mlib.smooth_shade(ob, 36)
    return ob


# Turnings taken off the set chair, ordered foot (t=0) -> seat (t=1) to match
# the direction _aim sweeps them: a domed foot, a small ring above it, a long
# taper up to the vase swelling, then the collar under the seat.
LEG_PROF = [(0.000, 0.0060), (0.007, 0.0115), (0.016, 0.0152), (0.030, 0.0172),
            (0.048, 0.0158), (0.075, 0.0138), (0.105, 0.0148), (0.190, 0.0140),
            (0.310, 0.0150), (0.440, 0.0168), (0.575, 0.0192), (0.675, 0.0222),
            (0.745, 0.0250), (0.800, 0.0260), (0.850, 0.0238), (0.888, 0.0198),
            (0.925, 0.0190), (0.952, 0.0216), (0.978, 0.0230), (1.000, 0.0208)]
# stretchers: a plain rod with a turned bobbin at mid-span
STR_PROF = [(0.000, 0.0125), (0.060, 0.0115), (0.300, 0.0100), (0.395, 0.0112),
            (0.430, 0.0150), (0.470, 0.0165), (0.530, 0.0165), (0.570, 0.0150),
            (0.605, 0.0112), (0.700, 0.0100), (0.940, 0.0115), (1.000, 0.0125)]
# spindles: slender, with a soft swell low down
SPN_PROF = [(0.000, 0.0110), (0.070, 0.0125), (0.170, 0.0115), (0.300, 0.0092),
            (0.500, 0.0078), (0.720, 0.0068), (0.900, 0.0062), (1.000, 0.0058)]


def _seat_outline(sw, sd, n=72):
    """D-shaped Windsor seat: a full round front, a squarer and slightly
    narrower back."""
    pts = []
    for i in range(n):
        a = math.tau * i / n
        c, s = math.cos(a), math.sin(a)
        k = 2.35 if s >= 0 else 3.60          # rounder front, squarer back
        taper = 1.0 if s >= 0 else 1.0 - 0.075 * (-s) ** 1.4
        x = (sw / 2) * taper * math.copysign(abs(c) ** (2.0 / k), c)
        y = (sd / 2) * math.copysign(abs(s) ** (2.0 / k), s)
        pts.append((x, y))
    return pts


def windsor_chair(name, cx, cy, rot, M, cname=C, seat_h=0.455, cushion=True):
    """Hoop-back Windsor side chair in golden oak, as on the set: a single
    steam-bent hoop springing from the back of the seat, five turned spindles
    inside it that die into the hoop's inner face, a saddled D-shaped plank
    seat, four raked turned legs and a turned H-stretcher.  Everything is
    joined at computed points so no member floats or passes through the seat."""
    parts = []
    sw, sd, st = 0.425, 0.395, 0.033
    ztop, zbot = seat_h, seat_h - st

    # ---------------------------------------------------------------- seat
    out = _seat_outline(sw, sd)
    rings = []
    for (dz, s) in ((-st, 0.90), (-st + 0.009, 0.965), (-0.013, 1.0),
                    (0.0, 1.0)):
        rings.append([(x * s, y * s, ztop + dz) for (x, y) in out])
    seat = mlib._loft(name + "_seat", rings, close_u=False, close_v=True,
                      cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(seat, 0.004, 2, 50)
    mlib.smooth_shade(seat, 38)
    parts.append(seat)

    # ---------------------------------------------------------------- legs
    RAKE_X, RAKE_Y = math.radians(7.5), math.radians(8.0)
    tops, feet = {}, {}
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        top = (sx * (sw / 2 - 0.068), sy * (sd / 2 - 0.062), zbot + 0.008)
        foot = (top[0] + sx * top[2] * math.tan(RAKE_X),
                top[1] + sy * top[2] * math.tan(RAKE_Y), 0.0)
        tops[(sx, sy)], feet[(sx, sy)] = top, foot
        ln = (Vector(top) - Vector(foot)).length
        lg = _turned(name + "_lg", ln, LEG_PROF, cname, seg=16)
        _aim(lg, foot, top)
        parts.append(lg)

    def on_leg(key, z):
        """Point on a leg's axis at height z."""
        a, b2 = feet[key], tops[key]
        t = (z - a[2]) / (b2[2] - a[2])
        return (a[0] + (b2[0] - a[0]) * t, a[1] + (b2[1] - a[1]) * t, z)

    # ------------------------------------------------------- H stretcher
    ZS = 0.190
    mids = []
    for sx in (-1, 1):
        a = on_leg((sx, 1), ZS)
        b2 = on_leg((sx, -1), ZS)
        # run the rod a little way into each leg so the joint is closed
        d = (Vector(b2) - Vector(a)).normalized() * 0.014
        a2, b3 = Vector(a) - d, Vector(b2) + d
        sr = _turned(name + "_st", (b3 - a2).length, STR_PROF, cname, seg=12)
        _aim(sr, a2, b3)
        parts.append(sr)
        mids.append((Vector(a) + Vector(b2)) * 0.5)
    d = (mids[1] - mids[0]).normalized() * 0.012
    cr = _turned(name + "_cs", (mids[1] - mids[0]).length + 0.024, STR_PROF,
                 cname, seg=12)
    _aim(cr, mids[0] - d, mids[1] + d)
    parts.append(cr)

    # ------------------------------------------------------------- hoop
    # The hoop is a straight-sided arch closed by a half ellipse, drawn in a
    # plane that leans back from the seat's rear edge.
    BASE_HW, ARCH_HW, ARCH_H, POST_H = 0.176, 0.166, 0.205, 0.360
    LEAN = math.radians(9.5)
    BASE_Y = -sd / 2 + 0.048

    def hoop_pt(u, v):
        return (u, BASE_Y - v * math.sin(LEAN), ztop - 0.014 + v * math.cos(LEAN))

    path = []
    for i in range(9):                                   # left post
        t = i / 8.0
        path.append(hoop_pt(-BASE_HW + (BASE_HW - ARCH_HW) * t, POST_H * t))
    for i in range(1, 30):                               # arch over the top
        th = math.pi * i / 30.0
        path.append(hoop_pt(-ARCH_HW * math.cos(th),
                            POST_H + ARCH_H * math.sin(th)))
    for i in range(9):                                   # right post
        t = 1.0 - i / 8.0
        path.append(hoop_pt(BASE_HW - (BASE_HW - ARCH_HW) * t, POST_H * t))
    hoop = mlib.tube_along(name + "_hoop", path,
                           mlib.rounded_rect(0.030, 0.023, 0.009, 3), cname)
    mlib.smooth_shade(hoop, 40)
    parts.append(hoop)

    # ---------------------------------------------------------- spindles
    NSP = 5
    for k in range(NSP):
        f = (k - (NSP - 1) / 2.0) / ((NSP - 1) / 2.0)     # -1 .. 1
        u_top = f * ARCH_HW * 0.74
        th = math.acos(max(-1.0, min(1.0, -u_top / ARCH_HW)))
        v_top = POST_H + ARCH_H * math.sin(th)
        tp = hoop_pt(u_top, v_top)
        # stop on the hoop's inner face, not through it
        tp = (tp[0], tp[1] + 0.011 * math.cos(LEAN), tp[2] - 0.011 * math.sin(LEAN))
        bs = (f * BASE_HW * 0.60, BASE_Y + 0.004, ztop - 0.012)
        ln = (Vector(tp) - Vector(bs)).length
        sp = _turned(name + "_sp%d" % k, ln, SPN_PROF, cname, seg=10)
        _aim(sp, bs, tp)
        parts.append(sp)

    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, M['chair'])
    mlib.rotate_z(ob, rot)
    mlib.translate(ob, (cx, cy, 0.0))
    res = [ob]
    if cushion:
        # A boxed pad tied on over the seat, not a mat laid inside it: it covers
        # the seat out to the edge, swells in the middle, and its front lip
        # slumps over the leading edge under its own weight.  Inset and flat, it
        # read as a dinner plate sitting on the chair.
        pts = _seat_outline(sw - 0.010, sd - 0.004, 56)
        z0 = ztop + 0.003

        def _sag(y):
            f = max(0.0, min(1.0, (y / (sd * 0.5) - 0.10) / 0.90))
            return f * f

        rings = []
        for (dz, s, dp) in ((0.000, 0.94, 0.30), (0.013, 1.005, 0.85),
                            (0.040, 1.025, 1.00), (0.068, 1.000, 0.80),
                            (0.081, 0.92, 0.45)):
            rings.append([(x * s, y * s, z0 + dz - 0.026 * dp * _sag(y))
                          for (x, y) in pts])
        cu = mlib._loft(name + "_cush", rings, close_u=False, close_v=True,
                        cname=cname, cap_start=True, cap_end=True)
        mlib.bevel(cu, 0.004, 2, 55)
        mlib.smooth_shade(cu, 50)
        mlib.set_mat(cu, M['tapestry'])
        mlib.rotate_z(cu, rot)
        mlib.translate(cu, (cx, cy, 0.0))
        res.append(cu)
        # piped seam round the middle of the box
        pipe = mlib.tube_along(
            name + "_pipe",
            [(x * 1.028, y * 1.028, z0 + 0.040 - 0.026 * _sag(y))
             for (x, y) in pts], mlib.circle(0.0055, 7), cname,
            close_path=True)
        mlib.smooth_shade(pipe, 40)
        mlib.set_mat(pipe, M['piping'])
        mlib.rotate_z(pipe, rot)
        mlib.translate(pipe, (cx, cy, 0.0))
        res.append(pipe)
    return res


def bentwood_chair(name, cx, cy, rot, M, cname=C, seat_h=0.455):
    parts = []
    r = 0.205
    # round seat
    st = mlib.revolve(name + "_seat", [(0.0, 0.0), (r - 0.012, 0.0),
                                       (r, 0.010), (r, 0.026), (r - 0.014, 0.034),
                                       (0.0, 0.030)], 34, cname=cname)
    mlib.smooth_shade(st, 34)
    parts.append(st)
    mlib.translate(st, (0, 0, seat_h - 0.034))
    # hoop back (a big circle bent up from the seat rim)
    pts = []
    n = 26
    for i in range(n + 1):
        t = i / n
        a = math.pi * (1.0 - t)
        pts.append((r * 0.93 * math.cos(a),
                    0.10 - 0.30 * math.sin(a) ** 1.4,
                    seat_h + 0.46 * math.sin(a) ** 0.55))
    for i in (0, n):
        pass
    full = [(pts[0][0], pts[0][1], seat_h - 0.01)] + pts + \
           [(pts[-1][0], pts[-1][1], seat_h - 0.01)]
    hoop = mlib.tube_along(name + "_hoop", full,
                           [(0.012, -0.016), (0.012, 0.016), (-0.012, 0.016),
                            (-0.012, -0.016)], cname)
    parts.append(hoop)
    # inner scroll
    inner = []
    for i in range(19):
        t = i / 18.0
        a = math.pi * (1.0 - t)
        inner.append((r * 0.55 * math.cos(a), 0.055 - 0.20 * math.sin(a) ** 1.4,
                      seat_h + 0.11 + 0.24 * math.sin(a) ** 0.6))
    parts.append(mlib.tube_along(name + "_in", inner, mlib.circle(0.010, 8), cname))
    # legs
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        lg = mlib.tube_along(name + "_lg%d" % k,
                             [(r * 0.72 * math.cos(a), r * 0.72 * math.sin(a),
                               seat_h - 0.03),
                              (r * 0.95 * math.cos(a), r * 0.95 * math.sin(a),
                               seat_h * 0.55),
                              (r * 1.18 * math.cos(a), r * 1.18 * math.sin(a), 0.0)],
                             mlib.circle(0.0145, 9), cname)
        parts.append(lg)
    ring = mlib.tube_along(name + "_ring",
                           [(r * 1.0 * math.cos(a), r * 1.0 * math.sin(a), 0.20)
                            for a in [i * math.tau / 26 for i in range(26)]],
                           mlib.circle(0.0095, 7), cname, close_path=True)
    parts.append(ring)
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 40)
    mlib.set_mat(ob, M['bentwood'])
    mlib.rotate_z(ob, rot)
    mlib.translate(ob, (cx, cy, 0.0))
    return [ob]


def build():
    M = mk_mats()
    cx, cy = L.TABLE_C
    round_table("D_table", cx, cy, M)
    windsor_chair("D_chair1", cx - 0.80, cy - 0.10, math.radians(-82), M)
    windsor_chair("D_chair2", cx + 0.22, cy - 0.78, math.radians(14), M)
    bentwood_chair("D_chair3", cx + 0.78, cy + 0.22, math.radians(108), M)
    windsor_chair("D_chair4", cx - 0.18, cy + 0.80, math.radians(190), M,
                  cushion=False)
    # a bowl of fruit + a couple of mugs on the glass top
    pool = P.palette(21, 8)
    bw = P.bowl("D_bowl", 0.115, 0.062, C, mats.paint('bowl_white', 'F0EBDC',
                                                      rough=0.14, coat=0.6))
    for o in bw:
        mlib.translate(o, (cx + 0.06, cy + 0.05, 0.766))
    rng = random.Random(3)
    fm = mats.paint('fruit_orange', 'D9721F', rough=0.42, coat=0.2)
    for i in range(5):
        a = math.tau * i / 5
        fr = mlib.revolve("D_fruit%d" % i, [(0.0, -0.031), (0.024, -0.020),
                                            (0.031, 0.0), (0.024, 0.020),
                                            (0.0, 0.031)], 16, cname=C)
        mlib.smooth_shade(fr, 40)
        mlib.set_mat(fr, fm)
        mlib.translate(fr, (cx + 0.06 + 0.042 * math.cos(a),
                            cy + 0.05 + 0.042 * math.sin(a), 0.828))
    for i, (dx, dy) in enumerate(((-0.30, 0.16), (-0.24, -0.14))):
        for o in P.cup("D_mug%d" % i, 0.042, 0.088, C, rng.choice(pool)):
            mlib.rotate_z(o, rng.uniform(0, 6.2))
            mlib.translate(o, (cx + dx, cy + dy, 0.764))
    print("dining built")
    return M
