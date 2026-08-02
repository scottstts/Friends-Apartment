"""Wall, ceiling and moulding solids.

Every wall is one closed solid whose INNER face lands exactly on its line in
L.py, so a piece of furniture pushed against a wall touches the number it was
given.  Openings are cut as part of the vertex grid rather than booleaned in
afterwards, which means the reveals round every window and door are real,
manifold and free of the stray interior faces a failed boolean leaves behind.

Applied trim - baseboard, panel mouldings, pilasters, casings - is always its
own solid standing proud of the wall face.  Nothing in this build is a decal
lying in the same plane as its host, because two coplanar surfaces are exactly
what the depth buffer cannot resolve.
"""
import bpy, math
from mathutils import Vector
import mlib, mats, L


def to_wall(obj, p0, p1, u0=0.0, z0=0.0, out=False):
    """Map a mesh built in the XZ plane onto the wall running p0 -> p1 of a CCW
    room outline.  x runs along the wall from u0, z is up, and y is either:

      out=False - INTO the room.  For applied trim: panel mouldings, anything
                  that stands proud of the inner face.
      out=True  - into the WALL, the same direction `wall()` grows.  For
                  anything that spans the thickness: door and window linings,
                  the leaf itself, glazing.

    One flag rather than two functions, because getting it wrong is silent: a
    door lining built with the trim convention lands wholly inside the room,
    hanging in mid-air in front of its own opening."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    tx, ty = dx / ln, dy / ln
    nx, ny = (ty, -tx) if out else (-ty, tx)
    for v in obj.data.vertices:
        x, y, z = v.co.x + u0, v.co.y, v.co.z
        v.co = Vector((p0[0] + tx * x + nx * y, p0[1] + ty * x + ny * y, z0 + z))
    obj.data.update()
    mlib.recalc_normals(obj)
    return obj


def wall(name, p0, p1, th, z0, z1, holes=(), cname="Shell"):
    """A wall solid.  p0 -> p1 is the inner face, walked CCW round the room, so
    the solid grows outward (to the right of travel).  holes are (u0, z0, u1,
    z1) in the wall's own coordinates, u measured from p0 and z from the floor.
    """
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    tx, ty = dx / ln, dy / ln
    nx, ny = ty, -tx          # outward
    hh = [(h[0], h[1] - z0, h[2], h[3] - z0) for h in holes]
    ob = mlib.panel_with_holes(name, ln, z1 - z0, th, hh, cname)
    for v in ob.data.vertices:
        x, y, z = v.co.x, v.co.y, v.co.z
        v.co = Vector((p0[0] + tx * x + nx * y, p0[1] + ty * x + ny * y, z0 + z))
    obj_update(ob)
    return ob


def obj_update(ob):
    ob.data.update()
    mlib.recalc_normals(ob)
    return ob


# ---------------------------------------------------------------- profiles

# Every applied moulding is let 2 mm INTO its host surface.  A back face laid
# exactly on the wall plane is coplanar with it, and coplanar is the one thing
# the depth buffer cannot resolve - it shows up as a shimmering seam along the
# whole length of the run at grazing angles.  Two millimetres is invisible and
# makes the fault impossible.
SINK = 0.002


def base_profile(h=None, t=None):
    """Baseboard: a plain square-edged board with a small bead cap, which is
    what the set actually has.  a is measured INTO the room, b is up."""
    h = L.BASE_H if h is None else h
    t = L.BASE_T if t is None else t
    return [(-SINK, 0.0), (t, 0.0), (t, h - 0.030),
            (t * 0.86, h - 0.020), (t * 0.86, h - 0.012),
            (t * 0.40, h - 0.002), (-SINK, h)]


def panel_profile():
    """Applied panel moulding: a small ogee, 46 mm on the wall, 15 mm proud."""
    return [(0.000, -SINK), (0.046, -SINK), (0.046, 0.006),
            (0.033, 0.012), (0.026, 0.015), (0.013, 0.015), (0.004, 0.009)]


def casing_profile(w=0.115, d=0.021):
    """Door / window architrave: a flat board with a stepped outer edge."""
    return [(0.0, -SINK), (w, -SINK), (w, d * 0.55), (w * 0.90, d * 0.72),
            (w * 0.90, d), (w * 0.10, d), (0.0, d * 0.80)]


def cornice_profile(h=0.055, d=0.035):
    """A modest cove where wall meets ceiling.  The photographs show no crown -
    the set has no ceiling at all - but this build does have one, and a raw
    butt joint between two painted planes is the one thing a real room never
    has.  Kept small enough to read as a shadow line, not as grandeur."""
    return [(-SINK, SINK), (-SINK, -h), (d * 0.30, -h * 0.86), (d * 0.62, -h * 0.55),
            (d * 0.86, -h * 0.22), (d, SINK)]


# ---------------------------------------------------------------- pieces

def trim_run(path, a=0.0, b=0.0):
    """Pull a moulding run back from each end along its own direction."""
    p = [tuple(q) for q in path]
    if a:
        dx, dy = p[1][0] - p[0][0], p[1][1] - p[0][1]
        ln = math.hypot(dx, dy)
        p[0] = (p[0][0] + dx / ln * a, p[0][1] + dy / ln * a)
    if b:
        dx, dy = p[-1][0] - p[-2][0], p[-1][1] - p[-2][1]
        ln = math.hypot(dx, dy)
        p[-1] = (p[-1][0] - dx / ln * b, p[-1][1] - dy / ln * b)
    return p


def baseboard(name, path, cname="Shell", h=None, t=None):
    """`path` is walked CLOCKWISE round the room, which puts the sweep's
    outward normal into the room where the board belongs.  Corners inside a run
    are mitred; the ends are cut square, so a run can die into a door casing or
    a pilaster plinth without either one having to know about the other."""
    ob = mlib.sweep_loop(name, path, base_profile(h, t), cname=cname, close=False)
    mlib.bevel(ob, 0.0015, 1, 34, harden=False)
    return ob


def wall_panel(name, p0, p1, u_c, z_c, w, h, cname="Shell"):
    """One applied panel moulding, centred at (u_c, z_c) on the wall p0 -> p1."""
    ob = mlib.sweep_rect_frame(name, w, h, panel_profile(), cname=cname,
                               center=(u_c, z_c))
    return to_wall(ob, p0, p1)


def pilaster(name, p0, p1, u_c, w=0.34, d=0.085, z1=None, cname="Shell"):
    """A shallow pier standing proud of the wall, with its own plinth block at
    the bottom - which is how the baseboard runs get to die into something
    instead of ploughing through it."""
    z1 = L.CZ if z1 is None else z1
    hw = w * 0.5
    shaft = mlib.prism_xz(name, [(u_c - hw, 0.0), (u_c + hw, 0.0),
                                 (u_c + hw, z1), (u_c - hw, z1)], 0.0, d, cname)
    # prism_xz builds in (x, z) extruded along Y; rebuild as a proper box
    bpy.data.objects.remove(shaft, do_unlink=True)
    pb = L.BASE_T + 0.012
    ph = L.BASE_H + 0.020
    shaft = mlib.box(name, u_c - hw, 0.0, ph, u_c + hw, d, z1, cname)
    plinth = mlib.box(name + "_plinth", u_c - hw - 0.014, 0.0, 0.0,
                      u_c + hw + 0.014, d + pb, ph, cname)
    cap = mlib.box(name + "_cap", u_c - hw - 0.020, 0.0, z1 - 0.075,
                   u_c + hw + 0.020, d + 0.022, z1, cname)
    ob = mlib.join([shaft, plinth, cap], name, cname)
    mlib.bevel(ob, 0.003, 2, 40)
    return to_wall(ob, p0, p1)


def ceiling(name, outline, z, th=0.14, cname="Shell"):
    ob = mlib.prism(name, outline, z, z + th, cname)
    return ob


def cornice(name, path, z, cname="Shell"):
    ob = mlib.sweep_loop(name, path, cornice_profile(), cname=cname, close=False)
    mlib.translate(ob, (0, 0, z))
    return ob
