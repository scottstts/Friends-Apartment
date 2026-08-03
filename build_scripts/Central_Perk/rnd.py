"""Render helpers.  `shots()` renders a list of camera names into renders/ at a
given size and sample count - the loop the whole build is checked with."""
import bpy, os, time
import view as V

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "renders")


def setup(w=1280, h=720, samples=64, engine='CYCLES', denoise=True, exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = engine
    # clay() leaves the view transform on Standard; put it back, or a Cycles
    # frame straight after a clay pass comes out blown to white
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.view_settings.exposure = exposure
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    if engine == 'CYCLES':
        sc.cycles.samples = samples
        sc.cycles.use_denoising = denoise
        sc.cycles.max_bounces = 8
        sc.cycles.transmission_bounces = 8
        sc.cycles.transparent_max_bounces = 12
    return sc


def clay(w=1280, h=720):
    """Workbench, studio-lit with cavity on: the honest way to read massing
    and clearances before there is any lighting in the room to read them by."""
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    d = sc.display.shading
    d.light = 'STUDIO'
    d.studio_light = 'Default'
    d.color_type = 'SINGLE'
    d.single_color = (0.62, 0.60, 0.56)
    d.show_cavity = True
    d.cavity_type = 'BOTH'
    d.curvature_ridge_factor = 1.0
    d.curvature_valley_factor = 1.0
    d.show_shadows = True
    d.shadow_intensity = 0.35
    d.show_object_outline = False
    sc.display.render_aa = '16'
    sc.view_settings.view_transform = 'Standard'
    return sc


def shot(name, tag="", **kw):
    sc = setup(**kw) if kw else bpy.context.scene
    V.use(name)
    path = os.path.join(OUT, ("%s%s.png" % (name, tag)))
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return path, round(time.time() - t, 1)


def shots(names, tag="", **kw):
    if kw:
        setup(**kw)
    out = []
    for n in names:
        out.append(shot(n, tag))
    return out
