"""The shell: floors, walls, ceilings, the raised bay platform, the cast-iron
columns and the beams they carry.

Every wall is one closed solid whose *inner* face lands exactly on its line in
L.py, and every opening is cut into that solid's own vertex grid rather than
booleaned in afterwards, so the shell stays manifold and quad-dominant.

Applied trim - skirting, dado rail, cornice - is a separate solid standing
proud of the wall it belongs to.  Nothing is coplanar with anything, so there
is no z-fighting anywhere in the build.
"""
import bpy, math, importlib
import mlib as M
import mats as T
import L

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C_SHELL = "Shell"
C_STRUCT = "Structure"
C_TRIM = "Trim"

MATS = {}


# ------------------------------------------------------------------ materials

def make_materials():
    MATS['concrete'] = T.concrete('floor_concrete', L.CONCRETE)
    MATS['plank'] = T.plank_floor('floor_plank')
    MATS['tile'] = T.dot_tile('tile_bay')
    MATS['brick'] = T.brick('brick_wall')
    # the entrance pier is a warmer, more varied stock than the field walls
    MATS['brick_pier'] = T.brick('brick_pier', face='875033', face2='5E3324',
                                 mortar='8E8171', spread=1.2)
    MATS['plaster_o'] = T.plaster('plaster_ochre', L.OCHRE, rough=0.78)
    MATS['plaster_t'] = T.plaster('plaster_terra', L.TERRA, rough=0.76)
    MATS['plaster_c'] = T.plaster('plaster_cream', L.CREAM, rough=0.8, mottle=0.1)
    MATS['ceiling'] = T.plaster('plaster_ceiling', 'CFC6B2', rough=0.86,
                                mottle=0.07, scale=12.0)
    MATS['green'] = T.paint('paint_green_dado', L.GREEN_DADO, rough=0.30, coat=0.12)
    MATS['iron'] = T.iron('iron_green', L.GREEN_IRON)
    MATS['joinery'] = T.paint('paint_joinery', L.GREEN_IRON, rough=0.26, coat=0.2)
    MATS['wood_dark'] = T.wood('wood_dark', light='8A5A2C', dark='3C2110', ring=30.0)
    MATS['wood_mid'] = T.wood('wood_mid', light='A87540', dark='5A3418', ring=26.0)
    # A warm travertine, not the green serpentine the default gives: the
    # counter top in every set photograph is a brown-and-cream stone and it
    # is the one large light-coloured surface in the middle of the room, so
    # its cast dominates the whole counter end.
    MATS['marble'] = T.marble('marble_counter', base='9A8468',
                              vein='55402A', vein2='D8C8A8', scale=1.8)
    MATS['glass'] = T.glass('glass_window', tint='F2F6F4', rough=0.004,
                            alpha=0.02)
    # The ceiling reads dark in every set photograph - it is above the lamps,
    # so nothing lights it but bounce.  A pale one flattens the whole room.
    MATS['tin'] = T.paint('paint_tin_ceiling', '6E6455', rough=0.56, coat=0.05)
    # the cross beam: an old stained timber, much darker than the ceiling it
    # hangs below, which is the whole reason it reads as a beam at all
    MATS['beam'] = T.wood('wood_beam', light='4C3A28', dark='231A11',
                          ring=8.0, rough=(0.62, 0.80))
    return MATS


# ------------------------------------------------------------------ floors

def floors():
    out = []
    # main room - a grid so the concrete's shading has vertices to sit on
    p = M.ccw(L.main_slab_poly())
    f = M.prism("Floor_main", p, L.SLAB_Z, 0.0, C_SHELL)
    M.set_mat(f, MATS['concrete'])
    out.append(f)

    # the boarded service zone, butting the slab on a line rather than lying
    # on top of it
    a, b, c, d = L.PLANK_ZONE
    o = L.SLAB_OVER
    w = M.prism("Floor_plank", [(a - o, c), (b, c), (b, d + o), (a - o, d + o)],
                L.SLAB_Z2, 0.0, C_SHELL)
    M.set_mat(w, MATS['plank'])
    out.append(w)

    # kitchen
    k = M.prism("Floor_kitchen",
                M.ccw(M.poly_offset(L.kitchen_poly(), L.SLAB_OVER - 0.02)),
                L.SLAB_Z3, 0.004, C_SHELL)
    M.set_mat(k, MATS['tile'])
    out.append(k)

    # The hallway through to the lavatories, and then the lavatories
    # themselves.  Two slabs, not one: the hallway is circulation off the
    # shop and is finished like the shop, and only the rooms at the end of it
    # get a tiled floor.  Laying one tiled slab under both put a lavatory
    # floor in the doorway you see from the couch.
    # Its south edge lands exactly where the main slab and the boards stop,
    # so the three butt on a LINE.  Overlapped, all three tops were the same
    # z = 0 plane under the north wall, which is the same modelling error as
    # any other coplanar pair even though the wall hides it.
    hs = L.NY + L.SLAB_OVER
    hl = M.prism("Floor_hall",
                 [(-L.TW - 0.1, hs), (L.WC_E + L.TW + 0.1, hs),
                  (L.WC_E + L.TW + 0.1, L.HALL_N + L.TP + L.SLAB_OVER),
                  (-L.TW - 0.1, L.HALL_N + L.TP + L.SLAB_OVER)],
                 L.SLAB_Z5, 0.0, C_SHELL)
    M.set_mat(hl, MATS['concrete'])
    out.append(hl)
    # and this one runs on UNDER the hallway's north wall rather than
    # stopping on its face, so no vertical face of the two is shared either
    lb = M.prism("Floor_wc",
                 [(-L.TW - 0.14, L.HALL_N - 0.10),
                  (L.WC_E + L.TW + 0.14, L.HALL_N - 0.10),
                  (L.WC_E + L.TW + 0.14, L.WC_N + L.TW + 0.14),
                  (-L.TW - 0.14, L.WC_N + L.TW + 0.14)],
                 L.SLAB_Z5 + 0.022, 0.004, C_SHELL)
    M.set_mat(lb, MATS['tile'])
    out.append(lb)

    # ---- the window bay: a step up, with a kerb that has a real top face ----
    bp = M.ccw(L.bay_poly())
    plat = M.prism("Floor_bay", M.ccw(M.poly_offset(bp, L.SLAB_OVER)),
                   L.SLAB_Z4, L.STEP, C_SHELL)
    M.set_mat(plat, MATS['tile'])
    out.append(plat)

    # The kerb: a painted timber nosing along the open (west) edge, standing
    # 6 mm proud of the tile so the two never coincide.  It has to reach far
    # enough west to cover the platform's own riser - the slab runs SLAB_OVER
    # past the layout line, so its tiled edge stood 20 mm proud of a kerb that
    # started at EX - 0.10, and that pale strip of tile on edge is the bright
    # step you see from the couch.  In every set photograph the step reads
    # dark against the white floor above it.
    kerb = M.prism("Kerb_bay",
                   [(L.EX - L.SLAB_OVER - 0.05, L.BAY_S),
                    (L.EX + 0.03, L.BAY_S),
                    (L.EX + 0.03, L.BAY_N),
                    (L.EX - L.SLAB_OVER - 0.05, L.BAY_N)],
                   -0.04, L.STEP + 0.006, C_SHELL)
    M.set_mat(kerb, MATS['joinery'])
    M.bevel(kerb, 0.006, 2, 50)
    out.append(kerb)
    return out


# ------------------------------------------------------------------ walls

def walls():
    out = []
    T_ = L.TW
    Z = L.CZ

    # -- west exterior ------------------------------------------------------
    w = M.wall_run("Wall_W", (0.0, 0.0), (0.0, L.WC_N), T_, L.FOUND_Z, Z,
                   cname=C_SHELL, side=+1)
    M.set_mat(w, MATS['brick'])
    out.append(w)

    # -- south exterior (kitchen window + solid main-room stretch) ----------
    s = M.wall_run("Wall_S", (L.EX, 0.0), (0.0, 0.0), T_, L.FOUND_Z, Z,
                   holes=[(L.EX - L.KIT_WIN[1], L.EX - L.KIT_WIN[0],
                           1.05, 2.30)],
                   cname=C_SHELL, side=+1)
    M.set_mat(s, MATS['brick'])
    out.append(s)

    # -- east (street) wall of the main room, north and south of the bay ----
    e1 = M.wall_run("Wall_E_S", (L.EX, -T_), (L.EX, L.BAY_S - L.TP), T_,
                    L.FOUND_Z, Z,
                    holes=[(T_ + L.E_WIN_S[0], T_ + L.E_WIN_S[1],
                            L.STORE_SILL, L.STORE_HEAD)],
                    cname=C_SHELL, side=-1)
    M.set_mat(e1, MATS['brick'])
    out.append(e1)

    # This one runs down ONTO the entrance pier rather than stopping clear of
    # the diagonal, because stopping clear of it left a 0.37 m slot of
    # daylight the full height of the corner.  It therefore shares plan area
    # with the pier and with the diagonal wall, so it is given its own top and
    # its own underside: overlapping solids are fine, coincident faces are not.
    e2 = M.wall_run("Wall_E_N", (L.EX, L.E_N_START), (L.EX, L.NY + L.TP), T_,
                    L.FOUND_Z2, Z + 0.05,
                    holes=[(L.E_WIN_N[0] - L.E_N_START, L.E_WIN_N[1] - L.E_N_START,
                            L.STORE_SILL, L.STORE_HEAD)],
                    cname=C_SHELL, side=-1)
    M.set_mat(e2, MATS['brick'])
    out.append(e2)

    # -- north wall of the main room: the painting wall, with the doorway
    #    through to the lavatories at its west end, behind the counter -------
    n = M.wall_run("Wall_N_main", (0.0, L.NY), (L.EX, L.NY), L.TP, L.FOUND_Z2, Z + 0.06,
                   holes=[(L.LOBBY_DR[0], L.LOBBY_DR[1], L.FOUND_Z, L.LOBBY_H)],
                   cname=C_SHELL, side=+1)
    M.set_mat(n, MATS['plaster_o'])
    out.append(n)

    # -- the window bay ------------------------------------------------------
    bs = M.wall_run("Wall_bay_S", (L.BAY_E + T_, L.BAY_S), (L.EX, L.BAY_S),
                    L.TP, L.FOUND_Z2, Z + 0.06, cname=C_SHELL, side=+1)
    M.set_mat(bs, MATS['plaster_c'])
    out.append(bs)

    be = M.wall_run("Wall_bay_E", (L.BAY_E, L.BAY_S), (L.BAY_E, L.BAY_DIAG_E),
                    T_, L.FOUND_Z, Z,
                    holes=[(a - L.BAY_S, b - L.BAY_S,
                            L.STEP + L.STORE_SILL, L.STORE_HEAD)
                           for (a, b) in L.BAY_WIN] +
                          [(L.TRAN_U[0], L.TRAN_U[1], L.TRAN_BOT, L.TRAN_TOP)],
                    cname=C_SHELL, side=-1)
    M.set_mat(be, MATS['brick'])
    out.append(be)

    # the diagonal, carrying the entrance doors and their transom
    (dx, dy), dl = L.diag_dir()
    bd = M.wall_run("Wall_bay_diag", L.DIAG_A, L.DIAG_B, T_, L.FOUND_Z, Z,
                    holes=[(L.ENTRY_U[0], L.ENTRY_U[1], L.FOUND_Z, L.ENTRY_H),
                           (L.ENTRY_U[0], L.ENTRY_U[1], L.TRAN_BOT, L.TRAN_TOP),
                           (L.DIAG_WIN[0], L.DIAG_WIN[1],
                            L.STEP + L.STORE_SILL, L.STORE_HEAD),
                           (L.DIAG_WIN[0], L.DIAG_WIN[1],
                            L.TRAN_BOT, L.TRAN_TOP)],
                    cname=C_SHELL, side=+1)
    M.set_mat(bd, MATS['brick'])
    out.append(bd)

    # The brick pier at the bay's north-west corner - what the corner of the
    # building actually lands on, and the thing the neon cup hangs off.  Its
    # north-east face is cut ON the entrance diagonal rather than squared off,
    # so the diagonal wall dies into it instead of ploughing through it.
    pier = M.prism("Pier_NW",
                   [(L.EX + 0.02, L.PIER[0]), (L.EX + L.TB, L.PIER[0]),
                    (L.EX + L.TB, L.PIER[1] - L.TB), (L.EX + 0.02, L.PIER[1] - 0.02)],
                   L.FOUND_Z, L.CZ + 0.06, C_SHELL)
    M.set_mat(pier, MATS['brick_pier'])
    M.bevel(pier, 0.012, 2, 50)
    out.append(pier)

    # -- kitchen ------------------------------------------------------------
    # The kitchen block stands IN the main room, so its three outward faces
    # are main-room walls and get the room's own ochre plaster.  Left in bare
    # cream they read as an unpainted stud box parked in the middle of a
    # finished shop.
    #
    # Three slabs do not make an enclosure by being pushed together, and there
    # is no length you can give a square-ended wall that closes an obtuse
    # corner.  The chamfer's end cap is cut square to the CHAMFER, so it runs
    # diagonally across the corner: stop the east wall on the outer mitre and
    # a wedge is left open between the two caps - the dark slot down the
    # block; run the chamfer past its corners instead (which the last pass
    # did, by 1.5 wall thicknesses) and it stands up to 65 mm proud of the
    # wall it should be flush with - the pair of seams.
    #
    # A corner is a mitre.  The two walls that have no openings in them are
    # therefore built as mitred quads rather than as runs, on the inner
    # layout line and the outer mitre points that L.kitchen_outer() already
    # computes for the dado - so wall and trim cannot drift apart.  Each quad
    # runs 5 mm past the joint into its neighbour's body, so the mating faces
    # are buried rather than coincident.
    # The three lap into one another, so no two of them may share a top or a
    # bottom: three slabs stopped on the same z = CZ + 0.06 gave 168 cm2 of
    # same-facing coplanar face in the overlap, which is a z-fight whether or
    # not the ceiling happens to hide it.
    KO = L.kitchen_outer()
    A, B = L.KIT_CH[0], L.KIT_CH[1]         # inner ends of the chamfer
    So, No = KO[1], KO[2]                   # the two outer mitre points
    LAP = 0.005
    ke = M.prism("Wall_kit_E",
                 M.ccw([(L.KIT_E, -0.06), (L.KIT_E + L.TP, -0.06),
                        (So[0], So[1] + LAP), (A[0], A[1] + LAP)]),
                 L.FOUND_Z2, Z + 0.06, C_SHELL)
    M.set_mat(ke, MATS['plaster_o'])
    out.append(ke)
    kc = M.prism("Wall_kit_CH",
                 M.ccw([(A[0], A[1]), (So[0], So[1]),
                        (No[0] - LAP, No[1]), (B[0] - LAP, B[1])]),
                 L.FOUND_Z2 - 0.012, Z + 0.048, C_SHELL)
    M.set_mat(kc, MATS['plaster_o'])
    out.append(kc)
    _kn0 = No[0]
    kn = M.wall_run("Wall_kit_N", (_kn0, L.KIT_N), (0.0, L.KIT_N),
                    L.TP, L.FOUND_Z2 - 0.024, Z + 0.072,
                    holes=[(_kn0 - L.KIT_DR[1], _kn0 - L.KIT_DR[0],
                            L.FOUND_Z, L.DOOR_H)],
                    cname=C_SHELL, side=-1)
    M.set_mat(kn, MATS['plaster_o'])
    out.append(kn)

    # -- lobby + WCs ---------------------------------------------------------
    ln = M.wall_run("Wall_N_ext", (L.WC_E, L.WC_N), (0.0, L.WC_N),
                    L.TW, L.FOUND_Z, Z,
                    holes=[(L.WC_E - w1, L.WC_E - w0, 1.35, 2.35)
                           for (w0, w1) in L.WC_WIN],
                    cname=C_SHELL, side=-1)
    M.set_mat(ln, MATS['brick'])
    out.append(ln)

    le = M.wall_run("Wall_WC_E", (L.WC_E, L.WC_N), (L.WC_E, L.WC_S), L.TW,
                    L.FOUND_Z, Z, cname=C_SHELL, side=+1)
    M.set_mat(le, MATS['brick'])
    out.append(le)

    # The hallway's north wall, carrying both lavatory doors.  This wall is
    # in the HALLWAY, not in a lavatory: you can see it straight through the
    # lobby doorway from the shop floor, so it is finished like the shop -
    # ochre plaster over the same green dado - and not like a WC.
    hn = M.wall_run("Wall_hall_N", (0.0, L.HALL_N), (L.WC_E, L.HALL_N), L.TP,
                    L.FOUND_Z, Z,
                    holes=[(a, b, L.FOUND_Z, L.DOOR_H) for (a, b) in L.WC_DOORS],
                    cname=C_SHELL, side=+1)
    M.set_mat(hn, MATS['plaster_o'])
    out.append(hn)

    # and the wall between the two of them
    wd = M.wall_run("Wall_WC_div", (L.GENTS[1], L.WC_N), (L.GENTS[1], L.WC_Y[0]),
                    L.TP, L.FOUND_Z2, Z + 0.06, cname=C_SHELL, side=+1)
    M.set_mat(wd, MATS['plaster_c'])
    out.append(wd)
    return out


# ------------------------------------------------------------------ ceilings

def ceilings():
    """One slab over the whole shop floor - main room, bay and kitchen read as
    a single space overhead, and building it as one polygon means the bay's
    edge has no coincident face pair hiding above the beam."""
    out = []
    o = 0.10
    poly = [(-L.TW - o, -L.TW - o), (L.EX, -L.TW - o), (L.EX, L.BAY_S),
            (L.BAY_E + L.TW + o, L.BAY_S), (L.BAY_E + L.TW + o, L.BAY_DIAG_E),
            (L.EX, L.BAY_N), (L.EX + L.TB, L.BAY_N),
            (L.EX + L.TB, L.NY + L.TP + o), (-L.TW - o, L.NY + L.TP + o)]
    c = M.prism("Ceil_main", M.ccw(poly), L.CZ, L.CZ + 0.22, C_SHELL)
    M.set_mat(c, MATS['tin'])
    out.append(c)
    lb = M.prism("Ceil_lobby",
                 [(-L.TW + 0.09, L.NY + 0.07), (L.WC_E + L.TW - 0.09, L.NY + 0.07),
                  (L.WC_E + L.TW - 0.09, L.WC_N + L.TW - 0.09),
                  (-L.TW + 0.09, L.WC_N + L.TW - 0.09)],
                 2.74, 2.96, C_SHELL)
    M.set_mat(lb, MATS['ceiling'])
    out.append(lb)
    return out


# ------------------------------------------------------------------ structure

def column(name, x, y, z0, z1, r=None, cname=C_STRUCT):
    """A cast-iron column: moulded base, entasised shaft with a slight swell,
    an astragal and a flared acanthus-block capital."""
    r = r or L.COL_R
    prof = [(0.0, z0)]
    # base
    prof += [(r * 1.85, z0), (r * 1.85, z0 + 0.035), (r * 1.62, z0 + 0.055),
             (r * 1.62, z0 + 0.10), (r * 1.34, z0 + 0.135),
             (r * 1.24, z0 + 0.20), (r * 1.10, z0 + 0.245)]
    # shaft with entasis
    h0, h1 = z0 + 0.245, z1 - 0.30
    n = 10
    for i in range(n + 1):
        t = i / n
        z = h0 + (h1 - h0) * t
        swell = 1.0 + 0.045 * math.sin(math.pi * min(1.0, t * 1.12)) - 0.06 * t
        prof.append((r * swell, z))
    # astragal + capital
    prof += [(r * 0.97, z1 - 0.285), (r * 1.12, z1 - 0.255), (r * 1.12, z1 - 0.225),
             (r * 0.96, z1 - 0.20), (r * 1.30, z1 - 0.115), (r * 1.55, z1 - 0.045),
             (r * 1.62, z1 - 0.012), (r * 1.62, z1), (0.0, z1)]
    ob = M.revolve(name, prof, segments=40, cname=cname)
    M.smooth_shade(ob, 34)
    M.set_mat(ob, MATS['iron'])
    M.translate(ob, (x, y, 0.0))
    return ob


def structure():
    out = []
    # the beam over the bay opening, and the cross beam that closes the
    # north alcove off - both boxed in and painted, as the photos show
    b1 = M.prism("Beam_bay",
                 [(L.COL_X - 0.14, L.BAY_S - 0.08), (L.COL_X + 0.14, L.BAY_S - 0.08),
                  (L.COL_X + 0.14, L.BAY_N), (L.COL_X - 0.14, L.BAY_N)],
                 L.BEAM_Z[0], L.CZ + 0.10, C_STRUCT)
    M.set_mat(b1, MATS['tin'])
    M.bevel(b1, 0.012, 2, 50)
    out.append(b1)

    # The cross beam.  It has to be a dark timber standing clear of the
    # ceiling, not a box in the ceiling's own colour: painted 'tin' and
    # buried in the slab it was invisible in every frame, which is the same
    # thing as not having built it.  It runs from the west wall to the far
    # face of the entrance pier and carries the SERVICE sign and the row of
    # schoolhouse pendants.
    hw = L.BEAM_W * 0.5
    bx = L.EX + L.TB - 0.06     # stops short of the pier's own outer face
    b2 = M.prism("Beam_cross",
                 [(-0.02, L.BEAM_Y - hw), (bx, L.BEAM_Y - hw),
                  (bx, L.BEAM_Y + hw), (-0.02, L.BEAM_Y + hw)],
                 L.BEAM_X_Z, L.CZ + 0.055, C_STRUCT)
    M.set_mat(b2, MATS['beam'])
    M.bevel(b2, 0.014, 2, 50)
    out.append(b2)
    # a moulded fillet along both bottom arrises, the way a boxed-in beam is
    # actually finished off against its own soffit
    for s in (-1, 1):
        f = M.prism("Beam_cross_f%d" % (s > 0),
                    [(-0.02, L.BEAM_Y + s * hw), (bx, L.BEAM_Y + s * hw),
                     (bx, L.BEAM_Y + s * (hw + 0.035)),
                     (-0.02, L.BEAM_Y + s * (hw + 0.035))],
                    L.BEAM_X_Z + 0.028, L.BEAM_X_Z + 0.088, C_STRUCT)
        M.set_mat(f, MATS['beam'])
        M.bevel(f, 0.008, 2, 50)
        out.append(f)

    for i, (x, y) in enumerate(L.COLS):
        # set into the floor, not standing on it: a base plate level with the
        # slab's top face would share that plane with everything else on it
        out.append(column("Column_%d" % i, x, y, L.ground(x, y) - 0.02,
                          L.BEAM_Z[0] + 0.02))
    return out


# ------------------------------------------------------------------ trim

def _run(name, pts, prof, mat, closed=False, cname=C_TRIM):
    """A moulding swept along a plan polyline at a given height, mitred at
    every corner by the sweep itself."""
    ob = M.tube_along(name, pts, prof, cname=cname, close_path=closed)
    M.set_mat(ob, mat)
    return ob


# The wall lines that carry the panelled dado in the main room.  Each entry is
# (name, [plan points], side) where side is +1 if the room is to the left of
# the direction of travel - which is what tells the sweep which way is "out".
# Two chains, not six runs.  The first starts at the bay's south wall, goes
# down the east wall, along the south wall, round the kitchen block, up the
# west wall and stops at the doorway; the second picks up on the far side of
# the doorway and runs to the east corner.  The only end caps in the whole
# room are the four inside a door reveal.
CASE = 0.095        # how far a door casing spreads beyond its opening

# The kitchen door is in the kitchen block's north face, so the dado that
# wraps that block has to break for it exactly as it breaks for the lobby
# door.  Swept straight through, the rail ran across the door at waist
# height and the bottom half of the leaf disappeared into it.
#
# L.KIT_DR is already a pair of WORLD x values - it is what build_openings
# converts INTO the wall's own u.  Converting it a second time here shifted
# the break 0.36 m west of the door it was meant to clear, so the rail still
# ran across the leaf's east half and a strip of wall west of the door was
# left bare.  The break is the doorway plus a casing, and nothing else.
_KO = L.kitchen_outer()
_KD0 = L.KIT_DR[0] - CASE
_KD1 = L.KIT_DR[1] + CASE
_KY = L.KIT_N + L.TP

DADO_RUNS = [
    ("A", [(L.EX, L.BAY_S - 0.04), (L.EX, 0.0)] + _KO[:3] + [(_KD1, _KY)]),
    ("A2", [(_KD0, _KY), (0.0, _KY), (0.0, L.NY),
            (L.LOBBY_DR[0] - CASE, L.NY)]),
    ("B", [(L.LOBBY_DR[1] + CASE, L.NY), (L.EX + 0.04, L.NY)]),
    # and on through the doorway: the hallway is finished like the shop, so
    # its dado is the shop's dado, mitred round the same way, breaking at
    # the lobby door and at both lavatory doors
    ("H", [(L.WC_DOORS[1][1] + CASE, L.HALL_N), (L.WC_E, L.HALL_N),
           (L.WC_E, L.WC_S), (L.LOBBY_DR[1] + CASE, L.WC_S)]),
    ("H2", [(L.LOBBY_DR[0] - CASE, L.WC_S), (0.0, L.WC_S), (0.0, L.HALL_N),
            (L.WC_DOORS[0][0] - CASE, L.HALL_N)]),
    ("H3", [(L.WC_DOORS[0][1] + CASE, L.HALL_N),
            (L.WC_DOORS[1][0] - CASE, L.HALL_N)]),
]

# Both profiles start at -TRIM_BED, i.e. the back of the moulding is bedded
# into the plaster rather than laid flush on it.  Real trim is fixed to
# grounds and the plaster is floated up to it; modelling it flush is what puts
# the moulding's back face on exactly the same plane as the wall face, and as
# the back of everything else that is also standing on that wall.
B = -L.TRIM_BED

SKIRT_PROF = [(B, -0.012), (0.030, -0.012), (0.030, L.BASE_H - 0.030),
              (0.022, L.BASE_H - 0.022), (0.022, L.BASE_H - 0.010),
              (0.008, L.BASE_H), (B, L.BASE_H)]

# dado: a flat panel field standing 18 mm off the plaster, capped by a moulded
# rail.  Built as one swept profile so the rail is genuinely part of the run.
DADO_PROF = [(B, L.BASE_H), (0.018, L.BASE_H), (0.018, L.DADO - 0.075),
             (0.030, L.DADO - 0.062), (0.034, L.DADO - 0.030),
             (0.030, L.DADO - 0.008), (0.014, L.DADO), (B, L.DADO)]


def trim():
    """Skirting and the panelled dado.

    Each is swept along one continuous polyline per wall loop rather than as a
    run per wall, so the corners are mitred by the sweep itself.  Cut into
    separate runs they met end-cap to end-cap, and every one of those joints
    was a coplanar pair."""
    out = []
    for nm, pts in DADO_RUNS:
        p3 = [(p[0], p[1], 0.0) for p in pts]
        p3 = M.densify(p3, 0.05)
        sk = M.tube_along("Skirt_" + nm, p3, SKIRT_PROF, cname=C_TRIM,
                          miter=True)
        M.set_mat(sk, MATS['green'])
        out.append(sk)
        dd = M.tube_along("Dado_" + nm, p3, DADO_PROF, cname=C_TRIM, miter=True)
        M.set_mat(dd, MATS['green'])
        out.append(dd)

    # the bay stands on its platform, so its skirting starts a step higher
    bay = [(L.BAY_E + 0.04, L.BAY_DIAG_E), (L.BAY_E, L.BAY_S),
           (L.EX - 0.04, L.BAY_S)]
    p3 = M.densify([(p[0], p[1], L.STEP) for p in bay], 0.05)
    sk = M.tube_along("Skirt_bay", p3, SKIRT_PROF, cname=C_TRIM, miter=True)
    M.set_mat(sk, MATS['joinery'])
    out.append(sk)
    return out


# ------------------------------------------------------------------ build

def build():
    M.purge()
    for c in (C_SHELL, C_STRUCT, C_TRIM):
        M.coll(c)
    make_materials()
    floors()
    walls()
    ceilings()
    structure()
    trim()
    print("shell:", len(bpy.data.objects), "objects")
