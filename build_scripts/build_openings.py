"""Assemble every door and window into the shell."""
import bpy, math
from mathutils import Matrix
import mlib, mats, L, s_openings as O


def swing_leaf(name, w, h, hinge, closed_dir, angle, M, cname, mat, t=0.042,
               rows=(0.30, 0.30, 0.20, 0.20)):
    """A panel door standing open.  hinge = world (x, y) of the hinge stile,
    closed_dir = unit 2D direction the closed leaf runs in from the hinge,
    angle = degrees swung (positive opens towards closed_dir rotated -90 deg)."""
    leaf = O.panel_door(name, w, h, t, rows=rows, stile=0.110, rail=0.120,
                        mid=0.082, cname=cname, mat=mat)
    # reorient: leaf runs along +Y from a hinge at the origin, thickness in -X
    mlib.rotate_z(leaf, math.pi / 2)
    mlib.translate(leaf, (0.0, w / 2, 0.010))
    knobs = []
    for sx, ang in ((0.004, math.pi / 2), (-t - 0.004, -math.pi / 2)):
        kn = O.knob_set(name + "_kn", cname, M['brass'])
        mlib.rot_x(kn, 0)
        mlib.rotate_z(kn, ang)
        mlib.translate(kn, (sx, w - 0.125, 1.00))
        knobs.append(kn)
    base = math.atan2(closed_dir[1], closed_dir[0]) - math.pi / 2
    for o in [leaf] + knobs:
        mlib.rotate_z(o, base - math.radians(angle))
        mlib.translate(o, (hinge[0], hinge[1], 0.0))
    return [leaf] + knobs


def mk_mats():
    M = {}
    M['door_purple'] = mats.paint('paint_door_purple', L.DOOR_PURPLE, rough=0.30,
                                  coat=0.30, variation=0.02)
    M['trim'] = mats.get('paint_lav_trim') or mats.paint('paint_lav_trim', L.LAV_TRIM)
    M['turq'] = mats.paint('paint_turquoise', L.TURQ, rough=0.30, coat=0.22)
    M['green_door'] = mats.paint('paint_green_door', L.GREEN_DOOR, rough=0.28, coat=0.25)
    M['gold'] = mats.paint('paint_gold_frame', L.GOLD, rough=0.34, coat=0.30)
    M['brass'] = mats.metal('metal_brass', 'B08D3A', rough=0.22, bump=0.05)
    M['chrome'] = mats.metal('metal_chrome', 'D8DCE0', rough=0.10, bump=0.02)
    M['steel_dk'] = mats.metal('metal_steel_dark', '3A322C', rough=0.34, bump=0.06)
    M['glass'] = mats.pane('glass_clear', rough=0.018, base_alpha=0.05, edge=0.62)
    M['glass_frost'] = mats.pane('glass_frosted', tint='E4E8E2', rough=0.50,
                                 base_alpha=0.80, edge=0.18, bumpn=280.0)
    M['glass_dark'] = mats.pane('glass_dark', tint='2C2F36', rough=0.06,
                                base_alpha=0.62, edge=0.34)
    M['stone'] = mats.plaster('stone_sill', '8D897E', rough=0.62, bump=0.5, scale=48)
    # The shade is a pale natural weave in the set photo; the old values went
    # near-black in the low light up on the rake.
    # The battens are real geometry now, so the material must not also draw a
    # pattern: one cathedral figure sampled across the whole panel ran straight
    # through every reed and read as moire.  A woven reed is plain.
    M['blind'] = mats.wood('blind_matchstick', ('DCC096', 'D3B78C', 'C9AC82'),
                           ring=24.0, warp=0.004, warp_scale=3.0, distort=0.04,
                           blotch=0.16, bump=0.20, rough=(0.52, 0.70),
                           aniso=0.0, axis='YZ', translucent=0.34,
                           grain_relief=0.05)
    return M


def build(M=None):
    M = M or mk_mats()
    C = "Openings"

    # ============================================================ FRONT DOOR
    w, top = L.FD_Y[1] - L.FD_Y[0], L.FD_TOP
    cy = (L.FD_Y[0] + L.FD_Y[1]) * 0.5
    ln = O.lining("FD_lining", w, top, L.TW, 0.024, C, M['trim'])
    O.place(ln, (0.0, cy, 0.0), (0, 1), (-1, 0))
    cs = O.casing("FD_casing", w, top, 0.100, 0.026, C, M['trim'])
    O.place(cs, (0.0, cy, 0.0), (0, 1), (1, 0))
    # outside architrave (seen from the hallway) - simple
    cs2 = O.casing("FD_casing_out", w, top, 0.070, 0.016, C, M['trim'])
    O.place(cs2, (-L.TW, cy, 0.0), (0, 1), (-1, 0))
    # transom: head rail + sash
    hr = mlib.box("FD_headrail", -w / 2, 0.0, L.FD_H, w / 2, L.TW, L.FD_H + 0.075, C)
    O.place(hr, (0.0, cy, 0.0), (0, 1), (-1, 0))
    mlib.set_mat(hr, M['trim'])
    tf, tg = O.steel_window("FD_transom", w - 0.048, top - L.FD_H - 0.085, [1], 1,
                            frame_w=0.048, frame_d=0.055, cname=C,
                            mat=M['trim'], glass=M['glass_dark'], cols_per_bay=1,
                            glass_back=0.008)
    for o in (tf, tg):
        o.data.transform(Matrix.Translation((0, 0, L.FD_H + 0.085)))
        O.place(o, (0.0, cy, 0.0), (0, 1), (-1, 0))
    # leaf
    lw, lh = w - 0.055, L.FD_H - 0.030
    leaf = O.flush_door("FD_leaf", lw, lh, 0.044, C, M['door_purple'])
    mlib.translate(leaf, (0, 0.075, 0.012))
    O.place(leaf, (0.0, cy, 0.0), (0, 1), (-1, 0))
    # the yellow frame + peephole boss + hardware (all on the leaf face)
    fx = -0.075
    # The gold frame is the one thing everyone knows about this door.  It was a
    # 185 x 205 swept loop, which reads as a fat rounded outline with no
    # moulding at all; on the set it is a proper mitred picture frame roughly
    # 300 x 340 with a stepped gilt section and crisp corners.
    FW, FH = 0.300, 0.340
    prof = [(0.0, 0.0015), (0.0, 0.0170), (0.0060, 0.0225), (0.0155, 0.0250),
            (0.0245, 0.0215), (0.0300, 0.0130), (0.0325, 0.0060),
            (0.0340, 0.0025), (0.0340, 0.0015)]
    fr = mlib.sweep_rect_frame("FD_yellowframe", FW, FH, prof, C)
    mlib.smooth_shade(fr, 34)
    mlib.set_mat(fr, M['gold'])
    O.place(fr, (fx, cy, 1.545), (0, 1), (1, 0))
    # spyhole above the frame, not floating in the middle of it
    ph = mlib.revolve("FD_peep", [(0.0, 0.0), (0.009, 0.0), (0.009, 0.006),
                                  (0.005, 0.008), (0.0, 0.008)], 16, cname=C)
    mlib.rot_x(ph, -math.pi / 2)
    O.place(ph, (fx, cy, 1.790), (0, 1), (1, 0))
    mlib.set_mat(ph, M['brass'])
    # knocker: back-plate and ring, well clear below the frame
    kp = mlib.revolve("FD_knock_plate", [(0.0, 0.0), (0.034, 0.0), (0.034, 0.007),
                                         (0.026, 0.013), (0.0, 0.015)], 24, cname=C)
    mlib.rot_x(kp, -math.pi / 2)
    mlib.smooth_shade(kp, 40)
    O.place(kp, (fx, cy, 1.290), (0, 1), (1, 0))
    mlib.set_mat(kp, M['brass'])
    # built flat then stood up, like the other face fittings - swept in XZ it
    # came out edge-on to the door once `place` had turned it
    ring = mlib.tube_along("FD_knock_ring",
                           [(0.030 * math.cos(a), 0.030 * math.sin(a), 0.0)
                            for a in [k * math.tau / 20 for k in range(20)]],
                           mlib.circle(0.0055, 8), C, close_path=True)
    mlib.rot_x(ring, -math.pi / 2)
    mlib.translate(ring, (0.0, 0.0, -0.036))
    mlib.smooth_shade(ring, 38)
    O.place(ring, (fx + 0.013, cy, 1.290), (0, 1), (1, 0))
    mlib.set_mat(ring, M['brass'])
    kn = O.knob_set("FD_knob", C, M['brass'])
    O.place(kn, (fx, L.FD_Y[0] + 0.11, 1.000), (0, 1), (1, 0))
    # the stack of locks up the latch stile: two deadbolts, a slide bolt, and a
    # security chain with an actual chain on it
    for k, (zz, rr2) in enumerate(((1.415, 0.026), (1.135, 0.022))):
        db = mlib.revolve("FD_deadbolt%d" % k,
                          [(0.0, 0.0), (rr2 * 1.35, 0.0), (rr2 * 1.35, 0.008),
                           (rr2, 0.014), (rr2, 0.030), (rr2 * 0.45, 0.036),
                           (0.0, 0.038)], 18, cname=C)
        mlib.rot_x(db, -math.pi / 2)
        mlib.smooth_shade(db, 40)
        O.place(db, (fx, L.FD_Y[0] + 0.105, zz), (0, 1), (1, 0))
        mlib.set_mat(db, M['brass'])
    sb = mlib.prism("FD_bolt", mlib.rounded_rect(0.115, 0.048, 0.008, 3), 0.0, 0.009, C)
    mlib.rot_x(sb, -math.pi / 2)
    O.place(sb, (fx, L.FD_Y[0] + 0.095, 1.265), (0, 1), (1, 0))
    mlib.set_mat(sb, M['brass'])
    cp = mlib.prism("FD_chainplate", mlib.rounded_rect(0.030, 0.075, 0.008, 3),
                    0.0, 0.007, C)
    mlib.rot_x(cp, -math.pi / 2)
    O.place(cp, (fx, L.FD_Y[0] + 0.085, 1.585), (0, 1), (1, 0))
    mlib.set_mat(cp, M['brass'])
    slack = [(0.0, 0.0, 0.0)]
    for k in range(1, 9):
        t = k / 8.0
        slack.append((-0.012 - 0.010 * math.sin(t * math.pi), 0.105 * t,
                      -0.055 * math.sin(t * math.pi) - 0.004 * t))
    chn = mlib.tube_along("FD_chain", slack, mlib.circle(0.0035, 6), C)
    mlib.smooth_shade(chn, 38)
    O.place(chn, (fx, L.FD_Y[0] + 0.085, 1.585), (0, 1), (1, 0))
    mlib.set_mat(chn, M['brass'])

    # ========================================================= KITCHEN WINDOW
    (dxc, dyc), cl = L.chamfer_dir()
    kw = L.KW_U[1] - L.KW_U[0]
    kh = L.KW_Z[1] - L.KW_Z[0]
    kc = L.chamfer_pt((L.KW_U[0] + L.KW_U[1]) * 0.5, 0.0)
    inw = (dyc, -dxc)           # into the room
    kl = O.lining("KW_lining", kw, kh, L.TW, 0.022, C, M['turq'])
    mlib.translate(kl, (0, 0, 0))
    O.place(kl, (kc[0], kc[1], L.KW_Z[0]), (dxc, dyc), (-inw[0], -inw[1]))
    kcs = O.casing("KW_casing", kw, kh, 0.105, 0.022, C, M['turq'], sides=4)
    kcs.data.transform(Matrix.Translation((0, 0, -kh * 0.5)))
    O.place(kcs, (kc[0], kc[1], L.KW_Z[0] + kh * 0.5), (dxc, dyc), inw)
    kf, kg = O.steel_window("KW", kw - 0.030, kh - 0.030, [1], 4, frame_w=0.050,
                            frame_d=0.062, mun_w=0.026, mun_d=0.030, cname=C,
                            mat=M['turq'], glass=M['glass'], cols_per_bay=2,
                            glass_back=0.014)
    for o in (kf, kg):
        o.data.transform(Matrix.Translation((0, 0, L.KW_Z[0] + 0.015)))
        O.place(o, (kc[0], kc[1], 0.0), (dxc, dyc), (-inw[0], -inw[1]))
    # outside sill
    sl = mlib.box("KW_sill", -kw / 2 - 0.05, 0.0, -0.05, kw / 2 + 0.05, 0.18, 0.0, C)
    mlib.bevel(sl, 0.006, 2, 40)
    O.place(sl, (kc[0], kc[1], L.KW_Z[0]), (dxc, dyc), (-inw[0], -inw[1]))
    mlib.set_mat(sl, M['stone'])

    # ============================================================ HUGE WINDOW
    bw = L.BW_X[1] - L.BW_X[0]
    bh = L.BW_TOP - L.BW_SILL
    bcx = (L.BW_X[0] + L.BW_X[1]) * 0.5
    # ONE window, sill to head, tilted a few degrees so the head leans into the
    # room - living_room.jpeg shows a single continuous steel grid, not a
    # vertical light with a separate raked one stacked on top.  The old pair
    # raked 38.7 degrees over its upper half, which drove the bay 1.53 m deep
    # and held the drapes 1.42 m off the glass.
    ang = math.pi / 2 - L.BW_TILT                  # slope measured from horizontal
    slope_len = (L.BW_HEAD - L.BW_SILL) / math.cos(L.BW_TILT)
    bf, bg = O.steel_window("BW", bw - 0.02, slope_len - 0.01, [1, 1.15, 1], 7,
                            frame_w=0.068, frame_d=0.075, mull_w=0.055,
                            mun_w=0.026, mun_d=0.032, cname=C, mat=M['steel_dk'],
                            glass=M['glass'], cols_per_bay=2, glass_back=0.018)
    for o in (bf, bg):
        # The head leans SOUTH, in over the room - the glass tips towards you as
        # it rises, which is the direction the set's window slopes.  +tilt here;
        # negating it tips the head out over the street instead.
        o.data.transform(Matrix.Rotation(math.pi / 2 - ang, 4, 'X'))
        O.place(o, (bcx, 0.0, 0.0), (1, 0), (0, 1))
        mlib.translate(o, (0, L.AL_Y[1] - 0.008, L.BW_SILL + 0.006))
    # The glass leans in off the wall plane, so the reveal at each jamb is a
    # triangle: nothing at the sill, BW_LEAN wide by the head.  The alcove's own
    # ceiling caps it from above.
    for i, (a, b) in enumerate(((L.BW_X[0] - 0.075, L.BW_X[0] + 0.012),
                                (L.BW_X[1] - 0.012, L.BW_X[1] + 0.075))):
        ck = mlib.prism_yz("BW_cheek_%d" % i,
                           [(L.NYW, L.BW_SILL), (L.NYW, L.BW_HEAD),
                            (L.NYW - L.BW_LEAN, L.BW_HEAD)], a, b, C)
        mlib.set_mat(ck, mats.get('wall_lavender'))
    # stone sill inside + out
    si = mlib.box("BW_sill_in", L.BW_X[0] - 0.06, L.AL_Y[1] - 0.02, L.BW_SILL - 0.055,
                  L.BW_X[1] + 0.06, L.AL_Y[1] + L.TW + 0.10, L.BW_SILL, C)
    mlib.bevel(si, 0.008, 2, 40)
    mlib.set_mat(si, M['stone'])
    # Matchstick blinds hanging on the rake (interior side).  These were single
    # flat quads: with no relief and all the daylight behind them they rendered
    # as dark plates.  Built as real battens instead, so the light rakes across
    # their edges and passes between them.
    # They hang down the upper half of the single window now, as in the crop -
    # head just under the window head, dropping roughly to mid-pane.
    PITCH, SLAT, THK = 0.0175, 0.0128, 0.0075
    for i, (a, b) in enumerate(((L.BW_X[0] + 0.03, L.BW_X[0] + bw / 3 - 0.02),
                                (L.BW_X[0] + bw / 3 + 0.02, L.BW_X[0] + 2 * bw / 3 - 0.02),
                                (L.BW_X[0] + 2 * bw / 3 + 0.02, L.BW_X[1] - 0.03))):
        t = 0.50 if i != 1 else 0.58
        # unit vector DOWN the leaning glass, and its inward normal
        uy, uz = math.sin(L.BW_TILT), -math.cos(L.BW_TILT)
        ny, nz = uz, -uy                       # south, i.e. into the room
        y0 = L.NYW - L.BW_LEAN + ny * 0.055
        z0 = L.BW_HEAD - 0.055
        run = (L.BW_HEAD - L.BW_SILL) / math.cos(L.BW_TILT) * t
        slats = []
        n = max(2, int(run / PITCH))
        for k in range(n):
            s0 = k * PITCH
            s1 = min(s0 + SLAT, run)
            # a batten is slightly proud at its lower edge, as a woven shade is
            quad = []
            for (s, o) in ((s0, -THK / 2), (s1, -THK / 2),
                           (s1, THK / 2), (s0, THK / 2)):
                quad.append((y0 + uy * s + ny * o, z0 + uz * s + nz * o))
            slats.append(mlib.prism_yz("BWR_slat", quad, a, b, C))
        # head rail and hem bar
        for (s, hh) in ((-0.012, 0.026), (run + 0.004, 0.030)):
            quad = [(y0 + uy * s + ny * -0.011, z0 + uz * s + nz * -0.011),
                    (y0 + uy * (s + hh) + ny * -0.011,
                     z0 + uz * (s + hh) + nz * -0.011),
                    (y0 + uy * (s + hh) + ny * 0.011,
                     z0 + uz * (s + hh) + nz * 0.011),
                    (y0 + uy * s + ny * 0.011, z0 + uz * s + nz * 0.011)]
            slats.append(mlib.prism_yz("BWR_bar", quad, a, b, C))
        ob = mlib.join(slats, "BWR_blind_%d" % i, C)
        mlib.set_mat(ob, M['blind'])

    # ================= BATHROOM DOOR (hallway west wall, faces east) ========
    bdw = L.BD_Y[1] - L.BD_Y[0]
    bdc = (L.BD_Y[0] + L.BD_Y[1]) * 0.5
    bl = O.lining("BD_lining", bdw, L.BD_H, 0.16, 0.022, "Hall", M['trim'])
    O.place(bl, (L.HALL_X[0], bdc, 0.0), (0, -1), (-1, 0))
    bcs = O.casing("BD_casing", bdw, L.BD_H, 0.090, 0.022, "Hall", M['trim'])
    O.place(bcs, (L.HALL_X[0], bdc, 0.0), (0, -1), (1, 0))
    # Left standing open.  It has to swing *out* into the hall: the pan sits
    # only 120 mm behind the closed leaf on the bathroom side, so an inward leaf
    # jams on the bowl at about fifteen degrees and can go no further.  Hinged
    # on the north jamb, which puts the open leaf north of the hall table
    # opposite and leaves the doorway itself clear from the living room.
    # Now that the bathroom is a proper room and the WC has moved off the east
    # wall, the leaf swings *in* - which is where a bathroom door belongs.  It
    # used to open into the hallway only because it fouled the bowl at about
    # fifteen degrees the other way.
    swing_leaf("BD_leaf", bdw - 0.050, L.BD_H - 0.028,
               (L.HALL_WW[0] + 0.030, L.BD_Y[1] - 0.045), (0.0, -1.0), 84.0, M,
               "Bathroom", M['trim'], t=0.040)

    # ============ CLOSET DOOR (green, head of the hallway, faces south) =====
    clw = L.CL_X[1] - L.CL_X[0]
    clc = (L.CL_X[0] + L.CL_X[1]) * 0.5
    cll = O.lining("CL_lining", clw, L.CL_H, 0.30, 0.022, "Hall", M['green_door'])
    O.place(cll, (clc, L.NW_Y, 0.0), (1, 0), (0, 1))
    clcs = O.casing("CL_casing", clw, L.CL_H, 0.092, 0.024, "Hall", M['green_door'])
    O.place(clcs, (clc, L.NW_Y, 0.0), (1, 0), (0, -1))
    cld = O.panel_door("CL_leaf", clw - 0.050, L.CL_H - 0.028, 0.040,
                       rows=(0.28, 0.28, 0.22, 0.22), stile=0.108, rail=0.118,
                       mid=0.082, cname="Hall", mat=M['green_door'])
    mlib.translate(cld, (0, 0.040, 0.010))
    O.place(cld, (clc, L.NW_Y, 0.0), (1, 0), (0, 1))
    kn3 = O.knob_set("CL_knob", "Hall", M['brass'])
    O.place(kn3, (L.CL_X[1] - 0.13, L.NW_Y - 0.040, 1.00), (1, 0), (0, -1))

    # ============ RACHEL'S DOORWAY: cased opening + transom, as photographed ==
    TWALL = L.EXW - L.EX
    cdw = L.CD_Y[1] - L.CD_Y[0]
    cdc = (L.CD_Y[0] + L.CD_Y[1]) * 0.5
    cl2 = O.lining("CD_lining", cdw, L.CD_TOP, TWALL, 0.024, C, M['trim'])
    O.place(cl2, (L.EX, cdc, 0.0), (0, -1), (1, 0))
    ccs = O.casing("CD_casing", cdw, L.CD_TOP, 0.100, 0.026, C, M['trim'])
    O.place(ccs, (L.EX, cdc, 0.0), (0, -1), (-1, 0))
    ccs2 = O.casing("CD_casing_out", cdw, L.CD_TOP, 0.075, 0.018, C, M['trim'])
    O.place(ccs2, (L.EXW, cdc, 0.0), (0, -1), (1, 0))
    hr2 = mlib.box("CD_headrail", -cdw / 2, 0.0, L.CD_H, cdw / 2, TWALL,
                   L.CD_H + 0.075, C)
    O.place(hr2, (L.EX, cdc, 0.0), (0, -1), (1, 0))
    mlib.set_mat(hr2, M['trim'])
    tf2, tg2 = O.steel_window("CD_transom", cdw - 0.048,
                              L.CD_TOP - L.CD_H - 0.085, [1], 1, frame_w=0.046,
                              frame_d=0.050, cname=C, mat=M['trim'],
                              glass=M['glass_frost'], cols_per_bay=1,
                              glass_back=0.008)
    for o in (tf2, tg2):
        o.data.transform(Matrix.Translation((0, 0, L.CD_H + 0.085)))
        O.place(o, (L.EX, cdc, 0.0), (0, -1), (1, 0))
    # Rachel's leaf, standing open into her room (hinged on the north jamb)
    swing_leaf("CD_leaf", cdw - 0.055, L.CD_H - 0.030,
               (L.EX + 0.052, L.CD_Y[1] - 0.028), (0.0, -1.0), -104.0, M,
               C, M['trim'])

    # ===== MONICA'S BEDROOM DOOR: in the central wall, south of the alcove ====
    # In living_room.jpeg this door is clear of the window bay with a stretch of
    # wall between the two, and it carries the same frosted transom as Rachel's.
    mdw = L.MD_Y[1] - L.MD_Y[0]
    mdc = (L.MD_Y[0] + L.MD_Y[1]) * 0.5
    ml2 = O.lining("MD_lining", mdw, L.MD_TOP, TWALL, 0.024, "Bedrooms",
                   M['trim'])
    O.place(ml2, (L.EX, mdc, 0.0), (0, -1), (1, 0))
    mcs = O.casing("MD_casing", mdw, L.MD_TOP, 0.095, 0.024, "Bedrooms",
                   M['trim'])
    O.place(mcs, (L.EX, mdc, 0.0), (0, -1), (-1, 0))
    mcs2 = O.casing("MD_casing_in", mdw, L.MD_TOP, 0.080, 0.020, "Bedrooms",
                    M['trim'])
    O.place(mcs2, (L.EXW, mdc, 0.0), (0, -1), (1, 0))
    # head rail between leaf and transom, then the transom itself
    hr3 = mlib.box("MD_headrail", -mdw / 2, 0.0, L.MD_H, mdw / 2, TWALL,
                   L.MD_H + 0.075, "Bedrooms")
    O.place(hr3, (L.EX, mdc, 0.0), (0, -1), (1, 0))
    mlib.set_mat(hr3, M['trim'])
    tf3, tg3 = O.steel_window("MD_transom", mdw - 0.048,
                              L.MD_TOP - L.MD_H - 0.085, [1], 1, frame_w=0.046,
                              frame_d=0.050, cname="Bedrooms", mat=M['trim'],
                              glass=M['glass_frost'], cols_per_bay=1,
                              glass_back=0.008)
    for o in (tf3, tg3):
        o.data.transform(Matrix.Translation((0, 0, L.MD_H + 0.085)))
        O.place(o, (L.EX, mdc, 0.0), (0, -1), (1, 0))
    # left standing open, swinging east into the bedroom (hinged on the south
    # jamb) exactly as the plan's swing arc shows
    swing_leaf("MD_leaf", mdw - 0.055, L.MD_H - 0.030,
               (L.EX + 0.052, L.MD_Y[0] + 0.028), (0.0, 1.0), 104.0, M,
               "Bedrooms", M['trim'])

    # ============================= bedroom windows ==========================
    for nm, cy in (("RW", L.RB_WIN_Y), ("MW", L.MB_WIN_Y)):
        bw, bh = 1.24, 1.38
        wl = O.lining(nm + "_lining", bw, bh, L.TW, 0.022, "Bedrooms", M['trim'])
        wl.data.transform(Matrix.Translation((0, 0, 0.86)))
        O.place(wl, (L.EXT_E, cy, 0.0), (0, 1), (1, 0))
        wcs = O.casing(nm + "_casing", bw, bh, 0.090, 0.020, "Bedrooms",
                       M['trim'], sides=4)
        wcs.data.transform(Matrix.Translation((0, 0, 0.86 + bh * 0.5)))
        O.place(wcs, (L.EXT_E, cy, 0.0), (0, 1), (-1, 0))
        wf, wg = O.steel_window(nm, bw - 0.030, bh - 0.030, [1], 3,
                                frame_w=0.048, frame_d=0.060, mun_w=0.024,
                                mun_d=0.028, cname="Bedrooms", mat=M['trim'],
                                glass=M['glass'], cols_per_bay=2,
                                glass_back=0.014)
        for o in (wf, wg):
            o.data.transform(Matrix.Translation((0, 0, 0.875)))
            O.place(o, (L.EXT_E, cy, 0.0), (0, 1), (1, 0))
        sl2 = mlib.box(nm + "_sill", -bw / 2 - 0.06, -0.02, -0.055,
                       bw / 2 + 0.06, 0.20, 0.0, "Bedrooms")
        mlib.bevel(sl2, 0.006, 2, 40)
        sl2.data.transform(Matrix.Translation((0, 0, 0.86)))
        O.place(sl2, (L.EXT_E, cy, 0.0), (0, 1), (1, 0))
        mlib.set_mat(sl2, M['stone'])
    print("openings built")
    return M
