"""Cameras.

The build is checked by rendering it and holding the result next to the
reference frame, so the camera set is part of the model, not an afterthought.
Five of them are aimed to reproduce a specific reference photograph as closely
as the room allows; the rest cover the room so nothing can hide in a corner.

`CAMS` is (name, eye, target, lens, note).  `look_at` does the aiming, so a
camera is moved by editing its two points and nothing else.
"""
import bpy, math, importlib
from mathutils import Vector
import mlib as M
import L

importlib.reload(M); importlib.reload(L)

C = "Cameras"

EYE = 1.62          # standing eye height
SIT = 1.15          # seated

CAMS = [
    # ---- the five that match a reference photograph ----------------------
    ("A_frontal", (4.74, 1.92, 1.68), (4.86, 8.20, 0.72), 24,
     "ref frontal.avif - straight down the room over the couch"),
    ("A_couch", (6.95, 3.15, 1.52), (2.20, 8.30, 1.15), 20,
     "ref main_couch.webp - across the couch to the counter"),
    ("A_top", (4.85, 0.70, 3.30), (5.20, 6.60, 0.40), 20,
     "ref top_view.webp - high three-quarter from the south"),
    ("A_entrance", (7.75, 3.15, 1.74), (9.55, 7.00, 1.55), 24,
     "ref entrance.webp - the doors and the corner window"),
    ("A_fullset", (2.62, 4.55, 1.90), (6.20, 10.80, 1.30), 17,
     "ref full_set.jpg - from the counter across the whole room"),

    # ---- the room, systematically ----------------------------------------
    ("B_couch_front", (4.79, 3.05, 1.28), (4.79, 6.60, 0.95), 35,
     "the couch square on"),
    ("B_couch_low", (4.79, 2.40, 0.85), (4.79, 6.20, 0.80), 28,
     "couch at seated height"),
    ("B_counter", (4.60, 7.60, 1.58), (1.30, 8.60, 1.10), 30,
     "the service counter and the stools"),
    ("B_backbar", (3.30, 9.98, 1.55), (0.20, 11.48, 1.35), 26,
     "the back bar and the chalkboard wall"),
    ("B_north_wall", (5.30, 7.60, 1.55), (5.60, 13.13, 1.75), 32,
     "the alcove, the settee and the painting wall"),
    ("B_alcove", (5.90, 9.98, 1.62), (6.10, 12.98, 1.20), 24,
     "into the north alcove"),
    ("B_bay_in", (6.40, 5.60, 1.58), (9.60, 5.55, 1.20), 28,
     "from the room into the window bay"),
    ("B_bay_along", (8.60, 3.00, 1.55), (8.90, 9.30, 1.45), 26,
     "along the bay, south to north"),
    ("B_bay_back", (9.60, 8.60, 1.58), (8.40, 3.40, 1.10), 26,
     "along the bay, north to south"),
    ("B_window_sofa", (7.90, 5.55, 1.35), (10.10, 5.60, 1.10), 32,
     "the damask settee under the CENTRAL PERK sign"),
    ("B_door_in", (8.30, 6.90, 1.62), (7.86, 9.55, 1.55), 24,
     "standing inside the door, looking at it"),
    ("B_from_door", (8.95, 8.55, 1.62), (4.20, 4.60, 1.10), 20,
     "the view a customer gets on the way in"),
    ("B_south", (4.90, 8.20, 1.58), (5.20, 1.10, 1.00), 26,
     "north to south, over the whole room"),
    ("B_south_zone", (5.30, 4.60, 1.50), (5.25, 0.60, 0.90), 30,
     "the south seating group"),
    ("B_sw_corner", (6.90, 3.60, 1.58), (1.60, 1.20, 1.10), 20,
     "the kitchen corner and the south-west of the room"),
    ("B_lobby", (1.32, 10.98, 1.58), (1.32, 15.18, 1.40), 30,
     "through the doorway to the lobby"),
    ("B_kitchen", (1.40, 4.40, 1.58), (1.35, 0.90, 1.05), 24,
     "into the kitchen"),

    # ---- close-ups, for judging materials rather than layout ---------------
    # A weave that looks right across a room can be a checkerboard at arm's
    # length and vice versa, and neither shows up in a wide shot.
    # far enough back to see three or four repeats: one motif filling the
    # frame says nothing about whether the cloth reads as cloth
    ("D_damask", (8.10, 5.30, 1.05), (9.62, 5.24, 0.80), 50,
     "the bay settee's damask, close"),
    ("D_chair", (7.55, 6.72, 1.05), (8.36, 6.06, 0.62), 55,
     "a bistro chair's black-and-gold cover"),
    ("D_couch", (4.10, 4.30, 0.96), (4.78, 5.70, 0.72), 45,
     "the hero couch's velvet and buttoning"),
    ("D_brick", (5.60, 11.60, 1.70), (7.30, 12.60, 1.90), 60,
     "brickwork and the dado, close"),
    ("D_rug", (3.05, 3.05, 1.15), (4.10, 4.05, 0.02), 45,
     "the main rug's weave"),

    # ---- overviews --------------------------------------------------------
    ("C_plan", (5.10, 6.40, 18.5), (5.10, 6.40, 0.0), 32, "orthographic plan"),
    ("C_iso_SE", (20.0, -9.0, 13.0), (5.2, 6.4, 1.0), 45, "cutaway iso"),
    ("C_iso_SW", (-12.0, -10.0, 12.0), (4.6, 6.2, 1.0), 45, "cutaway iso"),
    ("C_street", (17.0, 13.5, 2.10), (8.60, 8.60, 1.90), 24,
     "the shop from the pavement"),
]


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def cam(name, eye, target, lens, note=""):
    d = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    d.lens = lens
    d.clip_start = 0.02
    d.clip_end = 400.0
    d.sensor_fit = 'HORIZONTAL'
    ob = bpy.data.objects.get(name)
    if ob is None or ob.data != d:
        ob = bpy.data.objects.new(name, d)
    M.put(ob, C)
    ob.location = Vector(eye)
    look_at(ob, target)
    ob["note"] = note
    return ob


def build():
    M.coll(C)
    for spec in CAMS:
        ob = cam(*spec)
        if spec[0] == "C_plan":
            # a real plan: orthographic, and the near plane cuts the room at
            # 2.2 m so the ceiling and the beams are sliced away
            ob.data.type = 'ORTHO'
            ob.data.ortho_scale = 19.0
            ob.data.clip_start = ob.location.z - 2.2
        if spec[0].startswith("C_iso"):
            ob.data.clip_start = 6.0
    bpy.context.scene.camera = bpy.data.objects["A_frontal"]
    print("cameras:", len(CAMS))


def use(name):
    bpy.context.scene.camera = bpy.data.objects[name]
    return bpy.data.objects[name]
