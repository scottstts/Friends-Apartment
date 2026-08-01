"""mats - fully procedural materials for the apartment.  No image files,
no external assets: every surface is a node graph (plus, for the parquet,
real per-piece UVs and vertex colours generated at build time)."""
import bpy, math, colorsys

# ------------------------------------------------------------------ node help

class NB:
    """Tiny node-graph builder."""
    def __init__(self, mat):
        self.mat = mat
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.col = 0

    def n(self, kind, x=None, y=0, **kw):
        nd = self.nt.nodes.new(kind)
        self.col += 1
        nd.location = (x if x is not None else -260 * self.col, y)
        for k, v in kw.items():
            if k.startswith("i_"):
                key = k[2:].replace("_", " ")
                try:
                    nd.inputs[key].default_value = v
                except Exception:
                    nd.inputs[int(key)].default_value = v
            else:
                setattr(nd, k, v)
        return nd

    def l(self, a, ao, b, bi):
        so = a.outputs[ao] if isinstance(ao, str) else a.outputs[ao]
        si = b.inputs[bi] if isinstance(bi, str) else b.inputs[bi]
        self.nt.links.new(so, si)

    def out(self, shader):
        o = self.n('ShaderNodeOutputMaterial', x=300)
        self.l(shader, 0, o, 'Surface')
        return o

    # -- convenience -------------------------------------------------------
    def coord(self, kind='Object'):
        tc = self.n('ShaderNodeTexCoord', x=-1800)
        return tc, kind

    def mapping(self, src, srco, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), x=-1600):
        m = self.n('ShaderNodeMapping', x=x)
        m.inputs['Scale'].default_value = scale
        m.inputs['Location'].default_value = loc
        m.inputs['Rotation'].default_value = rot
        self.l(src, srco, m, 'Vector')
        return m

    def noise(self, vec, scale=5.0, detail=6.0, rough=0.5, dist=0.0, x=-1400, dim=None):
        nd = self.n('ShaderNodeTexNoise', x=x)
        if dim:
            nd.noise_dimensions = dim
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Distortion'].default_value = dist
        if vec is not None:
            self.l(vec[0], vec[1], nd, 'Vector')
        return nd

    def ramp(self, src, srco, stops, x=-1100, interp='LINEAR'):
        r = self.n('ShaderNodeValToRGB', x=x)
        r.color_ramp.interpolation = interp
        el = r.color_ramp.elements
        while len(el) > len(stops):
            el.remove(el[-1])
        for i, (p, c) in enumerate(stops):
            if i >= len(el):
                el.new(p)
            el[i].position = p
            el[i].color = c if len(c) == 4 else (c[0], c[1], c[2], 1.0)
        self.l(src, srco, r, 'Fac')
        return r

    def mix(self, a, ao, b, bo, fac, faco=None, blend='MIX', x=-900, factor=None):
        m = self.n('ShaderNodeMix', x=x, data_type='RGBA', blend_type=blend)
        if fac is None:
            m.inputs['Factor'].default_value = factor if factor is not None else 0.5
        else:
            self.l(fac, faco if faco is not None else 0, m, 'Factor')
        if isinstance(a, tuple):
            m.inputs['A'].default_value = _c(a)
        else:
            self.l(a, ao, m, 'A')
        if isinstance(b, tuple):
            m.inputs['B'].default_value = _c(b)
        else:
            self.l(b, bo, m, 'B')
        return m

    def math(self, op, a=None, ao=0, b=None, bo=0, va=None, vb=None, x=-1000, clamp=False):
        m = self.n('ShaderNodeMath', x=x, operation=op, use_clamp=clamp)
        if a is not None:
            self.l(a, ao, m, 0)
        elif va is not None:
            m.inputs[0].default_value = va
        if b is not None:
            self.l(b, bo, m, 1)
        elif vb is not None:
            m.inputs[1].default_value = vb
        return m

    def vmath(self, op, a=None, ao=0, b=None, bo=0, va=None, vb=None, x=-1000):
        m = self.n('ShaderNodeVectorMath', x=x, operation=op)
        if a is not None:
            self.l(a, ao, m, 0)
        elif va is not None:
            m.inputs[0].default_value = va
        if b is not None:
            self.l(b, bo, m, 1)
        elif vb is not None:
            m.inputs[1].default_value = vb
        return m

    def bump(self, height, ho=0, strength=0.3, dist=1.0, x=-500, normal=None):
        b = self.n('ShaderNodeBump', x=x)
        b.inputs['Strength'].default_value = strength
        b.inputs['Distance'].default_value = dist
        self.l(height, ho, b, 'Height')
        if normal is not None:
            self.l(normal, 'Normal', b, 'Normal')
        return b

    def principled(self, base=None, baseo=0, color=None, rough=0.45, roughn=None,
                   rougho=0, metal=0.0, normal=None, spec=0.5, x=0, ior=1.45,
                   sheen=0.0, coat=0.0, transm=0.0, emis=None, emis_str=0.0,
                   aniso=0.0, sheen_tint=None):
        p = self.n('ShaderNodeBsdfPrincipled', x=x)
        p.inputs['Roughness'].default_value = rough
        p.inputs['Metallic'].default_value = metal
        p.inputs['IOR'].default_value = ior
        try:
            p.inputs['Specular IOR Level'].default_value = spec
        except Exception:
            pass
        if sheen:
            p.inputs['Sheen Weight'].default_value = sheen
            p.inputs['Sheen Roughness'].default_value = 0.35
            # an untinted sheen lobe washes cloth out to white - tint it
            st = sheen_tint if sheen_tint is not None else (color or (0.5,) * 3)
            p.inputs['Sheen Tint'].default_value = _c(st)
        if coat:
            p.inputs['Coat Weight'].default_value = coat
            p.inputs['Coat Roughness'].default_value = 0.06
        if transm:
            p.inputs['Transmission Weight'].default_value = transm
        if anisoing := aniso:
            p.inputs['Anisotropic'].default_value = anisoing
        if color is not None:
            p.inputs['Base Color'].default_value = _c(color)
        if base is not None:
            self.l(base, baseo, p, 'Base Color')
        if roughn is not None:
            self.l(roughn, rougho, p, 'Roughness')
        if normal is not None:
            self.l(normal, 'Normal', p, 'Normal')
        if emis is not None:
            self.l(emis, 0, p, 'Emission Color')
            p.inputs['Emission Strength'].default_value = emis_str
        elif emis_str:
            p.inputs['Emission Strength'].default_value = emis_str
        return p


def wall_proj(b, x=-2400):
    """Vector that runs along a vertical surface: u = horizontal arc-length in
    the wall plane, v = z.  Works for any wall azimuth (including the 45 deg
    chamfer) without seams or ghosting."""
    tc = b.n('ShaderNodeTexCoord', x=x)
    geo = b.n('ShaderNodeNewGeometry', x=x, y=-520)
    sp = b.n('ShaderNodeSeparateXYZ', x=x + 200)
    b.l(tc, 'Object', sp, 'Vector')
    sn = b.n('ShaderNodeSeparateXYZ', x=x + 200, y=-520)
    b.l(geo, 'True Normal', sn, 'Vector')
    nx2 = b.math('MULTIPLY', sn, 0, sn, 0, x=x + 380)
    ny2 = b.math('MULTIPLY', sn, 1, sn, 1, x=x + 380)
    ny2.location = (x + 380, -300)
    s = b.math('ADD', nx2, 0, ny2, 0, x=x + 540)
    ln = b.math('SQRT', s, 0, x=x + 680)
    safe = b.math('MAXIMUM', ln, 0, vb=0.06, x=x + 820)
    a1 = b.math('MULTIPLY', sp, 0, sn, 1, x=x + 380)
    a1.location = (x + 380, 300)
    a2 = b.math('MULTIPLY', sp, 1, sn, 0, x=x + 380)
    a2.location = (x + 380, 460)
    d = b.math('SUBTRACT', a1, 0, a2, 0, x=x + 540)
    d.location = (x + 540, 380)
    u = b.math('DIVIDE', d, 0, safe, 0, x=x + 960)
    cmb = b.n('ShaderNodeCombineXYZ', x=x + 1100)
    b.l(u, 0, cmb, 'X')
    b.l(sp, 2, cmb, 'Y')
    return cmb


def _c(c):
    if len(c) == 3:
        return (c[0], c[1], c[2], 1.0)
    return tuple(c)


def srgb(h):
    """hex -> linear rgba"""
    if isinstance(h, str):
        h = h.lstrip('#')
        r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    else:
        r, g, b = h
    f = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


_CACHE = {}


def _mat(name):
    """Reuse the datablock if it already exists (NB clears its node tree), so
    rebuilding a material never orphans the objects that reference it."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    return m


def get(name):
    return bpy.data.materials.get(name)


# ================================================================== WOOD

def wood(name, cols, ring=26.0, warp=0.55, rough=(0.28, 0.52), coord='Object',
         axis='X', bump=0.16, pore=1.0, tint_attr=None, sheen=0.0, scale=1.0,
         aniso=0.35, distort=1.6, blotch=0.16, warp_scale=1.6, translucent=0.0,
         grain_relief=0.16):
    # `grain_relief` is how far the ring cuts into the normal.  It defaulted to
    # 0.55, which engraves a groove per ring: on anything finished - a table
    # top, a turned leg - that reads as a contour map ruled onto the surface,
    # because the shading comes from the relief and not from the timber.  Sawn
    # or weathered stock wants it back up; polished furniture wants almost none.
    """Generic procedural wood.
    cols: 3 hex colours (light early-wood, mid, dark late-wood/figure)."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2200)
    src, so = tc, ('UV' if coord == 'UV' else 'Object')
    # `axis` names the axis the growth rings vary along; grain lines run
    # perpendicular to it.  Pick the one that is constant along the member.
    ROT = {
        'X':  (0, 0, 0),                                   # rings vary with x
        'Y':  (0, 0, math.pi / 2),                          # with y
        'Z':  (0, math.pi / 2, 0),                          # with z
        'XY': (0, 0, -math.pi / 4),                         # with (x+y)
        'XZ': (0, math.pi / 4, 0),                          # with (x+z)
        'YZ': (0, math.pi / 2, -math.pi / 4),               # with (y+z)
        'D':  (0, 0, math.radians(32)),
    }
    rot = ROT.get(axis, (0, 0, 0))
    sc = (scale, scale, scale)
    mp = b.mapping(src, so, scale=sc, rot=rot, x=-2020)

    sep = b.n('ShaderNodeSeparateXYZ', x=-1860)
    b.l(mp, 'Vector', sep, 'Vector')

    # `warp` and `distort` are displacements of the ring axis in metres, but what
    # they actually do depends on how far apart the rings are.  Shove the axis by
    # much more than half a ring period and the grain folds back through itself
    # and closes into islands - the blotchy contour-map look, which is not
    # cathedral figure but the absence of it.  Hold the total against the ring
    # period so no caller can ask for that; anything already gentle is untouched.
    _amp = abs(warp) * 1.33 + abs(distort) * 0.055
    _k = min(1.0, (0.55 / max(ring, 1e-6)) / _amp) if _amp > 1e-9 else 1.0
    warp, distort = warp * _k, distort * _k

    # Compress the palette towards its own mean if the caller has asked for more
    # early-to-late-wood contrast than timber actually shows.  Past roughly a
    # third in luminance the rings stop reading as grain and start reading as
    # painted stripes - shown on the table top, where holding the ring ramp at a
    # single tone wiped the banding out completely while flattening the ring
    # *bump* changed nothing at all.  Palettes already inside this are untouched.
    _cl = [tuple(srgb(c)[:3]) for c in cols]
    _lum = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in _cl]
    _hi, _lo = max(_lum), min(_lum)
    if _hi > 1e-6 and (_hi - _lo) / _hi > 0.34:
        _t = 0.34 * _hi / (_hi - _lo)
        _md = [sum(c[i] for c in _cl) / 3.0 for i in range(3)]
        _cl = [tuple(_md[i] + (c[i] - _md[i]) * _t for i in range(3)) for c in _cl]

    # Two octaves of wander on the ring axis.  One scale alone gives rings that
    # all bend the same way at the same place, which reads as machine-pressed.
    wn = b.noise((mp, 'Vector'), scale=warp_scale, detail=3.0, rough=0.6, x=-1980,
                 dim='3D')
    wn.location = (-1980, -300)
    w1 = b.math('MULTIPLY_ADD', wn, 'Fac', vb=warp, x=-1840)
    w1.location = (-1840, -300)
    w1.inputs[2].default_value = -0.5 * warp
    wn2 = b.noise((mp, 'Vector'), scale=warp_scale * 4.3, detail=3.0, rough=0.55,
                  x=-1980, dim='3D')
    wn2.location = (-1980, -480)
    w2 = b.math('MULTIPLY_ADD', wn2, 'Fac', vb=warp * 0.33, x=-1840)
    w2.location = (-1840, -480)
    w2.inputs[2].default_value = -0.5 * warp * 0.33
    # Cathedral figure: a very low-frequency, large-amplitude shove of the ring
    # axis.  This used to come from the wave node's Distortion, but that noise
    # is sampled at the *ring-scaled* coordinate, so raising `ring` raised the
    # distortion frequency with it and the two compounded into extra rings.
    wn3 = b.noise((mp, 'Vector'), scale=0.42, detail=2.0, rough=0.5, x=-1980,
                  dim='3D')
    wn3.location = (-1980, -660)
    w3 = b.math('MULTIPLY_ADD', wn3, 'Fac', vb=distort * 0.055, x=-1840)
    w3.location = (-1840, -660)
    w3.inputs[2].default_value = -0.5 * distort * 0.055
    w12 = b.math('ADD', w1, 0, w2, 0, x=-1700)
    w12.location = (-1700, -380)
    wsc = b.math('ADD', w12, 0, w3, 0, x=-1640)
    wsc.location = (-1640, -520)
    warped = b.math('ADD', sep, 0, wsc, 0, x=-1560)

    # Ring spacing must not be constant: real growth years vary in width, and a
    # fixed period is exactly what makes procedural timber look like corduroy.
    #
    # This is a phase offset added after the ring count, NOT a varying
    # multiplier on the coordinate.  Multiplying meant the wobble was amplified
    # by however far the surface happened to sit from the world origin - fine at
    # x = 0, but this flat is twelve metres across and the parquet's UVs are
    # offset by up to nine more, so out there a few per cent of density noise
    # became hundreds of rings of swing and the grain closed into whorls.
    dn = b.noise((mp, 'Vector'), scale=0.55, detail=2.0, rough=0.5, x=-1700)
    dn.location = (-1700, -160)
    dj = b.math('MULTIPLY_ADD', dn, 'Fac', vb=ring * 0.72, x=-1560)
    dj.location = (-1560, -160)
    dj.inputs[2].default_value = -0.36 * ring

    # The rings themselves: frac(axis * rings-per-metre).  An explicit sawtooth
    # means `ring` is exactly the ring count per metre - a wave node's SIN
    # profile crossed the dark ramp stop twice per cycle, and its distortion
    # added still more crossings, so the nominal count bore no relation to what
    # was drawn.  The wrap's discontinuity is the sharp late-wood/early-wood
    # edge real timber has.
    r0 = b.math('MULTIPLY', warped, 0, vb=ring, x=-1480)
    r0.location = (-1480, -160)
    rr = b.math('ADD', r0, 0, dj, 0, x=-1440)
    rr.location = (-1440, -260)
    grain = b.math('WRAP', rr, 0, x=-1400)
    grain.inputs[1].default_value = 1.0
    grain.inputs[2].default_value = 0.0

    # Early-wood field, then a long soft darkening into the late-wood, and the
    # saw's reset as the abrupt edge back to early-wood.  A short, sharp dark
    # line on a flat field is what made the first pass read as a contour map;
    # timber darkens gradually across the ring and only snaps back at the edge.
    ramp = b.ramp(grain, 0, [(0.00, _cl[0]), (0.34, _cl[0]),
                             (0.74, _cl[1]), (0.97, _cl[2]),
                             (1.0, _cl[2])],
                  x=-1180)
    # Pull the whole ramp back towards its own mean.  A three-colour ramp taken
    # at full strength gives the flat, high-contrast banding of marbled paper;
    # timber lit in a room shows far less local contrast than that.
    _m = [sum(c[i] for c in _cl) / 3.0 for i in range(3)]
    soft = b.mix(ramp, 'Color', tuple(_m), 0, None, blend='MIX', x=-1100,
                 factor=0.30)
    soft.location = (-1100, 300)

    # Grain strength has to vary too.  Over a wide stretch of a real board the
    # figure fades almost to plain, then comes back; a uniform ring contrast
    # everywhere is the other half of the corduroy read.
    gn = b.noise((mp, 'Vector'), scale=1.35, detail=3.0, rough=0.55, x=-1400)
    gn.location = (-1400, 640)
    gm = b.ramp(gn, 'Fac', [(0.24, (0.34, 0.34, 0.34)), (0.78, (1, 1, 1))], x=-1180)
    gm.location = (-1180, 640)
    faded = b.mix(tuple(_m), 0, soft, 'Result', gm, 'Color', blend='MIX', x=-1020)
    faded.location = (-1020, 480)

    # Broad tonal blotches - some boards are warmer or darker over a whole
    # stretch.  The factor socket is driven by `bl`, so `blotch` has to scale
    # that signal; setting it as the socket default did nothing at all.
    blot = b.noise((mp, 'Vector'), scale=0.9, detail=4.0, rough=0.65, x=-1400)
    blot.location = (-1400, 420)
    bl = b.ramp(blot, 'Fac', [(0.32, (0, 0, 0)), (0.72, (1, 1, 1))], x=-1180)
    bl.location = (-1180, 420)
    blf = b.math('MULTIPLY', bl, 'Color', vb=blotch, x=-1020)
    blf.location = (-1020, 300)
    col = b.mix(faded, 'Result', (0.60, 0.50, 0.36), 0, None, blend='MULTIPLY',
                x=-940, factor=1.0)
    col2 = b.mix(faded, 'Result', col, 'Result', blf, 0, blend='MIX', x=-800)

    # Fine pores / medullary flecks -> bump + roughness break-up.  These must NOT
    # ride on `cmb`, whose X is already multiplied by `ring`: at ring=100+ that
    # drove the pore noise to thousands of cycles per metre and every wooden
    # surface - floor, beams, tables, the credenza - read as fine corduroy.
    # Pores are only mildly anisotropic: a little tighter across the grain than
    # along it.
    pcmb = b.n('ShaderNodeCombineXYZ', x=-1520, y=-640)
    prx = b.math('MULTIPLY', warped, 0, vb=6.0, x=-1600)
    prx.location = (-1600, -640)
    b.l(prx, 0, pcmb, 'X')
    b.l(sep, 1, pcmb, 'Y')
    b.l(sep, 2, pcmb, 'Z')
    pn = b.noise((pcmb, 'Vector'), scale=42.0 * pore, detail=6.0, rough=0.72,
                 x=-1400)
    pn.location = (-1400, -640)
    fine = b.n('ShaderNodeTexNoise', x=-1400, y=-940)
    fine.inputs['Scale'].default_value = 220.0
    fine.inputs['Detail'].default_value = 4.0
    b.l(mp, 'Vector', fine, 'Vector')

    # Height must not use the raw saw: its 1->0 reset is a step, and a step in a
    # bump map is a hard ridge, so every ring came out engraved.  Ramp it into a
    # shallow trough that starts and ends at the same level instead.
    gh = b.ramp(grain, 0, [(0.00, (0.55, 0.55, 0.55)), (0.34, (0.62,) * 3),
                           (0.80, (0.16,) * 3), (1.0, (0.55, 0.55, 0.55))],
                x=-1080)
    gh.location = (-1080, -880)
    # How much of the surface relief comes from the growth rings.  Flattening
    # the ring *colour* is not enough on its own: the rings still cut a trough
    # in the bump map, and that relief alone is enough to draw the same parallel
    # bands.  Big stained timber wants nearly none of this.
    gw = b.math('MULTIPLY', gh, 'Color', vb=grain_relief, x=-1080)
    gw.location = (-1080, -1060)
    hmix = b.math('ADD', gw, 0, pn, 'Fac', x=-1080)
    hmix.location = (-1080, -700)
    h2 = b.math('MULTIPLY_ADD', hmix, 0, vb=0.5, x=-940)
    h2.inputs[2].default_value = 0.0
    h3 = b.math('ADD', h2, 0, fine, 'Fac', x=-800)
    bmp = b.bump(h3, 0, strength=bump, dist=0.4, x=-620)

    rn = b.ramp(pn, 'Fac', [(0.25, (rough[0],) * 3), (0.85, (rough[1],) * 3)], x=-620)
    rn.location = (-620, -420)

    if tint_attr:
        at = b.n('ShaderNodeAttribute', x=-1180, y=800)
        at.attribute_name = tint_attr
        tint = b.mix(col2, 'Result', at, 'Color', None, blend='MULTIPLY', x=-380,
                     factor=0.85)
        base_src, base_o = tint, 'Result'
    else:
        base_src, base_o = col2, 'Result'

    p = b.principled(base=base_src, baseo=base_o, roughn=rn, rougho='Color',
                     normal=bmp, spec=0.5, sheen=sheen, x=-120, aniso=aniso)
    if translucent:
        # thin timber - a matchstick blind, a lampshade slat - glows when it is
        # backlit.  Without this a shade hung against daylight just reads as a
        # dark plate, because all the light is on the far side of it.
        tr = b.n('ShaderNodeBsdfTranslucent', x=-120, y=-320)
        b.l(base_src, base_o, tr, 'Color')
        mx = b.n('ShaderNodeMixShader', x=40)
        mx.inputs['Fac'].default_value = translucent
        b.l(p, 0, mx, 1)
        b.l(tr, 0, mx, 2)
        b.out(mx)
    else:
        b.out(p)
    return m


# ================================================================== PAINT

def paint(name, hexcol, rough=0.36, sheen=0.0, coat=0.0, bump=0.02, noise=140.0,
          variation=0.03):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1400)
    n1 = b.noise((tc, 'Object'), scale=noise, detail=3.0, rough=0.5, x=-1200)
    n2 = b.noise((tc, 'Object'), scale=2.4, detail=4.0, rough=0.6, x=-1200)
    n2.location = (-1200, -320)
    base = srgb(hexcol)
    dark = tuple(c * (1.0 - variation) for c in base[:3])
    lite = tuple(min(1.0, c * (1.0 + variation)) for c in base[:3])
    col = b.mix(dark, 0, lite, 0, n2, 'Fac', x=-900)
    rn = b.ramp(n1, 'Fac', [(0.3, (rough * 0.86,) * 3), (0.8, (rough * 1.14,) * 3)], x=-900)
    rn.location = (-900, -320)
    bmp = b.bump(n1, 'Fac', strength=bump, dist=0.3, x=-620)
    p = b.principled(base=col, baseo='Result', roughn=rn, rougho='Color', normal=bmp,
                     sheen=sheen, coat=coat, x=-300)
    b.out(p)
    return m


def plaster(name, hexcol, rough=0.72, bump=0.28, scale=26.0):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1500)
    n1 = b.noise((tc, 'Object'), scale=scale, detail=8.0, rough=0.62, x=-1300)
    n2 = b.noise((tc, 'Object'), scale=1.1, detail=5.0, rough=0.55, x=-1300)
    n2.location = (-1300, -340)
    base = srgb(hexcol)
    d = tuple(c * 0.93 for c in base[:3])
    l = tuple(min(1.0, c * 1.05) for c in base[:3])
    col = b.mix(d, 0, l, 0, n2, 'Fac', x=-1000)
    n3 = b.noise((tc, 'Object'), scale=420.0, detail=3.0, x=-1300)
    n3.location = (-1300, -680)
    hh = b.math('ADD', n1, 'Fac', n3, 'Fac', x=-1000)
    hh.location = (-1000, -600)
    bmp = b.bump(hh, 0, strength=bump, dist=0.16, x=-700)
    rn = b.ramp(n1, 'Fac', [(0.2, (rough - 0.08,) * 3), (0.9, (rough + 0.08,) * 3)], x=-700)
    rn.location = (-700, -380)
    p = b.principled(base=col, baseo='Result', roughn=rn, rougho='Color', normal=bmp,
                     spec=0.35, x=-350)
    b.out(p)
    return m


# ================================================================== BRICK

def brick_wall(name="brick_kitchen"):
    m = _mat(name)
    b = NB(m)
    tc = wall_proj(b, x=-3000)
    mp = b.mapping(tc, 'Vector', scale=(1, 1, 1), x=-1840)
    br = b.n('ShaderNodeTexBrick', x=-1650)
    br.offset = 0.5
    br.offset_frequency = 2
    br.squash = 1.0
    br.squash_frequency = 2
    br.inputs['Scale'].default_value = 1.0      # coords already in metres
    br.inputs['Mortar Size'].default_value = 0.0115
    br.inputs['Mortar Smooth'].default_value = 0.22
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 0.207
    br.inputs['Row Height'].default_value = 0.0705
    br.inputs['Color1'].default_value = srgb('AA6046')
    br.inputs['Color2'].default_value = srgb('90452F')
    br.inputs['Mortar'].default_value = srgb('B6AC9A')
    b.l(mp, 'Vector', br, 'Vector')

    # per-brick colour jitter driven by the brick texture's own Color output
    jn = b.noise((mp, 'Vector'), scale=9.0, detail=2.0, rough=0.5, x=-1650)
    jn.location = (-1650, 420)
    tone = b.ramp(jn, 'Fac', [(0.18, srgb('8E5238')), (0.45, srgb('B06A4C')),
                              (0.68, srgb('C08A6A')), (0.86, srgb('9B5A45'))],
                  x=-1420, interp='B_SPLINE')
    tone.location = (-1420, 420)
    brk = b.mix(br, 'Color', tone, 'Color', None, blend='MIX', x=-1200,
                factor=0.62)
    brk.location = (-1200, 420)

    # surface grit
    grit = b.noise((mp, 'Vector'), scale=190.0, detail=6.0, rough=0.7, x=-1650)
    grit.location = (-1650, -300)
    fine = b.noise((mp, 'Vector'), scale=760.0, detail=3.0, x=-1650)
    fine.location = (-1650, -560)
    gcol = b.mix(brk, 'Result', (0.35, 0.30, 0.28), 0, grit, 'Fac', blend='MULTIPLY',
                 x=-980)
    gcol.inputs['Factor'].default_value = 0.16
    gcol.location = (-980, 300)

    # mortar mask (brick fac == 1 in mortar)
    mortar = b.n('ShaderNodeValToRGB', x=-1200, y=-60)
    mortar.color_ramp.interpolation = 'LINEAR'
    mortar.color_ramp.elements[0].position = 0.15
    mortar.color_ramp.elements[1].position = 0.65
    b.l(br, 'Fac', mortar, 'Fac')

    mcol = b.mix(gcol, 'Result', srgb('BDB4A2'), 0, mortar, 'Color', x=-760)
    mcol.location = (-760, 240)
    mgr = b.noise((mp, 'Vector'), scale=95.0, detail=6.0, x=-1200)
    mgr.location = (-1200, -420)
    mcol2 = b.mix(mcol, 'Result', (0.35, 0.33, 0.30), 0, None, blend='MULTIPLY',
                  x=-560, factor=0.0)
    # height: bricks proud, mortar recessed, plus grit
    hb = b.math('SUBTRACT', va=1.0, b=mortar, bo='Color', x=-980)
    hb.location = (-980, -160)
    hg = b.math('MULTIPLY', grit, 'Fac', vb=0.22, x=-980)
    hg.location = (-980, -420)
    hf = b.math('MULTIPLY', fine, 'Fac', vb=0.10, x=-980)
    hf.location = (-980, -560)
    h1 = b.math('ADD', hb, 0, hg, 0, x=-800)
    h1.location = (-800, -300)
    h2 = b.math('ADD', h1, 0, hf, 0, x=-660)
    h2.location = (-660, -300)
    bmp = b.bump(h2, 0, strength=0.75, dist=0.035, x=-500)

    rn = b.ramp(grit, 'Fac', [(0.2, (0.62,) * 3), (0.9, (0.88,) * 3)], x=-500)
    rn.location = (-500, -560)
    rn2 = b.mix(rn, 'Color', (0.95, 0.95, 0.95), 0, mortar, 'Color', x=-330)
    rn2.location = (-330, -560)
    p = b.principled(base=mcol, baseo='Result', roughn=rn2, rougho='Result',
                     normal=bmp, spec=0.3, x=-100)
    b.out(p)
    return m


def subway_tile(name="tile_white", size=0.107, hexcol='F2F0EA', grout='C9C4B6',
                stack=False, rough=0.13):
    m = _mat(name)
    b = NB(m)
    tc = wall_proj(b, x=-3000)
    mp = b.mapping(tc, 'Vector', scale=(1, 1, 1), x=-1560)
    br = b.n('ShaderNodeTexBrick', x=-1380)
    br.offset = 0.0 if stack else 0.5
    br.squash = 1.0
    br.inputs['Scale'].default_value = 1.0 / size
    br.inputs['Mortar Size'].default_value = 0.022
    br.inputs['Mortar Smooth'].default_value = 0.1
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.0
    br.inputs['Color1'].default_value = srgb(hexcol)
    br.inputs['Color2'].default_value = srgb(hexcol)
    br.inputs['Mortar'].default_value = srgb(grout)
    b.l(mp, 'Vector', br, 'Vector')
    jn = b.noise((mp, 'Vector'), scale=1.0 / (size * 1.02), detail=1.0, x=-1380)
    jn.location = (-1380, 340)
    tint = b.ramp(jn, 'Fac', [(0.3, (0.93, 0.94, 0.93)), (0.7, (1.0, 1.0, 0.99))], x=-1150)
    tint.location = (-1150, 340)
    col = b.mix(br, 'Color', tint, 'Color', None, blend='MULTIPLY', x=-950, factor=0.7)
    grt = b.n('ShaderNodeValToRGB', x=-1150, y=-100)
    grt.color_ramp.elements[0].position = 0.1
    grt.color_ramp.elements[1].position = 0.55
    b.l(br, 'Fac', grt, 'Fac')
    gn = b.noise((mp, 'Vector'), scale=280.0, detail=4.0, x=-1150)
    gn.location = (-1150, -420)
    h = b.math('SUBTRACT', va=1.0, b=grt, bo='Color', x=-900)
    h.location = (-900, -160)
    h2 = b.math('MULTIPLY_ADD', gn, 'Fac', vb=0.16, x=-900)
    h2.location = (-900, -420)
    h3 = b.math('ADD', h, 0, h2, 0, x=-740)
    bmp = b.bump(h3, 0, strength=0.6, dist=0.012, x=-580)
    rn = b.mix((rough, rough, rough), 0, (0.68, 0.68, 0.68), 0, grt, 'Color', x=-580)
    rn.location = (-580, -300)
    col2 = b.mix(col, 'Result', srgb(grout), 0, grt, 'Color', x=-740, )
    col2.location = (-740, 200)
    p = b.principled(base=col2, baseo='Result', roughn=rn, rougho='Result',
                     normal=bmp, spec=0.6, coat=0.35, x=-320)
    b.out(p)
    return m


# ================================================================== METAL

def metal(name, hexcol, rough=0.28, aniso=0.0, bump=0.03, scale=140.0, brush=None):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1400)
    mp = b.mapping(tc, 'Object', scale=(1, 1, 1) if not brush else brush, x=-1240)
    n1 = b.noise((mp, 'Vector'), scale=scale, detail=5.0, rough=0.6, x=-1060)
    n2 = b.noise((mp, 'Vector'), scale=6.0, detail=4.0, x=-1060)
    n2.location = (-1060, -320)
    rn = b.ramp(n1, 'Fac', [(0.2, (rough * 0.7,) * 3), (0.85, (rough * 1.4,) * 3)], x=-820)
    col = b.mix(tuple(c * 0.9 for c in srgb(hexcol)[:3]), 0, srgb(hexcol), 0, n2, 'Fac', x=-820)
    col.location = (-820, 260)
    bmp = b.bump(n1, 'Fac', strength=bump, dist=0.06, x=-600)
    p = b.principled(base=col, baseo='Result', roughn=rn, rougho='Color', metal=1.0,
                     normal=bmp, aniso=aniso, x=-300)
    b.out(p)
    return m


def wicker(name, light='D8B478', dark='9C7238', rings=34.0, stakes=30.0,
           rough=0.62, bump=0.85, centre=(0.0, 0.0)):
    """Woven cane, for the kitchen pendant.  Horizontal weavers crossing
    vertical stakes in a plain over-under: the parity of the cell decides which
    of the two is on top, and that is cut into the normal, so the shade breaks
    the light up into a basket instead of returning it like a paper cone.

    Built on object coordinates around the shade's own axis - it is a body of
    revolution that never moves after it is made, so angle and height are a
    perfectly good pair of surface parameters.  `centre` is where that axis
    stands in the room: geometry here is moved vertex-wise, so object space is
    world space, and an angle taken about the world origin instead barely
    changes across a shade parked several metres out - the stakes vanish and
    only the weavers survive."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1600)
    sp = b.n('ShaderNodeSeparateXYZ', x=-1460)
    b.l(tc, 'Object', sp, 'Vector')
    dx = b.math('SUBTRACT', sp, 0, vb=centre[0], x=-1400)
    dy = b.math('SUBTRACT', sp, 1, vb=centre[1], x=-1400)
    dy.location = (-1400, -160)
    th = b.math('ARCTAN2', dy, 0, dx, 0, x=-1320)
    u = b.math('MULTIPLY', th, 0, vb=stakes / math.tau, x=-1180)
    v = b.math('MULTIPLY', sp, 2, vb=rings, x=-1180)
    v.location = (-1180, -260)
    cells, tri = [], []
    for src, yy in ((u, 60), (v, -260)):
        w = b.math('WRAP', src, 0, x=-1040)
        w.location = (-1040, yy)
        w.inputs[1].default_value = 1.0
        w.inputs[2].default_value = 0.0
        # triangle across each reed, so it rounds instead of stepping
        s = b.math('MULTIPLY_ADD', w, 0, vb=2.0, x=-900)
        s.location = (-900, yy)
        s.inputs[2].default_value = -1.0
        a = b.math('ABSOLUTE', s, 0, x=-770)
        a.location = (-770, yy)
        t = b.math('SUBTRACT', None, 0, a, 0, x=-640)
        t.location = (-640, yy)
        t.inputs[0].default_value = 1.0
        tri.append(t)
        f = b.math('FLOOR', src, 0, x=-1040)
        f.location = (-1040, yy - 130)
        cells.append(f)
    par = b.math('ADD', cells[0], 0, cells[1], 0, x=-900)
    par.location = (-900, -520)
    par = b.math('MODULO', par, 0, vb=2.0, x=-770)
    par.location = (-770, -520)
    # even cells: the weaver rides over; odd cells: the stake does
    hgt = b.mix(tri[0], 0, tri[1], 0, par, 0, x=-500)
    col = b.mix(srgb(dark), 0, srgb(light), 0, hgt, 'Result', x=-500)
    col.location = (-500, 220)
    bmp = b.bump(hgt, 'Result', strength=bump, dist=0.010, x=-340)
    rn = b.ramp(hgt, 'Result', [(0.0, (rough * 1.25,) * 3),
                                (1.0, (rough * 0.80,) * 3)], x=-340)
    rn.location = (-340, -220)
    p = b.principled(base=col, baseo='Result', roughn=rn, rougho='Color',
                     normal=bmp, sheen=0.25, x=-160)
    b.out(p)
    return m


def gingham(name='fabric_check_quilt', band=0.015, light='EFE7D2',
            dark='8E1F2A', rough=0.82, sheen=0.6, weave=700.0, bump=0.2):
    """Woven gingham: two perpendicular stripe sets, so where both cross you get
    the solid colour, where one crosses you get the half tone, and where neither
    does you get the ground.  A brick texture (as before) gives running-bond
    blocks, which read as broad pink stripes, not a check."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1700)
    sp = b.n('ShaderNodeSeparateXYZ', x=-1560)
    b.l(tc, 'Object', sp, 'Vector')
    f = 0.5 / band
    # u runs along the surface whatever its azimuth, v is height
    u = b.math('ADD', sp, 0, sp, 1, x=-1420)
    stripes = []
    for src, so, yy in ((u, 0, 0), (sp, 2, -200)):
        s = b.math('MULTIPLY', src, so, vb=f, x=-1280)
        s.location = (-1280, yy)
        w = b.math('WRAP', s, 0, x=-1140)
        w.location = (-1140, yy)
        w.inputs[1].default_value = 1.0
        w.inputs[2].default_value = 0.0
        r = b.ramp(w, 0, [(0.47, (1, 1, 1)), (0.50, (0, 0, 0))], x=-1000)
        r.location = (-1000, yy)
        stripes.append(r)
    tot = b.math('ADD', stripes[0], 'Color', stripes[1], 'Color', x=-860)
    half = b.math('MULTIPLY', tot, 0, vb=0.5, x=-720)
    lc = srgb(light)
    dc = srgb(dark)
    mid = tuple((lc[i] * 0.42 + dc[i] * 0.58) for i in range(3))
    br = b.ramp(half, 0, [(0.0, lc), (0.5, mid), (1.0, dc)], x=-580)
    wv = b.n('ShaderNodeTexWave', x=-1320, y=-520)
    wv.wave_type = 'BANDS'
    wv.wave_profile = 'TRI'
    wv.inputs['Scale'].default_value = weave
    b.l(tc, 'Object', wv, 'Vector')
    bmp = b.bump(wv, 'Fac', strength=bump, dist=0.005, x=-900)
    p = b.principled(base=br, baseo='Color', rough=rough, normal=bmp,
                     sheen=sheen, spec=0.25, x=-520)
    b.out(p)
    return m


def perforated(name, hexcol='B9BEC2', rough=0.26, around=36, rows=11,
               hole=0.30, bump=0.03, attr='surfq', vmin=0.32):
    """Punched sheet - a colander.  The holes are cut out of the alpha rather
    than painted on, so the brick behind really does show through them.

    The pattern rides on a baked surface parameterisation (see
    mlib.bake_surface_attr), which is the only thing here that stays pinned to a
    double-curved shell.  Anything volumetric - object coords, generated coords,
    even a Voronoi over the normal - is a 3-D cell structure that a thin shell
    merely grazes, so most of the sheet never passes near a feature point and
    the holes come out sparse or missing altogether.

    R and G carry cos/sin of the angle round the axis, biased into 0..1 because
    a colour attribute clamps, and B the fraction along the profile.  `around`
    must be a whole number of holes per turn or the ring fails to close.

    A ring holds `around` holes at every height, but the circumference it has to
    spread them over shrinks to nothing at the pole, so below `vmin` the sheet
    is left solid - otherwise the bottom rings run together into slots, which is
    what a plain (u, v) grid gives you on anything domed."""
    m = _mat(name)
    b = NB(m)
    at = b.n('ShaderNodeAttribute', x=-1500)
    at.attribute_name = attr
    sp = b.n('ShaderNodeSeparateXYZ', x=-1340)
    b.l(at, 'Color', sp, 0)
    # undo the 0..1 bias the attribute had to be stored under
    cs = b.math('MULTIPLY_ADD', sp, 0, vb=2.0, x=-1180)
    cs.inputs[2].default_value = -1.0
    sn = b.math('MULTIPLY_ADD', sp, 1, vb=2.0, x=-1180)
    sn.location = (-1180, -180)
    sn.inputs[2].default_value = -1.0
    # atan2 of the two interpolated channels: continuous through the seam, where
    # a stored angle would have swept 0..1 inside a single face
    th = b.math('ARCTAN2', sn, 0, cs, 0, x=-1100)
    th.location = (-1100, 180)
    u = b.math('MULTIPLY', th, 0, vb=around / math.tau, x=-1020)
    v = b.math('MULTIPLY', sp, 2, vb=float(rows), x=-1020)
    v.location = (-1020, -220)
    # offset alternate rings by half a pitch, the way punched sheet is nested
    rw = b.math('FLOOR', v, 0, x=-880)
    rw.location = (-880, -300)
    od = b.math('MODULO', rw, 0, vb=2.0, x=-880)
    od.location = (-880, -400)
    us = b.math('MULTIPLY_ADD', od, 0, vb=0.5, x=-740)
    us.location = (-740, -300)
    b.l(u, 0, us, 2)
    du = b.math('WRAP', us, 0, x=-600)
    du.inputs[1].default_value = 0.5
    du.inputs[2].default_value = -0.5
    dv = b.math('WRAP', v, 0, x=-600)
    dv.location = (-600, -160)
    dv.inputs[1].default_value = 0.5
    dv.inputs[2].default_value = -0.5
    sq = b.math('MULTIPLY', du, 0, du, 0, x=-460)
    sv = b.math('MULTIPLY', dv, 0, dv, 0, x=-460)
    sv.location = (-460, -160)
    ss = b.math('ADD', sq, 0, sv, 0, x=-330)
    d = b.math('SQRT', ss, 0, x=-330)
    d.location = (-330, -160)
    hm = b.ramp(d, 0, [(hole * 0.72, (0, 0, 0)), (hole, (1, 1, 1))], x=-200)
    solid = b.ramp(sp, 2, [(vmin - 0.05, (1, 1, 1)), (vmin, (0, 0, 0))], x=-200)
    solid.location = (-200, -300)
    a = b.mix(hm, 'Color', (1, 1, 1), 0, solid, 'Color', x=-60)
    a.location = (-60, -200)
    tc = b.n('ShaderNodeTexCoord', x=-1500, y=-420)
    n1 = b.noise((tc, 'Object'), scale=90.0, detail=4.0, x=-1200)
    n1.location = (-1200, -420)
    rn = b.ramp(n1, 'Fac', [(0.25, (rough * 0.75,) * 3), (0.85, (rough * 1.3,) * 3)],
                x=-940)
    rn.location = (-940, -420)
    bmp = b.bump(a, 'Result', strength=bump, dist=0.004, x=100)
    p = b.principled(color=srgb(hexcol), roughn=rn, rougho='Color', metal=1.0,
                     normal=bmp, x=260)
    b.l(a, 'Result', p, 'Alpha')
    b.out(p)
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        pass
    m.use_backface_culling = False
    return m


def pane(name, tint='EDF2F0', rough=0.025, base_alpha=0.055, edge=0.60,
         bumpn=0.0):
    """Architectural glazing: alpha-blended with a Fresnel-weighted reflection.
    EEVEE renders this reliably (true transmission goes opaque here)."""
    m = _mat(name)
    b = NB(m)
    lw = b.n('ShaderNodeLayerWeight', x=-980)
    lw.inputs['Blend'].default_value = 0.13
    a = b.math('MULTIPLY_ADD', lw, 'Facing', vb=edge, x=-780)
    a.inputs[2].default_value = base_alpha
    nrm = None
    if bumpn:
        tc = b.n('ShaderNodeTexCoord', x=-1400)
        nz = b.noise((tc, 'Object'), scale=bumpn, detail=4.0, x=-1200)
        nrm = b.bump(nz, 'Fac', strength=0.25, dist=0.004, x=-1000)
    p = b.principled(color=srgb(tint), rough=rough, spec=0.65, normal=nrm, x=-380)
    b.l(a, 0, p, 'Alpha')
    b.out(p)
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    m.use_backface_culling = False
    for attr, val in (("show_transparent_back", False),
                      ("use_transparent_shadow", True)):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    return m


def glass(name="glass", tint='F2F6F5', rough=0.02, ior=1.5, alpha=0.06):
    m = _mat(name)
    m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else 'BLEND'
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1200)
    n = b.noise((tc, 'Object'), scale=8.0, detail=3.0, x=-1000)
    bmp = b.bump(n, 'Fac', strength=0.04, dist=0.02, x=-800)
    p = b.principled(color=srgb(tint), rough=rough, transm=1.0, ior=ior,
                     normal=bmp, x=-400)
    b.out(p)
    try:
        m.use_backface_culling = False
        m.use_transparent_shadow = True
    except Exception:
        pass
    return m


def emissive(name, hexcol, strength=6.0, rough=0.6, base=None):
    m = _mat(name)
    b = NB(m)
    p = b.principled(color=srgb(base or hexcol), rough=rough, x=-300)
    p.inputs['Emission Color'].default_value = srgb(hexcol)
    p.inputs['Emission Strength'].default_value = strength
    b.out(p)
    return m


# ================================================================== FABRIC

def fabric(name, hexcol, rough=0.72, sheen=0.22, weave=520.0, bump=0.30,
           blotch=0.06, fuzz=0.0):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1600)
    mp = b.mapping(tc, 'Object', scale=(1, 1, 1), x=-1450)
    wv = b.n('ShaderNodeTexWave', x=-1280)
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    wv.wave_profile = 'TRI'
    wv.inputs['Scale'].default_value = weave
    wv.inputs['Distortion'].default_value = 0.6
    b.l(mp, 'Vector', wv, 'Vector')
    wv2 = b.n('ShaderNodeTexWave', x=-1280, y=-280)
    wv2.wave_type = 'BANDS'
    wv2.bands_direction = 'Y'
    wv2.wave_profile = 'TRI'
    wv2.inputs['Scale'].default_value = weave
    wv2.inputs['Distortion'].default_value = 0.6
    b.l(mp, 'Vector', wv2, 'Vector')
    wsum = b.math('MULTIPLY', wv, 'Fac', wv2, 'Fac', x=-1080)
    n2 = b.noise((mp, 'Vector'), scale=2.6, detail=5.0, rough=0.6, x=-1280)
    n2.location = (-1280, 320)
    base = srgb(hexcol)
    d = tuple(c * (1 - blotch) for c in base[:3])
    l = tuple(min(1, c * (1 + blotch)) for c in base[:3])
    col = b.mix(d, 0, l, 0, n2, 'Fac', x=-1000)
    col.location = (-1000, 320)
    fz = b.noise((mp, 'Vector'), scale=900.0, detail=3.0, x=-1280)
    fz.location = (-1280, -560)
    hh = b.math('ADD', wsum, 0, fz, 'Fac', x=-880)
    bmp = b.bump(hh, 0, strength=bump, dist=0.008, x=-700)
    rn = b.ramp(wsum, 0, [(0.1, (rough + 0.1,) * 3), (0.9, (rough - 0.1,) * 3)], x=-700)
    rn.location = (-700, -300)
    p = b.principled(base=col, baseo='Result', roughn=rn, rougho='Color',
                     normal=bmp, sheen=sheen, spec=0.28, x=-350,
                     sheen_tint=tuple(c * 0.9 for c in base[:3]))
    b.out(p)
    return m


def damask(name, base='E6DEC8', motif='D8CDB2', scale=2.6, rough=0.74, sheen=0.24):
    """Tone-on-tone jacquard: warped wave lattice + voronoi blossoms."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2000)
    mp = b.mapping(tc, 'Object', scale=(scale, scale, scale), x=-1860)
    warp = b.noise((mp, 'Vector'), scale=3.2, detail=4.0, rough=0.55, x=-1700)
    wv = b.n('ShaderNodeVectorMath', x=-1540, operation='MULTIPLY_ADD')
    b.l(warp, 'Color', wv, 0)
    wv.inputs[1].default_value = (0.22, 0.22, 0.22)
    b.l(mp, 'Vector', wv, 2)
    vor = b.n('ShaderNodeTexVoronoi', x=-1380)
    vor.feature = 'F1'
    vor.distance = 'MINKOWSKI'
    vor.inputs['Scale'].default_value = 3.4
    vor.inputs['Randomness'].default_value = 0.85
    try:
        vor.inputs['Exponent'].default_value = 3.5
    except Exception:
        pass
    b.l(wv, 'Vector', vor, 'Vector')
    lat = b.n('ShaderNodeTexWave', x=-1380, y=-320)
    lat.wave_type = 'RINGS'
    lat.rings_direction = 'SPHERICAL'
    lat.wave_profile = 'SIN'
    # a tight, heavily distorted ring lattice turns the whole slipcover into
    # watered silk - from any distance it reads as wood grain, not jacquard
    lat.inputs['Scale'].default_value = 3.2
    lat.inputs['Distortion'].default_value = 0.9
    lat.inputs['Detail'].default_value = 2.0
    b.l(wv, 'Vector', lat, 'Vector')
    mixm = b.math('MULTIPLY', vor, 'Distance', lat, 'Fac', x=-1160)
    pat = b.ramp(mixm, 0, [(0.06, (0, 0, 0)), (0.16, (1, 1, 1)),
                           (0.38, (1, 1, 1)), (0.52, (0, 0, 0))], x=-980,
                 interp='B_SPLINE')
    col = b.mix(srgb(base), 0, srgb(motif), 0, pat, 'Color', x=-780)
    wvv = b.n('ShaderNodeTexWave', x=-1380, y=340)
    wvv.wave_type = 'BANDS'
    wvv.wave_profile = 'TRI'
    wvv.inputs['Scale'].default_value = 900.0
    b.l(mp, 'Vector', wvv, 'Vector')
    hh = b.math('MULTIPLY_ADD', pat, 'Color', vb=0.7, x=-780)
    hh.location = (-780, -300)
    hh.inputs[2].default_value = 0.0
    h2 = b.math('ADD', hh, 0, wvv, 'Fac', x=-620)
    # most of what still read as watered silk was relief and gloss, not colour
    bmp = b.bump(h2, 0, strength=0.03, dist=0.01, x=-460)
    rn = b.ramp(pat, 'Color', [(0.0, (rough,) * 3), (1.0, (rough - 0.02,) * 3)], x=-460)
    rn.location = (-460, -300)
    p = b.principled(base=col, baseo='Result', roughn=rn, rougho='Color',
                     normal=bmp, sheen=sheen, spec=0.3, x=-200,
                     sheen_tint=tuple(c * 0.85 for c in srgb(base)[:3]))
    b.out(p)
    return m


def velvet(name, hexcol, rough=0.5, sheen=1.0):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1400)
    n = b.noise((tc, 'Object'), scale=680.0, detail=4.0, rough=0.7, x=-1200)
    n2 = b.noise((tc, 'Object'), scale=3.0, detail=5.0, x=-1200)
    n2.location = (-1200, -300)
    base = srgb(hexcol)
    col = b.mix(tuple(c * 0.7 for c in base[:3]), 0, tuple(min(1, c * 1.25) for c in base[:3]),
                0, n2, 'Fac', x=-960)
    fr = b.n('ShaderNodeLayerWeight', x=-1200, y=380)
    fr.inputs['Blend'].default_value = 0.28
    rim = b.ramp(fr, 'Facing', [(0.15, (0, 0, 0)), (0.95, (1, 1, 1))], x=-960)
    rim.location = (-960, 380)
    col2 = b.mix(col, 'Result', tuple(min(1, c * 1.9 + 0.03) for c in base[:3]), 0,
                 rim, 'Color', x=-740)
    bmp = b.bump(n, 'Fac', strength=0.16, dist=0.006, x=-740)
    bmp.location = (-740, -300)
    p = b.principled(base=col2, baseo='Result', rough=rough, normal=bmp,
                     sheen=sheen, spec=0.2, x=-420)
    p.inputs['Sheen Tint'].default_value = _c(tuple(min(1, c * 1.6) for c in base[:3]))
    b.out(p)
    return m


# ================================================================== SPECIALS

def floral_chintz(name, ground='F2B915', petal='D8266A', petal2='F2789F',
                  leaf='2C6B3F', leaf2='7FA85A', scale=5.0, rough=0.7,
                  ground2=None):
    """Cabbage-rose chintz: clustered voronoi blossoms + leaf sprigs."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2200)
    mp = b.mapping(tc, 'Object', scale=(scale, scale, scale), x=-2050)
    wn = b.noise((mp, 'Vector'), scale=2.0, detail=4.0, rough=0.55, x=-1900)
    wv = b.n('ShaderNodeVectorMath', x=-1750, operation='MULTIPLY_ADD')
    b.l(wn, 'Color', wv, 0)
    wv.inputs[1].default_value = (0.07, 0.07, 0.07)
    b.l(mp, 'Vector', wv, 2)

    # Blossoms.  The petals have to be built inside each cell, off the Voronoi's
    # Position output: driving them from a global rings wave (as before) meant
    # the petal geometry never lined up with the blossom it belonged to, so
    # every flower averaged out into an airbrushed dot.
    VSC = 2.1
    vo = b.n('ShaderNodeTexVoronoi', x=-1600)
    vo.inputs['Scale'].default_value = VSC
    vo.inputs['Randomness'].default_value = 1.0
    b.l(wv, 'Vector', vo, 'Vector')

    # Position comes back in the node's *input* space, not the internally
    # scaled one, so the offset is taken against `wv` directly.
    off = b.n('ShaderNodeVectorMath', x=-1450, y=-200, operation='SUBTRACT')
    b.l(wv, 'Vector', off, 0)
    b.l(vo, 'Position', off, 1)
    rlen = b.n('ShaderNodeVectorMath', x=-1300, y=-200, operation='LENGTH')
    b.l(off, 'Vector', rlen, 0)
    dirn = b.n('ShaderNodeVectorMath', x=-1300, y=-380, operation='NORMALIZE')
    b.l(off, 'Vector', dirn, 0)

    # A second Voronoi over the unit direction breaks the blossom's outline into
    # rounded lobes - the petals of a cabbage rose seen face on.
    pv = b.n('ShaderNodeTexVoronoi', x=-1150, y=-380)
    pv.inputs['Scale'].default_value = 2.4
    pv.inputs['Randomness'].default_value = 0.9
    b.l(dirn, 'Vector', pv, 'Vector')
    R0 = 0.60 / VSC                     # cells sit 1/VSC apart in input space
    rth = b.math('MULTIPLY_ADD', pv, 'Distance', vb=-0.78 * R0, x=-1000)
    rth.location = (-1000, -380)
    rth.inputs[2].default_value = 1.24 * R0
    diff = b.math('SUBTRACT', rth, 0, rlen, 'Value', x=-860)
    diff.location = (-860, -300)
    pmix = b.ramp(diff, 0, [(0.0, (0, 0, 0)), (0.012, (1, 1, 1))], x=-720)
    pmix.location = (-720, -300)

    # radius within the blossom -> the whorls of a rose, deep at the eye
    petals = b.math('DIVIDE', rlen, 'Value', vb=R0, x=-1000)
    petals.location = (-1000, -540)

    # leaves - stretched cells so the foliage reads as leaves rather than a
    # second field of dots, and dense enough to bed the blossoms into
    lstretch = b.n('ShaderNodeMapping', x=-1750, y=380)
    lstretch.inputs['Scale'].default_value = (1.0, 2.6, 1.0)
    b.l(wv, 0, lstretch, 'Vector')
    LSC = 3.4
    lv = b.n('ShaderNodeTexVoronoi', x=-1600, y=380)
    lv.inputs['Scale'].default_value = LSC
    lv.inputs['Randomness'].default_value = 1.0
    b.l(lstretch, 'Vector', lv, 'Vector')
    # thresholds expressed as a fraction of the cell spacing, so changing LSC
    # rescales the foliage instead of wiping it out
    lmask = b.ramp(lv, 'Distance', [(0.40 / LSC, (1, 1, 1)), (0.49 / LSC, (0, 0, 0))],
                   x=-1380)
    lmask.location = (-1380, 380)
    lcol = b.mix(srgb(leaf), 0, srgb(leaf2), 0, lv, 'Color', x=-1180, factor=0.5)
    lcol.location = (-1180, 380)

    gcol = srgb(ground)
    if ground2:
        gn = b.noise((mp, 'Vector'), scale=1.3, detail=4.0, x=-1600)
        gn.location = (-1600, 700)
        gmix = b.mix(srgb(ground), 0, srgb(ground2), 0, gn, 'Fac', x=-1380)
        gmix.location = (-1380, 700)
        g_src, g_o = gmix, 'Result'
    else:
        g_src, g_o = None, 0

    # concentric whorls out from the eye of each bloom
    pcol = b.ramp(petals, 0, [(0.00, srgb(petal)), (0.22, srgb(petal2)),
                              (0.48, srgb(petal)), (0.74, srgb(petal2)),
                              (1.00, srgb(petal))], x=-1180)
    pcol.location = (-1180, -540)

    if g_src:
        c1 = b.mix(g_src, g_o, lcol, 'Result', lmask, 'Color', x=-960)
    else:
        c1 = b.mix(gcol, 0, lcol, 'Result', lmask, 'Color', x=-960)
    c2 = b.mix(c1, 'Result', pcol, 'Color', pmix, 'Color', x=-780)

    wvv = b.n('ShaderNodeTexWave', x=-1600, y=-620)
    wvv.wave_type = 'BANDS'
    wvv.wave_profile = 'TRI'
    wvv.inputs['Scale'].default_value = 1400.0
    b.l(mp, 'Vector', wvv, 'Vector')
    bmp = b.bump(wvv, 'Fac', strength=0.14, dist=0.004, x=-600)
    p = b.principled(base=c2, baseo='Result', rough=rough, normal=bmp, sheen=0.20,
                     spec=0.3, x=-320,
                     sheen_tint=tuple(c * 0.85 for c in srgb(ground)[:3]))
    b.out(p)
    return m


def burl_veneer(name, cols=('B4712C', '8A4A18', '5A2C0C'), scale=9.0):
    """Figured / book-matched walnut veneer for the deco credenza."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2000)
    mp = b.mapping(tc, 'UV', scale=(scale, scale, scale), x=-1860)
    # mirror u about 0.5 -> book match
    sep = b.n('ShaderNodeSeparateXYZ', x=-1700)
    b.l(mp, 'Vector', sep, 'Vector')
    ab = b.math('ABSOLUTE', sep, 0, x=-1560)
    cmb = b.n('ShaderNodeCombineXYZ', x=-1420)
    b.l(ab, 0, cmb, 'X')
    b.l(sep, 1, cmb, 'Y')
    b.l(sep, 2, cmb, 'Z')
    wn = b.noise((cmb, 'Vector'), scale=1.6, detail=4.0, rough=0.6, x=-1280)
    wv = b.n('ShaderNodeVectorMath', x=-1120, operation='MULTIPLY_ADD')
    b.l(wn, 'Color', wv, 0)
    wv.inputs[1].default_value = (0.5, 0.14, 0.14)
    b.l(cmb, 'Vector', wv, 2)
    fig = b.n('ShaderNodeTexWave', x=-960)
    fig.wave_type = 'BANDS'
    fig.bands_direction = 'Y'
    fig.wave_profile = 'SIN'
    fig.inputs['Scale'].default_value = 6.0
    fig.inputs['Distortion'].default_value = 6.0
    fig.inputs['Detail'].default_value = 6.0
    b.l(wv, 'Vector', fig, 'Vector')
    ramp = b.ramp(fig, 'Fac', [(0.08, srgb(cols[0])), (0.45, srgb(cols[1])),
                               (0.80, srgb(cols[2])), (1.0, srgb(cols[1]))], x=-760)
    fn = b.noise((cmb, 'Vector'), scale=180.0, detail=5.0, x=-960)
    fn.location = (-960, -320)
    bmp = b.bump(fn, 'Fac', strength=0.06, dist=0.06, x=-540)
    rn = b.ramp(fn, 'Fac', [(0.3, (0.16,) * 3), (0.9, (0.28,) * 3)], x=-540)
    rn.location = (-540, -300)
    p = b.principled(base=ramp, baseo='Color', roughn=rn, rougho='Color',
                     normal=bmp, coat=0.55, spec=0.55, x=-260)
    b.out(p)
    return m


# ============================================================== BOTANICAL PLATE

def botanical(name, normal=(-1, 0), seed=0, ground='EFE8D2',
              stem='5A6B3A', leafc=('4C6B34', '7E9155'),
              bloom=('C0728A', 'E2B0BC'), rough=0.62):
    """A single pressed-flower plate for a picture frame.

    The framed art used to be handed the repeating upholstery chintz, which
    inside a mount reads as wallpaper - a botanical print is one specimen
    centred on cream paper, so it has to be drawn as one.
    """
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2600)
    g = b.n('ShaderNodeSeparateXYZ', x=-2460)
    b.l(tc, 'Generated', g, 'Vector')
    # Generated normalises each axis over the bounding box independently, so the
    # picture's width is whichever horizontal axis it is NOT thin along.
    uo = 1 if abs(normal[0]) > 0.5 else 0
    u = b.math('SUBTRACT', g, uo, vb=0.5, x=-2320)          # -0.5 .. 0.5
    v = b.math('SUBTRACT', g, 2, vb=0.5, x=-2320)
    v.location = (-2320, -180)

    rnd = [((seed * 7919 + i * 104729) % 1000) / 1000.0 for i in range(24)]

    def _rot(px, py, ang, x):
        """rotate (px,py) by -ang about the origin"""
        ca, sa = math.cos(ang), math.sin(ang)
        a1 = b.math('MULTIPLY', px, 0, vb=ca, x=x)
        a2 = b.math('MULTIPLY', py, 0, vb=sa, x=x)
        a2.location = (x, -160)
        rx = b.math('ADD', a1, 0, a2, 0, x=x + 130)
        b1 = b.math('MULTIPLY', px, 0, vb=-sa, x=x)
        b1.location = (x, -320)
        b2 = b.math('MULTIPLY', py, 0, vb=ca, x=x)
        b2.location = (x, -480)
        ry = b.math('ADD', b1, 0, b2, 0, x=x + 130)
        ry.location = (x + 130, -400)
        return rx, ry

    def _blob(px, py, cx, cy, la, lb, ang, p, x):
        """superellipse mask centred on (cx,cy); p<2 gives pointed ends"""
        dx = b.math('SUBTRACT', px, 0, vb=cx, x=x)
        dy = b.math('SUBTRACT', py, 0, vb=cy, x=x)
        dy.location = (x, -200)
        rx, ry = _rot(dx, dy, ang, x + 140)
        nx = b.math('DIVIDE', rx, 0, vb=la, x=x + 420)
        ny = b.math('DIVIDE', ry, 0, vb=lb, x=x + 420)
        ny.location = (x + 420, -400)
        ax = b.math('ABSOLUTE', nx, 0, x=x + 550)
        ay = b.math('ABSOLUTE', ny, 0, x=x + 550)
        ay.location = (x + 550, -400)
        ex = b.math('POWER', ax, 0, vb=p, x=x + 680)
        ey = b.math('POWER', ay, 0, vb=p, x=x + 680)
        ey.location = (x + 680, -400)
        s = b.math('ADD', ex, 0, ey, 0, x=x + 810)
        return s, ay                               # s < 1 inside; ay = |across|

    masks, cols = [], []

    # --- stem: a shallow parabola climbing the plate ------------------------
    sv = b.math('MULTIPLY', v, 0, vb=1.0, x=-2180)
    sq = b.math('MULTIPLY', sv, 0, sv, 0, x=-2040)
    bend = b.math('MULTIPLY_ADD', sq, 0, vb=0.42, x=-1900)
    bend.inputs[2].default_value = -0.035
    sx = b.math('SUBTRACT', u, 0, bend, 0, x=-1760)
    sax = b.math('ABSOLUTE', sx, 0, x=-1620)
    smask = b.ramp(sax, 0, [(0.0090, (1, 1, 1)), (0.0125, (0, 0, 0))], x=-1480)
    # only between the root and the crown
    vlo = b.ramp(v, 0, [(-0.40, (0, 0, 0)), (-0.36, (1, 1, 1))], x=-1480)
    vlo.location = (-1480, -200)
    vhi = b.ramp(v, 0, [(0.24, (1, 1, 1)), (0.28, (0, 0, 0))], x=-1480)
    vhi.location = (-1480, -380)
    st1 = b.math('MULTIPLY', smask, 'Color', vlo, 'Color', x=-1320)
    st = b.math('MULTIPLY', st1, 0, vhi, 'Color', x=-1180)
    masks.append((st, 0, srgb(stem)))

    # --- leaves: alternate sides up the stem --------------------------------
    # p just above 1 is a rhombus, which is what the first pass drew; a leaf
    # needs a rounded superellipse with a long major axis.
    LV = ((-0.345, -1, 0.190, 0.068, -0.26), (-0.205, 1, 0.205, 0.074, 0.30),
          (-0.055, -1, 0.185, 0.066, -0.22), (0.075, 1, 0.150, 0.055, 0.28),
          (-0.275, 1, 0.135, 0.049, 0.50), (-0.125, -1, 0.128, 0.046, -0.52))
    for i, (vy, side, la, lb, ang) in enumerate(LV):
        # pushed clear of the axis so the stem still reads between the leaves
        cx = 0.42 * vy * vy - 0.035 + side * (la * 0.96)
        s, ay = _blob(u, v, cx, vy, la, lb, ang, 1.65, -1100 + i * 40)
        mk = b.ramp(s, 0, [(0.97, (1, 1, 1)), (1.03, (0, 0, 0))], x=-100)
        mk.location = (-100, 300 - i * 90)
        c = srgb(leafc[i % 2])
        masks.append((mk, 'Color', c))
        # midrib: a pale line down the leaf, clipped to the leaf itself
        vn = b.ramp(ay, 0, [(0.10, (1, 1, 1)), (0.20, (0, 0, 0))], x=-60)
        vn.location = (-60, 300 - i * 90)
        vm = b.math('MULTIPLY', vn, 'Color', mk, 'Color', x=-20)
        vm.location = (-20, 260 - i * 90)
        masks.append((vm, 0, srgb(leafc[(i + 1) % 2])))

    # --- blooms: rosettes at the crown --------------------------------------
    BL = ((0.045, 0.320, 0.105), (-0.105, 0.225, 0.080), (0.125, 0.170, 0.062))
    for i, (bx, by, R) in enumerate(BL):
        dx = b.math('SUBTRACT', u, 0, vb=bx, x=-900 + i * 40)
        dy = b.math('SUBTRACT', v, 0, vb=by, x=-900 + i * 40)
        dy.location = (-900 + i * 40, -240)
        ang = b.math('ARCTAN2', dy, 0, dx, 0, x=-760 + i * 40)
        k = 5 + i
        ka = b.math('MULTIPLY', ang, 0, vb=float(k), x=-620 + i * 40)
        co = b.math('COSINE', ka, 0, x=-480 + i * 40)
        rth = b.math('MULTIPLY_ADD', co, 0, vb=0.26 * R, x=-340 + i * 40)
        rth.inputs[2].default_value = 0.80 * R
        dxs = b.math('MULTIPLY', dx, 0, dx, 0, x=-760 + i * 40)
        dxs.location = (-760 + i * 40, -400)
        dys = b.math('MULTIPLY', dy, 0, dy, 0, x=-760 + i * 40)
        dys.location = (-760 + i * 40, -560)
        rr = b.math('ADD', dxs, 0, dys, 0, x=-620 + i * 40)
        rr.location = (-620 + i * 40, -480)
        rl = b.math('SQRT', rr, 0, x=-480 + i * 40)
        rl.location = (-480 + i * 40, -480)
        d2 = b.math('SUBTRACT', rth, 0, rl, 0, x=-200 + i * 40)
        d2.location = (-200 + i * 40, -300)
        mk = b.ramp(d2, 0, [(0.0, (0, 0, 0)), (0.006, (1, 1, 1))], x=-60 + i * 40)
        mk.location = (-60 + i * 40, -300)
        # petal colour deepens towards the eye
        rn = b.math('DIVIDE', rl, 0, vb=R, x=-340 + i * 40)
        rn.location = (-340 + i * 40, -560)
        pc = b.ramp(rn, 0, [(0.0, srgb(bloom[0])), (0.30, srgb(bloom[1])),
                            (1.0, srgb(bloom[0]))], x=-200 + i * 40)
        pc.location = (-200 + i * 40, -620)
        masks.append((mk, 'Color', (pc, 'Color')))

    # --- aged paper ground, then composite the specimen over it -------------
    fox = b.noise((tc, 'Generated'), scale=9.0, detail=5.0, rough=0.7, x=-2320)
    fox.location = (-2320, 620)
    fx = b.ramp(fox, 'Fac', [(0.56, srgb(ground)), (0.78, srgb('DFD2AE'))],
                x=-2180)
    fx.location = (-2180, 620)
    cur, curo = fx, 'Color'
    for i, (mk, mko, c) in enumerate(masks):
        if isinstance(c, tuple) and len(c) == 2 and not isinstance(c[0], float):
            nx = b.mix(cur, curo, c[0], c[1], mk, mko, x=200 + i * 80)
        else:
            nx = b.mix(cur, curo, c, 0, mk, mko, x=200 + i * 80)
        nx.location = (200 + i * 80, 0)
        cur, curo = nx, 'Result'

    p = b.principled(base=cur, baseo=curo, rough=rough, spec=0.28, x=1400)
    b.out(p)
    return m


def foliage(name, dark='24501F', light='5E8C3A', translucent=0.38, rough=0.44):
    """Living leaf: a flat green paint reads as cut paper because real foliage
    is thin enough to glow where the light is behind it, and never one colour
    across a whole plant."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1600)
    # slow drift of tone from leaf to leaf across the plant
    n1 = b.noise((tc, 'Object'), scale=7.0, detail=3.0, rough=0.5, x=-1420)
    tone = b.ramp(n1, 'Fac', [(0.30, srgb(dark)), (0.72, srgb(light))], x=-1240)
    # fine mottle so the blade is not a flat wash
    n2 = b.noise((tc, 'Object'), scale=90.0, detail=4.0, rough=0.6, x=-1420)
    n2.location = (-1420, -260)
    mot = b.ramp(n2, 'Fac', [(0.38, (0.86, 0.86, 0.86)), (0.66, (1.06, 1.06, 1.06))],
                 x=-1240)
    mot.location = (-1240, -260)
    col = b.mix(tone, 'Color', mot, 'Color', None, blend='MULTIPLY', x=-1060,
                factor=1.0)
    bmp = b.bump(n2, 'Fac', strength=0.12, dist=0.004, x=-880)
    p = b.principled(base=col, baseo='Result', rough=rough, normal=bmp, spec=0.42,
                     coat=0.18, x=-620)
    tr = b.n('ShaderNodeBsdfTranslucent', x=-620, y=-320)
    b.l(col, 'Result', tr, 'Color')
    mx = b.n('ShaderNodeMixShader', x=-380)
    mx.inputs['Fac'].default_value = translucent
    b.l(p, 0, mx, 1)
    b.l(tr, 0, mx, 2)
    b.out(mx)
    return m
