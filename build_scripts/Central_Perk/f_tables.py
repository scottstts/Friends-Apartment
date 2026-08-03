"""Tables.

Two families.  The little round ones are cast-iron pub bases with a turned
baluster and a scalloped foot - they are revolves, and the whole job is
getting the profile right.  The coffee table in front of the couch is the
opposite: a slab of reclaimed pine on turned bobbin legs, where the plank
joints and the end-grain are the point.
"""
import bpy, math, importlib
import mlib as M
import mats as T
import L

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C = "Furniture"
TAU = math.tau
MAT = {}


def mats():
    if MAT:
        return MAT
    MAT['iron'] = T.iron('table_iron', '1C1E1C', rough=0.46)
    MAT['pine'] = T.wood('table_pine', light='C9A971', dark='8A7444',
                         ring=18.0, scale=0.55, rough=(0.40, 0.62))
    MAT['pine_g'] = T.wood('table_pine_green', light='C6A96E', dark='8A7A48',
                           ring=16.0, scale=0.5, rough=(0.44, 0.66))
    MAT['walnut'] = T.wood('table_walnut', light='6E4826', dark='2A1608',
                           ring=28.0, scale=1.0)
    MAT['mahog'] = T.wood('table_mahog', light='7A3A22', dark='34160C',
                          ring=32.0, scale=0.9)
    return MAT


# ------------------------------------------------------------- cast-iron base

def iron_base(name, h=0.70, foot=0.21, cname=C):
    """The pub-table pedestal: scalloped foot, knopped baluster, spider top.

    The scallop is done by squeezing the revolve's radius with a cosine of
    the sweep angle rather than by unioning feet onto a disc - a union there
    leaves interior faces at every joint."""
    prof = [(0.0, 0.0), (foot, 0.0), (foot * 0.97, 0.020),
            (foot * 0.72, 0.036), (foot * 0.55, 0.055), (foot * 0.42, 0.058),
            (0.070, 0.085), (0.058, 0.105), (0.070, 0.120),
            (0.052, 0.150), (0.044, 0.200),
            (0.062, 0.240), (0.070, 0.268), (0.058, 0.300),
            (0.036, 0.360), (0.031, h - 0.170),
            (0.044, h - 0.130), (0.038, h - 0.105),
            (0.030, h - 0.070), (0.105, h - 0.030), (0.112, h - 0.014),
            (0.0, h - 0.012)]
    seg = 48
    rings = []
    for s in range(seg):
        a = TAU * s / seg
        # four lobes, only near the floor where the foot is
        lobe = 1.0 + 0.30 * math.cos(4 * a)
        ring = []
        for (r, z) in prof:
            k = lobe if z < 0.075 and r > 0.09 else 1.0
            ring.append((r * k * math.cos(a), r * k * math.sin(a), z))
        rings.append(ring)
    ob = M._loft(name, rings, close_u=True, close_v=False, cname=cname,
                 weld_poles=True, cap_start=True, cap_end=True)
    M.smooth_shade(ob, 38)
    M.set_mat(ob, mats()['iron'])
    return ob


def ped_table(name, cx, cy, r=0.34, h=0.735, cname=C, top='walnut',
              thick=0.036):
    """Round pedestal table.  The top is a real slab with a moulded edge, so
    it catches a line of light where it overhangs the base."""
    m = mats()
    base = iron_base(name + "_base", h=h - thick, cname=cname)
    tp = M.revolve(name + "_top",
                   [(0.0, 0.0), (r - 0.014, 0.0), (r - 0.004, 0.006),
                    (r, 0.016), (r - 0.003, thick - 0.008),
                    (r - 0.012, thick), (0.0, thick)],
                   segments=44, cname=cname)
    M.smooth_shade(tp, 36)
    M.translate(tp, (0.0, 0.0, h - thick))
    M.set_mat(tp, m[top])
    for o in (base, tp):
        M.translate(o, (cx, cy, 0.0))
    return [base, tp]


# ------------------------------------------------------------- coffee table

def turned_leg(name, h, r=0.048, cname=C, style='bobbin'):
    """A turned leg.  The bobbin profile is the one on the coffee table in
    front of the couch: a square block at the top, then three swelling beads
    down to a small foot."""
    if style == 'bobbin':
        prof = [(0.0, 0.0), (r * 0.70, 0.0), (r * 0.62, 0.016),
                (r * 0.40, 0.030), (r * 0.52, 0.048), (r * 0.86, 0.090),
                (r * 0.94, 0.128), (r * 0.62, 0.168), (r * 0.50, 0.186),
                (r * 0.68, 0.206), (r * 0.98, 0.250), (r * 1.02, 0.292),
                (r * 0.66, 0.336), (r * 0.52, 0.356), (r * 0.70, 0.378),
                (r * 0.96, 0.420), (r * 0.92, h - 0.075),
                (r * 0.72, h - 0.070), (r * 0.78, h - 0.060)]
    else:
        prof = [(0.0, 0.0), (r * 0.75, 0.0), (r * 0.70, 0.020),
                (r * 0.45, 0.055), (r * 0.85, 0.115), (r * 0.72, 0.180),
                (r * 0.56, h * 0.62), (r * 0.70, h - 0.090),
                (r * 0.80, h - 0.070)]
    prof = [p for p in prof if p[1] <= h]
    prof.append((r * 1.02, h - 0.060))
    prof.append((r * 1.02, h))
    prof.append((0.0, h))
    ob = M.revolve(name, prof, segments=22, cname=cname)
    M.smooth_shade(ob, 40)
    return ob


def plank_top(name, w, d, t, nplank=4, cname=C, gap=0.004, z=0.0):
    """A tabletop made of separate boards.  They are separate objects joined
    at the end, with a real gap between them - a single slab with a groove
    texture reads as printed."""
    out = []
    pitch = d / nplank
    for i in range(nplank):
        y0 = -d / 2 + i * pitch + gap * 0.5
        y1 = -d / 2 + (i + 1) * pitch - gap * 0.5
        # each board cups very slightly, as sawn boards do
        cup = 0.0016 * (1 if i % 2 else -1)
        b = M.box(name + "_p%d" % i, -w / 2, y0, z, w / 2, y1, z + t, cname)
        M.bevel(b, 0.0035, 2, 55)
        M.translate(b, (0.0, 0.0, cup))
        out.append(b)
    return out


def coffee_table(name, cx, cy, w=1.57, d=0.88, h=0.44, cname=C):
    """The pine table in front of the couch: four boards on a chunky apron,
    turned bobbin legs, a lower shelf stretcher."""
    m = mats()
    parts = []
    t = 0.052
    parts += plank_top(name, w, d, t, nplank=4, cname=cname, z=h - t)
    # apron, set in from the top's edge
    ax, ay = w / 2 - 0.075, d / 2 - 0.075
    for (p0, p1) in (((-ax, -ay), (ax, -ay)), ((-ax, ay), (ax, ay)),
                     ((-ax, -ay), (-ax, ay)), ((ax, -ay), (ax, ay))):
        r = M.tube_along(name + "_ap%.2f%.2f" % (p0[0], p0[1]),
                         [(p0[0], p0[1], h - t - 0.055),
                          (p1[0], p1[1], h - t - 0.055)],
                         M.rounded_rect(0.026, 0.090, 0.006, seg=2),
                         cname=cname, up=(0, 0, 1), cap=True)
        parts.append(r)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lg = turned_leg(name + "_lg%d%d" % (sx, sy), h - t, r=0.050,
                            cname=cname)
            M.translate(lg, (sx * ax, sy * ay, 0.0))
            parts.append(lg)
    # lower stretcher shelf
    for sy in (-1, 1):
        st = M.tube_along(name + "_st%d" % sy,
                          [(-ax, sy * ay, 0.145), (ax, sy * ay, 0.145)],
                          M.rounded_rect(0.030, 0.048, 0.006, seg=2),
                          cname=cname, up=(0, 0, 1), cap=True)
        parts.append(st)
    st2 = M.tube_along(name + "_stc", [(0.0, -ay, 0.145), (0.0, ay, 0.145)],
                       M.rounded_rect(0.030, 0.048, 0.006, seg=2),
                       cname=cname, up=(0, 0, 1), cap=True)
    parts.append(st2)
    ob = M.join(parts, name, cname)
    M.set_mat(ob, m['pine_g'])
    M.translate(ob, (cx, cy, 0.0))
    return [ob]


def low_table(name, cx, cy, w, d, h=0.42, cname=C, wood='walnut', rot=0.0,
              oval=False):
    """The oval/rectangular low tables in the alcoves: a moulded top on four
    turned legs with a shaped rail."""
    m = mats()
    parts = []
    t = 0.034
    if oval:
        pts = [(w * 0.5 * math.cos(a), d * 0.5 * math.sin(a))
               for a in [i * TAU / 44 for i in range(44)]]
    else:
        pts = M.rounded_rect(w, d, 0.055, seg=5)
    rings = []
    for (o, dz) in ((-0.010, 0.0), (0.0, 0.008), (0.002, t - 0.008),
                    (-0.010, t)):
        p = M.poly_offset(pts, o)
        rings.append([(x, y, h - t + dz) for (x, y) in p])
    top = M._loft(name + "_top", rings, close_u=False, close_v=True,
                  cname=cname, cap_start=True, cap_end=True)
    M.smooth_shade(top, 34); parts.append(top)
    ax, ay = w / 2 - 0.11, d / 2 - 0.085
    for sx in (-1, 1):
        for sy in (-1, 1):
            lg = turned_leg(name + "_lg%d%d" % (sx, sy), h - t, r=0.040,
                            cname=cname, style='taper')
            M.translate(lg, (sx * ax, sy * ay, 0.0))
            parts.append(lg)
    for (p0, p1) in (((-ax, -ay), (ax, -ay)), ((-ax, ay), (ax, ay))):
        r = M.tube_along(name + "_r%.2f" % p0[1],
                         [(p0[0], p0[1], h - t - 0.045),
                          (p1[0], p1[1], h - t - 0.045)],
                         M.rounded_rect(0.022, 0.060, 0.005, seg=2),
                         cname=cname, up=(0, 0, 1), cap=True)
        parts.append(r)
    ob = M.join(parts, name, cname)
    M.set_mat(ob, m[wood])
    if rot:
        M.rotate_z(ob, math.radians(rot))
    M.translate(ob, (cx, cy, 0.0))
    return [ob]
