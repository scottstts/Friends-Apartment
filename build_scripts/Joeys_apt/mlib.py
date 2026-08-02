"""mlib - modelling toolkit for the Apt 19 build.

Everything in this build is real geometry: quad-dominant meshes lofted from
profiles, lathed, or swept along mitred paths.  Nothing is a scaled primitive
and nothing is a coplanar decal - applied trim is always its own solid standing
proud of, or let into, the surface it belongs to, so there is nothing anywhere
for the depth buffer to argue about.

The transform helpers move VERTICES, not objects.  That is deliberate and it
has one consequence that matters constantly: object coordinates and generated
texture coordinates end up in world space, so a procedural material keyed off
`Object` is keyed off where the thing stands in the room.  For wood that is
exactly right - two cabinet doors cut from the same stock should not share a
grain pattern.  For anything that must stay pinned to a curved surface, bake a
parameterisation into an attribute while the mesh is still in its own frame.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

TAU = math.pi * 2.0


# ---------------------------------------------------------------- scene utils

def coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    host = bpy.data.collections.get(parent) if parent else bpy.context.scene.collection
    if host is None:
        host = bpy.context.scene.collection
    if c.name not in [ch.name for ch in host.children]:
        try:
            host.children.link(c)
        except RuntimeError:
            pass
    return c


def put(obj, cname):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll(cname).objects.link(obj)
    return obj


def purge(prefix=None):
    """Delete objects (all, or by name prefix) and then the orphan datablocks."""
    for o in list(bpy.data.objects):
        if prefix is None or o.name.startswith(prefix):
            bpy.data.objects.remove(o, do_unlink=True)
    for _ in range(4):
        for col in (bpy.data.meshes, bpy.data.curves, bpy.data.lights,
                    bpy.data.cameras, bpy.data.node_groups, bpy.data.images):
            for d in list(col):
                if getattr(d, "users", 1) == 0:
                    try:
                        col.remove(d)
                    except Exception:
                        pass


def active(obj):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


# ---------------------------------------------------------------- mesh making

def mesh_obj(name, verts, faces, cname=None, edges=()):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], list(edges), [list(f) for f in faces])
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    put(ob, cname or "Scene")
    return ob


def box(name, x0, y0, z0, x1, y1, z1, cname=None):
    """Axis aligned box: 8 verts, 6 quads, outward normals."""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_obj(name, v, f, cname)


def prism(name, poly, z0, z1, cname=None, flip=False):
    """Extrude a closed 2D polygon given in (x, y) between two z levels."""
    n = len(poly)
    verts = [(p[0], p[1], z0) for p in poly] + [(p[0], p[1], z1) for p in poly]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    ob = mesh_obj(name, verts, faces, cname)
    recalc_normals(ob, flip)
    return ob


def prism_xz(name, poly, y0, y1, cname=None):
    """Extrude a closed 2D polygon given in (x, z) along Y."""
    n = len(poly)
    verts = [(p[0], y0, p[1]) for p in poly] + [(p[0], y1, p[1]) for p in poly]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    ob = mesh_obj(name, verts, faces, cname)
    recalc_normals(ob)
    return ob


def prism_yz(name, poly, x0, x1, cname=None):
    """Extrude a closed 2D polygon given in (y, z) along X."""
    n = len(poly)
    verts = [(x0, p[0], p[1]) for p in poly] + [(x1, p[0], p[1]) for p in poly]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, j + n, i + n))
    ob = mesh_obj(name, verts, faces, cname)
    recalc_normals(ob)
    return ob


def recalc_normals(obj, flip=False):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if flip:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def panel_with_holes(name, w, h, thickness, holes=(), cname=None, origin="corner"):
    """A flat wall panel in the XZ plane (y = 0..thickness) with rectangular
    openings cut in it.  Built as a welded vertex grid, so the result is a
    perfect manifold of quads with real reveals round every hole - no booleans,
    no stray interior faces, no seam for a coplanar cutter to fight over."""
    holes = [tuple(hh) for hh in holes]
    xs = sorted(set([0.0, w] + [v for hh in holes for v in (hh[0], hh[2])]))
    zs = sorted(set([0.0, h] + [v for hh in holes for v in (hh[1], hh[3])]))
    nx, nz = len(xs) - 1, len(zs) - 1

    def solid(i, j):
        if i < 0 or j < 0 or i >= nx or j >= nz:
            return False
        cx0, cx1, cz0, cz1 = xs[i], xs[i + 1], zs[j], zs[j + 1]
        for (a, b, c, d) in holes:
            if a - 1e-6 <= cx0 and cx1 <= c + 1e-6 and b - 1e-6 <= cz0 and cz1 <= d + 1e-6:
                return False
        return True

    idx, verts = {}, []

    def vid(i, j, side):
        k = (i, j, side)
        if k not in idx:
            idx[k] = len(verts)
            verts.append((xs[i], thickness if side else 0.0, zs[j]))
        return idx[k]

    faces = []
    for i in range(nx):
        for j in range(nz):
            if not solid(i, j):
                continue
            a, b = vid(i, j, 0), vid(i + 1, j, 0)
            c, d = vid(i + 1, j + 1, 0), vid(i, j + 1, 0)
            faces.append((a, b, c, d))
            a2, b2 = vid(i, j, 1), vid(i + 1, j, 1)
            c2, d2 = vid(i + 1, j + 1, 1), vid(i, j + 1, 1)
            faces.append((d2, c2, b2, a2))
            if not solid(i, j - 1):
                faces.append((b, a, a2, b2))
            if not solid(i, j + 1):
                faces.append((d, c, c2, d2))
            if not solid(i - 1, j):
                faces.append((a, d, d2, a2))
            if not solid(i + 1, j):
                faces.append((c, b, b2, c2))
    ob = mesh_obj(name, verts, faces, cname)
    recalc_normals(ob)
    if origin == "center":
        for v in ob.data.vertices:
            v.co.x -= w * 0.5
    return ob


# ---------------------------------------------------------------- lathe / loft

def _loft(name, rings, close_u=False, close_v=False, cname=None,
          weld_poles=False, cap_start=False, cap_end=False):
    nu, nv = len(rings), len(rings[0])
    verts, grid = [], []
    poleA = poleB = None
    for ring in rings:
        row = []
        for j, p in enumerate(ring):
            if weld_poles and j == 0 and abs(p[0]) < 1e-9 and abs(p[1]) < 1e-9:
                if poleA is None:
                    poleA = len(verts)
                    verts.append(p)
                row.append(poleA)
                continue
            if weld_poles and j == nv - 1 and abs(p[0]) < 1e-9 and abs(p[1]) < 1e-9:
                if poleB is None:
                    poleB = len(verts)
                    verts.append(p)
                row.append(poleB)
                continue
            row.append(len(verts))
            verts.append(p)
        grid.append(row)
    faces = []
    ulim = nu if close_u else nu - 1
    vlim = nv if close_v else nv - 1
    for i in range(ulim):
        i2 = (i + 1) % nu
        for j in range(vlim):
            j2 = (j + 1) % nv
            uq = []
            for k in (grid[i][j], grid[i2][j], grid[i2][j2], grid[i][j2]):
                if k not in uq:
                    uq.append(k)
            if len(uq) >= 3:
                faces.append(tuple(uq))
    if close_u and not close_v:
        if cap_start and grid[0][0] != grid[1][0]:
            faces.append(tuple(grid[i][0] for i in range(nu - 1, -1, -1)))
        if cap_end and grid[0][nv - 1] != grid[1][nv - 1]:
            faces.append(tuple(grid[i][nv - 1] for i in range(nu)))
    elif close_v and not close_u:
        if cap_start:
            faces.append(tuple(grid[0][j] for j in range(nv - 1, -1, -1)))
        if cap_end:
            faces.append(tuple(grid[nu - 1][j] for j in range(nv)))
    ob = mesh_obj(name, verts, faces, cname)
    recalc_normals(ob)
    return ob


def loft(name, rings, close_u=False, close_v=False, cname=None,
         cap_start=False, cap_end=False):
    return _loft(name, rings, close_u, close_v, cname,
                 cap_start=cap_start, cap_end=cap_end)


def revolve(name, profile, segments=32, arc=TAU, cname=None,
            cap_start=True, cap_end=True, close=None):
    """profile: [(r, z), ...] swept about the Z axis.  r may be 0 at the ends;
    those become single welded pole vertices rather than a fan of coincident
    ones, which is what stops a lathed knob shading like a crushed paper bag."""
    if close is None:
        close = abs(arc - TAU) < 1e-6
    nseg = segments if close else segments + 1
    rings = []
    for s in range(nseg):
        a = arc * (s / segments)
        ca, sa = math.cos(a), math.sin(a)
        rings.append([(r * ca, r * sa, z) for (r, z) in profile])
    return _loft(name, rings, close_u=close, cname=cname, weld_poles=True,
                 cap_start=cap_start, cap_end=cap_end)


def tube_along(name, path, profile, cname=None, close_path=False,
               up=(0, 0, 1), cap=True):
    """Sweep a closed 2D profile along a 3D polyline."""
    P = [Vector(p) for p in path]
    n = len(P)
    rings = []
    for i, p in enumerate(P):
        if i == 0:
            t = (P[1] - P[0]) if not close_path else (P[1] - P[-1])
        elif i == n - 1:
            t = (P[-1] - P[-2]) if not close_path else (P[0] - P[-2])
        else:
            t = P[i + 1] - P[i - 1]
        t.normalize()
        u = Vector(up)
        if abs(t.dot(u)) > 0.999:
            u = Vector((1, 0, 0))
        s = t.cross(u).normalized()
        u2 = s.cross(t).normalized()
        rings.append([tuple(p + s * a + u2 * b) for (a, b) in profile])
    return _loft(name, rings, close_u=close_path, close_v=True, cname=cname,
                 cap_start=cap and not close_path, cap_end=cap and not close_path)


def sweep_rect_frame(name, w, h, profile, cname=None, center=(0.0, 0.0)):
    """Mitred rectangular frame - picture frame, panel moulding, door casing.
    profile: [(a, b)] where a is the outward offset in the frame's plane and b
    is the offset along the frame normal.  Frame lies in XZ, normal +Y.  The
    profile is placed on each corner's 45 degree mitre, so the returns actually
    meet instead of overlapping in the corner the way four butted runs do."""
    hw, hh = w * 0.5, h * 0.5
    cx, cz = center
    corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    dirs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    rings = []
    for (px, pz), (sx, sz) in zip(corners, dirs):
        rings.append([(cx + px + sx * a, b, cz + pz + sz * a) for (a, b) in profile])
    return _loft(name, rings, close_u=True, close_v=True, cname=cname)


def sweep_run(name, p0, p1, profile, cname=None, up=(0, 0, 1)):
    """Straight moulding run between two 3D points.  profile (a, b): a lateral
    (right of travel), b along `up`."""
    A, B = Vector(p0), Vector(p1)
    t = (B - A).normalized()
    u = Vector(up)
    if abs(t.dot(u)) > 0.999:
        u = Vector((0, 1, 0))
    s = t.cross(u).normalized()
    u2 = s.cross(t).normalized()
    rings = [[tuple(p + s * a + u2 * b) for (a, b) in profile] for p in (A, B)]
    return _loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)


def sweep_loop(name, path, profile, cname=None, close=True, up=(0, 0, 1)):
    """Sweep a profile around a closed loop lying in the XY plane (a cornice, a
    baseboard, a plinth).  path: [(x, y)] CCW.  profile: (a, b) where a is
    outward in-plane and b is along +Z."""
    n = len(path)
    rings = []
    for i in range(n):
        p = Vector((path[i][0], path[i][1], 0.0))
        # An open run has no wrap-around neighbour: taking path[-1] as the
        # "previous" point at i = 0 mitres the first end against the far end of
        # the run, which throws the whole start of the moulding sideways.
        if not close and i == 0:
            a, b = p, Vector((path[1][0], path[1][1], 0.0))
        elif not close and i == n - 1:
            a, b = Vector((path[n - 2][0], path[n - 2][1], 0.0)), p
        else:
            a = Vector((path[i - 1][0], path[i - 1][1], 0.0))
            b = Vector((path[(i + 1) % n][0], path[(i + 1) % n][1], 0.0))
        # A TRUE mitre, not a swept average.  Offsetting along the mean tangent
        # rotates the profile through half the corner angle and pulls it in by
        # cos(theta/2): at a right angle that leaves the moulding running
        # diagonally into the wall for 150 mm either side of every corner, and
        # its front face is then neither parallel to the wall nor clear of it.
        # The mitre vector m = (n0 + n1) / (1 + n0.n1) puts the profile exactly
        # on the intersection of the two offset lines - it reduces to n on a
        # straight run and to n0 + n1 at ninety degrees, which is what a mitred
        # corner actually is.
        t0 = (p - a)
        t1 = (b - p)
        if t0.length < 1e-9:
            t0 = t1
        if t1.length < 1e-9:
            t1 = t0
        t0.normalize()
        t1.normalize()
        n0 = Vector((t0.y, -t0.x, 0.0))        # outward for CCW in XY
        n1 = Vector((t1.y, -t1.x, 0.0))
        d = n0.dot(n1)
        m = (n0 + n1) / (1.0 + d) if d > -0.98 else n0
        rings.append([tuple(p + m * aa + Vector((0, 0, bb))) for (aa, bb) in profile])
    return _loft(name, rings, close_u=close, close_v=True, cname=cname,
                 cap_start=not close, cap_end=not close)


# ---------------------------------------------------------------- modifiers

def bevel(obj, amount=0.004, segments=2, angle=40.0, clamp=True, harden=True):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = amount
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.miter_outer = 'MITER_ARC'
    m.use_clamp_overlap = clamp
    m.harden_normals = harden and segments > 1
    return m


def subsurf(obj, levels=2, render=None, simple=False):
    m = obj.modifiers.new("Subdiv", 'SUBSURF')
    m.levels = levels
    m.render_levels = render if render is not None else levels
    if simple:
        m.subdivision_type = 'SIMPLE'
    m.use_limit_surface = False
    return m


def solidify(obj, thickness=0.02, offset=-1, rim=True, even=True):
    m = obj.modifiers.new("Solidify", 'SOLIDIFY')
    m.thickness = thickness
    m.offset = offset
    m.use_rim = rim
    m.use_even_offset = even
    return m


def smooth_shade(obj, angle=32.0):
    """Blender 4.1+ style: every face smooth, edges past `angle` marked sharp."""
    me = obj.data
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    lim = math.radians(angle)
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        e.smooth = e.calc_face_angle() <= lim if len(e.link_faces) == 2 else True
    bm.to_mesh(me)
    bm.free()
    me.update()
    return obj


def flat_shade(obj):
    obj.data.polygons.foreach_set("use_smooth", [False] * len(obj.data.polygons))
    obj.data.update()
    return obj


def apply_all(obj):
    active(obj)
    for m in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
    return obj


def join(objs, name=None, cname=None):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) == 1:
        if name:
            objs[0].name = name
        if cname:
            put(objs[0], cname)
        return objs[0]
    tgt = objs[0]
    active(tgt)
    for o in objs:
        o.select_set(True)
    bpy.ops.object.join()
    if name:
        tgt.name = name
        tgt.data.name = name
    if cname:
        put(tgt, cname)
    return tgt


def boolean(obj, cutter, op='DIFFERENCE', solver='EXACT', apply=True):
    m = obj.modifiers.new("Bool", 'BOOLEAN')
    m.operation = op
    m.object = cutter
    m.solver = solver
    if apply:
        active(obj)
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except Exception:
            pass
        bpy.data.objects.remove(cutter, do_unlink=True)
    return obj


# ---------------------------------------------------------------- transforms
# These move vertices, so a built object always sits in world space already.

def translate(obj, d):
    for v in obj.data.vertices:
        v.co += Vector(d)
    obj.data.update()
    return obj


def rotate_z(obj, ang, pivot=(0, 0)):
    c, s = math.cos(ang), math.sin(ang)
    px, py = pivot
    for v in obj.data.vertices:
        x, y = v.co.x - px, v.co.y - py
        v.co.x = px + x * c - y * s
        v.co.y = py + x * s + y * c
    obj.data.update()
    return obj


def rot_x(obj, ang, pivot=(0, 0, 0)):
    c, s = math.cos(ang), math.sin(ang)
    p = Vector(pivot)
    for v in obj.data.vertices:
        y, z = v.co.y - p.y, v.co.z - p.z
        v.co.y = p.y + y * c - z * s
        v.co.z = p.z + y * s + z * c
    obj.data.update()
    return obj


def rot_y(obj, ang, pivot=(0, 0, 0)):
    c, s = math.cos(ang), math.sin(ang)
    p = Vector(pivot)
    for v in obj.data.vertices:
        x, z = v.co.x - p.x, v.co.z - p.z
        v.co.x = p.x + x * c + z * s
        v.co.z = p.z - x * s + z * c
    obj.data.update()
    return obj


def scale_mesh(obj, s, pivot=(0, 0, 0)):
    s = Vector(s) if hasattr(s, "__len__") else Vector((s, s, s))
    p = Vector(pivot)
    for v in obj.data.vertices:
        v.co = p + Vector(((v.co.x - p.x) * s.x, (v.co.y - p.y) * s.y,
                           (v.co.z - p.z) * s.z))
    obj.data.update()
    return obj


def mirror_x(obj, pivot=0.0):
    dup_ = obj.copy()
    dup_.data = obj.data.copy()
    put(dup_, obj.users_collection[0].name)
    for v in dup_.data.vertices:
        v.co.x = 2 * pivot - v.co.x
    recalc_normals(dup_)
    return join([obj, dup_], obj.name)


def dup(obj, name=None, cname=None, loc=None, rotz=None):
    d = obj.copy()
    d.data = obj.data.copy()
    put(d, cname or obj.users_collection[0].name)
    if name:
        d.name = name
    if loc is not None:
        d.location = Vector(loc)
    if rotz is not None:
        d.rotation_euler[2] = rotz
    return d


def clone_at(obj, name, dxyz=(0, 0, 0), rotz=None, pivot=None, cname=None):
    """Vertex-level copy: duplicate, optionally spin about a pivot, then move.
    Keeps the whole build in one world frame, so object coordinates stay usable
    as a texture space."""
    d = obj.copy()
    d.data = obj.data.copy()
    d.name = name
    d.data.name = name
    put(d, cname or obj.users_collection[0].name)
    if rotz:
        rotate_z(d, rotz, pivot or (0, 0))
    translate(d, dxyz)
    return d


def uv_planar(obj, flip_u=True, name="UVMap"):
    """UVs taken from the object's OWN bounding box, using its two largest
    extents, with V pinned to Z whenever Z is one of them - so a picture is
    always the right way up whichever wall it later gets mapped onto.

    U is flipped by default.  Every wall in `props.wall_place` ends up with the
    viewer's right pointing along the frame's local -X (the piece is either
    spun 180 degrees or viewed from behind its build direction), so an unflipped
    U prints every poster mirrored - which is invisible on an abstract image and
    glaring the moment there is lettering on it.
    """
    vs = [v.co for v in obj.data.vertices]
    mn = [min(c[i] for c in vs) for i in range(3)]
    mx = [max(c[i] for c in vs) for i in range(3)]
    ext = [mx[i] - mn[i] for i in range(3)]
    order = sorted(range(3), key=lambda i: -ext[i])
    a, b = order[0], order[1]
    if 2 in (a, b):
        v_ax = 2
        u_ax = a if a != 2 else b
    else:
        u_ax, v_ax = a, b
    me = obj.data
    uvl = me.uv_layers.get(name) or me.uv_layers.new(name=name)
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        u = (co[u_ax] - mn[u_ax]) / max(ext[u_ax], 1e-9)
        v = (co[v_ax] - mn[v_ax]) / max(ext[v_ax], 1e-9)
        uvl.data[loop.index].uv = (1.0 - u if flip_u else u, v)
    me.update()
    return obj


def bake_surface_attr(obj, fn, name="surfq"):
    """Freeze a surface parameterisation into a point colour attribute, taken
    from each vertex's position NOW - while the mesh is still in the frame it
    was modelled in.  FLOAT_COLOR clamps on write, so send a signed quantity as
    (x + 1) / 2 and decode it in the shader; for anything that wraps, hand back
    sine and cosine rather than the angle, because those interpolate across the
    seam where a raw angle would sweep its whole range inside one face."""
    at = obj.data.color_attributes.new(name=name, type='FLOAT_COLOR', domain='POINT')
    for i, v in enumerate(obj.data.vertices):
        a, b, c = fn(v.co)
        at.data[i].color = (a, b, c, 1.0)
    return at


# ---------------------------------------------------------------- materials

def set_mat(obj, mat, slot=0):
    if mat is None or obj is None:
        return obj
    while len(obj.data.materials) <= slot:
        obj.data.materials.append(None)
    obj.data.materials[slot] = mat
    return obj


def assign_mats(obj, mats):
    obj.data.materials.clear()
    for m in mats:
        obj.data.materials.append(m)
    return obj


def face_mat(obj, index, pred):
    """Give material slot `index` to every face where pred(centre, normal)."""
    for p in obj.data.polygons:
        if pred(p.center, p.normal):
            p.material_index = index
    obj.data.update()
    return obj


# ---------------------------------------------------------------- 2D shapes

def rounded_rect(w, h, r, seg=6):
    """CCW (x, y) for a rounded rectangle centred on the origin."""
    hw, hh = w * 0.5 - r, h * 0.5 - r
    pts = []
    for (cx, cy, a0) in ((hw, hh, 0.0), (-hw, hh, math.pi * .5),
                         (-hw, -hh, math.pi), (hw, -hh, math.pi * 1.5)):
        for k in range(seg + 1):
            a = a0 + (math.pi * .5) * (k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def circle(r, seg=32, cx=0.0, cy=0.0, phase=0.0):
    return [(cx + r * math.cos(phase + TAU * i / seg),
             cy + r * math.sin(phase + TAU * i / seg)) for i in range(seg)]


def superellipse(w, h, n=4.0, seg=48):
    pts = []
    for i in range(seg):
        a = TAU * i / seg
        ca, sa = math.cos(a), math.sin(a)
        pts.append((w * 0.5 * math.copysign(abs(ca) ** (2.0 / n), ca),
                    h * 0.5 * math.copysign(abs(sa) ** (2.0 / n), sa)))
    return pts


def bez(p0, p1, p2, p3, n=8, skip_first=False):
    out = []
    for i in range(1 if skip_first else 0, n + 1):
        t = i / n
        mt = 1 - t
        out.append((mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                    mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]))
    return out


def arc_pts(cx, cy, r, a0, a1, n=8, skip_first=False):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(1 if skip_first else 0, n + 1)]


def cushion(name, w, d, h, r=0.06, cname=None, seg=6, plump=1.055):
    """A filled upholstered cushion.  The waist has to bulge PAST the plan
    outline for it to read as something with stuffing in it - a rounded box
    with a chamfer is a slab, however carefully it is subdivided."""
    pts = rounded_rect(w, d, min(r, min(w, d) * 0.45), seg=seg)
    levels = [(0.00, 0.86), (0.08, 0.985), (0.50, plump), (0.92, 0.985), (1.00, 0.86)]
    rings = [[(x * s, y * s, t * h) for (x, y) in pts] for (t, s) in levels]
    ob = _loft(name, rings, close_u=False, close_v=True, cname=cname,
               cap_start=True, cap_end=True)
    bevel(ob, 0.005, 2, 60)
    subsurf(ob, 1)
    smooth_shade(ob, 44)
    return ob


def rounded_box(name, x0, y0, z0, x1, y1, z1, r=0.02, seg=4, cname=None):
    """A box with rounded vertical corners and a softened top/bottom - the
    shape most cabinet carcasses and appliance bodies actually are."""
    w, d = x1 - x0, y1 - y0
    pts = rounded_rect(w, d, min(r, min(w, d) * 0.45), seg=seg)
    cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    e = min(r * 0.55, (z1 - z0) * 0.25)
    levels = [(z0, 1.0 - e / max(w, d) * 2.0), (z0 + e, 1.0),
              (z1 - e, 1.0), (z1, 1.0 - e / max(w, d) * 2.0)]
    rings = [[(cx + x * s, cy + y * s, z) for (x, y) in pts] for (z, s) in levels]
    ob = _loft(name, rings, close_u=False, close_v=True, cname=cname,
               cap_start=True, cap_end=True)
    return ob
