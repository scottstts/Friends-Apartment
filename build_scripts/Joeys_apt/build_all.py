"""The pipeline.  `go(importlib.reload)` rebuilds the whole flat from scratch.

Order matters: shell -> openings -> exterior and sky -> rooms -> dressing ->
lighting -> cameras.  Dressing routines assume the casework they stand on has
already been built, and the lighting pass assumes the fixtures exist, because
every light in this scene is placed at a fixture rather than at a convenient
point in space.
"""
import bpy, math, importlib
import L, mlib, mats, s_walls, s_floor, s_openings
import build_shell, build_openings, build_env
import view, rnd, audit

# The room modules are imported lazily.  This file owns the camera set and the
# lighting rule, both of which are wanted long before the furniture exists -
# a hard import would make the whole pipeline unusable until the last builder
# is written.
MODS = ["L", "mlib", "mats", "props", "s_walls", "s_floor", "s_openings",
        "build_shell", "build_openings", "build_env",
        "f_kitchen", "f_living", "f_extra", "f_beds", "f_light",
        "view", "rnd", "audit"]


def _opt(name):
    try:
        m = __import__(name)
        importlib.reload(m)
        return m
    except ImportError:
        return None


def cameras():
    """Twenty-odd fixed cameras.  Four of them reproduce the reference
    photographs as closely as the lens data allows - those are the ones parity
    is actually judged on - and the rest are a survey: every wall square on,
    every corner, and a close pass over each piece of casework, so a fault
    cannot hide in the one direction nobody looked."""
    C = view.cam
    # --- reference-matching -------------------------------------------------
    # full_set.jpg is a publicity still taken from the audience side, above and
    # outside the fourth wall, which is why it can see the whole room at once.
    C("C_full",    (7.72, -2.55, 2.80), (2.45, 4.30, 0.92), lens=22.0)
    C("C_living",  (2.90, 2.85, 1.58), (6.95, 4.40, 1.00), lens=20.0)
    C("C_kitchen", (2.45, 1.15, 1.55), (5.52, 4.75, 1.05), lens=18.0)
    C("C_couch",   (2.35, 3.85, 1.62), (1.45, 6.95, 0.82), lens=22.0)

    # --- survey: the room from each corner ----------------------------------
    C("C_ne", (7.97, 3.95, 1.72), (1.20, 1.40, 0.95), lens=20.0)
    C("C_nw", (0.55, 6.80, 1.72), (7.22, 1.10, 0.95), lens=20.0)
    C("C_se", (7.97, 0.55, 1.72), (1.10, 6.40, 1.05), lens=20.0)
    C("C_sw", (0.52, 0.55, 1.72), (6.92, 4.00, 1.05), lens=20.0)

    # --- walls, square on ---------------------------------------------------
    C("C_wall_n", (2.05, 3.20, 1.42), (2.05, 7.30, 1.42), lens=26.0)
    C("C_wall_w", (3.40, 3.05, 1.42), (0.00, 3.05, 1.42), lens=26.0)
    C("C_wall_e", (4.62, 2.10, 1.42), (8.47, 2.10, 1.42), lens=26.0)
    C("C_wall_s", (4.50, 3.80, 1.42), (4.50, 0.00, 1.42), lens=26.0)
    C("C_wall_k", (6.55, 1.70, 1.45), (6.55, 4.90, 1.45), lens=26.0)

    # --- casework and furniture, close ---------------------------------------
    C("C_island",  (3.35, 2.10, 1.52), (5.40, 4.30, 0.98), lens=28.0)
    C("C_range",   (7.02, 2.15, 1.50), (7.02, 4.90, 1.12), lens=35.0)
    C("C_fridge",  (6.72, 2.45, 1.55), (7.98, 4.85, 1.30), lens=32.0)
    C("C_ent",     (3.45, 2.90, 1.36), (0.05, 3.30, 0.92), lens=30.0)
    C("C_recl",    (4.90, 2.20, 1.48), (2.20, 3.50, 0.72), lens=32.0)
    C("C_foos",    (5.40, 0.62, 1.52), (7.06, 1.55, 0.80), lens=30.0)
    C("C_frontdr", (5.65, 1.95, 1.55), (8.47, 2.58, 1.20), lens=30.0)
    C("C_bathdr",  (4.04, 4.70, 1.52), (4.04, 7.30, 1.20), lens=32.0)
    C("C_win",     (1.58, 4.60, 1.48), (1.58, 7.30, 1.40), lens=26.0)
    C("C_sofa_d",  (1.58, 5.30, 1.20), (1.58, 7.05, 0.62), lens=35.0)
    C("C_jog",     (3.10, 3.20, 1.50), (5.05, 5.10, 1.35), lens=26.0)
    C("C_chair",   (4.30, 2.05, 1.30), (2.50, 3.30, 0.55), lens=40.0)
    C("C_bath3",   (3.30, 8.20, 1.50), (5.30, 9.60, 0.75), lens=24.0)
    C("C_dog",     (2.20, 5.05, 1.30), (0.34, 6.46, 0.62), lens=40.0)
    C("C_sinkc",   (5.95, 3.30, 1.42), (6.15, 4.55, 0.90), lens=38.0)
    # the four corners that were leaking daylight, taken high so the ceiling
    # junction is what fills the frame
    C("C_cnr_sw",  (2.60, 1.60, 2.05), (0.10, -1.20, 3.05), lens=24.0)
    C("C_cnr_nw",  (2.20, 5.00, 2.05), (0.10, 7.20, 3.05), lens=24.0)
    C("C_cnr_se",  (6.10, 1.90, 2.05), (8.37, -1.20, 3.05), lens=24.0)
    C("C_cnr_ne",  (6.30, 3.20, 2.05), (8.37, 4.80, 3.05), lens=24.0)
    C("C_cnr_jog", (3.40, 4.60, 2.10), (4.95, 7.20, 3.05), lens=24.0)
    C("C_coff",    (2.05, 4.95, 0.86), (1.35, 6.05, 0.30), lens=34.0)
    C("C_phone",   (7.05, 3.05, 1.52), (8.42, 3.72, 1.44), lens=42.0)
    C("C_vanity",  (4.10, 8.40, 1.42), (5.55, 9.10, 0.92), lens=30.0)
    # the hound square on from the side and from the front, which is the only
    # way to judge a silhouette
    C("C_dog_s",   (2.30, 5.62, 0.90), (0.34, 6.46, 0.54), lens=46.0)
    C("C_dog_f",   (1.32, 4.72, 0.94), (0.34, 6.06, 0.62), lens=40.0)
    # Joey's leaf stands open, so the dartboard on it faces NORTH into the room
    C("C_joeydr",  (2.30, 2.55, 1.50), (-0.55, 0.06, 1.62), lens=30.0)
    C("C_cabs",    (4.05, 2.55, 1.70), (5.90, 4.62, 1.85), lens=24.0)
    C("C_stickfoot", (3.05, 5.95, 0.62), (3.32, 7.10, 0.10), lens=42.0)
    C("C_poster",  (6.70, 1.20, 1.62), (8.44, 1.05, 1.60), lens=32.0)
    C("C_poster2", (7.30, 2.05, 1.90), (8.42, 1.02, 1.55), lens=34.0)
    C("C_thresh",  (7.05, 3.35, 1.10), (8.40, 2.62, 0.06), lens=34.0)
    C("C_binchk",  (6.05, 3.10, 1.66), (8.36, 0.95, 0.62), lens=26.0)
    C("C_tubrim",  (4.92, 10.14, 1.26), (3.86, 10.58, 0.57), lens=34.0)
    C("C_basin",   (4.62, 9.05, 1.42), (5.30, 9.05, 0.86), lens=40.0)
    C("C_dog_r",   (1.32, 5.30, 1.05), (0.40, 6.72, 0.55), lens=44.0)

    # --- bedrooms and bathroom ----------------------------------------------
    C("C_chan",  (-1.05, 3.15, 1.58), (-2.55, 6.48, 1.25), lens=20.0)
    C("C_chan2", (-0.62, 4.95, 1.62), (-3.30, 3.70, 1.00), lens=18.0)
    C("C_joey",  (-0.70, 2.05, 1.58), (-3.50, 0.05, 1.05), lens=18.0)
    C("C_joey2", (-3.55, 2.30, 1.58), (-1.10, 0.30, 0.95), lens=20.0)
    C("C_bath",  (4.04, 7.05, 1.55), (3.70, 10.55, 1.05), lens=20.0)
    C("C_bath2", (4.70, 10.30, 1.55), (2.55, 7.85, 1.00), lens=19.0)

    # --- overhead ------------------------------------------------------------
    p = C("C_plan", (4.23, 3.65, 14.0), (4.23, 3.65, 0.0), lens=50.0)
    p.data.type = 'ORTHO'
    p.data.ortho_scale = 9.9
    p.rotation_euler = (0.0, 0.0, 0.0)      # straight down: yaw is pure roll
    q = C("C_plan_all", (2.20, 4.30, 17.0), (2.20, 4.30, 0.0), lens=50.0)
    q.data.type = 'ORTHO'
    q.data.ortho_scale = 14.2
    q.rotation_euler = (0.0, 0.0, 0.0)
    C("C_high", (7.32, 0.90, 2.75), (2.50, 5.20, 0.85), lens=18.0)


def fill():
    """Deliberately empty.

    There are no fill lights in this scene.  If a corner renders too dark, the
    fixture that is supposed to light it is missing, is in the wrong place, or
    is not bright enough - and the fix is the fixture, not a lamp floating in
    the middle of the room with nothing to explain it."""
    return None


def go(load=None, shell=True, rooms=True, light=True):
    if load:
        for m in MODS:
            try:
                load(__import__(m))
            except Exception as e:
                print("reload failed", m, e)
    rnd.setup()
    if shell:
        build_shell.build()
        build_openings.build()
        build_env.build()
    if rooms:
        for nm in ("f_kitchen", "f_living", "f_extra", "f_beds"):
            m = _opt(nm)
            if m:
                m.build()
    if light:
        m = _opt("f_light")
        if m:
            m.build()
    cameras()
    rnd.bloom()
    fill()
    importlib.reload(audit)
    audit.run()
    return build_shell.stats()
