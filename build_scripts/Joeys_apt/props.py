"""props - the parts every piece of furniture in this flat is made from.

Nothing here is a scaled cube.  A cabinet door is stiles, rails and a raised
field; a knob is a lathed profile; a curtain is a swept fold surface with real
thickness.  That matters less for any single object than it does cumulatively:
a room full of primitives reads as a render, and a room full of things that
were *made* reads as a room.

Two conventions run through the whole file:

  * Everything is built in world space by moving vertices, never by setting an
    object transform, so Object/Generated texture coordinates stay keyed to
    where a thing actually stands.  Two cabinet doors 400 mm apart get
    different grain, which is what happens when you cut them from a board.

  * Applied parts stand PROUD of, or are let INTO, whatever they sit on - never
    flush with it.  A pull floats 22 mm off its door, a plinth is set back
    75 mm, a raised field is 8 mm proud of its board.  There is then nothing
    anywhere for the depth buffer to argue about, and every joint throws a
    shadow line of its own.
"""
import bpy, math, random
from mathutils import Vector
import mlib, mats, L

TAU = math.pi * 2.0


# ================================================================== primitives

def cyl(name, r, z0, z1, seg=24, cx=0.0, cy=0.0, cname=None, phase=0.0):
    """A capped cylinder about the Z axis - n-gon ends, quad sides."""
    return mlib.prism(name, mlib.circle(r, seg, cx, cy, phase), z0, z1, cname)


def lathe(name, profile, seg=28, cname=None, smooth=42.0, cap=True):
    ob = mlib.revolve(name, profile, segments=seg, cname=cname,
                      cap_start=cap, cap_end=cap)
    if smooth:
        mlib.smooth_shade(ob, smooth)
    return ob


def rod(name, p0, p1, r, seg=12, cname=None, cap=True):
    """A round bar between two points in space."""
    return mlib.tube_along(name, [p0, p1], mlib.circle(r, seg), cname=cname,
                           cap=cap)


def torus(name, R, r, useg=32, vseg=12, cname=None, cz=0.0, cx=0.0, cy=0.0,
          arc=TAU):
    rings = []
    n = useg if abs(arc - TAU) < 1e-6 else useg + 1
    for i in range(n):
        a = arc * i / useg
        ca, sa = math.cos(a), math.sin(a)
        ring = []
        for j in range(vseg):
            b = TAU * j / vseg
            rr = R + r * math.cos(b)
            ring.append((cx + rr * ca, cy + rr * sa, cz + r * math.sin(b)))
        rings.append(ring)
    ob = mlib.loft(name, rings, close_u=abs(arc - TAU) < 1e-6, close_v=True,
                   cname=cname)
    mlib.smooth_shade(ob, 60)
    return ob


def sweep_var(name, spine, radii, seg=14, cname=None, up=(0, 0, 1), cap=True,
              smooth=60.0):
    """Sweep an ELLIPSE OF VARYING SIZE along a 3D spine, each section held
    perpendicular to the local tangent.

    This is the one tool that lets an organic form be a single manifold surface
    instead of a pile of interpenetrating lumps: a dog's body from rump to
    muzzle, an arm roll, a bolster, a curved handrail.  `radii` gives (across,
    up) half-widths per spine point, so a section can be flattened where the
    real thing is flattened.
    """
    P = [Vector(p) for p in spine]
    n = len(P)
    tans = []
    for i in range(n):
        if i == 0:
            t = P[1] - P[0]
        elif i == n - 1:
            t = P[-1] - P[-2]
        else:
            t = P[i + 1] - P[i - 1]
        tans.append(t.normalized())

    # PARALLEL TRANSPORT, not a fixed reference vector.  Deriving the frame
    # from `up` at every section looks equivalent and is not: the moment a
    # spine passes near vertical, the fallback axis kicks in for some sections
    # and not others, the frame flips between them, and the surface takes a
    # half turn in one segment.  On a dog's hind leg that shows up as a
    # corkscrew - which is exactly what it did.  Carrying the frame forward
    # and re-orthogonalising it can never flip.
    u = Vector(up)
    if abs(tans[0].dot(u)) > 0.9:
        u = Vector((1, 0, 0))
    s = tans[0].cross(u).normalized()

    rings = []
    for i, p in enumerate(P):
        t = tans[i]
        s = (s - t * s.dot(t))
        if s.length < 1e-6:
            s = t.cross(Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0)))
        s.normalize()
        u2 = s.cross(t).normalized()
        ra, rb = radii[i]
        ring = [tuple(p + s * (ra * math.cos(TAU * j / seg))
                      + u2 * (rb * math.sin(TAU * j / seg))) for j in range(seg)]
        rings.append(ring)
    ob = mlib.loft(name, rings, close_u=False, close_v=True, cname=cname,
                   cap_start=cap, cap_end=cap)
    if smooth:
        mlib.smooth_shade(ob, smooth)
    return ob


def face_y(obj, sign=-1.0, at=(0.0, 0.0, 0.0)):
    """Take something lathed about +Z and lay it down pointing along ±Y.

    `sign` is the direction the thing ends up POINTING, not the direction of
    rotation - face_y(-1) gives a knob standing out of a north-facing wall.
    Getting this backwards is silent: the knob is still there, still shaded,
    just buried inside the door it belongs to."""
    mlib.rot_x(obj, -math.pi * 0.5 * sign)
    mlib.translate(obj, at)
    return obj


def face_x(obj, sign=1.0, at=(0.0, 0.0, 0.0)):
    """As face_y, along ±X."""
    mlib.rot_y(obj, math.pi * 0.5 * sign)
    mlib.translate(obj, at)
    return obj


# ================================================================== casework

def cab_door(name, w, h, th=0.019, rail=0.058, inset=0.010, proud=0.0055,
             cname=None, bevel=True):
    """A frame-and-panel cabinet door, built flat: x 0..w, y 0..th, z 0..h,
    front face at y = 0.

    The field is a separate solid standing `proud` off the frame's rebate, so
    the ovolo round it is a real chamfer that catches light, not a texture."""
    parts = []
    parts.append(mlib.box(name + "_sl", 0, 0, 0, rail, th, h, cname))
    parts.append(mlib.box(name + "_sr", w - rail, 0, 0, w, th, h, cname))
    parts.append(mlib.box(name + "_rb", rail, 0, 0, w - rail, th, rail, cname))
    parts.append(mlib.box(name + "_rt", rail, 0, h - rail, w - rail, th, h, cname))
    # The panel sits in a rebate towards the back with its field pushed
    # forward.  The field STOPS SHORT of the panel's own back face - run them
    # out to the same plane and the two backs are coplanar, same-facing and
    # overlapping, which is the one configuration the depth buffer cannot call.
    pb = mlib.box(name + "_pb", rail - 0.004, th - 0.010, rail - 0.004,
                  w - rail + 0.004, th, h - rail + 0.004, cname)
    pf = mlib.box(name + "_pf", rail + inset, th - 0.010 - proud, rail + inset,
                  w - rail - inset, th - 0.004, h - rail - inset, cname)
    parts += [pb, pf]
    ob = mlib.join(parts, name, cname)
    if bevel:
        mlib.bevel(ob, min(proud * 0.85, 0.0045), 3, 34)
    return ob


def slab_front(name, w, h, th=0.019, groove=0.0, cname=None):
    """A plain drawer front with an eased edge - what a 1950s kitchen drawer is."""
    ob = mlib.box(name, 0, 0, 0, w, th, h, cname)
    mlib.bevel(ob, 0.0035, 3, 34)
    return ob


def carcass(name, x0, y0, x1, y1, z0, z1, cname=None, back=0.012, side=0.016,
            top=0.016, back_at='y0', shelves=(), lid=True):
    """An open-fronted box carcass: two sides, a back, a bottom, a top and any
    fixed shelves.  Built as solids that BUTT rather than one hollowed block,
    so the inside corners have real joint lines in them.

    `back_at` says which Y face the back panel is on - a run against a north
    wall has its back at y1, one against a south wall at y0.

    `lid=False` leaves the top OFF.  A sink base has no top: the bowl hangs
    down into it through the worktop.  Given one, the panel sits 40 mm under
    the stone and closes the cut-out, and every camera looking down at the sink
    sees a flat cream rectangle where the bowl should be - which is exactly
    what "the sink is not a real sink" looked like."""
    by0, by1 = (y0, y0 + back) if back_at == 'y0' else (y1 - back, y1)
    iy0, iy1 = (by1, y1) if back_at == 'y0' else (y0, by0)
    parts = [
        mlib.box(name + "_l", x0, y0, z0, x0 + side, y1, z1, cname),
        mlib.box(name + "_r", x1 - side, y0, z0, x1, y1, z1, cname),
        mlib.box(name + "_bk", x0 + side, by0, z0, x1 - side, by1, z1, cname),
        mlib.box(name + "_bt", x0 + side, iy0, z0, x1 - side, iy1, z0 + top, cname),
    ]
    if lid:
        parts.append(mlib.box(name + "_tp", x0 + side, iy0, z1 - top,
                              x1 - side, iy1, z1, cname))
    for i, sz in enumerate(shelves):
        parts.append(mlib.box(name + "_sh%d" % i, x0 + side, iy0, sz - 0.009,
                              x1 - side, iy1, sz + 0.009, cname))
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.0016, 2, 44)
    return ob


def worktop(name, x0, y0, x1, y1, ztop, th=0.038, r=0.008, cname=None,
            seg=4, radii=None):
    """A counter slab with an eased nose.  `radii` is (SW, SE, NE, NW): give a
    corner zero where the top dies into a wall and a radius where it is
    exposed, so the run reads as cut to fit rather than dropped in."""
    R = list(radii) if radii else [r] * 4
    spec = [((x0 + R[0], y0 + R[0]), math.pi, R[0]),
            ((x1 - R[1], y0 + R[1]), math.pi * 1.5, R[1]),
            ((x1 - R[2], y1 - R[2]), 0.0, R[2]),
            ((x0 + R[3], y1 - R[3]), math.pi * 0.5, R[3])]
    pts = []
    for (c, a0, rr) in spec:
        if rr <= 1e-6:
            pts.append(c)
        else:
            pts.extend(mlib.arc_pts(c[0], c[1], rr, a0, a0 + math.pi * 0.5, seg))
    ob = mlib.prism(name, pts, ztop - th, ztop, cname)
    mlib.bevel(ob, min(0.004, th * 0.16), 3, 40)
    mlib.smooth_shade(ob, 34)
    return ob


def plinth(name, x0, y0, x1, y1, z0, z1, cname=None, r=0.0):
    ob = mlib.box(name, x0, y0, z0, x1, y1, z1, cname)
    mlib.bevel(ob, 0.003, 2, 40)
    return ob


# ================================================================== hardware

def knob(name, r=0.017, cname=None, stem=0.014):
    """A turned mushroom knob, pointing +Z, base at the origin."""
    p = [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.60, 0.004),
         (r * 0.30, 0.007), (r * 0.28, stem * 0.55),
         (r * 0.52, stem * 0.86), (r * 0.98, stem + r * 0.30),
         (r * 0.94, stem + r * 0.72), (r * 0.62, stem + r * 1.02),
         (0.0, stem + r * 1.10)]
    return lathe(name, p, 22, cname, smooth=46)


def bar_pull(name, length, cname=None, r=0.0062, stand=0.030, post=0.007):
    """A bar pull lying along X, standing off the door in -Y.  The bar is a
    swept tube with radiused returns, not three sticks that happen to touch."""
    a = length * 0.5 - 0.014
    path = [(-a, 0.0, 0.0), (-a, -stand + r * 1.4, 0.0),
            (-a, -stand, 0.0), (a, -stand, 0.0),
            (a, -stand + r * 1.4, 0.0), (a, 0.0, 0.0)]
    ob = mlib.tube_along(name, path, mlib.circle(r, 12), cname=cname)
    mlib.smooth_shade(ob, 46)
    return ob


def handle_bar(name, length, cname=None, r=0.011, stand=0.052, plate=0.030):
    """A heavy appliance handle: two cast standoffs and a thick bar between.
    This is the range and fridge handle."""
    a = length * 0.5
    parts = [mlib.tube_along(name + "_b", [(-a, -stand, 0.0), (a, -stand, 0.0)],
                             mlib.circle(r, 14), cname=cname)]
    for s in (-1, 1):
        parts.append(lathe(name + "_p%d" % (s > 0),
                           [(0.0, 0.0), (plate * 0.5, 0.0), (plate * 0.46, 0.010),
                            (r * 1.5, stand - r), (0.0, stand - r)], 16, cname))
        face_y(parts[-1], -1.0, (a * s, 0.0, 0.0))
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 44)
    return ob


def hinge_leaf(name, h=0.062, cname=None, r=0.008):
    ob = lathe(name, [(0.0, 0.0), (r, 0.0), (r, h), (0.0, h)], 14, cname)
    return ob


# ================================================================== legs

def turned_leg(name, h, top_r=0.026, cname=None, seg=20, taper=0.55):
    """A lathed leg - a square-ish head, a swelled shaft, a small foot."""
    r = top_r
    p = [(0.0, 0.0), (r * taper * 0.9, 0.0), (r * taper * 1.05, 0.014),
         (r * taper * 0.86, 0.030), (r * 0.80, h * 0.30),
         (r * 0.98, h * 0.52), (r * 0.92, h * 0.74),
         (r * 1.02, h * 0.88), (r * 0.99, h * 0.95), (r, h), (0.0, h)]
    return lathe(name, p, seg, cname, smooth=44)


def taper_leg(name, h, top=0.042, bot=0.022, cname=None, r=0.004):
    """A square tapered leg, corners eased."""
    rings = []
    for (t, s) in ((0.0, bot), (1.0, top)):
        hw = s * 0.5
        rings.append([(x, y, t * h) for (x, y) in mlib.rounded_rect(s, s, r, 3)])
    ob = mlib.loft(name, rings, close_u=False, close_v=True, cname=cname,
                   cap_start=True, cap_end=True)
    mlib.bevel(ob, 0.0015, 2, 46)
    return ob


def hairpin(name, h, spread=0.16, r=0.005, cname=None, legs=3, plate=0.038):
    """A hairpin leg: steel rods splayed at the FOOT and converging on a
    mounting plate under the top, which is the way round they actually go."""
    parts = [mlib.box(name + "_p", -plate, -plate, h - 0.004, plate, plate, h,
                      cname)]
    for i in range(legs):
        a = TAU * i / legs + math.pi * 0.25
        dx, dy = math.cos(a) * spread, math.sin(a) * spread
        path = [(dx, dy, 0.0), (dx * 0.94, dy * 0.94, h * 0.10),
                (dx * 0.62, dy * 0.62, h * 0.44),
                (dx * 0.22, dy * 0.22, h * 0.80), (0.0, 0.0, h - 0.002)]
        parts.append(mlib.tube_along(name + "_r%d" % i, path, mlib.circle(r, 8),
                                     cname=cname))
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 46)
    return ob


# ================================================================== soft goods

def drape(name, x0, x1, y, z0, z1, folds=7, amp=0.055, cname=None,
          nz=14, taper=0.55, seed=3, axis='X', flare=1.18, th=0.0045):
    """A hanging curtain panel: a swept fold surface given real thickness.

    The fold amplitude is pinched near the head, where the fabric is gathered
    onto the rod, and allowed to open towards the hem - a constant-amplitude
    sine reads as corrugated iron.  Fold width and depth are jittered so no two
    folds match, which is the difference between cloth and a wave modifier.
    """
    rnd = random.Random(seed)
    span = x1 - x0
    ncol = max(24, int(folds * 9))
    jitter = [1.0 + rnd.uniform(-0.30, 0.30) for _ in range(folds + 2)]

    def depth(u):
        f = u * folds
        i = int(f) % len(jitter)
        k = jitter[i]
        return math.cos(f * TAU) * k

    rings = []
    for c in range(ncol + 1):
        u = c / ncol
        d = depth(u)
        # ends are pulled back to the wall so the panel does not float
        edge = min(1.0, (min(u, 1.0 - u) / 0.06))
        col = []
        for j in range(nz + 1):
            t = j / nz
            grow = taper + (1.0 - taper) * (t ** 0.65) * flare
            off = d * amp * grow * edge
            zz = z0 + (z1 - z0) * t
            # a little sag in the hem
            zz -= (1.0 - abs(d)) * 0.006 * (1.0 - t) ** 2
            if axis == 'X':
                col.append((x0 + span * u, y + off, zz))
            else:
                col.append((y + off, x0 + span * u, zz))
        rings.append(col)
    ob = mlib.loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, th, offset=0)
    mlib.apply_all(ob)
    mlib.smooth_shade(ob, 52)
    return ob


def skirt(name, x0, x1, y, z0, z1, folds=9, amp=0.026, cname=None, seed=7):
    """The gathered curtain hung under a sink counter in place of doors."""
    return drape(name, x0, x1, y, z0, z1, folds=folds, amp=amp, cname=cname,
                 nz=8, taper=0.28, seed=seed, flare=1.25, th=0.0035)


def pillow(name, w, h, d, cname=None, seg=6):
    ob = mlib.cushion(name, w, h, d, r=min(w, h) * 0.34, cname=cname, seg=seg,
                      plump=1.10)
    return ob


def bolster(name, length, r, cname=None, seg=20):
    """A cylindrical scatter cushion with pinched ends."""
    p = [(0.0, 0.0), (r * 0.30, 0.006), (r * 0.80, 0.030), (r, 0.10),
         (r * 1.02, length * 0.5), (r, length - 0.10),
         (r * 0.80, length - 0.030), (r * 0.30, length - 0.006), (0.0, length)]
    ob = lathe(name, p, seg, cname, smooth=50)
    return ob


def rug(name, cx, cy, w, d, regions, slots, cname=None, cell=0.035,
        th=0.014, pile=0.0016, seed=11, rot=0.0, z0=0.0):
    """A rug as one manifold slab whose TOP is a fine grid, so the pattern can
    be painted on per face instead of being stacked as separate slabs.

    Overlaying coloured panels on a base is the obvious way to do this and it
    is wrong twice: coplanar tops fight in the depth buffer, and lifting them
    clear turns a woven pattern into inlaid lino.  One mesh, many material
    slots, and a per-vertex height jitter for pile.  `regions` maps a point in
    the rug's own 0..1 space to a slot index.
    """
    rnd = random.Random(seed)
    nx = max(4, int(round(w / cell)))
    ny = max(4, int(round(d / cell)))
    x0, y0 = -w * 0.5, -d * 0.5

    top, verts, faces = {}, [], []

    def tv(i, j):
        k = (i, j)
        if k not in top:
            top[k] = len(verts)
            verts.append((x0 + w * i / nx, y0 + d * j / ny,
                          th + rnd.uniform(-pile, pile)))
        return top[k]

    mat_of = []
    for i in range(nx):
        for j in range(ny):
            faces.append((tv(i, j), tv(i + 1, j), tv(i + 1, j + 1), tv(i, j + 1)))
            mat_of.append(regions((i + 0.5) / nx, (j + 0.5) / ny))

    # border loop, dropped to the floor, then a single bottom n-gon
    loop = ([ (i, 0) for i in range(nx + 1) ] +
            [ (nx, j) for j in range(1, ny + 1) ] +
            [ (i, ny) for i in range(nx - 1, -1, -1) ] +
            [ (0, j) for j in range(ny - 1, 0, -1) ])
    low = []
    for (i, j) in loop:
        low.append(len(verts))
        vx, vy, _ = verts[tv(i, j)]
        verts.append((vx, vy, 0.0))
    nL = len(loop)
    for k in range(nL):
        a, b = tv(*loop[k]), tv(*loop[(k + 1) % nL])
        faces.append((a, low[k], low[(k + 1) % nL], b))
        mat_of.append(0)
    faces.append(tuple(reversed(low)))
    mat_of.append(0)

    ob = mlib.mesh_obj(name, verts, faces, cname)
    mlib.recalc_normals(ob)
    # Slots go on BEFORE the per-face indices.  Clearing or re-filling the
    # material list afterwards is what silently flattened the first pattern to
    # a single colour.
    mlib.assign_mats(ob, list(slots))
    for p, mi in zip(ob.data.polygons, mat_of):
        p.material_index = mi
    ob.data.update()
    if rot:
        mlib.rotate_z(ob, rot)
    # z0 lifts the whole slab.  The parquet stands 10.5 mm proud with half a
    # millimetre of lippage on top of that, so a rug modelled from z=0 has
    # its underside INSIDE the boards and its top only just clear - which
    # shows up as the floor pattern tearing through the rug.
    mlib.translate(ob, (cx, cy, z0))
    return ob


# ================================================================== tabletop

def book(name, w, h, t, cname=None, lean=0.0):
    """A book: boards, a spine with a real radius, and a block of leaves set in
    from the boards on three sides."""
    parts = [mlib.box(name + "_bk", 0, 0, 0, w, t, h, cname)]
    blk = mlib.box(name + "_lv", 0.004, 0.0022, 0.004, w - 0.002,
                   t - 0.0022, h - 0.004, cname)
    parts.append(blk)
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.0012, 2, 44)
    return ob


def can(name, cx, cy, z0, r=0.033, h=0.122, cname=None):
    p = [(0.0, 0.0), (r * 0.86, 0.0), (r * 0.94, 0.004), (r, 0.014),
         (r, h - 0.014), (r * 0.94, h - 0.004), (r * 0.86, h - 0.001),
         (r * 0.90, h), (0.0, h)]
    ob = lathe(name, p, 20, cname, smooth=44)
    mlib.translate(ob, (cx, cy, z0))
    return ob


def bottle(name, cx, cy, z0, r=0.036, h=0.24, neck=0.013, cname=None):
    p = [(0.0, 0.0), (r * 0.9, 0.0), (r, 0.012), (r, h * 0.52),
         (r * 0.96, h * 0.62), (neck * 1.9, h * 0.76), (neck, h * 0.84),
         (neck, h - 0.014), (neck * 1.18, h - 0.010), (neck * 1.18, h),
         (0.0, h)]
    ob = lathe(name, p, 20, cname, smooth=46)
    mlib.translate(ob, (cx, cy, z0))
    return ob


def jar(name, cx, cy, z0, r=0.052, h=0.15, cname=None):
    p = [(0.0, 0.0), (r * 0.88, 0.0), (r, 0.018), (r, h * 0.70),
         (r * 0.90, h * 0.82), (r * 0.74, h * 0.90), (r * 0.78, h),
         (0.0, h)]
    ob = lathe(name, p, 22, cname, smooth=46)
    mlib.translate(ob, (cx, cy, z0))
    return ob


def mug(name, cx, cy, z0, r=0.042, h=0.098, cname=None, handle=True, rotz=0.0):
    p = [(0.0, 0.0), (r * 0.80, 0.0), (r * 0.86, 0.006), (r * 0.80, 0.012),
         (r * 0.94, 0.030), (r, h - 0.004), (r, h),
         (r - 0.0045, h - 0.002), (r - 0.0045, 0.015), (0.0, 0.016)]
    body = lathe(name, p, 22, cname, smooth=48, cap=False)
    parts = [body]
    if handle:
        hp = [(r * 0.84, 0.0, h * 0.80), (r * 1.34, 0.0, h * 0.82),
              (r * 1.52, 0.0, h * 0.56), (r * 1.32, 0.0, h * 0.30),
              (r * 0.84, 0.0, h * 0.26)]
        hd = mlib.tube_along(name + "_h", hp, mlib.circle(0.0058, 8), cname=cname)
        mlib.smooth_shade(hd, 50)
        parts.append(hd)
    ob = mlib.join(parts, name, cname)
    if rotz:
        mlib.rotate_z(ob, rotz)
    mlib.translate(ob, (cx, cy, z0))
    return ob


def bowl(name, cx, cy, z0, r=0.10, h=0.062, cname=None):
    p = [(0.0, 0.0), (r * 0.42, 0.0), (r * 0.46, 0.004), (r * 0.74, h * 0.35),
         (r, h), (r - 0.004, h - 0.002), (r * 0.70, h * 0.34),
         (r * 0.40, 0.006), (0.0, 0.006)]
    ob = lathe(name, p, 26, cname, smooth=50, cap=False)
    mlib.translate(ob, (cx, cy, z0))
    return ob


def boxprop(name, cx, cy, z0, w, d, h, cname=None, rotz=0.0, r=0.004):
    """A carton - cereal, crackers, a games box.  Corners eased so it catches
    an edge highlight."""
    ob = mlib.box(name, -w * 0.5, -d * 0.5, 0.0, w * 0.5, d * 0.5, h, cname)
    mlib.bevel(ob, r, 2, 40)
    if rotz:
        mlib.rotate_z(ob, rotz)
    mlib.translate(ob, (cx, cy, z0))
    return ob


# ================================================================== wall goods

def frame_art(name, w, h, depth=0.030, cname=None, moulding=0.042,
              rebate=0.008, standoff=0.0):
    """A mitred picture frame with its image just behind the glass line.

    `rebate` is how far the print sits BEHIND the moulding's front face, and it
    has to be small.  Measured from the BACK of the frame instead, as it was,
    the print ends up 21 mm down a well, and from any angle off square you see
    the lit inner wall of that well as a pale band all round the picture -
    which reads as a mount nobody asked for, not as a frame.

    Built in the XZ plane centred on the origin, with +Y standing PROUD of the
    wall - the frame every wall-hung thing in this file is made in, see
    `wall_place`.  The moulding is let 2 mm back into the plaster and the
    picture is its own slab a few millimetres in front of it, so nothing is
    coplanar with anything.
    """
    # `standoff` lifts the whole frame off the plaster.  On a panelled wall the
    # picture hangs OVER the panel moulding, so its back has to clear the
    # moulding's face - let into the wall it intersects the panel instead, and
    # the two backs end up coplanar.
    b0 = standoff if standoff else -0.002
    b1 = b0 + depth
    prof = [(0.0, b0), (moulding, b0), (moulding, b0 + depth * 0.58),
            (moulding * 0.66, b1), (0.0, b1)]
    fr = mlib.sweep_rect_frame(name + "_f", w, h, prof, cname)
    mlib.bevel(fr, 0.0018, 2, 40)
    # sweep_rect_frame takes w, h as the frame's OPENING and grows the moulding
    # OUTWARD from it - so w x h is exactly the visible picture, and the print
    # has to be cut OVERSIZE and tucked under the rebate.  Cut undersize, as it
    # was, it leaves a ring of bare rebate showing all round the image, which
    # is the pale border that made the frame look too big for the poster.
    #
    # The oversize is a UNIFORM SCALE, not a fixed margin on each side: the
    # image is mapped over the print's whole bounding box, so adding the same
    # millimetres to a tall picture's width and height changes its aspect and
    # prints it stretched.  Scaling keeps w:h exactly, which means the frame's
    # opening must itself be cut to the file's ratio - that is the one number
    # each call site has to get right.  The second term stops the long side
    # growing out past the moulding on a very elongated frame.
    s = 1.0 + min(moulding * 0.80 / min(w, h), moulding * 1.60 / max(w, h))
    iw, ih = w * 0.5 * s, h * 0.5 * s
    pic = mlib.box(name + "_p", -iw, b1 - rebate - 0.005, -ih,
                   iw, b1 - rebate, ih, cname)
    mlib.uv_planar(pic)
    return [fr, pic]


def wall_place(objs, wall, u, z, at, flip=False):
    """Take something built in the XZ plane with +Y standing proud, and stand
    it on a wall.  `at` is the wall's inner face; `u` runs along the wall.

    N: plane y = at, room to the south, so the piece must face -Y.
    S: plane y = at, room to the north, faces +Y.
    E: plane x = at, room to the west, faces -X.
    W: plane x = at, room to the east, faces +X.
    """
    for o in objs:
        if wall == 'N':
            mlib.rotate_z(o, math.pi)
            mlib.translate(o, (u, at, z))
        elif wall == 'S':
            mlib.translate(o, (u, at, z))
        elif wall == 'E':
            mlib.rotate_z(o, math.pi * 0.5)
            mlib.translate(o, (at, u, z))
        else:
            mlib.rotate_z(o, -math.pi * 0.5)
            mlib.translate(o, (at, u, z))
    return objs
