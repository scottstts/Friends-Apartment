"""Door and window joinery.

The set's interior doors are all one pattern: a five-panel door with the panels
laid HORIZONTALLY, which is unusual enough that it is the most identifiable
piece of trim in the flat - it carries living_room.webp, kitchen.jpg and every
corridor shot.  The rail proportions matter more here than almost anything else
at this scale, because the eye reads a door before it reads a wall.

Everything is built flat in its own frame - x along the opening, z up, y from
the room face INTO the wall - and then mapped onto a wall line by
s_walls.to_wall(out=True).  Trim that has to stand proud of the inner face is
given negative y, which lands it back in the room.
"""
import bpy, math
from mathutils import Vector
import mlib, mats, L
from s_walls import to_wall, casing_profile


# ---------------------------------------------------------------- door leaf

def raised_panel(name, x0, z0, x1, z1, y0, y1, inset=0.032, proud=0.008,
                 cname="Openings"):
    """A recessed board with a raised field standing proud of it on both faces.
    Two solids joined and bevelled: the chamfer round the field is the bevel,
    which is both cleaner and truer than a lofted fake of one."""
    board = mlib.box(name, x0, y0, z0, x1, y1, z1, cname)
    field = mlib.box(name + "_f", x0 + inset, y0 - proud, z0 + inset,
                     x1 - inset, y1 + proud, z1 - inset, cname)
    ob = mlib.join([board, field], name, cname)
    mlib.bevel(ob, proud * 0.9, 3, 34)
    return ob


def panel_door(name, w, h, th=0.042, panels=5, cname="Openings",
               stile=0.112, top_rail=0.108, bot_rail=0.216, mid_rail=0.080,
               sink=0.010):
    """A five-panel leaf, panels horizontal, built as stiles, rails and panels
    rather than booleaned out of a slab - so it is manifold by construction and
    every joint throws its own shadow line."""
    inner_h = h - top_rail - bot_rail - mid_rail * (panels - 1)
    shares = [1.0] * (panels - 1) + [1.36]      # the top panel is the tall one
    tot = sum(shares)
    hs = [inner_h * s / tot for s in shares]

    parts = []
    x0, x1 = stile, w - stile
    parts.append(mlib.box(name + "_sl", 0, 0, 0, stile, th, h, cname))
    parts.append(mlib.box(name + "_sr", w - stile, 0, 0, w, th, h, cname))
    parts.append(mlib.box(name + "_rb", x0, 0, 0, x1, th, bot_rail, cname))
    parts.append(mlib.box(name + "_rt", x0, 0, h - top_rail, x1, th, h, cname))

    z = bot_rail
    for i, ph in enumerate(hs):
        parts.append(raised_panel(name + "_p%d" % i, x0 - 0.006, z,
                                  x1 + 0.006, z + ph, sink, th - sink, cname=cname))
        z += ph
        if i < panels - 1:
            parts.append(mlib.box(name + "_rm%d" % i, x0, 0, z, x1, th,
                                  z + mid_rail, cname))
            z += mid_rail
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.0018, 2, 44)
    return ob


def door_hardware(name, w, th, hinge_left=True, cname="Openings", z=1.02):
    """Knob, rose and a strike-side escutcheon, on both faces."""
    parts = []
    kx = w - 0.085 if hinge_left else 0.085
    for y, d in ((0.0, -1.0), (th, 1.0)):
        rose = mlib.revolve(name + "_r%d" % (d > 0),
                            [(0.0, 0.0), (0.031, 0.0), (0.033, 0.006),
                             (0.030, 0.011), (0.0, 0.012)], segments=24, cname=cname)
        knob = mlib.revolve(name + "_k%d" % (d > 0),
                            [(0.0, 0.011), (0.011, 0.013), (0.012, 0.031),
                             (0.021, 0.046), (0.026, 0.063), (0.022, 0.077),
                             (0.012, 0.084), (0.0, 0.086)], segments=24, cname=cname)
        mlib.smooth_shade(knob, 42)
        for o in (rose, knob):
            mlib.rot_x(o, math.pi / 2 * (1 if d > 0 else -1))
            mlib.translate(o, (kx, y, z))
            parts.append(o)
    # No escutcheon plate.  A 48 x 72 brass rectangle 5 mm proud below the knob
    # is not deep enough to catch a highlight, so it reads as a flat brown
    # sticker stuck on the door - which is exactly what it looked like.  These
    # doors take a tubular knob set, which has nothing under the rose.
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.0012, 2, 40)
    return ob


def hinges(name, h, th, x, cname="Openings"):
    parts = [mlib.box(name + "_h%.2f" % z, x - 0.004, -0.006, z - 0.048,
                      x + 0.004, th + 0.006, z + 0.048, cname)
             for z in (0.26, h * 0.52, h - 0.24)]
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.0015, 2, 40)
    return ob


def casing(name, w, h, cname="Openings", cw=0.115, cd=0.021, reveal=0.006,
           cut_below=None):
    """Architrave: one mitred loop standing proud of the wall face, with the
    bottom run cut away for a door (there is no casing across a threshold).
    Mitred as a loop rather than butted as three runs, because a butt joint at
    the head is visible from every angle in the room."""
    ob = mlib.sweep_rect_frame(name, w + reveal * 2, h + reveal * 2,
                               casing_profile(cw, cd), cname=cname,
                               center=(w * 0.5, h * 0.5))
    if cut_below is not None:
        cut = mlib.box(name + "_c", -1.0, -0.35, cut_below - 2.4,
                       w + 1.0, 0.45, cut_below, cname)
        mlib.boolean(ob, cut)
    mlib.bevel(ob, 0.0015, 2, 40)
    return ob


def _both_casings(name, w, h, wall_th, cname, cut_below=None, cw=0.115, cd=0.021):
    """Casing on both faces.  The room-side copy is mirrored into negative y so
    it stands proud of the inner face; the far-side copy is pushed out past the
    wall's back face."""
    a = casing(name + "_a", w, h, cname, cw=cw, cd=cd, cut_below=cut_below)
    mlib.scale_mesh(a, (1, -1, 1))
    b = casing(name + "_b", w, h, cname, cw=cw, cd=cd, cut_below=cut_below)
    mlib.translate(b, (0, wall_th, 0))
    return mlib.join([a, b], name, cname)


def make_door(name, p0, p1, u0, w, h, th=0.042, swing=0.0, hinge_left=True,
              cname="Openings", wall_th=None, knob=True, mats_=None):
    """A complete doorway on the wall p0 -> p1: lining in the reveal, casing
    proud of both faces, and a leaf hung at `swing` radians (0 = shut)."""
    wall_th = L.TW if wall_th is None else wall_th
    out = {}
    # Held 4 mm back from the wall's OUTER face.  Run flush, the lining's end
    # face is coplanar with the wall's outer face and pointing the same way -
    # a z-fight on the far side of every opening.  The outer casing covers the
    # recess completely.
    lt = wall_th - 0.004
    lin = [mlib.box(name + "_lj%.2f" % a, u0 + a, 0.0, 0.0, u0 + b, lt, h, cname)
           for (a, b) in ((0.0, 0.022), (w - 0.022, w))]
    lin.append(mlib.box(name + "_lh", u0, 0.0, h - 0.022, u0 + w, lt, h, cname))
    lining = mlib.join(lin, name + "_lining", cname)
    mlib.bevel(lining, 0.002, 2, 40)
    out['lining'] = to_wall(lining, p0, p1, out=True)

    cs = _both_casings(name + "_cs", w, h, wall_th, cname, cut_below=0.0)
    mlib.translate(cs, (u0, 0, 0))
    out['casing'] = to_wall(cs, p0, p1, out=True)

    lw, lh = w - 0.010, h - 0.012
    leaf = panel_door(name + "_leaf", lw, lh, th, cname=cname)
    hg = hinges(name + "_hg", lh, th, 0.0 if hinge_left else lw, cname)
    group = [leaf, hg]
    if knob:
        group.append(door_hardware(name + "_hw", lw, th, hinge_left, cname))
    # The hinge axis has to sit on the face the door swings TOWARDS - that is
    # where a real knuckle goes, and it is the only position where the leaf's
    # trailing corner stays inside the opening.  Pivot on the wrong face and,
    # at anything past about sixty degrees, that corner swings a half-thickness
    # PAST the jamb and buries itself in the lining.
    y0 = (wall_th - th) * 0.5
    ang = swing if hinge_left else -swing
    toward_neg = (ang < 0) if hinge_left else (ang > 0)
    piv = (0.0 if hinge_left else lw, y0 if toward_neg else y0 + th)
    for o in group:
        mlib.translate(o, (0, y0, 0.006))
        if swing:
            mlib.rotate_z(o, ang, piv)
        mlib.translate(o, (u0 + 0.005, 0, 0))
    out['leaf'] = to_wall(leaf, p0, p1, out=True)
    out['hinges'] = to_wall(hg, p0, p1, out=True)
    if knob:
        out['knob'] = to_wall(group[2], p0, p1, out=True)
    if mats_:
        mlib.set_mat(out['lining'], mats_.get('trim'))
        mlib.set_mat(out['casing'], mats_.get('trim'))
        mlib.set_mat(out['leaf'], mats_.get('door'))
        mlib.set_mat(out['hinges'], mats_.get('brass'))
        if knob:
            mlib.set_mat(out['knob'], mats_.get('brass'))
    return out


# ---------------------------------------------------------------- windows

def sash_window(name, w, h, th, cname="Openings", cols=2, frame=0.050,
                glaz=0.020, meet=0.036):
    """A double-hung sash window: box lining, two sashes in their OWN planes so
    they can never be coplanar, glazing bars, stool, apron and a sloped outer
    sill.  The lower sash sits 26 mm nearer the room than the upper, which is
    how a real double-hung runs and is the reason the two halves catch window
    light differently."""
    parts, glass = [], []
    lt = th - 0.004                     # see make_door: never flush with the
    for (a, b) in ((0.0, 0.022), (w - 0.022, w)):   # wall's outer face
        parts.append(mlib.box(name + "_lj%.2f" % a, a, 0.0, 0.0, b, lt, h, cname))
    parts.append(mlib.box(name + "_lh", 0, 0.0, h - 0.022, w, lt, h, cname))
    # The stool stops short of the wall's outer face for the same reason the
    # lining does - run through to `th` its end face is flush with the outside
    # of the building and fights the masonry from the light well.
    parts.append(mlib.box(name + "_stool", -0.032, -0.055, -0.040,
                          w + 0.032, lt, 0.0, cname))
    parts.append(mlib.box(name + "_apron", 0.014, -0.032, -0.150, w - 0.014,
                          -0.004, -0.040, cname))
    parts.append(mlib.prism_xz(name + "_sill",
                               [(-0.02, 0.0), (w + 0.02, 0.0),
                                (w + 0.02, -0.038), (-0.02, -0.058)],
                               th - 0.006, th + 0.080, cname))

    sh = (h - meet) * 0.5
    for k, (z0, z1, yy) in enumerate((
            (0.0, sh + meet, th - 0.024 - glaz),
            (sh, h - 0.022, th - 0.062 - glaz))):
        sw_, x0 = w - 0.046, 0.023
        for (a, b) in ((x0, x0 + frame), (x0 + sw_ - frame, x0 + sw_)):
            parts.append(mlib.box(name + "_s%d_v%.3f" % (k, a), a, yy, z0, b,
                                  yy + glaz, z1, cname))
        for (c, d) in ((z0, z0 + frame), (z1 - frame, z1)):
            parts.append(mlib.box(name + "_s%d_h%.3f" % (k, c), x0, yy, c,
                                  x0 + sw_, yy + glaz, d, cname))
        gw = sw_ - frame * 2
        for i in range(1, cols):
            bx = x0 + frame + gw * i / cols
            parts.append(mlib.box(name + "_s%d_b%d" % (k, i), bx - 0.010, yy + 0.004,
                                  z0 + frame, bx + 0.010, yy + glaz - 0.004,
                                  z1 - frame, cname))
        glass.append(mlib.box(name + "_g%d" % k, x0 + frame * 0.62, yy + glaz * 0.42,
                              z0 + frame * 0.62, x0 + sw_ - frame * 0.62,
                              yy + glaz * 0.58, z1 - frame * 0.62, cname))
    ob = mlib.join(parts, name, cname)
    mlib.bevel(ob, 0.0016, 2, 40)
    return ob, mlib.join(glass, name + "_glass", cname)


def venetian_blind(name, w, h, cname="Openings", slat=0.048, drop=0.94,
                   tilt=56.0, y=0.0):
    """Horizontal slats, each a real dished lath, plus head box, cords and
    bottom rail.  Every reference frame of this apartment has these behind the
    drapes - the drapes never cover the glass, so this is what the window light
    is actually shaped by."""
    parts = []
    pitch = slat * 0.82
    n = max(1, int((h * drop - 0.07) / pitch))
    a = math.radians(tilt)
    prof = [(-slat * 0.5, 0.0), (-slat * 0.24, -0.0058), (slat * 0.24, -0.0058),
            (slat * 0.5, 0.0), (slat * 0.24, 0.0020), (-slat * 0.24, 0.0020)]
    for i in range(n):
        z = h - 0.058 - i * pitch
        pts = [(y + (u * math.sin(a) + v * math.cos(a)),
                z + (u * math.cos(a) - v * math.sin(a))) for (u, v) in prof]
        parts.append(mlib.prism_yz(name + "_s%d" % i, pts, 0.012, w - 0.012, cname))
    parts.append(mlib.box(name + "_head", 0.0, y - 0.032, h - 0.058, w, y + 0.032, h, cname))
    zb = h - 0.058 - n * pitch
    parts.append(mlib.box(name + "_rail", 0.014, y - 0.021, zb - 0.021,
                          w - 0.014, y + 0.021, zb, cname))
    for cx in (w * 0.22, w * 0.78):
        parts.append(mlib.box(name + "_c%.2f" % cx, cx - 0.0022, y - 0.0022, zb,
                              cx + 0.0022, y + 0.0022, h - 0.058, cname))
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 34)
    return ob


def make_window(name, p0, p1, u0, w, sill, head, wall_th=None, cname="Openings",
                cols=2, blind=True, blind_drop=0.94, blind_tilt=56.0, mats_=None):
    wall_th = L.TW if wall_th is None else wall_th
    h = head - sill
    ob, gl = sash_window(name, w, h, wall_th, cname, cols=cols)
    out = {}
    for o in (ob, gl):
        mlib.translate(o, (u0, 0, sill))
    out['frame'] = to_wall(ob, p0, p1, out=True)
    out['glass'] = to_wall(gl, p0, p1, out=True)
    cs = _both_casings(name + "_cs", w, h, wall_th, cname, cut_below=0.0, cw=0.098)
    mlib.translate(cs, (u0, 0, sill))
    out['casing'] = to_wall(cs, p0, p1, out=True)
    if blind:
        bl = venetian_blind(name + "_bl", w - 0.034, h - 0.012, cname,
                            drop=blind_drop, tilt=blind_tilt, y=wall_th - 0.085)
        mlib.translate(bl, (u0 + 0.017, 0, sill))
        out['blind'] = to_wall(bl, p0, p1, out=True)
    if mats_:
        mlib.set_mat(out['frame'], mats_.get('trim'))
        mlib.set_mat(out['casing'], mats_.get('trim'))
        mlib.set_mat(out['glass'], mats_.get('glass'))
        if blind:
            mlib.set_mat(out['blind'], mats_.get('blind'))
    return out
