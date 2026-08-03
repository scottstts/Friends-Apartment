"""The world outside the glass: the pavement that wraps the corner, the street,
the facades opposite, and the sky and sun that light them.

None of this is decoration.  Every window in the shop looks at it, and the
daylight in the room is the sun plus that sky - there is no invisible lamp
standing in for either.
"""
import bpy, math, importlib
import mlib as M
import mats as T
import L
import build_shell as S

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C = "Street"

# the pavement wraps the north-east corner; the kerb line is this far out
WALK = 3.60
ROAD = 9.0


def build():
    M.coll(C)
    mats = S.MATS
    walk = T.concrete('paving', '8E8B82', rough=(0.6, 0.85), scale=2.4)
    road = T.concrete('asphalt', '3A3A3C', rough=(0.5, 0.78), scale=3.0)
    # Low contrast on purpose: these walls are nine metres away through glass,
    # and a bright mortar joint at that distance aliases into speckle.
    fac = T.brick('brick_street', face='6E4636', face2='5E3E30',
                  mortar='6A5A4C', spread=0.45)
    fac2 = T.brick('brick_street2', face='7A6E5A', face2='6A6050',
                   mortar='72685C', spread=0.45)
    glassm = mats['glass']
    dark = T.flat('glass_dark', '14161A', rough=0.18)

    # -- pavement -----------------------------------------------------------
    # It wraps the corner OUTSIDE the building: the earlier outline ran under
    # the shop, which put its slab on the same planes as the floors.
    e, n = L.BAY_E + L.TW, L.WC_N + L.TW
    p = [(L.EX + L.TW, -6.0), (e + WALK, -6.0), (e + WALK, n + WALK),
         (-6.0, n + WALK), (-6.0, n), (e, n), (e, L.BAY_DIAG_E),
         (L.EX + L.TW, L.BAY_N + L.TW), (L.EX + L.TW, -6.0)]
    pw = M.prism("Pavement", M.ccw(p[:-1]), -0.30, -0.02, C)
    M.set_mat(pw, walk)

    rd = M.prism("Road", [(-40, -40), (60, -40), (60, 60), (-40, 60)],
                 -0.46, -0.32, C)
    M.set_mat(rd, road)

    # -- the rest of the building the shop is the ground floor of -----------
    # Without it the storefront reads as a hut, and more to the point the
    # windows would see open sky where they should see a four-storey wall of
    # brick: the light falling into the bay depends on this being here.
    up = [(-L.TW, -L.TW), (L.EX, -L.TW), (L.EX, L.BAY_S),
          (L.BAY_E + L.TW, L.BAY_S), (L.BAY_E + L.TW, L.BAY_DIAG_E),
          (L.EX + L.TB, L.BAY_N), (L.EX + L.TB, L.WC_N + L.TW),
          (-L.TW, L.WC_N + L.TW)]
    ub = M.prism("Upper_block", M.ccw(up), L.CZ + 0.22, L.CZ + 0.22 + 12.6, C)
    M.set_mat(ub, fac)
    # its windows, four storeys of them, on the two street elevations
    for f in range(4):
        z = L.CZ + 0.55 + f * 3.05
        for i in range(5):
            y = 3.10 + i * 1.55
            a = M.box("Up_wE%d_%d" % (f, i), L.BAY_E + L.TW - 0.10, y - 0.42,
                      z, L.BAY_E + L.TW + 0.12, y + 0.42, z + 1.70, C)
            M.set_mat(a, dark)
        for i in range(4):
            x = 0.80 + i * 1.55
            a = M.box("Up_wN%d_%d" % (f, i), x - 0.42, L.WC_N + L.TW - 0.10,
                      z, x + 0.42, L.WC_N + L.TW + 0.12, z + 1.70, C)
            M.set_mat(a, dark)

    # -- the block opposite, across the street ------------------------------
    def facade(name, x0, y0, x1, y1, h, mat, floors=5, bays=6, axis='x'):
        w = M.prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], -0.30, h, C)
        M.set_mat(w, mat)
        # windows, as recessed boxes so the facade has depth from inside
        for f in range(floors):
            z = 0.95 + f * 3.05
            for bidx in range(bays):
                t = (bidx + 0.5) / bays
                if axis == 'x':
                    cx = x0 + (x1 - x0) * t
                    a = M.box("%s_w%d_%d" % (name, f, bidx), cx - 0.44, y0 - 0.14,
                              z, cx + 0.44, y0 + 0.10, z + 1.62, C)
                else:
                    cy = y0 + (y1 - y0) * t
                    a = M.box("%s_w%d_%d" % (name, f, bidx), x0 - 0.14, cy - 0.44,
                              z, x0 + 0.10, cy + 0.44, z + 1.62, C)
                M.set_mat(a, dark)
        return w

    facade("Fac_E", L.BAY_E + WALK + ROAD, -12.0,
           L.BAY_E + WALK + ROAD + 14.0, 12.0, 15.5, fac, 5, 5, axis='y')
    facade("Fac_NE", L.BAY_E + WALK + ROAD, 13.0,
           L.BAY_E + WALK + ROAD + 14.0, 30.0, 16.5, fac2, 5, 5, axis='y')
    facade("Fac_N", -14.0, L.WC_N + WALK + ROAD,
           L.WC_E + 6.0, L.WC_N + WALK + ROAD + 14.0, 14.0, fac2, 4, 6, axis='x')

    # -- sky and sun --------------------------------------------------------
    world = bpy.data.worlds.get("CP_World") or bpy.data.worlds.new("CP_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.location = (-400, 0)
    # Blender 5 renamed the Nishita model; multiple scattering is the same sky
    sky.sky_type = 'MULTIPLE_SCATTERING'
    for k, v in (("sun_elevation", math.radians(24.0)),
                 ("sun_rotation", math.radians(118.0)),
                 ("altitude", 30.0), ("air_density", 1.5),
                 ("dust_density", 2.4),
                 # the SUN lamp is the sun; the sky texture supplies sky only
                 ("sun_disc", False), ("sun_intensity", 0.0)):
        try:
            setattr(sky, k, v)
        except Exception:
            pass
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.location = (-140, 0)
    # Enough sky to keep the street readable through the glass and no more.
    # The room's own colour has to come from its tungsten; a strong sky pulls
    # the whole interior blue, which is the one thing this set never is.
    bg.inputs["Strength"].default_value = 0.34
    out = nt.nodes.new('ShaderNodeOutputWorld')
    out.location = (80, 0)
    nt.links.new(sky.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs['Surface'])

    # The sun: low and from the east-north-east, so it rakes across the
    # storefront and throws the mullion shadows the set photographs show.
    # Late afternoon rather than noon - about 3400 K - so the daylight
    # arriving through the storefront agrees with the tungsten indoors
    # instead of splitting the room into a warm half and a blue half.
    sd = bpy.data.lights.get("Sun") or bpy.data.lights.new("Sun", 'SUN')
    sd.energy = 1.35
    sd.angle = math.radians(1.6)
    sd.color = (1.0, 0.80, 0.58)
    so = bpy.data.objects.get("Sun")
    if so is None:
        so = bpy.data.objects.new("Sun", sd)
    M.put(so, C)
    so.location = (24.0, 10.0, 16.0)
    so.rotation_euler = (math.radians(66.0), 0.0, math.radians(118.0))
    print("street built")
