"""Everything you sit on.

The hero couch is the reason this module exists.  It is a Victorian
camelback with deep diamond buttoning, carved scroll arms and a bullion
fringe, and none of those three survive being approximated: a box with a
bevel reads as a box with a bevel from any angle the cameras can reach.  So
the tufting is real displaced geometry driven by the button lattice, the
arms are swept along a true volute, and the fringe is individual cords.

Local frame for every upholstered piece: +X along the length, +Y toward the
BACK, so a piece with its back to the north needs no rotation.  Everything
is modelled standing on z = 0 and lifted onto its rug by f_layout.settle.
"""
import bpy, math, importlib
from mathutils import Vector
import mlib as M
import mats as T
import L

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C = "Furniture"
TAU = math.tau
MAT = {}


def mats():
    if MAT:
        return MAT
    # Sampled off main_couch.webp: the hero couch is a GOLDEN ochre velvet,
    # not the red-orange it reads as in a wide shot - the redness in the
    # photographs is the tungsten, and building it into the albedo as well
    # doubles it up and turns the couch to terracotta.
    MAT['velvet'] = T.velvet('velvet_orange', 'BC7328', rough=0.42, pile=1.0)
    MAT['velvet_dk'] = T.velvet('velvet_rust', '8E3A16', rough=0.46, pile=0.8)
    MAT['velvet_red'] = T.velvet('velvet_red', '8E2318', rough=0.44, pile=0.9)
    # Scale is cells per metre, so it is a real measurement off the reference
    # and not a taste setting.  In entrance.webp the settee's damask repeats
    # about every 380 mm along its length and the chairs' black-and-gold
    # about every 140 mm; run at 23 and 34 cells/m - a 40 mm repeat - both
    # collapsed into a two-tone check that reads as gingham from across the
    # room, which is the single most conspicuous wrong note in the set.
    MAT['damask_gold'] = T.damask('damask_gold', ground='96331A',
                                  motif='C08A2E', sheen_c='E6BE6C',
                                  scale=(4.6, 3.55))
    MAT['damask_blk'] = T.damask('damask_black', ground='1A1610',
                                 motif='B58A2E', sheen_c='D8B468',
                                 scale=(11.5, 8.9))
    MAT['tapestry'] = T.tapestry('tapestry_floral')
    MAT['tapestry2'] = T.tapestry('tapestry_floral2', ground='3A2A1E',
                                  a='9E3524', bcol='4A5C3A', c='CFA85E',
                                  scale=8.5)
    # top_view.webp puts the recliner at 79663F - a warm khaki hide, not the
    # grey-olive it was, which with the old grain contrast read as granite
    MAT['leather'] = T.leather('leather_recliner', '7C6A46', rough=0.50)
    MAT["walnut"] = T.wood("wood_walnut", light="8A5C33", dark="47290F",
                           ring=26.0, scale=1.4)
    MAT['oak'] = T.wood('wood_oak', light='A87B47', dark='5A3A1C',
                        ring=30.0, scale=1.1)
    # Not a mirror.  At roughness 0.09 a 25 mm chrome tube is a specular
    # sliver, EEVEE's screen-space trace misses on geometry that thin and
    # falls back to the sky, and the stool legs rendered as flat white
    # plastic.  Real chromed tube in a dim room is a DARK object with one
    # bright line down it, which is what a satin roughness gives you.
    MAT['chrome'] = T.chrome('chrome_stool', rough=0.22, tint='B6BCC0')
    MAT['brass'] = T.metal('brass_trim', 'B8892E', rough=0.26, tarnish=0.5)
    MAT['fringe'] = T.fabric('fringe_bullion', 'A86323', rough=0.80,
                             sheen=0.55, scale=90.0)
    MAT['calico'] = T.fabric('calico_lining', '6B5B45', rough=0.86,
                             sheen=0.15)
    return MAT


# ------------------------------------------------------------------ tufting

def _tuft_field(u, v, buttons, sigma, amp):
    """How far the cover stands proud of the frame at (u, v).

    Distance to the NEAREST button, not a sum over all of them: a sum
    smooths into a quilt of round bumps, whereas real buttoning creases
    along the lines equidistant from two buttons.  Taking the minimum puts
    those creases exactly on the Voronoi boundaries of the button lattice,
    which is what makes the diamonds diamonds and not circles.

    The rise has to stay linear almost all the way out, too.  An exponential
    saturates a third of the way to the boundary, so the surface is already
    flat by the time it gets there and no crease forms at all - the first
    version of this read as a panel with dimples pressed into it.

    Everything here is in METRES, buttons included.  Measured in normalised
    (u, v) the cells came out tall and thin - a 1.87 m back is three times
    wider than it is high, so seven buttons across sit far closer together in
    u than three rows do in v - and every crease landed vertical.  The couch
    read as fluted rather than buttoned until the units were fixed."""
    d = min((u - bu) ** 2 + (v - bv) ** 2 for (bu, bv) in buttons) ** 0.5
    t = min(1.0, d / sigma)
    return amp * t ** 0.62


def button_lattice(nu, nv, u0=0.10, u1=0.90, v0=0.16, v1=0.80):
    """Rows of buttons, alternate rows offset half a pitch - the half-drop is
    what turns a grid of squares into a field of diamonds."""
    out = []
    for j in range(nv):
        v = v0 + (v1 - v0) * (j / max(1, nv - 1))
        n = nu if j % 2 == 0 else nu - 1
        span = (u1 - u0)
        for i in range(n):
            u = u0 + span * ((i + (0.5 if j % 2 else 0.0)) / max(1, nu - 1))
            out.append((u, v))
    return out


def tufted_back(name, ln, h_end, h_mid, y_in, thick, lean=0.09, bow=0.028,
                nbu=7, nbv=3, tuft=0.052, cname=C, nu=97, nv=33,
                seat_z=0.30, border=0.055, chan=0.0):
    """The buttoned inside of a sofa back, as a closed solid.

    (u, v) runs across the width and up the height.  The crest is a broad
    camel, the whole panel leans back and bows out in plan, and the cover is
    pushed in at each button and allowed to puff between them.  The outside
    of the back is a plain shell offset by `thick`, so the two are one
    watertight mesh rather than a surface with solidify guessing at it."""
    buttons = button_lattice(nbu, nbv)
    # The crest is a ROLL, not a lid.  Closing the top ring with one cap face
    # made a 242-sided n-gon 115 mm out of plane - Blender fan-triangulates
    # any n-gon, and that fan, shaded across a curved crest, is what read as
    # a crease running the length of the back.  So the buttoned panel now
    # stops one roll-radius short of the crest line and a run of rings arcs
    # over the top, front face to back face, closing on the ridge.  Same at
    # the bottom, where the cover tucks under the rail.  Nothing is capped;
    # every face in the piece is a quad or a ridge triangle.
    rr = thick * 0.5
    # the panel's real extent, so the button lattice can be measured in metres
    bh = h_mid - rr - seat_z
    bm = [(bu * ln, bv * bh) for (bu, bv) in buttons]
    # sigma: a shade over half the smaller button pitch, so the cones from
    # neighbouring buttons meet and crease instead of flattening out first
    pu = 0.80 * ln / max(1, nbu - 1)
    pv = 0.64 * bh / max(1, nbv - 1) if nbv > 1 else pu
    sigma = min(pu, pv) * 0.68
    rings = []
    lvl_lo = lvl_hi = None
    for j in range(nv):
        v = j / (nv - 1)
        front, back = [], []
        for i in range(nu):
            u = i / (nu - 1)
            x = (u - 0.5) * ln
            crest = h_end + (h_mid - h_end) * math.sin(math.pi * u) ** 0.55
            z = seat_z + v * (crest - rr - seat_z)
            # plan: leans back with height, bows out across the width
            ybase = y_in + lean * v * v + bow * math.sin(math.pi * u)
            # the cover is only buttoned inside a plain border
            eu = min(u, 1 - u) / border if border else 1.0
            ev = min(v / border, (1 - v) / (border * 1.6)) if border else 1.0
            k = max(0.0, min(1.0, min(eu, ev)))
            k = k * k * (3 - 2 * k)                 # smoothstep the border in
            d = _tuft_field(u * ln, v * bh, bm, sigma, tuft) * k
            # Channels.  The hero couch's back is not a plain buttoned panel:
            # main_couch.webp shows a dozen vertical flutes running the whole
            # height with the buttons pinching every OTHER one.
            #
            # The flute MODULATES the tufting, it is not added to it.  Added,
            # a ridge crest landing on a button gives a hard step where one
            # term is pushing out and the other pulling in, and the back
            # came out lumpy rather than channelled.  Physically a channelled
            # back is a row of stuffed tubes and a button sucks its tube
            # flat, so the tuft field - which is already zero at each button
            # and full between them - is exactly the right thing to scale by.
            if chan:
                ph = (u - 0.10) * 2.0 * (nbu - 1) / 0.80
                d *= (1.0 - chan) + 2.0 * chan * (0.5 + 0.5 * math.cos(TAU * ph))
            front.append((x, ybase - d, z))
            # outer shell: plain, and it swells slightly at mid height
            swell = 0.016 * math.sin(math.pi * v)
            back.append((x, ybase + thick + swell, z))
        rings.append(front + back[::-1])
        if j == 0:
            lvl_lo = (front[:], back[:])
        if j == nv - 1:
            lvl_hi = (front[:], back[:])

    def _wrap(level, up, n):
        """Arc the section from its two faces round onto its own centre line.

        At the top the tufting is already damped to nothing by the border, so
        the two faces are exactly `thick` apart there and the arc is a true
        half-round of radius rr.  The last ring closes on the ridge; the weld
        at the end turns that into one edge loop rather than a zero-width
        strip."""
        f0, b0 = level
        out = []
        for k in range(1, n + 1):
            a = (k / n) * (math.pi / 2)
            ca, sa = math.cos(a), math.sin(a)
            fr, bk = [], []
            for i in range(nu):
                yf, yb = f0[i][1], b0[i][1]
                yc, r = 0.5 * (yf + yb), 0.5 * (yb - yf)
                z = f0[i][2] + up * r * sa
                fr.append((f0[i][0], yc - r * ca, z))
                bk.append((b0[i][0], yc + r * ca, z))
            out.append(fr + bk[::-1])
        return out

    # 6 rings is 15 degrees a step, well inside the 46 degree auto-smooth, so
    # the roll shades as a round rather than as facets
    rings = _wrap(lvl_lo, -1, 3)[::-1] + rings + _wrap(lvl_hi, +1, 6)
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=False, cap_end=False)
    M.clean_mesh(ob)
    M.smooth_shade(ob, 46)
    return ob, buttons


def buttons_on(name, buttons, ln, h_end, h_mid, y_in, lean, bow, tuft,
               seat_z=0.30, r=0.021, cname=C, crest_r=0.0):
    """A covered button sunk into each pucker.  Modelled as a shallow dome on
    a shank so it catches a highlight - a flat disc disappears.

    `crest_r` is tufted_back's roll radius and must be the same number: the
    buttons are placed by re-evaluating that surface's own equation, so if
    the panel stops short of the crest and the buttons do not, the top row
    floats off the cover."""
    out = []
    for k, (u, v) in enumerate(buttons):
        x = (u - 0.5) * ln
        crest = h_end + (h_mid - h_end) * math.sin(math.pi * u) ** 0.55
        z = seat_z + v * (crest - crest_r - seat_z)
        y = y_in + lean * v * v + bow * math.sin(math.pi * u)
        b = M.revolve(name + "_%02d" % k,
                      [(0.0, 0.0), (r * 0.55, 0.001), (r, 0.006),
                       (r * 0.92, 0.012), (r * 0.45, 0.016), (0.0, 0.016)],
                      segments=14, cname=cname)
        M.rot_x(b, math.pi / 2)          # face -Y, into the room
        M.translate(b, (x, y + 0.002, z))
        M.smooth_shade(b, 50)
        out.append(b)
    return out


# -------------------------------------------------------------------- arms

def scroll_arm(name, x_in, x_out, y_back, y_front, z0, z_top, roll=0.155,
               cname=C):
    """An English scroll arm, built from its silhouette rather than swept.

    The first version ran a fat tube along a 1.35-turn spiral, on the theory
    that the arm *is* a roll.  It is not: an upholstered arm is a solid, and
    its outline is a plain flank with a big cylindrical bolster at the front.
    The visible spiral is a carved bead applied to the outer cheek, not the
    shape of the thing.  Sweeping it meant the tube passed under itself where
    the spiral closed, which is both wrong to look at and a self-intersection.

    So: one closed section in YZ, lofted across the arm's width with the end
    sections inset, which domes both cheeks and leaves the mesh watertight."""
    cy, cz = y_front + roll, z_top - roll
    sec = [(y_back, z0), (y_back, z_top - 0.055), (cy + roll * 0.62, z_top)]
    sec += M.arc_pts(cy, cz, roll, math.radians(90), math.radians(283),
                     n=18, skip_first=True)
    sec += [(cy + roll * 0.70, z0)]
    sec = M.ccw(sec)
    steps = [(0.000, -0.058), (0.012, -0.032), (0.035, -0.013),
             (0.075, -0.002), (0.925, -0.002), (0.965, -0.013),
             (0.988, -0.032), (1.000, -0.058)]
    rings = []
    for (t, ins) in steps:
        poly = M.poly_offset(sec, ins) if ins else sec
        x = x_in + (x_out - x_in) * t
        rings.append([(x, p[0], p[1]) for p in poly])
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)
    M.smooth_shade(ob, 44)
    return ob, (cy, cz)


def carved_volute(name, cx, cy, cz, r=0.105, depth=0.035, cname=C,
                  turns=1.6, flip=False):
    """The carved wooden scroll on the face of an arm: a tapering spiral
    bead, which is what the set piece actually has - a plain disc reads as a
    bolt head."""
    pts = []
    n = 40
    for i in range(n + 1):
        t = i / n
        a = TAU * turns * t
        rr = r * (1.0 - 0.68 * t)
        pts.append((0.0, rr * math.cos(a), rr * math.sin(a)))
    prof = M.circle(depth * 0.5, 8)
    ob = M.tube_along(name, pts, prof, cname=cname, up=(1, 0, 0), cap=True)
    M.smooth_shade(ob, 40)
    if flip:
        M.scale_mesh(ob, (1, -1, 1))
    M.translate(ob, (cx, cy, cz))
    return ob


# ------------------------------------------------------------------ fringe

def bullion(name, poly, ztop, length=0.115, pitch=0.0072, r=0.0034, cname=C,
            jitter=0.30):
    """Bullion fringe: a twisted cord per 13 mm of hem, each with its own
    slight lean and length.  Hanging a scalloped ribbon there instead looks
    like a pelmet; the couch reads as fringed because the cords separate."""
    walk = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(round(seg / pitch)))
        for j in range(k):
            t = j / k
            walk.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                         math.atan2(b[1] - a[1], b[0] - a[0])))
    rings = []
    cords = []
    for idx, (x, y, ang) in enumerate(walk):
        s = math.sin(idx * 2.399) * 0.5 + math.sin(idx * 0.77) * 0.5
        ln = length * (1.0 + jitter * 0.30 * s)
        # lean outward, away from the hem line
        ox, oy = math.sin(ang), -math.cos(ang)
        sway = 0.016 * jitter * s
        pts = [(x, y, ztop),
               (x + ox * sway * 0.4, y + oy * sway * 0.4, ztop - ln * 0.45),
               (x + ox * sway, y + oy * sway, ztop - ln * 0.88),
               (x + ox * sway * 1.1, y + oy * sway * 1.1, ztop - ln)]
        rad = [r * 0.85, r, r * 0.95, r * 0.55]
        ring = []
        for p, rr in zip(pts, rad):
            ring.append([(p[0] + rr * math.cos(a2), p[1] + rr * math.sin(a2),
                          p[2]) for a2 in
                         [k2 * TAU / 6 for k2 in range(6)]])
        cords.append(M._loft(name + "_c%04d" % idx, ring, close_u=False,
                             close_v=True, cname=cname, cap_start=True,
                             cap_end=True))
    ob = M.join(cords, name, cname)
    M.smooth_shade(ob, 40)
    return ob


# ------------------------------------------------------------- the hero couch

def plump(name, poly, z0, h, welt=0.006, cname=C, seg_scale=1.0):
    """A stuffed cushion with a welt (piping) sewn round its seam.  The welt
    is a ring in the loft rather than a separate torus, so there is no
    interpenetration to clean up afterwards."""
    levels = [(0.00, 0.90, 0.0), (0.12, 1.005, 0.0), (0.46, 1.02, welt),
              (0.54, 1.02, welt), (0.88, 1.005, 0.0), (1.00, 0.88, 0.0)]
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    rings = []
    for (t, s, w) in levels:
        r = []
        for (x, y) in poly:
            vx, vy = x - cx, y - cy
            ll = math.hypot(vx, vy) or 1.0
            r.append((cx + vx * s + vx / ll * w, cy + vy * s + vy / ll * w,
                      z0 + t * h))
        rings.append(r)
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)
    M.smooth_shade(ob, 48)
    return ob


def hero_couch(name="Couch_orange", ln=2.24, dp=0.92, cname=C):
    """The orange couch.  Everything else in the room is dressed around it."""
    m = mats()
    parts_v, parts_w, parts_f = [], [], []
    yb = dp * 0.5              # back face
    yf = -dp * 0.5             # front face
    # Vertical stack, all of it derived from a 450 mm seat: deck top 300,
    # cushion 158 thick.  The first pass put the deck at 375 and the seat
    # ended up at 525 - a bar stool, not a couch.
    seat_z = 0.300             # top of the deck, under the cushion
    arm_top = 0.615
    aw = 0.205                 # arm width
    inner = ln - 2 * aw

    # -- frame: a carved rail round the front and sides, on turned feet -----
    rail = [(-ln / 2, yf), (ln / 2, yf), (ln / 2, yb), (-ln / 2, yb)]
    fr = M.prism(name + "_rail", rail, 0.130, 0.242, cname)
    M.bevel(fr, 0.012, 2, 55)
    parts_w.append(fr)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ft = M.revolve(name + "_ft%d%d" % (sx, sy),
                           [(0.0, 0.0), (0.030, 0.004), (0.034, 0.020),
                            (0.026, 0.052), (0.036, 0.086), (0.030, 0.120),
                            (0.042, 0.140), (0.0, 0.140)], segments=16,
                           cname=cname)
            M.smooth_shade(ft, 40)
            M.translate(ft, (sx * (ln / 2 - 0.085), sy * (dp / 2 - 0.085), 0.0))
            parts_w.append(ft)

    # -- deck the cushion sits on ------------------------------------------
    dk = M.box(name + "_deck", -inner / 2 - 0.015, yf + 0.055, 0.238,
               inner / 2 + 0.015, yb - 0.055, seat_z, cname)
    M.bevel(dk, 0.010, 2, 50)
    parts_v.append(dk)
    # The upholstered front apron.  It used to run up to 0.330 and showed as a
    # flat band below the cushion; on the set the fringe starts immediately
    # under the seat, so the apron only has to cover the rail.
    ap = M.prism(name + "_apron",
                 [(-ln / 2 + 0.012, yf + 0.012), (ln / 2 - 0.012, yf + 0.012),
                  (ln / 2 - 0.012, yb - 0.012), (-ln / 2 + 0.012, yb - 0.012)],
                 0.232, 0.302, cname)
    M.bevel(ap, 0.016, 2, 55)
    parts_v.append(ap)

    # -- the buttoned back --------------------------------------------------
    lean, bow, tuft = 0.112, 0.030, 0.098
    y_in = yb - 0.225
    back, buttons = tufted_back(name + "_back", inner + 0.04, 0.845, 0.960,
                                y_in, 0.160, lean=lean, bow=bow, nbu=7, nbv=3,
                                tuft=tuft, cname=cname, seat_z=0.300,
                                chan=0.17, nu=121, nv=41)
    parts_v.append(back)
    parts_v += buttons_on(name + "_btn", buttons, inner + 0.04, 0.845, 0.960,
                          y_in, lean, bow, tuft, seat_z=0.300, r=0.026,
                          cname=cname, crest_r=0.160 * 0.5)

    # -- arms ---------------------------------------------------------------
    for s in (-1, 1):
        a, (rcy, rcz) = scroll_arm(name + "_arm%d" % s,
                                   s * (inner / 2 - 0.004), s * (ln / 2),
                                   yb - 0.050, yf + 0.048, 0.240,
                                   arm_top + 0.042, roll=0.166, cname=cname)
        parts_v.append(a)
        # the carved scroll applied to the outer cheek of the bolster
        cv = carved_volute(name + "_vol%d" % s, s * (ln / 2 + 0.006),
                           rcy, rcz, r=0.108, depth=0.042, cname=cname,
                           flip=(s < 0))
        parts_w.append(cv)

    # -- the seat: one long bench cushion, piped ---------------------------
    cu = plump(name + "_seat",
               M.rounded_rect(inner + 0.012, dp - 0.205, 0.060, seg=6),
               seat_z - 0.008, 0.158, welt=0.012, cname=cname)
    M.translate(cu, (0.0, -0.030, 0.0))
    parts_v.append(cu)

    # -- bullion fringe round the hem --------------------------------------
    hem = [(-ln / 2 + 0.006, yf + 0.006), (ln / 2 - 0.006, yf + 0.006),
           (ln / 2 - 0.006, yb - 0.006), (-ln / 2 + 0.006, yb - 0.006)]
    fg = bullion(name + "_fringe", hem, 0.248, length=0.178, cname=cname)
    parts_f.append(fg)

    ov = M.join(parts_v, name + "_uphol", cname); M.set_mat(ov, m['velvet'])
    ow = M.join(parts_w, name + "_frame", cname); M.set_mat(ow, m['walnut'])
    of = M.join(parts_f, name + "_hem", cname); M.set_mat(of, m['fringe'])
    return [ov, ow, of]


# ---------------------------------------------------------------- settees

def settee(name, ln=1.62, dp=0.78, cname=C, cover='damask_gold',
           frame='walnut', seat_h=0.415, back_h=0.925, nbu=5, nbv=2,
           fringe=False, cushions=2):
    """The smaller sofas: the gold damask one under the bay window and the
    rust one in the north alcove.  Same construction as the hero couch at a
    lighter scale, with a shallower roll to the arms."""
    m = mats()
    pv, pw, pf = [], [], []
    yb, yf = dp / 2, -dp / 2
    aw = 0.165
    inner = ln - 2 * aw
    seat_z = seat_h - 0.115

    rail = [(-ln / 2, yf), (ln / 2, yf), (ln / 2, yb), (-ln / 2, yb)]
    fr = M.prism(name + "_rail", rail, 0.115, 0.225, cname)
    M.bevel(fr, 0.010, 2, 55); pw.append(fr)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ft = M.revolve(name + "_ft%d%d" % (sx, sy),
                           [(0.0, 0.0), (0.026, 0.004), (0.030, 0.018),
                            (0.022, 0.048), (0.032, 0.076), (0.038, 0.115),
                            (0.0, 0.115)], segments=14, cname=cname)
            M.smooth_shade(ft, 40)
            M.translate(ft, (sx * (ln / 2 - 0.075), sy * (dp / 2 - 0.075), 0.0))
            pw.append(ft)

    dk = M.box(name + "_deck", -inner / 2 - 0.012, yf + 0.05, 0.220,
               inner / 2 + 0.012, yb - 0.065, seat_z, cname)
    M.bevel(dk, 0.010, 2, 50); pv.append(dk)
    ap = M.prism(name + "_apron",
                 [(-ln / 2 + 0.010, yf + 0.010), (ln / 2 - 0.010, yf + 0.010),
                  (ln / 2 - 0.010, yb - 0.010), (-ln / 2 + 0.010, yb - 0.010)],
                 0.215, 0.290, cname)
    M.bevel(ap, 0.016, 2, 55); pv.append(ap)

    lean, bow, tuft = 0.075, 0.022, 0.040
    y_in = yb - 0.185
    back, buttons = tufted_back(name + "_back", inner + 0.03, back_h - 0.055,
                                back_h, y_in, 0.130, lean=lean, bow=bow,
                                nbu=nbu, nbv=nbv, tuft=tuft, cname=cname,
                                seat_z=seat_z - 0.045, nu=57, nv=25)
    pv.append(back)
    pv += buttons_on(name + "_btn", buttons, inner + 0.03, back_h - 0.055,
                     back_h, y_in, lean, bow, tuft, seat_z=seat_z - 0.045,
                     r=0.014, cname=cname, crest_r=0.130 * 0.5)

    for s in (-1, 1):
        a, _ = scroll_arm(name + "_arm%d" % s, s * (inner / 2 - 0.004),
                          s * (ln / 2), yb - 0.045, yf + 0.042, 0.220,
                          seat_h + 0.170, roll=0.128, cname=cname)
        pv.append(a)

    pitch = (inner - 0.010) / cushions
    for i in range(cushions):
        cu = plump(name + "_seat%d" % i,
                   M.rounded_rect(pitch - 0.022, dp - 0.205, 0.05, seg=5),
                   seat_z - 0.005, 0.130, welt=0.006, cname=cname)
        M.translate(cu, (-inner / 2 + (i + 0.5) * pitch, -0.022, 0.0))
        pv.append(cu)

    out = []
    ov = M.join(pv, name + "_uphol", cname); M.set_mat(ov, m[cover])
    ow = M.join(pw, name + "_frame", cname); M.set_mat(ow, m[frame])
    out += [ov, ow]
    if fringe:
        hem = [(-ln / 2 + 0.005, yf + 0.005), (ln / 2 - 0.005, yf + 0.005),
               (ln / 2 - 0.005, yb - 0.005), (-ln / 2 + 0.005, yb - 0.005)]
        fg = bullion(name + "_fringe", hem, 0.128, length=0.100, cname=cname)
        M.set_mat(fg, m['fringe'])
        out.append(fg)
    return out


def club_chair(name, w=0.82, dp=0.86, h=0.90, cname=C, cover='velvet_dk',
               frame='walnut'):
    """The two red armchairs in the north alcove: low, square, deep-seated,
    with a plain rolled back rather than a buttoned one."""
    m = mats()
    pv, pw = [], []
    yb, yf = dp / 2, -dp / 2
    aw = 0.155
    seat_z = 0.300
    # body: a lofted tub so the back and arms are one continuous shell
    rings = []
    for (t, dz, inset) in ((0.00, 0.000, 0.000), (0.55, 0.170, -0.012),
                           (1.00, 0.230, -0.020)):
        poly = M.rounded_rect(w + inset * -1, dp + inset * -1, 0.075, seg=5)
        rings.append([(x, y, 0.150 + dz) for (x, y) in poly])
    tub = M._loft(name + "_tub", rings, close_u=False, close_v=True,
                  cname=cname, cap_start=True, cap_end=True)
    M.smooth_shade(tub, 44); pv.append(tub)
    # the back, rising behind the tub
    bk = M.prism(name + "_back",
                 M.rounded_rect(w - 0.010, 0.215, 0.070, seg=5),
                 0.320, h, cname)
    M.bevel(bk, 0.045, 3, 55); M.smooth_shade(bk, 44)
    M.translate(bk, (0.0, yb - 0.115, 0.0)); pv.append(bk)
    # arms
    for s in (-1, 1):
        ar = M.prism(name + "_arm%d" % s,
                     M.rounded_rect(aw, dp - 0.09, 0.055, seg=5),
                     0.360, 0.585, cname)
        M.bevel(ar, 0.045, 3, 55); M.smooth_shade(ar, 44)
        M.translate(ar, (s * (w - aw) / 2, -0.015, 0.0))
        pv.append(ar)
    cu = plump(name + "_seat",
               M.rounded_rect(w - 2 * aw + 0.02, dp - 0.245, 0.05, seg=5),
               0.375, 0.135, welt=0.006, cname=cname)
    M.translate(cu, (0.0, -0.045, 0.0)); pv.append(cu)
    bc = plump(name + "_backc",
               M.rounded_rect(w - 2 * aw + 0.01, 0.155, 0.05, seg=5),
               0.480, 0.330, welt=0.005, cname=cname)
    M.rot_x(bc, math.radians(-7))
    M.translate(bc, (0.0, yb - 0.255, 0.0)); pv.append(bc)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ft = M.revolve(name + "_ft%d%d" % (sx, sy),
                           [(0.0, 0.0), (0.028, 0.006), (0.024, 0.060),
                            (0.036, 0.100), (0.040, 0.150), (0.0, 0.150)],
                           segments=14, cname=cname)
            M.smooth_shade(ft, 40)
            M.translate(ft, (sx * (w / 2 - 0.075), sy * (dp / 2 - 0.075), 0.0))
            pw.append(ft)
    ov = M.join(pv, name + "_uphol", cname); M.set_mat(ov, m[cover])
    ow = M.join(pw, name + "_frame", cname); M.set_mat(ow, m[frame])
    return [ov, ow]


def recliner(name, w=0.94, dp=1.02, h=0.98, cname=C):
    """The taupe channel-tufted recliner beside the couch.  Its whole
    character is the vertical channels, so those are lofted ribs rather than
    a bump map - at 1.5 m from the camera a bump reads as dirt."""
    m = mats()
    pv, pw = [], []
    yb, yf = dp / 2, -dp / 2
    aw = 0.185
    nch = 5
    inner = w - 2 * aw

    # The back.  Channelled means bolsters, not grooves: each channel is a
    # tube of stuffing that stands proud and pinches to nothing at the seam
    # between it and its neighbour.  The first attempt subtracted a cosine
    # from a flat slab, which gives a fluted panel - the chair read as a
    # filing cabinet.  Here the channel depth is added OUTWARD from a curved
    # core, the whole back leans and curls forward at the head, and the ends
    # of the run are rounded off so it is not a rectangle in plan either.
    rings = []
    nu, nv = 16 * nch + 1, 26
    for j in range(nv):
        v = j / (nv - 1)
        front, back = [], []
        for i in range(nu):
            u = i / (nu - 1)
            # round the ends of the back in plan
            endk = min(1.0, min(u, 1 - u) / 0.06)
            endk = endk * endk * (3 - 2 * endk)
            x = (u - 0.5) * inner
            ph = (u * nch - 0.5) * TAU
            ch = 0.052 * (0.5 - 0.5 * math.cos(ph)) ** 0.75
            # lean back, then curl the head forward again
            lean = 0.115 * v * v - 0.145 * max(0.0, (v - 0.68) / 0.32) ** 2
            z = 0.400 + v * (h - 0.400)
            y = yb - 0.235 + lean
            taper = math.sin(math.pi * min(1.0, 0.06 + v * 1.02)) ** 0.35
            front.append((x, y - (ch * taper + 0.022) * endk, z))
            back.append((x, y + 0.115 + 0.020 * math.sin(math.pi * v), z))
        rings.append(front + back[::-1])
    bk = M._loft(name + "_back", rings, close_u=False, close_v=True,
                 cname=cname, cap_start=True, cap_end=True)
    M.smooth_shade(bk, 46); pv.append(bk)

    # deck, and a channelled seat cushion running front-to-back
    dk = M.box(name + "_deck", -inner / 2 - 0.012, yf + 0.06, 0.190,
               inner / 2 + 0.012, yb - 0.11, 0.395, cname)
    M.bevel(dk, 0.012, 2, 50); pv.append(dk)
    srings = []
    nsv = 18
    for j in range(nsv):
        v = j / (nsv - 1)
        top, bot = [], []
        for i in range(nu):
            u = i / (nu - 1)
            endk = min(1.0, min(u, 1 - u) / 0.05)
            endk = endk * endk * (3 - 2 * endk)
            x = (u - 0.5) * (inner + 0.02)
            ph = (u * nch - 0.5) * TAU
            ch = 0.040 * (0.5 - 0.5 * math.cos(ph)) ** 0.75
            y = yf + 0.070 + v * (dp - 0.255)
            # the cushion rolls over at the front and tucks at the back
            dome = math.sin(math.pi * min(1.0, max(0.0, 0.10 + v * 0.86))) ** 0.45
            top.append((x, y, 0.392 + (0.052 + ch) * dome * endk))
            bot.append((x, y, 0.386 - 0.010 * dome * endk))
        srings.append(top + bot[::-1])
    st = M._loft(name + "_seat", srings, close_u=False, close_v=True,
                 cname=cname, cap_start=True, cap_end=True)
    M.smooth_shade(st, 46); pv.append(st)

    # Arms: fat rolled bolsters standing from the deck to elbow height.  The
    # first section only ran z 0.23 to 0.33 - a 100 mm bar lying on its side,
    # which rendered as a flat sheet sticking out of the chair.
    az0, az1, ar_r = 0.190, 0.628, 0.108
    for s in (-1, 1):
        sec = [(yb - 0.055, az0), (yb - 0.055, az1 - ar_r)]
        sec += M.arc_pts(yb - 0.055 - ar_r, az1 - ar_r, ar_r, 0.0,
                         math.radians(90), n=7, skip_first=True)
        sec += M.arc_pts(yf + 0.055 + ar_r, az1 - ar_r, ar_r,
                         math.radians(90), math.radians(180), n=7,
                         skip_first=True)
        sec += [(yf + 0.055, az0)]
        sec = M.ccw(sec)
        steps = [(0.0, -0.062), (0.02, -0.030), (0.06, -0.008),
                 (0.94, -0.008), (0.98, -0.030), (1.0, -0.062)]
        arings = []
        x0 = s * (inner / 2 + 0.002)
        x1 = s * (w / 2)
        for (t, ins) in steps:
            poly = M.poly_offset(sec, ins) if ins else sec
            xx = x0 + (x1 - x0) * t
            arings.append([(xx, p[0], p[1]) for p in poly])
        ar = M._loft(name + "_arm%d" % s, arings, close_u=False, close_v=True,
                     cname=cname, cap_start=True, cap_end=True)
        M.smooth_shade(ar, 46); pv.append(ar)

    # plinth base, in shadow under the whole thing
    pl = M.prism(name + "_plinth",
                 M.rounded_rect(w - 0.13, dp - 0.20, 0.045, seg=4),
                 0.0, 0.195, cname)
    M.bevel(pl, 0.014, 2, 50); pw.append(pl)
    ov = M.join(pv, name + "_uphol", cname); M.set_mat(ov, m['leather'])
    ow = M.join(pw, name + "_base", cname); M.set_mat(ow, m['walnut'])
    return [ov, ow]


# ------------------------------------------------------------- side chairs

def bistro_chair(name, cname=C, w=0.455, dp=0.475, seat=0.455, back=0.925,
                 cover='damask_blk'):
    """The black-and-gold damask side chairs.  A turned-leg frame with a
    shaped crest rail and a drop-in upholstered seat - the shape the set has
    round the little pedestal tables."""
    m = mats()
    pw, pv = [], []
    hw, hd = w / 2, dp / 2
    # back legs continue up into the stiles, so they are one swept member
    for s in (-1, 1):
        path = [(s * (hw - 0.030), hd - 0.030, 0.0),
                (s * (hw - 0.030), hd - 0.032, seat),
                (s * (hw - 0.042), hd - 0.050, back - 0.075),
                (s * (hw - 0.048), hd - 0.062, back)]
        st = M.tube_along(name + "_stile%d" % s, path,
                          M.rounded_rect(0.034, 0.034, 0.012, seg=3),
                          cname=cname, up=(0, 1, 0), cap=True)
        pw.append(st)
        fl = M.revolve(name + "_fleg%d" % s,
                       [(0.0, 0.0), (0.024, 0.004), (0.020, 0.030),
                        (0.026, 0.070), (0.017, 0.130), (0.023, 0.190),
                        (0.016, 0.300), (0.022, 0.360), (0.018, seat - 0.055),
                        (0.024, seat), (0.0, seat)], segments=14, cname=cname)
        M.smooth_shade(fl, 40)
        M.translate(fl, (s * (hw - 0.030), -(hd - 0.030), 0.0))
        pw.append(fl)
    # seat rails
    for (a, bp) in (((-hw, -hd), (hw, -hd)), ((-hw, hd), (hw, hd)),
                    ((-hw, -hd), (-hw, hd)), ((hw, -hd), (hw, hd))):
        r = M.tube_along(name + "_rail%d%d" % (int(a[0] * 100), int(a[1] * 100)),
                         [(a[0], a[1], seat - 0.048), (bp[0], bp[1], seat - 0.048)],
                         M.rounded_rect(0.030, 0.052, 0.008, seg=2),
                         cname=cname, up=(0, 0, 1), cap=True)
        pw.append(r)
    # a stretcher near the floor, as the set chairs have
    for yy in (-hd + 0.035, hd - 0.035):
        s2 = M.tube_along(name + "_str%d" % int(yy * 100),
                          [(-hw + 0.030, yy, 0.115), (hw - 0.030, yy, 0.115)],
                          M.circle(0.011, 8), cname=cname, up=(0, 0, 1))
        pw.append(s2)
    # crest rail: a shaped board spanning the stiles, plus a mid splat
    crest = M.prism_xz(name + "_crest",
                       [(-hw + 0.020, back - 0.115), (hw - 0.020, back - 0.115),
                        (hw - 0.020, back - 0.020), (0.0, back + 0.012),
                        (-hw + 0.020, back - 0.020)],
                       hd - 0.078, hd - 0.040, cname)
    M.bevel(crest, 0.006, 2, 50); pw.append(crest)
    # a bottom rail closing the back frame, low down where the pad ends
    splat = M.prism_xz(name + "_splat",
                       [(-hw + 0.030, seat + 0.052), (hw - 0.030, seat + 0.052),
                        (hw - 0.030, seat + 0.092), (-hw + 0.030, seat + 0.092)],
                       hd - 0.076, hd - 0.046, cname)
    M.bevel(splat, 0.005, 2, 50); pw.append(splat)
    # drop-in seat and a padded back panel
    sq = plump(name + "_pad", M.rounded_rect(w - 0.045, dp - 0.050, 0.030, seg=5),
               seat - 0.050, 0.078, welt=0.005, cname=cname)
    pv.append(sq)
    # The back pad reaches DOWN to the lumbar, not just across the shoulders.
    # Started at seat + 0.250 it sat as a band across the top of the frame
    # with the small of your back over open air - which is not a chair anyone
    # would put in a coffee house, and not what the set's are.  It now runs
    # from just above the seat rail to just under the crest.
    b0, b1 = seat + 0.098, back - 0.122
    bp2 = plump(name + "_backpad",
                M.rounded_rect(w - 0.072, 0.072, 0.022, seg=4),
                b0, 0.075, welt=0.004, cname=cname)
    M.rot_x(bp2, math.radians(4))
    M.scale_mesh(bp2, (1, 1, (b1 - b0) / 0.075), pivot=(0, 0, b0))
    M.translate(bp2, (0.0, hd - 0.058, 0.0))
    pv.append(bp2)
    ow = M.join(pw, name + "_frame", cname); M.set_mat(ow, m['walnut'])
    ov = M.join(pv, name + "_pad", cname); M.set_mat(ov, m[cover])
    return [ow, ov]


def bar_stool(name, cname=C, h=0.735, r=0.185):
    """Chrome-legged tapestry bar stool: four splayed tubes, a footring, and
    a round sprung seat."""
    m = mats()
    pm, pv = [], []
    for i in range(4):
        a = math.radians(45 + i * 90)
        x0, y0 = 0.055 * math.cos(a), 0.055 * math.sin(a)
        x1, y1 = 0.215 * math.cos(a), 0.215 * math.sin(a)
        lg = M.tube_along(name + "_lg%d" % i,
                          [(x0, y0, h - 0.075), (x0 * 1.4, y0 * 1.4, h - 0.30),
                           (x1, y1, 0.020), (x1 * 1.02, y1 * 1.02, 0.0)],
                          M.circle(0.0125, 10), cname=cname, up=(0, 0, 1),
                          cap=True)
        M.smooth_shade(lg, 40); pm.append(lg)
    ring = M.tube_along(name + "_ring",
                        [(0.150 * math.cos(t * TAU / 24),
                          0.150 * math.sin(t * TAU / 24), 0.215)
                         for t in range(24)],
                        M.circle(0.0095, 8), cname=cname, close_path=True,
                        up=(0, 0, 1))
    M.smooth_shade(ring, 40); pm.append(ring)
    plate = M.revolve(name + "_plate",
                      [(0.0, h - 0.085), (0.075, h - 0.085), (0.078, h - 0.072),
                       (0.0, h - 0.072)], segments=20, cname=cname)
    M.smooth_shade(plate, 40); pm.append(plate)
    seat = M.revolve(name + "_seat",
                     [(0.0, h - 0.072), (r * 0.92, h - 0.070),
                      (r, h - 0.048), (r * 0.995, h - 0.020),
                      (r * 0.86, h + 0.004), (r * 0.45, h + 0.016),
                      (0.0, h + 0.018)], segments=32, cname=cname)
    M.smooth_shade(seat, 46); pv.append(seat)
    om = M.join(pm, name + "_frame", cname); M.set_mat(om, m['chrome'])
    ov = M.join(pv, name + "_seat", cname); M.set_mat(ov, m['damask_blk'])
    return [om, ov]


def wood_stool(name, cname=C, h=0.700, r=0.175):
    """The taller wooden stools around the middle tables: splayed turned legs
    with two stretcher rings and a padded tapestry top."""
    m = mats()
    pw, pv = [], []
    for i in range(4):
        a = math.radians(45 + i * 90)
        x0, y0 = 0.085 * math.cos(a), 0.085 * math.sin(a)
        x1, y1 = 0.205 * math.cos(a), 0.205 * math.sin(a)
        lg = M.tube_along(name + "_lg%d" % i,
                          [(x0, y0, h - 0.055), (x0 * 1.3, y0 * 1.3, h - 0.22),
                           (x1 * 0.94, y1 * 0.94, 0.13), (x1, y1, 0.0)],
                          M.rounded_rect(0.030, 0.030, 0.011, seg=3),
                          cname=cname, up=(0, 0, 1), cap=True)
        pw.append(lg)
    for (zz, rr) in ((0.235, 0.168), (0.150, 0.185)):
        for i in range(4):
            a0 = math.radians(45 + i * 90)
            a1 = math.radians(135 + i * 90)
            st = M.tube_along(name + "_st%d%d" % (int(zz * 100), i),
                              [(rr * math.cos(a0), rr * math.sin(a0), zz),
                               (rr * math.cos(a1), rr * math.sin(a1), zz)],
                              M.circle(0.010, 7), cname=cname, up=(0, 0, 1))
            pw.append(st)
        break
    frame = M.revolve(name + "_apron",
                      [(0.0, h - 0.060), (r * 0.96, h - 0.060),
                       (r * 0.99, h - 0.030), (0.0, h - 0.030)],
                      segments=24, cname=cname)
    M.smooth_shade(frame, 40); pw.append(frame)
    top = M.revolve(name + "_top",
                    [(0.0, h - 0.032), (r * 0.99, h - 0.030),
                     (r * 1.01, h - 0.004), (r * 0.94, h + 0.020),
                     (r * 0.5, h + 0.032), (0.0, h + 0.034)],
                    segments=28, cname=cname)
    M.smooth_shade(top, 46); pv.append(top)
    ow = M.join(pw, name + "_frame", cname); M.set_mat(ow, m['oak'])
    ov = M.join(pv, name + "_top", cname); M.set_mat(ov, m['tapestry2'])
    return [ow, ov]


def pouf(name, cname=C, r=0.33, h=0.42):
    """Round buttoned pouf in the north alcove."""
    m = mats()
    body = M.revolve(name + "_b",
                     [(0.0, 0.055), (r * 0.86, 0.050), (r, 0.14),
                      (r * 0.99, h - 0.08), (r * 0.72, h - 0.010),
                      (r * 0.30, h + 0.012), (0.0, h + 0.016)],
                     segments=32, cname=cname)
    M.smooth_shade(body, 46)
    parts = [body]
    for i in range(6):
        a = i * TAU / 6
        b = M.revolve(name + "_bt%d" % i,
                      [(0.0, 0.0), (0.013, 0.004), (0.011, 0.010), (0.0, 0.011)],
                      segments=10, cname=cname)
        M.translate(b, (r * 0.52 * math.cos(a), r * 0.52 * math.sin(a),
                        h + 0.002))
        parts.append(b)
    fe = []
    for i in range(4):
        a = math.radians(45 + i * 90)
        f = M.revolve(name + "_ft%d" % i,
                      [(0.0, 0.0), (0.028, 0.004), (0.022, 0.038),
                       (0.030, 0.058), (0.0, 0.058)], segments=12, cname=cname)
        M.translate(f, (r * 0.72 * math.cos(a), r * 0.72 * math.sin(a), 0.0))
        fe.append(f)
    ov = M.join(parts, name, cname); M.set_mat(ov, m['damask_gold'])
    ow = M.join(fe, name + "_ft", cname); M.set_mat(ow, m['walnut'])
    return [ov, ow]
