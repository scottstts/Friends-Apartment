"""Wall tiling, as real geometry - one slab per tile.

A projected tile texture cannot survive an inside corner: the pattern is keyed
to world position, so the course lines on two walls meeting at ninety degrees
land wherever they land, and the joint you see running into the corner does not
come out of it.  It also cannot make a clean top edge, because there is no such
thing as a half tile in a texture - the wainscot just stops mid-course.

Real tiles fix both by construction.  The grid starts AT the corner, so every
corner gets a whole tile; the height is snapped to a whole number of courses,
so the top edge is a joint rather than a cut; and the run gets a bullnose cap
that is its own solid, standing proud, throwing its own shadow.
"""
import bpy, math
import mlib, mats, L
from s_walls import to_wall

TILE = 0.104
JOINT = 0.0048
PITCH = TILE + JOINT
TH = 0.013                # how far the tiling stands off the plaster
SINK = 0.002


def courses(h):
    """Snap a height to a whole number of courses, so the top of a run is a
    joint line and not a row of slivers."""
    return max(1, int(round(h / PITCH)))


def height(n):
    return n * PITCH - JOINT


def field(name, p0, p1, u0, u1, z0, ncourse, cname="Shell", cap=True,
          th=TH, start_u=None):
    """Tile the wall p0 -> p1 between u0 and u1, `ncourse` courses tall.

    `start_u` is where the grid's origin sits - pass the corner the tiling
    runs FROM so that corner gets a whole tile and the cut lands in the middle
    of the run, where nothing meets it.
    """
    su = u0 if start_u is None else start_u
    z1 = z0 + height(ncourse)
    j = JOINT * 0.5
    verts, faces = [], []

    def slab(a, b, c, d):
        if b - a < 0.004 or d - c < 0.004:
            return
        base = len(verts)
        for (yy) in (-SINK, th):
            verts.extend([(a, yy, c), (b, yy, c), (b, yy, d), (a, yy, d)])
        faces.extend([(base + 3, base + 2, base + 1, base + 0),
                      (base + 4, base + 5, base + 6, base + 7),
                      (base + 0, base + 1, base + 5, base + 4),
                      (base + 1, base + 2, base + 6, base + 5),
                      (base + 2, base + 3, base + 7, base + 6),
                      (base + 3, base + 0, base + 4, base + 7)])

    i0 = int(math.floor((u0 - su) / PITCH))
    i1 = int(math.ceil((u1 - su) / PITCH))
    for i in range(i0, i1 + 1):
        a = su + i * PITCH + j
        b = a + TILE
        a, b = max(a, u0), min(b, u1)
        for k in range(ncourse):
            c = z0 + k * PITCH + j
            slab(a, b, c, min(c + TILE, z1))

    ob = mlib.mesh_obj(name, verts, faces, cname)
    mlib.recalc_normals(ob)
    mlib.bevel(ob, 0.0012, 2, 40, harden=False)
    out = [to_wall(ob, p0, p1)]

    if cap:
        # bullnose: a rounded capping tile sitting on the last course, proud of
        # the field so the wainscot ends on an edge instead of a raw cut
        cp = mlib.box(name + "_cap", u0, -SINK, z1, u1, th + 0.006, z1 + 0.021,
                      cname)
        mlib.bevel(cp, 0.006, 3, 34)
        mlib.smooth_shade(cp, 40)
        out.append(to_wall(cp, p0, p1))
    return out


def stop_bead(name, p0, p1, u, z0, z1, cname="Shell", th=TH):
    """A vertical bullnose closing the end of a run - what a tiler puts where
    a full-height panel steps down to a wainscot."""
    ob = mlib.box(name, u, -SINK, z0, u + 0.021, th + 0.006, z1, cname)
    mlib.bevel(ob, 0.006, 3, 34)
    mlib.smooth_shade(ob, 40)
    return to_wall(ob, p0, p1)


def tile_mats():
    mats.ceramic("M_BathTileGlaze", 'E7EAE3', rough=0.075, pitch=PITCH)
    return mats.get("M_BathTileGlaze")
