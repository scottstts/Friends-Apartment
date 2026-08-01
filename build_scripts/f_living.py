"""Living room: slipcovered sofa and armchair, slipper chair, velvet ottoman,
limed-oak coffee table, wrought-iron glass table, Aubusson rug, art-deco
waterfall credenza with the CRT and the Jouets poster, window seat, drapes,
lamps, plants."""
import bpy, math, random
from mathutils import Matrix, Vector
import mlib, mats, L, props as P

C = "Living"


# ------------------------------------------------------------------ materials
def mk_mats():
    M = {}
    # Both couches on the set are plain cream slipcovers - the jacquard is only
    # a whisper of tone-on-tone, and at any real contrast it reads as wood grain
    # across the arms.
    M['damask'] = mats.damask('fabric_damask_cream', base='C3B795',
                              motif='BEB290', scale=2.4, rough=0.80, sheen=0.24)
    M['cream'] = mats.fabric('fabric_cream_plain', 'C6BC9E', rough=0.82,
                             sheen=0.65, weave=560, blotch=0.05)
    # the slipper chair reads as a pale warm pink on the set, not the greyish
    # tan it was: next to the cream sofa the old value had no hue of its own
    M['blush'] = mats.fabric('fabric_blush', 'D3AE9F', rough=0.84, sheen=0.7,
                             weave=620)
    M['velvet_g'] = mats.velvet('velvet_teal', '1B5240')
    M['throw'] = mats.floral_chintz('chintz_throw', ground='C6AC6A',
                                    petal='A8705E', petal2='D8BE8E',
                                    leaf='6A6038', leaf2='9C8A54', scale=4.6,
                                    rough=0.86, ground2='AE8C46')
    # at scale 1.7 the motifs were a metre across and read as polka dots
    M['drape'] = mats.floral_chintz('chintz_drape', ground='B8AE90',
                                    petal='6B3543', petal2='8E5750',
                                    leaf='2E3A24', leaf2='5A6438', scale=4.4,
                                    rough=0.86)
    # The window seat and the console under it are dark in every set photo;
    # at the old value they read as painted MDF rather than timber.
    LIM = ('997F55', '82683F', '65502F')
    LK = dict(ring=15.0, warp=0.14, warp_scale=1.4, distort=0.9, bump=0.06,
              rough=(0.32, 0.52), grain_relief=0.30)
    M['limed'] = mats.wood('wood_limed_oak', LIM, axis='YZ', **LK)
    M['limed_y'] = mats.wood('wood_limed_oak_y', LIM, axis='XZ', **LK)
    M['limed_v'] = mats.wood('wood_limed_oak_v', LIM, axis='XY', **LK)
    # the coffee table is chunky honey pine, distinctly warmer than the rest
    PIN = ('D3A76E', 'BC8B4E', '9A6C36')
    PK = dict(ring=17.0, warp=0.20, warp_scale=1.3, distort=1.6, bump=0.07,
              rough=(0.30, 0.48))
    M['pine'] = mats.wood('wood_pine_coffee', PIN, axis='YZ', **PK)
    M['pine_y'] = mats.wood('wood_pine_coffee_y', PIN, axis='XZ', **PK)
    M['pine_v'] = mats.wood('wood_pine_coffee_v', PIN, axis='XY', **PK)
    WAL = ('987646', '806038', '5E4326')      # figured walnut, not honey oak
    WK = dict(ring=13.0, warp=0.19, warp_scale=2.4, distort=1.1, blotch=0.16,
              bump=0.05, rough=(0.14, 0.26))
    M['walnut'] = mats.wood('wood_walnut_fig', WAL, axis='YZ', **WK)
    M['walnut_v'] = mats.wood('wood_walnut_fig_v', WAL, axis='XY', **WK)
    # turned legs on the ottoman and the slipper chair are dark stained wood in
    # the set photo; at the old value they glowed orange against the velvet
    M['honey'] = mats.wood('wood_honey_leg', ('A87C48', '7E5624', '4E3210'),
                           ring=56.0, warp=0.08, distort=1.0, bump=0.14,
                           rough=(0.18, 0.32), axis='XY')
    # the pair of drum stools are a muted plum tapestry, not the gold throw
    M['stool_tap'] = mats.floral_chintz('chintz_stool', ground='7E4E44',
                                        petal='9A6A5E', petal2='C09A82',
                                        leaf='4E4436', leaf2='7A6C4E',
                                        scale=9.0, rough=0.86)
    M['bakelite'] = mats.paint('bakelite_dark', '2B211B', rough=0.22, coat=0.5)
    M['pewter'] = mats.metal('metal_pewter', '6E6A62', rough=0.46, bump=0.28)
    # the glass table's base is painted a chalky off-white, not bare iron
    M['iron_pale'] = mats.paint('iron_pale', 'CFD2CC', rough=0.42, coat=0.18,
                                variation=0.09)
    M['brass'] = mats.get('metal_brass') or mats.metal('metal_brass', 'B08D3A')
    M['glass'] = mats.get('glass_clear') or mats.pane('glass_clear')
    M['crt'] = mats.paint('plastic_crt', '2A2724', rough=0.36, coat=0.3)
    # the set TV is a dark wood-cased CRT: a light grey bezel turned it into a
    # microwave sitting on the sideboard
    M['crt_bez'] = mats.paint('plastic_crt_bez', '2E2723', rough=0.40, coat=0.25)
    M['screen'] = mats.paint('crt_screen', '15181C', rough=0.06, coat=0.7)
    M['shade'] = mats.fabric('shade_cream', 'E9DCBC', rough=0.72, sheen=0.4,
                             weave=700)
    M['leaf'] = mats.foliage('plant_leaf', dark='24501F', light='5E8C3A')
    M['terra'] = mats.paint('terracotta', 'A8613C', rough=0.62, variation=0.05)
    M['wicker'] = mats.wood('wicker_basket', ('D3B078', 'B08B4C', '80612C'),
                            ring=900.0, warp=0.03, bump=0.5, rough=(0.5, 0.7))
    M['rug'] = rug_mat()
    M['poster'] = poster_mat()
    M['pillow_r'] = mats.fabric('fabric_red_pillow', '9E2225', rough=0.78, sheen=0.5)
    M['pillow_y'] = mats.fabric('fabric_yellow_pillow', 'E0B426', rough=0.78,
                                sheen=0.5)
    M['pillow_rust'] = mats.fabric('fabric_rust_pillow', 'B05A32', rough=0.8,
                                   sheen=0.5)
    M['gold'] = mats.fabric('fabric_champagne_pillow', 'C0AB7C', rough=0.74,
                            sheen=0.85, weave=380, blotch=0.09)
    # the armchair's pair are pale botanicals, not flat mint blocks
    M['sage'] = mats.floral_chintz('chintz_sage_pillow', ground='CEC9B2',
                                   petal='9AA882', petal2='B6BE9E',
                                   leaf='5E6E4A', leaf2='8C9A6E', scale=6.0,
                                   rough=0.84)
    M['check'] = mats.gingham()
    return M


def rug_mat(name='rug_aubusson'):
    """Aubusson: cream field with a scrolling ground, a floral garland border, a
    scalloped inner edge and a navy outer band - all driven by the distance to
    the rug edge (object space, so the rug mesh must stay centred)."""
    m = mats._mat(name)
    b = mats.NB(m)
    W, H = L.RUG_WH
    tc = b.n('ShaderNodeTexCoord', x=-2800)
    sp = b.n('ShaderNodeSeparateXYZ', x=-2640)
    b.l(tc, 'Object', sp, 'Vector')
    ax = b.math('ABSOLUTE', sp, 0, x=-2480)
    ay = b.math('ABSOLUTE', sp, 1, x=-2480)
    ay.location = (-2480, -200)
    dx = b.math('SUBTRACT', va=W * 0.5, b=ax, bo=0, x=-2320)
    dy = b.math('SUBTRACT', va=H * 0.5, b=ay, bo=0, x=-2320)
    dy.location = (-2320, -200)
    d = b.math('MINIMUM', dx, 0, dy, 0, x=-2160)
    # Perimeter parameter -> the leafy edge where the cream field bites into the
    # navy band.  On the original that edge is a row of pointed petals about
    # 9 cm apart, riding on a slower swell - a single high-frequency sine with a
    # hard ramp behind it just reads as a saw-tooth, so two are summed here and
    # the ramp behind them is soft enough to keep the tips organic.
    per = b.math('ADD', sp, 0, sp, 1, x=-2480)
    per.location = (-2480, 300)
    ps = b.math('MULTIPLY', per, 0, vb=39.0, x=-2320)
    ps.location = (-2320, 300)
    sn = b.math('SINE', ps, 0, x=-2160)
    sn.location = (-2160, 300)
    sm = b.math('MULTIPLY', sn, 0, vb=0.011, x=-2000)
    sm.location = (-2000, 300)
    ps2 = b.math('MULTIPLY', per, 0, vb=11.0, x=-2320)
    ps2.location = (-2320, 160)
    sn2 = b.math('SINE', ps2, 0, x=-2160)
    sn2.location = (-2160, 160)
    sm2 = b.math('MULTIPLY', sn2, 0, vb=0.010, x=-2000)
    sm2.location = (-2000, 160)
    lobes = b.math('ADD', sm, 0, sm2, 0, x=-1920)
    lobes.location = (-1920, 230)
    # a little noise on top so the petal tips are hand-cut, not machined
    jt = b.noise((tc, 'Object'), scale=7.0, detail=3.0, x=-2160)
    jt.location = (-2160, 20)
    jc = b.math('SUBTRACT', jt, 'Fac', vb=0.5, x=-2000)
    jc.location = (-2000, 20)
    js = b.math('MULTIPLY', jc, 0, vb=0.022, x=-1920)
    js.location = (-1920, 20)
    lob2 = b.math('ADD', lobes, 0, js, 0, x=-1880)
    lob2.location = (-1880, 130)
    dmod = b.math('ADD', d, 0, lob2, 0, x=-1840)

    navy = b.ramp(dmod, 0, [(0.118, (0, 0, 0)), (0.158, (1, 1, 1))], x=-1680)
    band = b.ramp(dmod, 0, [(0.140, (0, 0, 0)), (0.170, (1, 1, 1)),
                            (0.400, (1, 1, 1)), (0.450, (0, 0, 0))], x=-1680)
    band.location = (-1680, -320)

    mp = b.mapping(tc, 'Object', scale=(1.0, 1.0, 1.0), x=-2480)
    mp.location = (-2480, -560)
    wn = b.noise((mp, 'Vector'), scale=2.2, detail=4.0, rough=0.55, x=-2320)
    wn.location = (-2320, -560)
    wv = b.n('ShaderNodeVectorMath', x=-2160, y=-560, operation='MULTIPLY_ADD')
    b.l(wn, 'Color', wv, 0)
    wv.inputs[1].default_value = (0.14, 0.14, 0.14)
    b.l(mp, 'Vector', wv, 2)
    VSC = 6.4
    vo = b.n('ShaderNodeTexVoronoi', x=-2000, y=-560)
    vo.inputs['Scale'].default_value = VSC
    vo.inputs['Randomness'].default_value = 1.0
    b.l(wv, 'Vector', vo, 'Vector')
    # The flower heads have to be drawn inside their own cell, off Position -
    # a plain distance ramp gives soft round dots, which is what the garland
    # read as: coloured blobs rather than blooms.
    off = b.n('ShaderNodeVectorMath', x=-1900, y=-700, operation='SUBTRACT')
    b.l(wv, 'Vector', off, 0)
    b.l(vo, 'Position', off, 1)
    rl = b.n('ShaderNodeVectorMath', x=-1760, y=-700, operation='LENGTH')
    b.l(off, 'Vector', rl, 0)
    dn = b.n('ShaderNodeVectorMath', x=-1760, y=-860, operation='NORMALIZE')
    b.l(off, 'Vector', dn, 0)
    pv = b.n('ShaderNodeTexVoronoi', x=-1620, y=-860)
    pv.inputs['Scale'].default_value = 2.6
    pv.inputs['Randomness'].default_value = 0.9
    b.l(dn, 'Vector', pv, 'Vector')
    R0 = 0.52 / VSC
    rth = b.math('MULTIPLY_ADD', pv, 'Distance', vb=-0.80 * R0, x=-1480)
    rth.location = (-1480, -860)
    rth.inputs[2].default_value = 1.22 * R0
    fd = b.math('SUBTRACT', rth, 0, rl, 'Value', x=-1340)
    fd.location = (-1340, -780)
    fl = b.ramp(fd, 0, [(0.0, (0, 0, 0)), (0.008, (1, 1, 1))], x=-1840)
    fl.location = (-1200, -780)
    # a continuous sage leaf ground under the blooms
    lfm = b.ramp(vo, 'Distance', [(0.34, (1, 1, 1)), (0.60, (0, 0, 0))], x=-1840)
    lfm.location = (-1840, -400)
    # faded Aubusson palette: sage, peach, dove blue, straw - never saturated
    fcol = b.ramp(vo, 'Color', [(0.12, mats.srgb('C4835A')),
                                (0.34, mats.srgb('93A078')),
                                (0.55, mats.srgb('C0A090')),
                                (0.78, mats.srgb('C6AC6A'))], x=-1840,
                  interp='CONSTANT')
    fcol.location = (-1840, -800)
    # Field: soft cloudy mottling only.  Any ring wave here - at whatever
    # distortion - draws concentric contours, and seen from above the middle of
    # the rug read as a slab of wood grain.  On the original the centre is very
    # nearly plain cream; all the drawing is in the garland and the medallion.
    dm = b.noise((wv, 'Vector'), scale=1.1, detail=3.0, rough=0.5, x=-2160)
    dm.location = (-2160, 440)
    scroll = b.ramp(dm, 'Fac', [(0.38, (0, 0, 0)), (0.64, (1, 1, 1))], x=-1840)
    scroll.location = (-1840, 440)
    field = b.mix(mats.srgb('D6CBA6'), 0, mats.srgb('CEC29D'), 0, scroll, 'Color',
                  x=-1520)
    field.location = (-1520, 440)

    # Central medallion and the line inside the garland.  Killing the old
    # contour-map scroll left the middle of the rug blank, but an Aubusson is
    # never blank: it carries an oval rosette in the centre with a thin scroll
    # ring around it.  Drawn from the radius, not from noise, so it is actual
    # drawing rather than texture.
    ex = b.math('DIVIDE', sp, 0, vb=1.00, x=-2320)
    ex.location = (-2320, 760)
    ey = b.math('DIVIDE', sp, 1, vb=1.45, x=-2320)
    ey.location = (-2320, 620)
    ex2 = b.math('MULTIPLY', ex, 0, ex, 0, x=-2180)
    ex2.location = (-2180, 760)
    ey2 = b.math('MULTIPLY', ey, 0, ey, 0, x=-2180)
    ey2.location = (-2180, 620)
    rsum = b.math('ADD', ex2, 0, ey2, 0, x=-2040)
    rsum.location = (-2040, 690)
    rad = b.math('SQRT', rsum, 0, x=-1900)
    rad.location = (-1900, 690)
    th = b.math('ARCTAN2', ey, 0, ex, 0, x=-2040)
    th.location = (-2040, 900)
    th8 = b.math('MULTIPLY', th, 0, vb=8.0, x=-1900)
    th8.location = (-1900, 900)
    lobe = b.math('COSINE', th8, 0, x=-1760)
    lobe.location = (-1760, 900)

    # rosette body
    rm = b.math('MULTIPLY_ADD', lobe, 0, vb=0.15 * 0.62, x=-1620)
    rm.location = (-1620, 900)
    rm.inputs[2].default_value = 0.62
    md = b.math('SUBTRACT', rm, 0, rad, 0, x=-1480)
    md.location = (-1480, 830)
    mmask = b.ramp(md, 0, [(0.0, (0, 0, 0)), (0.020, (1, 1, 1))], x=-1340)
    mmask.location = (-1340, 830)
    # its outline, plus a band either side of it that the garland flowers are
    # allowed into, so the medallion reads as a woven wreath rather than a
    # drawn-on vector line
    ro = b.math('MULTIPLY_ADD', lobe, 0, vb=0.09 * 0.74, x=-1620)
    ro.location = (-1620, 700)
    ro.inputs[2].default_value = 0.74
    rdif = b.math('SUBTRACT', rad, 0, ro, 0, x=-1480)
    rdif.location = (-1480, 700)
    rabs = b.math('ABSOLUTE', rdif, 0, x=-1400)
    rabs.location = (-1400, 700)
    oline = b.ramp(rabs, 0, [(0.008, (1, 1, 1)), (0.015, (0, 0, 0))], x=-1340)
    oline.location = (-1340, 700)
    mband = b.ramp(rabs, 0, [(0.030, (1, 1, 1)), (0.075, (0, 0, 0))], x=-1340)
    mband.location = (-1340, 560)

    f1 = b.mix(field, 'Result', mats.srgb('C9C39A'), 0, mmask, 'Color', x=-1240)
    f1.location = (-1240, 690)
    f2 = b.mix(f1, 'Result', mats.srgb('9CAA84'), 0, oline, 'Color', x=-1180)
    f2.location = (-1180, 620)
    field = f2
    # the flowers appear both in the border garland and in the medallion wreath
    zone = b.math('MAXIMUM', band, 'Color', mband, 'Color', x=-1260, clamp=True)
    zone.location = (-1260, -260)
    lmask = b.math('MULTIPLY', zone, 0, lfm, 'Color', x=-1360, clamp=True)
    lmask.location = (-1360, -400)
    gmask = b.math('MULTIPLY', zone, 0, fl, 'Color', x=-1200, clamp=True)
    gmask.location = (-1200, -320)
    c0 = b.mix(field, 'Result', mats.srgb('9CAA84'), 0, lmask, 0, x=-1120)
    c0.location = (-1120, 120)
    c1 = b.mix(c0, 'Result', fcol, 'Color', gmask, 0, x=-1000)
    c2 = b.mix(mats.srgb('141E2E'), 0, c1, 'Result', navy, 'Color', x=-820)
    fz = b.noise((mp, 'Vector'), scale=340.0, detail=4.0, x=-1200)
    fz.location = (-1200, -960)
    hh = b.math('ADD', gmask, 0, fz, 'Fac', x=-1000)
    hh.location = (-1000, -960)
    bmp = b.bump(hh, 0, strength=0.45, dist=0.009, x=-660)
    p = b.principled(base=c2, baseo='Result', rough=0.88, normal=bmp, sheen=0.10,
                     spec=0.20, x=-340)
    b.out(p)
    return m


def poster_mat(name='poster_jouets'):
    m = mats._mat(name)
    b = mats.NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1400)
    n = b.noise((tc, 'Object'), scale=90.0, detail=5.0, x=-1200)
    n2 = b.noise((tc, 'Object'), scale=6.0, detail=4.0, x=-1200)
    n2.location = (-1200, -300)
    col = b.mix(mats.srgb('E8DEBE'), 0, mats.srgb('D6C79E'), 0, n2, 'Fac', x=-960)
    bmp = b.bump(n, 'Fac', strength=0.10, dist=0.004, x=-760)
    p = b.principled(base=col, baseo='Result', rough=0.62, normal=bmp, spec=0.3,
                     x=-420)
    b.out(p)
    return m


# ---------------------------------------------------------------- upholstery
def _walk(poly, step=0.024):
    """Resample a closed polygon at a roughly constant spacing."""
    out = []
    n = len(poly)
    for i in range(n):
        a, c = poly[i], poly[(i + 1) % n]
        d = math.hypot(c[0] - a[0], c[1] - a[1])
        k = max(1, int(round(d / step)))
        for j in range(k):
            t = j / k
            out.append((a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t))
    return out


def skirt(name, poly, ztop, zbot=0.008, folds=34, depth=0.016, cname=C, mat=None):
    """Gathered slipcover skirt around a footprint polygon.  The footprint is
    resampled first - lofting the four bare corners of a rectangle gave five
    rings, so the fold count did nothing and the skirt read as a plain box."""
    poly = _walk(poly)
    n = len(poly)
    rings = []
    for i in range(n + 1):
        p = poly[i % n]
        ph = (i / n) * folds * math.tau
        amp = depth * (0.35 + 0.65 * (0.5 + 0.5 * math.sin(ph)))
        cx = sum(q[0] for q in poly) / n
        cy = sum(q[1] for q in poly) / n
        vx, vy = p[0] - cx, p[1] - cy
        ll = math.hypot(vx, vy) or 1.0
        rings.append([(p[0], p[1], ztop),
                      (p[0] + vx / ll * amp * 0.5, p[1] + vy / ll * amp * 0.5,
                       ztop - (ztop - zbot) * 0.55),
                      (p[0] + vx / ll * amp, p[1] + vy / ll * amp, zbot)])
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, 0.006, offset=0)
    mlib.smooth_shade(ob, 55)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def roll_arm(name, aw, h, dep, cname=C, mat=None, medallion=True, r=0.115):
    """English rolled arm.  Local: +X = across the seat depth, +Y = arm width,
    +Z = up.  Section drawn in XZ, extruded along Y."""
    sec = [(-dep * 0.5, 0.0), (dep * 0.5, 0.0), (dep * 0.5, h - r)]
    for i in range(1, 17):
        a = math.pi * i / 16.0
        sec.append((dep * 0.5 * math.cos(a), h - r + r * math.sin(a) * 1.03))
    sec.append((-dep * 0.5, h - r))
    ob = mlib.prism_xz(name, sec, 0.0, aw, cname)
    mlib.bevel(ob, 0.008, 2, 55)
    mlib.smooth_shade(ob, 42)
    out = [ob]
    if medallion:
        for yy, s in ((0.0, -1), (aw, 1)):
            md = mlib.revolve(name + "_md", [(0.0, 0.0), (r * 0.70, 0.004),
                                             (r * 0.78, 0.015), (r * 0.60, 0.026),
                                             (0.0, 0.028)], 20, cname=cname)
            mlib.rot_x(md, -s * math.pi / 2)
            mlib.translate(md, (0.0, yy, h - r))
            mlib.smooth_shade(md, 44)
            out.append(md)
    if mat:
        for o in out:
            mlib.set_mat(o, mat)
    return out


def _uphol_body(name, ln, dep, cname, seat_z=0.415, arm_z=0.630, back_z=0.850,
                aw=0.185, backt=0.22):
    """Common carcass for the sofa and armchair.  Local +X = front, +Y = length."""
    x0, x1 = -dep / 2, dep / 2
    y0, y1 = -ln / 2, ln / 2
    parts = []
    # back: soft-topped slab (lofted so the crown is rounded like a slipcover)
    rings = []
    for (dz, ex) in ((0.0, 0.0), (back_z - 0.215 - 0.10, 0.0),
                     (back_z - 0.215 - 0.045, 0.012), (back_z - 0.215 - 0.012, 0.006),
                     (back_z - 0.215, -0.030)):
        rings.append([(x0 - ex, y0 - ex * 0.5, 0.215 + dz),
                      (x0 + backt + ex, y0 - ex * 0.5, 0.215 + dz),
                      (x0 + backt + ex, y1 + ex * 0.5, 0.215 + dz),
                      (x0 - ex, y1 + ex * 0.5, 0.215 + dz)])
    body = mlib._loft(name + "_body", rings, close_u=False, close_v=True,
                      cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(body, 0.020, 2, 55)
    mlib.smooth_shade(body, 42)
    parts.append(body)
    deck = mlib.box(name + "_deck", x0 + backt - 0.02, y0, 0.215, x1 - 0.03, y1,
                    seat_z, cname)
    mlib.bevel(deck, 0.014, 2, 50)
    parts.append(deck)
    for yy in (y0, y1 - aw):
        # No scroll medallion on the arm ends.  Both couches on the set are
        # loose-slipcovered, so the arm reads as smooth cloth right round; the
        # rosette looked like an egg stuck to the side.
        arm = roll_arm(name + "_arm", aw, arm_z - 0.215, dep - 0.05, cname,
                       None, medallion=False, r=0.105)
        parts += arm
        for o in arm:
            mlib.translate(o, (0.0, yy, 0.215))
    # the slipcover skirt hangs from directly under the seat cushions - starting
    # it down at the deck rail left a dark recess along the whole front
    sk = skirt(name + "_skirt", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
               seat_z - 0.004, 0.006, max(20, int(ln * 26)), 0.034, cname, None)
    parts.append(sk)
    return parts, (x0, x1, y0, y1, seat_z, arm_z, back_z, aw, backt)


BACK_LEAN = math.radians(-6.0)


def _back_x(x0, backt, thick, h):
    """Local x for a back cushion so its top rear corner lands on the back
    rail's front face.  A back cushion that does not touch the rail reads as
    propped up on nothing, and at 12 degrees of lean its base stood 100 mm
    proud of the rail - so the lean is gentle and the offset is derived rather
    than guessed."""
    return x0 + backt + thick * 0.5 * math.cos(BACK_LEAN) \
        + h * abs(math.sin(BACK_LEAN))


def sofa(name, cx, cy, M, ln=2.32, dep=0.90, cname=C):
    parts, g = _uphol_body(name, ln, dep, cname)
    x0, x1, y0, y1, seat_z, arm_z, back_z, aw, backt = g
    nseat = 3
    inner = ln - 2 * aw
    pitch = inner / nseat
    seat_top = seat_z + 0.155
    for i in range(nseat):
        # 24 mm of daylight between neighbours: cushion() bulges to 1.025 of the
        # nominal width at mid height, so the nominal has to be cut back further
        # than the gap you want to read.
        w = pitch - 0.028
        yy = y0 + aw + (i + 0.5) * pitch
        cu = mlib.cushion(name + "_sc%d" % i, 0.56, w, 0.160, 0.105, cname)
        mlib.translate(cu, (0.15, yy, seat_z))
        parts.append(cu)
        # Back cushion.  It was 0.30 thick and centred at -0.039, which left it
        # floating 40 mm clear of the rail *and* eating half the seat: 0.90 of
        # depth minus a 0.22 rail minus 0.30 of cushion is 0.38 of usable seat.
        # 0.18 thick with its top corner set on the rail face gives 0.43.
        bc = mlib.cushion(name + "_bc%d" % i, 0.18, w, 0.46, 0.115, cname)
        mlib.rot_y(bc, BACK_LEAN)
        mlib.translate(bc, (_back_x(x0, backt, 0.18, 0.46), yy, 0.500))
        parts.append(bc)
    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, M['damask'])
    mlib.translate(ob, (cx, cy, 0.0))
    out = [ob]
    # chintz throw folded over the back rail at the near end (living_room ref)
    th = drape_over(name + "_throw", cx + x0 + backt * 0.5, cy - 0.52,
                    back_z, w=1.05, front=0.62, back=0.32, t=backt * 0.5 + 0.05,
                    cname=cname, mat=M['throw'])
    out.append(th)
    # accent pillows: red at the near arm, rust in the middle, champagne at the
    # far arm - the trio the set photographs show.  All three sit ON the seat
    # cushions and lean back into the back cushions; the two end ones are also
    # canted a few degrees into their arm so they settle in the corner.
    corner = y1 - aw - 0.20
    for i, (dy, tilt, mm) in enumerate(((-corner, 7.0, M['pillow_r']),
                                        (0.15, 0.0, M['pillow_rust']),
                                        (corner, -7.0, M['gold']))):
        pw = mlib.cushion(name + "_pw%d" % i, 0.135, 0.37, 0.37, 0.095, cname)
        mlib.rot_y(pw, math.radians(-22))
        mlib.rot_x(pw, math.radians(tilt))
        mlib.set_mat(pw, mm)
        mlib.translate(pw, (cx + 0.19, cy + dy, seat_top - 0.014))
        out.append(pw)
    return out


def drape_over(name, cx, cy, ztop, w=1.2, front=0.5, back=0.3, t=0.16, cname=C,
               mat=None):
    """A throw folded over a sofa back: U section swept along Y with ripple."""
    prof = []
    n = 10
    for i in range(n, 0, -1):
        tt = i / n
        prof.append((-t * 0.5 - 0.012 * math.sin(tt * 3.0), ztop - back * tt))
    for i in range(11):
        a = math.pi * (1 - i / 10.0)
        prof.append((-t * 0.5 * math.cos(a) * -1.0, ztop + 0.012 * math.sin(a)))
    for i in range(1, n + 1):
        tt = i / n
        prof.append((t * 0.5 + 0.016 * math.sin(tt * 2.4), ztop - front * tt))
    rings = []
    for k in range(11):
        s = k / 10.0
        yy = cy + (s - 0.5) * w
        wob = 1.0 + 0.14 * math.sin(s * 8.0)
        rings.append([(cx + x * wob, yy, z) for (x, z) in prof])
    ob = mlib._loft(name, rings, close_u=False, close_v=False, cname=cname)
    mlib.solidify(ob, 0.008, offset=0)
    mlib.smooth_shade(ob, 52)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def armchair(name, cx, cy, rot, M, w=0.96, dep=0.94, cname=C):
    parts, g = _uphol_body(name, w, dep, cname, aw=0.175, backt=0.21)
    x0, x1, y0, y1, seat_z, arm_z, back_z, aw, backt = g
    cu = mlib.cushion(name + "_sc", 0.58, w - 2 * aw - 0.02, 0.16, 0.05, cname)
    mlib.translate(cu, (0.155, 0.0, seat_z))
    parts.append(cu)
    bc = mlib.cushion(name + "_bc", 0.18, w - 2 * aw - 0.02, 0.48, 0.055, cname)
    mlib.rot_y(bc, BACK_LEAN)
    mlib.translate(bc, (_back_x(x0, backt, 0.18, 0.48), 0.0, seat_z - 0.02))
    parts.append(bc)
    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, M['damask'])
    mlib.rotate_z(ob, rot)
    mlib.translate(ob, (cx, cy, 0.0))
    # No quilt over this chair's back.  drape_over lays a shell of the given
    # thickness across the rail, and against a 0.21 rail it came out as a flat
    # striped card sitting inside the upholstery rather than cloth hanging over
    # it - the check pillows already carry that pattern where it reads.
    return [ob]


def slipper_chair(name, cx, cy, rot, M, w=0.63, dep=0.72, cname=C):
    """Mid-century armless slipper chair in pale blush, on splayed blond dowels.

    Built as three solids - plinth, seat cushion, back - rather than a slab with
    a curved sheet standing behind it.  The back is a real upholstered mass with
    thickness that meets the seat, bowed *forward at its ends* so it wraps the
    sitter, and rolled over at the top.  The old one bowed forward in the middle
    instead, which lifted it clear of the seat entirely and left a curved card
    hovering behind a mattress."""
    parts = []
    SEAT_T, RAIL_Z = 0.400, 0.235
    # --- upholstered plinth under the cushion --------------------------------
    pts = mlib.rounded_rect(dep - 0.020, w - 0.020, 0.045, 5)
    rings = []
    for (zz, s) in ((RAIL_Z, 0.955), (RAIL_Z + 0.020, 0.995),
                    (SEAT_T - 0.020, 1.0), (SEAT_T, 0.985)):
        rings.append([(x * s, y * s, zz) for (x, y) in pts])
    rail = mlib._loft(name + "_rail", rings, close_u=False, close_v=True,
                      cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(rail, 0.008, 2, 55)
    mlib.smooth_shade(rail, 48)
    parts.append(rail)
    # --- seat cushion, welted and rounded at the front -----------------------
    cpts = mlib.rounded_rect(dep - 0.030, w - 0.028, 0.060, 6)
    rings = []
    for (dz, s) in ((0.000, 0.94), (0.022, 1.0), (0.070, 1.02),
                    (0.112, 1.0), (0.132, 0.93)):
        rings.append([(x * s, y * s, SEAT_T + dz) for (x, y) in cpts])
    cush = mlib._loft(name + "_cush", rings, close_u=False, close_v=True,
                      cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(cush, 0.008, 2, 55)
    mlib.smooth_shade(cush, 48)
    parts.append(cush)
    # --- back: a solid section swept across the width ------------------------
    x0 = -dep / 2 + 0.052
    ztop = SEAT_T + 0.052
    # a closed section that arcs right over the top, so the back rolls the way
    # upholstery does instead of ending in a sawn-off flat with a hard corner
    sec = [(0.014, 0.000), (-0.004, 0.108), (-0.026, 0.222), (-0.042, 0.318),
           (-0.046, 0.384), (-0.034, 0.424), (-0.016, 0.446), (-0.042, 0.454),
           (-0.068, 0.444), (-0.084, 0.414), (-0.094, 0.358), (-0.100, 0.286),
           (-0.102, 0.188), (-0.098, 0.092), (-0.092, 0.000)]
    scx = sum(p[0] for p in sec) / len(sec)
    scz = sum(p[1] for p in sec) / len(sec)
    n = 30
    rings = []
    for i in range(n + 1):
        t = i / n
        yy = (t - 0.5) * (w - 0.030)
        # ends come forward, centre sits back: the chair wraps you
        bow = 0.032 * (2.0 * abs(t - 0.5)) ** 2.0
        # and the last sliver at each end draws in, rounding the back's corners
        e = max(0.0, min(1.0, min(t, 1.0 - t) / 0.055))
        k = 0.62 + 0.38 * e ** 0.6
        rings.append([(x0 + scx + (dx - scx) * k + bow, yy,
                       ztop + scz + (dz - scz) * k) for (dx, dz) in sec])
    back = mlib._loft(name + "_back", rings, close_u=False, close_v=True,
                      cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(back, 0.012, 2, 55)
    mlib.smooth_shade(back, 50)
    parts.append(back)
    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, M['blush'])
    # --- splayed blond dowel legs -------------------------------------------
    legs = []
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        lg = mlib.revolve(name + "_lg", [(0.0, 0.0), (0.009, 0.004),
                                         (0.013, 0.055), (0.017, 0.130),
                                         (0.021, 0.205), (0.023, 0.238),
                                         (0.0, 0.244)], 14, cname=cname)
        mlib.rot_y(lg, -sx * math.radians(11))
        mlib.rot_x(lg, sy * math.radians(11))
        mlib.translate(lg, (sx * (dep / 2 - 0.075), sy * (w / 2 - 0.075), 0.0))
        legs.append(lg)
    lo = mlib.join(legs, name + "_legs", cname)
    mlib.smooth_shade(lo, 40)
    mlib.set_mat(lo, M['honey'])
    for o in (ob, lo):
        mlib.rotate_z(o, rot)
        mlib.translate(o, (cx, cy, 0.0))
    # red and yellow scatter cushions, slumped against the back rather than
    # stood up square against it
    spec = ((-0.128, M['pillow_r'], -31.0, -9.0), (0.132, M['pillow_y'], -22.0, 8.0))
    for i, (dy, mm, ry, rx) in enumerate(spec):
        pw = mlib.cushion(name + "_pw%d" % i, 0.052, 0.310, 0.272, 0.086, cname)
        mlib.rot_y(pw, math.radians(ry))
        mlib.rot_x(pw, math.radians(rx))
        mlib.set_mat(pw, mm)
        mlib.translate(pw, (-dep / 2 + 0.196 + 0.012 * i, dy, SEAT_T + 0.108))
        mlib.rotate_z(pw, rot)
        mlib.translate(pw, (cx, cy, 0.0))
    return [ob, lo]


def ottoman(name, cx, cy, rot, M, w=0.56, dep=0.40, cname=C):
    top_z = 0.345
    pts = mlib.rounded_rect(dep, w, 0.085, 5)
    rings = []
    for (dz, s) in ((0.0, 0.90), (0.018, 0.98), (0.075, 1.0), (0.130, 0.985),
                    (0.160, 0.90), (0.175, 0.62)):
        rings.append([(x * s, y * s, top_z - 0.175 + dz) for (x, y) in pts])
    top = mlib._loft(name + "_top", rings, close_u=False, close_v=True,
                     cname=cname, cap_start=True, cap_end=True)
    mlib.bevel(top, 0.008, 2, 55)
    mlib.smooth_shade(top, 50)
    mlib.set_mat(top, M['velvet_g'])
    legs = []
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        # cabriole leg: bezier sweep
        # stop the leg one tube-radius above the floor so the swept tube's cap
        # does not sink through the boards; the pad foot closes the gap
        pts2 = mlib.bez((0.0, top_z - 0.155), (0.045, top_z - 0.235),
                        (0.055, top_z - 0.30), (0.012, 0.019), n=9)
        path = [(sx * (dep / 2 - 0.075) + sx * p[0] * 0.9,
                 sy * (w / 2 - 0.075) + sy * p[0] * 0.9, p[1]) for p in pts2]
        lg = mlib.tube_along(name + "_lg", path,
                            mlib.circle(0.017, 9), cname)
        legs.append(lg)
        pad = mlib.revolve(name + "_pad", [(0.0, 0.0), (0.026, 0.006),
                                           (0.028, 0.018), (0.0, 0.026)], 12,
                           cname=cname)
        mlib.translate(pad, (path[-1][0], path[-1][1], 0.0))
        legs.append(pad)
    lo = mlib.join(legs, name + "_legs", cname)
    mlib.smooth_shade(lo, 42)
    mlib.set_mat(lo, M['honey'])
    for o in (top, lo):
        mlib.rotate_z(o, rot)
        mlib.translate(o, (cx, cy, 0.0))
    return [top, lo]


# --------------------------------------------------------------------- tables
def credenza_flowers(name, vx, vy, vz, M, rng, cname=C):
    """The vase of blooms on the credenza top beside the television.  Mottled
    green-teal ceramic with pale cream flowers, not the cobalt-and-yellow it
    was: the set photo shows it clearly once you crop in on the sideboard."""
    vase = mlib.revolve(name, [(0.0, 0.0), (0.050, 0.0), (0.058, 0.018),
                               (0.074, 0.076), (0.070, 0.148), (0.048, 0.222),
                               (0.039, 0.272), (0.046, 0.296), (0.041, 0.300),
                               (0.034, 0.276), (0.034, 0.220), (0.0, 0.215)],
                        28, cname=cname)
    mlib.smooth_shade(vase, 34)
    mlib.set_mat(vase, mats.paint('ceramic_teal', '5E7F6E', rough=0.22,
                                  coat=0.55, variation=0.09, noise=34))
    mlib.translate(vase, (vx, vy, vz))
    stems, blooms, leaves = [], [], []
    for i in range(12):
        a = rng.uniform(0, math.tau)
        ln = rng.uniform(0.10, 0.26)
        pts = [(0.0, 0.0, 0.24)]
        for k in range(1, 6):
            t = k / 5.0
            pts.append((math.cos(a) * 0.095 * t ** 1.5,
                        math.sin(a) * 0.095 * t ** 1.5, 0.30 + ln * t))
        stems.append(mlib.tube_along(name + "_stem", pts,
                                     mlib.circle(0.0030, 5), cname))
        rr = rng.uniform(0.85, 1.20)
        hd = mlib.revolve(name + "_bloom",
                          [(0.0, 0.0), (0.012 * rr, 0.004), (0.024 * rr, 0.014),
                           (0.031 * rr, 0.030), (0.028 * rr, 0.044),
                           (0.016 * rr, 0.053), (0.0, 0.055)], 18, cname=cname)
        mlib.smooth_shade(hd, 45)
        mlib.rot_x(hd, rng.uniform(-0.35, 0.35))
        mlib.translate(hd, pts[-1])
        blooms.append(hd)
        lf = P.leaf_blade(name + "_leaf", rng.uniform(0.080, 0.120),
                          rng.uniform(0.020, 0.030), 5, cname, curl=0.55,
                          peak=0.42)
        mlib.rotate_z(lf, a + rng.uniform(-0.8, 0.8))
        mlib.rot_x(lf, rng.uniform(-1.15, -0.55))
        mlib.translate(lf, pts[2])
        leaves.append(lf)
    for grp, nm, mm in ((stems, name + "_stems", M['leaf']),
                        (leaves, name + "_leaves", M['leaf']),
                        (blooms, name + "_blooms",
                         mats.paint('bloom_cream', 'E8DEC0', rough=0.54,
                                    variation=0.06))):
        o = mlib.join(grp, nm, cname)
        mlib.smooth_shade(o, 40)
        mlib.set_mat(o, mm)
        mlib.translate(o, (vx, vy, vz))


def coffee_table(name, cx, cy, M, w=0.88, d=1.20, h=0.435, cname=C):
    parts = []
    t = 0.055
    # frame-and-panel top
    fw = 0.085
    top = mlib.panel_with_holes(name + "_topf", w, d, t,
                                [(fw, fw, w / 2 - 0.02, d - fw),
                                 (w / 2 + 0.02, fw, w - fw, d - fw)], cname)
    # local (lx, lz) -> world (x, y); local ly -> world z
    top.data.transform(Matrix(((1, 0, 0, -w / 2), (0, 0, 1, -d / 2),
                               (0, 1, 0, h - t), (0, 0, 0, 1))))
    mlib.recalc_normals(top)
    mlib.bevel(top, 0.004, 2, 45)
    parts.append((top, M['pine']))
    for (a, bb) in ((fw, w / 2 - 0.02), (w / 2 + 0.02, w - fw)):
        pn = mlib.box(name + "_tp", a - w / 2 - 0.008, -d / 2 + fw - 0.008,
                      h - 0.030, bb - w / 2 + 0.008, d / 2 - fw + 0.008,
                      h - 0.006, cname)
        mlib.bevel(pn, 0.003, 2, 45)
        parts.append((pn, M['pine']))
    # aprons
    for (ax0, ay0, ax1, ay1) in ((-w / 2 + 0.055, -d / 2, w / 2 - 0.055,
                                  -d / 2 + 0.030),
                                 (-w / 2 + 0.055, d / 2 - 0.030, w / 2 - 0.055,
                                  d / 2),
                                 (-w / 2, -d / 2 + 0.055, -w / 2 + 0.030,
                                  d / 2 - 0.055),
                                 (w / 2 - 0.030, -d / 2 + 0.055, w / 2,
                                  d / 2 - 0.055)):
        ap = mlib.box(name + "_ap", ax0, ay0, h - t - 0.075, ax1, ay1, h - t, cname)
        mlib.bevel(ap, 0.004, 2, 45)
        parts.append((ap, M['pine'] if abs(ax1 - ax0) > abs(ay1 - ay0)
                      else M['pine_y']))
    # legs: square tapered with a turned collar
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        lx = sx * (w / 2 - 0.055)
        ly = sy * (d / 2 - 0.055)
        sec = mlib.rounded_rect(0.088, 0.088, 0.008, 2)
        rings = []
        for (zz, s) in ((0.0, 0.84), (0.020, 0.92), (0.045, 1.05), (0.070, 1.05),
                        (0.095, 0.92), (0.115, 0.96), (0.135, 1.0),
                        (h - t - 0.075, 1.0), (h - t, 1.0)):
            rings.append([(x * s, y * s, zz) for (x, y) in sec])
        lg = mlib._loft(name + "_lg", rings, close_u=True, close_v=False,
                        cname=cname, cap_start=True, cap_end=True)
        mlib.bevel(lg, 0.004, 2, 50)
        mlib.translate(lg, (lx, ly, 0.0))
        parts.append((lg, M['pine_v']))
    # lower shelf: slatted
    for i in range(5):
        yy = -d / 2 + 0.115 + i * (d - 0.23) / 4.5
        sl = mlib.box(name + "_sl%d" % i, -w / 2 + 0.055, yy, 0.135,
                      w / 2 - 0.055, yy + (d - 0.23) / 5.6, 0.155, cname)
        mlib.bevel(sl, 0.003, 2, 45)
        parts.append((sl, M['pine']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, 0.0))
        objs.append(ob)
    return objs


def glass_table(name, cx, cy, M, w=0.60, d=0.60, h=0.575, cname=C):
    """Wrought-iron occasional table with a bevelled glass top.  The set piece
    has four cabriole legs that sweep out to scrolled feet and are tied only at
    the top, by a scrolled apron rail under the glass - there is no lower
    stretcher, so nothing is left hanging in mid air."""
    parts = []
    gt = mlib.prism(name + "_glass", mlib.rounded_rect(w, d, 0.075, 6), h,
                    h + 0.026, cname)
    # a wide ground bevel: it is the bright edge catching the light that makes
    # the top read as glass at all, and at 6 mm the slab was near invisible
    mlib.bevel(gt, 0.012, 3, 40)
    mlib.set_mat(gt, mats.get('glass_thick') or
                 mats.pane('glass_thick', tint='C2DED0', rough=0.02,
                           base_alpha=0.34, edge=0.90))
    parts.append(gt)
    ir = 0.011                                   # rod radius
    ax, ay = w / 2 - 0.075, d / 2 - 0.075        # leg centres at the top
    legs = []
    knees = {}
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        pts = mlib.bez((0.0, h - 0.055), (0.075, h - 0.24), (0.115, h - 0.40),
                       (0.052, 0.022), n=14)
        path = [(sx * (ax + p[0] * 0.80), sy * (ay + p[0] * 0.80), p[1])
                for p in pts]
        legs.append(mlib.tube_along(name + "_lg", path, mlib.circle(ir, 9), cname))
        knees[(sx, sy)] = path[0]
        # scrolled foot: the rod curls into a flat volute on the floor
        fx, fy, _ = path[-1]
        ux, uy = sx / math.sqrt(2.0), sy / math.sqrt(2.0)
        sc = []
        for i in range(15):
            t = i / 14.0
            a = t * math.pi * 1.75
            rr = 0.046 * (1.0 - 0.62 * t)
            sc.append((fx + ux * rr * math.sin(a) - ux * 0.046,
                       fy + uy * rr * math.sin(a) - uy * 0.046,
                       0.009 + rr * (1.0 - math.cos(a)) * 0.30))
        legs.append(mlib.tube_along(name + "_ft", sc, mlib.circle(ir * 0.85, 8),
                                    cname))
    # apron rail: a rounded-rectangle ring tucked right under the glass, run
    # through the top of every leg so the frame reads as one welded piece
    az = h - 0.055
    ring = [(x, y, az) for (x, y) in mlib.rounded_rect(2 * ax, 2 * ay, 0.055, 5)]
    legs.append(mlib.tube_along(name + "_ap", ring + [ring[0]],
                                mlib.circle(ir * 0.9, 8), cname))
    # a pair of opposed volutes hanging off the middle of each apron side: each
    # starts on the rail itself and curls in and down, so nothing floats free
    for k, (mx, my, dxs, dys) in enumerate(((0.0, -ay, 1.0, 0.0),
                                            (0.0, ay, 1.0, 0.0),
                                            (-ax, 0.0, 0.0, 1.0),
                                            (ax, 0.0, 0.0, 1.0))):
        for s in (-1, 1):
            cs = []
            for i in range(15):
                t = i / 14.0
                a = t * math.pi * 1.4
                rr = 0.023 * (1.0 - 0.45 * t)
                u = s * (0.072 - rr * (1.0 - math.cos(a)) * 1.15)
                zz = az - 0.005 - rr * math.sin(a) * 1.35
                cs.append((mx + dxs * u, my + dys * u, zz))
            legs.append(mlib.tube_along(name + "_cs%d%d" % (k, s > 0), cs,
                                        mlib.circle(ir * 0.70, 7), cname))
    lo = mlib.join(legs, name + "_base", cname)
    mlib.smooth_shade(lo, 40)
    mlib.set_mat(lo, M['iron_pale'])
    for o in (gt, lo):
        mlib.translate(o, (cx, cy, 0.0))
    return [gt, lo]


# ------------------------------------------------------------------- credenza
def credenza(name, M, cname=C):
    x0, x1 = 8.00, L.EX - 0.03
    y0, y1 = L.TV_C[1] - L.CRED_HW, L.TV_C[1] + L.CRED_HW
    h = 0.90
    d = x1 - x0
    ln = y1 - y0
    parts = []
    # plinth
    pl = mlib.box(name + "_plinth", x0 + 0.02, y0 + 0.03, 0.0, x1, y1 - 0.03,
                  0.085, cname)
    mlib.bevel(pl, 0.006, 2, 45)
    parts.append((pl, M['walnut']))
    # carcass
    car = mlib.box(name + "_car", x0 + 0.045, y0, 0.085, x1, y1, h - 0.055, cname)
    parts.append((car, M['walnut']))
    # rounded 'waterfall' top
    sec = [(x1, h - 0.055), (x1, h), (x0 + 0.10, h), (x0 + 0.055, h - 0.008),
           (x0 + 0.032, h - 0.026), (x0 + 0.026, h - 0.048),
           (x0 + 0.030, h - 0.055)]
    top = mlib.prism_xz(name + "_top", sec, y0 - 0.030, y1 + 0.030, cname)
    mlib.bevel(top, 0.005, 3, 40)
    mlib.smooth_shade(top, 34)
    parts.append((top, M['walnut']))
    # front faces: two end doors, three centre drawers, rounded pilasters
    endw = 0.30
    pilw = 0.075
    cw = ln - 2 * endw - 2 * pilw
    yy = y0
    fx = x0 + 0.030
    for kind, wid in (('door', endw), ('pil', pilw), ('drawers', cw),
                      ('pil', pilw), ('door', endw)):
        if kind == 'door':
            dr = mlib.box(name + "_dr", fx - 0.024, yy + 0.008, 0.100,
                          fx, yy + wid - 0.008, h - 0.070, cname)
            mlib.bevel(dr, 0.004, 2, 45)
            parts.append((dr, M['walnut_v']))
            pull = deco_pull(name + "_p", cname)
            mlib.translate(pull, (fx - 0.024, yy + wid * 0.5, 0.46))
            parts.append((pull, M['bakelite']))
        elif kind == 'pil':
            sec2 = [(fx - 0.030, 0.0)]
            for i in range(13):
                a = math.pi * i / 12.0
                sec2.append((fx - 0.030 + 0.030 * (1 - math.cos(a)),
                             wid * 0.5 * (1 - math.sin(a)) * 0 + 0.0))
            pilr = mlib.revolve(name + "_pil", [(wid * 0.5, 0.0), (wid * 0.5, 1.0)],
                                4, cname=cname)
            bpy.data.objects.remove(pilr, do_unlink=True)
            rings = []
            for i in range(13):
                a = math.pi * i / 12.0
                px = fx - 0.030 + 0.030 * math.sin(a)
                py = yy + wid * 0.5 - wid * 0.5 * math.cos(a)
                rings.append([(px, py, 0.095), (px, py, h - 0.058)])
            pilo = mlib._loft(name + "_pil", rings, close_u=False, close_v=False,
                              cname=cname)
            mlib.smooth_shade(pilo, 40)
            parts.append((pilo, M['walnut_v']))
        else:
            for k in range(3):
                dh = (h - 0.185) / 3
                z = 0.105 + k * dh
                dw = mlib.box(name + "_dw%d" % k, fx - 0.024, yy + 0.010,
                              z + 0.006, fx, yy + wid - 0.010, z + dh - 0.006,
                              cname)
                mlib.bevel(dw, 0.004, 2, 45)
                parts.append((dw, M['walnut']))
                pull = deco_pull(name + "_dp%d" % k, cname)
                mlib.translate(pull, (fx - 0.024, yy + wid * 0.5, z + dh * 0.5))
                parts.append((pull, M['bakelite']))
        yy += wid
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        objs.append(ob)
    return objs


def deco_pull(name, cname=C):
    """Elongated art-deco pull: a fan-shaped bar with a stepped centre."""
    parts = []
    sec = [(0.0, -0.024), (0.010, -0.022), (0.016, -0.012), (0.018, 0.0),
           (0.016, 0.012), (0.010, 0.022), (0.0, 0.024)]
    rings = []
    for i in range(11):
        t = i / 10.0
        s = 0.55 + 0.45 * math.sin(math.pi * t) ** 0.5
        rings.append([(-0.075 + 0.15 * t, y * s * 1.0, x * s)
                      for (x, y) in [(a, b) for (a, b) in sec]])
    ob = mlib._loft(name, rings, close_u=False, close_v=True, cname=cname,
                    cap_start=True, cap_end=True)
    mlib.smooth_shade(ob, 40)
    # rotate so the length runs along Y and it stands off in -X
    mlib.rotate_z(ob, math.pi / 2)
    return ob


def crt_tv(name, cx, cy, cz, M, w=0.60, d=0.52, h=0.50, cname=C):
    parts = []
    body = mlib.box(name + "_body", -d / 2, -w / 2, 0.0, d / 2, w / 2, h, cname)
    mlib.bevel(body, 0.014, 3, 45)
    parts.append((body, M['crt']))
    # bezel + slightly bulging screen
    # The tube fills most of the front on the set.  At 76 x 60 per cent of the
    # face, with a column of knobs and a vent stack down one side, this read as
    # a microwave standing on the sideboard rather than a television.
    bez = mlib.panel_with_holes(name + "_bez", w - 0.04, h - 0.04, 0.030,
                                [(0.048, 0.058, w - 0.088, h - 0.082)], cname)
    bez.data.transform(Matrix(((0, 0, 1, -d / 2 - 0.028), (1, 0, 0, -w / 2 + 0.02),
                               (0, 1, 0, 0.02), (0, 0, 0, 1))))
    mlib.recalc_normals(bez)
    mlib.bevel(bez, 0.005, 2, 45)
    # the bezel was the same dark plastic as the cabinet, so it never read; on
    # the set it is a distinctly lighter grey frame around the tube
    parts.append((bez, M['crt_bez']))
    # a small pair of tuning knobs low on the front, and nothing else: the set
    # television has a plain dark case, not an appliance fascia
    for k, yy in enumerate((w / 2 - 0.075, w / 2 - 0.036)):
        kn = mlib.revolve(name + "_kn%d" % k, [(0.0, 0.0), (0.012, 0.003),
                                               (0.013, 0.010), (0.009, 0.016),
                                               (0.0, 0.018)], 14, cname=cname)
        mlib.rot_y(kn, -math.pi / 2)
        mlib.smooth_shade(kn, 40)
        mlib.translate(kn, (-d / 2 - 0.030, yy, 0.036))
        parts.append((kn, M['crt_bez']))
    rings = []
    # The tube used to be 20 mm lower than the bezel's opening, so it covered
    # the frame along the bottom and left a gap along the top.  Centre it in the
    # aperture and inset it so the grey frame actually shows all round.
    sw, sh = w - 0.19, h - 0.23
    pts = mlib.rounded_rect(sw, sh, 0.055, 5)
    for (dx, s) in ((0.0, 1.0), (-0.014, 0.94)):
        rings.append([(-d / 2 - 0.010 + dx, x * s, h / 2 + y * s)
                      for (x, y) in pts])
    scr = mlib._loft(name + "_scr", rings, close_u=False, close_v=True,
                     cname=cname, cap_start=True, cap_end=True)
    mlib.smooth_shade(scr, 40)
    parts.append((scr, M['screen']))
    # vented back panel
    for k in range(9):
        zz = 0.10 + k * (h - 0.20) / 8
        vt = mlib.box(name + "_v%d" % k, d / 2 - 0.004, -w / 2 + 0.06, zz,
                      d / 2 + 0.004, w / 2 - 0.06, zz + 0.014, cname)
        parts.append((vt, M['screen']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, cz))
        objs.append(ob)
    return objs


def speaker(name, cx, cy, M, w=0.32, d=0.40, h=0.70, cname=C):
    """Floor-standing hi-fi speaker of the period: a veneered box with a
    recessed baffle, a big woofer with a coloured surround and a small tweeter
    above it.  It used to be a squat 0.44 m block with two flat discs stuck on
    the front, which read as a plinth rather than a loudspeaker."""
    parts = []
    veneer = mats.wood('wood_speaker', ('7A5028', '5A3418', '3A2008'),
                       ring=44, warp=0.05, bump=0.28, axis='YZ')
    box = mlib.box(name + "_b", -d / 2, -w / 2, 0.0, d / 2, w / 2, h, cname)
    mlib.bevel(box, 0.006, 2, 45)
    parts.append((box, veneer))
    # baffle recessed behind a shallow lip, so the drivers sit in a face rather
    # than on one
    bf = mlib.box(name + "_bf", -d / 2 - 0.010, -w / 2 + 0.022, 0.026,
                  -d / 2 + 0.004, w / 2 - 0.022, h - 0.026, cname)
    mlib.bevel(bf, 0.003, 2, 45)
    parts.append((bf, M['bakelite']))
    surr = mats.paint('rubber_surround', '5E2018', rough=0.62)
    cone_m = mats.paint('driver_cone', '241E1A', rough=0.80)
    # (centre z, outer radius, surround?) - woofer low and large, tweeter above
    for (zz, rr, has_s) in ((h * 0.34, 0.098, True), (h * 0.76, 0.036, False)):
        if has_s:
            ring = mlib.revolve(name + "_r", [(rr * 0.62, 0.0), (rr, 0.012),
                                              (rr * 1.06, 0.026),
                                              (rr * 0.98, 0.034),
                                              (rr * 0.60, 0.020)], 26,
                                cname=cname)
            mlib.rot_y(ring, -math.pi / 2)
            mlib.translate(ring, (-d / 2 - 0.006, 0.0, zz))
            mlib.smooth_shade(ring, 40)
            parts.append((ring, surr))
        # dished cone with a dust cap at its centre
        cone = mlib.revolve(name + "_c", [(0.0, -0.030 * (rr / 0.098)),
                                          (rr * 0.28, -0.022 * (rr / 0.098)),
                                          (rr * 0.62, 0.002),
                                          (rr * 0.70, 0.010)], 26, cname=cname)
        mlib.rot_y(cone, -math.pi / 2)
        mlib.translate(cone, (-d / 2 - 0.006, 0.0, zz))
        mlib.smooth_shade(cone, 40)
        parts.append((cone, cone_m))
        cap = mlib.revolve(name + "_cap", [(0.0, 0.0), (rr * 0.24, -0.004),
                                           (rr * 0.26, -0.018)], 20, cname=cname)
        mlib.rot_y(cap, -math.pi / 2)
        mlib.translate(cap, (-d / 2 - 0.006 - 0.030 * (rr / 0.098), 0.0, zz))
        mlib.smooth_shade(cap, 40)
        parts.append((cap, M['bakelite']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, 0.0))
        objs.append(ob)
    return objs


# ------------------------------------------------------------------- the rug
def rug(name, M, cname=C):
    w, d = L.RUG_WH
    cx, cy = L.RUG_C
    pts = []
    n = 96
    for i in range(n):
        t = i / n
        # rectangle perimeter with a slight cloth wobble
        if t < 0.25:
            u = t / 0.25
            p = (-w / 2 + w * u, -d / 2)
        elif t < 0.5:
            u = (t - 0.25) / 0.25
            p = (w / 2, -d / 2 + d * u)
        elif t < 0.75:
            u = (t - 0.5) / 0.25
            p = (w / 2 - w * u, d / 2)
        else:
            u = (t - 0.75) / 0.25
            p = (-w / 2, d / 2 - d * u)
        wob = 0.006 * math.sin(t * 37.0)
        pts.append((p[0] * (1 + wob * 0.02) + wob, p[1] + wob))
    ob = mlib.prism(name, pts, 0.0008, 0.0128, cname)
    mlib.bevel(ob, 0.003, 2, 40)
    mlib.set_mat(ob, M['rug'])
    # keep the mesh centred so Object coords drive the border pattern
    ob.location = (cx, cy, 0.0)
    return ob


# --------------------------------------------------------------- window seat
def window_seat(name, M, cname=C):
    x0, x1 = L.BW_X[0] - 0.10, L.BW_X[1] + 0.10
    y0, y1 = L.AL_Y[1] - L.SEAT_D, L.AL_Y[1]
    h = L.SEAT_H
    parts = []
    base = mlib.box(name + "_base", x0, y0 + 0.05, 0.0, x1, y1, h - 0.055, cname)
    parts.append((base, M['limed']))
    kick = mlib.box(name + "_kick", x0 + 0.02, y0, h - 0.055, x1 - 0.02, y1,
                    h, cname)
    mlib.bevel(kick, 0.006, 2, 45)
    parts.append((kick, M['limed']))
    for i in range(4):
        pw = (x1 - x0 - 0.10) / 4
        px = x0 + 0.05 + i * pw
        pn = mlib.box(name + "_p%d" % i, px + 0.03, y0 + 0.028, 0.075,
                      px + pw - 0.03, y0 + 0.048, h - 0.085, cname)
        mlib.bevel(pn, 0.004, 2, 45)
        parts.append((pn, M['limed']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        objs.append(ob)
    # long mattress cushion + pillows
    cu = mlib.cushion(name + "_cush", x1 - x0 - 0.05, y1 - y0 - 0.05, 0.10, 0.055,
                      cname)
    mlib.translate(cu, ((x0 + x1) / 2, (y0 + y1) / 2, h))
    mlib.set_mat(cu, M['cream'])
    rng = random.Random(6)
    for i in range(4):
        px = x0 + 0.30 + i * (x1 - x0 - 0.60) / 3
        pw = mlib.cushion(name + "_pw%d" % i, rng.uniform(0.34, 0.44),
                          rng.uniform(0.34, 0.42), 0.13, 0.05, cname)
        mlib.rot_x(pw, math.radians(rng.uniform(62, 78)))
        mlib.rotate_z(pw, rng.uniform(-0.2, 0.2))
        mlib.set_mat(pw, [M['throw'], M['drape'], M['pillow_rust'],
                          M['damask']][i % 4])
        mlib.translate(pw, (px, y1 - 0.20, h + 0.20))
    return objs


def console_table(name, M, cname=C):
    """Long sofa table under the window.

    Rebuilt: it used to be a 40 mm slab on four legs that started inside the
    top's footprint and splayed out past it, tied by one thin bar floating at
    mid height between them, touching nothing.  Now it is a proper frame -
    lipped top, four rails set back from the edge, square tapered legs standing
    at the frame's corners, and an H-stretcher whose members actually meet."""
    cx = (L.BW_X[0] + L.BW_X[1]) * 0.5
    cy = L.AL_Y[1] - L.SEAT_D - 0.30
    w, d, h = 1.35, 0.42, 0.715
    parts = []
    top = mlib.box(name + "_top", -w / 2, -d / 2, h - 0.028, w / 2, d / 2, h,
                   cname)
    mlib.bevel(top, 0.006, 3, 42)
    parts.append((top, M['limed']))
    lip = mlib.box(name + "_lip", -w / 2 + 0.012, -d / 2 + 0.012, h - 0.046,
                   w / 2 - 0.012, d / 2 - 0.012, h - 0.028, cname)
    mlib.bevel(lip, 0.004, 2, 45)
    parts.append((lip, M['limed']))
    ix, iy, RT = w / 2 - 0.058, d / 2 - 0.040, 0.026
    for nm, x0, y0, x1, y1 in (
            (name + "_rf", -ix, iy - RT, ix, iy),
            (name + "_rb", -ix, -iy, ix, -iy + RT),
            (name + "_rl", -ix, -iy, -ix + RT, iy),
            (name + "_rr", ix - RT, -iy, ix, iy)):
        rail = mlib.box(nm, x0, y0, h - 0.148, x1, y1, h - 0.046, cname)
        mlib.bevel(rail, 0.003, 2, 45)
        parts.append((rail, M['limed_y']))
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        pts = [(sx * (ix - RT * 0.5), sy * (iy - RT * 0.5), h - 0.046),
               (sx * (ix - 0.034), sy * (iy - 0.030), 0.0)]
        lg = mlib.tube_along(name + "_lg", pts,
                             mlib.rounded_rect(0.048, 0.044, 0.005, 2), cname)
        parts.append((lg, M['limed_v']))
    # H-stretcher: a bar across each end between that end's pair of legs, joined
    # by one running the length between their midpoints
    SZ0, SZ1 = 0.188, 0.214
    for sx in (-1, 1):
        a, b = sorted((sx * (ix - 0.048), sx * (ix - 0.014)))
        e = mlib.box(name + "_se", a, -(iy - 0.026), SZ0, b, iy - 0.026, SZ1,
                     cname)
        mlib.bevel(e, 0.003, 2, 45)
        parts.append((e, M['limed_y']))
    lb = mlib.box(name + "_sl", -(ix - 0.030), -0.017, SZ0 + 0.002,
                  ix - 0.030, 0.017, SZ1 - 0.002, cname)
    mlib.bevel(lb, 0.003, 2, 45)
    parts.append((lb, M['limed']))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, 0.0))
        objs.append(ob)
    return objs


def door_wall(name, M, cname=C):
    """The stretch of central wall between Monica's door and the alcove.

    This is the piece the build was missing entirely.  In living_room.jpeg the
    window bay does not run into the bedroom door: between them is a stand of
    wall carrying a brass sconce over a hung picture, with a low console under
    it and framed photographs standing on the console.  Without it the door sits
    in the corner of the flat behind the drape, which is what it had been doing.
    """
    cy = (L.MD_WALL[0] + L.MD_WALL[1]) * 0.5
    w, d, h = 0.78, 0.36, 0.725          # w runs along Y, the console's length
    cx = L.EX - d / 2 - 0.012
    parts = []
    # Top: a slab with a moulded lip, overhanging the frame on all four sides.
    # The first attempt was a plain box on four splayed sticks - no lip, no
    # frame, no stretcher - which is why it read as a trestle rather than a
    # piece of furniture.
    top = mlib.box(name + "_top", -d / 2, -w / 2, h - 0.026, d / 2, w / 2, h,
                   cname)
    mlib.bevel(top, 0.006, 3, 42)
    parts.append((top, M['limed_y']))
    lip = mlib.box(name + "_lip", -d / 2 + 0.010, -w / 2 + 0.010, h - 0.040,
                   d / 2 - 0.010, w / 2 - 0.010, h - 0.026, cname)
    mlib.bevel(lip, 0.004, 2, 45)
    parts.append((lip, M['limed_y']))
    # Frame: four rails set back from the top's edge, with a shaped lower edge
    # on the long faces so the apron has a profile instead of a flat band.
    ix, iy = d / 2 - 0.030, w / 2 - 0.030
    for nm, a, b in ((name + "_rf", (ix - 0.022, -iy), (ix, iy)),
                     (name + "_rb", (-ix, -iy), (-ix + 0.022, iy)),
                     (name + "_rl", (-ix, -iy), (ix, -iy + 0.022)),
                     (name + "_rr", (-ix, iy - 0.022), (ix, iy))):
        rail = mlib.box(nm, a[0], a[1], h - 0.155, b[0], b[1], h - 0.040, cname)
        mlib.bevel(rail, 0.003, 2, 45)
        parts.append((rail, M['limed_y']))
    # Legs: square, tapered, standing at the frame's corners - not splayed.
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        pts = [(sx * (ix - 0.022), sy * (iy - 0.022), h - 0.040),
               (sx * (ix - 0.030), sy * (iy - 0.030), 0.0)]
        lg = mlib.tube_along(name + "_lg", pts,
                             mlib.rounded_rect(0.044, 0.044, 0.004, 2), cname)
        parts.append((lg, M['limed_v']))
    # Stretcher shelf low between the legs, as the crop shows under the console
    sh = mlib.box(name + "_sh", -ix + 0.030, -iy + 0.034, 0.175,
                  ix - 0.030, iy - 0.034, 0.196, cname)
    mlib.bevel(sh, 0.004, 2, 45)
    parts.append((sh, M['limed_y']))
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, 0.0))
    gilt = mats.get('paint_gilt') or mats.paint('paint_gilt', 'C9A24A',
                                                rough=0.30, coat=0.4)
    # the hung picture, then the pair of photographs standing on the console
    P.framed(name + "_art", 0.34, 0.42, (L.EX - 0.028, cy, 1.40), (-1, 0), cname,
             framemat=gilt, mat_w=0.055,
             artmat=mats.botanical('art_doorwall', normal=(-1, 0), seed=27,
                                   ground='E6DEC2', stem='4A5C34',
                                   leafc=('3F5730', '738650'),
                                   bloom=('9C6A78', 'DCC0C6')))
    # No standing photographs on the top.  P.framed builds a wall-hung frame, so
    # standing two of them on the console only ever put their backs through the
    # wall and their bottom rails into the timber - the hung picture above
    # carries this wall on its own.
    sconce(name + "_sc", (L.EX - 0.020, cy, 1.86), (-1, 0), M, cname=cname,
           energy=14.0)


# ----------------------------------------------------------------------- lamps
def table_lamp(name, cx, cy, cz, M, cname=C, energy=26.0, scale=1.0):
    parts = []
    base = mlib.revolve(name + "_base", [(0.0, 0.0), (0.075, 0.0), (0.078, 0.012),
                                         (0.058, 0.030), (0.040, 0.052),
                                         (0.046, 0.082), (0.056, 0.110),
                                         (0.048, 0.150), (0.028, 0.180),
                                         (0.020, 0.215), (0.020, 0.300),
                                         (0.0, 0.300)], 24, cname=cname)
    mlib.smooth_shade(base, 34)
    parts.append((base, M['brass']))
    sh = P.pleated_shade(name + "_shade", 0.105, 0.175, 0.20, 24, cname,
                         mats.get('shade_emis') or
                         mats.emissive('shade_emis', 'FFE6BE', strength=1.6,
                                       base='EDDFBE'))
    mlib.translate(sh, (0, 0, 0.285))
    parts.append((sh, None))
    bl = P.bulb(name + "_bulb", cname, e=22.0)
    mlib.translate(bl, (0, 0, 0.315))
    parts.append((bl, None))
    for ob, mm in parts:
        if mm:
            mlib.set_mat(ob, mm)
        mlib.scale_mesh(ob, (scale, scale, scale))
        mlib.translate(ob, (cx, cy, cz))
    P.point_light(name + "_light", (cx, cy, cz + 0.35 * scale), energy,
                  (1.0, 0.80, 0.60), 0.07)
    return parts


def floor_lamp(name, cx, cy, M, cname=C, energy=34.0):
    parts = []
    base = mlib.revolve(name + "_base", [(0.0, 0.0), (0.150, 0.0), (0.155, 0.014),
                                         (0.120, 0.030), (0.040, 0.042),
                                         (0.026, 0.060), (0.020, 0.090),
                                         (0.018, 1.30), (0.0, 1.30)], 24,
                        cname=cname)
    mlib.smooth_shade(base, 34)
    parts.append((base, M['brass']))
    sh = P.pleated_shade(name + "_shade", 0.130, 0.205, 0.235, 26, cname,
                         mats.get('shade_emis'))
    mlib.translate(sh, (0, 0, 1.26))
    parts.append((sh, None))
    bl = P.bulb(name + "_bulb", cname, e=22.0)
    mlib.translate(bl, (0, 0, 1.31))
    parts.append((bl, None))
    for ob, mm in parts:
        if mm:
            mlib.set_mat(ob, mm)
        mlib.translate(ob, (cx, cy, 0.0))
    P.point_light(name + "_light", (cx, cy, 1.36), energy, (1.0, 0.81, 0.62), 0.08)
    return parts


def ceiling_light(name, cx, cy, M, cname=C, energy=350.0, ztop=None,
                  drop=0.30, r=0.185, kelvin=5500.0):
    """The living room's overhead.  Not a chandelier - a plain semi-flush fitting
    of the kind every apartment of this vintage had: a frosted opal bowl slung
    a hand's width under the ceiling on three brass arms, with a turned finial
    under it.  A six-arm candle chandelier belongs in a dining room in a much
    grander flat than this one.

    Unconfirmable from the reference photos, which stop at the picture rail
    because the sets had no ceiling - see build_scripts/README.md."""
    import props as P
    ztop = ztop if ztop is not None else L.CZ
    parts = []
    rim_z = ztop - drop
    can = mlib.revolve(name + "_can", [(0.0, ztop - 0.004), (0.062, ztop - 0.008),
                                       (0.066, ztop - 0.024), (0.040, ztop - 0.038),
                                       (0.0, ztop - 0.040)], 22, cname=cname)
    parts.append(can)
    # three arms bowing out from the canopy to the bowl's rim
    for k in range(3):
        a = math.tau * k / 3 + math.radians(30.0)
        pts = []
        for i in range(13):
            t = i / 12.0
            rr = 0.038 + (r - 0.030) * math.sin(t * math.pi * 0.5)
            zz = (ztop - 0.032) - drop * 0.86 * (t ** 1.25)
            pts.append((rr * math.cos(a), rr * math.sin(a), zz))
        parts.append(mlib.tube_along(name + "_arm%d" % k, pts,
                                     mlib.circle(0.0062, 8), cname))
    # brass collar the glass sits in
    parts.append(mlib.revolve(name + "_rim",
                              [(r - 0.014, rim_z + 0.026), (r + 0.008, rim_z + 0.020),
                               (r + 0.010, rim_z + 0.006), (r - 0.006, rim_z - 0.004),
                               (r - 0.014, rim_z + 0.004)], 34, cname=cname))
    fin = mlib.revolve(name + "_fin",
                       [(0.0, rim_z - 0.150), (0.016, rim_z - 0.138),
                        (0.022, rim_z - 0.116), (0.014, rim_z - 0.098),
                        (0.026, rim_z - 0.080), (0.020, rim_z - 0.062),
                        (0.010, rim_z - 0.050), (0.0, rim_z - 0.048)], 18,
                       cname=cname)
    parts.append(fin)
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 38)
    mlib.set_mat(ob, M['brass'])
    # the opal bowl itself, opening upward, held in the collar
    prof = []
    for i in range(15):
        t = i / 14.0
        ang = math.pi * 0.52 * t
        prof.append((r * math.sin(ang) / math.sin(math.pi * 0.52),
                     rim_z + 0.020 - 0.115 * (1.0 - math.cos(ang))))
    sh = mlib.revolve(name + "_sh", prof, 34, cname=cname, cap_start=False,
                      cap_end=False)
    mlib.solidify(sh, 0.006, offset=0)
    mlib.smooth_shade(sh, 48)
    mlib.set_mat(sh, mats.get('opal_shade') or
                 mats.emissive('opal_shade', 'FFF0D2', strength=2.2,
                               base='F6EEDC'))
    out = [ob, sh]
    for k in range(2):
        bl = P.bulb(name + "_bl%d" % k, cname, e=26.0, r=0.024)
        mlib.translate(bl, (0.055 * (1 if k else -1), 0.0, rim_z - 0.048))
        out.append(bl)
    for o in out:
        mlib.translate(o, (cx, cy, 0.0))
    P.point_light(name + "_light", (cx, cy, rim_z + 0.010), energy,
                  P.blackbody(kelvin), 0.16)
    return out


def sconce(name, loc, normal, M, cname=C, energy=13.0):
    """Two-candle brass wall sconce with small shades."""
    parts = []
    bp = mlib.revolve(name + "_bp", [(0.0, 0.0), (0.052, 0.004), (0.056, 0.016),
                                     (0.030, 0.026), (0.0, 0.028)], 18, cname=cname)
    mlib.rot_x(bp, -math.pi / 2)
    parts.append(bp)
    for s in (-1, 1):
        arm = []
        for i in range(13):
            t = i / 12.0
            a = math.pi * 0.85 * t
            arm.append((s * 0.145 * math.sin(a) ** 0.8, 0.055 + 0.055 * t,
                        0.03 + 0.115 * (1 - math.cos(a)) * 0.6))
        parts.append(mlib.tube_along(name + "_arm", arm, mlib.circle(0.0075, 7),
                                     cname))
        cd = mlib.revolve(name + "_cd", [(0.0, 0.0), (0.024, 0.0), (0.024, 0.012),
                                         (0.013, 0.020), (0.013, 0.085),
                                         (0.0, 0.085)], 14, cname=cname)
        mlib.translate(cd, (s * 0.145, 0.11, 0.145))
        parts.append(cd)
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 38)
    mlib.set_mat(ob, M['brass'])
    shades = []
    for s in (-1, 1):
        sh = P.pleated_shade(name + "_sh", 0.042, 0.062, 0.075, 14, cname,
                             mats.get('shade_emis'))
        mlib.translate(sh, (s * 0.145, 0.11, 0.215))
        shades.append(sh)
        bl = P.bulb(name + "_bl", cname, e=16.0, r=0.016)
        mlib.scale_mesh(bl, (0.6, 0.6, 0.6))
        mlib.translate(bl, (s * 0.145, 0.11, 0.225))
        shades.append(bl)
    grp = [ob] + shades
    ang = math.atan2(normal[1], normal[0]) - math.pi / 2
    for o in grp:
        mlib.rotate_z(o, ang)
        mlib.translate(o, loc)
    P.point_light(name + "_light", (loc[0] + normal[0] * 0.14,
                                    loc[1] + normal[1] * 0.14, loc[2] + 0.20),
                  energy, (1.0, 0.74, 0.50), 0.06)
    return grp


# -------------------------------------------------------------------- poster
def text_mesh(name, body, size, cname=C, bold=False, extrude=0.0006,
              width=1.0, mat=None):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    cu.space_character = 1.0
    ob = bpy.data.objects.new(name, cu)
    mlib.put(ob, cname)
    mlib.active(ob)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.view_layer.objects.active
    if width != 1.0:
        mlib.scale_mesh(ob, (width, 1.0, 1.0))
    mlib.rot_x(ob, math.pi / 2)
    if mat:
        mlib.set_mat(ob, mat)
    return ob


def jouets_poster(name, M, cname=C):
    w, h = 1.24, 0.74
    cz = 1.81
    # Everything printed on the sheet below was laid out in absolute metres for
    # a 1.28 m poster, so resizing the sheet left the artwork stranded at its
    # old size in the middle of it.  k carries the whole layout with the sheet.
    k = w / 1.28
    gold = mats.paint('paint_poster_frame', 'C9A24A', rough=0.30, coat=0.45)
    parts = P.framed(name, w, h, (L.EX - 0.028, L.TV_SET_Y, cz), (-1, 0), cname,
                     framemat=gold, artmat=M['poster'], mat_w=0.0, fw=0.030,
                     fd=0.024)
    red = mats.paint('ink_red', '9A1B1E', rough=0.55, coat=0.0)
    dark = mats.paint('ink_dark', '2A211C', rough=0.6, coat=0.0)
    txt = []

    def put(ob, dx, dz):
        """text_mesh anchors its lines at a corner, not on their own centre, so
        every line used to sit at whatever x its own letter-count put it - which
        is why the top line ran off the sheet.  Measure each line and place it
        deliberately: dx is where its CENTRE lands."""
        xs = [v.co.x for v in ob.data.vertices]
        mlib.translate(ob, (dx - (min(xs) + max(xs)) * 0.5, 0.0, dz))
        return ob

    txt.append(put(text_mesh(name + "_t1", "AUX BUTTES CHAUMONT", 0.066 * k,
                             cname, mat=red, width=0.92), 0.0, h * 0.34))
    txt.append(put(text_mesh(name + "_t2", "Jouets", 0.20 * k, cname, mat=red,
                             width=1.0), 0.12 * k, h * 0.02))
    txt.append(put(text_mesh(name + "_t3", "ET  OBJETS  POUR  ETRENNES",
                             0.042 * k, cname, mat=dark, width=0.9),
                   0.15 * k, -h * 0.22))
    txt.append(put(text_mesh(name + "_t4", "MAISON  DU  PROGRES", 0.030 * k,
                             cname, mat=dark, width=0.9), 0.15 * k, -h * 0.35))
    # three harlequin figures printed bottom-left: skirt, torso, head, hat
    figs = []
    rng = random.Random(11)
    cols = [mats.paint('ink_fig_a', 'C43A2C', rough=0.58),
            mats.paint('ink_fig_b', 'D8A32A', rough=0.58),
            mats.paint('ink_fig_c', '3C4C74', rough=0.58)]
    for i, (bx, sc) in enumerate(((-w * 0.29, 1.00 * k), (-w * 0.20, 0.86 * k),
                                  (-w * 0.11, 0.94 * k))):
        bz = -h * 0.20 + rng.uniform(-0.01, 0.02)
        m2 = cols[i]
        skirt_p = [(bx - 0.042 * sc, bz), (bx + 0.042 * sc, bz),
                   (bx + 0.020 * sc, bz + 0.085 * sc),
                   (bx - 0.020 * sc, bz + 0.085 * sc)]
        torso_p = [(bx - 0.019 * sc, bz + 0.082 * sc),
                   (bx + 0.019 * sc, bz + 0.082 * sc),
                   (bx + 0.014 * sc, bz + 0.148 * sc),
                   (bx - 0.014 * sc, bz + 0.148 * sc)]
        for k, pp in enumerate((skirt_p, torso_p)):
            fg = mlib.prism_xz(name + "_fg%d_%d" % (i, k), pp, 0.0, 0.0007, cname)
            mlib.set_mat(fg, m2)
            figs.append(fg)
        hd = mlib.revolve(name + "_fh%d" % i, [(0.0, -0.017 * sc),
                                               (0.013 * sc, -0.010 * sc),
                                               (0.016 * sc, 0.0),
                                               (0.013 * sc, 0.010 * sc),
                                               (0.0, 0.017 * sc)], 12, cname=cname)
        mlib.scale_mesh(hd, (1.0, 0.04, 1.0))
        mlib.translate(hd, (bx, 0.0004, bz + 0.166 * sc))
        mlib.set_mat(hd, m2)
        figs.append(hd)
    for ob in txt + figs:
        mlib.rotate_z(ob, -math.pi / 2)
        # TV_SET_Y, same as the sheet - this line still said TV_C[1] after the
        # sheet moved off the cabinet's centre, so the whole printed layout sat
        # 0.26 m to one side of the paper it belongs on.
        mlib.translate(ob, (L.EX - 0.055, L.TV_SET_Y, cz))
    return parts


def carved_crest(name, M, cname=C):
    """Carved wooden pediment above the poster.  Well narrower than the poster,
    and standing clear of its top edge rather than sitting on it."""
    w, h = 0.70, 0.16
    pts = [(-w / 2, 0.0)]
    n = 26
    for i in range(n + 1):
        t = i / n
        x = -w / 2 + w * t
        z = h * (math.sin(math.pi * t) ** 0.55) * (0.65 + 0.35 *
                                                   abs(math.sin(t * 9.0)) ** 2)
        pts.append((x, z))
    pts.append((w / 2, 0.0))
    ob = mlib.prism_xz(name, pts, 0.0, 0.055, cname)
    mlib.bevel(ob, 0.008, 2, 45)
    mlib.smooth_shade(ob, 44)
    mlib.set_mat(ob, mats.wood('wood_crest', ('6A4020', '452408', '2A1404'),
                               ring=26, warp=0.05, distort=0.5, bump=0.4,
                               axis='YZ'))
    mlib.rotate_z(ob, math.pi / 2)
    # tucked up just under the picture rail at 2.73, not sitting on the poster
    mlib.translate(ob, (L.EX - 0.030, L.TV_SET_Y, 2.55))
    return ob


# ------------------------------------------------------------------ build all
def build():
    M = mk_mats()
    rug("LR_rug", M)
    sofa("LR_sofa", L.SOFA_C[0], L.SOFA_C[1], M, ln=L.SOFA_L)
    armchair("LR_armchair", L.CHAIR_ARM_WIN[0], L.CHAIR_ARM_WIN[1],
             math.radians(-90), M)
    # Red-and-white checked pillows on that armchair, as in the set photo -
    # they were a pale sage floral, which nothing in the references shows.
    for i, dy in enumerate((-0.16, 0.16)):
        ck = mlib.cushion("LR_ckpillow%d" % i, 0.12, 0.33, 0.34, 0.06, C)
        mlib.rot_y(ck, math.radians(-20))
        mlib.set_mat(ck, M['check'])
        mlib.translate(ck, (0.16, dy, 0.560))
        mlib.rotate_z(ck, math.radians(-90))
        mlib.translate(ck, (L.CHAIR_ARM_WIN[0], L.CHAIR_ARM_WIN[1], 0.0))
    # Cast-iron radiator.  It used to sit under the big window, entirely buried
    # inside the window seat's carcass; on the set that whole run is bench, so
    # the radiator lives in the return between the bench's east end and the
    # central wall, where it actually shows.
    rad = []
    rx0, rx1 = L.AL_X[1] - 0.42, L.AL_X[1] - 0.06
    n = 8
    for i in range(n):
        xx = rx0 + (rx1 - rx0) * i / (n - 1)
        fin = mlib.revolve("LR_radfin", [(0.0, 0.0), (0.030, 0.008),
                                         (0.034, 0.10), (0.030, 0.48),
                                         (0.020, 0.545), (0.0, 0.55)], 10,
                           cname=C)
        mlib.scale_mesh(fin, (1.0, 1.9, 1.0))
        mlib.translate(fin, (xx, L.AL_Y[1] - 0.16, 0.06))
        rad.append(fin)
    rad.append(mlib.box("LR_radbase", rx0 - 0.05, L.AL_Y[1] - 0.22, 0.0,
                        rx1 + 0.04, L.AL_Y[1] - 0.10, 0.075, C))
    ro = mlib.join(rad, "LR_radiator", C)
    mlib.smooth_shade(ro, 40)
    mlib.set_mat(ro, mats.paint('radiator_cream', 'BFB59A', rough=0.42, coat=0.15,
                                variation=0.05))
    slipper_chair("LR_slipper", L.CHAIR_SLIPPER[0], L.CHAIR_SLIPPER[1],
                  math.radians(L.SLIPPER_ROT), M)
    # the ottoman is that chair's footstool: squared up in front of it
    ofx, ofy = L.slipper_front(0.74)
    ottoman("LR_ottoman", ofx, ofy, math.radians(L.SLIPPER_ROT), M)
    coffee_table("LR_coffee", L.COFFEE_C[0], L.COFFEE_C[1], M, d=L.COFFEE_D)
    glass_table("LR_glasstable", L.GLASS_T[0], L.GLASS_T[1], M)
    # The room's key light.  No set photo can confirm this - those sets were
    # built open to the studio roof and lit from the grid, which is why the
    # frames stop at the picture rail - but this build has a real ceiling, and a
    # real ceiling wants the fixture an apartment would hang from it.  Declared
    # as a deliberate deviation in build_scripts/README.md, along with the rule
    # that no light in this scene may exist without an object to emit it.
    ceiling_light("LR_ceiling", L.CHANDELIER[0], L.CHANDELIER[1], M,
                  energy=350.0, kelvin=5500.0)
    credenza("LR_credenza", M)
    # Scaled up with the sideboard it stands on, and set towards its south end -
    # in the crop the set is right of centre, with the vase, the pair of bronze
    # figures and the fern filling the longer stretch to its left.
    crt_tv("LR_tv", 8.23, L.TV_SET_Y, 0.90, M, w=0.80, d=0.62, h=0.64)
    # Tucked in beside the sideboard with its face on the same line, not standing
    # 215 mm proud of it out into the room.  8.045 is the sideboard's front.
    speaker("LR_speaker", 8.045 + 0.20, L.TV_C[1] - L.CRED_HW - 0.19, M)
    window_seat("LR_seat", M)
    console_table("LR_console", M)
    door_wall("LR_doorwall", M)
    jouets_poster("LR_poster", M)
    carved_crest("LR_crest", M)
    # The pair of gilt-framed botanicals on the wall south of Rachel's doorway.
    # On the set they hang high - centred on that wall panel, in its upper half,
    # with the lower frame's bottom well clear of the slipper chair's back.
    gilt = mats.get('paint_gilt') or mats.paint('paint_gilt', 'C9A24A', rough=0.30,
                                                coat=0.4)
    botan_y = (L.SY + L.CD_Y[0]) * 0.5
    for i, (zz, w, h) in enumerate(((2.24, 0.38, 0.46), (1.60, 0.38, 0.46))):
        P.framed("LR_botan%d" % i, w, h, (L.EX - 0.028, botan_y, zz),
                 (-1, 0), C, framemat=gilt, mat_w=0.075,
                 artmat=mats.botanical(
                     'art_botan%d' % i, normal=(-1, 0), seed=3 + i,
                     ground='E9E1C6', stem=('4A5C30', '55663A')[i],
                     leafc=(('3E5A2A', '6E8348'), ('4A6234', '7C8E56'))[i],
                     bloom=(('B0705C', 'DFC3A4'), ('9A7C4E', 'E0D0A8'))[i]))
    # lamps
    table_lamp("LR_lamp1", (L.BW_X[0] + L.BW_X[1]) * 0.5 + 0.46,
               L.AL_Y[1] - L.SEAT_D - 0.30, 0.715, M, energy=24.0)
    # No floor lamp in the bay's east return.  It only ever existed to put
    # something in the strip behind the drapes, and that strip is now wall in
    # front of them, carrying the sconce over the console instead.
    # On the hallway's east wall, facing back down the hall.  It used to hang at
    # (4.625, 4.30) facing south - which was 320 mm clear of any wall even before
    # the short return was taken out, so it was lighting the hall from mid-air.
    sconce("LR_sconce", (L.HALL_X[0] + 0.020, L.NW_Y - 0.50, 1.86), (1, 0), M)
    # Drapes at the bay, now hung close to the glass rather than 1.42 m in front
    # of it.  The panels sit OUTBOARD of the window seat (x 4.80..8.08) instead
    # of overlapping its ends - at this rod line their lower folds would
    # otherwise hang straight through the bench.
    for k, (a, b2) in enumerate(((L.AL_X[0] + 0.02, L.BW_X[0] - 0.12),
                                 (L.BW_X[1] + 0.12, L.AL_X[1] - 0.03))):
        dp = P.curtain_panel("LR_drape%d" % k, a, b2, L.AL_Z - 0.06, 0.004,
                             depth=0.14, folds=4, cname=C, mat=M['drape'],
                             gather=0.5, flare=1.35, seed=11 + k, hem=0.016,
                             fullness=2.4)
        mlib.translate(dp, (0, L.AL_S + 0.13, 0))
    sw = P.swag("LR_valance", L.AL_X[0] + 0.30, L.AL_X[1] - 0.30, L.AL_Z - 0.04,
                sag=0.22, depth=0.13, folds=8, cname=C, mat=M['drape'])
    mlib.translate(sw, (0, L.AL_S + 0.11, 0))
    # curtain rod
    rod = mlib.revolve("LR_rod", [(0.0, 0.0), (0.016, 0.0), (0.016, L.AL_X[1] -
                                                             L.AL_X[0]),
                                  (0.0, L.AL_X[1] - L.AL_X[0])], 14, cname=C)
    mlib.rot_y(rod, math.pi / 2)
    mlib.translate(rod, (L.AL_X[0], L.AL_S + 0.16, L.AL_Z - 0.02))
    mlib.smooth_shade(rod, 34)
    mlib.set_mat(rod, mats.wood('wood_rod', ('5A3418', '3A1E0A', '221004'),
                                ring=60, warp=0.03, bump=0.2, axis='YZ'))
    # plants
    # In the set photo this is a big spiky palm standing as high as the poster,
    # not a tabletop fern on the floor.
    # `r` and `scale` multiply, and the crown must sit exactly one pot-height up
    # (r * 0.62) or the pot hangs in the air - which it had been doing all along.
    # It stands in the gap between the sideboard's north end and Monica's door,
    # fronds lapping over the sideboard exactly as in the crop - but the pot has
    # to clear the carcass in x, and at r=0.55 the fronds reached 0.20 into the
    # door void, so it is sized to the gap it actually has.
    # ON the sideboard at its north end, beside the vase - not standing on the
    # floor.  Sized so its fronds spill over that end without reaching through
    # the wall behind: at r = 0.32 they span 0.76 m, and the cabinet's face is
    # only 0.52 m off the plaster.
    P.fern("LR_fern", (8.12, L.TV_C[1] + 1.02, 0.900 + 0.32 * 0.62), 0.32,
           30, 3, C, True, M['leaf'], M['terra'])
    # Standing ON the speaker, not on the floor beside it.  trailing_plant's z
    # is the pot's RIM, not its base, so the speaker's 0.66 top plus the pot's
    # own 0.124 height is what puts it down on the cabinet.
    P.trailing_plant("LR_pothos", (8.245, L.TV_C[1] - L.CRED_HW - 0.19, 0.824),
                     14, 6, C, M['leaf'], M['wicker'], 0.13)
    # Credenza-top dressing.  The set photo has one thing on this top beside the
    # television: a tall vase of yellow blooms at the far end.  The two little
    # bronze figures that stood here are in none of the references and read as
    # turned bowling pins, so they are gone.
    # Two small bronze figures stand on the credenza top beside the vase.  I had
    # removed these as unattested; cropping into the sideboard in the living-room
    # photo shows both of them plainly, so they are back.
    for i, (dy, hh, tw) in enumerate(((0.32, 0.155, 0.030), (0.44, 0.205, 0.023))):
        prof = [(0.0, 0.0), (tw * 1.5, 0.006), (tw * 1.6, 0.016),
                (tw * 0.62, 0.030), (tw * 0.50, hh * 0.42),
                (tw * 0.86, hh * 0.60), (tw * 0.66, hh * 0.78),
                (tw * 0.30, hh * 0.93), (0.0, hh)]
        fg = mlib.revolve("LR_figure%d" % i, prof, 18, cname=C)
        mlib.smooth_shade(fg, 42)
        mlib.rotate_z(fg, 0.5 + i)
        mlib.set_mat(fg, mats.metal('metal_bronze_fig', '6E5230', rough=0.42,
                                    bump=0.09))
        mlib.translate(fg, (8.16 + 0.03 * i, L.TV_C[1] + dy, 0.900))
    credenza_flowers("LR_vase", 8.14, L.TV_C[1] + 0.56, 0.900, M,
                     random.Random(23))
    dress(M)
    print("living built")
    return M


def book(name, w, d, h, cover, cname=C, mag=False):
    """A book, not a coloured slab: a cream page block set in slightly from a
    wrapped cover, with a rounded spine down one long edge."""
    pgs = mats.get('book_pages') or mats.paint('book_pages', 'E4DDC8', rough=0.62,
                                               variation=0.05)
    ct = 0.0022 if mag else 0.0035
    parts = []
    blk = mlib.box(name + "_pg", -w / 2 + ct, -d / 2 + 0.005, ct,
                   w / 2 - 0.006, d / 2 - 0.005, h - ct, cname)
    mlib.bevel(blk, 0.0012, 2, 45)
    parts.append((blk, pgs))
    for z0, z1 in ((0.0, ct), (h - ct, h)):
        bd = mlib.box(name + "_bd", -w / 2, -d / 2, z0, w / 2, d / 2, z1, cname)
        mlib.bevel(bd, 0.0012, 2, 45)
        parts.append((bd, cover))
    sp = mlib.prism(name + "_sp",
                    [(-w / 2, -d / 2), (-w / 2 + ct * 2.2, -d / 2),
                     (-w / 2 + ct * 2.2, d / 2), (-w / 2, d / 2)], 0.0, h, cname)
    mlib.bevel(sp, min(0.004, h * 0.35), 3, 55)
    parts.append((sp, cover))
    objs = []
    for o, mm in parts:
        mlib.set_mat(o, mm)
        objs.append(o)
    return mlib.join(objs, name, cname)


# ---------------------------------------------------------------- dressing
def dress(M):
    rng = random.Random(31)
    pool = P.palette(55, 12)
    cx, cy = L.COFFEE_C
    # magazines on the lower shelf and books on the top
    for i in range(4):
        bk = book("LR_mag%d" % i, 0.230, 0.300, rng.uniform(0.006, 0.011),
                  rng.choice(pool), C, mag=True)
        mlib.rotate_z(bk, rng.uniform(-0.30, 0.30))
        mlib.translate(bk, (cx + rng.uniform(-0.08, 0.08),
                            cy + rng.uniform(-0.28, 0.28), 0.157 + i * 0.011))
    for i, dy in enumerate((-0.34, 0.30)):
        z = 0.436
        for k in range(rng.randint(2, 3)):
            h = rng.uniform(0.021, 0.034)
            bk = book("LR_bk%d_%d" % (i, k), 0.210 - k * 0.012,
                      0.270 - k * 0.014, h, rng.choice(pool), C)
            mlib.rotate_z(bk, rng.uniform(-0.3, 0.3))
            mlib.translate(bk, (cx + rng.uniform(-0.08, 0.08), cy + dy, z))
            z += h + 0.001
    # a shallow white dish + a candle on the coffee table
    for o in P.bowl("LR_dish", 0.115, 0.038, C,
                    mats.paint('bowl_white2', 'EAE3D2', rough=0.16, coat=0.5)):
        mlib.translate(o, (cx + 0.02, cy + 0.02, 0.437))
    cnd = mlib.revolve("LR_candle", [(0.0, 0.0), (0.035, 0.0), (0.035, 0.115),
                                     (0.030, 0.125), (0.0, 0.128)], 18, cname=C)
    mlib.smooth_shade(cnd, 40)
    mlib.set_mat(cnd, mats.paint('wax_cream', 'E4DBC0', rough=0.42))
    mlib.translate(cnd, (cx - 0.20, cy - 0.10, 0.437))
    # phone + a tissue box on the glass table
    ph = []
    body = mlib.box("LR_phone", -0.085, -0.055, 0.0, 0.085, 0.055, 0.038, C)
    mlib.bevel(body, 0.006, 2, 45)
    ph.append(body)
    hs = mlib.prism("LR_phone_h", mlib.rounded_rect(0.175, 0.045, 0.018, 4),
                    0.038, 0.070, C)
    mlib.bevel(hs, 0.008, 2, 45)
    ph.append(hs)
    po = mlib.join(ph, "LR_phone", C)
    mlib.set_mat(po, mats.paint('phone_black', '1E1C1A', rough=0.28, coat=0.4))
    mlib.rotate_z(po, 0.4)
    mlib.translate(po, (L.GLASS_T[0] - 0.05, L.GLASS_T[1] + 0.11, 0.601))
    # two little round tapestry stools stacked beside the glass table
    for i, (dz, rr) in enumerate(((0.0, 0.145), (0.115, 0.135))):
        st = mlib.revolve("LR_stool%d" % i, [(0.0, 0.0), (rr, 0.010),
                                             (rr * 1.02, 0.055), (rr * 0.92, 0.100),
                                             (rr * 0.6, 0.112), (0.0, 0.114)],
                          24, cname=C)
        mlib.smooth_shade(st, 40)
        mlib.set_mat(st, M['stool_tap'])
        mlib.translate(st, (L.STOOLS[0], L.STOOLS[1], dz))
    # a jug of tulips on the window-seat console
    ccx = (L.BW_X[0] + L.BW_X[1]) * 0.5
    ccy = L.AL_Y[1] - L.SEAT_D - 0.30
    jug = mlib.revolve("LR_jug", [(0.0, 0.0), (0.062, 0.0), (0.070, 0.020),
                                  (0.078, 0.075), (0.070, 0.130), (0.048, 0.160),
                                  (0.046, 0.180), (0.052, 0.192), (0.046, 0.196),
                                  (0.040, 0.182), (0.042, 0.160), (0.0, 0.155)],
                       24, cname=C)
    mlib.smooth_shade(jug, 34)
    mlib.set_mat(jug, mats.paint('ceramic_pewter', '8E9084', rough=0.22, coat=0.5))
    mlib.translate(jug, (ccx - 0.42, ccy, 0.715))
    stems, blooms = [], []
    for i in range(9):
        a = rng.uniform(0, math.tau)
        ln = rng.uniform(0.16, 0.28)
        pts = [(0, 0, 0.19)]
        for k in range(1, 6):
            t = k / 5.0
            pts.append((math.cos(a) * 0.075 * t ** 1.6, math.sin(a) * 0.075 * t ** 1.6,
                        0.19 + ln * t))
        stems.append(mlib.tube_along("LR_stem", pts, mlib.circle(0.0032, 5), C))
        bl = mlib.revolve("LR_bloom", [(0.0, 0.0), (0.020, 0.012), (0.026, 0.034),
                                       (0.022, 0.052), (0.0, 0.056)], 12, cname=C)
        mlib.translate(bl, pts[-1])
        blooms.append(bl)
    so = mlib.join(stems, "LR_stems", C)
    mlib.set_mat(so, M['leaf'])
    bo2 = mlib.join(blooms, "LR_blooms", C)
    mlib.smooth_shade(bo2, 40)
    mlib.set_mat(bo2, mats.paint('tulip_yellow', 'D9AE22', rough=0.44))
    for o in (so, bo2):
        mlib.translate(o, (ccx - 0.42, ccy, 0.715))

