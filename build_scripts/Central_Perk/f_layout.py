"""Where everything goes.

This module owns no geometry.  It calls f_seating, f_tables, f_counter and
f_props for the pieces, lays the rugs first, and then settles every piece
onto whatever it is standing on.  The anchors all come from L.py, so moving
a chair is a one-line edit there and nothing here changes.

One convention to watch.  L.py's rotations were written with "rot = 0 faces
+Y"; the furniture modules are built with the BACK at +Y, because that is
what lets a piece against the north wall need no rotation at all.  `R()`
converts between them, and every call site uses it rather than carrying two
sets of angles around.
"""
import bpy, math, importlib
import mlib as M
import mats as T
import L
import f_seating as FS
import f_tables as FT
import f_counter as FC
import f_props as FP

importlib.reload(M); importlib.reload(T); importlib.reload(L)
importlib.reload(FS); importlib.reload(FT); importlib.reload(FC); importlib.reload(FP)

C = "Furniture"
CR = "Rugs"


def R(a):
    """L.py angle -> furniture-module angle."""
    return a + 180.0


# every rug laid so far, as (x0, y0, x1, y1, top_z); settle() reads it
RUGS = []


def G(bb):
    """The height a piece stands at, given its plan bounding box: the floor
    under its centre, or the top of any rug it overlaps.

    It has to be the whole footprint and not just the centre.  A chair with
    two legs over the edge of a rug, placed by its centre, ends up with its
    underside on exactly the plane of the rug's underside - and the legs
    through the pile."""
    x0, y0, x1, y1 = bb
    z = L.ground((x0 + x1) * 0.5, (y0 + y1) * 0.5)
    for (rx0, ry0, rx1, ry1, top) in RUGS:
        if x0 < rx1 and x1 > rx0 and y0 < ry1 and y1 > ry0 and top > z:
            z = top
    return z


def settle(group):
    """Lift one piece - which may be several objects - onto the surface it
    stands on, as a unit.

    Settling object by object would be wrong for anything built in parts: a
    couch whose fringe hangs past the rug edge would compute a different
    ground height from its own frame, and the two would part company."""
    objs = [o for o in group if o is not None and o.type == 'MESH']
    if not objs:
        return group
    xs = [v.co.x for o in objs for v in o.data.vertices]
    ys = [v.co.y for o in objs for v in o.data.vertices]
    z = G((min(xs), min(ys), max(xs), max(ys)))
    if z:
        for o in group:
            if o is None:
                continue
            if o.type == 'MESH':
                M.translate(o, (0.0, 0.0, z))
            else:
                o.location.z += z
    return group


def rug(name, cx, cy, w, d, z=None, rot=0.0, oval=False, pal=None):
    """A knotted carpet, with its own weave graph sized to its own extent so
    the medallion lands in the middle of THIS rug rather than of some
    nominal one.

    The mesh stays at the origin and the rug is moved by its OBJECT
    transform.  That matters here and almost nowhere else in the build: the
    carpet graph normalises Object coordinates to +/-1 across the rug, so
    baking the position into the vertices - which is what M.translate does -
    puts the medallion at the world origin and leaves every rug showing a
    corner of the border.  Tiling materials do not care; this one does."""
    if z is None:
        z = L.ground(cx, cy)
    if oval:
        pts = [(w * 0.5 * math.cos(a), d * 0.5 * math.sin(a))
               for a in [i * math.tau / 48 for i in range(48)]]
    else:
        pts = M.rounded_rect(w, d, 0.02, 3)
    ob = M.prism(name, pts, 0.0, L.RUG_T, CR)
    M.bevel(ob, 0.004, 2, 55)
    if rot:
        M.rotate_z(ob, math.radians(rot))
    ob.location = (cx, cy, z)
    p = pal or {}
    # a different slice of the same lattice for every rug in the room.
    # Derived from the letters of the name rather than from hash(), which is
    # salted per process: the same build would lay a different set of
    # carpets every time Blender started.
    ph = (sum((i + 3) * ord(c) for i, c in enumerate(name)) % 997) * 0.0173
    M.set_mat(ob, T.persian('rug_' + name, wd=(w, d), phase=ph, **p))
    RUGS.append((cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2, z + L.RUG_T))
    return ob


# ---------------------------------------------------------------- the rooms

def place(group, x, y, rot=None):
    """Move a piece to its anchor.  Position BEFORE settling, always - the
    ground height depends on which rug the footprint lands on, and a piece
    still sitting at the origin lands on the wrong one (or on none)."""
    for o in group:
        if o is None:
            continue
        if rot is not None:
            if o.type == 'MESH':
                M.rotate_z(o, math.radians(rot))
            else:
                o.rotation_euler.z += math.radians(rot)
        if o.type == 'MESH':
            M.translate(o, (x, y, 0.0))
        else:
            o.location.x += x
            o.location.y += y
    return settle(group)


def main_group():
    out = []
    out.append(place(FS.hero_couch("Couch", L.SOFA_L, L.SOFA_D),
                     L.SOFA_C[0], L.SOFA_C[1]))
    out.append(settle(FT.coffee_table("Table_coffee", L.COFFEE_C[0],
                                      L.COFFEE_C[1], L.COFFEE_WD[0],
                                      L.COFFEE_WD[1], L.COFFEE_H)))
    out.append(place(FS.recliner("Recliner"), L.RECLINER_C[0],
                     L.RECLINER_C[1], R(L.RECLINER_ROT)))
    out.append(settle(FT.ped_table("Table_side", L.SIDE_T_C[0], L.SIDE_T_C[1],
                                   L.SIDE_T_R, 0.735)))
    for nm, a in (("a", L.CHAIR_A), ("b", L.CHAIR_B)):
        out.append(place(FS.bistro_chair("Chair_" + nm), a[0], a[1], R(a[2])))
    return out


def counter_group():
    out = [FC.build()]
    for i, (x, y) in enumerate(L.STOOLS):
        out.append(place(FS.bar_stool("Stool_%d" % i, h=L.STOOL_H), x, y))
    return out


def tables_zone():
    out = []
    for i, (x, y) in enumerate((L.TABLE_1, L.TABLE_2)):
        out.append(settle(FT.ped_table("Table_mid_%d" % i, x, y,
                                       L.TABLE_MID_R, 0.735)))
    for i, (x, y, r) in enumerate(L.TZ_CHAIRS):
        out.append(place(FS.wood_stool("Stool_mid_%d" % i), x, y))
    return out


def north_alcove():
    out = []
    out.append(place(FS.settee("Settee_north", L.SETTEE_L, 0.80,
                               cover="velvet_dk", nbu=5, nbv=2, fringe=True,
                               cushions=2), L.SETTEE_C[0], L.SETTEE_C[1]))
    for nm, a in (("L", L.ARMCH_L), ("R", L.ARMCH_R)):
        out.append(place(FS.club_chair("Chair_red_" + nm, 0.84, 0.88, 0.90,
                                       cover="velvet_red"),
                         a[0], a[1], R(a[2])))
    out.append(settle(FT.low_table("Table_oval", L.OVAL_T[0], L.OVAL_T[1],
                                   L.OVAL_T_WD[0], L.OVAL_T_WD[1], 0.42,
                                   oval=True, wood='mahog')))
    out.append(place(FS.pouf("Pouf_north"), L.POUF[0], L.POUF[1]))
    out.append(settle(FT.ped_table("Table_north_side", L.ROUND_T_N[0],
                                   L.ROUND_T_N[1], 0.28, 0.68)))
    out.append(settle(FP.potted("Plant_north", L.PLANT_N[0], L.PLANT_N[1], 0.0,
                                r=0.24, ph=0.42, sp=1.05)))
    return out


def south_zone():
    out = []
    out.append(place(FS.settee("Sofa_south", L.SOFA_S_L, 0.86, cover="velvet",
                               nbu=6, nbv=2, fringe=True, cushions=2),
                     L.SOFA_S[0], L.SOFA_S[1], R(0.0)))
    out.append(settle(FT.low_table("Table_south", L.TABLE_S[0], L.TABLE_S[1],
                                   L.TABLE_S_WD[0], L.TABLE_S_WD[1], 0.44,
                                   wood='walnut')))
    for i, (x, y, r) in enumerate(L.TS_CHAIRS):
        out.append(place(FS.bistro_chair("Chair_south_%d" % i), x, y, R(r)))
    out.append(settle(FT.ped_table("Table_south_side", L.SIDE_T_S[0],
                                   L.SIDE_T_S[1], 0.30, 0.70)))
    out.append(settle(FP.potted("Plant_south", L.PLANT_S[0], L.PLANT_S[1], 0.0,
                                r=0.21, ph=0.36, sp=0.86)))
    return out


def bay():
    out = []
    out.append(place(FS.settee("Settee_bay", L.BAY_SOFA_L, 0.80,
                               cover="damask_gold", nbu=6, nbv=2,
                               back_h=0.945),
                     L.BAY_SOFA[0], L.BAY_SOFA[1], R(90.0)))
    out.append(settle(FT.low_table("Table_bay_low", L.BAY_LOW_T[0],
                                   L.BAY_LOW_T[1], L.BAY_LOW_WD[0],
                                   L.BAY_LOW_WD[1], 0.42, wood='mahog')))
    out.append(settle(FT.ped_table("Table_bay_round", L.BAY_ROUND_T[0],
                                   L.BAY_ROUND_T[1], 0.33, 0.735)))
    for i, (x, y, r) in enumerate(L.BAY_CH):
        out.append(place(FS.bistro_chair("Chair_bay_%d" % i), x, y, R(r)))
    z = L.ground(*L.BAY_URN)
    out.append(FP.urn_planter("Urn_bay", L.BAY_URN[0], L.BAY_URN[1], z,
                              r=0.25, h=0.62))
    out.append(FP.bouquet("Flowers_bay", L.BAY_URN[0], L.BAY_URN[1], z + 0.56,
                          r=0.34, h=0.40, nstem=110))
    out.append(settle(FP.potted("Plant_bay", L.BAY_PLANT[0], L.BAY_PLANT[1],
                                0.0, r=0.22, ph=0.36, sp=0.80)))
    # clear of the flower urn: leaned at 9.55/6.35 its neck went through the
    # arrangement standing on the urn at 9.72/6.86
    out.append(FP.guitar("Guitar", 9.62, 6.34, L.STEP, rot=-150.0, lean=12.0))
    return out


# ---------------------------------------------------------------- fittings

# The four fixtures that actually light the room, and how hard.  Everything
# else in fittings() is a practical that glows without illuminating.
#
# Four, not thirty.  A lamp per fixture is defensible one fixture at a time
# and wrong as a whole: thirty small sources arriving from every direction
# cancel each other's modelling out, so the room ends up evenly grey with no
# sense of where the light is coming from, and EEVEE runs out of shadow
# atlas at about twenty of them anyway.  These four are spread one per zone
# so the room is lit right through without any of them having to carry it
# alone, and each is a real overhead fitting hanging in plain sight.  Colour
# is 2700-3000 K throughout - domestic tungsten, well under the 4000 K the
# brief calls for.
# Levels are set against a measurement rather than by eye.  stats.py reports
# a frame's mean luminance; the three reference photographs sit at 0.231,
# 0.238 and 0.246, so 0.235 is the number a render of this room aims at and
# "sufficient but not over lit" has an answer instead of an opinion.
LAMPS = {
    "Pendant_1": 300.0,       # opal schoolhouse on the cross beam, mid room
    "Pendant_ctr_a": 250.0,   # green enamel cone over the counter
    "Pendant_tiff": 300.0,    # leaded amber shade over the couch group
    "Chandelier": 240.0,      # antler chandelier over the entrance and bay
}


def fittings():
    """Every practical in the room.

    The set photographs show fixtures right across the ceiling - schoolhouse
    pendants on the cross beam, a green enamel cone over the counter, a
    leaded amber shade above the seating group, the antler chandelier by the
    door, sconces on the brick, neon in the windows - and all of them are
    here and all of them are lit.  Only the four in LAMPS carry light data;
    the rest glow through their own shade materials, which is what the
    lighting rule asks for and also what a real photograph of the set looks
    like, where most of the fittings are sources in frame rather than
    sources of the exposure."""
    out = []
    for i, (x, y) in enumerate(L.PENDANTS):
        nm = "Pendant_%d" % i
        out.append(FP.schoolhouse(nm, x, y, L.PENDANT_Z, L.BEAM_X_Z,
                                  energy=LAMPS.get(nm, 0.0)))
    # over the middle tables, and over the couch group
    out.append(FP.schoolhouse("Pendant_mid", 5.24, 7.60, 2.42, L.CZ,
                              energy=LAMPS.get("Pendant_mid", 0.0)))
    out.append(FP.tiffany_pendant("Pendant_tiff", 6.24, 5.10, 2.26, L.CZ,
                                  energy=LAMPS.get("Pendant_tiff", 0.0)))
    for nm, y in (("Pendant_ctr_a", 9.20), ("Pendant_ctr_b", 6.85)):
        out.append(FP.cone_pendant(nm, 2.05, y, 2.06, L.CZ,
                                   energy=LAMPS.get(nm, 0.0)))
    out.append(FP.antler_chandelier("Chandelier", L.CHANDELIER[0],
                                    L.CHANDELIER[1], 2.42,
                                    energy=LAMPS.get("Chandelier", 0.0)))
    # sconces on the brick, where the reference has them
    for i, (x, y, f) in enumerate((
            (0.055, 8.05, (1, 0)), (0.055, 10.60, (1, 0)),
            (L.EX - 0.02, 11.85, (-1, 0)), (0.055, 2.10, (1, 0)),
            (0.055, 5.05, (1, 0)), (L.EX - 0.02, 2.35, (-1, 0)))):
        # The two on the west wall sit ABOVE the back bar's top shelf: at
        # 1.86 their brackets reached into the shelving at 1.39-2.11.
        z = 2.34 if x < 0.5 and 4.2 < y < 12.7 else 1.86
        out.append(FP.sconce("Sconce_%d" % i, x, y, z, f))
    # the corridor: two plain opal globes on the lobby ceiling, emissive only
    for i, (gx, gy) in enumerate(((1.32, L.NY + 0.62), (2.70, L.HALL_N - 0.70),
                                  (4.90, L.HALL_N - 0.70))):
        out.append(FP.ceiling_globe("Globe_hall_%d" % i, gx, gy, 2.72))
    # the little shaded lamp on the bay table
    out.append(FP.table_lamp("Lamp_bay", L.BAY_ROUND_T[0] - 0.02,
                             L.BAY_ROUND_T[1], L.STEP + 0.735))
    # Neon.  Every neon word on this set is a joined-up script, so all of them
    # are bent tube out of FP's own alphabet rather than type pushed out of a
    # wall - see the note over _SCRIPT.
    out.append(FP.neon_script("Neon_latte", "Latte", 0.10, 11.55, 2.46, 0.155,
                              'FF3D7A', (1, 0), fit=0.86))
    # The cup, on the brick by the entrance.  Finding a wall for it took three
    # goes.  It was hung at EX + 0.03, which is 10 mm INSIDE the pier's own
    # face, so the moment it stopped being rotated 90 degrees it vanished into
    # the brickwork.  The pier's WEST face is 19 degrees off edge-on from
    # every camera in the room, which squashes a 0.45 m sign to 0.15.  And the
    # brick on the entrance diagonal, which faces the room properly, sits
    # directly behind the third cast-iron column.  What is left - and what the
    # reference shows, square to the eye - is the pier's SOUTH face: 21
    # degrees off head-on from the couch, unobstructed, 0.32 m wide, so the
    # cup is sized to it rather than the other way round.
    out.append(FP.neon_cup("Neon_cup", L.EX + L.TB * 0.5 + 0.01,
                           L.PIER[0] - 0.035, 2.30, 0.115, (0, -1)))
    # Cappuccino and Espresso hang INSIDE the transom band over the bay
    # windows, which is where entrance.webp has them - one in each of the two
    # northern lights - and each is fitted to its own light so it cannot run
    # off the end of the panel it is on.
    # tz is the BASELINE, and the ascenders reach 1.86 x-heights above it, so
    # it sits below the band's mid-line rather than on it
    tz = 2.86
    for nm, word, cy, xh in (("Neon_capp", "Cappuccino", 6.15, 0.115),
                             ("Neon_esp", "Espresso", 4.30, 0.115)):
        out.append(FP.neon_script(nm, word, L.BAY_E - 0.115, cy, tz, xh,
                                  'FF3244', (-1, 0), fit=1.24))
    # the arrow hangs off the cross beam, not off the painting wall
    out.append(FP.service_sign("Service", L.SERVICE_SIGN[0],
                               L.SERVICE_SIGN[1], L.SERVICE_SIGN[2],
                               w=L.SERVICE_WH[0], h=L.SERVICE_WH[1],
                               top=L.BEAM_X_Z))
    out.append(FP.painting("Painting", L.PAINTING[0], L.NY - 0.004,
                           L.PAINTING[1], L.PAINTING[2], (0, -1),
                           FP.ASSETS + "status_of_liberty_painting.png"))
    # the window decal, on the middle bay light, facing the street
    bx = (L.BAY_WIN[1][0] + L.BAY_WIN[1][1]) * 0.5
    out.append(FP.decal("Decal", L.BAY_E - 0.012, bx, 1.66, 1.28, (-1, 0),
                        FP.ASSETS + "central_perk_sticker.png"))
    return out


def curtains():
    out = []
    # bay window drapes, hung between the mullions
    for i, (a, b) in enumerate(L.BAY_WIN):
        for s, (u0, u1) in ((0, (a - 0.10, a + 0.30)), (1, (b - 0.30, b + 0.10))):
            out.append(FP.curtain("Curt_bay%d_%d" % (i, s),
                                  (L.BAY_E - 0.10, u0), (L.BAY_E - 0.10, u1),
                                  L.STORE_HEAD + 0.06, L.STEP + 0.02,
                                  folds=4, depth=0.048,
                                  mat='curtain' if s else 'curtain2'))
    # the tall street window north of the entrance
    for s, (u0, u1) in ((0, (L.E_WIN_N[0] - 0.08, L.E_WIN_N[0] + 0.34)),
                        (1, (L.E_WIN_N[1] - 0.34, L.E_WIN_N[1] + 0.08))):
        out.append(FP.curtain("Curt_en%d" % s, (L.EX - 0.10, u0),
                              (L.EX - 0.10, u1), 2.52, 0.02, folds=4,
                              depth=0.046, mat='curtain'))
    return out


def dressing():
    """The clutter.  A set that has nobody in it still has to look used."""
    out = []
    # A table standing on a rug is 12 mm higher than the floor it is on,
    # and L.ground() does not know about rugs - only G() does.  Every cup,
    # book and vase on this table was therefore placed 12 mm low and sat
    # with its foot buried in the top; on a china saucer that is most of
    # its thickness.  TOP() asks the same question settle() asks.
    def TOP(x, y, h):
        return G((x - 0.22, y - 0.22, x + 0.22, y + 0.22)) + h
    cx, cy = L.COFFEE_C[0], L.COFFEE_C[1]
    cz = TOP(cx, cy, L.COFFEE_H)
    out.append(FP.bouquet("Flowers_coffee", cx + 0.44, cy - 0.10, cz,
                          r=0.16, h=0.20, nstem=16, vase=(0.115, 0.105, None),
                          colours=('E2621F', 'E8A41C', 'D8324A')))
    for i, (dx, dy, col) in enumerate(((-0.42, 0.14, 'EDE8DC'),
                                       (-0.18, -0.16, 'E8D24A'),
                                       (0.10, 0.18, 'D8E4C8'))):
        out.append(FP.cup("Cup_c%d" % i, cx + dx, cy + dy, cz, colour=col,
                          rot=i * 47))
    # a stack, not two books side by side on the same plane: laid at the same
    # height they share their whole underside, which is a guaranteed z-fight
    for i, (dx, dy, col, rt) in enumerate(((-0.05, -0.06, '2E4A7A', 8),
                                           (-0.03, -0.09, '9E3A24', -13),
                                           (-0.06, -0.05, 'C8B24A', 21))):
        out.append(FP.book("Book_c%d" % i, cx + dx, cy + dy,
                           cz + i * 0.030, colour=col, rot=rt))
    # a cup on most of the little tables
    for i, (x, y, h) in enumerate(((L.TABLE_1[0] + 0.10, L.TABLE_1[1], 0.735),
                                   (L.TABLE_2[0] - 0.08, L.TABLE_2[1] + 0.06, 0.735),
                                   (L.SIDE_T_C[0], L.SIDE_T_C[1] + 0.05, 0.735),
                                   # off-centre: the table lamp stands on the
                                   # middle of this one
                                   (L.BAY_ROUND_T[0] + 0.19,
                                    L.BAY_ROUND_T[1] - 0.11, 0.735),
                                   (L.SIDE_T_S[0], L.SIDE_T_S[1], 0.70))):
        z = TOP(x, y, h)
        out.append(FP.cup("Cup_t%d" % i, x, y, z, colour='EDE8DC', rot=i * 33))
    # flowers on the alcove and bay tables
    out.append(FP.bouquet("Flowers_oval", L.OVAL_T[0], L.OVAL_T[1],
                          TOP(L.OVAL_T[0], L.OVAL_T[1], 0.42),
                          r=0.15, h=0.22, nstem=14,
                          vase=(0.110, 0.115, '6E5A3A')))
    out.append(FP.bouquet("Flowers_bayt", L.BAY_LOW_T[0], L.BAY_LOW_T[1],
                          TOP(L.BAY_LOW_T[0], L.BAY_LOW_T[1], 0.42), r=0.14, h=0.20, nstem=12,
                          vase=(0.105, 0.100, None)))
    return out


def build():
    M.coll(C); M.coll(CR); M.coll(FP.C); M.coll(FP.CD)
    RUGS.clear()
    FS.MAT.clear(); FT.MAT.clear(); FC.MAT.clear(); FP.MAT.clear()
    # rugs first: everything else needs to know what it is standing on
    rug("main", *L.RUG_MAIN)
    rug("oval", *L.RUG_OVAL, oval=True,
        pal=dict(ground='7E3320', border='30405E', motif='CFC098'))
    rug("mid", *L.RUG_MID,
        pal=dict(ground='96361F', border='23364F', motif='D6C49C'))
    rug("north", *L.RUG_N,
        pal=dict(ground='8A2A20', border='24405A', motif='D2C098'))
    rug("south", *L.RUG_S,
        pal=dict(ground='922C1E', border='2A3A54', motif='D8C69E'))
    rug("bay", *L.BAY_RUG,
        pal=dict(ground='8E3524', border='2E4258', motif='D4C29A',
                 accent='3A5C40'))
    # The bay platform is 7.4 m long and one rug covered less than half of
    # it, which left a bare white tiled apron between the seating and the
    # doors - in top_view.webp that stretch is carpeted too, and an empty
    # floor that size reads as a set with the dressing not finished.
    rug("bay_n", *L.BAY_RUG_N,
        pal=dict(ground='7E3020', border='27395A', motif='CFBE96',
                 accent='355340'))
    groups = []
    groups += main_group()
    groups += counter_group()
    groups += tables_zone()
    groups += north_alcove()
    groups += south_zone()
    groups += bay()
    groups += fittings()
    groups += curtains()
    groups += dressing()
    n = len([o for o in bpy.data.objects
             if o.users_collection and
             o.users_collection[0].name in (C, CR, FP.C, FP.CD, FC.C)])
    print("layout:", n)
    return groups
