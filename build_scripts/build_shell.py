"""Build the architectural shell: floor, walls, ceilings, mouldings, timber."""
import bpy, math
import mlib, mats, L, s_floor, s_walls as W

CZ, RAIL, TW, TP = L.CZ, L.RAIL, L.TW, L.TP


# ------------------------------------------------------------------- materials
def build_mats():
    M = {}
    # the set floor is a pale tan oak parquet; the old mix was a full step too
    # red and made every wide shot read orange
    M['parquet'] = mats.wood('parquet_oak',
                             ('C8AC80', 'AB8C61', '866A42'),
                             ring=62.0, warp=0.06, warp_scale=1.0, distort=0.7,
                             blotch=0.12, coord='UV', axis='X',
                             bump=0.22, pore=1.0, tint_attr='ptint',
                             rough=(0.16, 0.34), aniso=0.4)
    M['lav'] = mats.plaster('wall_lavender', L.LAV, rough=0.68, bump=0.26, scale=30)
    M['cream'] = mats.plaster('wall_cream', L.CREAM, rough=0.74, bump=0.30, scale=26)
    M['ceil'] = mats.plaster('ceiling_cream', 'EFE6CB', rough=0.82, bump=0.34, scale=20)
    M['brick'] = mats.brick_wall('brick_kitchen')
    M['tile'] = mats.subway_tile('tile_kitchen', size=0.084, stack=True)
    M['bathtile'] = mats.subway_tile('tile_bath', size=0.075, hexcol='EFEFE8',
                                     grout='BFBCAE', stack=False)
    M['green'] = mats.paint('paint_green_dado', L.GREEN_DADO, rough=0.28, coat=0.22)
    M['trim'] = mats.paint('paint_lav_trim', L.LAV_TRIM, rough=0.26, coat=0.25)
    # Near-uniform on purpose.  In every set photo the dropped beam and the
    # posts are plain stained timber - you read them by their colour and their
    # rough surface, not by grain lines.  Any real early/late-wood contrast at
    # this size draws long parallel bands that look like a contour map.
    BEAMC = ('85613D', '805C3A', '7B5737')
    # 90 rings/m with almost no warp gave the posts and the dropped beam a
    # machined pinstripe; reclaimed timber is coarse and wanders.  But the
    # cathedral shove has to stay small on a member this long: `distort` moves
    # the ring axis in metres, so at 1.8 a six-metre beam picked up sweeping
    # arcs across its whole face and read as a contour map.  A big sawn baulk
    # shows long, roughly parallel grain, and the contrast between early and
    # late wood on old stained timber is low.
    BK = dict(ring=11.0, warp=0.018, warp_scale=1.1, distort=0.15, blotch=0.32,
              bump=0.34, rough=(0.34, 0.58), aniso=0.18, grain_relief=0.06)
    # rings vary across the member, so the grain runs along its length
    M['beam'] = mats.wood('wood_beam', BEAMC, axis='YZ', **BK)     # runs along X
    M['beam_y'] = mats.wood('wood_beam_y', BEAMC, axis='XZ', **BK)  # runs along Y
    M['beam_v'] = mats.wood('wood_beam_v', BEAMC, axis='XY', **BK)  # vertical
    M['beam_z'] = mats.wood('wood_beam_z', BEAMC, axis='Z', **BK)   # diagonal plan
    M['corr'] = mats.plaster('wall_corridor', 'C09258', rough=0.62, bump=0.22)
    M['corrwood'] = mats.wood('wood_corridor', ('9C6A38', '73441F', '43250F'),
                              ring=16.0, warp=0.6, bump=0.25)
    M['stone'] = mats.plaster('stone_sill', '8D897E', rough=0.62, bump=0.5, scale=48)
    return M


# ----------------------------------------------------------------------- build
def build():
    mlib.purge()
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for nm in ("Shell", "Trim", "Openings", "Kitchen", "Dining", "Living",
               "Details", "Lighting", "Corridor", "Bathroom", "Exterior",
               "Hall"):
        mlib.coll(nm)
    M = build_mats()

    # ---------------------------------------------------------------- floor
    sub = mlib.box("Floor_Sub", -0.6, L.SY - 0.6, -0.02, 12.4, 7.1, 0.0035, "Shell")
    mlib.set_mat(sub, mats.paint('subfloor_dark', '2A1F16', rough=0.8))
    # 0.52 m module: the set's parquet reads big - roughly one tile per stride -
    # and at 0.445 the lattice was fussy enough to shimmer in the wide shots
    par = s_floor.build(-0.45, L.SY - 0.45, 12.3, 6.9, T=0.52)
    mlib.set_mat(par, M['parquet'])

    # ---------------------------------------------------------------- walls
    # -- west: lavender front-door wall (split at the picture rail)
    W.wall("W_west_lo", (0, L.SY), (0, L.W_PLASTER[1]), 0, RAIL, TW,
           [(L.FD_Y[0] - L.SY, 0, L.FD_Y[1] - L.SY, L.FD_TOP)], mat=M['lav'])
    W.wall("W_west_hi", (0, L.SY), (0, L.W_PLASTER[1]), RAIL, CZ, TW,
           mat=M['cream'])
    # -- west: brick
    W.wall("W_west_brick", (0, L.W_BRICK[0]), (0, L.W_BRICK[1]), 0, CZ, TW,
           mat=M['brick'])
    # -- chamfer with the kitchen window
    W.wall("W_chamfer", L.CH_A, L.CH_B, 0, CZ, TW,
           [(L.KW_U[0], L.KW_Z[0], L.KW_U[1], L.KW_Z[1])], mat=M['brick'])
    # -- north brick (counter run + fridge nook); body forms the bathroom's south wall
    W.wall("W_north_brick", (L.N_BRICK[0], L.NY), (L.N_BRICK[1], L.NY), 0, CZ, TP,
           mat=M['brick'])
    # -- hallway west wall: one solid, brick on the kitchen side, lavender/cream
    #    on the hallway side, bathroom door through it
    hw = W.wall("W_hall_w", (L.HALL_X[0], L.HALL_Y0), (L.HALL_X[0], L.AL_Y[1]),
                0, CZ, L.HALL_X[0] - L.HALL_WW[0],
                [(L.BD_Y[0] - L.HALL_Y0, 0, L.BD_Y[1] - L.HALL_Y0, L.BD_H)],
                mat=M['lav'], mats_extra=[M['cream'], M['brick']])
    xm = (L.HALL_WW[0] + L.HALL_X[0]) * 0.5
    mlib.face_mat(hw, 1, lambda c, n: c.x > xm and c.z > RAIL)
    mlib.face_mat(hw, 2, lambda c, n: c.x < xm)
    # -- hallway north wall (exterior) with the green closet door + dado
    W.wall("W_hall_n_lo", (L.HALL_X[0], L.AL_Y[1]), (L.HALL_X[1], L.AL_Y[1]),
           0, 1.10, 0.30,
           [(L.CL_X[0] - L.HALL_X[0], 0, L.CL_X[1] - L.HALL_X[0], 1.10)],
           mat=M['green'])
    W.wall("W_hall_n_hi", (L.HALL_X[0], L.AL_Y[1]), (L.HALL_X[1], L.AL_Y[1]),
           1.10, CZ, 0.30,
           [(L.CL_X[0] - L.HALL_X[0], 1.10, L.CL_X[1] - L.HALL_X[0], L.CL_H)],
           mat=M['cream'])
    # closet cavity behind the green door
    cav = mlib.box("W_closet", L.HALL_X[0] + 0.02, L.AL_Y[1] + 0.30, 0.0,
                   L.HALL_X[1] - 0.02, L.AL_Y[1] + 0.34, L.CL_H + 0.20, "Hall")
    mlib.set_mat(cav, mats.paint('closet_dark', '3B342C', rough=0.8))
    for zz in (0.55, 1.05, 1.55):
        sh = mlib.box("W_closet_shelf", L.HALL_X[0] + 0.03, L.AL_Y[1] + 0.20, zz,
                      L.HALL_X[1] - 0.03, L.AL_Y[1] + 0.30, zz + 0.020, "Hall")
        mlib.set_mat(sh, M['trim'])
    # -- hallway east wall = alcove west wall: green dado + cream on the hall
    #    side, lavender on the alcove side
    he = W.wall("W_hall_e", (L.HALL_X[1], L.AL_Y[1]), (L.HALL_X[1], L.NY),
                0, CZ, L.HALL_EW[1] - L.HALL_EW[0], mat=M['green'],
                mats_extra=[M['cream'], M['lav']])
    xe = (L.HALL_EW[0] + L.HALL_EW[1]) * 0.5
    mlib.face_mat(he, 1, lambda c, n: c.x < xe and c.z > 1.10)
    mlib.face_mat(he, 2, lambda c, n: c.x > xe)
    # -- north exterior wall of the alcove: huge window, wall stops at BW_TOP
    W.wall("W_alcove_n", (L.AL_X[0], L.AL_Y[1]), (L.AL_X[1], L.AL_Y[1]), 0, L.BW_TOP,
           TW, [(L.BW_X[0] - L.AL_X[0], L.BW_SILL, L.BW_X[1] - L.AL_X[0], L.BW_TOP)],
           mat=M['lav'])
    # -- header over the alcove opening
    W.wall("W_alcove_hdr", (L.AL_X[0], L.NY), (L.AL_X[1], L.NY), L.AL_Z, CZ, 0.22,
           mat=M['cream'])
    # -- central wall: Rachel's doorway at the south, Monica's door at the north
    u = lambda y: L.NYW - y
    W.wall("W_east_lo", (L.EX, L.NYW), (L.EX, L.SY), 0, RAIL, L.EXW - L.EX,
           [(u(L.CD_Y[1]), 0, u(L.CD_Y[0]), L.CD_TOP),
            (u(L.MD_Y[1]), 0, u(L.MD_Y[0]), L.MD_H)],
           mat=M['lav'], mats_extra=[M['cream']])
    W.wall("W_east_hi", (L.EX, L.NYW), (L.EX, L.SY), RAIL, CZ, L.EXW - L.EX,
           mat=M['cream'])
    # -- south (fourth) wall, now running the full width including the bedrooms
    W.wall("W_south_lo", (L.EXT_E, L.SY), (0, L.SY), 0, RAIL, TW, mat=M['lav'])
    W.wall("W_south_hi", (L.EXT_E, L.SY), (0, L.SY), RAIL, CZ, TW, mat=M['cream'])

    # ---------------------------------------------------------- bathroom shell
    W.wall("W_bath_n", (L.BA_X[0], L.BA_Y[1]), (L.BA_X[1], L.BA_Y[1]), 0, L.AL_Z,
           TW, mat=M['bathtile'], cname="Bathroom")
    W.wall("W_bath_w", (L.BA_X[0], L.BA_Y[0]), (L.BA_X[0], L.BA_Y[1]), 0, L.AL_Z,
           TW, mat=M['bathtile'], cname="Bathroom")
    o = mlib.box("W_bath_s_liner", L.BA_X[0], L.BA_Y[0] + 0.002, 0.0,
                 L.BA_X[1], L.BA_Y[0] + 0.014, L.AL_Z, "Bathroom")
    mlib.set_mat(o, M['bathtile'])
    # The east liner is the bathroom's face of the hall wall, so it has to carry
    # that wall's door void with it.  As one slab it tiled straight across the
    # opening and sealed the doorway shut - invisible for as long as the leaf
    # stood closed in front of it.
    ex0, ex1 = L.BA_X[1] - 0.014, L.BA_X[1] - 0.002
    for nm, y0, y1, z0 in (("W_bath_e_liner_s", L.BA_Y[0], L.BD_Y[0], 0.0),
                           ("W_bath_e_liner_n", L.BD_Y[1], L.BA_Y[1], 0.0),
                           ("W_bath_e_liner_h", L.BD_Y[0], L.BD_Y[1], L.BD_H)):
        o = mlib.box(nm, ex0, y0, z0, ex1, y1, L.AL_Z, "Bathroom")
        mlib.set_mat(o, M['bathtile'])
    bc = mlib.box("C_bath", L.BA_X[0], L.BA_Y[0], L.AL_Z,
                  L.BA_X[1], L.BA_Y[1], L.AL_Z + 0.08, "Bathroom")
    mlib.set_mat(bc, M['ceil'])

    # ------------------------------------------------- bedroom block (east)
    B = "Bedrooms"
    mlib.coll(B)
    # dividing wall between the two bedrooms
    W.wall("W_bed_div_s", (L.BED_X[0], L.BED_DIV[0]), (L.BED_X[1], L.BED_DIV[0]),
           0, CZ, L.BED_DIV[1] - L.BED_DIV[0], mat=M['lav'],
           mats_extra=[M['cream']], cname=B)
    dv = bpy.data.objects["W_bed_div_s"]
    ym = (L.BED_DIV[0] + L.BED_DIV[1]) * 0.5
    mlib.face_mat(dv, 1, lambda c, n: c.z > RAIL)
    # east exterior wall with a window behind each bed head
    wz = (0.86, 2.24)
    holes = []
    for cy in (L.RB_WIN_Y, L.MB_WIN_Y):
        holes.append((L.NYW - (cy + 0.62), wz[0], L.NYW - (cy - 0.62), wz[1]))
    W.wall("W_bed_e_lo", (L.EXT_E, L.NYW), (L.EXT_E, L.SY), 0, RAIL, TW, holes,
           mat=M['lav'], cname=B)
    W.wall("W_bed_e_hi", (L.EXT_E, L.NYW), (L.EXT_E, L.SY), RAIL, CZ, TW,
           mat=M['cream'], cname=B)
    # north exterior wall of Monica's room
    W.wall("W_bed_n", (L.BED_X[0], L.NYW), (L.BED_X[1], L.NYW), 0, CZ, TW,
           mat=M['lav'], mats_extra=[M['cream']], cname=B)
    bn = bpy.data.objects["W_bed_n"]
    mlib.face_mat(bn, 1, lambda c, n: c.z > RAIL)
    for nm, y0, y1 in (("C_bed_r", L.RB_Y[0], L.RB_Y[1]),
                       ("C_bed_m", L.MB_Y[0], L.MB_Y[1])):
        c = mlib.box(nm, L.BED_X[0], y0, CZ, L.BED_X[1], y1, CZ + 0.10, B)
        mlib.set_mat(c, M['ceil'])

    # ------------------------------------------------------------- ceilings
    main_poly = [(0, L.SY), (0, L.CH_A[1]), L.CH_B, (L.N_BRICK[1], L.NY),
                 (L.HALL_WW[0], L.HALL_Y0), (L.HALL_X[0], L.HALL_Y0),
                 (L.HALL_X[0], L.AL_Y[1]), (L.HALL_X[1], L.AL_Y[1]),
                 (L.HALL_X[1], L.NY), (L.EX, L.NY), (L.EX, L.SY)]
    ceil = mlib.prism("C_main", main_poly, CZ, CZ + 0.10, "Shell")
    mlib.set_mat(ceil, M['ceil'])
    alc = mlib.box("C_alcove", L.AL_X[0], L.NY, L.AL_Z, L.AL_X[1], L.RAKE_Y,
                   L.AL_Z + 0.10, "Shell")
    mlib.set_mat(alc, M['ceil'])

    # ---------------------------------------------------------------- trim
    per = [(L.EX, L.NY), (L.EX, L.SY), (0, L.SY), (0, L.CH_A[1]), L.CH_B,
           (L.N_BRICK[1], L.NY), (L.HALL_WW[0], L.HALL_Y0),
           (L.HALL_X[0], L.HALL_Y0), (L.HALL_X[0], L.AL_Y[1]),
           (L.HALL_X[1], L.AL_Y[1]), (L.HALL_X[1], L.NY), (L.EX, L.NY)]
    W.run_molding("T_cove", per, W.CROWN_PROF, mat=M['ceil'])
    W.run_molding("T_cove_alcove",
                  [(L.AL_X[0], L.NY), (L.AL_X[0], L.RAKE_Y)], W.ALCOVE_CROWN,
                  mat=M['ceil'])
    W.run_molding("T_cove_alcove2",
                  [(L.AL_X[1], L.RAKE_Y), (L.AL_X[1], L.NY)], W.ALCOVE_CROWN,
                  mat=M['ceil'])
    W.run_molding("T_rail", [(L.EX, L.CD_Y[1] + 0.06), (L.EX, L.SY), (0, L.SY),
                             (0, L.W_PLASTER[1])], W.RAIL_PROF, mat=M['beam'])
    W.run_molding("T_rail2", [(L.EX, L.NY), (L.EX, L.MD_Y[1] + 0.06)],
                  W.RAIL_PROF, mat=M['beam'])
    W.run_molding("T_rail3", [(L.EX, L.MD_Y[0] - 0.06), (L.EX, L.CD_Y[1] + 0.06)],
                  W.RAIL_PROF, mat=M['beam'], cap=True)
    W.run_molding("T_rail_hall",
                  [(L.HALL_X[0], L.AL_Y[1]), (L.HALL_X[0], L.HALL_Y0)],
                  W.RAIL_PROF, mat=M['beam'])
    # baseboards (broken at door openings and at brickwork)
    for i, p in enumerate([
        [(L.EX, L.CD_Y[0]), (L.EX, L.SY), (0, L.SY), (0, L.FD_Y[0])],
        [(0, L.FD_Y[1]), (0, L.W_PLASTER[1])],
        [(L.EX, L.NY), (L.EX, L.MD_Y[1])],
        [(L.EX, L.MD_Y[0]), (L.EX, L.CD_Y[1])],
        [(L.HALL_X[0], L.BD_Y[0]), (L.HALL_X[0], L.HALL_Y0)],
        [(L.HALL_X[0], L.AL_Y[1]), (L.HALL_X[0], L.BD_Y[1])],
        [(L.HALL_X[1], L.AL_Y[1]), (L.HALL_X[1], L.NY)],
        [(L.AL_X[0], L.NY), (L.AL_X[0], L.AL_Y[1]), (L.AL_X[1], L.AL_Y[1])],
    ]):
        W.run_molding("T_base_%d" % i, p, W.BASE_PROF, mat=M['trim'])
    # chair rail capping the green dado in the hallway
    CHAIR = [(1.078, 0.0012), (1.078, 0.0230), (1.098, 0.0265),
             (1.110, 0.0195), (1.110, 0.0012)]
    W.run_molding("T_chair_hn1", [(L.HALL_X[0], L.AL_Y[1]), (L.CL_X[0], L.AL_Y[1])],
                  CHAIR, mat=M['green'])
    W.run_molding("T_chair_hn2", [(L.CL_X[1], L.AL_Y[1]), (L.HALL_X[1], L.AL_Y[1])],
                  CHAIR, mat=M['green'])
    W.run_molding("T_chair_he", [(L.HALL_X[1], L.AL_Y[1]), (L.HALL_X[1], L.NY)],
                  CHAIR, mat=M['green'])

    # ------------------------------------------------- wall panel mouldings
    # Panels are laid out per *solid* wall stretch, so none of them ever runs
    # across a doorway or gets sliced into a sliver, and the gaps either side of
    # a run come out equal.  On the set they are tall panels whose bottom rail
    # sits well above the baseboard.
    PAN_Z0, PAN_Z1 = 0.60, 2.52
    PAN_CZ, PAN_H = (PAN_Z0 + PAN_Z1) / 2, PAN_Z1 - PAN_Z0
    pan = []

    def panel_run(tag, a, b, normal, at, horiz, want=1.30, margin=0.34):
        """Fill the stretch a..b with as many equal panels as fit."""
        span = b - a
        n = max(1, int(round((span - margin) / (want + margin))))
        w = (span - (n + 1) * margin) / n
        if w < 0.42:
            return
        for i in range(n):
            c = a + margin + w * 0.5 + i * (w + margin)
            cx, cy = (c, at) if horiz == 'x' else (at, c)
            pan.append(W.panel_moulding("P_%s_%d" % (tag, i), cx, cy, PAN_CZ, w,
                                        PAN_H, normal, mat=M['trim']))

    # south ('back') wall - broken by the timber post that carries the beam
    panel_run("s0", 0.0, L.POST_X[0], (0, 1), L.SY, 'x')
    panel_run("s1", L.POST_X[1], L.EX, (0, 1), L.SY, 'x')
    # east wall - three solid stretches: south of Rachel's opening, behind the
    # credenza (skipped: the Jouets poster lives there), and north of it
    panel_run("e0", L.SY, L.CD_Y[0], (-1, 0), L.EX, 'y')
    panel_run("e1", L.TV_C[1] + L.CRED_HW, L.NY, (-1, 0), L.EX, 'y')

    # ------------------------------------------------------- kitchen timber
    bz0, bz1 = L.BEAM_Z
    bx0, bx1 = L.BEAM_X
    by0, by1 = L.BEAM_Y
    px0, px1 = L.POST_X
    beams = []
    # THE beam: a single dropped timber running north-south on the line that
    # divides the kitchen from the living room (see stylized_ref/1.png)
    beams.append((mlib.box("B_main", bx0, by0 - TW, bz0, bx1, by1, bz1, "Shell"),
                  M['beam_y']))
    # wall plates along the top of the brickwork
    beams.append((mlib.box("B_plate_w", 0.0, L.W_BRICK[0], bz0, 0.135, L.CH_A[1],
                           bz1, "Shell"), M['beam_y']))
    beams.append((mlib.box("B_plate_n", L.N_BRICK[0], L.NY - 0.135, bz0,
                           L.HALL_WW[0], L.NY, bz1, "Shell"), M['beam']))
    cp = [L.chamfer_pt(0.0, 0.0), L.chamfer_pt(1.44, 0.0),
          L.chamfer_pt(1.44, 0.135), L.chamfer_pt(0.0, 0.135)]
    beams.append((mlib.prism("B_plate_ch", cp, bz0, bz1, "Shell"), M['beam_z']))
    for b, mm in beams:
        mlib.set_mat(b, mm)
        mlib.bevel(b, 0.007, 2, 45)
    # post at the beam's north end, where kitchen, hall and living room meet
    post = mlib.box("B_post", px0, by1 - 0.20, 0.0, px1, by1, bz0 + 0.002, "Shell")
    mlib.bevel(post, 0.008, 2, 45)
    mlib.set_mat(post, M['beam_v'])
    # knee brace in the plane of the beam
    d = 0.50
    ya, za = by1 - 0.20, bz0 - d
    br = mlib.prism_yz("B_brace",
                       [(ya, za), (ya - 0.115, za + 0.115),
                        (ya - 0.115 - d, za + 0.115 + d), (ya - d, za + d)],
                       bx0 + 0.024, bx1 - 0.024, "Shell")
    for v in br.data.vertices:               # mirror so the brace leans south
        v.co.y = 2 * ya - v.co.y
    mlib.recalc_normals(br)
    mlib.bevel(br, 0.006, 2, 45)
    mlib.set_mat(br, M['beam_y'])

    # ------------------------------------------ kitchen tile splash + sills
    tiles = []
    tiles.append(mlib.box("K_tile_w", 0.0015, L.W_BRICK[0], 0.86, 0.0135, L.CH_A[1],
                          1.52, "Kitchen"))
    tiles.append(mlib.box("K_tile_n", L.N_BRICK[0], L.NY - 0.0135, 0.86,
                          L.FRIDGE_X[0], L.NY - 0.0015, 1.52, "Kitchen"))
    ct = mlib.prism("K_tile_ch", [L.chamfer_pt(0.02, 0.0015),
                                  L.chamfer_pt(1.40, 0.0015),
                                  L.chamfer_pt(1.40, 0.0135),
                                  L.chamfer_pt(0.02, 0.0135)], 0.86, 1.52,
                    "Kitchen")
    tiles.append(ct)
    for t in tiles:
        mlib.set_mat(t, M['tile'])

    print("shell built:", len(bpy.data.objects), "objects")
    return M
