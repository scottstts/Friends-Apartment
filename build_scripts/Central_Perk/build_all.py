"""The pipeline.

    import build_all, importlib
    build_all.go(importlib.reload)

`go` takes a loader callable so the whole build can be re-imported cleanly from
inside a running Blender.  Order matters: shell -> openings -> street -> layout
-> cameras.  Nothing later assumes anything earlier is still selected, and
`build_shell.build()` opens with a purge, so a rebuild always starts empty.
"""
import bpy, sys, os, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MODS = ["mlib", "mats", "L", "build_shell", "build_openings", "build_env",
        "f_seating", "f_tables", "f_counter", "f_props", "f_layout",
        "view", "comp", "audit"]


def go(load=None, check=True):
    mods = {}
    for name in MODS:
        m = importlib.import_module(name)
        if load is not None:
            m = load(m)
        mods[name] = m
    mods["build_shell"].build()
    mods["build_openings"].build()
    mods["build_env"].build()
    mods["f_layout"].build()
    mods["view"].build()
    mods["comp"].build()
    # sweep out any zero-area faces the lofts left behind before anything
    # downstream asks those faces for a normal
    mods["mlib"].clean_all()
    scene()
    print("=== central perk: %d objects ===" % len(bpy.data.objects))
    if check:
        # the build is not finished until this says zero: coplanar same-facing
        # pairs are z-fighting, and they are cheaper to catch here than to
        # find later in a frame
        zf = mods["audit"].zfight()
        if zf:
            print("!! %d Z-FIGHTING PAIRS - run audit.run() !!" % len(zf))
            for r in zf[:10]:
                print("   %9.1f cm2  %-28s %-28s @ %s"
                      % (r[2] * 1e4, r[0][:28], r[1][:28], r[3]))
        else:
            print("audit: clean")
    return mods


def scene():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        sc.cycles.device = 'GPU'
    except Exception:
        pass
    sc.cycles.samples = 128
    sc.cycles.preview_samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 900
    sc.render.film_transparent = False
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Base Contrast'
    sc.render.filepath = os.path.join(os.path.dirname(HERE), "renders", "cp_")
