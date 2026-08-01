"""Doors, windows, casings, sashes, glazing, hardware.

Real joinery: linings inside the reveal, mitred architraves proud of the
plaster, stile-and-rail doors with panels housed behind the frame (so no
coincident faces), steel windows with glass sitting in a rabbet behind the
muntins.
"""
import bpy, math
from mathutils import Vector, Matrix
import mlib, mats, L

# ------------------------------------------------------------------ transform


def place(ob, origin, xdir, ydir=None):
    """Map local (x,y,z) so local +X -> xdir (2D), +Y -> ydir, +Z -> up."""
    ux, uy = xdir
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    if ydir is None:
        vx, vy = -uy, ux
    else:
        vx, vy = ydir
        n2 = math.hypot(vx, vy)
        vx, vy = vx / n2, vy / n2
    M = Matrix(((ux, vx, 0.0, origin[0]),
                (uy, vy, 0.0, origin[1]),
                (0.0, 0.0, 1.0, origin[2]),
                (0.0, 0.0, 0.0, 1.0)))
    ob.data.transform(M)
    ob.data.update()
    mlib.recalc_normals(ob)
    return ob


# --------------------------------------------------------------------- casings

def casing_profile(cw=0.095, proud=0.024):
    h = cw * 0.5
    return [(-h, 0.0012), (-h, proud * 1.10), (-h + 0.008, proud * 1.30),
            (-h + 0.017, proud * 1.30), (-h + 0.023, proud * 0.88),
            (h - 0.020, proud * 0.72), (h - 0.014, proud * 0.98),
            (h - 0.004, proud * 0.98), (h, proud * 0.55), (h, 0.0012)]


def casing(name, w, h, cw=0.095, proud=0.024, cname="Openings", mat=None,
           sides=3, prof=None):
    """Mitred architrave around an opening of clear size w x h whose bottom
    sits at local z = 0.  Built in the XZ plane, +Y proud into the room.
    sides=3 -> two legs and a head (no threshold)."""
    p = prof or casing_profile(cw, proud)
    hw = w * 0.5 + cw * 0.5
    r2 = math.sqrt(2.0)
    if sides == 4:
        ob = mlib.sweep_rect_frame(name, w + cw, h + cw, p, cname)
        ob.data.transform(Matrix.Translation((0, 0, h * 0.5)))
        mlib.recalc_normals(ob)
    else:
        top = h + cw * 0.5
        corners = [(-hw, 0.0, (-1.0, 0.0), 1.0),
                   (-hw, top, (-0.70711, 0.70711), r2),
                   (hw, top, (0.70711, 0.70711), r2),
                   (hw, 0.0, (1.0, 0.0), 1.0)]
        rings = []
        for (cx, cz, (ox, oz), sc) in corners:
            rings.append([(cx + ox * a * sc, b, cz + oz * a * sc) for (a, b) in p])
        ob = mlib._loft(name, rings, close_u=False, close_v=True, cname=cname,
                        cap_start=True, cap_end=True)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def lining(name, w, h, depth, t=0.026, cname="Openings", mat=None):
    """Box lining inside a reveal: two jambs + head, set flush with the reveal."""
    parts = []
    parts.append(mlib.box(name + "_jl", -w / 2, 0.0, 0.0, -w / 2 + t, depth, h, cname))
    parts.append(mlib.box(name + "_jr", w / 2 - t, 0.0, 0.0, w / 2, depth, h, cname))
    parts.append(mlib.box(name + "_hd", -w / 2, 0.0, h - t, w / 2, depth, h, cname))
    ob = mlib.join(parts, name, cname)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


# ----------------------------------------------------------------------- doors

def flush_door(name, w, h, t=0.042, cname="Openings", mat=None):
    ob = mlib.box(name, -w / 2, 0.0, 0.0, w / 2, t, h, cname)
    mlib.bevel(ob, 0.003, 2, 40)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def panel_door(name, w, h, t=0.042, rows=(0.30, 0.30, 0.20, 0.20), stile=0.115,
               rail=0.115, mid=0.085, cname="Openings", mat=None):
    """Stile-and-rail door.  Panels are housed *behind* the frame so that no
    two faces are coincident."""
    tot = sum(rows)
    inner_h = h - 2 * rail - (len(rows) - 1) * mid
    holes = []
    z = rail
    for r in rows:
        hh = inner_h * (r / tot)
        holes.append((stile, z, w - stile, z + hh))
        z += hh + mid
    frame = mlib.panel_with_holes(name + "_frame", w, h, t, holes, cname)
    frame.data.transform(Matrix.Translation((-w / 2, 0, 0)))
    parts = [frame]
    for i, (x0, z0, x1, z1) in enumerate(holes):
        pw, ph = (x1 - x0) + 0.028, (z1 - z0) + 0.028
        pt = 0.016
        pan = mlib.box(name + "_p%d" % i, x0 - 0.014 - w / 2, t * 0.34,
                       z0 - 0.014, x1 + 0.014 - w / 2, t * 0.34 + pt, z1 + 0.014, cname)
        mlib.bevel(pan, 0.004, 2, 40)
        parts.append(pan)
        # sticking (bead) around the opening, front face
        bd = mlib.sweep_rect_frame(
            name + "_b%d" % i, (x1 - x0) + 0.013, (z1 - z0) + 0.013,
            [(-0.0075, 0.0006), (0.0075, 0.0006), (0.0075, 0.0075),
             (0.0020, 0.0115), (-0.0075, 0.0100)], cname)
        bd.data.transform(Matrix.Translation(((x0 + x1) / 2 - w / 2, 0.0, (z0 + z1) / 2)))
        mlib.recalc_normals(bd)
        parts.append(bd)
    ob = mlib.join(parts, name, cname)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


# --------------------------------------------------------------------- windows

def steel_window(name, w, h, bays, rows, frame_w=0.052, frame_d=0.062,
                 mull_w=0.040, mun_w=0.020, mun_d=0.026, cname="Openings",
                 mat=None, glass=None, cols_per_bay=2, glass_back=0.012):
    """Multi-pane steel/timber window.  Local: XZ plane centred at (0, *, h/2),
    +Y into the room.  bays = list of relative widths."""
    parts = []
    hw, hh = w / 2, h / 2
    # outer frame
    fp = [(-frame_w / 2, 0.0), (frame_w / 2, 0.0),
          (frame_w / 2, frame_d), (-frame_w / 2, frame_d)]
    of = mlib.sweep_rect_frame(name + "_of", w - frame_w, h - frame_w, fp, cname)
    of.data.transform(Matrix.Translation((0, 0, hh)))
    parts.append(of)
    tot = sum(bays)
    xs = [-hw]
    acc = 0.0
    for bb in bays:
        acc += bb
        xs.append(-hw + w * acc / tot)
    # mullions between bays
    for x in xs[1:-1]:
        parts.append(mlib.box(name + "_mu", x - mull_w / 2, 0.0, frame_w,
                              x + mull_w / 2, frame_d, h - frame_w, cname))
    # muntins inside each bay
    for k in range(len(bays)):
        x0 = xs[k] + (frame_w if k == 0 else mull_w / 2)
        x1 = xs[k + 1] - (frame_w if k == len(bays) - 1 else mull_w / 2)
        bw = x1 - x0
        for c in range(1, cols_per_bay):
            xc = x0 + bw * c / cols_per_bay
            parts.append(mlib.box(name + "_v", xc - mun_w / 2, 0.0, frame_w,
                                  xc + mun_w / 2, mun_d, h - frame_w, cname))
        for r in range(1, rows):
            zc = frame_w + (h - 2 * frame_w) * r / rows
            parts.append(mlib.box(name + "_hz", x0, 0.0, zc - mun_w / 2,
                                  x1, mun_d, zc + mun_w / 2, cname))
    fr = mlib.join(parts, name, cname)
    mlib.bevel(fr, 0.0022, 2, 40)
    if mat:
        mlib.set_mat(fr, mat)
    gl = mlib.box(name + "_glass", -hw + frame_w * 0.4, -glass_back - 0.004, frame_w * 0.4,
                  hw - frame_w * 0.4, -glass_back, h - frame_w * 0.4, cname)
    if glass:
        mlib.set_mat(gl, glass)
    return fr, gl


# ------------------------------------------------------------------- hardware

def knob_set(name, cname="Openings", mat=None):
    """Brass knob on a rectangular back plate; axis along +Y."""
    parts = []
    plate = mlib.prism(name + "_pl", mlib.rounded_rect(0.048, 0.135, 0.012, 4),
                       0.0, 0.005, cname)
    mlib.rot_x(plate, -math.pi / 2)
    parts.append(plate)
    prof = [(0.000, 0.004), (0.014, 0.006), (0.017, 0.014), (0.011, 0.021),
            (0.014, 0.026), (0.027, 0.035), (0.031, 0.047), (0.024, 0.057),
            (0.013, 0.063), (0.000, 0.065)]
    kn = mlib.revolve(name + "_kn", prof, 24, cname=cname)
    mlib.rot_x(kn, -math.pi / 2)
    parts.append(kn)
    kh = mlib.prism(name + "_kh", mlib.rounded_rect(0.011, 0.024, 0.004, 3),
                    0.0, 0.006, cname)
    mlib.rot_x(kh, -math.pi / 2)
    mlib.translate(kh, (0, 0, -0.040))
    parts.append(kh)
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 34)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def ornate_frame(name, w=0.175, h=0.195, cname="Openings", mat=None,
                 prof=None, bulge=0.014, crest=0.006, rr=0.040):
    """Rococo-ish moulded frame: rounded-rectangle loop whose radius bulges at
    the corners and crests at the edge centres."""
    base = mlib.rounded_rect(w, h, rr, seg=9)
    path = []
    for (x, z) in base:
        th = math.atan2(z / max(1e-6, h), x / max(1e-6, w))
        c4 = math.cos(4 * th)
        d = bulge * ((1 - c4) * 0.5) ** 1.4 + crest * ((1 + c4) * 0.5) ** 7.0
        r = math.hypot(x, z)
        if r < 1e-6:
            path.append((x, z))
        else:
            path.append((x + x / r * d, z + z / r * d))
    p = prof or [(-0.017, 0.0015), (-0.017, 0.0075), (-0.0140, 0.0165),
                 (-0.0065, 0.0225), (0.0035, 0.0235), (0.0110, 0.0190),
                 (0.0155, 0.0100), (0.0170, 0.0040), (0.0170, 0.0015)]
    ob = mlib.sweep_planar_loop(name, path, p, cname)
    mlib.smooth_shade(ob, 42)
    if mat:
        mlib.set_mat(ob, mat)
    return ob
