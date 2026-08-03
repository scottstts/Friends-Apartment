"""Headless render driver.

    "/Applications/Blender 5.0.app/Contents/MacOS/Blender" -b central_perk.blend \
        --python build_scripts/shoot.py -- A_frontal A_couch ...

Renders are done out of process on purpose.  Driving `bpy.ops.render.render`
from inside the interactive session works until it doesn't - once that
session's render path wedges, every engine returns a blank white frame with
no error - and a fresh process is both a clean slate and something that can
run while the file stays open for inspection.
"""
import bpy, sys, os, time

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.environ.get("CP_OUT", "/tmp/cp_renders")
SAMPLES = int(os.environ.get("CP_SAMPLES", "110"))
# 1280x756 is the reference frame's own aspect, so a render drops straight on
# top of frontal.jpeg without a rescale in between
RES = os.environ.get("CP_RES", "1280x756")
REBUILD = os.environ.get("CP_REBUILD", "0") == "1"
ENGINE = os.environ.get("CP_ENGINE", "CYCLES").upper()
# EEVEE exposure trim - see the note in main()
EE_EV = float(os.environ.get("CP_EE_EV", "-1.35"))


def main():
    here = os.path.join(os.path.dirname(bpy.data.filepath), "build_scripts")
    if here not in sys.path:
        sys.path.insert(0, here)
    if REBUILD:
        import build_all
        build_all.go(check=False)
    sc = bpy.context.scene
    if ENGINE.startswith("EEVEE"):
        # the comparison loop runs on EEVEE: a frame in seconds instead of
        # minutes is what makes render -> compare -> correct a loop at all
        # Blender 5 dropped the _NEXT suffix again: the enum is BLENDER_EEVEE
        sc.render.engine = 'BLENDER_EEVEE'
        ee = sc.eevee
        ee.taa_render_samples = max(16, SAMPLES)
        for attr, val in (("use_raytracing", True), ("use_shadows", True),
                          ("use_volumetric_shadows", True),
                          # A fast-GI ray that gives up after 1 m falls back to
                          # the world probe, and the world probe is not
                          # occluded by the building - so the sky leaks through
                          # the walls and the room renders a stop and a half
                          # hot.  Untraced distance is the whole problem, so
                          # the distance goes to 0 (infinite) and the rays get
                          # enough steps to be worth tracing.
                          ("fast_gi_distance", 0.0), ("fast_gi_ray_count", 4),
                          ("fast_gi_step_count", 32), ("fast_gi_quality", 0.5),
                          ("fast_gi_resolution", '1'),
                          ("shadow_ray_count", 2), ("shadow_step_count", 12)):
            if hasattr(ee, attr):
                setattr(ee, attr, val)
        # And it is STILL a stop hot after that, because EEVEE's screen-space
        # tracing has no answer for anything off screen and defaults it bright.
        # The scene's lighting is calibrated against Cycles, which agrees with
        # the reference photographs to within a twentieth of a stop; rather
        # than pull the practicals down and make Cycles wrong, EEVEE is stopped
        # down here, in the driver, where it belongs.  With this trim the two
        # engines and the reference frame all sit at mean luminance 0.24.
        sc.view_settings.exposure = EE_EV
    else:
        sc.render.engine = 'CYCLES'
        try:
            sc.cycles.device = 'GPU'
        except Exception:
            pass
        sc.cycles.samples = SAMPLES
        sc.cycles.use_denoising = True
        sc.view_settings.exposure = 0.0      # Cycles needs no trim
    w, h = RES.split("x")
    sc.render.resolution_x, sc.render.resolution_y = int(w), int(h)
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    os.makedirs(OUT, exist_ok=True)

    names = ARGS or [o.name for o in bpy.data.objects if o.type == 'CAMERA']
    for nm in names:
        cam = bpy.data.objects.get(nm)
        if cam is None or cam.type != 'CAMERA':
            print("!! no camera", nm)
            continue
        sc.camera = cam
        sc.render.filepath = os.path.join(OUT, nm + ".png")
        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        print("== %-14s %6.1fs  %s" % (nm, time.time() - t0,
                                       sc.render.filepath))


main()
