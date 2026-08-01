"""Dressing for the bathroom hallway and the bedroom corridor - both are seen
through openings from the living room, so they need real light and content."""
import bpy, math, random
import mlib, mats, L, props as P
import f_living as FL

CH, CO = "Hall", "Corridor"


def build(M=None):
    ML = FL.mk_mats()
    gold = mats.paint('paint_gilt', 'C9A24A', rough=0.30, coat=0.4)
    # ---------------------------------------------------- bathroom hallway
    # framed prints + oval mirror on the hallway west wall (faces east)
    for i, (yy, zz, w, h) in enumerate(((4.36, 1.86, 0.24, 0.30),
                                        (4.36, 1.50, 0.24, 0.30),
                                        (4.66, 1.70, 0.22, 0.28))):
        P.framed("H_art%d" % i, w, h, (L.HALL_X[0] + 0.030, yy, zz), (1, 0), CH,
                 framemat=gold,
                 artmat=mats.botanical('art_hall_%d' % i, normal=(1, 0),
                                       seed=31 + i * 5, ground='E6DEC6',
                                       stem='5C6A40', leafc=('4E5E36', '86946A'),
                                       bloom=('A87A52', 'DCC69C')))
    # white cabriole side table against the hallway east wall
    tw, td, th = 0.44, 0.34, 0.72
    white = mats.paint('paint_white_table', 'EDE7DA', rough=0.28, coat=0.35)
    parts = []
    top = mlib.prism("H_tab_top", mlib.rounded_rect(td, tw, 0.05, 4), th - 0.026,
                     th, CH)
    mlib.bevel(top, 0.005, 3, 40)
    parts.append(top)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        pts = mlib.bez((0.0, th - 0.03), (0.05, th - 0.28), (0.08, th - 0.52),
                       (0.025, -0.012), n=10)
        path = [(sx * (td / 2 - 0.055 + p[0] * 0.8),
                 sy * (tw / 2 - 0.055 + p[0] * 0.8), p[1]) for p in pts]
        parts.append(mlib.tube_along("H_tab_lg", path, mlib.circle(0.013, 8), CH))
    tob = mlib.join(parts, "H_table", CH)
    mlib.smooth_shade(tob, 40)
    mlib.set_mat(tob, white)
    mlib.translate(tob, (L.HALL_X[1] - 0.24, 5.10, 0.0))
    FL.table_lamp("H_lamp", L.HALL_X[1] - 0.24, 5.10, 0.72, ML, CH, energy=16.0,
                  scale=0.85)
    FL.sconce("H_sconce", (L.HALL_X[0] + 0.02, 4.10, 1.78), (1, 0), ML, CH,
              energy=11.0)

    # ------------------------------------------------------------ corridor
    warm = mats.wood('wood_corr_panel', ('A2703C', '7A4A20', '4A2A10'),
                     ring=16.0, warp=0.12, warp_scale=1.5, distort=1.6,
                     bump=0.26, axis='XZ')
    # wainscot panelling on the corridor walls
    for nm, p0, p1, nrm in (("Co_pw", (L.CO_X[0] + 0.01, L.CO_Y[0] + 0.02),
                             (L.CO_X[0] + 0.01, L.CO_Y[1] - 0.02), (1, 0)),
                            ("Co_pe", (L.CO_X[1] - 0.01, L.CO_Y[0] + 0.02),
                             (L.CO_X[1] - 0.01, L.CO_Y[1] - 0.02), (-1, 0))):
        pass
    dado = mlib.box("Co_dado_e", L.CO_X[1] - 0.022, L.CO_Y[0], 0.0,
                    L.CO_X[1], L.CO_Y[1], 1.02, CO)
    mlib.set_mat(dado, warm)
    cap = mlib.box("Co_dado_cap", L.CO_X[1] - 0.038, L.CO_Y[0], 1.02,
                   L.CO_X[1], L.CO_Y[1], 1.055, CO)
    mlib.bevel(cap, 0.005, 2, 45)
    mlib.set_mat(cap, warm)
    # a chest of drawers at the end of the corridor
    parts = []
    cxx, cyy = L.CO_X[1] - 0.30, 2.66
    body = mlib.box("Co_chest", cxx - 0.26, cyy - 0.52, 0.06, cxx + 0.26,
                    cyy + 0.52, 0.88, CO)
    mlib.bevel(body, 0.008, 2, 45)
    parts.append(body)
    top = mlib.box("Co_chest_top", cxx - 0.29, cyy - 0.56, 0.88, cxx + 0.29,
                   cyy + 0.56, 0.925, CO)
    mlib.bevel(top, 0.006, 3, 40)
    parts.append(top)
    for k in range(3):
        z = 0.10 + k * 0.255
        dw = mlib.box("Co_dw%d" % k, cxx - 0.275, cyy - 0.47, z, cxx - 0.255,
                      cyy + 0.47, z + 0.225, CO)
        mlib.bevel(dw, 0.004, 2, 45)
        parts.append(dw)
    ch = mlib.join(parts, "Co_chest", CO)
    mlib.set_mat(ch, warm)
    # 'Excelsior' style poster on the corridor east wall
    P.framed("Co_poster", 0.46, 0.68, (L.CO_X[1] - 0.045, 1.60, 1.72), (-1, 0), CO,
             framemat=mats.paint('frame_black', '1E1B18', rough=0.35, coat=0.4),
             artmat=mats.floral_chintz('art_excelsior', ground='1A1512',
                                       petal='B31E22', petal2='D8A32A',
                                       leaf='6B2020', leaf2='8E3A22', scale=6.0),
             mat_w=0.0, fw=0.030, fd=0.024)
    # two sconces are the only light in the corridor - nothing unmotivated
    FL.sconce("Co_sconce", (L.CO_X[1] - 0.05, 2.10, 1.82), (-1, 0), ML, CO,
              energy=26.0)
    FL.sconce("Co_sconce2", (L.CO_X[1] - 0.05, 1.10, 1.82), (-1, 0), ML, CO,
              energy=20.0)

    # ------------------------------------------------------------ bathroom
    tile = mats.get('tile_bath')
    wht = mats.paint('porcelain', 'F2F0E8', rough=0.10, coat=0.6)
    # tub along the west wall
    tb = mlib.prism("BA_tub", mlib.rounded_rect(0.72, 1.55, 0.22, 6), 0.10, 0.58,
                    "Bathroom")
    mlib.bevel(tb, 0.02, 2, 50)
    mlib.set_mat(tb, wht)
    mlib.translate(tb, (L.BA_X[0] + 0.40, 5.30, 0.0))
    inner = mlib.prism("BA_tub_in", mlib.rounded_rect(0.60, 1.42, 0.18, 6), 0.16,
                       0.585, "Bathroom")
    mlib.set_mat(inner, mats.paint('tub_inside', 'E8E6DC', rough=0.16, coat=0.5))
    mlib.translate(inner, (L.BA_X[0] + 0.40, 5.30, 0.0))
    # pedestal basin
    ped = mlib.revolve("BA_ped", [(0.0, 0.0), (0.115, 0.0), (0.100, 0.05),
                                  (0.072, 0.30), (0.085, 0.58), (0.140, 0.66),
                                  (0.0, 0.66)], 20, cname="Bathroom")
    mlib.smooth_shade(ped, 34)
    mlib.set_mat(ped, wht)
    bs = mlib.prism("BA_basin", mlib.rounded_rect(0.52, 0.40, 0.12, 5), 0.66, 0.80,
                    "Bathroom")
    mlib.bevel(bs, 0.014, 2, 50)
    mlib.set_mat(bs, wht)
    for o in (ped, bs):
        mlib.translate(o, (2.60, L.BA_Y[1] - 0.24, 0.0))
    # loo
    lo = mlib.revolve("BA_wc", [(0.0, 0.0), (0.16, 0.0), (0.15, 0.10),
                                (0.19, 0.34), (0.22, 0.38), (0.0, 0.40)], 22,
                      cname="Bathroom")
    mlib.smooth_shade(lo, 36)
    mlib.set_mat(lo, wht)
    mlib.translate(lo, (1.90, L.BA_Y[1] - 0.30, 0.0))
    P.flush_dome("BA_light", (2.20, 5.40, 2.62), cname=C, r=0.115, energy=15.0,
                 colr=(1.0, 0.90, 0.80), drop=0.070)
    print("hall/corridor/bath dressed")
