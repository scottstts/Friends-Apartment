"""Every door and window placed into the shell.

Each opening is handed the SAME wall line the shell used to cut it, so the
lining lands in the reveal rather than somewhere near it.  That is also why
`out=True` is not optional here - see s_walls.to_wall.
"""
import bpy, math
import mlib, mats, props, L, s_openings as SO
from s_walls import to_wall

CN = "Openings"


def materials():
    mats.paint("M_Door", L.DOOR_GREY, rough=0.30, coat=0.14, brush=0.7)
    mats.paint("M_DoorFront", mats.shade(L.TRIM, 1.02), rough=0.34, coat=0.10, brush=0.8)
    mats.metal("M_Brass", 'B08A3E', rough=0.24, brush=0.25, grime=0.35)
    mats.metal("M_Nickel", 'C9CBCC', rough=0.18, brush=0.35, grime=0.30)
    mats.clear_glass("M_Glass", 'EAF1F2', rough=0.012)
    # Blind slats are painted aluminium: near-white, satin, and dusty on the
    # up-facing side, which is most of what makes a blind read as a blind.
    mats.paint("M_Blind", 'E6E2D6', rough=0.42, coat=0.05, brush=0.25)
    mats.plastic("M_BoardBlue", '1F7FD0', rough=0.28, coat=0.35)
    mats.plastic("M_BoardFace", 'F2F3F0', rough=0.16, coat=0.45)
    return {'trim': mats.get("M_Trim"), 'door': mats.get("M_Door"),
            'brass': mats.get("M_Brass"), 'glass': mats.get("M_Glass"),
            'blind': mats.get("M_Blind")}


# ---------------------------------------------------------------- front door

def front_door(p0, p1, u0, w, h, wall_th, M):
    """Two-panel entrance door: a short top panel over a tall one, heavy
    stiles, and the ironmongery that actually appears in living_room.webp - a
    brass knob, three deadbolts up the strike side, a chain, a peephole, and
    the little blue message board screwed to the middle rail."""
    out = {}
    lin = [mlib.box("FD_lj%.2f" % a, u0 + a, 0.0, 0.0, u0 + b, wall_th, h, CN)
           for (a, b) in ((0.0, 0.026), (w - 0.026, w))]
    lin.append(mlib.box("FD_lh", u0, 0.0, h - 0.026, u0 + w, wall_th, h, CN))
    lining = mlib.join(lin, "FD_lining", CN)
    mlib.bevel(lining, 0.002, 2, 40)
    out['lining'] = mlib.set_mat(to_wall(lining, p0, p1, out=True), M['trim'])

    cs = SO._both_casings("FD_cs", w, h, wall_th, CN, cut_below=0.0, cw=0.132, cd=0.024)
    mlib.translate(cs, (u0, 0, 0))
    out['casing'] = mlib.set_mat(to_wall(cs, p0, p1, out=True), M['trim'])

    lw, lh, th = w - 0.012, h - 0.014, 0.048
    stile, top_r, bot_r, mid_r = 0.145, 0.130, 0.240, 0.150
    parts = []
    parts.append(mlib.box("FD_sl", 0, 0, 0, stile, th, lh, CN))
    parts.append(mlib.box("FD_sr", lw - stile, 0, 0, lw, th, lh, CN))
    parts.append(mlib.box("FD_rb", stile, 0, 0, lw - stile, th, bot_r, CN))
    parts.append(mlib.box("FD_rt", stile, 0, lh - top_r, lw - stile, th, lh, CN))
    zsplit = lh * 0.665
    parts.append(mlib.box("FD_rm", stile, 0, zsplit, lw - stile, th,
                          zsplit + mid_r, CN))
    parts.append(SO.raised_panel("FD_p0", stile - 0.007, bot_r, lw - stile + 0.007,
                                 zsplit, 0.011, th - 0.011, inset=0.042,
                                 proud=0.009, cname=CN))
    parts.append(SO.raised_panel("FD_p1", stile - 0.007, zsplit + mid_r,
                                 lw - stile + 0.007, lh - top_r, 0.011, th - 0.011,
                                 inset=0.042, proud=0.009, cname=CN))
    leaf = mlib.join(parts, "FD_leaf", CN)
    mlib.bevel(leaf, 0.002, 2, 44)

    hw = SO.door_hardware("FD_hw", lw, th, hinge_left=False, cname=CN, z=1.04)
    hg = SO.hinges("FD_hg", lh, th, lw, CN)
    # Ironmongery up the strike side (the hinges are on the right, so the locks
    # run up the LEFT edge as seen from inside).
    #
    # TWO locks and a chain, not three deadbolts stacked up the stile, and the
    # deadbolt sits 160 mm above the knob at 1.20 rather than at shoulder
    # height - a bolt you cannot reach without lifting your elbow is not a
    # bolt anybody fitted.  Everything on this stile is a rose let into the
    # leaf, a raised housing, and one turn standing clear of it; that is all a
    # lock is from inside a flat, and anything more reads as clutter.
    iron = []
    KX = 0.094

    def rose(nm, x, z, r=0.030, t=0.006):
        p = props.lathe(nm, [(0.0, 0.0), (r, 0.0), (r, t * 0.55),
                             (r * 0.82, t), (0.0, t + 0.001)], 26, CN)
        props.face_y(p, -1.0, (x, 0.0, z))
        return p

    def lock(nm, z, r=0.031, hr=0.021, hl=0.020, turn=0.030):
        iron.append(rose(nm + "_r", KX, z, r))
        cyl = props.lathe(nm + "_c", [
            (0.0, 0.0), (hr, 0.0), (hr, hl - 0.005), (hr * 0.78, hl),
            (0.0, hl)], 24, CN)
        props.face_y(cyl, -1.0, (KX, -0.005, z))
        iron.append(cyl)
        sp = props.lathe(nm + "_s", [(0.0, 0.0), (0.009, 0.0), (0.009, 0.012),
                                     (0.0, 0.013)], 14, CN)
        props.face_y(sp, -1.0, (KX, -0.004 - hl, z))
        iron.append(sp)
        # the turn itself: a flat tab across the spindle, standing on edge
        tb = mlib.box(nm + "_t", KX - 0.008, -0.028 - hl, z - turn,
                      KX + 0.008, -0.019 - hl, z + turn, CN)
        mlib.bevel(tb, 0.0035, 3, 38)
        iron.append(tb)

    lock("FD_bolt", 1.200)                       # the deadbolt, over the knob
    lock("FD_latch", 1.455, r=0.027, hr=0.018, hl=0.016, turn=0.024)

    # chain lock: a slide track on the leaf and a real chain of links hanging
    # off it, rather than a plate with a bump on it
    slide = mlib.box("FD_chsl", 0.052, -0.011, 1.688, 0.168, 0.0, 1.716, CN)
    mlib.bevel(slide, 0.004, 3, 38)
    iron.append(slide)
    for x in (0.058, 0.162):
        scr = props.lathe("FD_chsc%d" % int(x * 1000), [
            (0.0, 0.0), (0.007, 0.0), (0.007, 0.004), (0.0, 0.005)], 12, CN)
        props.face_y(scr, -1.0, (x, -0.011, 1.702))
        iron.append(scr)
    knobc = props.lathe("FD_chkn", [(0.0, 0.0), (0.011, 0.0), (0.012, 0.011),
                                    (0.008, 0.016), (0.0, 0.017)], 16, CN)
    props.face_y(knobc, -1.0, (0.150, -0.011, 1.702))
    iron.append(knobc)
    for i in range(8):
        t = i / 7.0
        lx = 0.062 + 0.026 * math.sin(t * 2.4)
        lz = 1.686 - t * 0.128
        lk = props.torus("FD_chl%d" % i, 0.0090, 0.0021, 14, 6, CN,
                         cx=lx, cy=-0.018, cz=lz)
        mlib.rot_x(lk, math.pi * 0.5, (lx, -0.018, lz))
        if i % 2:
            mlib.rot_y(lk, math.pi * 0.5, (lx, -0.018, lz))
        iron.append(lk)

    # peephole: a real barrel with a lens ring, at eye height on the centre line
    iron.append(rose("FD_peeprose", lw * 0.5, 1.545, 0.019, t=0.005))
    peep = props.lathe("FD_peep", [(0.0, 0.0), (0.013, 0.0), (0.014, 0.008),
                                   (0.010, 0.013), (0.009, 0.016),
                                   (0.0, 0.016)], 20, CN)
    props.face_y(peep, -1.0, (lw * 0.5, -0.005, 1.545))
    iron.append(peep)
    ironwork = mlib.join(iron, "FD_iron", CN)
    mlib.bevel(ironwork, 0.0015, 2, 40)

    # the message board
    bf = mlib.box("FD_bd", lw * 0.52 - 0.155, -0.016, 1.62, lw * 0.52 + 0.155, 0.0, 1.86, CN)
    mlib.bevel(bf, 0.005, 3, 40)
    face = mlib.box("FD_bdf", lw * 0.52 - 0.126, -0.018, 1.645,
                    lw * 0.52 + 0.126, -0.014, 1.835, CN)

    for o in (leaf, hw, hg, ironwork, bf, face):
        mlib.translate(o, (u0 + 0.006, (wall_th - th) * 0.5, 0.007))
    out['leaf'] = mlib.set_mat(to_wall(leaf, p0, p1, out=True), mats.get("M_DoorFront"))
    out['knob'] = mlib.set_mat(to_wall(hw, p0, p1, out=True), M['brass'])
    out['hinges'] = mlib.set_mat(to_wall(hg, p0, p1, out=True), M['brass'])
    out['iron'] = mlib.set_mat(to_wall(ironwork, p0, p1, out=True), M['brass'])
    out['board'] = mlib.set_mat(to_wall(bf, p0, p1, out=True), mats.get("M_BoardBlue"))
    out['boardface'] = mlib.set_mat(to_wall(face, p0, p1, out=True),
                                    mats.get("M_BoardFace"))
    return out


# ---------------------------------------------------------------- placement

def build():
    mlib.coll(CN)
    M = materials()

    N0, N1 = (L.JX, L.NY), (L.WX, L.NY)          # north wall, as built
    E0, E1 = (L.EX, L.SY), (L.EX, L.NY2)         # east wall
    B0, B1 = (L.BED_E, L.JO_Y[0]), (L.BED_E, L.NY)
    W0, W1 = (L.BED_W, L.CH_Y[1] + L.TW), (L.BED_W, L.JO_Y[0] - L.TW)
    C0, C1 = (L.BED_E, L.CH_Y[1]), (L.BED_W, L.CH_Y[1])

    def u(p0, p1, pt):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(dx, dy)
        return ((pt[0] - p0[0]) * dx + (pt[1] - p0[1]) * dy) / ln

    # --- living room windows ------------------------------------------------
    for i, (a, b) in enumerate((L.WIN_A, L.WIN_B)):
        u0 = min(u(N0, N1, (a, L.NY)), u(N0, N1, (b, L.NY)))
        SO.make_window("Win_LR%d" % i, N0, N1, u0, b - a, L.WIN_SILL, L.WIN_HEAD,
                       wall_th=L.TW, cname=CN, cols=2, blind_drop=0.95,
                       blind_tilt=54.0, mats_=M)

    # --- bathroom door ------------------------------------------------------
    # Hinged on its WEST jamb and opening INTO the bathroom, which is where a
    # bathroom door goes - swung the other way it stood wide open across the
    # living room's north wall.  The leaf reaches y = 8.39 at x = 3.6, which is
    # clear of the pan, the vanity and the bath mat alike.
    OPEN = math.radians(L.DOOR_OPEN)
    u0 = min(u(N0, N1, (L.BD_X[0], L.NY)), u(N0, N1, (L.BD_X[1], L.NY)))
    SO.make_door("Door_Bath", N0, N1, u0, L.BD_X[1] - L.BD_X[0], L.BD_H,
                 wall_th=L.TW, cname=CN, swing=OPEN, hinge_left=False, mats_=M)

    # --- bedroom doors ------------------------------------------------------
    # Both open INTO their bedrooms, hinged on opposite jambs so the two leaves
    # do not end up standing parallel a metre apart across the living room.
    u0 = min(u(B0, B1, (L.BED_E, L.JOEY_DOOR[0])), u(B0, B1, (L.BED_E, L.JOEY_DOOR[1])))
    SO.make_door("Door_Joey", B0, B1, u0, L.JOEY_DOOR[1] - L.JOEY_DOOR[0],
                 L.DOOR_TOP, wall_th=L.BW_TH, cname=CN,
                 swing=-OPEN, hinge_left=True, mats_=M)
    # NEGATIVE swing on a right-hung leaf, same as Joey's on a left-hung one.
    # With hinge_left=False a POSITIVE swing throws the leaf the other way
    # across the hinge, and Chandler's door was standing wide open into the
    # living room instead of into his own bedroom.
    u0 = min(u(B0, B1, (L.BED_E, L.CHAN_DOOR[0])), u(B0, B1, (L.BED_E, L.CHAN_DOOR[1])))
    SO.make_door("Door_Chan", B0, B1, u0, L.CHAN_DOOR[1] - L.CHAN_DOOR[0],
                 L.DOOR_TOP, wall_th=L.BW_TH, cname=CN, swing=-OPEN,
                 hinge_left=False, mats_=M)

    # --- bedroom windows ----------------------------------------------------
    for i, (a, b) in enumerate(L.CH_WIN):
        u0 = min(u(C0, C1, (a, L.CH_Y[1])), u(C0, C1, (b, L.CH_Y[1])))
        SO.make_window("Win_Chan%d" % i, C0, C1, u0, b - a, L.WIN_SILL, L.WIN_HEAD,
                       wall_th=L.TW, cname=CN, cols=2, blind_drop=0.55,
                       blind_tilt=72.0, mats_=M)
    a, b = L.JO_WIN
    u0 = min(u(W0, W1, (L.BED_W, a)), u(W0, W1, (L.BED_W, b)))
    SO.make_window("Win_Joey", W0, W1, u0, b - a, L.WIN_SILL, L.WIN_HEAD,
                   wall_th=L.TW, cname=CN, cols=2, blind_drop=0.40,
                   blind_tilt=76.0, mats_=M)

    # --- front door ---------------------------------------------------------
    u0 = min(u(E0, E1, (L.EX, L.FD_Y[0])), u(E0, E1, (L.EX, L.FD_Y[1])))
    front_door(E0, E1, u0, L.FD_Y[1] - L.FD_Y[0], L.FD_H, L.TW, M)
    return True
