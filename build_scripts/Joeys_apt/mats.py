"""mats - every surface in Apt 19 as a procedural node graph.

No image files and no external assets.  Where a material needs information the
shader cannot derive - which parquet finger a face belongs to, which way its
grain runs - that information is generated at build time as UVs and colour
attributes on the mesh itself, and read back here.
"""
import bpy, math, colorsys


# ------------------------------------------------------------------ node help

def _sock(node, name, typ=None, out=False):
    """ShaderNodeMix carries four sockets called 'A' - one per data type - so a
    lookup by name alone lands on the float and every colour write throws.
    Match on the type as well and the graph builds whatever Blender does to the
    socket ordering next."""
    coll = node.outputs if out else node.inputs
    for s in coll:
        if s.name == name and (typ is None or s.type == typ):
            return s
    return coll[name]


class NB:
    """Small builder over a material's node tree."""

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
        so = a.outputs[ao] if not isinstance(ao, tuple) else _sock(a, ao[0], ao[1], True)
        si = b.inputs[bi] if not isinstance(bi, tuple) else _sock(b, bi[0], bi[1])
        self.nt.links.new(so, si)

    def out(self, shader):
        o = self.n('ShaderNodeOutputMaterial', x=340)
        self.l(shader, 0, o, 'Surface')
        return o

    # -- convenience ------------------------------------------------------
    def mapping(self, src, srco, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0),
                x=-1600, y=0):
        m = self.n('ShaderNodeMapping', x=x, y=y)
        m.inputs['Scale'].default_value = scale
        m.inputs['Location'].default_value = loc
        m.inputs['Rotation'].default_value = rot
        self.l(src, srco, m, 'Vector')
        return m

    def noise(self, vec, scale=5.0, detail=6.0, rough=0.5, dist=0.0, x=-1400,
              dim=None, lac=2.0, y=0):
        nd = self.n('ShaderNodeTexNoise', x=x, y=y)
        if dim:
            nd.noise_dimensions = dim
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Lacunarity'].default_value = lac
        nd.inputs['Distortion'].default_value = dist
        if vec is not None:
            self.l(vec[0], vec[1], nd, 'Vector')
        return nd

    def vor(self, vec, scale=8.0, rand=1.0, smooth=0.0, x=-1400, y=0,
            feat='F1', dim='3D'):
        nd = self.n('ShaderNodeTexVoronoi', x=x, y=y)
        nd.feature = feat
        nd.voronoi_dimensions = dim
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Randomness'].default_value = rand
        try:
            nd.inputs['Smoothness'].default_value = smooth
        except Exception:
            pass
        if vec is not None:
            self.l(vec[0], vec[1], nd, 'Vector')
        return nd

    def ramp(self, src, srco, stops, x=-1100, y=0, interp='LINEAR'):
        r = self.n('ShaderNodeValToRGB', x=x, y=y)
        r.color_ramp.interpolation = interp
        el = r.color_ramp.elements
        while len(el) > len(stops):
            el.remove(el[-1])
        for i, (p, c) in enumerate(stops):
            if i >= len(el):
                el.new(p)
            el[i].position = p
            el[i].color = c if len(c) == 4 else (c[0], c[1], c[2], 1.0)
        if src is not None:
            self.l(src, srco, r, 'Fac')
        return r

    def mix(self, a, ao, b, bo, fac, faco=None, blend='MIX', x=-900, y=0, factor=None):
        m = self.n('ShaderNodeMix', x=x, y=y, data_type='RGBA', blend_type=blend)
        if fac is None:
            _sock(m, 'Factor', 'VALUE').default_value = 0.5 if factor is None else factor
        else:
            self.nt.links.new(fac.outputs[faco if faco is not None else 0],
                              _sock(m, 'Factor', 'VALUE'))
        for key, obj, o in (('A', a, ao), ('B', b, bo)):
            s = _sock(m, key, 'RGBA')
            if isinstance(obj, (tuple, list)):
                s.default_value = _c(obj)
            elif isinstance(obj, str):
                s.default_value = srgb(obj)
            else:
                self.nt.links.new(obj.outputs[o], s)
        return m

    def mixo(self, m):
        """The RGBA Result of a mix node."""
        return (m, 2)

    def math(self, op, a=None, ao=0, b=None, bo=0, va=None, vb=None, x=-1000,
             y=0, clamp=False, vc=None):
        m = self.n('ShaderNodeMath', x=x, y=y, operation=op, use_clamp=clamp)
        if a is not None:
            self.l(a, ao, m, 0)
        elif va is not None:
            m.inputs[0].default_value = va
        if b is not None:
            self.l(b, bo, m, 1)
        elif vb is not None:
            m.inputs[1].default_value = vb
        if vc is not None:
            m.inputs[2].default_value = vc
        return m

    def vmath(self, op, a=None, ao=0, b=None, bo=0, va=None, vb=None, x=-1000, y=0):
        m = self.n('ShaderNodeVectorMath', x=x, y=y, operation=op)
        if a is not None:
            self.l(a, ao, m, 0)
        elif va is not None:
            m.inputs[0].default_value = va
        if b is not None:
            self.l(b, bo, m, 1)
        elif vb is not None:
            m.inputs[1].default_value = vb
        return m

    def bump(self, height, ho=0, strength=0.3, dist=1.0, x=-500, y=0, normal=None):
        b = self.n('ShaderNodeBump', x=x, y=y)
        b.inputs['Strength'].default_value = strength
        b.inputs['Distance'].default_value = dist
        self.l(height, ho, b, 'Height')
        if normal is not None:
            self.l(normal, 'Normal', b, 'Normal')
        return b

    def principled(self, base=None, baseo=0, color=None, rough=0.45, roughn=None,
                   rougho=0, metal=0.0, metaln=None, normal=None, spec=0.5, x=60,
                   ior=1.45, sheen=0.0, coat=0.0, coat_rough=0.06, transm=0.0,
                   emis=None, emis_str=0.0, aniso=0.0, sheen_tint=None, y=0,
                   spec_tint=None, alpha=None, alphao=0):
        p = self.n('ShaderNodeBsdfPrincipled', x=x, y=y)
        p.inputs['Roughness'].default_value = rough
        p.inputs['Metallic'].default_value = metal
        p.inputs['IOR'].default_value = ior
        p.inputs['Specular IOR Level'].default_value = spec
        if sheen:
            p.inputs['Sheen Weight'].default_value = sheen
            p.inputs['Sheen Roughness'].default_value = 0.35
            st = sheen_tint if sheen_tint is not None else (color or (0.5,) * 3)
            p.inputs['Sheen Tint'].default_value = _c(srgb(st) if isinstance(st, str) else st)
        if coat:
            p.inputs['Coat Weight'].default_value = coat
            p.inputs['Coat Roughness'].default_value = coat_rough
        if transm:
            p.inputs['Transmission Weight'].default_value = transm
        if aniso:
            p.inputs['Anisotropic'].default_value = aniso
        if spec_tint is not None:
            p.inputs['Specular Tint'].default_value = _c(srgb(spec_tint)
                                                        if isinstance(spec_tint, str) else spec_tint)
        if color is not None:
            p.inputs['Base Color'].default_value = srgb(color) if isinstance(color, str) else _c(color)
        if base is not None:
            self.l(base, baseo, p, 'Base Color')
        if roughn is not None:
            self.l(roughn, rougho, p, 'Roughness')
        if metaln is not None:
            self.l(metaln, 0, p, 'Metallic')
        if normal is not None:
            self.l(normal, 'Normal', p, 'Normal')
        if alpha is not None:
            self.l(alpha, alphao, p, 'Alpha')
        if emis is not None:
            self.l(emis, 0, p, 'Emission Color')
            p.inputs['Emission Strength'].default_value = emis_str
        elif emis_str:
            p.inputs['Emission Strength'].default_value = emis_str
            p.inputs['Emission Color'].default_value = (1, 1, 1, 1)
        return p


def _c(c):
    return (c[0], c[1], c[2], 1.0) if len(c) == 3 else tuple(c)


def srgb(h):
    """hex (or an 0-1 sRGB triple) -> linear rgba"""
    if isinstance(h, str):
        h = h.lstrip('#')
        r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    else:
        r, g, b = h[:3]
    f = lambda u: u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


def shade(h, k):
    """Lighten (k>1) or darken (k<1) a hex colour, staying in sRGB."""
    h = h.lstrip('#')
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return '%02X%02X%02X' % tuple(int(max(0, min(1, c * k)) * 255) for c in (r, g, b))


def _mat(name):
    """Reuse the datablock if it exists - NB clears the node tree anyway, so a
    rebuild never orphans the objects already pointing at it."""
    m = bpy.data.materials.get(name)
    return m if m else bpy.data.materials.new(name)


def get(name):
    return bpy.data.materials.get(name)


def wall_proj(b, x=-2500):
    """A vector that runs along any vertical surface: u is horizontal
    arc-length in the wall's own plane, v is z.  Works at any wall azimuth,
    including the jog's return, without a seam or a ghosted second copy of the
    texture where two walls meet at a corner."""
    tc = b.n('ShaderNodeTexCoord', x=x)
    geo = b.n('ShaderNodeNewGeometry', x=x, y=-520)
    sp = b.n('ShaderNodeSeparateXYZ', x=x + 200)
    b.l(tc, 'Object', sp, 'Vector')
    sn = b.n('ShaderNodeSeparateXYZ', x=x + 200, y=-520)
    b.l(geo, 'True Normal', sn, 'Vector')
    nx2 = b.math('MULTIPLY', sn, 0, sn, 0, x=x + 380, y=-460)
    ny2 = b.math('MULTIPLY', sn, 1, sn, 1, x=x + 380, y=-300)
    s = b.math('ADD', nx2, 0, ny2, 0, x=x + 540, y=-380)
    ln = b.math('SQRT', s, 0, x=x + 680, y=-380)
    safe = b.math('MAXIMUM', ln, 0, vb=0.06, x=x + 820, y=-380)
    a1 = b.math('MULTIPLY', sp, 0, sn, 1, x=x + 380, y=300)
    a2 = b.math('MULTIPLY', sp, 1, sn, 0, x=x + 380, y=460)
    d = b.math('SUBTRACT', a1, 0, a2, 0, x=x + 540, y=380)
    u = b.math('DIVIDE', d, 0, safe, 0, x=x + 960, y=100)
    cmb = b.n('ShaderNodeCombineXYZ', x=x + 1100)
    b.l(u, 0, cmb, 'X')
    b.l(sp, 2, cmb, 'Y')
    return cmb


# ================================================================== PLASTER

def plaster(name, col='CFC3AE', rough=0.86, bump=0.34, patch=0.05, scale=1.0):
    """Painted plaster.  Three things separate this from a flat diffuse fill:
    an orange-peel relief at roughly a centimetre, a much larger and very weak
    tonal drift so a long wall is not one dead value, and a slight roughness
    break-up so grazing light off the windows picks the surface out."""
    m = _mat(name)
    b = NB(m)
    v = wall_proj(b)
    mp = b.mapping(v, 'Vector', scale=(scale,) * 3, x=-1250)

    peel = b.noise((mp, 'Vector'), scale=52.0, detail=5.0, rough=0.62, x=-1050, y=-260)
    fine = b.noise((mp, 'Vector'), scale=210.0, detail=3.0, rough=0.5, x=-1050, y=-460)
    h = b.math('MULTIPLY_ADD', peel, 'Fac', vb=0.72, vc=0.0, x=-860, y=-360)
    h2 = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.28, x=-860, y=-500)
    hh = b.math('ADD', h, 0, h2, 0, x=-700, y=-420)
    nrm = b.bump(hh, 0, strength=bump, dist=0.006, x=-520, y=-420)

    drift = b.noise((mp, 'Vector'), scale=0.85, detail=3.0, rough=0.55, x=-1050, y=260)
    tint = b.ramp(drift, 'Fac', [(0.30, srgb(shade(col, 0.955))),
                                (0.72, srgb(shade(col, 1.035)))], x=-820, y=260)
    # The stain map is a broad noise, but its STRENGTH is `patch` - so the
    # ramp has to be a mix of the two tones weighted down, not the noise used
    # raw as a factor, or every wall gets a full-contrast blotch across it.
    grime = b.noise((mp, 'Vector'), scale=2.4, detail=6.0, rough=0.62, x=-1050, y=460)
    gr = b.ramp(grime, 'Fac', [(0.30, (0.0, 0.0, 0.0)), (0.85, (patch,) * 3)],
                x=-820, y=460)
    base = b.mix(tint, 0, shade(col, 0.90), 0, gr, 0, 'MIX', x=-560, y=300)
    rg = b.ramp(peel, 'Fac', [(0.25, (rough - 0.06,) * 3), (0.80, (rough + 0.05,) * 3)],
                x=-560, y=-120)
    p = b.principled(base=base, baseo=2, roughn=rg, rougho=0, normal=nrm, spec=0.30,
                     ior=1.44)
    b.out(p)
    return m


def ceiling_paint(name, col='E0DACD'):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1400)
    n1 = b.noise((tc, 'Object'), scale=34.0, detail=5.0, rough=0.6, x=-1150)
    n2 = b.noise((tc, 'Object'), scale=1.1, detail=3.0, rough=0.5, x=-1150, y=-260)
    nrm = b.bump(n1, 'Fac', strength=0.22, dist=0.005, x=-800)
    base = b.ramp(n2, 'Fac', [(0.3, srgb(shade(col, 0.97))), (0.75, srgb(col))], x=-880, y=-260)
    p = b.principled(base=base, baseo=0, rough=0.92, normal=nrm, spec=0.22)
    b.out(p)
    return m


# ================================================================== PAINT

def paint(name, col='DED6C4', rough=0.28, coat=0.0, brush=0.5, sheen_lift=0.0):
    """Enamelled joinery paint.  Set dressing is repainted constantly, so the
    film is thick, slightly uneven and holds a faint brush direction; that
    directional relief is most of what makes painted trim read as painted wood
    rather than as tinted plastic."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1700)
    mp = b.mapping(tc, 'Object', scale=(1.0, 26.0, 1.0), x=-1500)
    br = b.noise((mp, 'Vector'), scale=44.0, detail=4.0, rough=0.5, x=-1300, y=-240)
    lump = b.noise((tc, 'Object'), scale=7.0, detail=4.0, rough=0.55, x=-1300, y=-440)
    h = b.math('MULTIPLY_ADD', br, 'Fac', vb=0.55 * brush, x=-1080, y=-300)
    h2 = b.math('MULTIPLY_ADD', lump, 'Fac', vb=0.45, x=-1080, y=-460)
    hh = b.math('ADD', h, 0, h2, 0, x=-900, y=-380)
    nrm = b.bump(hh, 0, strength=0.16 + 0.10 * brush, dist=0.004, x=-720, y=-380)
    drift = b.noise((tc, 'Object'), scale=1.6, detail=3.0, rough=0.5, x=-1300, y=240)
    base = b.ramp(drift, 'Fac', [(0.28, srgb(shade(col, 0.965))),
                                 (0.74, srgb(shade(col, 1.025)))], x=-1000, y=240)
    rg = b.ramp(lump, 'Fac', [(0.2, (rough - 0.05,) * 3), (0.85, (rough + 0.07,) * 3)],
                x=-1000, y=-120)
    p = b.principled(base=base, baseo=0, roughn=rg, normal=nrm, spec=0.5, coat=coat,
                     ior=1.5, sheen=sheen_lift, sheen_tint=col)
    b.out(p)
    return m


# ================================================================== WOOD

def wood(name, cols, ring=24.0, warp=0.5, rough=(0.26, 0.5), coord='Object',
         axis='X', bump=0.16, pore=1.0, tint_attr=None, scale=1.0, aniso=0.3,
         distort=1.5, coat=0.0, grain_relief=0.14, sheen=0.0):
    """Generic procedural timber.  cols: three hex tones - early-wood, mid,
    late-wood/figure.

    `axis` names the direction the growth rings vary along; the grain lines run
    perpendicular to it.  Pick the axis that stays constant along the member,
    or a table leg ends up with rings running up it like a barber's pole.

    `grain_relief` is how deep the rings cut the normal.  Push it and every
    ring becomes an engraved contour line, which is what makes procedural wood
    look like a topographic map: on polished furniture the shading has to come
    from the timber's colour, not from its relief.
    """
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2300)
    src, so = tc, ('UV' if coord == 'UV' else 'Object')
    ROT = {'X': (0, 0, 0), 'Y': (0, 0, math.pi / 2), 'Z': (0, math.pi / 2, 0),
           'XY': (0, 0, -math.pi / 4), 'XZ': (0, math.pi / 4, 0),
           'YZ': (0, math.pi / 2, -math.pi / 4), 'D': (0, 0, math.radians(30))}
    mp = b.mapping(src, so, scale=(scale,) * 3, rot=ROT.get(axis, (0, 0, 0)), x=-2100)
    sep = b.n('ShaderNodeSeparateXYZ', x=-1940)
    b.l(mp, 'Vector', sep, 'Vector')

    # Warp and distortion shove the ring axis, but what they do depends on how
    # far apart the rings are.  Push the axis more than about half a ring
    # period and the grain folds back through itself and closes into islands -
    # the blotchy look that is the ABSENCE of cathedral figure, not the
    # presence of it.  Hold the total against the ring period so no caller can
    # ask for that; anything already gentle passes through untouched.
    amp = abs(warp) * 1.33 + abs(distort) * 0.055
    k = min(1.0, (0.55 / max(ring, 1e-6)) / amp) if amp > 1e-9 else 1.0
    warp, distort = warp * k, distort * k

    w1n = b.noise((mp, 'Vector'), scale=1.6, detail=3.0, rough=0.6, x=-1900, y=-300)
    w1 = b.math('MULTIPLY_ADD', w1n, 'Fac', vb=warp, vc=-0.5 * warp, x=-1740, y=-300)
    w2n = b.noise((mp, 'Vector'), scale=6.9, detail=3.0, rough=0.55, x=-1900, y=-460)
    w2 = b.math('MULTIPLY_ADD', w2n, 'Fac', vb=warp * 0.33, vc=-0.165 * warp, x=-1740, y=-460)
    w3n = b.noise((mp, 'Vector'), scale=0.42, detail=2.0, rough=0.5, x=-1900, y=-620)
    w3 = b.math('MULTIPLY_ADD', w3n, 'Fac', vb=distort * 0.055,
                vc=-0.0275 * distort, x=-1740, y=-620)
    s12 = b.math('ADD', w1, 0, w2, 0, x=-1580, y=-380)
    ws = b.math('ADD', s12, 0, w3, 0, x=-1440, y=-500)
    warped = b.math('ADD', sep, 0, ws, 0, x=-1300, y=-160)

    # Ring spacing must not be constant - real growth years vary in width, and
    # a fixed period is exactly what makes procedural timber look like
    # corduroy.  This is a phase offset added AFTER the ring count, never a
    # multiplier on the coordinate: multiplied, the wobble gets amplified by
    # however far the surface sits from the world origin, and this flat is
    # eight metres across.
    cnt = b.math('MULTIPLY', warped, 0, vb=ring, x=-1160, y=-160)
    dn = b.noise((mp, 'Vector'), scale=0.9, detail=2.0, rough=0.5, x=-1300, y=-780)
    ph = b.math('MULTIPLY_ADD', dn, 'Fac', vb=2.4, vc=-1.2, x=-1160, y=-780)
    cnt2 = b.math('ADD', cnt, 0, ph, 0, x=-1020, y=-380)
    fr = b.math('FRACT', cnt2, 0, x=-880, y=-380)

    cl = [srgb(c) for c in cols]
    rings = b.ramp(fr, 0, [(0.00, cl[0]), (0.30, cl[1]), (0.52, cl[2]),
                           (0.62, cl[1]), (1.00, cl[0])], x=-720, y=-160)

    # blotch: broad tonal variation across the board, independent of the rings
    bl = b.noise((mp, 'Vector'), scale=1.15, detail=4.0, rough=0.55, x=-1300, y=340)
    blr = b.ramp(bl, 'Fac', [(0.25, (0.86, 0.86, 0.86)), (0.78, (1.14, 1.14, 1.14))],
                 x=-1060, y=340)
    tinted = b.mix(rings, 0, blr, 0, None, blend='MULTIPLY', x=-520, y=180, factor=1.0)

    if tint_attr:
        at = b.n('ShaderNodeAttribute', x=-1060, y=560)
        at.attribute_name = tint_attr
        tinted = b.mix(tinted, 2, at, 0, None, blend='MULTIPLY', x=-340, y=300, factor=1.0)

    # pores: fine elongated ticks running WITH the grain
    pv = b.mapping(mp, 'Vector', scale=(1.0, 34.0, 5.0), x=-1300, y=-980)
    pn = b.vor((pv, 'Vector'), scale=90.0, rand=1.0, x=-1120, y=-980, feat='F1')
    pr = b.ramp(pn, 'Distance', [(0.0, (0, 0, 0)), (0.22, (1, 1, 1))], x=-940, y=-980)
    ringh = b.ramp(fr, 0, [(0.0, (0.5, .5, .5)), (0.5, (0.0, 0, 0)), (1.0, (0.5, .5, .5))],
                   x=-880, y=-1160)
    ph2 = b.math('MULTIPLY_ADD', pr, 0, vb=0.42 * pore, x=-720, y=-980)
    rh = b.math('MULTIPLY_ADD', ringh, 0, vb=grain_relief, x=-720, y=-1160)
    hsum = b.math('ADD', ph2, 0, rh, 0, x=-560, y=-1060)
    nrm = b.bump(hsum, 0, strength=bump, dist=0.004, x=-380, y=-1060)

    rg = b.ramp(pr, 0, [(0.0, (rough[1],) * 3), (0.35, (rough[0],) * 3)], x=-560, y=-700)
    p = b.principled(base=tinted, baseo=2, roughn=rg, rougho=0, normal=nrm,
                     spec=0.45, coat=coat, aniso=aniso, ior=1.52, sheen=sheen,
                     sheen_tint=cols[1])
    b.out(p)
    return m


# ================================================================== METAL

def metal(name, col='C6C8CA', rough=0.22, aniso=0.0, brush=0.0, grime=0.0,
          bump=0.06, scale=1.0):
    """Metal.  `brush` adds a directional satin; `grime` breaks the roughness
    up so a chrome leg is not a perfect mirror where hands and shoes reach it."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1700)
    mp = b.mapping(tc, 'Object', scale=(scale * 90.0, scale * 1.4, scale * 90.0), x=-1500)
    ln = b.noise((mp, 'Vector'), scale=26.0, detail=4.0, rough=0.5, x=-1300)
    gn = b.noise((tc, 'Object'), scale=6.0, detail=5.0, rough=0.6, x=-1300, y=-280)
    h = b.math('MULTIPLY_ADD', ln, 'Fac', vb=brush + 0.15, x=-1080, y=-140)
    nrm = b.bump(h, 0, strength=bump + brush * 0.25, dist=0.003, x=-880, y=-140)
    rg = b.ramp(ln, 'Fac', [(0.1, (max(0.02, rough - 0.07),) * 3), (0.9, (rough + 0.08,) * 3)],
                x=-1080, y=-420)
    if grime:
        rg2 = b.ramp(gn, 'Fac', [(0.35, (rough,) * 3), (0.85, (min(0.9, rough + 0.35),) * 3)],
                     x=-1080, y=-620)
        rg = b.mix(rg, 0, rg2, 0, None, blend='MIX', x=-860, y=-520, factor=grime)
        ro, roo = rg, 2
    else:
        ro, roo = rg, 0
    base = b.ramp(gn, 'Fac', [(0.2, srgb(shade(col, 0.93))), (0.8, srgb(col))], x=-1080, y=200)
    p = b.principled(base=base, baseo=0, roughn=ro, rougho=roo, metal=1.0,
                     normal=nrm, aniso=aniso, spec=0.5)
    b.out(p)
    return m


def enamel(name, col='F2EDE2', rough=0.12, tint='E8E2D2'):
    """Vitreous appliance enamel - the fridge and the range.  A thick, slightly
    wavy glaze over steel: the highlight has to ripple a little or the panel
    reads as flat plastic."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1500)
    wav = b.noise((tc, 'Object'), scale=2.6, detail=3.0, rough=0.45, x=-1300)
    chip = b.vor((tc, 'Object'), scale=42.0, rand=1.0, x=-1300, y=-300, feat='F1')
    h = b.math('MULTIPLY_ADD', wav, 'Fac', vb=0.8, x=-1080, y=-120)
    nrm = b.bump(h, 0, strength=0.10, dist=0.004, x=-880, y=-120)
    base = b.ramp(wav, 'Fac', [(0.3, srgb(tint)), (0.75, srgb(col))], x=-1080, y=220)
    rg = b.ramp(chip, 'Distance', [(0.0, (rough + 0.18,) * 3), (0.15, (rough,) * 3)],
                x=-1080, y=-420)
    p = b.principled(base=base, baseo=0, roughn=rg, rougho=0, normal=nrm,
                     spec=0.6, coat=0.55, coat_rough=0.045, ior=1.5)
    b.out(p)
    return m


# ================================================================== FABRIC

def fabric(name, col='9A8F7A', rough=0.78, weave=340.0, sheen=0.35, bump=0.4,
           fuzz=0.5):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1600)
    wx = b.n('ShaderNodeTexWave', x=-1350, y=-140)
    wx.bands_direction = 'X'
    wx.wave_profile = 'SIN'
    wx.inputs['Scale'].default_value = weave
    b.l(tc, 'Object', wx, 'Vector')
    wy = b.n('ShaderNodeTexWave', x=-1350, y=-340)
    wy.bands_direction = 'Y'
    wy.wave_profile = 'SIN'
    wy.inputs['Scale'].default_value = weave
    b.l(tc, 'Object', wy, 'Vector')
    wv = b.math('MULTIPLY', wx, 'Fac', wy, 'Fac', x=-1130, y=-240)
    fz = b.noise((tc, 'Object'), scale=weave * 2.4, detail=3.0, rough=0.6, x=-1350, y=-560)
    h = b.math('MULTIPLY_ADD', fz, 'Fac', vb=0.35 * fuzz, x=-1130, y=-540)
    hs = b.math('ADD', wv, 0, h, 0, x=-960, y=-380)
    nrm = b.bump(hs, 0, strength=bump, dist=0.0025, x=-780, y=-380)
    dr = b.noise((tc, 'Object'), scale=3.4, detail=4.0, rough=0.55, x=-1350, y=260)
    base = b.ramp(dr, 'Fac', [(0.25, srgb(shade(col, 0.9))), (0.8, srgb(shade(col, 1.06)))],
                  x=-1100, y=260)
    p = b.principled(base=base, baseo=0, rough=rough, normal=nrm, spec=0.28,
                     sheen=sheen, sheen_tint=shade(col, 1.4))
    b.out(p)
    return m


def velvet(name, col='0E4A44', rough=0.55, sheen=0.9):
    """Cut velvet - the barstool tops.  The pile means the fabric goes PALE at
    grazing angles, so the sheen lobe does the work and the base stays dark."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1500)
    pile = b.noise((tc, 'Object'), scale=460.0, detail=3.0, rough=0.6, x=-1300, y=-200)
    crush = b.noise((tc, 'Object'), scale=17.0, detail=5.0, rough=0.62, x=-1300, y=-420)
    h = b.math('MULTIPLY_ADD', pile, 'Fac', vb=0.5, x=-1090, y=-260)
    h2 = b.math('MULTIPLY_ADD', crush, 'Fac', vb=0.5, x=-1090, y=-420)
    hs = b.math('ADD', h, 0, h2, 0, x=-930, y=-340)
    nrm = b.bump(hs, 0, strength=0.28, dist=0.003, x=-760, y=-340)
    base = b.ramp(crush, 'Fac', [(0.2, srgb(shade(col, 0.72))), (0.85, srgb(shade(col, 1.2)))],
                  x=-1090, y=220)
    rg = b.ramp(crush, 'Fac', [(0.2, (rough - 0.1,) * 3), (0.9, (rough + 0.12,) * 3)],
                x=-1090, y=-40)
    p = b.principled(base=base, baseo=0, roughn=rg, rougho=0, normal=nrm, spec=0.2,
                     sheen=sheen, sheen_tint=shade(col, 2.6))
    b.out(p)
    return m


def leather(name, col='121214', rough=0.34, crease=1.0, grain=1.0, coat=0.35,
            scale=1.0, sheen=0.0):
    """Upholstery leather.  Two scales of relief: the pebble grain, and the far
    larger soft creasing where the hide has been sat in.  Black leather is all
    highlight - what the eye reads is the SHAPE of that highlight breaking over
    the creases, so those have to be geometry-scale, not a fine noise."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1600)
    mp = b.mapping(tc, 'Object', scale=(scale,) * 3, x=-1420)
    cell = b.vor((mp, 'Vector'), scale=120.0, rand=0.95, x=-1220, y=-220, feat='F1')
    cr = b.noise((mp, 'Vector'), scale=9.0, detail=5.0, rough=0.68, dist=0.6,
                 x=-1220, y=-460)
    cr2 = b.noise((mp, 'Vector'), scale=26.0, detail=4.0, rough=0.6, x=-1220, y=-660)
    g = b.ramp(cell, 'Distance', [(0.0, (0, 0, 0)), (0.32, (1, 1, 1))], x=-1010, y=-220)
    hg = b.math('MULTIPLY_ADD', g, 0, vb=0.30 * grain, x=-840, y=-220)
    hc = b.math('MULTIPLY_ADD', cr, 'Fac', vb=0.90 * crease, x=-840, y=-460)
    hc2 = b.math('MULTIPLY_ADD', cr2, 'Fac', vb=0.30 * crease, x=-840, y=-620)
    s1 = b.math('ADD', hg, 0, hc, 0, x=-680, y=-340)
    hs = b.math('ADD', s1, 0, hc2, 0, x=-540, y=-460)
    nrm = b.bump(hs, 0, strength=0.55, dist=0.004, x=-380, y=-460)
    base = b.ramp(cr, 'Fac', [(0.22, srgb(shade(col, 0.80))), (0.80, srgb(shade(col, 1.22)))],
                  x=-1010, y=240)
    rg = b.ramp(g, 0, [(0.0, (rough + 0.20,) * 3), (0.55, (rough,) * 3)], x=-1010, y=-40)
    p = b.principled(base=base, baseo=0, roughn=rg, rougho=0, normal=nrm, spec=0.55,
                     coat=coat, coat_rough=0.22, ior=1.48, sheen=sheen,
                     sheen_tint=shade(col, 1.6))
    b.out(p)
    return m


# ================================================================== TILE

def tile(name, col='EDE7DA', grout='B7AE9C', size=0.152, joint=0.010, rough=0.16,
         relief=0.55, mottle=0.5, plane='XZ'):
    """Glazed square tile with real grout joints.  `plane` chooses which pair
    of world axes the grid runs in, so a splashback and a worktop cut from the
    same material still line their joints up with their own surface."""
    m = _mat(name)
    b = NB(m)
    if plane == 'XZ':
        v = wall_proj(b)
        src, so = v, 'Vector'
    else:
        src, so = b.n('ShaderNodeTexCoord', x=-2000), 'Object'
    mp = b.mapping(src, so, scale=(1.0 / size, 1.0 / size, 1.0 / size), x=-1500)
    sep = b.n('ShaderNodeSeparateXYZ', x=-1340)
    b.l(mp, 'Vector', sep, 'Vector')
    fu = b.math('FRACT', sep, 0, x=-1180, y=120)
    fv = b.math('FRACT', sep, 1, x=-1180, y=-80)
    t = joint / size
    # distance to the nearest joint, in tile units
    su = b.math('SUBTRACT', va=1.0, b=fu, bo=0, x=-1020, y=40)
    mu = b.math('MINIMUM', fu, 0, su, 0, x=-880, y=80)
    sv = b.math('SUBTRACT', va=1.0, b=fv, bo=0, x=-1020, y=-160)
    mv = b.math('MINIMUM', fv, 0, sv, 0, x=-880, y=-120)
    d = b.math('MINIMUM', mu, 0, mv, 0, x=-740, y=-20)
    gmask = b.ramp(d, 0, [(t * 0.45, (0, 0, 0)), (t * 1.15, (1, 1, 1))], x=-600, y=-20)

    mot = b.noise((mp, 'Vector'), scale=0.9, detail=4.0, rough=0.55, x=-1340, y=380)
    cellv = b.vor((mp, 'Vector'), scale=1.0, rand=0.0, x=-1340, y=560, feat='F1')
    per = b.ramp(cellv, 'Color', [(0.15, srgb(shade(col, 0.965))),
                                  (0.85, srgb(shade(col, 1.03)))], x=-1120, y=560)
    face = b.mix(per, 0, shade(col, 0.93), 0, mot, 'Fac', 'MIX', x=-900, y=440)
    base = b.mix(grout, 0, face, 2, gmask, 0, 'MIX', x=-680, y=300)
    hh = b.math('MULTIPLY_ADD', gmask, 0, vb=relief, x=-600, y=-220)
    nrm = b.bump(hh, 0, strength=0.85, dist=0.0035, x=-440, y=-220)
    rg = b.mix((rough + 0.55,) * 3, 0, (rough,) * 3, 0, gmask, 0, 'MIX', x=-680, y=-420)
    p = b.principled(base=base, baseo=2, roughn=rg, rougho=2, normal=nrm, spec=0.5,
                     coat=0.35, coat_rough=0.08, ior=1.5)
    b.out(p)
    return m


# ================================================================== GLASS etc.

def ceramic(name, col='E7EAE3', rough=0.08, pitch=0.1088, vary=1.0):
    """Glaze for tiles that are REAL GEOMETRY - so no grout grid here, the
    joints are modelled.  What the shader has to supply is what makes a wall of
    tiles read as a wall of tiles rather than one sheet: each tile fired
    slightly differently, and a glaze surface that ripples enough to break the
    reflection up tile by tile."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1700)
    mp = b.mapping(tc, 'Object', scale=(1.0 / pitch,) * 3, x=-1500)
    cell = b.vor((mp, 'Vector'), scale=1.0, rand=0.0, x=-1300, y=200, feat='F1')
    per = b.ramp(cell, 'Color', [(0.10, srgb(shade(col, 0.955))),
                                 (0.90, srgb(shade(col, 1.035)))], x=-1060, y=200)
    fire = b.noise((mp, 'Vector'), scale=0.42, detail=4.0, rough=0.55, x=-1300, y=420)
    base = b.mix(per, 0, shade(col, 0.93), 0, fire, 'Fac', 'MIX', x=-820, y=300)
    rip = b.noise((mp, 'Vector'), scale=2.6, detail=4.0, rough=0.5, x=-1300, y=-260)
    fine = b.noise((tc, 'Object'), scale=260.0, detail=3.0, rough=0.5, x=-1300, y=-460)
    h1 = b.math('MULTIPLY_ADD', rip, 'Fac', vb=0.85 * vary, x=-1080, y=-300)
    h2 = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.15, x=-1080, y=-460)
    hs = b.math('ADD', h1, 0, h2, 0, x=-900, y=-380)
    nrm = b.bump(hs, 0, strength=0.16, dist=0.0035, x=-720, y=-380)
    rg = b.ramp(rip, 'Fac', [(0.2, (rough,) * 3), (0.85, (rough + 0.06,) * 3)],
                x=-1080, y=-100)
    p = b.principled(base=base, baseo=2, roughn=rg, rougho=0, normal=nrm,
                     spec=0.6, coat=0.62, coat_rough=0.045, ior=1.52)
    b.out(p)
    return m


def pane(name, tint='EDF2F4', rough=0.02, alpha=0.10, wave=1.0, grime=0.35):
    """Old drawn glass in a sash window.

    Two things stop a pane reading as a hole in the wall.  Its SURFACE is not
    flat - drawn glass ripples at a scale the eye reads as a slow wobble
    travelling across whatever is reflected in it - and it is never clean, so
    the roughness climbs towards the edges where the putty line and the frame
    collect dust.  A perfectly smooth, perfectly clean pane is the one piece of
    "correct" physics that always looks wrong."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1700)
    rip = b.noise((tc, 'Object'), scale=3.0, detail=3.0, rough=0.45, x=-1460)
    fine = b.noise((tc, 'Object'), scale=38.0, detail=3.0, rough=0.5,
                   x=-1460, y=-240)
    h1 = b.math('MULTIPLY_ADD', rip, 'Fac', vb=0.90 * wave, x=-1240, y=-110)
    h2 = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.12 * wave, x=-1240, y=-250)
    hs = b.math('ADD', h1, 0, h2, 0, x=-1060, y=-180)
    nrm = b.bump(hs, 0, strength=0.055 * wave, dist=0.005, x=-880, y=-180)
    dirt = b.noise((tc, 'Object'), scale=7.5, detail=5.0, rough=0.62,
                   x=-1460, y=260)
    rg = b.ramp(dirt, 'Fac', [(0.28, (rough,) * 3),
                              (0.88, (rough + 0.11 * grime,) * 3)],
                x=-1220, y=260)
    base = b.ramp(dirt, 'Fac', [(0.30, srgb(tint)),
                                (0.90, srgb(shade(tint, 0.94)))], x=-1220, y=460)
    p = b.principled(base=base, baseo=0, roughn=rg, rougho=0, normal=nrm,
                     transm=1.0, ior=1.52, spec=0.5)
    b.out(p)
    m.use_backface_culling = False
    return m


def clear_glass(name, tint='E9F1F2', rough=0.015, smear=0.6):
    """Table and vessel glass.  Cleaner than a window but handled - so the
    roughness breaks up in smears and fingerprints at hand height rather than
    over the whole sheet, and the surface carries only a very fine relief."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1600)
    sm = b.noise((tc, 'Object'), scale=26.0, detail=6.0, rough=0.68, dist=1.2,
                 x=-1380, y=220)
    fine = b.noise((tc, 'Object'), scale=180.0, detail=3.0, rough=0.5,
                   x=-1380, y=-220)
    h = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.35, x=-1160, y=-220)
    nrm = b.bump(h, 0, strength=0.020, dist=0.002, x=-960, y=-220)
    rg = b.ramp(sm, 'Fac', [(0.42, (rough,) * 3),
                            (0.78, (rough + 0.085 * smear,) * 3)],
                x=-1160, y=220)
    p = b.principled(color=tint, roughn=rg, rougho=0, normal=nrm, transm=1.0,
                     ior=1.52, spec=0.5)
    b.out(p)
    return m


def emissive(name, col='FFF1D2', strength=6.0):
    m = _mat(name)
    b = NB(m)
    e = b.n('ShaderNodeEmission', x=0)
    e.inputs['Color'].default_value = srgb(col)
    e.inputs['Strength'].default_value = strength
    b.out(e)
    return m


def plastic(name, col='E9E9E4', rough=0.28, coat=0.25, bump=0.06):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1200)
    n1 = b.noise((tc, 'Object'), scale=280.0, detail=3.0, rough=0.5, x=-1000)
    n2 = b.noise((tc, 'Object'), scale=4.0, detail=3.0, rough=0.5, x=-1000, y=-240)
    nrm = b.bump(n1, 'Fac', strength=bump, dist=0.002, x=-780)
    base = b.ramp(n2, 'Fac', [(0.3, srgb(shade(col, 0.97))), (0.8, srgb(col))], x=-780, y=-240)
    p = b.principled(base=base, baseo=0, rough=rough, normal=nrm, coat=coat, spec=0.5)
    b.out(p)
    return m


def rubber(name, col='1A1A1C', rough=0.72):
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1000)
    n1 = b.noise((tc, 'Object'), scale=180.0, detail=4.0, rough=0.6, x=-820)
    nrm = b.bump(n1, 'Fac', strength=0.3, dist=0.002, x=-620)
    p = b.principled(color=col, rough=rough, normal=nrm, spec=0.35)
    b.out(p)
    return m


# ================================================================== STONE

def stone(name, col='F1EEE6', vein='CBC2B0', rough=0.13, scale=1.0, coat=0.40,
          speck=0.6, vein_str=0.55):
    """Composite worktop - the kitchen counter and the island top.

    Two independent structures: a slow, stretched vein running through the
    slab, and a fine mineral speckle sitting on top of it.  The speckle is what
    stops it reading as painted board, and it has to be almost colourless -
    speckle with hue in it turns the whole slab into granite worktop showroom
    samples, which is not what a 1990s sitcom kitchen has.
    """
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1800)
    mp = b.mapping(tc, 'Object', scale=(scale * 0.55, scale * 1.6, scale * 0.55),
                   x=-1600)
    vn = b.noise((mp, 'Vector'), scale=2.3, detail=8.0, rough=0.62, dist=1.5,
                 x=-1400, y=200)
    vr = b.ramp(vn, 'Fac', [(0.40, srgb(col)), (0.52, srgb(vein)),
                            (0.63, srgb(col))], x=-1160, y=200)
    base = b.mix(col, 0, vr, 0, None, blend='MIX', x=-900, y=240, factor=vein_str)
    gr = b.vor((tc, 'Object'), scale=1400.0, rand=1.0, x=-1400, y=-40, feat='F1')
    grr = b.ramp(gr, 'Distance', [(0.0, (0.80, 0.80, 0.80)),
                                  (0.30, (1.06, 1.06, 1.06))], x=-1160, y=-40)
    spk = b.mix(base, 2, grr, 0, None, blend='MULTIPLY', x=-660, y=100, factor=speck)
    fine = b.noise((tc, 'Object'), scale=520.0, detail=3.0, rough=0.5, x=-1400, y=-360)
    h = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.5, x=-1160, y=-360)
    nrm = b.bump(h, 0, strength=0.055, dist=0.0025, x=-940, y=-360)
    rg = b.ramp(gr, 'Distance', [(0.0, (rough + 0.05,) * 3), (0.4, (rough,) * 3)],
                x=-1160, y=-560)
    p = b.principled(base=spk, baseo=2, roughn=rg, rougho=0, normal=nrm,
                     spec=0.5, coat=coat, coat_rough=0.04, ior=1.5)
    b.out(p)
    return m


def carpet(name, col='DCD5C4', rough=0.94, pile=1.0, scale=1.0):
    """Cut pile.  The give-away for carpet is not colour, it is that the pile
    lies in clumps - so the tone has to vary at two scales at once, and the
    sheen has to be strong enough that the rug goes pale where it is walked
    on."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1500)
    mp = b.mapping(tc, 'Object', scale=(scale,) * 3, x=-1340)
    tuft = b.vor((mp, 'Vector'), scale=300.0, rand=1.0, x=-1160, y=-200, feat='F1')
    clump = b.noise((mp, 'Vector'), scale=13.0, detail=5.0, rough=0.62, x=-1160, y=-460)
    h1 = b.math('MULTIPLY_ADD', tuft, 'Distance', vb=2.6 * pile, x=-940, y=-240)
    h2 = b.math('MULTIPLY_ADD', clump, 'Fac', vb=0.55 * pile, x=-940, y=-460)
    hs = b.math('ADD', h1, 0, h2, 0, x=-760, y=-340)
    nrm = b.bump(hs, 0, strength=0.55, dist=0.0035, x=-580, y=-340)
    base = b.ramp(clump, 'Fac', [(0.20, srgb(shade(col, 0.88))),
                                 (0.82, srgb(shade(col, 1.08)))], x=-940, y=240)
    p = b.principled(base=base, baseo=0, rough=rough, normal=nrm, spec=0.20,
                     sheen=0.55, sheen_tint=shade(col, 1.5))
    b.out(p)
    return m


def paper(name, col='D8D2C4', rough=0.58, sheen=0.0, gloss=0.0):
    """Printed board - cereal cartons, posters, book jackets."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1200)
    tooth = b.noise((tc, 'Object'), scale=420.0, detail=3.0, rough=0.5, x=-1000)
    crease = b.noise((tc, 'Object'), scale=9.0, detail=4.0, rough=0.55, x=-1000, y=-260)
    h = b.math('MULTIPLY_ADD', tooth, 'Fac', vb=0.4, x=-800, y=-60)
    nrm = b.bump(h, 0, strength=0.10, dist=0.002, x=-620, y=-60)
    base = b.ramp(crease, 'Fac', [(0.28, srgb(shade(col, 0.94))),
                                  (0.80, srgb(shade(col, 1.05)))], x=-800, y=240)
    p = b.principled(base=base, baseo=0, rough=rough, normal=nrm, spec=0.4,
                     coat=gloss, coat_rough=0.10, sheen=sheen, sheen_tint=col)
    b.out(p)
    return m


# ================================================================== PRINTED CLOTH

def _cloth_relief(b, weave, bump, fuzz=0.5, x=-1350):
    wx = b.n('ShaderNodeTexWave', x=x, y=-140)
    wx.bands_direction, wx.wave_profile = 'X', 'SIN'
    wx.inputs['Scale'].default_value = weave
    wy = b.n('ShaderNodeTexWave', x=x, y=-340)
    wy.bands_direction, wy.wave_profile = 'Y', 'SIN'
    wy.inputs['Scale'].default_value = weave
    tc = b.n('ShaderNodeTexCoord', x=x - 240, y=-240)
    b.l(tc, 'Object', wx, 'Vector')
    b.l(tc, 'Object', wy, 'Vector')
    wv = b.math('MULTIPLY', wx, 'Fac', wy, 'Fac', x=x + 220, y=-240)
    fz = b.noise((tc, 'Object'), scale=weave * 2.2, detail=3.0, rough=0.6,
                 x=x, y=-560)
    h = b.math('MULTIPLY_ADD', fz, 'Fac', vb=0.35 * fuzz, x=x + 220, y=-540)
    hs = b.math('ADD', wv, 0, h, 0, x=x + 390, y=-380)
    return b.bump(hs, 0, strength=bump, dist=0.0025, x=x + 560, y=-380)


def stripe(name, cols=('E8E2D2', 'B4463C', '2E6B62', 'E8E2D2', 'D8A63C'),
           pitch=0.062, rough=0.80, axis='Z', weave=300.0, sheen=0.30,
           bump=0.42):
    """Woven ticking.  Bands run across `axis`, hard-edged - a stripe is dyed
    yarn, so there is no gradient between one colour and the next, and a linear
    ramp here is the single fastest way to make cloth look printed."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2000, y=300)
    sep = b.n('ShaderNodeSeparateXYZ', x=-1820, y=300)
    b.l(tc, 'Object', sep, 'Vector')
    k = {'X': 0, 'Y': 1, 'Z': 2}[axis]
    u = b.math('MULTIPLY', sep, k, vb=1.0 / pitch, x=-1640, y=300)
    fr = b.math('FRACT', u, 0, x=-1480, y=300)
    n = len(cols)
    stops = []
    for i, c in enumerate(cols):
        stops.append((i / n, srgb(c)))
    ramp = b.ramp(fr, 0, stops, x=-1300, y=300, interp='CONSTANT')
    drift = b.noise((tc, 'Object'), scale=3.0, detail=4.0, rough=0.55, x=-1640, y=560)
    shadeit = b.ramp(drift, 'Fac', [(0.25, (0.90, 0.90, 0.90)),
                                    (0.80, (1.08, 1.08, 1.08))], x=-1460, y=560)
    base = b.mix(ramp, 0, shadeit, 0, None, blend='MULTIPLY', x=-1080, y=420, factor=1.0)
    nrm = _cloth_relief(b, weave, bump)
    p = b.principled(base=base, baseo=2, rough=rough, normal=nrm, spec=0.28,
                     sheen=sheen, sheen_tint=shade(cols[0], 1.35))
    b.out(p)
    return m


def diamond(name, col='C3AE85', ink='9C875C', pitch=0.115, rough=0.76,
            weave=280.0, sheen=0.42, bump=0.40, line=0.16):
    """The living-room curtains: a heavy tan cloth with a woven diamond
    lattice.  The lattice is built in rotated coordinates - a square grid in
    (x+z, x-z) IS a diamond grid in (x, z) - which keeps the lines dead
    straight, where crossing two sine waves would give a soft quilted blob."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2200, y=300)
    sep = b.n('ShaderNodeSeparateXYZ', x=-2020, y=300)
    b.l(tc, 'Object', sep, 'Vector')
    s = 1.0 / pitch
    a = b.math('ADD', sep, 0, sep, 2, x=-1840, y=380)
    d = b.math('SUBTRACT', sep, 0, sep, 2, x=-1840, y=180)
    au = b.math('MULTIPLY', a, 0, vb=s, x=-1690, y=380)
    du = b.math('MULTIPLY', d, 0, vb=s * 1.55, x=-1690, y=180)
    fa = b.math('FRACT', au, 0, x=-1540, y=380)
    fd = b.math('FRACT', du, 0, x=-1540, y=180)
    ca = b.math('SUBTRACT', fa, 0, vb=0.5, x=-1400, y=380)
    cd = b.math('SUBTRACT', fd, 0, vb=0.5, x=-1400, y=180)
    aa = b.math('ABSOLUTE', ca, 0, x=-1260, y=380)
    ad = b.math('ABSOLUTE', cd, 0, x=-1260, y=180)
    mn = b.math('MINIMUM', aa, 0, ad, 0, x=-1110, y=280)
    lat = b.ramp(mn, 0, [(0.0, srgb(ink)), (line, srgb(col))], x=-950, y=280)
    drift = b.noise((tc, 'Object'), scale=2.4, detail=4.0, rough=0.55, x=-1690, y=600)
    sh = b.ramp(drift, 'Fac', [(0.22, (0.88, 0.88, 0.88)), (0.82, (1.10, 1.10, 1.10))],
                x=-1480, y=600)
    base = b.mix(lat, 0, sh, 0, None, blend='MULTIPLY', x=-760, y=420, factor=1.0)
    nrm = _cloth_relief(b, weave, bump)
    p = b.principled(base=base, baseo=2, rough=rough, normal=nrm, spec=0.30,
                     sheen=sheen, sheen_tint=shade(col, 1.45))
    b.out(p)
    return m


def picture(name, path, rough=0.44, gloss=0.22, bump=0.06):
    """A printed image on paper or board.  The image drives base colour off the
    object's own UVs; everything else about it is still procedural - the paper
    tooth in the normal and a light varnish - so it sits in the same lighting
    as the rest of the flat instead of reading as a flat decal."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-1100)
    img = b.n('ShaderNodeTexImage', x=-800)
    try:
        im = bpy.data.images.load(path, check_existing=True)
        img.image = im
    except Exception as e:
        print("picture: could not load", path, e)
    img.extension = 'EXTEND'
    b.l(tc, 'UV', img, 'Vector')
    tooth = b.noise((tc, 'Object'), scale=520.0, detail=3.0, rough=0.5,
                    x=-1100, y=-340)
    h = b.math('MULTIPLY_ADD', tooth, 'Fac', vb=0.4, x=-880, y=-340)
    nrm = b.bump(h, 0, strength=bump, dist=0.0015, x=-680, y=-340)
    p = b.principled(base=img, baseo=0, rough=rough, normal=nrm, spec=0.45,
                     coat=gloss, coat_rough=0.12)
    b.out(p)
    return m
