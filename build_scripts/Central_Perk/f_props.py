"""Fittings and dressing: the lamps, the neon, the signs, the flowers and the
clutter on the tables.

Every light in this module is created by the thing that emits it.  A pendant
function returns its shade AND its lamp, a sconce returns its bowl AND its
lamp, the neon returns tubing whose material is the emitter.  Nothing here
can produce an unmotivated light, because there is no way to ask for one -
which is the phase-4 rule expressed as an API rather than as a convention.

There is a second rule on top of that one, and it is about count rather than
motivation: only a HANDFUL of fixtures may carry actual light data.  A room
with a lamp object per practical had thirty-odd shadow-casting lights in it,
which is both slower than the whole rest of the frame put together (EEVEE
runs out of shadow atlas at about twenty) and flatter, because thirty small
sources from every direction cancel each other's modelling out.  So every
fixture here takes `energy` and defaults it to zero: with no energy it is
lit by its own shade material and contributes nothing but its glow, and the
four that do get energy are named in f_layout.fittings().
"""
import bpy, math, importlib
import mlib as M
import mats as T
import L

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C = "Fittings"
CD = "Dressing"
TAU = math.tau
MAT = {}
ASSETS = "/Users/scott/Documents/Projects/Blender/central_perk/assets/"


def mats():
    if MAT:
        return MAT
    MAT['opal'] = T.paint('opal_glass', 'F2EEE2', rough=0.22, coat=0.4)
    # The shades of the fixtures that are switched on.  Every practical in
    # the room is lit whether or not it carries light data, so the glow lives
    # in the material and the four lamps that actually illuminate are chosen
    # separately - see the module docstring.
    MAT['opal_lit'] = T.lampshade('opal_glass_lit', 'F2EEE2', 'FFDCAE',
                                  strength=3.8, rough=0.22, transm=0.26)
    MAT['amber_lit'] = T.lampshade('amber_glass_lit', 'D8A45A', 'FFB765',
                                   strength=8.0, rough=0.16, transm=0.40)
    MAT['enamel_lit'] = T.lampshade('enamel_white_lit', 'F0EDE4', 'FFD9A0',
                                    strength=5.5, rough=0.24, transm=0.0)
    MAT['bulb_lit'] = T.lampshade('bulb_lit', 'FFF4E2', 'FFE0B0',
                                  strength=8.0, rough=0.18, transm=0.5)
    # the corridor globes: brighter than a shop fitting because they are the
    # only thing lighting that corridor - see ceiling_globe()
    MAT['globe_lit'] = T.lampshade('globe_lit', 'F6F0E0', 'FFD9A2',
                                   strength=22.0, rough=0.24, transm=0.5)
    MAT['flame'] = T.emissive('candle_flame', 'FFB05A', strength=26.0)
    MAT['brass'] = T.metal('fit_brass', 'A88433', rough=0.28, tarnish=0.5)
    MAT['brass_dk'] = T.metal('fit_brass_dk', '8A6A28', rough=0.38,
                              tarnish=0.66)
    MAT['iron'] = T.iron('fit_iron', '1A1C1A', rough=0.5)
    MAT['antler'] = T.paint('antler_horn', '473A2A', rough=0.66, bump=0.28)
    MAT['amber'] = T.glass('amber_glass', tint='D89838', rough=0.12, alpha=0.3)
    MAT['wood'] = T.wood('prop_wood', light='6E4826', dark='2A1608', ring=28.0)
    MAT['gilt'] = T.metal('frame_gilt', 'B08A3E', rough=0.34, tarnish=0.44)
    MAT['red'] = T.paint('sign_red', 'B01F1C', rough=0.42, coat=0.2)
    MAT['cream'] = T.paint('sign_cream', 'CFC3A6', rough=0.46, coat=0.16)
    MAT['yellow'] = T.paint('sign_yellow', 'E8B62A', rough=0.40, coat=0.2)
    MAT['green'] = T.paint('sign_green', L.GREEN_IRON, rough=0.36, coat=0.2)
    # The curtains beside the counter are a bold woven ticking in full_set.jpg
    # and main_couch.webp - cream, crimson, bottle green and a thin gold -
    # not the flat green they were.
    _TICK = ((3.0, 'C9B894'), (1.6, '8E2A22'), (0.7, 'C9B894'),
             (1.8, '2C5240'), (0.6, 'B8912F'))
    MAT['curtain'] = T.fabric('curtain_stripe', 'C9B894', rough=0.80,
                              sheen=0.35, scale=140.0, stripes=_TICK,
                              pitch=0.30)
    MAT['curtain2'] = T.fabric('curtain_stripe2', 'C9B894', rough=0.82,
                               sheen=0.30, scale=140.0, stripes=_TICK,
                               pitch=0.26)
    MAT['leaf'] = T.foliage('prop_leaf')
    MAT['stem'] = T.foliage('prop_stem', light='6E8A46', dark='3E5424',
                            scale=70.0)
    MAT['china'] = T.paint('prop_china', 'EDE8DC', rough=0.14, coat=0.55)
    MAT['paper'] = T.flat('prop_paper', 'D8D2C4', rough=0.78)
    return MAT


def _light(name, kind, energy, loc, color=(1.0, 0.86, 0.66), radius=0.06,
           cname=C, spot=None):
    """A lamp, or nothing at all.

    `energy` of zero is not an error and not a light with no output: it means
    this fixture is one of the many that glows without illuminating, so no
    light datablock is made and any one left over from a previous build is
    removed.  Every caller can therefore hand its energy straight through
    without testing it first."""
    if not energy:
        ob = bpy.data.objects.get(name)
        if ob is not None and ob.type == 'LIGHT':
            bpy.data.objects.remove(ob, do_unlink=True)
        return None
    ld = bpy.data.lights.get(name) or bpy.data.lights.new(name, kind)
    ld.type = kind
    ld.energy = energy
    ld.color = color
    try:
        ld.shadow_soft_size = radius
    except Exception:
        pass
    if kind == 'AREA':
        ld.size = radius * 2
    if kind == 'SPOT' and spot:
        ld.spot_size = spot[0]
        ld.spot_blend = spot[1]
    ob = bpy.data.objects.get(name)
    if ob is None or ob.data != ld:
        if ob:
            bpy.data.objects.remove(ob, do_unlink=True)
        ob = bpy.data.objects.new(name, ld)
    M.put(ob, cname)
    ob.location = loc
    return ob


# ------------------------------------------------------------------- lamps

def schoolhouse(name, x, y, z, ztop, cname=C, energy=0.0):
    """The pair of ribbed opal pendants over the north alcove.  Rod, brass
    fitter, and a fluted shade that flares out and tucks back under - the
    tuck is what stops it reading as a lampshade off a bedside table."""
    m = mats()
    parts, brass = [], []
    rod = M.tube_along(name + "_rod", [(0, 0, z + 0.145), (0, 0, ztop)],
                       M.circle(0.010, 10), cname=cname, up=(0, 0, 1))
    brass.append(rod)
    ros = M.revolve(name + "_ros", [(0.0, ztop - 0.030), (0.062, ztop - 0.028),
                                    (0.058, ztop - 0.006), (0.0, ztop)],
                    segments=18, cname=cname)
    brass.append(ros)
    fit = M.revolve(name + "_fit",
                    [(0.0, z + 0.155), (0.048, z + 0.150), (0.052, z + 0.118),
                     (0.070, z + 0.104), (0.066, z + 0.086), (0.0, z + 0.086)],
                    segments=20, cname=cname)
    brass.append(fit)
    # fluted shade: radius squeezed by a cosine of the sweep
    prof = [(0.062, z + 0.100), (0.088, z + 0.070), (0.126, z + 0.020),
            (0.150, z - 0.038), (0.155, z - 0.080), (0.140, z - 0.104),
            (0.118, z - 0.108), (0.126, z - 0.090), (0.140, z - 0.056),
            (0.132, z + 0.010), (0.100, z + 0.062), (0.058, z + 0.094)]
    seg, rings = 36, []
    for s in range(seg):
        a = TAU * s / seg
        k = 1.0 + 0.020 * math.cos(12 * a)
        rings.append([(r * k * math.cos(a), r * k * math.sin(a), zz)
                      for (r, zz) in prof])
    sh = M._loft(name + "_shade", rings, close_u=True, close_v=True,
                 cname=cname)
    M.smooth_shade(sh, 40)
    parts.append(sh)
    ob = M.join(parts, name + "_glass", cname); M.set_mat(ob, m['opal_lit'])
    obr = M.join(brass, name + "_brass", cname); M.set_mat(obr, m['brass'])
    for o in (ob, obr):
        M.translate(o, (x, y, 0.0))
    # The lamp sits at the MOUTH of the shade, not inside it.  Inside, the
    # opal globe is a closed dielectric across every outgoing direction and
    # swallows most of what the lamp emits - which is why the first pass with
    # four practicals lit four small pools and left the rest of the room two
    # stops down.  At the mouth it throws down and out the way a schoolhouse
    # pendant actually does, and the glass above it still glows because the
    # glass is an emitter in its own right.
    lt = _light(name + "_lamp", 'POINT', energy, (x, y, z - 0.135),
                color=(1.0, 0.84, 0.60), radius=0.11, cname=cname)
    return [ob, obr, lt]


def ceiling_globe(name, x, y, z, r=0.13, cname=C, energy=0.0):
    """A plain opal globe screwed straight to a ceiling - what a back
    corridor gets, as against the fittings in the shop itself.

    It carries no light data.  Through the lobby doorway the shop sees a lit
    corridor in every set photograph and a black rectangle in the first pass;
    the lighting rule caps the room at four practicals, so this one earns its
    brightness from its own emission rather than from a fifth lamp - which is
    exactly the second rule, and which works because the fitting is on screen
    whenever the corridor is."""
    m = mats()
    ring = M.revolve(name + "_r",
                     [(0.0, z), (r * 0.52, z), (r * 0.55, z - 0.018),
                      (r * 0.46, z - 0.030), (0.0, z - 0.030)],
                     segments=20, cname=cname)
    M.set_mat(ring, m['brass_dk'])
    prof = [(0.0, z - 0.022)]
    for k in range(1, 13):
        a = math.pi * k / 13.0
        prof.append((r * math.sin(a) * 1.02, z - 0.022 - r * 0.92 *
                     (1.0 - math.cos(a))))
    prof.append((0.0, z - 0.022 - r * 1.84))
    gl = M.revolve(name + "_g", prof, segments=24, cname=cname)
    M.smooth_shade(gl, 44)
    M.set_mat(gl, m['globe_lit'])
    for o in (ring, gl):
        M.translate(o, (x, y, 0.0))
    lt = _light(name + "_lamp", 'POINT', energy, (x, y, z - r), cname=cname)
    return [o for o in (ring, gl, lt) if o is not None]


def antler_chandelier(name, x, y, z, cname=C, energy=0.0, arms=9):
    """The antler chandelier by the entrance.  Each horn is a tapering tube
    with two forks; a candle tube and a flame-sized lamp sit on the tips that
    point up."""
    m = mats()
    horn, brs, flame = [], [], []
    rod = M.tube_along(name + "_rod", [(0, 0, z + 0.10), (0, 0, L.CZ - 0.02)],
                       M.circle(0.008, 8), cname=cname, up=(0, 0, 1))
    brs.append(rod)
    lamps = []
    for i in range(arms):
        a = TAU * i / arms
        tilt = 0.34 + 0.26 * ((i * 7) % 3) / 2.0
        ln = 0.56 + 0.14 * ((i * 5) % 3) / 2.0
        pts = [(0.0, 0.0, z)]
        for k in range(1, 7):
            t = k / 6.0
            r = ln * t
            # antlers sweep UP and out, they do not radiate flat like a starburst
            zz = z + (t ** 0.7) * tilt * 0.85 - 0.06 * math.sin(t * math.pi)
            wob = 0.10 * math.sin(t * 3.4 + i)
            pts.append(((r + wob * 0.2) * math.cos(a + wob),
                        (r + wob * 0.2) * math.sin(a + wob), zz))
        rad = [0.034, 0.030, 0.026, 0.022, 0.018, 0.014, 0.010]
        rings = []
        for p, rr in zip(pts, rad):
            rings.append([(p[0] + rr * math.cos(t2), p[1] + rr * math.sin(t2),
                           p[2]) for t2 in [k2 * TAU / 8 for k2 in range(8)]])
        hb = M._loft(name + "_h%d" % i, rings, close_u=False, close_v=True,
                     cname=cname, cap_start=True, cap_end=True)
        M.smooth_shade(hb, 40); horn.append(hb)
        # a fork off the middle
        f0 = pts[3]
        fk = [f0]
        for k in range(1, 4):
            t = k / 3.0
            fk.append((f0[0] + 0.22 * t * math.cos(a + 0.7),
                       f0[1] + 0.22 * t * math.sin(a + 0.7),
                       f0[2] + 0.19 * t))
        fr = [0.019, 0.015, 0.012, 0.008]
        rings = []
        for p, rr in zip(fk, fr):
            rings.append([(p[0] + rr * math.cos(t2), p[1] + rr * math.sin(t2),
                           p[2]) for t2 in [k2 * TAU / 7 for k2 in range(7)]])
        hf = M._loft(name + "_f%d" % i, rings, close_u=False, close_v=True,
                     cname=cname, cap_start=True, cap_end=True)
        M.smooth_shade(hf, 40); horn.append(hf)
        # candle on the tip
        tp = pts[-1]
        cd = M.revolve(name + "_c%d" % i,
                       [(0.0, 0.0), (0.024, 0.002), (0.022, 0.016),
                        (0.014, 0.020), (0.014, 0.090), (0.0, 0.094)],
                       segments=12, cname=cname)
        M.translate(cd, (tp[0], tp[1], tp[2]))
        brs.append(cd)
        # the flame itself is what is actually bright: a teardrop of emission
        # on the wick, so the chandelier reads as burning without nine lamps
        fl = M.revolve(name + "_fl%d" % i,
                       [(0.0, 0.090), (0.009, 0.101), (0.011, 0.116),
                        (0.006, 0.134), (0.0, 0.142)], segments=10,
                       cname=cname)
        M.smooth_shade(fl, 40)
        M.translate(fl, (tp[0], tp[1], tp[2]))
        flame.append(fl)
    oh = M.join(horn, name + "_horn", cname); M.set_mat(oh, m['antler'])
    ob = M.join(brs, name + "_brass", cname); M.set_mat(ob, m['brass_dk'])
    of = M.join(flame, name + "_flame", cname); M.set_mat(of, m['flame'])
    M.translate(of, (x, y, 0.0))
    # ONE lamp for the whole fitting, sitting in the ring of candles, not one
    # per arm.  Nine coincident point lights cost nine times as much, count
    # nine times over against the light budget, and are indistinguishable
    # from one at this radius - the ring of flames is what the eye reads as
    # nine sources, and that is geometry, not light data.
    lamps = [_light(name + "_lamp", 'POINT', energy,
                    (x, y, z + 0.30), color=(1.0, 0.72, 0.40), radius=0.34,
                    cname=cname), of]
    lamps = [o for o in lamps if o is not None]
    for o in (oh, ob):
        M.translate(o, (x, y, 0.0))
    return [oh, ob] + lamps


def sconce(name, x, y, z, facing, cname=C, energy=0.0):
    """Brass wall bracket with an amber shade.  `facing` is the outward wall
    normal in plan."""
    m = mats()
    fx, fy = facing
    brs, gl = [], []
    bp = M.revolve(name + "_bp",
                   [(0.0, 0.0), (0.055, 0.0), (0.052, 0.020), (0.030, 0.034),
                    (0.0, 0.036)], segments=18, cname=cname)
    M.rot_x(bp, math.radians(90))
    ang = math.atan2(fy, fx)
    M.rotate_z(bp, ang + math.pi / 2)
    M.translate(bp, (0, 0, 0)); brs.append(bp)
    arm = M.tube_along(name + "_arm",
                       [(0.0, 0.0, 0.0), (fx * 0.075, fy * 0.075, 0.045),
                        (fx * 0.135, fy * 0.135, 0.090),
                        (fx * 0.150, fy * 0.150, 0.128)],
                       M.circle(0.010, 8), cname=cname, up=(0, 0, 1))
    M.smooth_shade(arm, 40); brs.append(arm)
    shade = M.revolve(name + "_sh",
                      [(0.030, 0.128), (0.052, 0.140), (0.086, 0.176),
                       (0.098, 0.212), (0.094, 0.222), (0.080, 0.190),
                       (0.046, 0.152), (0.028, 0.140)],
                      segments=22, cname=cname)
    M.smooth_shade(shade, 42)
    M.translate(shade, (fx * 0.150, fy * 0.150, 0.0)); gl.append(shade)
    ob = M.join(brs, name + "_brass", cname); M.set_mat(ob, m['brass'])
    og = M.join(gl, name + "_glass", cname); M.set_mat(og, m['amber_lit'])
    for o in (ob, og):
        M.translate(o, (x, y, z))
    lt = _light(name + "_lamp", 'POINT', energy,
                (x + fx * 0.150, y + fy * 0.150, z + 0.170),
                color=(1.0, 0.70, 0.42), radius=0.045, cname=cname)
    return [ob, og, lt]


# -------------------------------------------------------------------- neon

def _fit_x(ob, width):
    """Squeeze a mesh to `width` across, about its own centre.

    Lettering set at a nominal point size is whatever width the font makes
    it, and on the SERVICE plate that came out wider than the plate: the
    render read "SERVIC" with the E off the end.  A sign painter sizes the
    letters to the board, so this does too."""
    xs = [v.co.x for v in ob.data.vertices]
    if not xs:
        return ob
    w = max(xs) - min(xs)
    if w > width > 0:
        M.scale_mesh(ob, (width / w, 1.0, 1.0))
    return ob


def _text_mesh(name, body, size, cname=C, extrude=0.010, bold=False,
               align='CENTER', spacing=1.0):
    cu = bpy.data.curves.new(name + "_c", type='FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.space_character = spacing
    ob = bpy.data.objects.new(name, cu)
    M.put(ob, cname)
    M.active(ob)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.object
    ob.name = name
    return ob


def neon_text(name, body, x, y, z, size, colour, facing, cname=C,
              energy=None, tilt=0.0):
    """A neon word.  The glass really is the emitter - there is no lamp
    hiding behind it - so what it lights is exactly what the tube can see."""
    ob = _text_mesh(name, body, size, cname=cname, extrude=0.014)
    M.rot_x(ob, math.radians(90))
    M.rotate_z(ob, math.atan2(facing[1], facing[0]) + math.pi / 2)
    if tilt:
        M.rot_y(ob, math.radians(tilt))
    M.translate(ob, (x, y, z))
    M.set_mat(ob, T.neon('neon_' + name, colour, strength=24.0))
    out = [ob]
    if energy:
        out.append(_light(name + "_glow", 'POINT', energy,
                          (x + facing[0] * 0.10, y + facing[1] * 0.10, z),
                          color=T.srgb(colour)[:3], radius=0.16, cname=cname))
    return out


def _ell(cx, cy, rx, ry, a0=0.0, a1=TAU, n=28):
    """Points on an ellipse arc - the shape a drawn cup rim and a drawn
    saucer actually are, as against the straight line the first pass used."""
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n),
             cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def _neon_tubes(name, paths, s, x, y, z, facing, colour, cname, rad,
                strength=20.0):
    """Bend a set of (u, v) polylines into glass tube and stand them on a
    wall whose outward normal in plan is `facing`.

    The local frame is +X along the wall's normal, +Y along the wall and +Z
    up, so the rotation that aims it is atan2 of the facing and NOTHING
    else.  The extra quarter turn that used to be here - copied from the
    lettering, which starts life lying in the XY plane and needs it - stood
    the whole sign on edge, pointing along the wall instead of off it."""
    ang = math.atan2(facing[1], facing[0])
    prof = M.circle(rad, 8)
    parts = []
    for i, p in enumerate(paths):
        # Bezier segments are chained end to start, so every joint carries a
        # duplicate point.  Swept, a zero-length step has no tangent to build
        # a ring on and the tube collapses there.
        pts = []
        for (u, v) in p:
            q = (0.0, u * s, v * s)
            if pts and abs(q[1] - pts[-1][1]) < 1e-7 \
                    and abs(q[2] - pts[-1][2]) < 1e-7:
                continue
            pts.append(q)
        if len(pts) < 2:
            continue
        loop = (abs(pts[0][1] - pts[-1][1]) < 1e-6 and
                abs(pts[0][2] - pts[-1][2]) < 1e-6)
        if loop:
            pts = pts[:-1]
        t = M.tube_along(name + "_t%d" % i, pts, prof, cname=cname,
                         up=(1, 0, 0), cap=True, close_path=loop)
        M.smooth_shade(t, 40)
        parts.append(t)
    ob = M.join(parts, name, cname)
    M.rotate_z(ob, ang)
    M.translate(ob, (x, y, z))
    M.set_mat(ob, T.neon('neon_' + name, colour, strength=strength))
    return ob


def neon_cup(name, x, y, z, s, facing, cname=C, cup='F5C518',
             saucer='35E0C8'):
    """The outline coffee cup on the entrance pier, drawn as bent tube.

    Measured off frontal.jpeg, where the whole sign is 0.45 m across: an
    amber cup with an elliptical rim, a looped handle on the right and two
    wisps of steam, standing in a separate cyan saucer ring.  `s` is the
    bowl's half width; everything else is proportioned off it.

    The rim is an ellipse and not the straight line it was: a cup drawn
    without the ellipse of its own opening reads as a bucket."""
    bowl = [(-1.00, 0.0), (-0.96, -0.30), (-0.84, -0.60), (-0.62, -0.79),
            (-0.32, -0.90), (0.0, -0.92), (0.32, -0.90), (0.62, -0.79),
            (0.84, -0.60), (0.96, -0.30), (1.00, 0.0)]
    amber = [bowl,
             _ell(0.0, 0.0, 1.00, 0.20),                       # the rim
             M.arc_pts(1.00, -0.38, 0.52, math.radians(-78),
                       math.radians(78), n=14)]
    for k, (dx, hgt) in enumerate(((-0.34, 1.20), (0.04, 1.14))):
        amber.append([(dx + 0.10 * math.sin(t * 5.4 + k * 1.4),
                       0.10 + hgt * t)
                      for t in [i / 9.0 for i in range(10)]])
    cyan = [_ell(0.0, -0.79, 1.27, 0.41)]
    ob = _neon_tubes(name, amber, s, x, y, z, facing, cup, cname, 0.0085)
    og = _neon_tubes(name + "_saucer", cyan, s, x, y, z, facing, saucer,
                     cname, 0.0085)
    return [ob, og]


# ------------------------------------------------------- script neon lettering
# A neon word is bent tube, not extruded type, and every neon word on this set
# is a joined-up script.  Setting it in the default sans and pushing it 14 mm
# out of the wall gets the colour right and everything else wrong: the letters
# are separate, they are flat-sided, and the strokes have corners.
#
# So the alphabet below is a skeleton, one stroke per pen-lift, drawn in a box
# whose x-height is 1.0 and whose baseline is 0.  `adv` is how far the pen
# moves on afterwards.  A slant is applied to the whole word at the end, which
# is what a writing master does too - the letters are drawn upright and the
# hand is held at an angle.
def _b(p0, p1, p2, p3, n=10):
    return M.bez(p0, p1, p2, p3, n)


_SCRIPT = {
    # Lower case.  Every letter ENTERS at (0.00, 0.18) and LEAVES at about
    # (adv, 0.30), so with the pen advancing by exactly `adv` the exit stroke
    # of one letter lands on the entry stroke of the next and the word joins
    # up by construction.  The first attempt drew each letter as a shape in
    # its own right and left the joining to a fudge factor, which is why
    # "Cappuccino" came out as a knot: three strokes of the p ran through the
    # same half em, and the a and the u overlapped whatever followed them.
    'a': ([_b((0.00, 0.18), (0.24, 0.52), (0.46, 0.82), (0.60, 0.92)) +
           _b((0.60, 0.92), (0.28, 1.04), (0.02, 0.80), (0.06, 0.46)) +
           _b((0.06, 0.46), (0.10, 0.06), (0.52, -0.06), (0.66, 0.28)) +
           _b((0.66, 0.28), (0.69, 0.16), (0.71, 0.10), (0.75, 0.08)) +
           _b((0.75, 0.08), (0.86, 0.06), (0.94, 0.18), (1.00, 0.32))],
          1.04),
    'c': ([_b((0.00, 0.18), (0.24, 0.52), (0.44, 0.82), (0.60, 0.92)) +
           _b((0.60, 0.92), (0.30, 1.06), (0.02, 0.84), (0.06, 0.48)) +
           _b((0.06, 0.48), (0.10, 0.10), (0.48, -0.06), (0.72, 0.14)) +
           _b((0.72, 0.14), (0.79, 0.20), (0.84, 0.26), (0.88, 0.32))],
          0.92),
    'e': ([_b((0.00, 0.18), (0.14, 0.34), (0.26, 0.46), (0.38, 0.52)) +
           _b((0.38, 0.52), (0.14, 0.62), (0.10, 0.94), (0.34, 0.96)) +
           _b((0.34, 0.96), (0.58, 0.98), (0.66, 0.62), (0.46, 0.34)) +
           _b((0.46, 0.34), (0.32, 0.12), (0.46, -0.04), (0.66, 0.06)) +
           _b((0.66, 0.06), (0.76, 0.12), (0.84, 0.22), (0.90, 0.32))],
          0.94),
    'i': ([_b((0.00, 0.18), (0.14, 0.52), (0.26, 0.82), (0.32, 0.94)) +
           _b((0.32, 0.94), (0.30, 0.62), (0.28, 0.28), (0.32, 0.14)) +
           _b((0.32, 0.14), (0.42, 0.02), (0.56, 0.14), (0.64, 0.32)),
           [(0.33, 1.22), (0.38, 1.31)]],
          0.70),
    'n': ([_b((0.00, 0.18), (0.14, 0.54), (0.24, 0.82), (0.30, 0.94)) +
           _b((0.30, 0.94), (0.28, 0.66), (0.26, 0.36), (0.28, 0.20)) +
           _b((0.28, 0.20), (0.34, 0.72), (0.56, 1.02), (0.74, 0.86)) +
           _b((0.74, 0.86), (0.82, 0.76), (0.78, 0.36), (0.74, 0.14)) +
           _b((0.74, 0.14), (0.82, 0.04), (0.94, 0.14), (1.02, 0.32))],
          1.06),
    'o': ([_b((0.00, 0.18), (0.24, 0.52), (0.44, 0.82), (0.58, 0.92)) +
           _b((0.58, 0.92), (0.28, 1.06), (0.02, 0.82), (0.06, 0.48)) +
           _b((0.06, 0.48), (0.10, 0.08), (0.56, -0.06), (0.70, 0.30)) +
           _b((0.70, 0.30), (0.80, 0.58), (0.72, 0.82), (0.58, 0.90)) +
           _b((0.58, 0.90), (0.70, 0.97), (0.86, 0.90), (0.98, 0.76))],
          1.00),
    # p keeps its stem and its bowl in different halves of the em - that is
    # the whole reason the word is readable now
    'p': ([_b((0.00, 0.18), (0.14, 0.54), (0.26, 0.84), (0.32, 0.96)) +
           _b((0.32, 0.96), (0.26, 0.48), (0.16, -0.14), (0.10, -0.56)) +
           _b((0.10, -0.56), (0.26, -0.44), (0.34, -0.16), (0.34, 0.06)),
           _b((0.31, 0.60), (0.52, 0.90), (0.90, 0.80), (0.90, 0.46)) +
           _b((0.90, 0.46), (0.90, 0.20), (0.62, 0.06), (0.44, 0.18)),
           _b((0.87, 0.34), (0.94, 0.26), (0.99, 0.26), (1.06, 0.34))],
          1.08),
    'r': ([_b((0.00, 0.18), (0.14, 0.52), (0.24, 0.80), (0.30, 0.92)) +
           _b((0.30, 0.92), (0.32, 0.68), (0.28, 0.50), (0.34, 0.44)) +
           _b((0.34, 0.44), (0.46, 0.36), (0.58, 0.52), (0.68, 0.58)) +
           _b((0.68, 0.58), (0.78, 0.62), (0.88, 0.50), (0.94, 0.36))],
          0.96),
    's': ([_b((0.00, 0.18), (0.16, 0.50), (0.28, 0.80), (0.32, 0.92)) +
           _b((0.32, 0.92), (0.24, 0.60), (0.06, 0.48), (0.10, 0.26)) +
           _b((0.10, 0.26), (0.14, 0.04), (0.44, 0.00), (0.54, 0.20)) +
           _b((0.54, 0.20), (0.62, 0.34), (0.72, 0.34), (0.80, 0.26))],
          0.82),
    't': ([_b((0.00, 0.18), (0.14, 0.60), (0.24, 1.10), (0.30, 1.42)) +
           _b((0.30, 1.42), (0.28, 0.90), (0.24, 0.40), (0.28, 0.16)) +
           _b((0.28, 0.16), (0.36, 0.00), (0.54, 0.10), (0.64, 0.28)),
           [(0.00, 0.79), (0.32, 0.84), (0.62, 0.89)]],
          0.74),
    'u': ([_b((0.00, 0.18), (0.16, 0.56), (0.28, 0.84), (0.34, 0.94)) +
           _b((0.34, 0.94), (0.28, 0.60), (0.18, 0.20), (0.28, 0.08)) +
           _b((0.28, 0.08), (0.42, -0.04), (0.56, 0.20), (0.62, 0.52)) +
           _b((0.62, 0.52), (0.66, 0.74), (0.68, 0.86), (0.70, 0.94)) +
           _b((0.70, 0.94), (0.64, 0.60), (0.58, 0.24), (0.64, 0.12)) +
           _b((0.64, 0.12), (0.74, 0.02), (0.90, 0.14), (0.98, 0.32))],
          1.02),
    # capitals, with the swash a shopfront neon actually has ----------------
    'C': ([_b((1.30, 1.40), (1.16, 1.74), (0.62, 1.86), (0.34, 1.56)) +
           _b((0.34, 1.56), (0.00, 1.18), (0.02, 0.42), (0.40, 0.14)) +
           _b((0.40, 0.14), (0.70, -0.06), (1.00, 0.06), (1.16, 0.30)),
           _b((0.56, 1.58), (0.86, 1.68), (1.08, 1.58), (1.30, 1.38))],
          1.24),
    'E': ([_b((1.06, 1.50), (0.88, 1.78), (0.44, 1.74), (0.38, 1.40)) +
           _b((0.38, 1.40), (0.32, 1.14), (0.62, 1.06), (0.76, 1.02)) +
           _b((0.76, 1.02), (0.42, 1.00), (0.26, 0.84), (0.28, 0.54)) +
           _b((0.28, 0.54), (0.30, 0.18), (0.68, 0.02), (1.02, 0.24))],
          1.10),
    'L': ([_b((1.20, 1.52), (1.08, 1.82), (0.66, 1.86), (0.58, 1.50)) +
           _b((0.58, 1.50), (0.50, 1.10), (0.60, 0.56), (0.42, 0.24)) +
           _b((0.42, 0.24), (0.26, -0.04), (0.06, 0.10), (0.14, 0.32)) +
           _b((0.14, 0.32), (0.26, 0.58), (0.70, 0.36), (1.02, 0.26))],
          1.10),
}

# Tangent of the pen angle.  At 0.20 an ascender leans a third of an em to
# the right by the time it reaches the top, which walks it into the letter
# after it; 0.14 is a writing-master's slope and stays inside its own column.
SLANT = 0.14


def script_word(word, xh=1.0, tight=1.0):
    """The word as a list of (u, v) polylines, x-height 1, baseline 0.

    `tight` pulls each letter back a little so the exit stroke of one runs
    into the entry stroke of the next - which is what makes it a script and
    not a row of shapes."""
    out, pen = [], 0.0
    for ch in word:
        g = _SCRIPT.get(ch)
        if g is None:
            pen += 0.5
            continue
        strokes, adv = g
        for st in strokes:
            out.append([((u + pen + v * SLANT) * xh, v * xh) for (u, v) in st])
        pen += adv * tight
    w = max(p[0] for st in out for p in st) - min(p[0] for st in out
                                                 for p in st)
    cx = 0.5 * (max(p[0] for st in out for p in st) +
                min(p[0] for st in out for p in st))
    return [[(u - cx, v) for (u, v) in st] for st in out], w


def neon_script(name, word, x, y, z, xh, colour, facing, cname=C,
                rad=0.0085, strength=24.0, fit=None):
    """A neon word in joined-up script, standing off a wall.

    `xh` is the x-height in metres; `fit`, if given, is the width the word
    must not exceed, and the x-height is reduced until it does not - a sign
    that runs off the end of the panel it is fixed to is the one thing a
    real signwriter never delivers."""
    paths, w = script_word(word, 1.0)
    if fit and w * xh > fit:
        xh = fit / w
    paths = [[(u * xh, v * xh) for (u, v) in st] for st in paths]
    ob = _neon_tubes(name, paths, 1.0, x, y, z, facing, colour, cname, rad,
                     strength=strength)
    return [ob]


def service_sign(name, x, y, z, cname=C, w=1.58, h=0.40, top=None):
    """The red SERVICE arrow, pointing west.

    It hangs on two short rods from the cross beam - it is not fixed to a
    wall.  `top` is the height its hangers reach up to; left unset they run
    all the way to the ceiling, which is only right if nothing is in the
    way."""
    m = mats()
    # The plate is a double-ended chevron: a broad arrow head at the pointing
    # end and a shallower one at the tail, which is what the sign on the set
    # is.  It carries a pale pinstripe just inside its edge, so the plate is
    # built twice - a cream ground and a red field inset into it - rather
    # than painted on, because a stripe with no thickness is a texture and
    # everything here is geometry.
    out_poly = M.ccw([(-w / 2, -h / 2), (-w / 2 + h * 0.42, 0.0),
                      (-w / 2, h / 2), (w / 2 - h * 0.92, h / 2),
                      (w / 2, 0.0), (w / 2 - h * 0.92, -h / 2)])
    board = M.prism_xz(name + "_b", out_poly, -0.014, 0.014, cname)
    M.bevel(board, 0.004, 2, 50)
    M.set_mat(board, m['cream'])
    field = M.prism_xz(name + "_fld", M.poly_offset(out_poly, -0.030),
                       -0.019, 0.019, cname)
    M.bevel(field, 0.003, 2, 50)
    M.set_mat(field, m['red'])
    # the arrow points west, so mirror the plate
    M.scale_mesh(board, (-1, 1, 1))
    M.scale_mesh(field, (-1, 1, 1))
    # the lettering sits on the shaft of the arrow, clear of the point and
    # of the swallowtail, and is squeezed to whatever is left
    fieldw = w - h * 0.92 - h * 0.55
    txt = _text_mesh(name + "_t", "SERVICE", h * 0.62, cname=cname,
                     extrude=0.006)
    _fit_x(txt, fieldw)
    M.rot_x(txt, math.radians(90))
    M.translate(txt, (h * 0.20, -0.022, 0.0))
    M.set_mat(txt, m['yellow'])
    txt2 = _text_mesh(name + "_t2", "SERVICE", h * 0.62, cname=cname,
                      extrude=0.006)
    _fit_x(txt2, fieldw)
    M.rot_x(txt2, math.radians(90))
    M.rotate_z(txt2, math.pi)
    M.translate(txt2, (h * 0.20, 0.022, 0.0))
    M.set_mat(txt2, m['yellow'])
    hang = []
    ztop = (L.CZ if top is None else top) - z
    for s in (-1, 1):
        c = M.tube_along(name + "_ch%d" % s,
                         [(s * w * 0.30, 0.0, h * 0.42),
                          (s * w * 0.30, 0.0, ztop)],
                         M.circle(0.005, 6), cname=cname, up=(0, 0, 1))
        hang.append(c)
        # an eye where the rod passes through the plate, so it hangs off
        # something rather than being skewered by a wire
        ey = M.revolve(name + "_ey%d" % s,
                       [(0.005, h * 0.40), (0.018, h * 0.40),
                        (0.018, h * 0.46), (0.005, h * 0.46)],
                       segments=10, cname=cname)
        M.translate(ey, (s * w * 0.30, 0.0, 0.0))
        hang.append(ey)
    oh = M.join(hang, name + "_chain", cname); M.set_mat(oh, m['iron'])
    out = [board, field, txt, txt2, oh]
    for o in out:
        M.translate(o, (x, y, z))
    return out


# ------------------------------------------------------------------ pictures

def painting(name, x, y, z, w, facing, path, cname=C, ratio=1.0):
    """The Statue of Liberty canvas on the north wall, in a plain dark
    frame.  One of the two bitmaps the brief allows.

    Square by default, because the artwork is: stretched to 1.3:1 the print
    lands on the canvas cropped top and bottom and the whole thing reads as
    a poster rather than as the painting on the set."""
    m = mats()
    h = w / ratio
    canvas = M.grid_plane(name + "_c", [(-w / 2, -h / 2), (w / 2, -h / 2),
                                        (w / 2, h / 2), (-w / 2, h / 2)],
                          0.0, 2, 2, cname)
    M.rot_x(canvas, math.radians(90))
    # UVs so the image lands square on the canvas
    me = canvas.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((v.x + w / 2) / w, (v.z + h / 2) / h)
    M.set_mat(canvas, T.img_mat(name + "_img", path, rough=0.62))
    fr = M.sweep_rect_frame(name + "_f", w + 0.055, h + 0.055,
                            [(0.0, -0.030), (0.048, -0.034), (0.052, 0.016),
                             (0.0, 0.020)], cname=cname)
    M.set_mat(fr, m['wood'])
    ang = math.atan2(facing[1], facing[0]) + math.pi / 2
    out = [canvas, fr]
    for o in out:
        M.rotate_z(o, ang)
        M.translate(o, (x + facing[0] * 0.028, y + facing[1] * 0.028, z))
    return out


def decal(name, x, y, z, w, facing, path, cname=C, ratio=1.5):
    """The Central Perk transfer on the shop window: a cut-out with alpha,
    facing the street, so it reads reversed from inside as it does on set.

    `ratio` is the ARTWORK's aspect, and it has to be the artwork's actual
    aspect: central_perk_sticker.png is 1536 x 1024, i.e. 1.5, and forcing it
    to 2.1 squashed the whole sign by 40 per cent vertically - the cups went
    oval and the lettering went condensed."""
    h = w / ratio
    pl = M.grid_plane(name, [(-w / 2, -h / 2), (w / 2, -h / 2),
                             (w / 2, h / 2), (-w / 2, h / 2)], 0.0, 2, 2, cname)
    M.rot_x(pl, math.radians(90))
    me = pl.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers[0].data
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((v.x + w / 2) / w, (v.z + h / 2) / h)
    M.set_mat(pl, T.img_mat(name + "_img", path, alpha=True, rough=0.40))
    M.rotate_z(pl, math.atan2(facing[1], facing[0]) + math.pi / 2)
    M.translate(pl, (x, y, z))
    return [pl]


# ------------------------------------------------------------------ curtains

def curtain(name, p0, p1, ztop, zbot, cname=C, folds=9, depth=0.055,
            mat='curtain', gathered=0.62):
    """A hung curtain: a rippled sheet, wider than its opening so the folds
    are real gathers and not a corrugated plane."""
    m = mats()
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    ll = math.hypot(ux, uy) or 1.0
    ux, uy = ux / ll, uy / ll
    nx, ny = uy, -ux
    n = folds * 8
    rings = []
    for j in range(11):
        t = j / 10.0
        z = ztop - (ztop - zbot) * t
        ring = []
        for i in range(n + 1):
            u = i / n
            ph = u * folds * TAU
            # gathers deepen toward the top where the tape is
            amp = depth * (0.55 + 0.45 * (1.0 - t)) * math.sin(ph)
            s = u * ll * gathered + ll * (1 - gathered) * 0.5
            ring.append((p0[0] + ux * s + nx * amp,
                         p0[1] + uy * s + ny * amp,
                         z - 0.02 * math.sin(u * math.pi * 3) * t))
        rings.append(ring)
    ob = M._loft(name, rings, close_u=False, close_v=False, cname=cname)
    M.solidify(ob, 0.006, offset=0)
    M.smooth_shade(ob, 50)
    M.set_mat(ob, m[mat])
    return ob


# -------------------------------------------------------------- plants etc.

def _petal(name, ln, wd, cup, cname=CD, n=7):
    """One petal: a cupped blade lying in the XY plane, rooted at the origin
    and pointing along +Y, with a lens-shaped section so it has a visible
    thickness and an edge that catches light."""
    rings = []
    for i in range(n):
        t = i / (n - 1.0)
        w = wd * math.sin(math.pi * min(1.0, 0.10 + t * 0.92)) ** 0.62
        z = cup * t * t
        th = 0.0016 * (1.0 - 0.7 * t)
        rings.append([(-w, ln * t, z * 0.45), (0.0, ln * t, z + th),
                      (w, ln * t, z * 0.45), (0.0, ln * t, z - th)])
    ob = M._loft(name, rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)
    M.smooth_shade(ob, 50)
    return ob


def _vase(name, r, h, cname=CD, colour=None):
    """A short vase for a table arrangement.

    Flowers standing on a table with nothing at the foot of them look like
    they are growing out of it - which is exactly what the first pass did.
    A real posy is gathered into a squat glass or a pot; the stems have to
    disappear into something at the point they meet the surface."""
    prof = [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.68, 0.020),
            (r * 0.92, h * 0.34), (r * 0.98, h * 0.60), (r * 0.86, h * 0.88),
            (r * 0.80, h), (r * 0.73, h), (r * 0.79, h * 0.88),
            (r * 0.91, h * 0.60), (r * 0.85, h * 0.34), (r * 0.60, 0.030),
            (0.0, 0.030)]
    ob = M.revolve(name, prof, segments=26, cname=cname)
    M.smooth_shade(ob, 40)
    m = mats()
    M.set_mat(ob, T.paint(name + "_m", colour, rough=0.22, coat=0.5)
              if colour else m['glass'] if 'glass' in m else
              T.glass(name + "_g", tint='E6EEE8', rough=0.05))
    return ob


def bouquet(name, x, y, z, r=0.30, h=0.52, cname=CD, nstem=34, vase=None,
            colours=('E2621F', 'E8A41C', 'D8324A', 'EFE0C0')):
    """A big loose arrangement.  Every stem is a swept tube with a head of
    petals on it; done as a noise-blob it reads as moss."""
    m = mats()
    stems, heads = [], {}
    for i in range(nstem):
        a = TAU * (i * 0.618) % TAU
        t = (i % 7) / 6.0
        rr = r * (0.30 + 0.70 * t)
        # Heads have to finish on a dome, not on a range of heights: with the
        # tips spread over half the arrangement's height and the stems ruler
        # straight, every flower read as a lollipop on a stick.  Tight height
        # spread, a real curve to the stem, and thinner stalks fix it.
        hh = h * (0.80 + 0.20 * ((i * 3) % 5) / 4.0) * (1.0 - 0.30 * t * t)
        lean = 0.55 + 0.75 * t
        bend = 0.12 * t
        pts = []
        # With a vase, every stem starts BELOW its mouth and stays inside the
        # neck until it is clear of the rim.  Fanned from the table top the
        # way they were, the outer stems left the glass through its side
        # halfway up - a bunch of flowers spearing its own vase.
        vh = vase[1] if vase else 0.0
        vm = (vase[0] * 0.74) if vase else 0.0
        z0 = vh * 0.14
        for k in range(9):
            u = k / 8.0
            zz = z0 + (hh - z0) * u ** 0.72
            g = max(0.0, min(1.0, (zz - vh * 0.96) / max(1e-6, hh * 0.40)))
            g = g * g * (3 - 2 * g)
            rad = rr * lean * u * g + max(0.0, u - 0.15) * vm * 0.55
            rad = min(rad, vm) if zz < vh else rad
            pts.append((rad * math.cos(a) + bend * u * u * g * math.cos(a + 1.2),
                        rad * math.sin(a) + bend * u * u * g * math.sin(a + 1.2),
                        zz))
        st = M.tube_along(name + "_s%d" % i, pts, M.circle(0.0032, 5),
                          cname=cname, up=(0, 0, 1))
        stems.append(st)
        cidx = i % len(colours)
        tip = pts[-1]
        head = []
        # Three whorls of real petals.  They used to be full revolves of a
        # little profile - which is a DOME, not a petal - and seventeen domes
        # in a cluster is why every arrangement in the room read as coral.  A
        # petal is a cupped blade: it widens, curls up at the edges, comes to
        # a rounded point, and has a section you can see the thickness of.
        for ring, (np_, rad, tilt, lift) in enumerate(
                ((8, 0.030, 62, 0.0), (7, 0.024, 40, 0.010),
                 (5, 0.016, 20, 0.019), (3, 0.010, 6, 0.026))):
            for p in range(np_):
                pa = TAU * p / np_ + ring * 0.42
                pet = _petal(name + "_p%d_%d_%d" % (i, ring, p), rad,
                             rad * 0.62, rad * 0.34, cname)
                M.rot_x(pet, math.radians(90 - tilt))
                M.rotate_z(pet, pa)
                M.translate(pet, (tip[0] + rad * 0.16 * math.cos(pa),
                                  tip[1] + rad * 0.16 * math.sin(pa),
                                  tip[2] + lift))
                head.append(pet)
        heads.setdefault(cidx, []).extend(head)
    ost = M.join(stems, name + "_stems", cname); M.set_mat(ost, m['stem'])
    out = [ost]
    if vase:
        vr, vh, vcol = vase
        out.append(_vase(name + "_v", vr, vh, cname=cname, colour=vcol))
    for cidx, lst in heads.items():
        o = M.join(lst, name + "_h%d" % cidx, cname)
        M.set_mat(o, T.petal('petal_%s' % colours[cidx], colours[cidx]))
        out.append(o)
    for o in out:
        M.translate(o, (x, y, z))
    return out


def urn_planter(name, x, y, z, r=0.24, h=0.60, cname=CD, colour='4E6B4A'):
    m = mats()
    body = M.revolve(name + "_b",
                     [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.66, 0.030),
                      (r * 0.82, 0.110), (r * 0.98, 0.300), (r, 0.430),
                      (r * 0.92, h - 0.070), (r * 0.98, h - 0.030),
                      (r * 1.03, h), (r * 0.94, h), (r * 0.88, h - 0.040),
                      (r * 0.86, 0.120), (r * 0.54, 0.030), (0.0, 0.030)],
                     segments=30, cname=cname)
    M.smooth_shade(body, 38)
    M.set_mat(body, T.paint(name + "_m", colour, rough=0.40, coat=0.25,
                            bump=0.10))
    M.translate(body, (x, y, z))
    return [body]


def potted(name, x, y, z, r=0.24, ph=0.40, sp=0.95, cname=CD):
    """A leafy floor plant: terracotta pot, then fronds swept from the crown."""
    m = mats()
    pot = M.revolve(name + "_p",
                    [(0.0, 0.0), (r * 0.66, 0.0), (r * 0.70, 0.020),
                     (r * 0.92, ph - 0.070), (r, ph - 0.040),
                     (r * 1.05, ph), (r * 0.96, ph), (r * 0.92, ph - 0.040),
                     (r * 0.62, 0.030), (0.0, 0.030)], segments=24, cname=cname)
    M.smooth_shade(pot, 38)
    M.set_mat(pot, T.paint(name + "_pm", '8A4A32', rough=0.72, bump=0.22))
    fronds = []
    for i in range(16):
        a = TAU * (i * 0.618) % TAU
        t = (i % 5) / 4.0
        ln = sp * (0.55 + 0.45 * t)
        pts, wid = [], []
        for k in range(7):
            u = k / 6.0
            pts.append((ln * 0.62 * u * math.cos(a), ln * 0.62 * u * math.sin(a),
                        ph + ln * (u - 0.55 * u * u)))
            wid.append(0.055 * math.sin(math.pi * min(1.0, u * 1.15)) + 0.006)
        rings = []
        for p, ww in zip(pts, wid):
            rings.append([(p[0] + ww * math.cos(a + math.pi / 2) * cc,
                           p[1] + ww * math.sin(a + math.pi / 2) * cc,
                           p[2] + ww * 0.16 * (1 - abs(cc)))
                          for cc in (-1.0, -0.4, 0.0, 0.4, 1.0)])
        fr = M._loft(name + "_f%d" % i, rings, close_u=False, close_v=False,
                     cname=cname)
        M.solidify(fr, 0.003, offset=0)
        M.smooth_shade(fr, 50)
        fronds.append(fr)
    of = M.join(fronds, name + "_leaves", cname); M.set_mat(of, m['leaf'])
    for o in (pot, of):
        M.translate(o, (x, y, z))
    return [pot, of]


# --------------------------------------------------------------- tabletop

def cup(name, x, y, z, cname=CD, colour='EDE8DC', saucer=True, rot=0.0):
    """A cup, measured rather than guessed.

    The first one was 92 mm across and 66 mm tall - wider than it was high,
    which is a sugar bowl, not a cup.  A china cup of the sort on this set is
    about 82 mm across the rim and 92 mm to it, on a 68 mm foot, with a wall
    that thins from 5 mm at the foot to 3 mm at the rim and a rounded lip.

    The handle is an arc with a strap section, swept about the axis normal to
    its own plane.  Two things had to be right and neither was: swept with
    up = +Z the frame goes singular where the path turns vertical, so the
    tube collapsed into a flat twisted bracket; and its ends have to finish
    INSIDE the cup wall, or the flat end caps show as slivers sticking out of
    the side - which is the spur in the last render."""
    m = mats()
    parts = []
    RIM, FOOT, HT = 0.0410, 0.0345, 0.092
    c = M.revolve(name + "_c",
                  [(0.0, 0.0), (0.0250, 0.0), (0.0320, 0.0035),
                   (FOOT, 0.0090), (0.0362, 0.0260), (0.0392, 0.0620),
                   (RIM, 0.0860), (0.0409, HT - 0.0015), (0.0398, HT),
                   (0.0384, HT - 0.0020), (0.0378, 0.0840),
                   (0.0358, 0.0560), (0.0326, 0.0200), (0.0300, 0.0140),
                   (0.0, 0.0140)], segments=28, cname=cname)
    M.smooth_shade(c, 44); parts.append(c)
    # The two ends land 1 mm inside the OUTER surface at the height they meet
    # it (r 0.0390 at z 0.080, r 0.0355 at z 0.030), and both end tangents
    # point into the cup, so each flat cap is buried in the wall.  A circular
    # arc cannot do that on a 3 mm wall - it either stops short in mid air or
    # runs out through the inside of the bowl.
    hp2 = (M.bez((0.0390, 0.0800), (0.0620, 0.0836), (0.0706, 0.0704),
                 (0.0706, 0.0552), 10)
           + M.bez((0.0706, 0.0552), (0.0706, 0.0398), (0.0602, 0.0300),
                   (0.0355, 0.0300), 10, skip_first=True))
    hp = [(u, 0.0, v) for (u, v) in hp2]
    sec = [(0.0068 * math.cos(t), 0.0036 * math.sin(t))
           for t in [k * TAU / 12 for k in range(12)]]
    hd = M.tube_along(name + "_h", hp, sec, cname=cname, up=(0, 1, 0))
    M.smooth_shade(hd, 46); parts.append(hd)
    if saucer:
        s = M.revolve(name + "_s",
                      [(0.0, 0.0), (0.0300, 0.0), (0.0400, 0.0025),
                       (0.0640, 0.0090), (0.0680, 0.0135), (0.0672, 0.0158),
                       (0.0620, 0.0128), (0.0430, 0.0075), (0.0300, 0.0062),
                       (0.0, 0.0058)], segments=28, cname=cname)
        M.smooth_shade(s, 40); parts.append(s)
        M.translate(c, (0, 0, 0.0062)); M.translate(hd, (0, 0, 0.0062))
    ob = M.join(parts, name, cname)
    M.set_mat(ob, T.paint('china_' + colour, colour, rough=0.14, coat=0.55))
    if rot:
        M.rotate_z(ob, math.radians(rot))
    M.translate(ob, (x, y, z))
    return [ob]


def book(name, x, y, z, w=0.16, d=0.23, t=0.028, colour='7A2A22', rot=0.0,
         cname=CD):
    m = mats()
    cover = M.prism(name + "_c", M.rounded_rect(w, d, 0.004, seg=2), 0.0, t,
                    cname)
    M.bevel(cover, 0.002, 2, 55)
    M.set_mat(cover, T.paint('book_' + colour, colour, rough=0.46, coat=0.15))
    # the block sits INSIDE the boards on every side - a 1 mm reveal is under
    # the audit tolerance and reads as a z-fight rather than as a fore-edge
    pg = M.prism(name + "_p", M.rounded_rect(w - 0.016, d - 0.013, 0.003, seg=2),
                 0.004, t - 0.004, cname)
    M.translate(pg, (0.004, 0.0, 0.0))
    M.set_mat(pg, m['paper'])
    out = [cover, pg]
    for o in out:
        if rot:
            M.rotate_z(o, math.radians(rot))
        M.translate(o, (x, y, z))
    return out


def guitar(name, x, y, z, rot=0.0, lean=14.0, cname=CD):
    """The acoustic leaning by the entrance."""
    m = mats()
    body_pts = []
    for i in range(52):
        t = i / 52.0
        a = TAU * t
        # two lobes: a figure-of-eight waist
        rr = 0.170 + 0.052 * math.cos(2 * a) - 0.020 * math.cos(4 * a)
        body_pts.append((rr * math.sin(a) * 0.86, rr * math.cos(a) * 1.28))
    rings = []
    for (o, dz) in ((-0.020, 0.0), (0.0, 0.014), (0.0, 0.086), (-0.020, 0.100)):
        p = M.poly_offset(body_pts, o)
        rings.append([(px, dz, py) for (px, py) in p])
    bd = M._loft(name + "_b", rings, close_u=False, close_v=True, cname=cname,
                 cap_start=True, cap_end=True)
    M.smooth_shade(bd, 40)
    neck = M.box(name + "_n", -0.026, 0.030, 0.215, 0.026, 0.078, 0.700, cname)
    M.bevel(neck, 0.008, 2, 50)
    head = M.box(name + "_h", -0.038, 0.030, 0.690, 0.038, 0.074, 0.800, cname)
    M.bevel(head, 0.005, 2, 50)
    hole = M.revolve(name + "_o", [(0.044, 0.0), (0.050, 0.0), (0.050, 0.004),
                                   (0.044, 0.004)], segments=22, cname=cname)
    M.rot_x(hole, math.radians(-90)); M.translate(hole, (0, 0.084, 0.30))
    ob = M.join([bd, neck, head, hole], name, cname)
    M.set_mat(ob, T.wood('guitar_spruce', light='D9B577', dark='A07E44',
                         ring=40.0, scale=0.6))
    M.rot_x(ob, math.radians(lean))
    M.rotate_z(ob, math.radians(rot))
    M.translate(ob, (x, y, z))
    return [ob]


def cone_pendant(name, x, y, z, ztop, cname=C, energy=0.0, r=0.20,
                 colour='1F4032'):
    """The green enamel shade hanging over the counter.  Enamel is white
    inside, which is half of why these throw such a hard pool of light - so
    the shade is a solid with two materials rather than a single-sided cone."""
    m = mats()
    prof = [(0.030, 0.150), (0.052, 0.140), (r * 0.86, 0.048), (r, 0.0),
            (r, -0.012), (r * 0.84, 0.040), (0.046, 0.130), (0.028, 0.140)]
    sh = M.revolve(name + "_sh", prof, segments=30, cname=cname)
    M.smooth_shade(sh, 40)
    M.set_mat(sh, T.paint(name + "_enamel", colour, rough=0.20, coat=0.45))
    inner = M.revolve(name + "_in",
                      [(0.028, 0.138), (0.046, 0.128), (r * 0.83, 0.038),
                       (r * 0.99, -0.002)], segments=30, cname=cname,
                      cap_start=False, cap_end=False)
    M.smooth_shade(inner, 40)
    M.set_mat(inner, m['enamel_lit'])
    rod = M.tube_along(name + "_rod", [(0, 0, 0.145), (0, 0, ztop - z)],
                       M.circle(0.008, 8), cname=cname, up=(0, 0, 1))
    M.set_mat(rod, m['brass_dk'])
    bulb = M.revolve(name + "_bulb",
                     [(0.0, 0.020), (0.026, 0.006), (0.030, -0.020),
                      (0.022, -0.044), (0.0, -0.050)], segments=14, cname=cname)
    M.set_mat(bulb, m['bulb_lit'])
    out = [sh, inner, rod, bulb]
    for o in out:
        M.translate(o, (x, y, z))
    out.append(_light(name + "_lamp", 'POINT', energy, (x, y, z - 0.045),
                      color=(1.0, 0.83, 0.60), radius=0.10, cname=cname))
    return out


def tiffany_pendant(name, x, y, z, ztop, cname=C, energy=0.0, r=0.26):
    """The leaded amber shade over the main seating.  Its panels are real
    facets, so it breaks the light up the way the set piece does."""
    m = mats()
    prof = [(0.038, 0.210), (0.090, 0.190), (0.160, 0.140), (0.215, 0.075),
            (r, 0.010), (r * 1.02, -0.006)]
    seg, rings = 20, []
    for s in range(seg):
        a = TAU * s / seg
        k = 1.0 + 0.028 * math.cos(seg * a * 0.5) - 0.012
        rings.append([(rr * k * math.cos(a), rr * k * math.sin(a), zz)
                      for (rr, zz) in prof])
    sh = M._loft(name + "_sh", rings, close_u=True, close_v=False, cname=cname,
                 cap_start=False, cap_end=False)
    M.solidify(sh, 0.006, offset=0)
    M.flat_shade(sh)
    M.set_mat(sh, T.lampshade(name + "_amber", 'B87322', 'FF9A2E',
                              strength=2.2, rough=0.16, transm=0.34))
    cap = M.revolve(name + "_cap", [(0.0, 0.232), (0.040, 0.226),
                                    (0.044, 0.204), (0.0, 0.200)],
                    segments=18, cname=cname)
    M.set_mat(cap, m['brass_dk'])
    ch = M.tube_along(name + "_ch", [(0, 0, 0.230), (0, 0, ztop - z)],
                      M.circle(0.007, 7), cname=cname, up=(0, 0, 1))
    M.set_mat(ch, m['brass_dk'])
    bulb = M.revolve(name + "_bulb",
                     [(0.0, 0.150), (0.030, 0.132), (0.034, 0.100),
                      (0.024, 0.072), (0.0, 0.064)], segments=14, cname=cname)
    M.set_mat(bulb, m['bulb_lit'])
    out = [sh, cap, ch, bulb]
    for o in out:
        M.translate(o, (x, y, z))
    out.append(_light(name + "_lamp", 'POINT', energy, (x, y, z - 0.010),
                      color=(1.0, 0.76, 0.48), radius=0.13, cname=cname))
    return out


def table_lamp(name, x, y, z, cname=C, energy=0.0, h=0.52):
    """A small shaded lamp for a side table - the one on the bay table in the
    reference, which is most of the warm light in that corner."""
    m = mats()
    base = M.revolve(name + "_b",
                     [(0.0, 0.0), (0.085, 0.004), (0.080, 0.020),
                      (0.036, 0.050), (0.028, 0.120), (0.034, 0.150),
                      (0.026, 0.180), (0.014, h - 0.180), (0.0, h - 0.180)],
                     segments=20, cname=cname)
    M.smooth_shade(base, 40); M.set_mat(base, m['brass'])
    sh = M.revolve(name + "_s",
                   [(0.072, h - 0.010), (0.128, h - 0.185),
                    (0.130, h - 0.192), (0.074, h - 0.017)],
                   segments=24, cname=cname, cap_start=False, cap_end=False)
    M.smooth_shade(sh, 44)
    M.set_mat(sh, T.lampshade(name + "_shade", 'D6B078', 'FFC888',
                              strength=4.2, rough=0.70, transm=0.45))
    out = [base, sh]
    for o in out:
        M.translate(o, (x, y, z))
    out.append(_light(name + "_lamp", 'POINT', energy,
                      (x, y, z + h - 0.115), color=(1.0, 0.74, 0.46),
                      radius=0.055, cname=cname))
    return out
