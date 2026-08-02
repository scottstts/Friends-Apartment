"""Floor, walls, ceiling and mouldings for the whole flat.

Three blocks: the main living room, the west block holding the two bedrooms,
and the bathroom pushed north into the light well.  None of them line up with
each other, which is deliberate - see L.py.

Order matters: the walls are cut with their openings as they are built, the
parquet is laid across every room that has it in ONE pass so the pattern runs
continuously through the doorways, and the trim is placed against wall lines
rather than against other trim.
"""
import bpy, math
from mathutils import Vector
import mlib, mats, L, s_walls as SW, s_floor, s_tile


def outline():
    """The main room, walked CCW.  Every wall in it derives from this list, so
    the L-shaped notch the kitchen alcove cuts out of the north-east corner is
    stated exactly once."""
    return [(L.WX, L.SY), (L.EX, L.SY), (L.EX, L.NY2),
            (L.JX, L.NY2), (L.JX, L.NY), (L.WX, L.NY)]


def _u(p0, p1, pt):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    return ((pt[0] - p0[0]) * dx + (pt[1] - p0[1]) * dy) / ln


PAD = 0.002


def hole(p0, p1, a, b, z0, z1, pad=PAD):
    """Opening between two world points on a wall line, as wall-local u.

    Cut 2 mm oversize all round.  The lining that goes into the reveal is built
    at the nominal size, so those 2 mm bury its outer faces inside the wall
    instead of leaving them exactly coplanar with the reveal - which is a
    guaranteed z-fight along all three edges of every door and window."""
    ua, ub = _u(p0, p1, a), _u(p0, p1, b)
    return (min(ua, ub) - pad, z0 - pad, max(ua, ub) + pad, z1 + pad)


def offset_poly(poly, d):
    """Offset a closed rectilinear polygon outward by d.  Each vertex moves
    along the sum of its two adjacent edges' outward normals, which lands on
    the intersection of the two offset edges for convex AND reflex corners
    alike - the only two kinds this plan has."""
    n = len(poly)
    out = []
    for i in range(n):
        p = poly[i]
        a, b = poly[i - 1], poly[(i + 1) % n]
        t0 = (p[0] - a[0], p[1] - a[1])
        t1 = (b[0] - p[0], b[1] - p[1])
        l0 = math.hypot(*t0) or 1.0
        l1 = math.hypot(*t1) or 1.0
        n0 = (t0[1] / l0, -t0[0] / l0)
        n1 = (t1[1] / l1, -t1[0] / l1)
        out.append((p[0] + d * (n0[0] + n1[0]), p[1] + d * (n0[1] + n1[1])))
    return out


def mats_shell():
    mats.plaster("M_Wall", L.WALL, rough=0.88, bump=0.36, patch=0.055)
    mats.plaster("M_WallBed", mats.shade(L.WALL, 1.04), rough=0.86, bump=0.34,
                 patch=0.05)
    mats.plaster("M_WallBath", 'C8CEC2', rough=0.84, bump=0.30, patch=0.05)
    mats.ceiling_paint("M_Ceiling", L.CEIL)
    mats.paint("M_Trim", L.TRIM, rough=0.30, coat=0.12, brush=0.6)
    mats.paint("M_TrimW", mats.shade(L.TRIM, 1.03), rough=0.26, coat=0.18, brush=0.5)
    s_floor.parquet_mat("M_Parquet")
    # Bathroom: a small-format sage subway tile on the walls, and a warm buff
    # floor tile.  Both are cut to their own surface, so the joints line up
    # with the plane they are on rather than with the world.
    mats.tile("M_BathWallTile", 'D9DCD2', 'A8AAA0', size=0.108, joint=0.007,
              rough=0.10, relief=0.6, plane='XZ')
    mats.tile("M_BathFloorTile", 'C6B79E', '8E8271', size=0.152, joint=0.009,
              rough=0.24, relief=0.5, plane='XY')


def _walls_main():
    O = outline()
    S, E, K, J, N = ((O[0], O[1]), (O[1], O[2]), (O[2], O[3]),
                     (O[3], O[4]), (O[4], O[5]))
    w = []
    w.append(SW.wall("W_South", S[0], S[1], L.TW, 0.0, L.CZ))
    w.append(SW.wall("W_East", E[0], E[1], L.TW, 0.0, L.CZ, holes=[
        hole(E[0], E[1], (L.EX, L.FD_Y[0]), (L.EX, L.FD_Y[1]), 0.0, L.FD_H)]))
    # Every wall grows OUTWARD from its inner face, so at a convex corner the
    # two solids meet and leave a void outside (harmless), but at a REFLEX
    # corner they grow into each other and overlap by thickness squared.  This
    # room has exactly one reflex corner - (JX, NY2), where the kitchen wall
    # meets the jog - and that overlap put the jog's end cap in the same plane
    # as the kitchen wall's inner face: a 300 mm strip of coplanar geometry,
    # full height, that z-fought in every shot looking that way.
    #
    # The fix is to give the corner block to exactly one wall.  The jog keeps
    # it (it runs the full depth from NY2 to NY), so the kitchen wall starts a
    # thickness east of the corner instead of at it.
    w.append(SW.wall("W_KitBack", K[0], (K[1][0] + L.TW, K[1][1]), L.TW, 0.0, L.CZ))
    w.append(SW.wall("W_Jog", J[0], J[1], L.TW, 0.0, L.CZ))
    w.append(SW.wall("W_North", N[0], N[1], L.TW, 0.0, L.CZ, holes=[
        hole(N[0], N[1], (L.WIN_A[0], L.NY), (L.WIN_A[1], L.NY), L.WIN_SILL, L.WIN_HEAD),
        hole(N[0], N[1], (L.WIN_B[0], L.NY), (L.WIN_B[1], L.NY), L.WIN_SILL, L.WIN_HEAD),
        hole(N[0], N[1], (L.BD_X[0], L.NY), (L.BD_X[1], L.NY), 0.0, L.BD_H)]))
    return w, O


def _walls_west():
    """The bedroom block.  The wall between the bedrooms and the living room is
    ONE solid running the full height of the block - from Joey's south wall up
    past Chandler's north wall to the living room's own - rather than three
    stacked pieces, because the two rooms it separates do not share a single
    corner with each other."""
    w = []
    a, b = (L.BED_E, L.JO_Y[0] - 0.0), (L.BED_E, L.NY)
    w.append(SW.wall("W_BedEast", a, b, L.BW_TH, 0.0, L.CZ, holes=[
        hole(a, b, (L.BED_E, L.JOEY_DOOR[0]), (L.BED_E, L.JOEY_DOOR[1]), 0.0, L.DOOR_TOP),
        hole(a, b, (L.BED_E, L.CHAN_DOOR[0]), (L.BED_E, L.CHAN_DOOR[1]), 0.0, L.DOOR_TOP)]))
    a, b = (L.BED_W, L.CH_Y[1] + L.TW), (L.BED_W, L.JO_Y[0] - L.TW)
    w.append(SW.wall("W_BedWest", a, b, L.TW, 0.0, L.CZ, holes=[
        hole(a, b, (L.BED_W, L.JO_WIN[0]), (L.BED_W, L.JO_WIN[1]),
             L.WIN_SILL, L.WIN_HEAD)]))
    a, b = (L.BED_E, L.CH_Y[1]), (L.BED_W, L.CH_Y[1])
    w.append(SW.wall("W_ChanN", a, b, L.TW, 0.0, L.CZ, holes=[
        hole(a, b, (L.CH_WIN[0][0], L.CH_Y[1]), (L.CH_WIN[0][1], L.CH_Y[1]),
             L.WIN_SILL, L.WIN_HEAD),
        hole(a, b, (L.CH_WIN[1][0], L.CH_Y[1]), (L.CH_WIN[1][1], L.CH_Y[1]),
             L.WIN_SILL, L.WIN_HEAD)]))
    w.append(SW.wall("W_JoeyS", (L.BED_W, L.JO_Y[0]), (L.BED_E, L.JO_Y[0]),
                     L.TW, 0.0, L.CZ))
    w.append(SW.wall("W_Party", (L.BED_W, L.CH_Y[0]), (L.BED_E, L.CH_Y[0]),
                     L.PARTY[1] - L.PARTY[0], 0.0, L.CZ))
    return w


def _walls_bath():
    """Three sides of the bathroom.  Its south side is the living room's north
    wall for most of its width - that wall is already built and already carries
    the door - so only the strip east of the living room's north wall is added
    here.  Building a second full south wall would put two solids in the same
    place and leave the door opening blocked from one side."""
    w = []
    x0, x1 = L.BA_X
    y0, y1 = L.BA_Y
    # Full living-room height, not bathroom height.  The bathroom's own ceiling
    # is at BA_CZ and nothing above it is ever seen from inside - but the strip
    # of W_BathS west of the bathroom is also the block that fills the outside
    # corner where the jog meets the north wall, and stopped at 2.92 it left a
    # 230 mm slot open to the sky right at the living room's cornice.
    w.append(SW.wall("W_BathW", (x0, y1 + L.TW), (x0, y0), L.TW, 0.0, L.CZ))
    w.append(SW.wall("W_BathN", (x1, y1), (x0, y1), L.TW, 0.0, L.CZ))
    # taken down to NY, not to y0, so it meets the jog wall's head instead of
    # leaving a 300 mm void between the two at the alcove's outside corner
    w.append(SW.wall("W_BathE", (x1, L.NY), (x1, y1 + L.TW), L.TW, 0.0, L.CZ))
    if x1 > L.JX:
        # the strip of the bathroom's south wall that reaches PAST the living
        # room's north wall, which only runs as far as the jog
        w.append(SW.wall("W_BathS", (L.JX, y0), (x1, y0), L.TW, 0.0, L.CZ))
    return w


def _corner_posts():
    """The blocks that fill the outside corners.

    Every wall in this build grows OUTWARD from its own line, so at a convex
    corner the two solids meet along a single line and the square of masonry
    beyond it belongs to neither of them.  From inside the room the two faces
    close the corner exactly - and let daylight straight through the knife
    edge between them, which is what put a vertical white streak down the top
    of four corners of this flat.

    Each entry is the void: the outward strip of one wall crossed with the
    outward strip of the other.  They butt against both walls and share volume
    with neither, so nothing here can z-fight.
    """
    T, B = L.TW, L.BW_TH
    voids = [
        # living room SW - the bedroom block's east wall meets the fourth wall.
        # This one also closes Joey's own south-east corner.
        (L.WX - B, L.SY - T, L.WX, L.SY),
        # living room NW - the same wall meets the north wall
        (L.WX - B, L.NY, L.WX, L.NY + T),
        # living room SE - the fourth wall meets the east wall
        (L.EX, L.SY - T, L.EX + T, L.SY),
        # the alcove's outside corner - east wall meets the kitchen back wall
        (L.EX, L.NY2, L.EX + T, L.NY2 + T),
    ]
    out = []
    for i, (a, b, c, d) in enumerate(voids):
        p = mlib.box("W_Post%d" % i, a, b, 0.0, c, d, L.CZ, "Shell")
        out.append(p)
    return out


def _bath_lining():
    """The bathroom's tiling, laid wall by wall as real tiles.

    ONE height, all four walls, with a bullnose cap running unbroken round the
    room.  The earlier version tiled the tub alcove full height and the rest to
    a wainscot, which is what a real bathroom often does - but the tub only
    covers 1.55 m of a 2.75 m wall, so the tall panel read as a rectangle of
    tiles stuck on at random rather than as a surround.  A single line all the
    way round is both cleaner and more obviously deliberate.

    The grid starts at whichever corner each run comes FROM, so every corner
    gets a whole tile and the cut lands mid-wall where nothing meets it; the
    height is a whole number of courses, so the top is a joint and not a row of
    slivers.
    """
    tm = s_tile.tile_mats()
    x0, x1 = L.BA_X
    y0, y1 = L.BA_Y
    n = s_tile.courses(2.05)
    out = []

    S = ((x0, y0), (x1, y0))           # inner faces, walked CCW inside the room
    E = ((x1, y0), (x1, y1))
    N = ((x1, y1), (x0, y1))
    W = ((x0, y1), (x0, y0))

    def run(nm, seg, a, b, start):
        out.extend(s_tile.field(nm, seg[0], seg[1], a, b, 0.0, n,
                                cname="Shell", start_u=start))

    # south wall, broken either side of the doorway and stopped clear of the
    # architrave - the casing is applied to plaster and stands proud of it, so
    # tile butts to it rather than running behind it
    CASE = 0.123
    run("BT_S0", S, 0.0, L.BD_X[0] - CASE - x0, 0.0)
    run("BT_S1", S, L.BD_X[1] + CASE - x0, x1 - x0, x1 - x0)
    run("BT_E", E, 0.0, y1 - y0, 0.0)
    run("BT_N", N, 0.0, x1 - x0, 0.0)
    run("BT_W", W, 0.0, y1 - y0, 0.0)
    for o in out:
        mlib.set_mat(o, tm)
    return mlib.join(out, "Bath_Tiling", "Shell")


def _two_sided(obj, other, pred):
    """Give a wall a second material on the faces that belong to the room on
    its far side.  A wall between two differently painted rooms is one solid,
    so without this the bathroom looks out at a stripe of living-room greige
    above its own door."""
    mlib.assign_mats(obj, [obj.data.materials[0], other])
    mlib.face_mat(obj, 1, pred)
    return obj


def build():
    mlib.purge()
    mlib.coll("Shell")
    mats_shell()
    W, T = mats.get("M_Wall"), mats.get("M_Trim")

    walls, O = _walls_main()
    for w in walls:
        mlib.set_mat(w, W)
    for w in _walls_west():
        mlib.set_mat(w, mats.get("M_WallBed"))
    for w in _walls_bath():
        mlib.set_mat(w, mats.get("M_WallBath"))
    for w in _corner_posts():
        mlib.set_mat(w, W)
    _bath_lining()

    # ------------------------------------------- walls that face two rooms
    # A wall is one solid, but it has a room on each side and those rooms are
    # not painted the same.  The bathroom's south wall IS the living room's
    # north wall, and above the door it was showing the living room's greige
    # straight into the bathroom, next to the bathroom's own sage on the strip
    # of wall that belongs to the bathroom alone.
    def _n(o):
        return bpy.data.objects.get(o)
    nb = _n("W_North")
    if nb:
        _two_sided(nb, mats.get("M_WallBath"),
                   lambda c, n: n.y > 0.9 and c.y > L.NY + L.TW * 0.5)
    be = _n("W_BedEast")
    if be:
        _two_sided(be, W, lambda c, n: n.x > 0.9 and c.x > L.WX - 0.01)

    # ------------------------------------------------------------- ceilings
    # Every ceiling slab is offset out to the middle of its walls, so its edge
    # faces are buried in masonry.  Cut exactly to the room, those edges sit in
    # the same plane as the wall faces, pointing the other way - two coplanar
    # surfaces at the same depth, which is the same fault as the jog corner.
    for nm, poly, z in (
            ("Ceiling", O, L.CZ),
            ("Ceiling_Chan", [(L.CH_X[0], L.CH_Y[0]), (L.CH_X[1], L.CH_Y[0]),
                              (L.CH_X[1], L.CH_Y[1]), (L.CH_X[0], L.CH_Y[1])], L.CZ),
            ("Ceiling_Joey", [(L.JO_X[0], L.JO_Y[0]), (L.JO_X[1], L.JO_Y[0]),
                              (L.JO_X[1], L.JO_Y[1]), (L.JO_X[0], L.JO_Y[1])], L.CZ),
            ("Ceiling_Bath", [(L.BA_X[0], L.BA_Y[0]), (L.BA_X[1], L.BA_Y[0]),
                              (L.BA_X[1], L.BA_Y[1]), (L.BA_X[0], L.BA_Y[1])], L.BA_CZ)):
        # 65 mm, not half a wall: the party wall between the bedrooms is only
        # 160 thick, so anything past 80 makes the two bedroom slabs overlap
        # each other inside it - one coplanar fault traded for another.
        mlib.set_mat(SW.ceiling(nm, offset_poly(poly, 0.065), z, 0.16),
                     mats.get("M_Ceiling"))

    cw = [(p[0], p[1]) for p in O][::-1]
    mlib.set_mat(SW.cornice("Cornice", cw + [cw[0]], L.CZ), mats.get("M_TrimW"))
    for nm, xr, yr in (("Cornice_Chan", L.CH_X, L.CH_Y), ("Cornice_Joey", L.JO_X, L.JO_Y)):
        p = [(xr[0], yr[0]), (xr[0], yr[1]), (xr[1], yr[1]), (xr[1], yr[0])]
        mlib.set_mat(SW.cornice(nm, p + [p[0]], L.CZ), mats.get("M_TrimW"))

    # ------------------------------------------------------------- floors
    # One parquet object across every boarded room, laid on one grid, so the
    # pattern runs through the doorways instead of restarting at each threshold.
    # Each region is grown 60 mm past its walls so the boards run UNDER them,
    # as a real floor does - and so the cut ends of the parquet are buried
    # rather than sitting in the same plane as the wall faces.
    g = 0.06
    # Each room's region stops 60 mm inside its own walls, which leaves the
    # THRESHOLDS unfloored - a doorway is a hole in the wall, and the two rooms'
    # regions each stop short of it from opposite sides.  Every opening
    # therefore gets its own strip carrying the boards right through the wall.
    thr = [(L.BED_E - 0.02, L.JOEY_DOOR[0] - 0.02, L.WX + 0.02, L.JOEY_DOOR[1] + 0.02),
           (L.BED_E - 0.02, L.CHAN_DOOR[0] - 0.02, L.WX + 0.02, L.CHAN_DOOR[1] + 0.02),
           # The FRONT DOOR needed one too.  The room's boards are grown only
           # 60 mm past the east wall's inner face, but that wall is 300 thick
           # and the leaf hangs in the middle of it - 126 to 174 mm in - so
           # there was no floor at all under the front door and the light well
           # showed through the gap under it as a strip of sky.  Stopped 40 mm
           # short of the wall's outer face, so the cut end stays buried.
           (L.EX - 0.02, L.FD_Y[0] - 0.03, L.EX + L.TW - 0.04, L.FD_Y[1] + 0.03),
           # taken 40 mm PAST the wall's far face, not exactly to it: run to
           # the face and the threshold's own north side lands in the same
           # plane as the wall's, pointing the same way.  Past it, the strip
           # finishes under the bath tile, which is 3.5 mm proud of it.
           (L.BD_X[0] - 0.02, L.NY - 0.02, L.BD_X[1] + 0.02, L.NY + L.TW + 0.04)]
    fl = s_floor.build([(L.WX - g, L.SY - g, L.JX + g, L.NY + g),
                        (L.JX - g, L.SY - g, L.EX + g, L.NY2 + g),
                        (L.CH_X[0] - g, L.CH_Y[0] - g, L.CH_X[1] + g, L.CH_Y[1] + g),
                        (L.JO_X[0] - g, L.JO_Y[0] - g, L.JO_X[1] + g, L.JO_Y[1] + g)]
                       + thr, "Floor_Parquet", "Shell", phase=(0.03, 0.05))
    mlib.set_mat(fl, mats.get("M_Parquet"))

    # The bath tile sits 3.5 mm proud of the boards - a real threshold step,
    # and it means the two floors overlap in plan at the doorway without ever
    # sharing a plane.
    bf = mlib.box("Floor_Bath", L.BA_X[0] - g, L.NY + L.TW - 0.03, -0.02,
                  L.BA_X[1] + g, L.BA_Y[1] + g, 0.0145)
    mlib.set_mat(bf, mats.get("M_BathFloorTile"))
    mlib.bevel(bf, 0.002, 1, 40)

    # ------------------------------------------------------------- baseboard
    # A baseboard dies into a door CASING, not into the opening - the casing is
    # 115 mm wide and 6 mm of reveal proud of that, so a run taken all the way
    # to the door edge finishes underneath the architrave with both back faces
    # in the same plane.  CASE is how far back each run stops.
    CASE = 0.121
    FDC = 0.138          # the front door's architrave is wider than the rest
    runs = [
        # west wall from Chandler's door, round the north-west corner, to the
        # bathroom door: one run, so that corner is mitred rather than butted
        ([(L.WX, L.CHAN_DOOR[1]), (L.WX, L.NY), (L.BD_X[0], L.NY)], CASE, CASE),
        ([(L.BD_X[1], L.NY), (L.JX, L.NY), (L.JX, L.NY2), (L.EX, L.NY2),
          (L.EX, L.FD_Y[1])], CASE, FDC),
        ([(L.EX, L.FD_Y[0]), (L.EX, L.SY), (L.WX, L.SY),
          (L.WX, L.JOEY_DOOR[0])], FDC, CASE),
        ([(L.WX, L.JOEY_DOOR[1]), (L.WX, L.CHAN_DOOR[0])], CASE, CASE),
        # Chandler: clockwise from his door round to it again
        ([(L.BED_E, L.CHAN_DOOR[0]), (L.BED_E, L.CH_Y[0]), (L.CH_X[0], L.CH_Y[0]),
          (L.CH_X[0], L.CH_Y[1]), (L.BED_E, L.CH_Y[1]),
          (L.BED_E, L.CHAN_DOOR[1])], CASE, CASE),
        ([(L.BED_E, L.JOEY_DOOR[0]), (L.BED_E, L.JO_Y[0]), (L.JO_X[0], L.JO_Y[0]),
          (L.JO_X[0], L.JO_Y[1]), (L.BED_E, L.JO_Y[1]),
          (L.BED_E, L.JOEY_DOOR[1])], CASE, CASE),
    ]
    for i, (r, ta, tb) in enumerate(runs):
        mlib.set_mat(SW.baseboard("Base_%02d" % i, SW.trim_run(r, ta, tb)), T)

    # ------------------------------------------------------------- panelling
    PZ, PH = 1.415, 2.10

    def panels(p0, p1, tag, spec):
        """spec entries are (u_centre, width) or (u_centre, width, z_centre,
        height) - a bay with tall furniture standing in it needs a SHORT panel
        sitting above the furniture, not a full-height one sliced off by it."""
        for j, item in enumerate(spec):
            uc, w = item[0], item[1]
            zc = item[2] if len(item) > 2 else PZ
            h = item[3] if len(item) > 3 else PH
            mlib.set_mat(SW.wall_panel("Panel_%s_%d" % (tag, j), p0, p1, uc,
                                       zc, w, h), T)

    # Panel positions are held clear of every door and window CASING, not just
    # of the opening: an architrave is 115 mm wide and stands 21 mm proud, so a
    # panel that merely misses the door still ploughs straight through its
    # trim.  Each bay below is the clear wall between two casings.
    Om = O
    panels(Om[0], Om[1], "S", [(1.00, 1.60), (2.90, 1.60), (4.80, 1.60),
                               (6.70, 1.60)])
    panels(Om[1], Om[2], "E", [(1.55, 1.55), (5.15, 1.05)])
    # The west wall is walked NORTH to SOUTH, so u counts down from NY.  With
    # Joey's door moved south the bays are 0..1.95 (north of Chandler's),
    # 2.85..6.53 (the wide pier the unit stands on) and 7.43..8.60.
    # The wide pier carries the entertainment unit, so its panel is a single
    # frieze sitting clear ABOVE the unit's 1.60 m top rather than two
    # full-height panels the unit cuts in half.
    _entu = L.NY - (L.ENT_Y[0] + L.ENT_Y[1]) * 0.5
    panels(Om[5], Om[0], "W", [(0.95, 1.25), (_entu, 3.10, 2.075, 0.80),
                               (8.10, 0.72)])
    # the jog's panel is keyed to the jog's own depth, so shortening the jog
    # cannot leave the moulding hanging off the end of the wall again
    _jw = L.NY - L.NY2
    panels(Om[3], Om[4], "J", [(_jw * 0.5, _jw - 0.70)])
    # bedrooms: one panel per clear stretch of wall
    panels((L.CH_X[0], L.CH_Y[0]), (L.CH_X[0], L.CH_Y[1]), "CW", [(1.90, 1.55)])
    panels((L.CH_X[1], L.CH_Y[0]), (L.CH_X[0], L.CH_Y[0]), "CS", [(1.05, 1.45), (2.70, 1.45)])
    panels((L.JO_X[0], L.JO_Y[1]), (L.JO_X[1], L.JO_Y[1]), "JN", [(1.05, 1.45), (2.70, 1.45)])
    panels((L.JO_X[1], L.JO_Y[0]), (L.JO_X[0], L.JO_Y[0]), "JS", [(1.05, 1.45), (2.70, 1.45)])
    return walls


def stats():
    n = len(bpy.data.objects)
    f = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
    return "objects %d  faces %d" % (n, f)
