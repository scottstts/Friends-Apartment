"""Assemble every door and window into the shell."""
import bpy, bmesh, math
from mathutils import Matrix, Vector
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


def _sup_r(th, a, b, n):
    """Radius of the superellipse |x/a|^n + |z/b|^n = 1 along a ray."""
    c, s = math.cos(th), math.sin(th)
    return (abs(c / a) ** n + abs(s / b) ** n) ** (-1.0 / n)


# ---- the peephole surround, measured off ref_images/decoration.png ------
# Everything here is in REFERENCE PIXELS of that image with the origin at the
# centre of the opening, +X right, +Z up: outer 341 x 361, opening 188 x 223.
_PF_AW, _PF_AH = 96.0, 114.0        # opening half-width / half-height
_PF_APN = 7.0                       # opening is a superellipse: straight sides
_PF_CMAX = 0.5 ** (1.0 / _PF_APN)   # ...so this is |x|/AW on its diagonal
# How far the moulding stands out from the opening, round the loop: widest at
# the middle of each side, cut back towards the diagonals where the curls take
# the outline over.  Cutting on min(|x|/AW, |z|/AH) rather than on the polar
# angle is what keeps the sides' bulge broad and flat the way the reference's
# is - an angle-based taper starts eating into it far too early.  It also has
# to bite hard enough that the rail's outer edge actually falls away towards a
# corner: the opening's own radius grows by a third between the middle of a
# side and the diagonal, so a gentler taper leaves the outline widening all
# the way in, and with the curls sitting on the diagonals the whole thing
# comes out a circle.  40 at 1.7 holds each side flat and then pinches, which
# squares the outline off and opens the notch in front of each curl.
_PF_BW_TB, _PF_BW_EX = 69.5, 4.5    # 69.5 top and bottom, 74 at the sides
_PF_BW_CUT, _PF_BW_CP = 38.0, 1.7
# min() of the two has a kink exactly on the diagonal, and since the whole
# section is scaled by the rail's width that kink draws a dead-straight
# crease diagonally across each corner.  Round the min off over this much.
_PF_BW_SM = 0.30
# The rail's section, in fractions of its width.  It is ONE solid band with a
# flat top, a crown over each of its three lobes, and two narrow grooves cut
# into it - not three rolls laid side by side.  Built up out of rolls instead,
# the rail comes out as three thin separate arcs with bare bed showing between
# them however the rolls are spaced: butt them together and the crease is a
# wide shallow dish, leave a gap and the gap itself reads as a hole.  The
# moulding on the reference is one mass and its ridges are cuts in it, so that
# is how it is built here.  Three grooves, four lobes - the reference's
# middle crease is the shallow one.  The crowns are deliberately slight next
# to the grooves' depth: the rail has to read as a flat drapery creased by
# fold lines, and crowning the lobes any harder turns it back into a row of
# tubes with the silhouette rolling over far too softly.
_PF_BAND_H, _PF_BAND_P = 14.5, 8.0  # height, and how flat the top is
# The folds are not evenly spaced: they bunch towards the outer edge, so
# the lobe against the opening is the broad one and they narrow outwards.
# Spacing them evenly reads as knitting rather than gathered drapery.
_PF_LOBES = ((0.150, 0.150, 2.7), (0.430, 0.130, 3.0),
             (0.660, 0.100, 3.0), (0.885, 0.115, 2.7))
_PF_GROOVES = ((0.30, 0.065, 8.0), (0.565, 0.058, 6.9), (0.76, 0.058, 7.4))
# Powers ABOVE one on purpose.  A groove or a crown that reaches zero as a
# square root does it with a vertical tangent, so its rim is a crease of
# infinite slope sitting in the middle of an otherwise smooth surface - no
# mesh can carry that, and it comes out as the fine herringbone that used to
# run along every groove edge round the curls.  Above one the feature dies
# away tangentially and simply blends in.  Depths and widths are up a little
# to keep the same read, since these profiles are narrower at half depth.
_PF_GROOVE_P = 1.5                  # narrow and steep-sided, not a dish
_PF_LOBE_P = 1.25
_PF_FOLD_OFF, _PF_FOLD_ON = 28.0, 16.0   # rail width the folds fade over
_PF_BLEND = 2.0                     # px the curls run into the rails over
_PF_SOFT = 0.9                      # px the whole mass is softened by
# Keep that small.  Widened, the rounding piles up where the rail and BOTH
# curls of a corner are all in play at once and raises a flat wedge there.
# The eight curls.  Every one is the same size, and the two on a corner are
# each other reflected in that corner's axis, so a corner reads symmetrically
# however the frame's own proportions fall.  The axis is a degree or two off
# the true diagonal because the frame is taller than it is wide: that is what
# lands the pair's reach on 0.945, the outer proportion the reference has.
# They stand a little proud of the rails at both extremes, so each corner
# reads as its own bump.  Same idea as the rail: a solid domed lobe with a
# spiral groove cut across it, which leaves the rolled ribbon between the
# wraps standing - a raised spiral instead just reads as wire on a blob.
_PF_VOL_AXIS = 132.7                # deg, the top-left corner's axis
_PF_VOL_MID = 186.0                 # the pair's centre, out along that axis
_PF_VOL_SEP = 23.0                  # and half their step across it
_PF_VOL_R = 32.0
# A low root under each curl, tying it back into its rail: centre at this
# fraction of the eye's radius, then radius and height.  Without it the two
# masses simply do not meet at the notch - the relief drops to nothing
# between them, so the frame stops being star-shaped about its own centre,
# and a ring that lays one row per ray has no choice but to span the void.
# That is what sawed all four corners up.  It sits below both crests and
# well inside the curl's own outline, so nothing you can see moves.
_PF_ROOT_AT, _PF_ROOT_R, _PF_ROOT_H = 0.80, 40.0, 7.2
_PF_VOL_END = -10.0                 # where the rail runs into the curl
# The spiral must not start too near its own eye: at r0 = 4 the innermost
# wrap sat at a radius smaller than the groove cutting it, so the groove ate
# its own centre and the eye came out as a patch of noise.
#              turns  r0   rmax  gw   GD   CR    HB    re   Ae
_PF_VOL_CUT = (1.15, 8.0, 26.0, 4.8, 9.2, 3.5, 16.0, 7.0, 5.6)


def peephole_frame(name, w, h, cname, mat):
    """The gold rococo surround round the peephole on Monica's door.

    Built the way the prop is actually made - as ONE moulded piece.  It is
    not an assembly of tubes: on the reference each side and the two curls
    at its ends are a single continuous mass, and the ridges running along
    it are creases in that mass, not gaps between separate rods.

    So the shape is described as a relief - a height above the door face -
    and then meshed in one go as a single quad ring:

      * round the opening, a solid band with a flat top and a rolled edge at
        either side, crowned over three lobes and cut with two grooves.  It
        is widest at the middle of each side and pinched towards the corners,
        which both bulges the outline between the corners and squares it off.
      * at each corner a pair of volutes, one ending each rail: a domed lobe
        with an Archimedean spiral groove cut across it and a boss in its
        eye, so what stands proud is the rolled ribbon between the wraps.

    The mass is the upper envelope of all of that, so nothing is a seam.
    Built in XZ with +Y out of the door, matching what the caller's `place`
    expects.  w x h is the outer size.
    """
    TAU = math.tau

    def band_w(th):
        r = _sup_r(th, _PF_AW, _PF_AH, _PF_APN)
        u = abs(r * math.cos(th)) / _PF_AW
        v = abs(r * math.sin(th)) / _PF_AH
        e = max(0.0, 1.0 - abs(u - v) / _PF_BW_SM)
        c = (min(u, v) - 0.25 * _PF_BW_SM * e * e) / _PF_CMAX
        return (_PF_BW_TB + _PF_BW_EX * math.cos(th) ** 2
                - _PF_BW_CUT * max(c, 0.0) ** _PF_BW_CP)

    def rail_h(r, th):
        """The moulding, measured out from the opening along the ray.  Radial
        rather than normal to the opening: on a superellipse this near a
        rectangle the two differ by under a degree, and doing it the other way
        costs a search per sample."""
        bw = band_w(th)
        t = (r - _sup_r(th, _PF_AW, _PF_AH, _PF_APN)) / bw
        if t <= 0.0 or t >= 1.0:
            return 0.0
        k = bw / 71.0                       # the section thins with the rail
        y = _PF_BAND_H * math.sqrt(1.0 - (2.0 * t - 1.0) ** _PF_BAND_P)
        # The folds die out as the rail narrows into a corner, and they have
        # to: their width is a FRACTION of the rail's, so by the diagonal
        # they are a couple of tenths of a millimetre across - finer than
        # the mesh can carry there, because that is also where the rows are
        # longest.  Left in, they alias into the ragged steps that used to
        # sit in all four corners.  On the reference they gather and vanish
        # into the scrolls here in any case.
        f = min(max((bw - _PF_FOLD_OFF) / _PF_FOLD_ON, 0.0), 1.0)
        f = f * f * (3.0 - 2.0 * f)
        if f > 0.0:
            for (c, hw, amp) in _PF_LOBES:
                q = (t - c) / hw
                if -1.0 < q < 1.0:
                    y += f * amp * (1.0 - q * q) ** _PF_LOBE_P
            for (c, hw, d) in _PF_GROOVES:
                q = (t - c) / hw
                if -1.0 < q < 1.0:
                    y -= f * d * (1.0 - q * q) ** _PF_GROOVE_P
        return max(y, 0.0) * k

    # the curls: one pair built on the top-left corner's axis, then mirrored
    # out to the other three.  Reflecting a spiral turns it over, so the
    # handedness and the start angle travel with it - which is also how the
    # second curl of each pair is made from the first.
    ax = math.radians(_PF_VOL_AXIS)
    ux, uz = math.cos(ax), math.sin(ax)
    qx, qz = math.sin(ax), -math.cos(ax)
    turns, r0, rmax, gw, GD, CR, HB, re, Ae = _PF_VOL_CUT
    K, U, R = (rmax - r0) / turns, TAU * turns, _PF_VOL_R
    vols = []
    for sgn in (1.0, -1.0):
        ex = _PF_VOL_MID * ux + sgn * _PF_VOL_SEP * qx
        ez = _PF_VOL_MID * uz + sgn * _PF_VOL_SEP * qz
        te, hand = math.radians(_PF_VOL_END), 1.0
        if sgn < 0.0:                       # the side rail's curl, mirrored
            te, hand = 2.0 * ax - te, -hand
        for sx in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
                t, hd = te, hand
                if sx > 0.0:                # mirrored in X off the top-left
                    t, hd = math.pi - t, -hd
                if sz < 0.0:                # ...and in Z
                    t, hd = -t, -hd
                vols.append((sx * abs(ex), sz * abs(ez), t - hd * U, hd,
                             _PF_ROOT_AT * sx * abs(ex),
                             _PF_ROOT_AT * sz * abs(ez)))

    def vol_h(x, z, V):
        ex, ez, th0, hd, rx, rz = V
        dx, dz = x - rx, z - rz
        d2 = (dx * dx + dz * dz) / (_PF_ROOT_R * _PF_ROOT_R)
        root = _PF_ROOT_H * (1.0 - d2 ** 1.6) ** 1.3 if d2 < 1.0 else 0.0
        dx, dz = x - ex, z - ez
        d2 = dx * dx + dz * dz
        if d2 >= R * R:
            return root
        d = math.sqrt(d2)
        y = HB * math.sqrt(1.0 - (d / R) ** 3)
        # Where this point sits on the spiral: g counts wraps out from the
        # eye, so it lands on a whole number exactly on a groove and halfway
        # between two of them at the middle of a ribbon.  Working in that
        # coordinate crowns the ribbon as well as cutting the groove, which
        # is what makes a curl read as coiled rope instead of a flat disc
        # with a scratch in it.  psi's wrap shifts g by exactly one turn, so
        # its fraction - all the section depends on - runs on through.
        psi = (hd * (math.atan2(dz, dx) - th0)) % TAU
        g = (d - r0) / K - psi / TAU
        # ...and it fades in over most of a wrap as it winds down to the eye,
        # rather than arriving at full depth.
        f = min((g + 0.15) / 0.55, (turns + 0.3 - g) / 0.4)
        if f > 0.0:
            f = min(f, 1.0)
            f = f * f * (3.0 - 2.0 * f)     # ...and ease it in and out
            fr = g - math.floor(g)
            y += f * CR * math.sin(math.pi * fr) ** 1.4
            dd = min(fr, 1.0 - fr) * K
            if dd < gw:
                y -= f * GD * (1.0 - (dd / gw) ** 2) ** _PF_GROOVE_P
        if d < re:                          # the boss in the eye
            y += Ae * (1.0 - (d / re) ** 2) ** _PF_LOBE_P
        return max(y, root, 0.0)

    def field_s(x, z):
        """The mass, softened.  Done in WORLD space on purpose: the rows
        below run radially between two boundaries that move at very
        different rates round a corner, so grid neighbours there sit at
        quite different places across the moulding.  Averaging those - the
        obvious way to soften a height grid - smears every groove by a
        different amount from one column to the next, and that is exactly
        what put ragged chevrons in all four corners.  Sampling the field
        itself a fraction either side is the same softening and is blind
        to how the surface happens to be parametrised."""
        return (0.60 * field(x, z)
                + 0.10 * (field(x + _PF_SOFT, z) + field(x - _PF_SOFT, z)
                          + field(x, z + _PF_SOFT) + field(x, z - _PF_SOFT)))

    def field(x, z):
        r = math.hypot(x, z)
        y = rail_h(r, math.atan2(z, x)) if r > 1e-6 else 0.0
        for V in vols:
            v = vol_h(x, z, V)
            # A rounded max, not a plain one: taken flat it leaves a hard
            # crease everywhere a curl crosses its rail, and on the
            # reference the two run into one another.  The grooves are cut
            # by subtraction rather than by this, so rounding here softens
            # the joins without touching them.
            # The rounding width has to fall away with the smaller of the
            # two, or it adds height out where BOTH are zero and the
            # whole silhouette inflates into a disc.
            k = min(_PF_BLEND, v, y)
            d = k - abs(v - y) if k > 0.0 else 0.0
            y = max(v, y) + (d * d / (4.0 * k) if d > 0.0 else 0.0)
        return y

    # ---- mesh it as one ring ------------------------------------------
    # For each ray out of the centre, find where the mass ends, then lay a
    # row of samples from the opening out to there.  The relief is zero at
    # both, so the ring closes onto the door of its own accord.
    # Rows matter more than columns here.  Every groove - the rail's folds
    # and the curls' spirals alike - is crossed by the rows and run along by
    # the columns, so it is the row count that decides whether a groove comes
    # out round or terraced.  The curls sit entirely in the outer stretch of
    # each row, which is why that gets nearly half of them.
    NU, NV, EPS = 720, 68, 0.05
    BSPLIT, BFRAC = 0.52, 0.88          # share of each row given to the rail,
    #                                     and how much of the rail it spans
    cols = []
    for i in range(NU):
        th = TAU * i / NU
        ct, st = math.cos(th), math.sin(th)
        r_in = _sup_r(th, _PF_AW, _PF_AH, _PF_APN)
        lo, step, r = r_in, 2.0, r_in + 2.0
        while r < 240.0:                    # last radius still carrying mass
            if field_s(r * ct, r * st) > EPS:
                lo = r
            r += step
        hi = lo + step
        for _ in range(20):                 # then close on the edge
            m = 0.5 * (lo + hi)
            if field_s(m * ct, m * st) > EPS:
                lo = m
            else:
                hi = m
        cols.append((ct, st, r_in, lo, band_w(th)))
    # Smooth the outline before laying rows on it.  Every row runs radially
    # from the opening out to this boundary, so wherever the boundary steps
    # - and it steps by 40-odd px where a curl's arc gives way to the rail's
    # edge - neighbouring rows are stretched by very different amounts and
    # the shear between them shows as a straight crease running inwards.
    # Spreading the step over a handful of columns takes that out; it costs
    # a little of the notch in front of each curl, which is worth it.
    outs = [c[3] for c in cols]
    for _ in range(3):
        outs = [0.0625 * outs[i - 2] + 0.25 * outs[i - 1] + 0.375 * outs[i]
                + 0.25 * outs[(i + 1) % NU] + 0.0625 * outs[(i + 2) % NU]
                for i in range(NU)]

    grid = []
    for (ct, st, r_in, _, bw), r_out in zip(cols, outs):
        # Rows are NOT spread evenly from the opening out to the outline.
        # Round a corner the outline runs on to a curl while the rail itself
        # narrows, so an even spread leaves barely two samples across a
        # groove AND slides them along it from one column to the next: the
        # groove then beats against the grid and comes out as the fine comb
        # that used to sit in all four corners.  Giving the rail a fixed
        # share of the rows pins every groove to the same row the whole way
        # round.  The share has to be a CONSTANT to do that - deriving it
        # from how much of the row the rail happens to occupy puts the drift
        # straight back in wherever that ratio changes.  It stops short of
        # the rail's outer edge so there is always some row left over for
        # whatever lies beyond it, even mid-side where nothing does.
        span = r_out - r_in
        band = min(BFRAC * bw, span * 0.95)
        sp = BSPLIT
        col = []
        for j in range(NV + 1):
            u = j / NV
            if u <= sp:
                r = r_in + band * (u / sp)
            else:
                r = r_in + band + (span - band) * ((u - sp) / (1.0 - sp))
            x, z = r * ct, r * st
            col.append([x, z, field_s(x, z)])
        col[0][2] = col[NV][2] = 0.0
        grid.append(col)
    # Scale off what actually got built rather than off a nominal outer size:
    # the curls set the silhouette, and they move whenever their placement is
    # touched.
    ox = max(abs(c[0]) for col in grid for c in col)
    oz = max(abs(c[1]) for col in grid for c in col)
    SX, SZ = 0.5 * w / ox, 0.5 * h / oz
    SY = 0.5 * (SX + SZ)
    verts, faces = [], []
    for col in grid:
        for (x, z, y) in col:
            verts.append((x * SX, y * SY, z * SZ))
    W = NV + 1
    for i in range(NU):
        i2 = (i + 1) % NU
        for j in range(NV):
            faces.append((i * W + j, i2 * W + j, i2 * W + j + 1, i * W + j + 1))
        # the back, flat on the door and never seen
        faces.append((i2 * W, i * W, i * W + NV, i2 * W + NV))

    ob = mlib.mesh_obj(name, verts, faces, cname)
    mlib.recalc_normals(ob)
    # Shade it all smooth and mark ONLY the two rims sharp - the edges where
    # the relief turns over onto its own flat back.  An angle threshold
    # cannot tell those from the steep wall of a groove: at anything low
    # enough to catch the rim it also catches a couple of thousand scattered
    # groove edges, and hard-shading those is what made the curls look
    # patchy.  Here the rim is known by index, so it can just be named.
    me = ob.data
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    bm = bmesh.new()
    bm.from_mesh(me)
    for e in bm.edges:
        a, b = e.verts[0].index % W, e.verts[1].index % W
        e.smooth = not (a == b and (a == 0 or a == NV))
    bm.to_mesh(me)
    bm.free()
    me.update()
    mlib.set_mat(ob, mat)
    return ob


def _lock_plate(name, w, h, r, y0, y1, cname, seg=4):
    """A back plate lying flat on a face: outline in (x, z), standing off in Y."""
    return mlib.prism_xz(name, mlib.rounded_rect(w, h, r, seg), y0, y1, cname)


def _lock_turn(name, prof, cname, at, seg=20):
    """Anything turned - a knob, a collar, a screw head - with its axis out of
    the face it is mounted on."""
    ob = mlib.revolve(name, prof, seg, cname=cname)
    mlib.rot_x(ob, -math.pi / 2)
    mlib.translate(ob, at)
    return ob


def surface_bolt(name, cname, mat):
    """A barrel bolt lying across the stile: back plate, two guide straps, the
    bolt running through them towards the door edge, and a thumb tab on it.
    The old one was a bare rounded slab with no bolt on it at all."""
    P = [_lock_plate(name + "_pl", 0.100, 0.032, 0.007, 0.0, 0.005, cname)]
    for k, gx in enumerate((-0.030, 0.024)):    # the two guide straps
        g = _lock_plate(name + "_gd%d" % k, 0.013, 0.026, 0.004,
                        0.005, 0.0165, cname, seg=2)
        mlib.translate(g, (gx, 0.0, 0.0))
        P.append(g)
    # the bolt, shot to within a few mm of the leaf's edge
    P.append(mlib.tube_along(name + "_bo",
                             [(-0.064, 0.0107, 0.0), (0.036, 0.0107, 0.0)],
                             mlib.circle(0.0055, 14), cname, up=(0, 0, 1)))
    # a flat lug to throw it by - a turned knob here reads as a third lock
    P.append(_lock_plate(name + "_tb", 0.011, 0.019, 0.005,
                         0.0150, 0.0194, cname, seg=3))
    screw = ((0.0, 0.0), (0.0030, 0.0), (0.0030, 0.0012),
             (0.0017, 0.0021), (0.0, 0.0023))
    for k, (sx, sz) in enumerate(((-0.043, 0.0), (0.043, 0.0))):
        P.append(_lock_turn(name + "_sc%d" % k, screw, cname, (sx, 0.005, sz), 10))
    ob = mlib.join(P, name, cname)
    mlib.smooth_shade(ob, 34)
    mlib.set_mat(ob, mat)
    return [ob]


def chain_slide(name, cname, mat, dark):
    """The door half of a security chain: the track its ball-end runs in, with
    the round pocket at the open end that the ball drops into."""
    P = [_lock_plate(name + "_pl", 0.086, 0.024, 0.011, 0.0, 0.0048, cname)]
    screw = ((0.0, 0.0), (0.0028, 0.0), (0.0028, 0.0011),
             (0.0016, 0.0020), (0.0, 0.0022))
    for k, sx in enumerate((-0.036, 0.036)):
        P.append(_lock_turn(name + "_sc%d" % k, screw, cname, (sx, 0.0048, 0.0), 10))
    ob = mlib.join(P, name, cname)
    mlib.smooth_shade(ob, 34)
    mlib.set_mat(ob, mat)
    # the slot, and the pocket at the door-edge end of it
    sl = mlib.prism_xz(name + "_sl", mlib.rounded_rect(0.050, 0.008, 0.004, 3),
                       0.0, 0.0052, cname)
    mlib.translate(sl, (0.008, 0.0, 0.0))
    pk = mlib.prism_xz(name + "_pk", mlib.circle(0.0072, 14), 0.0, 0.0052, cname)
    mlib.translate(pk, (-0.020, 0.0, 0.0))
    slot = mlib.join([sl, pk], name + "_slot", cname)
    mlib.set_mat(slot, dark)
    return [ob, slot]


def _chain_link(name, c, R, r, across, cname):
    """One link, lying in a plane that contains the vertical so it hangs, and
    turned across its neighbours the way a chain actually runs."""
    a = [math.tau * k / 12.0 for k in range(12)]
    if across:
        path = [(c[0], c[1] + R * math.cos(t), c[2] + R * math.sin(t)) for t in a]
        up = (1.0, 0.0, 0.0)
    else:
        path = [(c[0] + R * math.cos(t), c[1], c[2] + R * math.sin(t)) for t in a]
        up = (0.0, 1.0, 0.0)
    return mlib.tube_along(name, path, mlib.circle(r, 6), cname,
                           close_path=True, up=up)


def chain_anchor(name, cname, mat, links=12):
    """The jamb half: the anchor plate, and the chain hanging slack off it with
    its ball-end swinging free - the door is shut but not chained, which is how
    the set photo has it.  The old chain was one smooth bent tube."""
    P = [_lock_plate(name + "_pl", 0.026, 0.052, 0.007, 0.0, 0.005, cname, seg=3)]
    screw = ((0.0, 0.0), (0.0028, 0.0), (0.0028, 0.0011),
             (0.0016, 0.0020), (0.0, 0.0022))
    for k, sz in enumerate((-0.018, 0.018)):
        P.append(_lock_turn(name + "_sc%d" % k, screw, cname, (0.0, 0.005, sz), 10))
    R, r, pitch = 0.0062, 0.0017, 0.0088
    x0, y0, z0 = 0.0, 0.0088, -0.022
    for k in range(links):
        t = k / float(links - 1)
        c = (x0, y0 + 0.006 * t, z0 - pitch * k)
        P.append(_chain_link(name + "_lk%d" % k, c, R, r, k % 2 == 1, cname))
    # the ball on the free end that runs in the track
    end = (x0, y0 + 0.006, z0 - pitch * (links - 0.6))
    bl = mlib.revolve(name + "_bl",
                      [(0.0, -0.0072), (0.0042, -0.0060), (0.0058, -0.0022),
                       (0.0058, 0.0022), (0.0042, 0.0060), (0.0, 0.0072)],
                      12, cname=cname)
    mlib.translate(bl, end)
    P.append(bl)
    ob = mlib.join(P, name, cname)
    mlib.smooth_shade(ob, 40)
    mlib.set_mat(ob, mat)
    return [ob]


def build(M=None):
    M = M or mk_mats()
    C = "Openings"

    # ============================================================ FRONT DOOR
    w, top = L.FD_Y[1] - L.FD_Y[0], L.FD_TOP
    cy = (L.FD_Y[0] + L.FD_Y[1]) * 0.5
    jamb_t = 0.024
    ln = O.lining("FD_lining", w, top, L.TW, jamb_t, C, M['trim'])
    O.place(ln, (0.0, cy, 0.0), (0, 1), (-1, 0))
    cs = O.casing("FD_casing", w, top, 0.100, 0.026, C, M['trim'])
    O.place(cs, (0.0, cy, 0.0), (0, 1), (1, 0))
    # outside architrave (seen from the hallway) - simple
    cs2 = O.casing("FD_casing_out", w, top, 0.070, 0.016, C, M['trim'])
    O.place(cs2, (-L.TW, cy, 0.0), (0, 1), (-1, 0))
    # transom: head rail + sash
    # ...between the linings, not across the whole rough opening: full width
    # it sits inside both jambs and the shared faces flicker at the two top
    # corners.  The transom above already sizes itself this way.
    hw = w / 2 - jamb_t
    hr = mlib.box("FD_headrail", -hw, 0.0, L.FD_H, hw, L.TW, L.FD_H + 0.075, C)
    O.place(hr, (0.0, cy, 0.0), (0, 1), (-1, 0))
    mlib.set_mat(hr, M['trim'])
    # ...and clear of the head lining as well as the jambs.  Run to the full
    # height of the rough opening its top rail sits inside the lining's head,
    # and the shared faces flicker in a stripe right across the transom.
    tf, tg = O.steel_window("FD_transom", w - 2 * jamb_t,
                            top - jamb_t - L.FD_H - 0.085, [1], 1,
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
    # The gold frame is the one thing everyone knows about this door, and a
    # mitred rectangle is not it.  The prop is a moulded rococo surround with
    # a pair of volutes on every corner and a reeded rail between them; see
    # peephole_frame.  300 x 318 is the reference's own outer proportion.
    fr = peephole_frame("FD_yellowframe", 0.300, 0.3178, C, M['gold'])
    O.place(fr, (fx, cy, 1.545), (0, 1), (1, 0))
    # ...and the spyhole belongs in the middle of it.  It was moved out above
    # the frame back when the frame was a plain rectangle with nothing to say
    # about where it sat; the frame is hung *around* the spyhole on the set.
    ph = mlib.revolve("FD_peep", [(0.0, 0.0), (0.009, 0.0), (0.009, 0.006),
                                  (0.005, 0.008), (0.0, 0.008)], 16, cname=C)
    mlib.rot_x(ph, -math.pi / 2)
    O.place(ph, (fx, cy, 1.545), (0, 1), (1, 0))
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
    # Three fittings up the latch stile and no more, top to bottom: the
    # security chain, the bolt, and the knob - which is exactly what the set
    # photo has.  Only ONE of them is a knob you turn; every escutcheon added
    # beyond these just puts another brass disc on the stile.
    ly = L.FD_Y[0]
    for ob in chain_slide("FD_chain_slide", C, M['chrome'], M['steel_dk']):
        O.place(ob, (fx, ly + 0.080, 1.585), (0, 1), (1, 0))
    # ...the chain itself hangs off the reveal, not off the leaf: a chain with
    # both ends on the door is the thing that made this stack read as nonsense.
    for ob in chain_anchor("FD_chain", C, M['chrome']):
        # ...on the lining's face, not on the rough opening - the reveal is
        # lined, so the jamb you can actually screw into is a jamb_t in.
        # Hung off ly it ends up buried inside the lining and invisible.
        O.place(ob, (-0.045, ly + jamb_t, 1.585), (1, 0), (0, 1))
    for ob in surface_bolt("FD_bolt", C, M['brass']):
        O.place(ob, (fx, ly + 0.085, 1.265), (0, 1), (1, 0))

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
    # Standing right back against its own wall.  swing_leaf pivots the leaf
    # about a point on its face, so where that point sits is what limits the
    # swing: 30 mm inside the reveal and the leaf ate into the jamb past 127
    # deg, while 84 deg left it stranded across the middle of a room that has
    # nothing in that quadrant to stop it.  Put the pivot on the arris (held
    # 6 mm clear of the plaster) and the leaf itself never reaches the wall at
    # any angle - what runs out first is the knob on its back face, which
    # touches at about 174.  165 keeps 111 mm behind the knob.  Nothing in the
    # room is even close: the tip lands at (3.04, 6.32), 0.27 m short of the
    # basin, and the tub is a full metre from the hinge - further than the leaf
    # is long, so it could never have been reached whatever the angle.
    swing_leaf("BD_leaf", bdw - 0.050, L.BD_H - 0.028,
               (L.HALL_WW[0] - 0.006, L.BD_Y[1] - 0.024), (0.0, -1.0), 165.0, M,
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
