"""Geometry audit - the build's unit tests.

Coplanar faces from two different objects are the one defect that always
survives a screenshot check: they look fine from most angles, then flicker
from one.  So the build asserts they do not exist rather than trusting the eye.

    import audit; audit.run()          # everything
    import audit; audit.zfight()       # just the coplanar check, full list

The coplanar test works on TRIANGLES, not polygons, and measures the real
clipped overlap area rather than a bounding-box guess.  Two earlier versions
of this file got that wrong in both directions:

  * bucketing by a quantised plane key without expanding into the neighbouring
    cells meant two genuinely coplanar faces whose normals straddled a cell
    boundary were never compared - silent misses;
  * comparing axis-aligned bounding boxes reported the L-shaped floor slabs as
    overlapping when their outlines only touch along an edge - false alarms
    loud enough to bury the real hits.

Both are fixed here: every triangle registers in all sixteen neighbouring
cells of the 4-D plane grid, so no pair within tolerance can be missed, and
overlap is the true area of one triangle clipped against the other.

Checks:

  zfight       coplanar, SAME-facing, overlapping -> guaranteed z-fighting.
  backtoback   coplanar, opposed.  An object's underside on the floor, a
               lining's back in its reveal.  Both belong to closed solids so a
               nearer face is always hit first.  Reported for information.
  degenerate   zero-area faces, loose vertices, duplicate vertices.
  manifold     edges with other than two faces.
  nomat        meshes with no material.
  lights       every non-SUN light needs a fixture within FIXTURE_R.
  clash        two SOLIDS occupying the same space - a bar stool whose legs
               run through the counter, a chair inside a wall.  This is the
               defect the first version of the audit had no test for, and it
               is not the same thing as a coplanar pair: nothing is level
               with anything, the meshes simply intersect.  It cannot be
               caught by bounding boxes either - every stool's box overlaps
               the counter's box - so it works on real triangle-triangle
               intersection through a BVH.
"""
import bpy, math
from collections import defaultdict
from mathutils import Vector

ANG = 0.0025         # normal-dot tolerance, ~0.13 degrees
DIST = 0.0015        # 1.5 mm - tighter than any deliberate offset in the build
OVERLAP_A = 2e-4     # 2 cm2 of genuinely shared surface before it is a defect
CELL_N = 0.02        # plane-grid cell, normal axes
CELL_D = 0.02        # plane-grid cell, distance axis
FIXTURE_R = 0.30
CLASH_DEPTH = 0.030  # how far two solids must run into one another to count

SKIP = ()


def _meshes(collections=None):
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.data.polygons or o.name in SKIP:
            continue
        if collections is not None:
            cn = o.users_collection[0].name if o.users_collection else ""
            if cn not in collections:
                continue
        out.append(o)
    return out


def _tris(o):
    """World-space triangles: (normal, d, [p0,p1,p2], area)."""
    me = o.data
    me.calc_loop_triangles()
    mw = o.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    out = []
    for t in me.loop_triangles:
        a, b, c = (vs[i] for i in t.vertices)
        n = (b - a).cross(c - a)
        ar = n.length * 0.5
        if ar < 1e-9:
            continue
        n = n / (ar * 2.0)
        out.append((n, n.dot(a), (a, b, c), ar))
    return out


def _basis(n):
    a = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(a).normalized()
    return u, n.cross(u).normalized()


def _clip_area(P, Q):
    """Area of convex polygon P clipped by convex triangle Q (2-D)."""
    out = list(P)
    n = len(Q)
    # orient Q counter-clockwise so the half-plane test has a fixed sign
    s = 0.0
    for i in range(n):
        x0, y0 = Q[i]
        x1, y1 = Q[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    if s < 0:
        Q = Q[::-1]
    for i in range(n):
        ax, ay = Q[i]
        bx, by = Q[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        inp, out = out, []
        if not inp:
            return 0.0
        prev = inp[-1]
        dprev = ex * (prev[1] - ay) - ey * (prev[0] - ax)
        for cur in inp:
            dcur = ex * (cur[1] - ay) - ey * (cur[0] - ax)
            if dcur >= 0:
                if dprev < 0:
                    t = dprev / (dprev - dcur)
                    out.append((prev[0] + (cur[0] - prev[0]) * t,
                                prev[1] + (cur[1] - prev[1]) * t))
                out.append(cur)
            elif dprev >= 0:
                t = dprev / (dprev - dcur)
                out.append((prev[0] + (cur[0] - prev[0]) * t,
                            prev[1] + (cur[1] - prev[1]) * t))
            prev, dprev = cur, dcur
    if len(out) < 3:
        return 0.0
    a = 0.0
    for i in range(len(out)):
        x0, y0 = out[i]
        x1, y1 = out[(i + 1) % len(out)]
        a += x0 * y1 - x1 * y0
    return abs(a) * 0.5


def _canon(n, d):
    """A sign-independent (normal, distance) so a plane has one key whichever
    way its two faces point."""
    if (n.z < -1e-9 or (abs(n.z) <= 1e-9 and
                        (n.y < -1e-9 or (abs(n.y) <= 1e-9 and n.x < 0)))):
        return -n, -d
    return n, d


def zfight(collections=None, facing='same', limit=None, verbose=False):
    tris = []
    for o in _meshes(collections):
        for (n, d, p, ar) in _tris(o):
            tris.append((o.name, n, d, p, ar))

    grid = defaultdict(list)
    for idx, (nm, n, d, p, ar) in enumerate(tris):
        cn, cd = _canon(n, d)
        base = (cn.x / CELL_N, cn.y / CELL_N, cn.z / CELL_N, cd / CELL_D)
        f = [math.floor(b) for b in base]
        # register in all sixteen neighbouring cells: two triangles within
        # tolerance then always share at least one bucket, whatever boundary
        # they happen to straddle
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    for e in (0, 1):
                        grid[(f[0] + a, f[1] + b, f[2] + c, f[3] + e)].append(idx)

    seen = set()
    hits = {}
    for cell, items in grid.items():
        if len(items) < 2:
            continue
        for i in range(len(items)):
            ii = items[i]
            ni, di, pi, ari = tris[ii][1], tris[ii][2], tris[ii][3], tris[ii][4]
            for j in range(i + 1, len(items)):
                jj = items[j]
                if tris[ii][0] == tris[jj][0]:
                    continue
                pair = (ii, jj) if ii < jj else (jj, ii)
                if pair in seen:
                    continue
                seen.add(pair)
                nj, dj, pj = tris[jj][1], tris[jj][2], tris[jj][3]
                dot = ni.dot(nj)
                if abs(dot) < 1 - ANG:
                    continue
                if (dot > 0) != (facing == 'same'):
                    continue
                # signed distance between the two planes, along a shared normal
                if abs(ni.dot(pj[0]) - di) > DIST:
                    continue
                u, v = _basis(ni)
                A = [(q.dot(u), q.dot(v)) for q in pi]
                B = [(q.dot(u), q.dot(v)) for q in pj]
                ov = _clip_area(A, B)
                if ov < OVERLAP_A:
                    continue
                k = tuple(sorted((tris[ii][0], tris[jj][0])))
                cur = hits.get(k)
                ctr = (pi[0] + pi[1] + pi[2]) / 3.0
                if cur is None:
                    hits[k] = [ov, tuple(round(x, 3) for x in ctr)]
                else:
                    cur[0] += ov
    out = sorted(((a, b, v[0], v[1]) for (a, b), v in hits.items()),
                 key=lambda r: -r[2])
    if verbose:
        print("%s-facing coplanar pairs: %d" % (facing, len(out)))
        for r in (out if limit is None else out[:limit]):
            print("   %9.1f cm2  %-28s %-28s @ %s"
                  % (r[2] * 1e4, r[0][:28], r[1][:28], r[3]))
    return out


def degenerate(collections=None):
    bad = []
    for o in _meshes(collections):
        me = o.data
        z = sum(1 for p in me.polygons if p.area < 1e-9)
        used = set()
        for p in me.polygons:
            used.update(p.vertices)
        loose = len(me.vertices) - len(used)
        seen, dup = set(), 0
        for v in me.vertices:
            k = (round(v.co.x, 5), round(v.co.y, 5), round(v.co.z, 5))
            if k in seen:
                dup += 1
            seen.add(k)
        if z or loose or dup:
            bad.append((o.name, z, loose, dup))
    return bad


def manifold(collections=None):
    bad = []
    for o in _meshes(collections):
        cnt = defaultdict(int)
        for p in o.data.polygons:
            vs = list(p.vertices)
            for i in range(len(vs)):
                a, b = vs[i], vs[(i + 1) % len(vs)]
                cnt[(min(a, b), max(a, b))] += 1
        op = sum(1 for c in cnt.values() if c == 1)
        mu = sum(1 for c in cnt.values() if c > 2)
        if op or mu:
            bad.append((o.name, op, mu))
    return bad


def nomat(collections=None):
    return [o.name for o in _meshes(collections)
            if not o.data.materials or all(m is None for m in o.data.materials)]


def lights():
    bad = []
    meshes = _meshes()
    for o in bpy.data.objects:
        if o.type != 'LIGHT' or o.data.type == 'SUN':
            continue
        p = o.matrix_world.translation
        near = 1e9
        for m in meshes:
            mw = m.matrix_world
            bb = [mw @ Vector(c) for c in m.bound_box]
            lo = Vector((min(b.x for b in bb), min(b.y for b in bb),
                         min(b.z for b in bb)))
            hi = Vector((max(b.x for b in bb), max(b.y for b in bb),
                         max(b.z for b in bb)))
            near = min(near, Vector((max(lo.x - p.x, 0, p.x - hi.x),
                                     max(lo.y - p.y, 0, p.y - hi.y),
                                     max(lo.z - p.z, 0, p.z - hi.z))).length)
        if near > FIXTURE_R:
            bad.append((o.name, round(near, 3)))
    return bad


# Things that are BUILT to occupy the same space.  Upholstery sits inside its
# own frame, a cushion sits in its own deck, trim is bedded into plaster, a
# wall runs into the wall it turns the corner with.  Each entry is a pair of
# name prefixes (either order) that may intersect; everything else may not.
CLASH_OK = [
    ("Wall_", "Wall_"), ("Wall_", "Pier_"), ("Wall_", "Floor_"),
    ("Wall_", "Ceil_"), ("Wall_", "Beam_"), ("Wall_", "Skirt_"),
    ("Wall_", "Dado_"), ("Wall_", "Column_"), ("Pier_", "Beam_"),
    ("Pier_", "Floor_"), ("Pier_", "Ceil_"), ("Floor_", "Kerb_"),
    ("Floor_", "Floor_"), ("Floor_", "Column_"), ("Floor_", "Skirt_"),
    ("Beam_", "Beam_"), ("Beam_", "Ceil_"), ("Beam_", "Column_"),
    ("Ceil_", "Column_"), ("Skirt_", "Dado_"),
    # fitted joinery stands against the wall it is fitted to, over the
    # skirting and dado that run on behind it - as built joinery does
    ("Back_", "Skirt_"), ("Back_", "Dado_"), ("Back_", "Wall_"),
    ("Counter_", "Skirt_"), ("Counter_", "Dado_"), ("Counter_", "Wall_"),
    ("Chalk_", "Wall_"), ("Menu_", "Wall_"),
    # stock standing on the shelf it was put on
    ("Back_", "Tin"), ("Back_", "Jar"), ("Back_", "Bag"), ("Back_", "Beans"),
    ("Back_", "Cupstack"), ("Back_", "TJar"), ("Back_", "Brew"),
    ("Back_", "Gr_"), ("Back_", "Urn_"), ("Back_", "Espresso"),
    ("Counter_", "RTin"), ("Counter_", "RBag"), ("Counter_", "Cake"),
    ("Counter_", "Till"),
]


def _clash_allowed(a, b):
    for (p, q) in CLASH_OK:
        if (a.startswith(p) and b.startswith(q)) or \
           (a.startswith(q) and b.startswith(p)):
            return True
    # two parts of the SAME piece: same name up to the last underscore
    ra, rb = a.rsplit("_", 1)[0], b.rsplit("_", 1)[0]
    return ra == rb or a.startswith(rb) or b.startswith(ra)


def clash(collections=None, limit=None, verbose=False):
    """Objects whose meshes genuinely intersect.

    BVH-tree overlap, then a real triangle-triangle test, so two parts that
    merely touch along an edge are not reported.  `n` is how many triangle
    pairs cross - one or two is a graze, hundreds is one solid buried in
    another."""
    from mathutils.bvhtree import BVHTree
    obs = _meshes(collections)
    dg = bpy.context.evaluated_depsgraph_get()
    trees, boxes = {}, {}
    for o in obs:
        try:
            trees[o.name] = BVHTree.FromObject(o, dg)
        except Exception:
            continue
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        boxes[o.name] = (Vector((min(p.x for p in pts), min(p.y for p in pts),
                                 min(p.z for p in pts))),
                         Vector((max(p.x for p in pts), max(p.y for p in pts),
                                 max(p.z for p in pts))))
    names = sorted(trees)
    out = []
    for i, a in enumerate(names):
        a0, a1 = boxes[a]
        for b in names[i + 1:]:
            b0, b1 = boxes[b]
            if (a1.x < b0.x or b1.x < a0.x or a1.y < b0.y or b1.y < a0.y
                    or a1.z < b0.z or b1.z < a0.z):
                continue
            if _clash_allowed(a, b):
                continue
            # A cup standing on a table shares a millimetre of its own base
            # with the top, and a curtain brushing a settee shares a hair.
            # Neither is a modelling error.  What matters is how DEEP the two
            # solids run into one another, so the shared box has to be thick
            # in its thinnest direction before this is worth reporting.
            lo = Vector((max(a0.x, b0.x), max(a0.y, b0.y), max(a0.z, b0.z)))
            hi = Vector((min(a1.x, b1.x), min(a1.y, b1.y), min(a1.z, b1.z)))
            # ...but the threshold has to SCALE.  A flat constant of 30 mm is
            # blind to thin things: a 16 mm saucer sunk halfway into a table
            # shares a box only 8 mm thick and sailed straight through the
            # test, which is exactly the defect it was written to catch.  So
            # the bar is 30 mm OR a third of the thinner object's own least
            # dimension, whichever is smaller.
            ta = min(a1.x - a0.x, a1.y - a0.y, a1.z - a0.z)
            tb = min(b1.x - b0.x, b1.y - b0.y, b1.z - b0.z)
            lim = min(CLASH_DEPTH, max(0.004, 0.34 * min(ta, tb)))
            if min(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z) < lim:
                continue
            ov = trees[a].overlap(trees[b])
            if len(ov) > 2:
                out.append((len(ov), a, b))
    out.sort(reverse=True)
    if verbose:
        for (n, a, b) in out[:(limit or 40)]:
            print("   %6d tri  %-28s %-28s" % (n, a, b))
    return out


def unsupported(collections=('Counter', 'Dressing', 'Furniture'),
                limit=None, verbose=False, gap=0.045):
    """Objects standing on nothing.

    The other half of the placement question, and the half that let a cake
    dome hang over the edge of the counter and a saucer sit on air.  It does
    not use the bounding box - a chair's box corners are past its legs and a
    bouquet's are past its vase.  It uses the object's own DOWNWARD faces at
    its lowest level, which is exactly the set of feet it actually stands on,
    and asks whether there is anything under each of them."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for o in _meshes(collections):
        me = o.data
        mw = o.matrix_world
        zs = [(mw @ v.co).z for v in me.vertices]
        if not zs:
            continue
        z0 = min(zs)
        feet = []
        for p in me.polygons:
            c = mw @ p.center
            n = (mw.to_3x3() @ p.normal).normalized()
            if c.z - z0 < 0.006 and n.z < -0.5:
                feet.append(c)
        if not feet or len(feet) > 400:
            continue
        miss = 0
        for c in feet:
            org = Vector((c.x, c.y, c.z - 0.0012))
            hit = sc.ray_cast(dg, org, Vector((0, 0, -1)), distance=gap)[0]
            if not hit:
                miss += 1
        if miss and miss * 2 >= len(feet):
            out.append((round(miss / float(len(feet)), 2), o.name, round(z0, 3)))
    out.sort(reverse=True)
    if verbose:
        for (f, nm, z) in out[:(limit or 30)]:
            print("   %4.0f%% of its feet on air  %-28s z=%.3f" % (f * 100, nm, z))
    return out


def run(collections=None, limit=None):
    print("=" * 76)
    print("AUDIT   %d meshes" % len(_meshes(collections)))
    print("-" * 76)
    zf = zfight(collections, 'same', limit, verbose=True)
    bb = zfight(collections, 'back')
    print("back-to-back pairs (harmless): %d" % len(bb))
    dg = degenerate(collections)
    print("degenerate    : %d" % len(dg))
    for r in dg[:20]:
        print("   %-32s zero=%d loose=%d dup=%d" % r)
    mf = manifold(collections)
    print("non-manifold  : %d" % len(mf))
    for r in mf[:20]:
        print("   %-32s open=%d multi=%d" % r)
    nm = nomat(collections)
    print("no material   : %d  %s" % (len(nm), nm[:8]))
    li = lights()
    print("unjust lights : %d  %s" % (len(li), li[:8]))
    cl = clash(collections, limit, verbose=True)
    print("interpenetrate: %d" % len(cl))
    us = unsupported(verbose=True, limit=limit)
    print("unsupported   : %d" % len(us))
    print("=" * 76)
    return {'zfight': zf, 'back': bb, 'degenerate': dg, 'manifold': mf,
            'nomat': nm, 'lights': li, 'clash': cl, 'unsupported': us}
