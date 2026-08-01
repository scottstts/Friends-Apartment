"""Full rebuild of the apartment."""
import bpy, sys, importlib, math

MODS = ('mlib', 'mats', 'L', 's_floor', 's_walls', 's_openings', 'props',
        'build_shell', 'build_openings', 'build_env', 'f_kitchen', 'f_dining',
        'f_living', 'f_beds', 'f_extra', 'view', 'rnd')


def go(load):
    for m in MODS:
        load(m)
    S = sys.modules
    M = S['build_shell'].build()
    S['build_openings'].build()
    S['build_env'].build()
    S['build_env'].sky_and_sun(strength=0.145, sun_energy=2.4)
    for l in bpy.data.lights:
        if l.name == 'SUN':
            l.color = (1.0, 0.86, 0.68)
    S['f_kitchen'].build()
    S['f_dining'].build()
    S['f_living'].build()
    S['f_beds'].build()
    S['f_beds'].dress_hall()
    S['f_extra'].build()
    fill(S['props'])
    cams(S['view'])
    S['rnd'].bloom()
    return M


def fill(P):
    """Deliberately empty.

    There were two bare point lights hanging at ceiling height here, one per
    room, with no object of any kind to emit them.  Under this project's rule
    (build_scripts/README.md) that is not allowed: every light must come from
    something you can see.  Both rooms now have a real overhead fixture instead
    - LR_ceiling and K_ceiling - which is what those two lights were standing
    in for.  If somewhere reads too dark, the answer is a fixture, not a lamp
    floating in the air."""
    return


def cams(v):
    v.cam("CAM_master", (2.30, -1.15, 1.64), (6.4, 3.9, 1.20), lens=19)
    v.cam("CAM_kitchen", (5.20, 0.85, 1.58), (0.40, 3.55, 1.20), lens=24)
    v.cam("CAM_living", (2.95, -0.85, 1.54), (7.9, 3.1, 1.15), lens=25)
    v.cam("CAM_window", (4.10, 0.70, 1.58), (6.5, 5.9, 1.40), lens=27)
    v.cam("CAM_hall", (4.10, 2.30, 1.58), (3.90, 5.9, 1.35), lens=28)
    v.cam("CAM_dine", (3.95, -0.10, 1.44), (1.65, 2.85, 0.80), lens=32)
    v.cam("CAM_tv", (6.10, 2.20, 1.45), (8.6, 3.2, 1.30), lens=34)
    v.cam("CAM_door", (3.30, 2.70, 1.55), (0.0, 0.10, 1.30), lens=30)
    v.cam("CAM_wide", (1.40, -1.15, 2.10), (7.4, 4.4, 1.00), lens=15)
    v.cam("CAM_beam", (6.60, -0.60, 1.62), (1.60, 3.90, 1.60), lens=24)
    v.cam("CAM_monica", (7.10, 5.30, 1.55), (10.8, 4.6, 1.10), lens=24)
    v.cam("CAM_rachel", (7.40, 1.55, 1.55), (11.2, 0.9, 1.05), lens=24)
    v.cam("CAM_mon_in", (9.10, 3.30, 1.55), (11.4, 5.2, 1.00), lens=22)
    v.cam("CAM_rac_in", (9.10, 2.20, 1.55), (11.4, 0.3, 1.00), lens=22)
