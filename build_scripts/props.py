"""Reusable dressing: crockery, jars, bottles, plants, framed art, drapes,
lampshades, books.  All lathed / lofted geometry, all procedural materials."""
import bpy, math, random, colorsys
from mathutils import Matrix, Vector
import mlib, mats


# --------------------------------------------------------------- material pool
_POOL = {}


def col_mat(key, hexcol, rough=0.28, coat=0.4, metal=0.0):
    k = "prop_" + key
    m = mats.get(k)
    if m is None:
        if metal:
            m = mats.metal(k, hexcol, rough=rough)
        else:
            m = mats.paint(k, hexcol, rough=rough, coat=coat, variation=0.02)
    return m


def palette(seed=0, n=26):
    """A believable jumble of kitchen-jar colours."""
    rng = random.Random(seed)
    hexes = ['E4DFD2', 'D9CBB0', 'C8452F', 'D97B2B', 'E8B93C', '6E9E4C',
             '2E7D9A', '3E4C8A', '8C4A7A', '9B2F30', '4C4A46', 'F0EDE6',
             'BFC9CC', 'A8763E', '6B3F2A', 'D8A0A8', '7FB2A5', 'EAD6A0',
             '2F5C3A', '8E9AA8', 'C6D2B0', 'E2C9E0', '3A3A44', 'B8543A',
             '5E7BA8', 'DAB86A']
    out = []
    for i in range(n):
        out.append(col_mat("c%d" % i, hexes[i % len(hexes)],
                           rough=rng.uniform(0.12, 0.55), coat=rng.uniform(0.1, 0.6)))
    return out


# ------------------------------------------------------------------- crockery
def jar(name, r=0.045, h=0.13, neck=0.62, lid=True, cname="Details", mat=None,
        lidmat=None):
    p = [(0.0, 0.0), (r * 0.92, 0.004), (r, 0.022), (r, h * 0.72),
         (r * neck, h * 0.86), (r * neck, h)]
    ob = mlib.revolve(name, p, 22, cname=cname)
    mlib.smooth_shade(ob, 34)
    if mat:
        mlib.set_mat(ob, mat)
    out = [ob]
    if lid:
        lp = [(0.0, 0.0), (r * neck + 0.004, 0.0), (r * neck + 0.004, 0.016),
              (r * neck * 0.7, 0.020), (0.0, 0.020)]
        lo = mlib.revolve(name + "_lid", lp, 22, cname=cname)
        mlib.translate(lo, (0, 0, h))
        mlib.smooth_shade(lo, 40)
        if lidmat:
            mlib.set_mat(lo, lidmat)
        out.append(lo)
    return out


def can(name, r=0.038, h=0.11, cname="Details", mat=None):
    p = [(0.0, 0.0), (r, 0.006), (r, h - 0.006), (r * 0.96, h), (0.0, h)]
    ob = mlib.revolve(name, p, 20, cname=cname)
    mlib.smooth_shade(ob, 38)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


def bottle(name, r=0.036, h=0.28, cname="Details", mat=None):
    p = [(0.0, 0.0), (r * 0.9, 0.004), (r, 0.02), (r, h * 0.52),
         (r * 0.72, h * 0.62), (r * 0.30, h * 0.72), (r * 0.26, h * 0.94),
         (r * 0.30, h), (0.0, h)]
    ob = mlib.revolve(name, p, 22, cname=cname)
    mlib.smooth_shade(ob, 40)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


def cup(name, r=0.042, h=0.085, cname="Details", mat=None, handle=True):
    p = [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.70, 0.008), (r * 0.86, h * 0.4),
         (r, h), (r - 0.004, h), (r * 0.82, h * 0.4), (r * 0.6, 0.010),
         (0.0, 0.010)]
    ob = mlib.revolve(name, p, 20, cname=cname)
    mlib.smooth_shade(ob, 36)
    parts = [ob]
    if handle:
        path = []
        for i in range(9):
            t = i / 8.0
            a = math.pi * (t - 0.5)
            path.append((r * 0.92 + 0.030 * math.cos(a), 0.0,
                         h * 0.62 + 0.030 * math.sin(a) * 1.3))
        hd = mlib.tube_along(name + "_h", path, mlib.circle(0.0055, 8), cname)
        parts.append(hd)
    ob = mlib.join(parts, name, cname)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


def bowl(name, r=0.10, h=0.055, cname="Details", mat=None):
    p = [(0.0, 0.0), (r * 0.42, 0.0), (r * 0.5, 0.006), (r * 0.78, h * 0.5),
         (r, h), (r - 0.004, h), (r * 0.74, h * 0.5), (r * 0.44, 0.008),
         (0.0, 0.008)]
    ob = mlib.revolve(name, p, 26, cname=cname)
    mlib.smooth_shade(ob, 34)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


def plate_stack(name, r=0.105, n=4, cname="Details", mat=None):
    parts = []
    for i in range(n):
        p = [(0.0, 0.0), (r * 0.5, 0.0), (r * 0.72, 0.004), (r, 0.014),
             (r - 0.003, 0.016), (r * 0.68, 0.009), (r * 0.46, 0.005), (0.0, 0.005)]
        o = mlib.revolve(name + "_%d" % i, p, 24, cname=cname)
        mlib.translate(o, (0, 0, i * 0.016))
        parts.append(o)
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 34)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


def stemware(name, r=0.035, h=0.155, cname="Details", mat=None):
    """A wine glass.  The shelf reads as tins and tumblers without one of these
    in it - a stem is the one silhouette on a kitchen shelf you cannot mistake
    for anything else, and the set's has a whole row."""
    bowl_z = h * 0.42
    p = [(0.0, 0.0), (r * 0.86, 0.0), (r * 0.90, 0.004), (r * 0.34, 0.010),
         (0.0175 * r / 0.035, 0.020), (0.0165 * r / 0.035, bowl_z * 0.86),
         (r * 0.42, bowl_z), (r * 0.86, bowl_z + (h - bowl_z) * 0.36),
         (r, bowl_z + (h - bowl_z) * 0.74), (r * 0.94, h),
         (r * 0.94 - 0.0012, h), (r * 0.86, bowl_z + (h - bowl_z) * 0.74),
         (r * 0.30, bowl_z + 0.004), (0.0, bowl_z + 0.006)]
    ob = mlib.revolve(name, p, 24, cname=cname)
    mlib.smooth_shade(ob, 44)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


def carton(name, w=0.075, d=0.05, h=0.16, cname="Details", mat=None,
           band=None, cname2=None):
    """Grocery box.  A printed carton is never one flat colour: the set's
    shelves carry cereal boxes with a broad band across the middle, and that
    band is most of what stops them reading as painted blocks."""
    ob = mlib.box(name, -w / 2, -d / 2, 0, w / 2, d / 2, h, cname)
    mlib.bevel(ob, 0.003, 2, 45)
    if mat:
        mlib.set_mat(ob, mat)
    out = [ob]
    if band is not None:
        z0 = h * random.Random(int(w * 9973)).uniform(0.30, 0.52)
        lb = mlib.box(name + "_bd", -w / 2 - 0.0008, -d / 2 - 0.0008, z0,
                      w / 2 + 0.0008, d / 2 + 0.0008, z0 + h * 0.26, cname)
        mlib.bevel(lb, 0.0022, 2, 45)
        mlib.set_mat(lb, band)
        out.append(lb)
    return out


def book(name, w=0.16, t=0.032, h=0.225, cname="Details", mat=None):
    ob = mlib.box(name, -w / 2, -t / 2, 0, w / 2, t / 2, h, cname)
    mlib.bevel(ob, 0.0025, 2, 45)
    if mat:
        mlib.set_mat(ob, mat)
    return [ob]


# Weighted towards crockery.  Cartons and books are the two shapes that read
# worst at shelf scale - a flat coloured rectangle stays a flat coloured
# rectangle - while the set's shelves are mostly jars, tins, stacked plates and
# rows of glasses.
ITEMS = [
    ('jar', 0.18), ('can', 0.14), ('bottle', 0.12), ('cup', 0.12),
    ('bowl', 0.10), ('plates', 0.14), ('carton', 0.08), ('book', 0.03),
    ('stem', 0.09),
]


def fill_shelf(name, p0, p1, z, depth, seed=0, cname="Details", maxh=0.20,
               density=1.0, mats_pool=None, back=0.55, fill=1.0, skip=()):
    """Scatter believable crockery along a shelf running p0->p1 at height z.

    `fill` is how much of the run gets used, 0..1.  Nobody loads a shelf evenly:
    on the set the two top tiers are mostly bare brick with a couple of things
    pushed to one end, and the two below them are jammed.  An even scatter at
    one density everywhere is what makes procedural shelves read as wallpaper.

    Items come in clusters with real gaps between them, rather than a constant
    trickle, for the same reason.

    `skip` is a list of (u0, u1) stretches of the run that are already spoken
    for - a coffee maker, a mixer, a dish rack - which the scatter steps over.
    Without it the counter runs were being filled straight through the standing
    appliances: a bowl was sharing its space with the blender, a jar with the
    toaster.  Passing nothing leaves the random walk byte-identical, so every
    shelf that has no appliances on it is untouched."""
    rng = random.Random(seed)
    pool = mats_pool or palette(seed)
    # a quarter of the vessels are glass: a shelf of nothing but opaque colour
    # reads as a row of painted blocks, and the set's is full of glass
    gl = [mats.get('glass_thick') or mats.pane('glass_thick', tint='E8EEEA',
                                               base_alpha=0.16, edge=0.72),
          mats.get('glass_clear') or mats.pane('glass_clear')]
    brass = [mats.get('shelf_brass') or mats.metal('shelf_brass', 'A8813C',
                                                   rough=0.34, bump=0.05),
             mats.get('shelf_copper') or mats.metal('shelf_copper', 'A96A38',
                                                    rough=0.36, bump=0.06)]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux
    # a sparse shelf keeps its things together at one end, not spread thin
    span = ln * max(0.12, min(1.0, fill))
    u = rng.uniform(0.02, 0.06) + (ln - span) * rng.random()
    stop = u + span
    grp = rng.randint(3, 6)
    out = []
    while u < min(stop, ln - 0.05):
        # step over anything already standing here.  0.13 is a look-ahead for
        # the widest thing the scatter can produce, so an item is never started
        # close enough to a zone that its far side lands inside it.
        blk = [s1 for (s0, s1) in skip if u + 0.13 > s0 and u < s1]
        if blk:
            u = max(blk) + 0.03
            grp = rng.randint(3, 6)
            continue
        kind = rng.choices([k for k, _ in ITEMS], [w for _, w in ITEMS])[0]
        m = rng.choice(pool)
        if kind in ('jar', 'bottle', 'cup', 'stem') and rng.random() < 0.30:
            m = rng.choice(gl)
        elif kind in ('bowl', 'jar') and rng.random() < 0.16:
            m = rng.choice(brass)
        v = depth * back + rng.uniform(-0.03, 0.03)
        objs, wid = [], 0.09
        if kind == 'jar':
            r = rng.uniform(0.030, 0.052)
            h = min(maxh, rng.uniform(0.09, 0.17))
            objs = jar(name, r, h, cname=cname, mat=m, lidmat=rng.choice(pool))
            wid = 2 * r
        elif kind == 'can':
            r = rng.uniform(0.028, 0.042)
            h = min(maxh, rng.uniform(0.08, 0.13))
            objs = can(name, r, h, cname=cname, mat=m)
            wid = 2 * r
        elif kind == 'bottle':
            r = rng.uniform(0.026, 0.040)
            h = min(maxh + 0.04, rng.uniform(0.16, 0.26))
            objs = bottle(name, r, h, cname=cname, mat=m)
            wid = 2 * r
        elif kind == 'cup':
            r = rng.uniform(0.034, 0.046)
            objs = cup(name, r, rng.uniform(0.07, 0.095), cname=cname, mat=m)
            wid = 2.6 * r
        elif kind == 'bowl':
            r = rng.uniform(0.075, 0.115)
            objs = bowl(name, r, rng.uniform(0.045, 0.07), cname=cname, mat=m)
            wid = 2 * r
        elif kind == 'plates':
            r = rng.uniform(0.085, 0.115)
            objs = plate_stack(name, r, rng.randint(2, 5), cname=cname, mat=m)
            wid = 2 * r
        elif kind == 'carton':
            w = rng.uniform(0.055, 0.095)
            objs = carton(name, w, rng.uniform(0.04, 0.07),
                          min(maxh, rng.uniform(0.10, 0.19)), cname=cname, mat=m,
                          band=rng.choice(pool) if rng.random() < 0.75 else None)
            # a carton is the one item the walk turns on its own axis, by up to
            # half a radian, which swings its corners further along the shelf
            # than its width - and its label band is a further 0.8 mm proud on
            # every face.  Both were unpaid for, so cartons grazed their
            # neighbours.
            wid = w + 0.022
        elif kind == 'stem':
            r = rng.uniform(0.030, 0.040)
            objs = stemware(name, r, min(maxh, rng.uniform(0.13, 0.175)),
                            cname=cname, mat=m)
            wid = 2.05 * r
        else:
            # A book is built w across and t thick, and the walk then turns it
            # so w lies ALONG the shelf - but it was advancing by a fresh draw
            # in the thickness range instead, so each book claimed 26-50 mm of
            # shelf while occupying 120-190 mm of it.  Books simply grew through
            # whatever stood next to them.
            w = rng.uniform(0.12, 0.19)
            objs = book(name, w, rng.uniform(0.026, 0.05),
                        min(maxh, rng.uniform(0.17, 0.225)), cname=cname, mat=m)
            rng.uniform(0.026, 0.05)    # kept: kills the draw, not the sequence
            wid = w + 0.022
        u += wid * 0.5
        # Two things the walk never checked.  Along the run, the last item was
        # placed on its centre with no test that its far side still had shelf
        # under it - which is how a bowl came to hang 68 mm off the end of the
        # top cubby and into the window jabot.  Across the run, `v` is jittered
        # by up to 30 mm with no regard for how wide the item is, so a 172 mm
        # bowl on a 190 mm shelf could stand 22 mm proud of the front edge.
        if u + wid * 0.5 > ln - 0.008:
            for o in objs:
                bpy.data.objects.remove(o, do_unlink=True)
            break
        if depth > wid + 0.012:
            v = min(max(v, wid * 0.5 + 0.006), depth - wid * 0.5 - 0.006)
        else:
            v = depth * 0.5          # wider than the shelf is deep: centre it
        ang = rng.uniform(-0.5, 0.5)
        for o in objs:
            if kind in ('carton', 'book'):
                mlib.rotate_z(o, math.atan2(uy, ux) + ang)
            mlib.translate(o, (p0[0] + ux * u + nx * v, p0[1] + uy * u + ny * v, z))
            out.append(o)
        # tight inside a cluster, then a proper gap before the next one
        grp -= 1
        if grp <= 0:
            grp = rng.randint(3, 6)
            u += wid * 0.5 + rng.uniform(0.022, 0.080) / density
        else:
            u += wid * 0.5 + rng.uniform(0.001, 0.010) / density
    return out


# ---------------------------------------------------------------------- plants
def leaf_blade(name, ln=0.22, w=0.035, seg=7, cname="Details", curl=0.5,
               peak=0.5):
    """A blade folded either side of its midrib.  Three columns made a flat
    ribbon that read as a cut-out card from any angle; five give the leaf a
    spine to catch light along.  `peak` moves the widest point down the blade,
    which is what separates a heart-shaped pothos leaf from a lens."""
    rings = []
    for i in range(seg + 1):
        t = i / seg
        u = (t / peak) if t < peak else (1.0 - (t - peak) / (1.0 - peak))
        ww = w * max(0.0, u) ** 0.55
        droop = -curl * ln * (t ** 2) * 0.5
        # a deeper trough either side of the midrib: at 0.20 the blade was near
        # enough planar and caught the light as one flat facet
        fold = 0.34 * ww
        rings.append([(-ww, ln * t, droop - fold * 0.30),
                      (-ww * 0.55, ln * t, droop + fold * 0.55),
                      (0.0, ln * t, droop + fold),
                      (ww * 0.55, ln * t, droop + fold * 0.55),
                      (ww, ln * t, droop - fold * 0.30)])
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, 0.0016, offset=0)
    mlib.smooth_shade(ob, 50)
    return ob


def fern(name, loc, r=0.24, n=26, seed=1, cname="Details", pot=True,
         leafmat=None, potmat=None, scale=1.0):
    rng = random.Random(seed)
    fronds = []
    for i in range(n):
        a = rng.uniform(0, math.tau)
        tilt = rng.uniform(0.55, 1.35)
        ln = r * rng.uniform(0.7, 1.25) * scale
        fr = []
        stem_pts = []
        # arching fronds drop below the crown; on a big floor plant that put the
        # tips through the boards, so the arc is clamped to the pot's own base
        zfloor = -(loc[2] - 0.035)
        for k in range(9):
            t = k / 8.0
            zz = ln * (0.55 * math.sin(t * 1.9) - tilt * 0.85 * t * t)
            stem_pts.append((math.cos(a) * ln * t,
                             math.sin(a) * ln * t, max(zz, zfloor)))
        st = mlib.tube_along(name + "_st", stem_pts, mlib.circle(0.0035, 5), cname)
        fr.append(st)
        for k in range(1, 8):
            t = k / 8.0
            for s in (-1, 1):
                lf = leaf_blade(name + "_lf", ln * 0.30 * (1 - 0.55 * t),
                                0.016 * scale, 5, cname, curl=0.7)
                mlib.rotate_z(lf, a + s * rng.uniform(1.0, 1.4))
                mlib.rot_x(lf, rng.uniform(-0.35, 0.1))
                mlib.translate(lf, stem_pts[k])
                fr.append(lf)
        fronds += fr
    ob = mlib.join(fronds, name, cname)
    if leafmat:
        mlib.set_mat(ob, leafmat)
    mlib.translate(ob, loc)
    out = [ob]
    if pot:
        p = [(0.0, 0.0), (r * 0.42, 0.0), (r * 0.46, 0.012), (r * 0.55, r * 0.55),
             (r * 0.60, r * 0.62), (r * 0.555, r * 0.62), (r * 0.50, r * 0.55),
             (r * 0.40, 0.014), (0.0, 0.014)]
        po = mlib.revolve(name + "_pot", p, 26, cname=cname)
        mlib.smooth_shade(po, 34)
        if potmat:
            mlib.set_mat(po, potmat)
        mlib.translate(po, (loc[0], loc[1], loc[2] - r * 0.62))
        out.append(po)
    return out


def trailing_plant(name, loc, n=14, seed=2, cname="Details", leafmat=None,
                   potmat=None, r=0.11):
    rng = random.Random(seed)
    parts = []
    for i in range(n):
        a = rng.uniform(0, math.tau)
        ln = rng.uniform(0.22, 0.55)
        pts = []
        for k in range(10):
            t = k / 9.0
            pts.append((math.cos(a) * ln * 0.55 * t ** 0.7,
                        math.sin(a) * ln * 0.55 * t ** 0.7,
                        0.10 * math.sin(t * 2.4) - ln * t ** 1.7))
        st = mlib.tube_along(name + "_v", pts, mlib.circle(0.0028, 5), cname)
        parts.append(st)
        for k in range(2, 10):
            t = k / 9.0
            lf = leaf_blade(name + "_l", rng.uniform(0.070, 0.105),
                            rng.uniform(0.042, 0.058), 6, cname, curl=0.25,
                            peak=0.34)
            mlib.rotate_z(lf, a + rng.uniform(-2.2, 2.2))
            mlib.rot_x(lf, rng.uniform(-0.7, 0.2))
            mlib.translate(lf, pts[k])
            parts.append(lf)
    ob = mlib.join(parts, name, cname)
    if leafmat:
        mlib.set_mat(ob, leafmat)
    mlib.translate(ob, loc)
    out = [ob]
    p = [(0.0, 0.0), (r * 0.7, 0.0), (r * 0.78, 0.012), (r, r * 0.85),
         (r * 1.04, r * 0.95), (r * 0.98, r * 0.95), (r * 0.94, r * 0.85),
         (r * 0.66, 0.014), (0.0, 0.014)]
    po = mlib.revolve(name + "_pot", p, 22, cname=cname)
    mlib.smooth_shade(po, 34)
    if potmat:
        mlib.set_mat(po, potmat)
    mlib.translate(po, (loc[0], loc[1], loc[2] - r * 0.95))
    out.append(po)
    return out


# ------------------------------------------------------------------ framed art
def framed(name, w, h, loc, normal, cname="Details", framemat=None, artmat=None,
           mat_w=0.055, fw=0.032, fd=0.026, matmat=None):
    """Picture with a real frame, a mount board and the artwork inset in the
    rabbet (so nothing is coplanar)."""
    prof = [(-fw / 2, 0.0015), (-fw / 2, fd * 0.55), (-fw / 2 + 0.006, fd),
            (fw / 2 - 0.008, fd * 0.92), (fw / 2 - 0.004, fd * 0.42),
            (fw / 2, fd * 0.30), (fw / 2, 0.0015)]
    fr = mlib.sweep_rect_frame(name + "_fr", w + fw, h + fw, prof, cname)
    if framemat:
        mlib.set_mat(fr, framemat)
    parts = [fr]
    if mat_w > 0:
        mb = mlib.panel_with_holes(name + "_mb", w, h, 0.004,
                                   [(mat_w, mat_w, w - mat_w, h - mat_w)], cname)
        mb.data.transform(Matrix.Translation((-w / 2, 0, -h / 2)))
        mlib.translate(mb, (0, fd * 0.22, 0))
        mlib.set_mat(mb, matmat or mats.paint('mount_cream', 'EDE6D2', rough=0.75,
                                              coat=0.0))
        parts.append(mb)
    art = mlib.box(name + "_art", -w / 2 + 0.004, fd * 0.30, -h / 2 + 0.004,
                   w / 2 - 0.004, fd * 0.30 + 0.003, h / 2 - 0.004, cname)
    if artmat:
        mlib.set_mat(art, artmat)
    parts.append(art)
    ang = math.atan2(normal[1], normal[0]) - math.pi / 2
    for ob in parts:
        mlib.rotate_z(ob, ang)
        mlib.translate(ob, loc)
    return parts


# ---------------------------------------------------------------------- drapes
def swag(name, x0, x1, ztop, sag=0.34, depth=0.14, folds=7, cname="Details",
         mat=None, nseg=48):
    """A draped fabric swag: straight at the rod, sagging in the middle,
    rippled in depth."""
    rings = []
    w = x1 - x0
    for i in range(nseg + 1):
        u = i / nseg
        x = x0 + w * u
        rip = math.sin(u * folds * math.pi)
        col = []
        for j in range(9):
            v = j / 8.0
            drop = sag * math.sin(math.pi * u) ** 0.85 * v
            yy = depth * (0.35 + 0.65 * v) * (0.55 + 0.45 * rip)
            col.append((x, yy, ztop - drop - 0.02 * v * v))
        rings.append(col)
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, 0.006, offset=0)
    mlib.smooth_shade(ob, 55)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def jabot(name, x, ztop, ln=1.05, w=0.20, depth=0.13, side=1, cname="Details",
          mat=None):
    """Cascading tail beside a window."""
    rings = []
    for i in range(15):
        t = i / 14.0
        col = []
        # the ripple runs across v at 1.7 cycles; at seven rows that was four
        # samples a cycle, i.e. a zigzag with a facet on every fold
        for j in range(25):
            v = j / 24.0
            fold = math.sin(v * 3.4 * math.pi + t * 1.4)
            col.append((x + side * (w * v * (0.55 + 0.45 * t)),
                        depth * (0.25 + 0.75 * v) * (0.6 + 0.4 * fold),
                        ztop - ln * t - 0.10 * v * t))
        rings.append(col)
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, 0.006, offset=0)
    mlib.smooth_shade(ob, 55)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def curtain_panel(name, x0, x1, ztop, zbot, depth=0.10, folds=9, cname="Details",
                  mat=None, gather=0.55, flare=1.25, seed=0, hem=0.0,
                  fullness=2.2):
    """Long curtain with vertical folds, gathered at the top.

    Four things have to be true or it reads as something other than cloth.

    The folds swing to *both* sides of the panel's mean plane - a one-sided
    bulge is a corrugation, and that is the whole difference.  They wander
    sideways as they fall, because a fold that holds one plumb line for two
    metres is pressed tin.  No two are the same depth: gathered cloth is never
    regular, and regularity is what the eye picks up first.

    And the fold can be no deeper than the cloth can physically supply.  Cloth
    does not stretch, so a fold of pitch p and amplitude A implies a fullness
    ratio - flat width over hung width - of about

        F = sqrt(1 + 2 (pi A / p) ** 2)

    which inverts to a hard ceiling on A for a given p.  Left unbounded the
    loft happily draws folds three times deeper than they are wide; those are
    not folds but blades standing on edge, and where `solidify` thickens a
    blade whose crest is sharper than the shell is thick the offset surface
    crosses itself and sheds bright triangular shards.  That, plus sampling a
    sine five times a cycle, is what made these panels read as folded paper.
    `fullness` is how much cloth is gathered into the hung width: 2 to 2.5 for
    a curtain hanging at a window, 3 for one pushed to one end and bunched."""
    rng = random.Random(seed)
    s1, s2, s3 = (rng.uniform(0, math.tau) for _ in range(3))
    rings = []
    w = x1 - x0
    # a dozen-odd columns per fold, or the loft draws a zigzag - and a zigzag
    # under smooth shading is exactly the faceted look we are chasing out
    nseg = max(48, folds * 16)
    kmax = math.sqrt(max(fullness * fullness - 1.0, 0.0) / 2.0) / math.pi
    # the sideways wander adds up to 0.72 of a fold to the local frequency, so
    # the tightest pitch anywhere is w / (folds + 0.72), not w / folds
    def _spread(v):
        return 0.86 + 0.14 * v

    def _amp(u, v, k):
        # each fold also swells and shrinks as it falls: one that holds a single
        # depth for its whole drop is a pressed pleat, not cloth.  Inside _amp
        # rather than applied afterwards, so the fullness cap still sees it.
        vary = 1.0 + 0.22 * math.sin(u * folds * 1.3 + v * 2.1 + s3)
        return depth * k * vary * (gather + (1 - gather) * v) * flare ** v

    def _k(u):
        return 1.0 + 0.30 * math.sin(u * folds * 2.0 + s1) \
                   + 0.17 * math.sin(u * folds * 3.7 + s2)

    # one global scale rather than a per-sample clamp: clamping flattens every
    # deep fold to the same depth, and it is the unevenness that reads as cloth
    scale = 1.0
    for i in range(nseg + 1):
        u = i / nseg
        for j in range(13):
            v = j / 12.0
            a = _amp(u, v, _k(u))
            if a > 1e-9:
                scale = min(scale, kmax * w * _spread(v) / (folds + 0.72) / a)
    for i in range(nseg + 1):
        u = i / nseg
        k = _k(u)
        col = []
        for j in range(13):
            v = j / 12.0
            ph = (u * folds + 0.14 * math.sin(v * 2.3 + u * 5.1)) * math.tau
            amp = _amp(u, v, k) * scale
            xx = x0 + w * (u * _spread(v))
            yy = amp * math.sin(ph)
            zz = ztop - (ztop - zbot) * v
            if hem:
                # one-sided on purpose: a floor-length curtain breaks *on* the
                # boards and pools upward, so a signed wave put the hem through
                # the floor wherever it went negative
                zz += hem * (v ** 3) * (0.5 + 0.5 * math.sin(u * folds * 1.7 + s3))
            col.append((xx, yy, zz))
        rings.append(col)
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    # 3.5 mm, not 6: the shell has to be thinner than the crest radius of the
    # deepest fold or it self-intersects there, which is the other half of the
    # shard problem
    mlib.solidify(ob, 0.0035, offset=0)
    mlib.smooth_shade(ob, 55)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


# --------------------------------------------------------------------- lamps
def pleated_shade(name, rt=0.09, rb=0.17, h=0.19, pleats=26, cname="Details",
                  mat=None):
    rings = []
    for j in range(2):
        z = h * j
        r = rt + (rb - rt) * j
        ring = []
        for i in range(pleats * 2):
            a = math.tau * i / (pleats * 2)
            rr = r * (1.0 + (0.022 if i % 2 == 0 else -0.010))
            ring.append((rr * math.cos(a), rr * math.sin(a), z))
        rings.append(ring)
    ob = mlib._loft(name, [rings[0], rings[1]], close_u=True, close_v=False,
                    cname=cname)
    # note: u = ring index, so build transposed
    bpy.data.objects.remove(ob, do_unlink=True)
    cols = []
    for i in range(pleats * 2):
        a = math.tau * i / (pleats * 2)
        k = (0.022 if i % 2 == 0 else -0.010)
        cols.append([((rt * (1 + k)) * math.cos(a), (rt * (1 + k)) * math.sin(a), h),
                     ((rb * (1 + k)) * math.cos(a), (rb * (1 + k)) * math.sin(a), 0.0)])
    ob = mlib._loft(name, cols, close_u=True, close_v=False, cname=cname)
    mlib.solidify(ob, 0.0035, offset=0)
    mlib.smooth_shade(ob, 24)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def bulb(name, cname="Lighting", e=40.0, r=0.028):
    p = [(0.0, 0.0), (r, 0.014), (r * 1.1, 0.038), (r * 0.85, 0.062),
         (r * 0.40, 0.074), (r * 0.40, 0.094), (0.0, 0.094)]
    ob = mlib.revolve(name, p, 18, cname=cname)
    mlib.smooth_shade(ob, 40)
    mlib.set_mat(ob, mats.get('bulb_warm') or
                 mats.emissive('bulb_warm', 'FFE0AE', strength=e, base='FFF3E2'))
    return ob


def flush_dome(name, loc, cname="Lighting", r=0.115, energy=16.0,
               colr=(1.0, 0.86, 0.70), drop=0.075):
    """Small opal ceiling fitting - a dome on a ring, bulb inside.  For the
    utility rooms, where the light has to come from something but the something
    should not draw attention to itself.  Returns the geometry; the lamp goes in
    at the bulb, which is the only place it can honestly be."""
    parts = []
    ring = mlib.revolve(name + "_rg", [(0.0, 0.0), (r * 0.80, -0.004),
                                       (r * 0.84, -0.016), (r * 0.62, -0.024),
                                       (0.0, -0.026)], 20, cname=cname)
    mlib.set_mat(ring, mats.get('shelf_brass') or
                 mats.metal('shelf_brass', 'A8813C', rough=0.34, bump=0.05))
    parts.append(ring)
    prof = []
    for i in range(13):
        t = i / 12.0
        a = math.pi * 0.5 * t
        prof.append((r * math.sin(a), -0.018 - drop * (1.0 - math.cos(a))))
    sh = mlib.revolve(name + "_sh", prof, 26, cname=cname, cap_start=False,
                      cap_end=False)
    mlib.solidify(sh, 0.004, offset=0)
    mlib.smooth_shade(sh, 46)
    mlib.set_mat(sh, mats.get('opal_shade') or
                 mats.emissive('opal_shade', 'FFF0D2', strength=2.2,
                               base='F6EEDC'))
    parts.append(sh)
    bl = bulb(name + "_bl", cname, e=24.0, r=0.020)
    mlib.translate(bl, (0, 0, -drop - 0.030))
    parts.append(bl)
    for o in parts:
        mlib.translate(o, loc)
    point_light(name + "_light", (loc[0], loc[1], loc[2] - drop * 0.55), energy,
                colr, 0.07)
    return parts


def blackbody(kelvin):
    """Linear-sRGB tint of a Planckian radiator at `kelvin`.

    Planck's law integrated against the CIE 1931 2-degree observer - the
    Wyman/Sloan/Shirley multi-lobe fit, good to about a percent - then through
    the Rec.709 primaries.  Written out rather than eyeballed as an RGB triple
    so that a fixture's source says 3500 K and actually means it.

    Normalised so the brightest channel is 1.0, which is the convention every
    other light in this build already follows: the wattage carries the
    intensity and the colour carries only the tint, so the numbers stay
    comparable from fixture to fixture."""
    def g(x, mu, s1, s2):
        return math.exp(-((x - mu) / (s1 if x < mu else s2)) ** 2 / 2.0)
    X = Y = Z = 0.0
    for nm in range(380, 781, 5):
        lm = nm * 1e-9
        # Planck, minus the constants that cancel in the normalisation
        sp = 1.0 / (lm ** 5 * (math.exp(1.4387769e-2 / (lm * kelvin)) - 1.0))
        X += sp * (1.056 * g(nm, 599.8, 37.9, 31.0)
                   + 0.362 * g(nm, 442.0, 16.0, 26.7)
                   - 0.065 * g(nm, 501.1, 20.4, 26.2))
        Y += sp * (0.821 * g(nm, 568.8, 46.9, 40.5)
                   + 0.286 * g(nm, 530.9, 16.3, 31.1))
        Z += sp * (1.217 * g(nm, 437.0, 11.8, 36.0)
                   + 0.681 * g(nm, 459.0, 26.0, 13.8))
    rgb = (3.2406 * X - 1.5372 * Y - 0.4986 * Z,
           -0.9689 * X + 1.8758 * Y + 0.0415 * Z,
           0.0557 * X - 0.2040 * Y + 1.0570 * Z)
    m = max(rgb)
    return tuple(max(c / m, 0.0) for c in rgb)


def point_light(name, loc, energy=25.0, colr=(1.0, 0.80, 0.60), size=0.05):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = colr
    ld.shadow_soft_size = size
    lo = bpy.data.objects.new(name, ld)
    mlib.put(lo, "Lighting")
    lo.location = Vector(loc)
    return lo
