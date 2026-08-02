"""Walls, ceilings, mouldings and the exposed timber of the kitchen.

Each wall is one closed solid panel whose *inner* face sits exactly on the
room boundary and whose body extends outward, so nothing overlaps and nothing
is coplanar-with-overlap.  Openings are real holes with real reveals.
"""
import bpy, math
from mathutils import Vector, Matrix
import mlib, mats, L


# --------------------------------------------------------------------- walls

def wall(name, p0, p1, z0, z1, t, holes=(), cname="Shell", mat=None,
         mats_extra=None):
    """Wall whose inner face runs p0->p1 (interior on the RIGHT of travel).
    holes: (u0, z0, u1, z1) in wall-local coords measured from p0/floor."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    hh = [(h[0], h[1] - z0, h[2], h[3] - z0) for h in holes]
    ob = mlib.panel_with_holes(name, ln, z1 - z0, t, hh, cname)
    # local x -> (ux,uy,0), local y -> (-uy,ux,0)  (outward), local z -> z
    M = Matrix(((ux, -uy, 0.0, p0[0]),
                (uy, ux, 0.0, p0[1]),
                (0.0, 0.0, 1.0, z0),
                (0.0, 0.0, 0.0, 1.0)))
    ob.data.transform(M)
    ob.data.update()
    mlib.recalc_normals(ob)
    if mat:
        mlib.set_mat(ob, mat)
    if mats_extra:
        for m in mats_extra:
            ob.data.materials.append(m)
    return ob


def _isect(a0, u0, b0, u1):
    den = u0.x * (-u1.y) - u0.y * (-u1.x)
    if abs(den) < 1e-9:
        return b0
    w = b0 - a0
    tt = (w.x * (-u1.y) - w.y * (-u1.x)) / den
    return a0 + u0 * tt


def offset_polyline(pts, d, closed=False):
    """Offset a polyline to its right-hand side by d, mitring the corners."""
    P = [Vector(p) for p in pts]
    n = len(P)
    segs = []
    m = n if closed else n - 1
    for i in range(m):
        a, b = P[i], P[(i + 1) % n]
        u = (b - a).normalized()
        nn = Vector((u.y, -u.x))          # right of travel
        segs.append((a + nn * d, b + nn * d, u))
    out = []
    if closed:
        for i in range(n):
            s_prev = segs[(i - 1) % m]
            s_cur = segs[i % m]
            out.append(_isect(s_prev[0], s_prev[2], s_cur[0], s_cur[2]))
    else:
        out.append(segs[0][0])
        for i in range(len(segs) - 1):
            out.append(_isect(segs[i][0], segs[i][2], segs[i + 1][0], segs[i + 1][2]))
        out.append(segs[-1][1])
    return [(p.x, p.y) for p in out]


def run_molding(name, path, profile, cname="Trim", mat=None, cap=True,
                closed=False):
    """Sweep a closed profile [(z, depth_into_room), ...] along a plan path.
    Interior is on the RIGHT of travel; depth measured into the room."""
    rings = []
    offs = {}
    for (z, d) in profile:
        if d not in offs:
            offs[d] = offset_polyline(path, d, closed)
    npts = len(path)
    for i in range(npts):
        ring = []
        for (z, d) in profile:
            p = offs[d][i]
            ring.append((p[0], p[1], z))
        rings.append(ring)
    ob = mlib._loft(name, rings, close_u=closed, close_v=True, cname=cname,
                    cap_start=cap and not closed, cap_end=cap and not closed)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def panel_moulding(name, cx, cy, cz, w, h, normal, cname="Trim", mat=None,
                   prof=None):
    """Applied rectangular panel moulding on a wall.  normal = outward from
    the wall into the room (unit 2D)."""
    p = prof or [(-0.026, 0.0010), (0.026, 0.0010), (0.026, 0.0062),
                 (0.019, 0.0128), (0.010, 0.0165), (-0.002, 0.0175),
                 (-0.015, 0.0128), (-0.026, 0.0072)]
    ob = mlib.sweep_rect_frame(name, w, h, p, cname)
    # frame is built in XZ with +Y normal -> rotate so +Y maps to `normal`
    ang = math.atan2(normal[1], normal[0]) - math.pi / 2
    ca, sa = math.cos(ang), math.sin(ang)
    M = Matrix(((ca, -sa, 0.0, cx), (sa, ca, 0.0, cy), (0.0, 0.0, 1.0, cz),
                (0.0, 0.0, 0.0, 1.0)))
    ob.data.transform(M)
    mlib.recalc_normals(ob)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


# ------------------------------------------------------------------ profiles

BASE_PROF = [(0.0, 0.0012), (0.0, 0.0215), (0.118, 0.0215), (0.128, 0.0275),
             (0.140, 0.0275), (0.148, 0.0205), (0.155, 0.0110), (0.155, 0.0012)]

RAIL_PROF = [(2.688, 0.0012), (2.688, 0.0295), (2.716, 0.0325),
             (2.734, 0.0270), (2.742, 0.0150), (2.742, 0.0012)]

CROWN_PROF = [(3.086, 0.0012), (3.104, 0.0175), (3.146, 0.0455),
              (3.196, 0.0680), (3.242, 0.0808), (3.2585, 0.0845),
              (3.2585, 0.0012)]

ALCOVE_CROWN = [(p[0] - (L.CZ - L.AL_Z), p[1]) for p in CROWN_PROF]
