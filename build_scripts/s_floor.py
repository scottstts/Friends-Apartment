"""Parquet floor - real geometry, one slab per parquet piece.

Tile module (matches the set's chevron/diamond parquet): a square laid at 45
degrees to the walls, framed by four mitred strips, with a lozenge in the
middle and four corner triangles.  Every piece is inset by half a joint so the
grooves are real, gets its own grain direction via generated UVs, and its own
tonal jitter via a colour attribute.
"""
import bpy, bmesh, math, random
from mathutils import Vector
import mlib, mats, L


def _inset(poly, d):
    """Inward mitre offset of a convex CCW polygon."""
    n = len(poly)
    out = []
    for i in range(n):
        p = Vector(poly[i] + (0,))
        a = Vector(poly[i - 1] + (0,))
        b = Vector(poly[(i + 1) % n] + (0,))
        e0 = (p - a).normalized()
        e1 = (b - p).normalized()
        # inward normals for CCW polygon
        n0 = Vector((-e0.y, e0.x, 0))
        n1 = Vector((-e1.y, e1.x, 0))
        bis = (n0 + n1)
        if bis.length < 1e-6:
            bis = n0
        bis.normalize()
        cosh = max(0.2, bis.dot(n0))
        q = p + bis * (d / cosh)
        out.append((q.x, q.y))
    return out


def tile_pieces(b=0.152):
    """Pieces of the unit tile in (u,v) 0..1, CCW, with grain direction."""
    U, V = 1.0, 1.0
    i0, i1 = b, 1 - b
    P = []
    # four mitred border strips
    P.append(([(0, 0), (U, 0), (i1, b), (b, b)], (1, 0), 'strip'))
    P.append(([(U, 0), (U, V), (i1, i1), (i1, b)], (0, 1), 'strip'))
    P.append(([(U, V), (0, V), (b, i1), (i1, i1)], (1, 0), 'strip'))
    P.append(([(0, V), (0, 0), (b, b), (b, i1)], (0, 1), 'strip'))
    # central lozenge
    mid = 0.5
    P.append(([(mid, b), (i1, mid), (mid, i1), (b, mid)], (0.7071, 0.7071), 'diamond'))
    # four corner triangles
    P.append(([(b, b), (mid, b), (b, mid)], (0.7071, -0.7071), 'corner'))
    P.append(([(i1, b), (i1, mid), (mid, b)], (0.7071, 0.7071), 'corner'))
    P.append(([(i1, i1), (mid, i1), (i1, mid)], (0.7071, -0.7071), 'corner'))
    P.append(([(b, i1), (b, mid), (mid, i1)], (0.7071, 0.7071), 'corner'))
    return P


def build(x0, y0, x1, y1, T=0.445, gap=0.0014, th=0.0095, ang=math.radians(45.0),
          name="Floor_Parquet", cname="Shell"):
    ca, sa = math.cos(ang), math.sin(ang)

    def to_world(u, v):
        return (u * ca - v * sa, u * sa + v * ca)

    def to_uv(x, y):
        return (x * ca + y * sa, -x * sa + y * ca)

    us, vs = [], []
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        u, v = to_uv(x, y)
        us.append(u)
        vs.append(v)
    ui0, ui1 = int(math.floor(min(us) / T)) - 1, int(math.ceil(max(us) / T)) + 1
    vj0, vj1 = int(math.floor(min(vs) / T)) - 1, int(math.ceil(max(vs) / T)) + 1

    pieces = tile_pieces()
    verts, faces, uvs, cols = [], [], [], []
    rng = random.Random(20240)

    # oak tonal palette: multiplier tints per piece
    def tint():
        h = rng.uniform(0.055, 0.085)
        s = rng.uniform(0.12, 0.42)
        v = rng.uniform(0.72, 1.18)
        import colorsys
        r, g, bb = colorsys.hsv_to_rgb(h, s, min(1.0, v))
        k = rng.uniform(0.80, 1.15)
        return (min(1.4, r * k * 1.25), min(1.4, g * k * 1.12), min(1.4, bb * k))

    for i in range(ui0, ui1):
        for j in range(vj0, vj1):
            ou, ov = i * T, j * T
            for (poly, gd, kind) in pieces:
                wp = [to_world(ou + p[0] * T, ov + p[1] * T) for p in poly]
                cx = sum(p[0] for p in wp) / len(wp)
                cy = sum(p[1] for p in wp) / len(wp)
                if not (x0 - 0.35 < cx < x1 + 0.35 and y0 - 0.35 < cy < y1 + 0.35):
                    continue
                wp = _inset(wp, gap * 0.5)
                n = len(wp)
                base = len(verts)
                for (px, py) in wp:
                    verts.append((px, py, 0.0))
                for (px, py) in wp:
                    verts.append((px, py, th))
                # grain axis in world space
                gx = gd[0] * ca - gd[1] * sa
                gy = gd[0] * sa + gd[1] * ca
                ro = (rng.uniform(-9, 9), rng.uniform(-9, 9))
                t = tint()

                def uv_of(px, py):
                    across = px * (-gy) + py * gx
                    along = px * gx + py * gy
                    return (across + ro[0], along + ro[1])

                top = tuple(range(base + n, base + 2 * n))
                bot = tuple(range(base + n - 1, base - 1, -1))
                faces.append(top)
                uvs.append([uv_of(*wp[k]) for k in range(n)])
                faces.append(bot)
                uvs.append([uv_of(*wp[n - 1 - k]) for k in range(n)])
                for k in range(n):
                    k2 = (k + 1) % n
                    faces.append((base + k, base + k2, base + n + k2, base + n + k))
                    uvs.append([uv_of(*wp[k]), uv_of(*wp[k2]),
                                uv_of(*wp[k2]), uv_of(*wp[k])])
                for _ in range(2 * n):
                    cols.append(t)

    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], [], [list(f) for f in faces])
    me.validate()
    uvl = me.uv_layers.new(name="UVMap")
    li = 0
    for fi, f in enumerate(faces):
        for k in range(len(f)):
            uvl.data[li].uv = uvs[fi][k]
            li += 1
    ca_ = me.color_attributes.new(name="ptint", type='FLOAT_COLOR', domain='POINT')
    for vi in range(len(verts)):
        c = cols[vi]
        ca_.data[vi].color = (c[0], c[1], c[2], 1.0)
    me.update()
    ob = bpy.data.objects.new(name, me)
    mlib.put(ob, cname)
    mlib.recalc_normals(ob)
    mlib.bevel(ob, 0.0007, 1, 30, harden=False)
    return ob
