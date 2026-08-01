"""Monica's kitchen: turquoise casework, butcher-block counters, pro range,
double sink, retro fridge, open shelving, hanging pot rack, rattan pendant."""
import bpy, math, random
from mathutils import Matrix, Vector
import mlib, mats, L
import s_openings as O

C = "Kitchen"
CTR_H, CTR_D, TOE = L.CTR_H, L.CTR_D, L.TOE
TOP_T = 0.042          # butcher block thickness
# the big turquoise unit over the counter is a set of cubbies, not one long
# ladder of boards - four bays, with the outer two shelved differently
SHELF_BAYS = 4
SHELF_TIERS = (3, 4, 4, 3)


# ------------------------------------------------------------------ materials
def mk_mats():
    M = {}
    M['turq'] = mats.get('paint_turquoise') or mats.paint('paint_turquoise', L.TURQ)
    M['turq2'] = mats.paint('paint_turq_dark', '2A8E9C', rough=0.32, coat=0.20)
    M['block'] = mats.wood('wood_butcher', ('D6B078', 'B98C4E', '8E6430'),
                           ring=14.0, warp=0.08, bump=0.16, rough=(0.20, 0.36),
                           axis='Y')
    M['block_n'] = mats.wood('wood_butcher_n', ('D6B078', 'B98C4E', '8E6430'),
                             ring=14.0, warp=0.08, bump=0.16, rough=(0.20, 0.36),
                             axis='X')
    M['ovenglass'] = mats.paint('oven_glass', '17161A', rough=0.10, coat=0.85)
    # the set range is a satin bronze, not chrome - at 0.26 roughness it only
    # mirrored the dark kitchen and read as a black box
    M['steel'] = mats.metal('metal_range', 'A28C6C', rough=0.42, bump=0.02,
                            aniso=0.6, brush=(1, 40, 1))
    M['steel_d'] = mats.metal('metal_range_dark', '35312B', rough=0.44, bump=0.08)
    M['chrome'] = mats.get('metal_chrome') or mats.metal('metal_chrome', 'D8DCE0',
                                                         rough=0.10)
    # A flat chrome face at 0.10 roughness mirrors the unlit room and goes
    # black; the range knobs read bright on the set, so give them a satin finish
    # that gathers light instead of reflecting the far wall.
    M['chrome_s'] = mats.metal('metal_chrome_satin', 'DEE2E5', rough=0.25,
                               bump=0.02)
    M['sink'] = mats.metal('metal_sink', 'C4C8CB', rough=0.31, bump=0.03,
                           aniso=0.45, brush=(1, 30, 1))
    M['castiron'] = mats.paint('cast_iron', '1B1A19', rough=0.55, bump=0.14,
                               noise=260)
    M['enamel'] = mats.paint('enamel_fridge', 'EFEDE2', rough=0.13, coat=0.55,
                             variation=0.012)
    M['celadon'] = mats.paint('paint_celadon', 'C4D49A', rough=0.32, coat=0.18)
    M['copper'] = mats.metal('metal_copper', 'B87333', rough=0.33, bump=0.06)
    # The pans' tinned linings and their polished strap handles.  Both are kept
    # well off a mirror finish: below about 0.4 roughness a metal in here stops
    # showing its own colour and just returns the cold window, which turned the
    # linings into bowls of milk.
    M['tin'] = mats.metal('metal_tinned', 'BFAD8E', rough=0.50, bump=0.02,
                          scale=620.0)
    M['panhandle'] = mats.metal('metal_panhandle', 'A9A69F', rough=0.31,
                                bump=0.04, aniso=0.3, brush=(1, 1, 26))
    M['perf'] = mats.perforated('metal_perf', 'A7ACB0', rough=0.34,
                                around=48, rows=12, hole=0.20, vmin=0.40)
    M['iron'] = mats.metal('metal_wrought', '35322E', rough=0.48, bump=0.16)
    M['glass'] = mats.get('glass_clear') or mats.pane('glass_clear')
    # both oven towels are small gingham checks on the set, not flat colours -
    # at this size the check is most of what makes them read as cloth
    M['towel_r'] = mats.gingham('towel_rust', band=0.0055, light='E9DDCB',
                                dark='B4502C', rough=0.86, sheen=0.35,
                                weave=1400.0, bump=0.28)
    M['towel_b'] = mats.gingham('towel_navy', band=0.0055, light='E4E6E4',
                                dark='2F4C7A', rough=0.86, sheen=0.35,
                                weave=1400.0, bump=0.28)
    return M


# ------------------------------------------------------------------- casework
def slab_door(name, w, h, t=0.019, cname=C, mat=None, rail=0.062):
    """Shaker-ish door: frame with a shallow recessed panel, pull included."""
    fr = mlib.panel_with_holes(name + "_f", w, h, t,
                               [(rail, rail, w - rail, h - rail)], cname)
    fr.data.transform(Matrix.Translation((-w / 2, 0, 0)))
    pan = mlib.box(name + "_p", -w / 2 + rail - 0.006, t * 0.42, rail - 0.006,
                   w / 2 - rail + 0.006, t * 0.42 + 0.010, h - rail + 0.006, cname)
    ob = mlib.join([fr, pan], name, cname)
    mlib.bevel(ob, 0.0025, 2, 45)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def bar_pull(name, ln=0.135, cname=C, mat=None):
    parts = []
    parts.append(mlib.revolve(name + "_b", [(0.0, 0.0), (0.0065, 0.0),
                                            (0.0065, ln), (0.0, ln)], 14, cname=cname))
    for z in (0.012, ln - 0.012):
        p = mlib.revolve(name + "_p", [(0.0, 0.0), (0.0055, 0.0), (0.0055, 0.026),
                                       (0.0, 0.026)], 12, cname=cname)
        mlib.rot_x(p, math.pi / 2)
        mlib.translate(p, (0, 0, z))
        parts.append(p)
    ob = mlib.join(parts, name, cname)
    mlib.translate(ob, (0, 0, -ln / 2))
    mlib.smooth_shade(ob, 34)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def base_run(name, p0, p1, M, doors=2, drawers=0, dr_h=0.16, depth=CTR_D,
             top=True, top_mat=None, cname=C):
    """Base cabinet run along p0->p1 (interior side is to the RIGHT of travel,
    i.e. carcass grows away from the wall)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux                      # into the room
    parts = []
    # carcass (front face held back 21 mm so the doors never sit coplanar)
    car = mlib.box(name + "_car", 0.0, TOE, TOE, ln, depth - 0.021,
                   CTR_H - TOP_T, cname)
    parts.append((car, M['turq']))
    kick = mlib.box(name + "_kick", 0.0, TOE + 0.055, 0.0, ln, depth - 0.030,
                    TOE, cname)
    parts.append((kick, M['turq2']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        objs.append(ob)
    # fronts
    z0 = TOE
    fh = CTR_H - TOP_T - TOE
    rows = []
    if drawers:
        for i in range(drawers):
            rows.append(('dr', dr_h))
    rows.append(('dr_or_door', fh - drawers * dr_h))
    zz = z0
    fronts = []
    for kind, hh in rows:
        n = doors if kind != 'dr' else 1
        for i in range(n):
            w = (ln - 0.012 * (n + 1)) / n
            cx = 0.006 + i * (w + 0.012) + w / 2
            d = slab_door(name + "_d", w, hh - 0.010, 0.019, cname, M['turq'],
                          rail=0.055 if kind != 'dr' else 0.038)
            mlib.translate(d, (cx, depth - 0.019, zz + 0.005))
            fronts.append(d)
            pl = bar_pull(name + "_pl", 0.125 if kind == 'dr' else 0.115, cname,
                          M['chrome'])
            if kind == 'dr':
                mlib.rot_y(pl, math.pi / 2)
                mlib.translate(pl, (cx, depth + 0.028, zz + hh * 0.55))
            else:
                mlib.translate(pl, (cx + w / 2 - 0.058, depth + 0.028,
                                    zz + hh - 0.14))
            fronts.append(pl)
        zz += hh
    # place everything: local x along the run, local y into the room, from the wall
    grp = objs + fronts
    for ob in grp:
        M4 = Matrix(((ux, nx, 0.0, p0[0]), (uy, ny, 0.0, p0[1]),
                     (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
        ob.data.transform(M4)
        mlib.recalc_normals(ob)
    if top:
        tp = mlib.box(name + "_top", -0.002, -0.012, CTR_H - TOP_T, ln + 0.002,
                      depth + 0.022, CTR_H, cname)
        M4 = Matrix(((ux, nx, 0.0, p0[0]), (uy, ny, 0.0, p0[1]),
                     (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
        tp.data.transform(M4)
        mlib.recalc_normals(tp)
        mlib.bevel(tp, 0.005, 3, 45)
        mlib.set_mat(tp, top_mat or M['block'])
    return grp


# --------------------------------------------------------------- open shelving
def shelf_unit(name, p0, p1, z0, z1, depth, tiers, M, cname=C, back=False,
               bays=0, stagger=()):
    """Open shelving.  `bays` adds vertical dividers, splitting the run into
    cubbies the way the set unit is built - without them the shelves read as
    one long ladder of boards.  `stagger` gives a per-bay tier count so the
    cubbies are not all identical."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux
    t = 0.024
    parts = []
    parts.append(mlib.box(name + "_l", 0.0, 0.0, z0, t, depth, z1, cname))
    parts.append(mlib.box(name + "_r", ln - t, 0.0, z0, ln, depth, z1, cname))
    parts.append(mlib.box(name + "_top", 0.0, 0.0, z1 - t * 1.4, ln, depth, z1, cname))
    parts.append(mlib.box(name + "_bot", 0.0, 0.0, z0, ln, depth, z0 + t * 1.4, cname))
    inner = (z1 - t * 1.4) - (z0 + t * 1.4)
    zb, zt = z0 + t * 1.4, z1 - t * 1.4
    if bays > 1:
        edges = [t] + [ln * i / bays for i in range(1, bays)] + [ln - t]
        for i in range(1, bays):
            xx = edges[i]
            parts.append(mlib.box(name + "_d%d" % i, xx - t / 2, 0.0, zb,
                                  xx + t / 2, depth, zt, cname))
        for k in range(bays):
            nt = stagger[k % len(stagger)] if stagger else tiers
            a, b2 = edges[k] + (t / 2 if k else 0), edges[k + 1] - (t / 2 if k < bays - 1 else 0)
            for i in range(1, nt):
                zz = zb + inner * i / nt
                parts.append(mlib.box(name + "_s%d_%d" % (k, i), a, 0.0,
                                      zz - t / 2, b2, depth, zz + t / 2, cname))
    else:
        for i in range(1, tiers):
            zz = zb + inner * i / tiers
            parts.append(mlib.box(name + "_s%d" % i, t, 0.0, zz - t / 2,
                                  ln - t, depth, zz + t / 2, cname))
    if back:
        parts.append(mlib.box(name + "_bk", 0.0, 0.0, z0, ln, 0.008, z1, cname))
    for ob in parts:
        M4 = Matrix(((ux, nx, 0.0, p0[0]), (uy, ny, 0.0, p0[1]),
                     (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
        ob.data.transform(M4)
        mlib.recalc_normals(ob)
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.002, 2, 45)
    mlib.set_mat(ob, M['turq'])
    return ob


def wedge_shelf(name, p0, p1, z, depth, M, cname=C):
    """Shallow bottle shelf with the triangular bracket end."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux
    t = 0.024
    parts = [mlib.box(name + "_s", 0.0, 0.0, z, ln, depth, z + t, cname),
             mlib.box(name + "_lip", 0.0, depth - t, z, ln, depth, z + 0.055, cname)]
    tri = mlib.prism_xz(name + "_tri",
                        [(0.0, z + t), (0.0, z + 0.40), (0.0 + 0.02, z + 0.40),
                         (depth, z + t)], 0.0, t, cname)
    mlib.rotate_z(tri, 0) if False else None
    # rebuild the triangle in the run's local frame: it spans y (depth) and z
    bpy.data.objects.remove(tri, do_unlink=True)
    vs = [(0.0, 0.0, z + t), (0.0, depth, z + t), (0.0, 0.0, z + 0.42),
          (t, 0.0, z + t), (t, depth, z + t), (t, 0.0, z + 0.42)]
    fs = [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    tri = mlib.mesh_obj(name + "_tri", vs, fs, cname)
    mlib.recalc_normals(tri)
    parts.append(tri)
    for ob in parts:
        M4 = Matrix(((ux, nx, 0.0, p0[0]), (uy, ny, 0.0, p0[1]),
                     (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
        ob.data.transform(M4)
        mlib.recalc_normals(ob)
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.002, 2, 45)
    mlib.set_mat(ob, M['turq'])
    return ob


# ------------------------------------------------------------------ peninsula
def peninsula(name, M, cname=C):
    x0, x1 = 0.0, 0.60
    y0, y1 = L.KIT_PEN
    t = 0.024
    parts = []
    # side panels (east face is the solid one that faces the room)
    parts.append(mlib.box(name + "_e", x1 - t, y0, 0.0, x1, y1, CTR_H - 0.03, cname))
    parts.append(mlib.box(name + "_w", x0, y0, 0.0, x0 + t, y1, CTR_H - 0.03, cname))
    parts.append(mlib.box(name + "_n", x0, y1 - t, 0.0, x1, y1, CTR_H - 0.03, cname))
    for i, zz in enumerate((0.20, 0.44, 0.68)):
        parts.append(mlib.box(name + "_s%d" % i, x0 + t, y0, zz, x1 - t, y1 - t,
                              zz + t, cname))
    top = mlib.box(name + "_top", x0 - 0.018, y0 - 0.026, CTR_H - 0.03,
                   x1 + 0.030, y1 + 0.018, CTR_H, cname)
    mlib.bevel(top, 0.006, 2, 45)
    parts.append(top)
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.002, 2, 45)
    mlib.set_mat(ob, M['turq'])
    # wooden mail pocket on the east face
    mp = []
    # shield-topped back board with a pocket in front of it; the pocket's top
    # edge dips in the middle so you can get at what is filed in it
    back = mlib.prism_xz(name + "_mb",
                         [(0.0, 0.0), (0.196, 0.0), (0.196, 0.222),
                          (0.176, 0.268), (0.140, 0.294), (0.098, 0.302),
                          (0.056, 0.294), (0.020, 0.268), (0.0, 0.222)],
                         0.0, 0.015, cname)
    mp.append(back)
    dip = [(0.010, 0.0), (0.186, 0.0), (0.186, 0.140), (0.170, 0.128),
           (0.132, 0.116), (0.098, 0.113), (0.064, 0.116), (0.026, 0.128),
           (0.010, 0.140)]
    front = mlib.prism_xz(name + "_mf", dip, 0.0, 0.013, cname)
    mlib.translate(front, (0, 0.082, 0))
    mp.append(front)
    mp.append(mlib.box(name + "_mbase", 0.010, 0.0, -0.002, 0.186, 0.085, 0.011, cname))
    pocket = mlib.join(mp, name + "_mail", cname)
    mlib.bevel(pocket, 0.002, 2, 45)
    mlib.rotate_z(pocket, -math.pi / 2)
    mlib.translate(pocket, (x1 + 0.001, (y0 + y1) / 2 + 0.098, 0.475))
    mlib.set_mat(pocket, mats.wood('wood_plaque', ('C39A62', 'A57B44', '85602F'),
                                   ring=44, warp=0.7, bump=0.30, axis='Y',
                                   grain_relief=0.40))
    return ob


# ---------------------------------------------------------------------- range
def pro_range(name, M, cname=C):
    """The set range is a professional gas cooker in satin bronze - one finish
    from the backguard to the plinth, not a black box with brass trim.  What
    identifies it: continuous cast-iron grates over six burners, a slotted
    backguard, five big chrome knobs on a deep fascia, and a full-width tubular
    handle across the top of the oven door.  That handle is also the towel rail;
    there is no separate bar."""
    y0, y1 = L.KIT_STOVE
    w = y1 - y0
    x0, x1 = 0.0, CTR_D - 0.01
    parts = []
    body = mlib.box(name + "_body", x0, y0, 0.0, x1 - 0.02, y1, CTR_H - 0.015, cname)
    mlib.bevel(body, 0.006, 2, 45)
    parts.append((body, M['steel']))
    # control fascia - bronze like everything else, and deep enough to carry the
    # knobs proud of the door below it
    fas = mlib.box(name + "_fas", x1 - 0.052, y0, CTR_H - 0.190, x1, y1,
                   CTR_H - 0.015, cname)
    mlib.bevel(fas, 0.004, 2, 45)
    parts.append((fas, M['steel']))
    # cook top: a shallow recessed pan the grates sit down into
    ct = mlib.box(name + "_ct", x0 + 0.014, y0 + 0.010, CTR_H - 0.030, x1 - 0.052,
                  y1 - 0.010, CTR_H - 0.004, cname)
    parts.append((ct, M['steel_d']))
    GX = (x0 + 0.175, x0 + 0.430)
    GY = [y0 + 0.145 + j * (w - 0.29) / 2.0 for j in range(3)]
    for gx in GX:
        for gy in GY:
            bu = mlib.revolve(name + "_bu", [(0.0, 0.0), (0.045, 0.004),
                                             (0.047, 0.013), (0.028, 0.020),
                                             (0.013, 0.030), (0.0, 0.030)], 20,
                              cname=cname)
            mlib.translate(bu, (gx, gy, CTR_H - 0.028))
            mlib.smooth_shade(bu, 40)
            parts.append((bu, M['castiron']))
    # One continuous cast-iron grate per column of three burners, ribbed the
    # long way: separate round trivets read as a domestic hob, and the whole
    # point of the set range is that the top is covered edge to edge.
    for c, gx in enumerate(GX):
        gw, gd = (w - 0.10) / 3.0, 0.245
        for j, gy in enumerate(GY):
            gp = []
            for s in (-1, 1):             # side rails
                gp.append(mlib.box(name + "_gs", gx - gd / 2, gy + s * gw / 2 - 0.0055,
                                   0.0, gx + gd / 2, gy + s * gw / 2 + 0.0055,
                                   0.023, cname))
            # two ribs, not four: a closer grid closes the grate up into a
            # waffle and you lose the burner and the light under it
            for i in range(2):            # ribs running front to back
                yy = gy - gw / 2 + (i + 1) * gw / 3.0
                gp.append(mlib.box(name + "_gb", gx - gd / 2, yy - 0.0045, 0.009,
                                   gx + gd / 2, yy + 0.0045, 0.023, cname))
            for s in (-1, 1):             # end rails, so the grate reads closed
                gp.append(mlib.box(name + "_ge", gx + s * gd / 2 - 0.0055,
                                   gy - gw / 2, 0.0, gx + s * gd / 2 + 0.0055,
                                   gy + gw / 2, 0.023, cname))
            gr = mlib.join(gp, name + "_grate%d%d" % (c, j), cname)
            mlib.bevel(gr, 0.0018, 1, 45)
            mlib.translate(gr, (0, 0, CTR_H - 0.004))
            parts.append((gr, M['castiron']))
    # back riser with its slotted vent
    riser = mlib.box(name + "_riser", x0, y0, CTR_H - 0.030, x0 + 0.052, y1,
                     CTR_H + 0.118, cname)
    mlib.bevel(riser, 0.005, 2, 45)
    parts.append((riser, M['steel']))
    for i in range(9):
        sy = y0 + 0.075 + i * (w - 0.15) / 8.0
        sl = mlib.box(name + "_sl", x0 + 0.048, sy - 0.014, CTR_H + 0.030,
                      x0 + 0.056, sy + 0.014, CTR_H + 0.092, cname)
        parts.append((sl, M['steel_d']))
    # --- oven door ----------------------------------------------------------
    DZ0, DZ1 = 0.152, CTR_H - 0.196
    od = mlib.panel_with_holes(name + "_od", w - 0.030, DZ1 - DZ0, 0.026,
                               [(0.072, 0.068, w - 0.102, DZ1 - DZ0 - 0.175)],
                               cname)
    # panel_with_holes lays the panel out in local x/z with its thickness on y,
    # so the width axis maps to world y and the height axis to world z
    od.data.transform(Matrix(((0, 1, 0, x1 - 0.030), (1, 0, 0, y0 + 0.015),
                              (0, 0, 1, DZ0), (0, 0, 0, 1))))
    mlib.recalc_normals(od)
    mlib.bevel(od, 0.004, 2, 45)
    parts.append((od, M['steel']))
    gl = mlib.box(name + "_odgl", x1 - 0.024, y0 + 0.087, DZ0 + 0.068,
                  x1 - 0.014, y1 - 0.087, DZ1 - 0.107, cname)
    parts.append((gl, M['ovenglass']))
    # full-width tubular handle on two heavy standoffs - this is the towel rail
    HZ = DZ1 - 0.052
    tb = mlib.revolve(name + "_tb", [(0.0, 0.0), (0.0115, 0.0), (0.0115, w - 0.086),
                                     (0.0, w - 0.086)], 16, cname=cname)
    mlib.rot_x(tb, -math.pi / 2)
    mlib.translate(tb, (x1 + 0.042, y0 + 0.043, HZ))
    mlib.smooth_shade(tb, 34)
    parts.append((tb, M['chrome_s']))
    for yy in (y0 + 0.043, y1 - 0.043):
        st = mlib.revolve(name + "_st", [(0.0, 0.0), (0.016, 0.0), (0.016, 0.030),
                                         (0.011, 0.042), (0.0, 0.042)], 14,
                          cname=cname)
        mlib.rot_y(st, math.pi / 2)
        mlib.translate(st, (x1 - 0.002, yy, HZ))
        mlib.smooth_shade(st, 36)
        parts.append((st, M['chrome_s']))
    # five chunky chrome knobs with a dark centre boss
    for j in range(5):
        ky = y0 + 0.092 + j * (w - 0.184) / 4.0
        # a flat-faced chrome disc on a short waist - a domed knob catches one
        # highlight dead centre and turns into an eyeball
        kb = mlib.revolve(name + "_kb", [(0.0, 0.0), (0.017, 0.0), (0.017, 0.008),
                                         (0.031, 0.013), (0.032, 0.024),
                                         (0.029, 0.028), (0.0, 0.028)], 24,
                          cname=cname)
        mlib.rot_y(kb, math.pi / 2)
        mlib.translate(kb, (x1 + 0.001, ky, CTR_H - 0.100))
        mlib.smooth_shade(kb, 32)
        parts.append((kb, M['chrome_s']))
        pt = mlib.box(name + "_kpt", x1 + 0.028, ky - 0.0022, CTR_H - 0.094,
                      x1 + 0.030, ky + 0.0022, CTR_H - 0.076, cname)
        parts.append((pt, M['castiron']))
    # lower drawer
    dw = mlib.box(name + "_dw", x1 - 0.028, y0 + 0.015, 0.022, x1 - 0.004,
                  y1 - 0.015, DZ0 - 0.012, cname)
    mlib.bevel(dw, 0.004, 2, 45)
    parts.append((dw, M['steel']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        objs.append(ob)
    # towels thrown over the door handle
    for k, (yy, mm) in enumerate(((y0 + 0.255, M['towel_r']),
                                  (y0 + 0.495, M['towel_b']))):
        tw = towel(name + "_tw%d" % k, cname, seed=k * 7 + 3)
        mlib.rotate_z(tw, math.pi / 2)
        mlib.translate(tw, (x1 + 0.042, yy, HZ))
        mlib.set_mat(tw, mm)
    return objs


def towel(name, cname=C, w=0.235, drop=0.345, back=0.215, r=0.014, seed=0):
    """Dish towel thrown over the oven handle.  Two things have to be true or it
    reads as a panel screwed to the door: the cloth has to carry on over the bar
    and back down the far side, and the two tails have to be different lengths -
    nobody lines them up - so the fold and the near hem both show.

    Each column of the loft gets its own hem height and its own swing away from
    the door, so the bottom edge is a wandering line rather than a ruled one,
    and the front hem kicks out at the bottom the way a hanging cloth curls."""
    rng = random.Random(seed)
    ph = rng.uniform(0.0, math.tau)
    nu, tail = 17, 14
    rings = []
    for k in range(nu):
        s = k / (nu - 1.0)
        xx = (s - 0.5) * w
        sw = 0.85 + 0.30 * math.sin(s * 5.3 + ph)
        df = drop * (1.0 + 0.055 * math.sin(s * 4.1 + ph * 1.7))
        db = back * (1.0 + 0.080 * math.sin(s * 3.3 + ph))
        prof = []
        for i in range(tail, 0, -1):      # outer tail: hem -> bar, room side
            t = i / tail
            prof.append((-r - 0.018 * sw * math.sin(t * 2.3) - 0.030 * t ** 3,
                         -df * t))
        for i in range(13):               # over the bar, outer -> inner
            a = math.pi * i / 12.0
            prof.append((-r * math.cos(a), r * math.sin(a)))
        for i in range(1, tail + 1):      # inner tail, hanging against the door
            t = i / tail
            prof.append((r + 0.011 * sw * math.sin(t * 2.6), -db * t))
        rings.append([(xx, y, z) for (y, z) in prof])
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, 0.0038, offset=0)
    mlib.smooth_shade(ob, 50)
    return ob


# ----------------------------------------------------------------------- sink
def double_sink(name, M, cname=C):
    (dxc, dyc), cl = L.chamfer_dir()
    inw = (dyc, -dxc)
    cen = L.chamfer_pt(cl * 0.5, CTR_D * 0.52)
    parts = []
    # The rim has to be a frame, not a plate.  It was a solid prism across the
    # whole 780 x 440 footprint, which lidded both bowls: the basins were there
    # underneath all along, you simply could not see into them, and the sink
    # read as a flat tray sitting on the worktop.
    HX, HY, GAP = 0.1725, 0.1875, 0.0155
    for nm, a in ((name + "_rf", (-0.39, -0.22, 0.39, -HY)),
                  (name + "_rb", (-0.39, HY, 0.39, 0.22)),
                  (name + "_rl", (-0.39, -HY, -0.188 - HX, HY)),
                  (name + "_rr", (0.188 + HX, -HY, 0.39, HY)),
                  (name + "_rc", (-GAP, -HY, GAP, HY))):
        o = mlib.box(nm, a[0], a[1], CTR_H - 0.004, a[2], a[3], CTR_H + 0.004,
                     cname)
        mlib.bevel(o, 0.003, 2, 45)
        parts.append(o)
    for sx in (-1, 1):
        bowl = []
        r = mlib.rounded_rect(0.345, 0.375, 0.040, 4)
        lv = [(0.0, 1.0), (-0.03, 0.985), (-0.14, 0.955), (-0.175, 0.90)]
        rings = []
        for (dz, s) in lv:
            rings.append([(x * s + sx * 0.188, y * s, CTR_H + dz) for (x, y) in r])
        rings.append([(x * 0.86 + sx * 0.188, y * 0.86, CTR_H - 0.178)
                      for (x, y) in r])
        bw = mlib._loft(name + "_bw", rings, close_u=False, close_v=True,
                        cname=cname, cap_start=False, cap_end=True)
        mlib.bevel(bw, 0.004, 2, 50)
        parts.append(bw)
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 32)
    # satin stainless, not mirror chrome: at 0.10 roughness the two bowls filled
    # with the ceiling's reflection and the sink read as a flat tray
    mlib.set_mat(ob, M['sink'])
    ang = math.atan2(dyc, dxc)
    mlib.rotate_z(ob, ang)
    mlib.translate(ob, (cen[0], cen[1], 0.0))
    # gooseneck faucet
    prof = [(0.0, 0.0), (0.030, 0.0), (0.030, 0.030), (0.020, 0.045),
            (0.019, 0.150)]
    base = mlib.revolve(name + "_fb", prof, 20, cname=cname)
    path = [(0, 0, 0.150)]
    for i in range(1, 13):
        t = i / 12.0
        a = math.pi * t
        path.append((0.085 * (1 - math.cos(a)), 0, 0.150 + 0.115 * math.sin(a)))
    neck = mlib.tube_along(name + "_fn", path, mlib.circle(0.0165, 12), cname)
    lever = mlib.revolve(name + "_fl", [(0.0, 0.0), (0.011, 0.0), (0.011, 0.075),
                                        (0.0, 0.080)], 12, cname=cname)
    mlib.rot_y(lever, math.radians(-58))
    mlib.translate(lever, (-0.028, 0.0, 0.118))
    fa = mlib.join([base, neck, lever], name + "_faucet", cname)
    mlib.smooth_shade(fa, 34)
    mlib.set_mat(fa, M['chrome'])
    fc = L.chamfer_pt(cl * 0.5, 0.16)
    mlib.rotate_z(fa, ang)
    mlib.translate(fa, (fc[0], fc[1], CTR_H))
    return ob


# ---------------------------------------------------------------------- fridge
def fridge(name, M, cname=C):
    x0, x1 = L.FRIDGE_X
    d = 0.70
    y1 = L.NY - 0.012
    y0 = y1 - d
    w = x1 - x0
    parts = []
    # rounded-corner body built as a lofted superellipse prism
    prof = mlib.rounded_rect(w, d, 0.055, 5)
    rings = []
    for (dz, s, sy) in ((0.10, 0.965, 0.99), (0.16, 1.0, 1.0), (1.60, 1.0, 1.0),
                        (1.70, 0.985, 0.992), (1.735, 0.94, 0.96)):
        rings.append([(x * s, y * sy, dz) for (x, y) in prof])
    body = mlib._loft(name + "_b", rings, close_u=False, close_v=True, cname=cname,
                      cap_start=True, cap_end=True)
    mlib.bevel(body, 0.006, 2, 50)
    mlib.smooth_shade(body, 34)
    parts.append((body, M['enamel']))
    # base plinth
    pl = mlib.prism(name + "_pl", mlib.rounded_rect(w - 0.03, d - 0.03, 0.03, 3),
                    0.0, 0.10, cname)
    parts.append((pl, M['steel_d']))
    # door split line + freezer door
    gap = mlib.box(name + "_gap", -w / 2 - 0.001, -d / 2 - 0.004, 1.26,
                   w / 2 + 0.001, -d / 2 + 0.004, 1.272, cname)
    parts.append((gap, M['steel_d']))
    # chrome handle: long vertical bar with a base plate
    hb = mlib.prism(name + "_hb", mlib.rounded_rect(0.048, 0.62, 0.020, 4),
                    0.0, 0.012, cname)
    mlib.rot_x(hb, -math.pi / 2)
    mlib.translate(hb, (w / 2 - 0.085, -d / 2 - 0.004, 0.92))
    parts.append((hb, M['chrome_s']))
    hl = mlib.revolve(name + "_hl", [(0.0, 0.0), (0.013, 0.0), (0.013, 0.40),
                                     (0.0, 0.40)], 14, cname=cname)
    mlib.translate(hl, (w / 2 - 0.085, -d / 2 - 0.038, 0.72))
    mlib.smooth_shade(hl, 34)
    parts.append((hl, M['chrome_s']))
    for zz in (0.72, 1.12):
        st = mlib.revolve(name + "_hs", [(0.0, 0.0), (0.008, 0.0), (0.008, 0.036),
                                         (0.0, 0.036)], 10, cname=cname)
        mlib.rot_x(st, -math.pi / 2)
        mlib.translate(st, (w / 2 - 0.085, -d / 2 - 0.038, zz))
        parts.append((st, M['chrome_s']))
    hf = mlib.prism(name + "_hf", mlib.rounded_rect(0.10, 0.036, 0.014, 3),
                    0.0, 0.030, cname)
    mlib.rot_x(hf, -math.pi / 2)
    mlib.translate(hf, (w / 2 - 0.085, -d / 2 - 0.004, 1.40))
    parts.append((hf, M['chrome_s']))
    # badge
    bg = mlib.prism(name + "_bg", mlib.rounded_rect(0.09, 0.024, 0.010, 3),
                    0.0, 0.006, cname)
    mlib.rot_x(bg, -math.pi / 2)
    mlib.translate(bg, (0.0, -d / 2 - 0.002, 1.52))
    parts.append((bg, M['chrome_s']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, ((x0 + x1) / 2, (y0 + y1) / 2, 0.0))
        objs.append(ob)
    return objs


# -------------------------------------------------------------- hanging things
def _saucepan(name, rr, hh, hl, M, cname, lined=True):
    """A French copper pan, built mouth-up (+Z) with its long strap handle
    running out along +X.  Returns (parts, eye) - 'eye' is the hanging hole at
    the handle tip, in the same local frame, which is what the S-hook takes."""
    parts, wall = [], 0.0032
    # a flat base with a crisp edge, then straight walls - the rounded bottom a
    # smoother profile gives reads as an egg the moment the pan turns on its side
    prf = [(0.0, 0.0), (rr * 0.90, 0.0), (rr, 0.017), (rr, hh),
           (rr - wall, hh), (rr - wall, 0.017), (rr * 0.90 - wall, 0.0045),
           (0.0, 0.0045)]
    body = mlib.revolve(name + "_b", prf, 44, cname=cname)
    mlib.smooth_shade(body, 32)
    mlib.set_mat(body, M['copper'])
    parts.append(body)
    # A tinned lining reads as a pale bowl inside the copper shell and is most
    # of what tells you these are cooking pans - but the set has unlined ones
    # too, copper right through, and a rack of nothing but pale discs loses the
    # copper entirely.
    if lined:
        lin = mlib.revolve(name + "_l", [(0.0, 0.0052), (rr * 0.86, 0.0052),
                                         (rr - wall - 0.0008, 0.020),
                                         (rr - wall - 0.0008, hh - 0.0015)],
                           44, cname=cname, cap_start=False, cap_end=False)
        mlib.smooth_shade(lin, 42)
        mlib.set_mat(lin, M['tin'])
        parts.append(lin)
    # --- handle: a flat strap leaving the rim steeply and flattening off
    hz, N = hh * 0.70, 12
    b0, b1 = math.radians(46.0), math.radians(21.0)
    step = hl / N
    path = [(rr - 0.004, 0.0, hz)]
    for i in range(N):
        a = b0 + (b1 - b0) * ((i + 0.5) / N)
        x, _, z = path[-1]
        path.append((x + step * math.cos(a), 0.0, z + step * math.sin(a)))
    sec = mlib.rounded_rect(1.0, 1.0, 0.34, seg=3)
    rings = []
    for i, p in enumerate(path):
        t = i / N
        w = (0.036 - 0.013 * (t / 0.20) ** 0.6) if t < 0.20 else \
            (0.023 - 0.004 * (t - 0.20) / 0.80)
        th = 0.0050 - 0.0019 * t
        tg = Vector(path[min(i + 1, N)]) - Vector(path[max(i - 1, 0)])
        tg.normalize()
        nrm = Vector((-tg.z, 0.0, tg.x))
        rings.append([tuple(Vector(p) + Vector((0.0, 1.0, 0.0)) * (u * w)
                            + nrm * (v * th)) for (u, v) in sec])
    hd = mlib._loft(name + "_hd", rings, close_v=True, cname=cname,
                    cap_start=True, cap_end=True)
    mlib.smooth_shade(hd, 46)
    mlib.set_mat(hd, M['panhandle'])
    parts.append(hd)
    return parts, path[-1]


def _colander(name, rr, M, cname):
    """Perforated steel bowl with two riveted loop handles - the one bright
    silver thing in the copper huddle."""
    parts = []
    # 26 rings, comfortably finer than the 12 rows of holes: at one ring per row
    # the hole pattern beats against the mesh's own resolution
    NR = 26
    prf = [(0.0, 0.0)]
    for i in range(1, NR + 1):
        a = math.pi * 0.53 * i / NR
        prf.append((rr * math.sin(a), rr * 0.80 * (1.0 - math.cos(a))))
    # left single-sided on purpose: solidified, the inner shell would take its
    # own draw of the hole pattern and you would see a second, misaligned set of
    # holes through the first
    bowl = mlib.revolve(name + "_b", prf, 48, cname=cname,
                        cap_start=False, cap_end=False)
    # bake the parameterisation now, while the bowl is still upright about +Z
    cz0 = rr * 0.80
    top = rr * 0.80 * (1.0 - math.cos(math.pi * 0.53))

    def _q(co):
        g = math.hypot(co.x, co.y)
        psi = math.atan2(g, cz0 - co.z) / (math.pi * 0.53)
        if g < 1e-7:
            return (1.0, 0.5, psi)
        return (co.x / g * 0.5 + 0.5, co.y / g * 0.5 + 0.5, psi)

    mlib.bake_surface_attr(bowl, _q)
    mlib.smooth_shade(bowl, 55)
    mlib.set_mat(bowl, M['perf'])
    parts.append(bowl)
    rim = mlib.tube_along(name + "_rm",
                          [(rr * math.sin(math.pi * 0.53) * math.cos(a),
                            rr * math.sin(math.pi * 0.53) * math.sin(a), top)
                           for a in [i * math.tau / 48 for i in range(48)]],
                          mlib.circle(0.0032, 8), cname, close_path=True)
    mlib.smooth_shade(rim, 40)
    mlib.set_mat(rim, M['panhandle'])
    parts.append(rim)
    rw = rr * math.sin(math.pi * 0.53)
    eye = None
    for s in (1, -1):
        pts = []
        for i in range(13):
            t = i / 12.0
            ang = math.pi * t
            pts.append((s * (rw - 0.004 + 0.030 * math.sin(ang)), 0.0,
                        top + 0.052 * math.sin(ang) - 0.004 * math.cos(ang)))
        lp = mlib.tube_along(name + "_lp%d" % (s > 0), pts,
                             mlib.rounded_rect(0.0075, 0.0032, 0.0014, seg=2),
                             cname, up=(0, 1, 0))
        mlib.smooth_shade(lp, 40)
        mlib.set_mat(lp, M['panhandle'])
        parts.append(lp)
        if s > 0:
            eye = (s * (rw - 0.004 + 0.030), 0.0, top + 0.052)
    return parts, eye


def _s_hook(name, cname, hoop_hw=0.015, drop=0.062):
    """Thin wrought S-hook: the top curl bites over the hoop's upper edge, the
    lower one takes the handle.  Built in the XZ plane with the hoop centre-
    line at the origin; returns (object, lower-curl centre)."""
    r1, r2 = 0.0088, 0.0105
    c1 = (0.0, hoop_hw - r1 * 0.30)
    c2 = (0.0, c1[1] - drop)
    pts = []
    for k in range(15):                       # top curl, over the strap edge
        a = math.radians(205.0 - 250.0 * k / 14.0)
        pts.append((c1[0] + r1 * math.cos(a), 0.0, c1[1] + r1 * math.sin(a)))
    for k in range(1, 16):                    # lower curl, opening the other way
        a = math.radians(75.0 + 250.0 * k / 15.0)
        pts.append((c2[0] + r2 * math.cos(a), 0.0, c2[1] + r2 * math.sin(a)))
    ob = mlib.tube_along(name, pts, mlib.circle(0.0022, 7), cname, up=(0, 1, 0))
    mlib.smooth_shade(ob, 40)
    return ob, (c2[0], 0.0, c2[1] - r2)


def pot_rack(name, M, cname=C):
    """The wrought-iron dome over the peninsula.  Flat-strap hoop and ribs, and
    the pans hang off it by their handles the way pans do - disc dangling
    vertical, mouth turned sideways - not lying flat like a candle tray."""
    cx, cy, cz = 0.50, 1.02, 2.40
    R, DOME = 0.30, 0.285
    parts = []
    # bottom hoop: flat bar bent the hard way, so its face looks outward
    HW, HT = 0.030, 0.0052
    strap = [(-HT / 2, -HW / 2), (HT / 2, -HW / 2), (HT / 2, HW / 2),
             (-HT / 2, HW / 2)]
    parts.append(mlib.tube_along(
        name + "_h", [(R * math.cos(a), R * math.sin(a), 0.0)
                      for a in [i * math.tau / 72 for i in range(72)]],
        strap, cname, close_path=True))
    # eight meridional ribs, also flat strap, riveted proud of the hoop
    RW, RT = 0.020, 0.0044
    rib = [(-RT / 2, -RW / 2), (RT / 2, -RW / 2), (RT / 2, RW / 2),
           (-RT / 2, RW / 2)]
    R2 = R + (HT + RT) * 0.5
    for k in range(8):
        a = math.tau * k / 8
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for i in range(17):
            psi = math.radians(84.0) * i / 16.0
            rr = R2 * math.cos(psi)
            pts.append((rr * ca, rr * sa, DOME * math.sin(psi)))
        # up = the azimuthal direction, which is constant along one meridian:
        # the rib's tangent turns through 84 deg but never leaves this plane,
        # so the frame stays stable where a global up would flip at the pole
        parts.append(mlib.tube_along(name + "_r%d" % k, pts, rib, cname,
                                     up=(-sa, ca, 0.0)))
    parts.append(mlib.revolve(name + "_cap", [(0.0, DOME - 0.012),
                                              (0.030, DOME - 0.010),
                                              (0.030, DOME + 0.026),
                                              (0.0, DOME + 0.026)], 18,
                              cname=cname))
    parts.append(mlib.tube_along(name + "_ch", [(0, 0, DOME + 0.026),
                                                (0, 0, L.CZ - cz)],
                                 mlib.circle(0.006, 6), cname))
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 36)
    mlib.set_mat(ob, M['iron'])
    mlib.translate(ob, (cx, cy, cz))

    # --- the pans ------------------------------------------------------------
    # azimuths are clustered on the east and south arcs, facing the room, and
    # kept off the north one where the big shelf unit starts at y = 1.38
    # 'mouth' is the compass bearing the pan's opening ends up pointing, 0 being
    # due east into the room: a rack you only ever see the backs of looks like a
    # row of shields, so half of these are turned to show their tinned insides.
    # Handle length sets how far each pan falls, so they are staggered to keep
    # neighbouring discs from slicing through one another.
    specs = [   # az deg, radius, depth, handle, mouth deg, tin-lined
        (-104.0, 0.074, 0.046, 0.130, 30.0, True),
        (-64.0, 0.105, 0.055, 0.196, -32.0, False),
        (-24.0, 0.086, 0.056, 0.140, 118.0, True),
        (14.0, 0.108, 0.048, 0.201, -8.0, True),
        (52.0, 0.079, 0.051, 0.134, 156.0, False),
        (88.0, 0.096, 0.062, 0.178, 64.0, False),
    ]
    for i, (az, rr, hh, hl, mouth, lined) in enumerate(specs):
        a = math.radians(az)
        hook, low = _s_hook(name + "_hk%d" % i, cname, HW * 0.5)
        mlib.set_mat(hook, M['iron'])
        mlib.rotate_z(hook, a)
        mlib.translate(hook, (cx + R * math.cos(a), cy + R * math.sin(a), cz))
        pan, eye = _saucepan(name + "_p%d" % i, rr, hh, hl, M, cname, lined)
        hp = (cx + (R + low[0]) * math.cos(a), cy + (R + low[0]) * math.sin(a),
              cz + low[2])
        _hang(pan, eye, hh * 0.42, hp, math.radians(mouth - 180.0))
    # the colander, hung off its loop from the last hook
    az = math.radians(-140.0)
    hook, low = _s_hook(name + "_hkc", cname, HW * 0.5)
    mlib.set_mat(hook, M['iron'])
    mlib.rotate_z(hook, az)
    mlib.translate(hook, (cx + R * math.cos(az), cy + R * math.sin(az), cz))
    col, eye = _colander(name + "_col", 0.100, M, cname)
    _hang(col, eye, 0.100 * 0.34, (cx + (R + low[0]) * math.cos(az),
                                   cy + (R + low[0]) * math.sin(az),
                                   cz + low[2]), math.radians(-150.0 - 180.0))
    return ob


def _hang(parts, eye, com_z, hook_pt, face):
    """Swing a mouth-up vessel into the pose it actually takes when you hang it
    from `eye`: rotate about Y until the centre of mass sits plumb under the
    hook, then spin it about the vertical to aim the mouth."""
    ex, _, ez = eye
    phi = math.atan2(-ex, ez - com_z)
    for ob in parts:
        mlib.translate(ob, (-ex, 0.0, -ez))
        mlib.rot_y(ob, phi)
        mlib.rotate_z(ob, face)
        mlib.translate(ob, hook_pt)


def ceiling_dome(name, loc, M, cname=C, r=0.165, energy=300.0, kelvin=6000.0):
    """Plain opal schoolhouse dome on a short brass stem - the kitchen's
    overhead.  Like the living-room chandelier this is inference, not
    documented: see build_scripts/README.md.  It is the only thing in the room
    that could account for general light at ceiling height, and under this
    project's rule a light without such a thing is not allowed to exist."""
    import props as P
    parts = []
    brass = M.get('brass') or mats.metal('brass_fitting', 'A8813C', rough=0.32,
                                         bump=0.04)
    can = mlib.revolve(name + "_can", [(0.0, 0.0), (0.072, -0.006),
                                       (0.076, -0.022), (0.044, -0.038),
                                       (0.0, -0.042)], 20, cname=cname)
    mlib.set_mat(can, brass)
    parts.append(can)
    stem = mlib.revolve(name + "_stem", [(0.0, -0.038), (0.014, -0.038),
                                         (0.014, -0.150), (0.0, -0.150)], 12,
                        cname=cname)
    mlib.set_mat(stem, brass)
    parts.append(stem)
    gal = mlib.revolve(name + "_gal", [(0.0, -0.150), (0.052, -0.156),
                                       (0.058, -0.176), (0.040, -0.190),
                                       (0.0, -0.192)], 18, cname=cname)
    mlib.set_mat(gal, brass)
    parts.append(gal)
    # opal glass dome, open at the bottom
    prof = []
    for i in range(15):
        t = i / 14.0
        a = math.pi * 0.52 * t
        prof.append((r * math.sin(a) * 1.0, -0.176 - r * 0.86 * (1 - math.cos(a))))
    sh = mlib.revolve(name + "_sh", prof, 30, cname=cname, cap_start=False,
                      cap_end=False)
    mlib.solidify(sh, 0.005, offset=0)
    mlib.smooth_shade(sh, 46)
    mlib.set_mat(sh, mats.get('opal_shade') or
                 mats.emissive('opal_shade', 'FFF0D2', strength=2.2,
                               base='F6EEDC'))
    parts.append(sh)
    bl = P.bulb(name + "_bl", cname, e=30.0, r=0.026)
    mlib.translate(bl, (0, 0, -0.246))
    parts.append(bl)
    for o in parts:
        mlib.translate(o, loc)
    P.point_light(name + "_light", (loc[0], loc[1], loc[2] - 0.232), energy,
                  P.blackbody(kelvin), 0.10)
    return parts


def rattan_pendant(name, loc, M, cname=C, r=0.235, h=0.225, drop=1.05):
    parts = []
    # A flared bell with a hollow, concave waist - the set shade swells outward
    # towards an open bottom rim.  A straight cone read as a paper lampshade.
    prof = [(0.032, h), (0.046, h * 0.955), (0.062, h * 0.90),
            (0.079, h * 0.805), (0.098, h * 0.700), (0.117, h * 0.590),
            (0.136, h * 0.480), (0.153, h * 0.382), (0.170, h * 0.290),
            (0.187, h * 0.205), (0.202, h * 0.130), (0.220, h * 0.062),
            (r, 0.020), (r, 0.0)]
    # the weave has to be told where the shade's axis stands - see mats.wicker
    wk = mats.wicker('rattan_shade', light='CFAA6D', dark='8A6229', rings=46.0,
                     stakes=62.0, rough=0.60, bump=0.80,
                     centre=(loc[0], loc[1]))
    sh = mlib.revolve(name + "_sh", prof, 32, cname=cname, cap_start=False,
                      cap_end=False)
    mlib.solidify(sh, 0.008, offset=0)
    mlib.smooth_shade(sh, 46)
    mlib.set_mat(sh, wk)
    parts.append(sh)
    cord = mlib.tube_along(name + "_cd", [(0, 0, h), (0, 0, h + drop)],
                           mlib.circle(0.005, 6), cname)
    mlib.set_mat(cord, mats.paint('cord_black', '18181A', rough=0.5))
    parts.append(cord)
    cap = mlib.revolve(name + "_cp", [(0.0, h + drop - 0.03), (0.045, h + drop - 0.03),
                                      (0.045, h + drop), (0.0, h + drop)], 16,
                       cname=cname)
    mlib.set_mat(cap, mats.get('cord_black'))
    parts.append(cap)
    bulb = mlib.revolve(name + "_bl", [(0.0, 0.0), (0.028, 0.012), (0.032, 0.035),
                                       (0.024, 0.058), (0.011, 0.066),
                                       (0.011, 0.086), (0.0, 0.086)], 18, cname=cname)
    mlib.translate(bulb, (0, 0, h * 0.45))
    mlib.smooth_shade(bulb, 40)
    mlib.set_mat(bulb, mats.emissive('bulb_warm', 'FFE0AE', strength=46.0,
                                     base='FFF3E2'))
    parts.append(bulb)
    for ob in parts:
        mlib.translate(ob, loc)
    ld = bpy.data.lights.new(name + "_light", 'POINT')
    ld.energy = 32.0
    ld.color = (1.0, 0.82, 0.62)
    ld.shadow_soft_size = 0.06
    lo = bpy.data.objects.new(name + "_light", ld)
    mlib.put(lo, "Lighting")
    lo.location = (loc[0], loc[1], loc[2] + h * 0.42)
    return parts


def _place_chamfer(ob, ang, u, z, off=0.02):
    """Map an object built in local XZ (+Y = out of the wall) onto the chamfer:
    local +X -> chamfer direction, local +Y -> into the room."""
    (dxc, dyc), cl = L.chamfer_dir()
    ix, iy = dyc, -dxc
    p = L.chamfer_pt(u, off)
    M4 = Matrix(((dxc, ix, 0.0, p[0]), (dyc, iy, 0.0, p[1]),
                 (0.0, 0.0, 1.0, z), (0.0, 0.0, 0.0, 1.0)))
    ob.data.transform(M4)
    ob.data.update()
    mlib.recalc_normals(ob)
    return ob


# ------------------------------------------------------------------ build all
def build():
    M = mk_mats()
    (dxc, dyc), cl = L.chamfer_dir()

    # --- base runs -----------------------------------------------------------
    base_run("K_base_w", (0.0, L.KIT_CTR[0]), (0.0, L.KIT_CTR[1]), M,
             doors=1, drawers=1, dr_h=0.17)
    # chamfer run (sink)
    base_run("K_base_ch", L.chamfer_pt(0.0), L.chamfer_pt(cl), M, doors=2)
    # north run
    base_run("K_base_n", (L.N_BRICK[0], L.NY), (L.FRIDGE_X[0] - 0.02, L.NY), M,
             doors=2, drawers=1, dr_h=0.17, top_mat=M['block_n'])
    peninsula("K_peninsula", M)
    pro_range("K_range", M)
    double_sink("K_sink", M)
    fridge("K_fridge", M)

    # --- upper shelving ------------------------------------------------------
    shelf_unit("K_shelf", (0.0, L.KIT_SHELF[0]), (0.0, L.KIT_SHELF[1]),
               1.50, 2.42, 0.30, 4, M, bays=SHELF_BAYS, stagger=SHELF_TIERS)
    wedge_shelf("K_wedge", (0.0, L.KIT_WEDGE[0]), (0.0, L.KIT_WEDGE[1]),
                1.54, 0.19, M)
    # celadon wall cabinet above the fridge
    cc = mlib.box("K_celadon", L.FRIDGE_X[0] + 0.02, L.NY - 0.36, 1.86,
                  L.FRIDGE_X[1] + 0.04, L.NY - 0.012, 2.54, C)
    mlib.bevel(cc, 0.004, 2, 45)
    mlib.set_mat(cc, M['celadon'])
    for i in range(2):
        d = slab_door("K_cel_d%d" % i, (L.FRIDGE_X[1] - L.FRIDGE_X[0]) / 2 - 0.012,
                      0.64, 0.018, C, M['celadon'], rail=0.055)
        mlib.rotate_z(d, 0) if False else None
        mlib.translate(d, (0, 0, 0))
        mlib.rotate_z(d, math.pi)
        mlib.translate(d, (L.FRIDGE_X[0] + 0.04 + (i + 0.5) *
                           ((L.FRIDGE_X[1] - L.FRIDGE_X[0]) / 2), L.NY - 0.375, 1.88))
    # small paper-towel shelf under the big shelf unit
    pts = mlib.box("K_ptshelf", 0.0, L.KIT_WEDGE[0], 1.34, 0.19, L.KIT_WEDGE[1],
                   1.36, C)
    mlib.set_mat(pts, mats.wood('wood_shelf_small', ('D9B47C', 'B08148', '7A5220'),
                                ring=26, warp=0.5, bump=0.3, axis='X'))
    pot_rack("K_potrack", M)
    rattan_pendant("K_pendant", (0.62, 3.28, 1.96), M)
    # kitchen overhead - the room's own key light, clear of the pot rack, the
    # shelf unit and the pendant, roughly over the middle of the working floor
    ceiling_dome("K_ceiling", (1.62, 2.02, L.CZ), M, energy=300.0, kelvin=6000.0)
    dress(M)
    print("kitchen built")
    return M


# ------------------------------------------------------------------- dressing
def dress(M):
    import props as P
    pool = P.palette(4, 24)
    z0, z1, t = 1.50, 2.42, 0.024
    zb = z0 + t * 1.4
    inner = (z1 - t * 1.4) - zb
    y0, y1 = L.KIT_SHELF
    # fill each cubby on its own so nothing straddles a divider
    edges = [y0 + (y1 - y0) * k / SHELF_BAYS for k in range(SHELF_BAYS + 1)]
    n = 0
    for k in range(SHELF_BAYS):
        nt = SHELF_TIERS[k % len(SHELF_TIERS)]
        for i in range(nt):
            zz = zb + inner * i / nt + t / 2
            # Tier 0 is the bottom.  The set's shelves are loaded from the
            # bottom up: the reachable tiers are jammed and the top two are
            # mostly bare brick with a teapot or a bowl pushed to one end.
            frac = i / max(1, nt - 1)
            P.fill_shelf("K_sf%d" % n, (0.02, edges[k] + 0.055),
                         (0.02, edges[k + 1] - 0.055), zz, 0.28, seed=100 + n,
                         cname=C, maxh=inner / nt - 0.045, mats_pool=pool,
                         back=0.55, fill=1.0 - 0.52 * frac ** 1.5)
            n += 1
    # bottle shelf over the range
    P.fill_shelf("K_wf", (0.02, L.KIT_WEDGE[0] + 0.03),
                 (0.02, L.KIT_WEDGE[1] - 0.03), 1.566, 0.17, seed=77, cname=C,
                 maxh=0.30, mats_pool=pool, back=0.5)
    # peninsula shelves
    for i, zz in enumerate((0.224, 0.464, 0.704)):
        P.fill_shelf("K_pf%d" % i, (0.05, L.KIT_PEN[0] + 0.05),
                     (0.05, L.KIT_PEN[1] - 0.05), zz, 0.30, seed=40 + i,
                     cname=C, maxh=0.20, mats_pool=pool, back=0.5)
    # counter dressing on the north run
    P.fill_shelf("K_cn", (L.N_BRICK[0] + 0.10, L.NY - 0.001),
                 (L.FRIDGE_X[0] - 0.14, L.NY - 0.001), CTR_H, 0.62, seed=9,
                 cname=C, maxh=0.30, mats_pool=pool, back=0.34)
    # counter dressing on the west run
    P.fill_shelf("K_cw", (0.001, L.KIT_CTR[0] + 0.08),
                 (0.001, L.KIT_CTR[1] - 0.06), CTR_H, 0.62, seed=13,
                 cname=C, maxh=0.30, mats_pool=pool, back=0.34)
    # yellow floral swag + tails over the kitchen window
    chintz = mats.floral_chintz('chintz_yellow', ground='DCA412', petal='B81C55',
                                petal2='DE6389', leaf='1E4E33', leaf2='5F8C44',
                                scale=2.3)
    (dxc, dyc), cl = L.chamfer_dir()
    ang = math.atan2(dyc, dxc)
    u0, u1 = L.KW_U[0] - 0.06, L.KW_U[1] + 0.06
    zt = L.KW_Z[1] + 0.10
    sw = P.swag("K_swag", -(u1 - u0) / 2, (u1 - u0) / 2, 0.0, sag=0.30,
                depth=0.13, folds=5, cname=C, mat=chintz)
    for k in range(2):
        j = P.jabot("K_jab%d" % k, (-1 if k == 0 else 1) * ((u1 - u0) / 2 - 0.01),
                    0.02, ln=1.18, w=0.17, depth=0.12,
                    side=(-1 if k == 0 else 1), cname=C, mat=chintz)
        _place_chamfer(j, ang, (u0 + u1) / 2, zt)
    _place_chamfer(sw, ang, (u0 + u1) / 2, zt)
    # little café skirt under the sink cabinet
    sk = P.curtain_panel("K_skirt", -(u1 - u0) / 2 + 0.06, (u1 - u0) / 2 - 0.06,
                         0.0, -0.42, depth=0.05, folds=11, cname=C, mat=chintz,
                         gather=0.8, flare=1.0, seed=19, fullness=2.6)
    _place_chamfer(sk, ang, (u0 + u1) / 2, CTR_H - 0.05)
    # framed botanical prints on the north brick
    gold = mats.paint('paint_gilt', 'C9A24A', rough=0.30, coat=0.4)
    for i, (xx, zz, w, h) in enumerate(((1.42, 1.98, 0.27, 0.33),
                                        (1.98, 1.86, 0.24, 0.30))):
        P.framed("K_art%d" % i, w, h, (xx, L.NY - 0.02, zz), (0, -1), C,
                 framemat=gold,
                 artmat=mats.botanical('art_botanical_%d' % i, normal=(0, -1),
                                       seed=47 + i * 7, ground='E5DCBE',
                                       stem='55642E', leafc=('445A28', '7A8A4C'),
                                       bloom=('A85E30', 'D9A867')))
    # wrought-iron ornament + coat hooks beside the front door
    hk = []
    rail = mlib.box("K_hookrail", 0.004, 1.30, 1.62, 0.026, 1.34, 1.70, C)
    hk.append(rail)
    for yy in (1.305, 1.318, 1.331):
        pts = [(0.020, yy, 1.655), (0.055, yy, 1.650), (0.062, yy, 1.628),
               (0.048, yy, 1.618)]
        hk.append(mlib.tube_along("K_hook", pts, mlib.circle(0.0045, 6), C))
    ob = mlib.join(hk, "K_hooks", C)
    mlib.set_mat(ob, M['iron'])
