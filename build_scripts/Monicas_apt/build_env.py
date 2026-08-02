"""Exterior world (only ever seen through the windows) + sky/sun.

All room light originates from the windows and from the practical fittings;
the world is a real sky, so the only way it reaches the interior is through
the glazing.
"""
import bpy, math, random
from mathutils import Vector, Matrix
import mlib, mats, L, props as P


def sky_and_sun(az=289.0, el=23.0, strength=2.2, sun_energy=5.4):
    w = bpy.data.worlds.get("ApartmentSky")
    if w:
        bpy.data.worlds.remove(w)
    w = bpy.data.worlds.new("ApartmentSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.location = (-400, 0)
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = math.radians(el)
    sky.sun_rotation = math.radians(az)
    sky.altitude = 60.0
    sky.air_density = 1.4
    sky.aerosol_density = 2.4
    sky.ozone_density = 1.0
    sky.sun_disc = False
    sky.sun_intensity = 0.0
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.location = (-140, 0)
    bg.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputWorld')
    out.location = (80, 0)
    nt.links.new(sky.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs['Surface'])

    for o in list(bpy.data.objects):
        if o.type == 'LIGHT' and o.name.startswith("SUN"):
            bpy.data.objects.remove(o, do_unlink=True)
    ld = bpy.data.lights.new("SUN", 'SUN')
    ld.energy = sun_energy
    ld.angle = math.radians(1.6)
    ld.color = (1.0, 0.90, 0.76)
    sun = bpy.data.objects.new("SUN", ld)
    mlib.put(sun, "Lighting")
    a = math.radians(az)
    e = math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    sun.location = d * 40 + Vector((3, 3, 0))
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return sun


def facade(name, x0, x1, z0, z1, y, t=0.42, cols=8, rows=6, mat=None,
           glass=None, lit=None, cname="Exterior", seed=3, flip=False):
    """Brick facade with a grid of windows; some panes warm-lit."""
    w, h = x1 - x0, z1 - z0
    holes = []
    rng = random.Random(seed)
    ww, wh = w / cols * 0.42, h / rows * 0.46
    for i in range(cols):
        for j in range(rows):
            cx = w * (i + 0.5) / cols
            cz = h * (j + 0.42) / rows
            holes.append((cx - ww / 2, cz - wh / 2, cx + ww / 2, cz + wh / 2))
    ob = mlib.panel_with_holes(name, w, h, t, holes, cname)
    M = Matrix(((1, 0, 0, x0), (0, 1, 0, y), (0, 0, 1, z0), (0, 0, 0, 1)))
    if flip:
        M = Matrix(((-1, 0, 0, x1), (0, -1, 0, y), (0, 0, 1, z0), (0, 0, 0, 1)))
    ob.data.transform(M)
    mlib.recalc_normals(ob)
    if mat:
        mlib.set_mat(ob, mat)
    # panes
    verts, faces, ids = [], [], []
    for k, (a, b, c, d) in enumerate(holes):
        px0, px1 = x0 + a, x0 + c
        pz0, pz1 = z0 + b, z0 + d
        yy = y + t * 0.72
        base = len(verts)
        verts += [(px0, yy, pz0), (px1, yy, pz0), (px1, yy, pz1), (px0, yy, pz1)]
        faces.append((base, base + 1, base + 2, base + 3))
        ids.append(k)
    pane = mlib.mesh_obj(name + "_panes", verts, faces, cname)
    mlib.recalc_normals(pane)
    if lit:
        pane.data.materials.append(lit)
        pane.data.materials.append(glass or lit)
        rng2 = random.Random(seed + 7)
        for p in pane.data.polygons:
            p.material_index = 0 if rng2.random() < 0.45 else 1
    return ob


def build(M=None):
    C = "Exterior"
    mb = mats.brick_wall("brick_exterior")
    for n in mb.node_tree.nodes:
        if n.type == 'TEX_BRICK':
            n.inputs['Color1'].default_value = mats.srgb('7C4636')
            n.inputs['Color2'].default_value = mats.srgb('5A3128')
            n.inputs['Mortar'].default_value = mats.srgb('8E8577')
    m_lit = mats.emissive('win_lit', 'FFD9A0', strength=5.0, base='2A2015')
    m_dark = mats.paint('win_dark', '15161C', rough=0.16, coat=0.5)
    m_conc = mats.plaster('concrete_ext', '7E7A70', rough=0.75, bump=0.55, scale=38)
    m_steel = mats.metal('metal_dark_ext', '2E2C2A', rough=0.5, bump=0.15)

    # brick veneer on the outside of the alcove north wall
    # starts at the hall block's east face, not at the bay's west edge - the bay
    # now runs on past that block, whose own north wall stands further out
    VX = L.HALL_EW[1]
    ven = mlib.panel_with_holes(
        "EXT_veneer", L.AL_X[1] - VX, L.BW_TOP, 0.03,
        [(L.BW_X[0] - VX, L.BW_SILL, L.BW_X[1] - VX, L.BW_TOP)], C)
    ven.data.transform(Matrix(((1, 0, 0, VX), (0, 1, 0, L.AL_Y[1] + L.TW + 0.002),
                               (0, 0, 1, 0), (0, 0, 0, 1))))
    mlib.recalc_normals(ven)
    mlib.set_mat(ven, mb)

    # narrow setback ledge outside the window with a low masonry parapet, kept
    # close so it reads as a band across the bottom of the glass
    # The ledge starts east of the bathroom/hall block, which now projects north
    # past this line - at x = 2.0 the terrace and parapet ran straight through it.
    TX = L.HALL_EW[1] + 0.13
    ter = mlib.box("EXT_terrace", TX, L.AL_Y[1] + L.TW, -0.10, 13.0, 7.00, 0.02, C)
    mlib.set_mat(ter, m_conc)
    par = mlib.box("EXT_parapet", TX, 6.80, -0.05, 13.0, 7.00, 0.88, C)
    mlib.bevel(par, 0.02, 2, 40)
    mlib.set_mat(par, m_conc)
    cap = mlib.box("EXT_parapet_cap", TX - 0.04, 6.76, 0.88, 13.04, 7.04, 0.945, C)
    mlib.bevel(cap, 0.012, 2, 40)
    mlib.set_mat(cap, m_conc)
    # fire-escape rail rising past the window
    rails = []
    for x in (5.35, 7.55):
        rails.append(mlib.revolve("EXT_rail", [(0.0, 0.0), (0.022, 0.0),
                                               (0.022, 1.15), (0.0, 1.15)], 12,
                                  cname=C))
        mlib.translate(rails[-1], (x, 6.62, 0.02))
    rails.append(mlib.box("EXT_railbar", 5.35, 6.598, 1.10, 7.55, 6.642, 1.142, C))
    rr = mlib.join(rails, "EXT_railing", C)
    mlib.set_mat(rr, m_steel)

    # building across the street
    facade("EXT_facade_a", -8.0, 10.0, -12.0, 14.0, 11.0, 0.6, 7, 10,
           mat=mb, glass=m_dark, lit=m_lit, seed=5)
    facade("EXT_facade_b", 10.0, 24.0, -12.0, 11.0, 10.2, 0.6, 6, 9,
           mat=mb, glass=m_dark, lit=m_lit, seed=11)
    # building opposite the bedroom windows, to the east
    facade("EXT_facade_e", -6.0, 12.0, -12.0, 12.0, 16.6, 0.6, 7, 9,
           mat=mb, glass=m_dark, lit=m_lit, seed=23)
    fe = bpy.data.objects["EXT_facade_e"]
    mlib.rotate_z(fe, math.radians(-90))
    mlib.translate(fe, (L.EXT_E + 9.6, 1.2, 0.0))
    fp = bpy.data.objects["EXT_facade_e_panes"]
    mlib.rotate_z(fp, math.radians(-90))
    mlib.translate(fp, (L.EXT_E + 9.6, 1.2, 0.0))
    # street level
    st = mlib.box("EXT_street", -12.0, 7.2, -12.06, 26.0, 11.0, -12.0, C)
    mlib.set_mat(st, mats.plaster('asphalt', '3A3A3C', rough=0.8, bump=0.4, scale=60))

    # sunlit light-well wall opposite the kitchen window: a pale stucco return
    # a few metres north-west, so the window reads as a bright hole
    m_stucco = mats.plaster('stucco_lightwell', 'C9C0AC', rough=0.72, bump=0.4,
                            scale=30)
    lw = mlib.prism("EXT_lightwell",
                    [(-4.20, 5.00), (0.60, 9.80), (0.16, 10.24), (-4.64, 5.44)],
                    -12.0, 9.5, C)
    mlib.set_mat(lw, m_stucco)
    lw2 = mlib.box("EXT_lightwell2", -5.0, 2.0, -12.0, -4.2, 6.2, 9.5, C)
    mlib.set_mat(lw2, m_stucco)
    lg = bpy.data.lights.new("KW_skylight", 'AREA')
    lg.energy = 260.0
    lg.shape = 'RECTANGLE'
    lg.size, lg.size_y = 3.2, 2.6
    lg.color = (1.0, 0.95, 0.86)
    lo2 = bpy.data.objects.new("KW_skylight", lg)
    mlib.put(lo2, "Lighting")
    kp = L.chamfer_pt(0.72, -1.45)
    lo2.location = (kp[0], kp[1], 2.10)
    # d2 is the direction the panel throws.  It pointed north-west, i.e. out
    # over the light well and away from the flat, so the kitchen window was
    # getting only the edge of it: aim the sky panel at the window it stands for.
    wc = L.chamfer_pt(0.72, 0.0)
    d2 = (Vector((wc[0], wc[1], (L.KW_Z[0] + L.KW_Z[1]) * 0.5))
          - Vector(lo2.location)).normalized()
    lo2.rotation_mode = 'QUATERNION'
    lo2.rotation_quaternion = (-d2).to_track_quat('Z', 'Y')

    # -- the landing outside the front door (Monica/Chandler's hallway) --------
    m_hall = mats.plaster('landing_wall', '7E6EA8', rough=0.6, bump=0.22)
    m_hwood = mats.wood('landing_wood', ('8A5A30', '5F3A1A', '3A2010'),
                        ring=16, warp=0.12, warp_scale=1.5, distort=1.6,
                        bump=0.3, axis='Z')
    lx0, lx1 = -2.40, -L.TW
    ly0, ly1 = L.SY - 0.20, 1.10
    for nm, a, b, mm in (
        ("EXT_land_w", (lx0 - 0.22, ly0, 0), (lx0, ly1, L.CZ), m_hall),
        ("EXT_land_s", (lx0 - 0.22, ly0 - 0.22, 0), (lx1, ly0, L.CZ), m_hall),
        ("EXT_land_n", (lx0 - 0.22, ly1, 0), (lx1, ly1 + 0.22, L.CZ), m_hall),
        ("EXT_land_c", (lx0 - 0.22, ly0 - 0.22, L.CZ), (lx1, ly1 + 0.22,
                                                        L.CZ + 0.1), m_hall),
        ("EXT_land_f", (lx0 - 0.22, ly0 - 0.22, -0.02), (lx1, ly1 + 0.22, 0.004),
         m_hwood),
    ):
        o = mlib.box(nm, a[0], a[1], a[2], b[0], b[1], b[2], C)
        mlib.set_mat(o, mm)
    # A fitting on the landing ceiling, so the glow through the transom over the
    # purple door has something making it.  There was a bare bulb here.
    P.flush_dome("LAND_light", (-1.15, 0.10, L.CZ - 0.010), cname=C, r=0.125,
                 energy=26.0, colr=(1.0, 0.78, 0.55), drop=0.085)
    print("exterior built")
