"""Rebuild the whole scene from the scripts and save it.

    "/Applications/Blender 5.0.app/Contents/MacOS/Blender" -b central_perk.blend \
        --python build_scripts/rebuild.py

Run out of process, like the renders, so an interactive session can stay
open on the file while it is regenerated underneath.
"""
import bpy, sys, os, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import build_all                                              # noqa: E402

build_all.go(importlib.reload, check=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "central_perk.blend"))

lamps = [o for o in bpy.data.objects if o.type == 'LIGHT']
print("lights: %d  %s" % (len(lamps),
                          [(o.name, round(o.data.energy, 1)) for o in lamps]))
