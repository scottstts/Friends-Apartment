"""The world outside the windows, and the daylight that comes through them.

The windows face north into a light well, which decides the whole lighting
scheme: a north window never sees the sun's disc, so the key is the sky itself
plus whatever the building opposite bounces back.  That is why the reference
photographs have such soft, cool window light against such warm practicals -
and why putting a SUN outside these windows and aiming it in would be wrong
even though it would be brighter.

The facade opposite is real geometry standing at a real distance.  It is what
the blinds are backlit against, it is what supplies the bounce, and it means
the light falling on the couch has a reason to be the colour it is.
"""
import bpy, math, random
from mathutils import Vector
import mlib, mats, L

CNAME = "Exterior"


def world(strength=1.0, turbidity=2.6, elev=54.0, rot=195.0):
    w = bpy.data.worlds.get("ApartmentSky") or bpy.data.worlds.new("ApartmentSky")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.location = (-520, 0)
    # Blender 5 renamed the physical sky models; MULTIPLE_SCATTERING is what
    # used to be called Nishita, and it is the only one that gets the blue of a
    # north-facing light well right rather than washing it grey.
    sky.sky_type = 'MULTIPLE_SCATTERING'
    for k, v in (("sun_elevation", math.radians(elev)),
                 ("sun_rotation", math.radians(rot)),
                 ("altitude", 60.0), ("air_density", 1.1),
                 ("dust_density", turbidity),
                 ("sun_disc", False)):   # the disc is a lamp's job, not the sky's
        try:
            setattr(sky, k, v)
        except Exception:
            pass
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.location = (-240, 0)
    bg.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputWorld')
    out.location = (0, 0)
    nt.links.new(sky.outputs[0], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    return w


def facade():
    """The brownstone across the light well, plus a stub of the well's floor.
    Eight metres out: close enough to fill the window and be what the blinds
    read against, far enough that it never sharpens into a wall of detail."""
    mats.plaster("M_BrickOut", '7A4B3C', rough=0.94, bump=0.7, patch=0.22, scale=0.6)
    mats.plaster("M_Areaway", '5A5550', rough=0.95, bump=0.5, patch=0.3, scale=0.5)
    g = mats.clear_glass("M_WinDark", '10161C', rough=0.06)

    y0 = L.NY + 8.4
    x0 = L.BED_W - L.TW - 7.6          # the return opposite Joey's west window
    objs = []
    b = mlib.box("EXT_Facade", -18.0, y0, -7.0, 17.0, y0 + 1.6, 18.0, CNAME)
    mlib.set_mat(b, mats.get("M_BrickOut"))
    objs.append(b)
    bw = mlib.box("EXT_FacadeW", x0 - 1.6, -9.0, -7.0, x0, y0 + 1.6, 18.0, CNAME)
    mlib.set_mat(bw, mats.get("M_BrickOut"))
    objs.append(bw)

    # windows opposite - dark glass in shallow reveals, so the facade has scale
    win = []
    for gx in range(-6, 9):
        for gz in range(0, 7):
            x = -3.2 + gx * 1.9
            z = -1.2 + gz * 2.7
            if z < -0.4:
                continue
            win.append(mlib.box("EXT_W%d_%d" % (gx, gz), x, y0 - 0.10, z,
                                x + 1.05, y0 + 0.02, z + 1.55, CNAME))
    for gy in range(-4, 8):
        for gz in range(0, 7):
            y = -6.0 + gy * 1.9
            z = -1.2 + gz * 2.7
            if z < -0.4:
                continue
            win.append(mlib.box("EXT_V%d_%d" % (gy, gz), x0 - 0.02, y, z,
                                x0 + 0.10, y + 1.05, z + 1.55, CNAME))
    ow = mlib.join(win, "EXT_Windows", CNAME)
    mlib.set_mat(ow, g)
    objs.append(ow)

    fl = mlib.box("EXT_Well", -18.0, -9.0, -7.10, 17.0, y0 + 0.1, -7.0, CNAME)
    mlib.set_mat(fl, mats.get("M_Areaway"))
    objs.append(fl)
    return objs


def build():
    world()
    facade()
