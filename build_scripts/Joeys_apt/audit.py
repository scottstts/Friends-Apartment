"""Build checks that run after every rebuild.

The z-fighting on the jog wall was in the scene for two full passes before
anyone looked at it from the one angle that showed it.  That is the failure
mode this file exists to close: coplanar geometry is invisible from almost
every direction and unmissable from one, so it cannot be caught by looking at
renders - it has to be caught by measuring the model.

`solid_overlaps` is the cheap version and catches the case that actually bites:
two SOLIDS occupying the same volume.  Coincident faces between two solids that
merely touch are fine (that is what a corner is); it is shared VOLUME that puts
two surfaces in the same plane with nothing to break the tie.
"""
import bpy
from mathutils import Vector

# Pairs that are supposed to interpenetrate.  Glazing sits inside its own sash;
# a raised panel field is buried in its board; trim is let into its host.  Each
# entry is a pair of name prefixes.
ALLOWED = [
    ("Win_", "Win_"), ("FD_", "FD_"), ("Door_", "Door_"),
    ("Floor_Parquet", "Base_"), ("Floor_Parquet", "Door_"),
    ("Floor_Parquet", "Win_"), ("Floor_Bath", "Bath_Tiling"),
    ("Bath_Tiling", "W_Bath"), ("Bath_Tiling", "W_North"),
    ("Cornice", "Ceiling"), ("Cornice", "W_"),
    ("EXT_", "EXT_"),
]


def _bb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def _allowed(a, b):
    for (p, q) in ALLOWED:
        if (a.startswith(p) and b.startswith(q)) or (a.startswith(q) and b.startswith(p)):
            return True
    return False


def solid_overlaps(prefix="W_", eps=0.004, min_vol=1e-4, report=24):
    """Report pairs of objects whose bounding boxes share real volume.

    Restricted to a prefix by default because walls are the class where an
    overlap is always a bug - two wall solids in the same place means a corner
    was given to both of them, and the shared faces will z-fight.
    """
    objs = [o for o in bpy.data.objects
            if o.type == 'MESH' and o.name.startswith(prefix)]
    boxes = {o.name: _bb(o) for o in objs}
    hits = []
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            a, b = objs[i], objs[j]
            if _allowed(a.name, b.name):
                continue
            (la, ha), (lb, hb) = boxes[a.name], boxes[b.name]
            d = [min(ha[k], hb[k]) - max(la[k], lb[k]) - eps for k in range(3)]
            if all(v > 0 for v in d):
                vol = d[0] * d[1] * d[2]
                if vol > min_vol:
                    hits.append((vol, a.name, b.name, tuple(round(v, 3) for v in d)))
    hits.sort(reverse=True)
    return hits[:report]


def coplanar_risk(eps=0.0012, report=20):
    """Large flat faces from DIFFERENT objects in the same plane, FACING THE
    SAME WAY.  Same-facing is the whole test: two solids butted back to back
    also share a plane, but their faces point away from each other and each is
    buried behind the other's body, so nothing ever rasterises both.  It is two
    surfaces looking the same direction at the same depth that fight - a panel
    laid flat on a wall, a sill sitting exactly on a reveal."""
    faces = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.hide_render:
            continue
        mw = o.matrix_world
        for p in o.data.polygons:
            if p.area < 0.02:
                continue
            n = (mw.to_3x3() @ p.normal).normalized()
            c = mw @ p.center
            # an in-plane basis, so two coplanar faces can be tested for real
            # overlap rather than for their centres happening to be near each
            # other - which flags every mitre in the building as a fault
            u = Vector((0, 0, 1)).cross(n)
            if u.length < 1e-4:
                u = Vector((1, 0, 0)).cross(n)
            u.normalize()
            v = n.cross(u)
            pts = [mw @ o.data.vertices[k].co for k in p.vertices]
            us = [q.dot(u) for q in pts]
            vs = [q.dot(v) for q in pts]
            faces.append((o.name, n, n.dot(c), c, p.area,
                          (min(us), max(us), min(vs), max(vs)), u, v))
    hits = []
    for i in range(len(faces)):
        fa = faces[i]
        for j in range(i + 1, len(faces)):
            fb = faces[j]
            if fa[0] == fb[0] or _allowed(fa[0], fb[0]):
                continue
            if fa[1].dot(fb[1]) < 0.999:
                continue
            if abs(fa[2] - fb[2]) > eps:
                continue
            au, bu = fa[5], fb[5]
            ov_u = min(au[1], bu[1]) - max(au[0], bu[0])
            ov_v = min(au[3], bu[3]) - max(au[2], bu[2])
            if ov_u <= 0.004 or ov_v <= 0.004:
                continue
            hits.append((ov_u * ov_v, fa[0], fb[0],
                         tuple(round(x, 3) for x in fa[3])))
    hits.sort(reverse=True)
    seen, out = set(), []
    for h in hits:
        k = (h[1], h[2])
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
        if len(out) >= report:
            break
    return out


def run(verbose=True):
    w = solid_overlaps("W_")
    c = coplanar_risk()
    if verbose:
        print("--- wall solid overlaps: %d" % len(w))
        for (v, a, b, d) in w:
            print("    %.4f m3  %-14s x %-14s  %s" % (v, a, b, d))
        print("--- coplanar face pairs: %d" % len(c))
        for (ar, a, b, at) in c:
            print("    %.3f m2  %-18s x %-18s at %s" % (ar, a, b, at))
    return w, c
