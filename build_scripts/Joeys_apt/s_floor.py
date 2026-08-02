"""The parquet, as real geometry - one slab per finger.

The set's floor is mosaic (finger-block) parquet: a square block of five
parallel strips, with every neighbouring block turned through ninety degrees,
so the floor reads as a basket weave.  It is by far the most recognisable
surface in the apartment and it will not survive being a texture: at the
camera heights these photographs were taken from you can see the joints as
grooves, you can see individual fingers standing a fraction proud of their
neighbours, and every finger catches the window light differently because its
grain runs a different way.

So each finger is its own slab, inset by half a joint so the grooves are real,
carrying its own generated UVs (grain axis) and its own colour attribute
(tone).  The blocks are laid to the room, not at 45 degrees.
"""
import bpy, math, random, colorsys
from mathutils import Vector
import mlib, mats

T = 0.3048          # block module - 12 inch
NFING = 5           # fingers per block
JOINT = 0.0012      # groove between fingers
TH = 0.0105         # slab thickness
DECK = 0.0026       # how far below the finger tops the sub-floor sits
SUB = 0.030         # sub-floor thickness


def _clip(poly, rect):
    """Sutherland-Hodgman against an axis-aligned rectangle (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = rect
    edges = ((0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1))
    out = list(poly)
    for (ax, val, sgn) in edges:
        if not out:
            return []
        src, out = out, []
        n = len(src)
        for i in range(n):
            a, b = src[i], src[(i + 1) % n]
            da = (a[ax] - val) * sgn
            db = (b[ax] - val) * sgn
            if da >= -1e-9:
                out.append(a)
            if (da > 1e-9) != (db > 1e-9) and abs(da - db) > 1e-12:
                t = da / (da - db)
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    # drop duplicate points the clip can leave behind on a grazing edge
    cleaned = []
    for p in out:
        if not cleaned or (abs(p[0] - cleaned[-1][0]) > 1e-7 or abs(p[1] - cleaned[-1][1]) > 1e-7):
            cleaned.append(p)
    if len(cleaned) > 2 and abs(cleaned[0][0] - cleaned[-1][0]) < 1e-7 \
            and abs(cleaned[0][1] - cleaned[-1][1]) < 1e-7:
        cleaned.pop()
    return cleaned if len(cleaned) >= 3 else []


def _sub_rect(r, cut):
    """r minus cut, as up to four axis-aligned rectangles."""
    x0, y0, x1, y1 = r
    a0, b0, a1, b1 = cut
    if a1 <= x0 or a0 >= x1 or b1 <= y0 or b0 >= y1:
        return [r]
    out = []
    if a0 > x0:
        out.append((x0, y0, a0, y1))
    if a1 < x1:
        out.append((a1, y0, x1, y1))
    mx0, mx1 = max(x0, a0), min(x1, a1)
    if b0 > y0:
        out.append((mx0, y0, mx1, b0))
    if b1 < y1:
        out.append((mx0, b1, mx1, y1))
    return [q for q in out if q[2] - q[0] > 1e-6 and q[3] - q[1] > 1e-6]


def disjoint(regions):
    """The same area as `regions`, but as rectangles that do not overlap.

    The regions handed to build() deliberately overlap - each room is grown
    past its own walls and every threshold is a strip laid across two rooms -
    which is right for the fingers, because a finger is clipped to a region and
    two clips of the same finger land in the same place.  It is wrong for the
    sub-floor, where two slabs in the same place would put two top faces at the
    same height with nothing to break the tie.
    """
    out, done = [], []
    for r in regions:
        pend = [r]
        for p in done:
            nxt = []
            for q in pend:
                nxt += _sub_rect(q, p)
            pend = nxt
        out += pend
        done.append(r)
    return out


def _area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) * 0.5


def build(regions, name="Floor_Parquet", cname="Shell", z=0.0, seed=7311,
          phase=(0.0, 0.0)):
    """regions: list of (x0, y0, x1, y1) convex rectangles that tile the floor.

    A piece is inset BEFORE it is clipped, so where two regions abut, the two
    halves butt against each other with no groove between them - otherwise the
    seam between the tiling rectangles would print itself onto the floor as a
    joint line that no real parquet has.

    Under the fingers runs a CONTINUOUS sub-floor, in the same mesh.  A floor of
    separate blocks with real grooves between them is not a floor - it is a
    grille, and this one sat over open space, so the sky came up through every
    joint in the flat as a bright line.  The deck stops 2.6 mm under the finger
    tops, which leaves the grooves reading as joints and makes them opaque.
    """
    rng = random.Random(seed)
    verts, faces, uvs, cols = [], [], [], []
    fw = T / NFING

    bx0 = min(r[0] for r in regions)
    by0 = min(r[1] for r in regions)
    bx1 = max(r[2] for r in regions)
    by1 = max(r[3] for r in regions)

    i0 = int(math.floor((bx0 - phase[0]) / T)) - 1
    i1 = int(math.ceil((bx1 - phase[0]) / T)) + 1
    j0 = int(math.floor((by0 - phase[1]) / T)) - 1
    j1 = int(math.ceil((by1 - phase[1]) / T)) + 1

    def tone():
        # Oak, and a strip floor of this age IS a jumble of boards - but only
        # a little.  Multiplied over the wood shader, so these are gains around
        # 1.0, not colours, and a 2:1 spread (which is what this was) turns a
        # varnished plane into a weave of loose sticks.
        h = rng.uniform(0.058, 0.082)
        s = rng.uniform(0.12, 0.27)
        v = rng.uniform(0.90, 1.08)
        r, g, bb = colorsys.hsv_to_rgb(h, s, min(1.0, v))
        k = rng.uniform(0.93, 1.07)
        return (min(1.45, r * k * 1.30), min(1.45, g * k * 1.14), min(1.45, bb * k * 0.98))

    for i in range(i0, i1):
        for j in range(j0, j1):
            ox, oy = phase[0] + i * T, phase[1] + j * T
            horiz = ((i + j) % 2 == 0)      # checkerboard turn
            for k in range(NFING):
                if horiz:
                    p = [(ox, oy + k * fw), (ox + T, oy + k * fw),
                         (ox + T, oy + (k + 1) * fw), (ox, oy + (k + 1) * fw)]
                    gx, gy = 1.0, 0.0
                else:
                    p = [(ox + k * fw, oy), (ox + (k + 1) * fw, oy),
                         (ox + (k + 1) * fw, oy + T), (ox + k * fw, oy + T)]
                    gx, gy = 0.0, 1.0
                h = JOINT * 0.5
                p = [(p[0][0] + h, p[0][1] + h), (p[1][0] - h, p[1][1] + h),
                     (p[2][0] - h, p[2][1] - h), (p[3][0] + h, p[3][1] - h)]

                for reg in regions:
                    q = _clip(p, reg)
                    if len(q) < 3 or _area(q) < 1.2e-4:
                        continue
                    # A HAIR of lippage per finger - a tenth of a millimetre,
                    # enough for raking window light to find the joints and no
                    # more.  Any deeper and the floor stops reading as one
                    # varnished plane with a pattern in it and starts reading
                    # as loose sticks laid side by side, which is what it did.
                    dz = rng.uniform(-0.00010, 0.00016)
                    ro = (rng.uniform(-11, 11), rng.uniform(-11, 11))
                    t = tone()
                    base = len(verts)
                    n = len(q)
                    for (px, py) in q:
                        verts.append((px, py, z + dz))
                    for (px, py) in q:
                        verts.append((px, py, z + TH + dz))

                    def uv_of(px, py):
                        return (px * (-gy) + py * gx + ro[0], px * gx + py * gy + ro[1])

                    faces.append(tuple(range(base + n, base + 2 * n)))
                    uvs.append([uv_of(*q[m]) for m in range(n)])
                    faces.append(tuple(range(base + n - 1, base - 1, -1)))
                    uvs.append([uv_of(*q[n - 1 - m]) for m in range(n)])
                    for m in range(n):
                        m2 = (m + 1) % n
                        faces.append((base + m, base + m2, base + n + m2, base + n + m))
                        uvs.append([uv_of(*q[m]), uv_of(*q[m2]), uv_of(*q[m2]), uv_of(*q[m])])
                    for _ in range(2 * n):
                        cols.append(t)

    # ---------------------------------------------------------- sub-floor
    dtop = z + TH - DECK
    for (a, b, c, d) in disjoint(regions):
        base = len(verts)
        for zz in (z - SUB, dtop):
            verts.extend([(a, b, zz), (c, b, zz), (c, d, zz), (a, d, zz)])
        for f in ((3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                  (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append(tuple(base + k for k in f))
            uvs.append([(verts[base + k][0], verts[base + k][1]) for k in f])
        for _ in range(8):
            cols.append((0.88, 0.80, 0.70))

    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], [], [list(f) for f in faces])
    me.validate()
    uvl = me.uv_layers.new(name="UVMap")
    li = 0
    for fi, f in enumerate(faces):
        for k in range(len(f)):
            uvl.data[li].uv = uvs[fi][k]
            li += 1
    at = me.color_attributes.new(name="ptint", type='FLOAT_COLOR', domain='POINT')
    for vi in range(len(verts)):
        c = cols[vi]
        at.data[vi].color = (c[0], c[1], c[2], 1.0)
    me.update()
    ob = bpy.data.objects.new(name, me)
    mlib.put(ob, cname)
    mlib.recalc_normals(ob)
    # a third of the joint width - any more and the arris eats the groove and
    # the pattern goes soft
    mlib.bevel(ob, 0.00035, 1, 30, harden=False)
    return ob


def parquet_mat(name="M_Parquet"):
    """Golden-oak mosaic parquet under an old, slightly yellowed satin varnish.
    Grain runs along the finger (UV-driven), tone comes from the per-piece
    attribute, and the varnish adds a broad, dirty gloss that does not follow
    the grain at all - which is what stops it reading as a decal."""
    # Lighter and much less red than the first pass.  Under warm practicals a
    # saturated golden oak goes orange and takes the whole room with it; the
    # set floor is a pale honey oak that reads almost neutral once it is lit.
    # ring=13 over a 61 x 305 finger puts ONE light-to-dark sweep across each
    # piece, so every finger reads as a separate rounded stick and the floor
    # reads as basketwork rather than as boards under varnish.  Fine grain and
    # much less relief: the pattern comes from the LAYOUT, not from each piece
    # being modelled as a cushion.
    return mats.wood(name, ('D8C29E', 'BEA47E', '96805A'), ring=28.0, warp=0.22,
                     rough=(0.19, 0.42), coord='UV', axis='Y', bump=0.07,
                     pore=1.0, tint_attr='ptint', scale=1.0, aniso=0.28,
                     distort=0.8, coat=0.42, grain_relief=0.05)
