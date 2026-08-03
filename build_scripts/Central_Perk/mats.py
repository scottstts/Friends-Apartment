"""mats - fully procedural materials for Central Perk.

No image files and no external assets: every surface is a node graph.  The
node builder `NB` and the helpers above the first material are shared with
the Monica's-apartment build; the materials themselves are all new.
"""
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

    @staticmethod
    def sock(coll, key):
        """Resolve a socket, skipping the disabled ones.

        ShaderNodeMix carries one A/B/Result set per data type and hides all
        but the active one, so `inputs['A']` and `outputs[0]` both land on a
        dead VALUE socket - which links without complaint and renders white.
        Anything that resolves to a disabled socket is retried by name against
        the enabled ones."""
        s = coll[key]
        if getattr(s, "enabled", True):
            return s
        for t in coll:
            if t.name == s.name and t.enabled:
                return t
        return s

    def l(self, a, ao, b, bi):
        self.nt.links.new(self.sock(a.outputs, ao), self.sock(b.inputs, bi))

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
            self.sock(m.inputs, 'Factor').default_value = (
                factor if factor is not None else 0.5)
        else:
            self.l(fac, faco if faco is not None else 0, m, 'Factor')
        if isinstance(a, tuple):
            self.sock(m.inputs, 'A').default_value = _c(a)
        else:
            self.l(a, ao, m, 'A')
        if isinstance(b, tuple):
            self.sock(m.inputs, 'B').default_value = _c(b)
        else:
            self.l(b, bo, m, 'B')
        return m

    def fmix(self, a, ao, b, bo, fac, faco=None, x=-900, factor=None):
        """Mix two scalars.  Roughness and strength blends have to go through
        a FLOAT-typed Mix: routing them through the RGBA one works by luck of
        the implicit colour-to-value conversion, and either end of the blend
        may legitimately be a plain number rather than a node."""
        m = self.n('ShaderNodeMix', x=x, data_type='FLOAT')
        if fac is None:
            self.sock(m.inputs, 'Factor').default_value = (
                factor if factor is not None else 0.5)
        else:
            self.l(fac, faco if faco is not None else 0, m, 'Factor')
        for val, o, key in ((a, ao, 'A'), (b, bo, 'B')):
            if isinstance(val, (int, float)):
                self.sock(m.inputs, key).default_value = float(val)
            else:
                self.l(val, o, m, key)
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




# ==================================================================== helpers

def _lattice(b, vec, x=-1500):
    """From a mapped vector, the per-cell fractional coordinate centred on
    zero (`g`), its absolute value split into components, and the cell id.
    Everything tiled - tile, plank, brick - is built off this."""
    fr = b.vmath('FRACTION', vec[0], vec[1], x=x)
    g = b.vmath('SUBTRACT', fr, 0, vb=(0.5, 0.5, 0.5), x=x + 160)
    ab = b.vmath('ABSOLUTE', g, 0, x=x + 320)
    sp = b.n('ShaderNodeSeparateXYZ', x=x + 460)
    b.l(ab, 0, sp, 'Vector')
    cell = b.vmath('FLOOR', vec[0], vec[1], x=x + 160)
    cell.location = (x + 160, -300)
    return g, sp, cell


def _rand(b, cell, x=-900, seed=0.0):
    wn = b.n('ShaderNodeTexWhiteNoise', x=x, noise_dimensions='3D')
    if seed:
        off = b.vmath('ADD', cell, 0, vb=(seed, seed * 1.7, seed * 0.3), x=x - 160)
        b.l(off, 0, wn, 'Vector')
    else:
        b.l(cell, 0, wn, 'Vector')
    return wn


def _obj_vec(b, scale=(1, 1, 1), rot=(0, 0, 0), loc=(0, 0, 0), coord='Object'):
    tc = b.n('ShaderNodeTexCoord', x=-2000)
    m = b.mapping(tc, coord, scale=scale, rot=rot, loc=loc, x=-1800)
    return (m, 0)


def _tri_vec(b, scale=(1.0, 1.0), x=-2400):
    """A 2-D surface coordinate that follows the surface instead of being
    projected straight down the Z axis.

    An object-space XY mapping is fine on a rug and useless on a sofa back.
    Where the normal is horizontal, one of X or Y barely changes across the
    whole panel, so the repeat collapses in that direction and the pattern
    smears into vertical streaks - which is exactly what the damask did on
    the bay settee, at three times its nominal size and only in one axis.

    This is the triplanar trick, reduced to what it costs least to do: pick
    whichever pair of coordinates actually spans the surface, based on the
    dominant axis of the true normal.  The switch is hard rather than
    blended; on upholstery the switch line falls on a curve and never reads,
    and a blend would need the whole pattern evaluated three times."""
    tc = b.n('ShaderNodeTexCoord', x=x)
    geo = b.n('ShaderNodeNewGeometry', x=x, y=-460)
    p = b.n('ShaderNodeSeparateXYZ', x=x + 200)
    b.l(tc, 'Object', p, 'Vector')
    ab = b.vmath('ABSOLUTE', geo, 'True Normal', x=x + 200)
    ab.location = (x + 200, -460)
    n = b.n('ShaderNodeSeparateXYZ', x=x + 360, y=-460)
    b.l(ab, 0, n, 'Vector')

    def dom(i, j, k, y):
        g1 = b.math('GREATER_THAN', n, i, n, j, x=x + 520)
        g1.location = (x + 520, y)
        g2 = b.math('GREATER_THAN', n, i, n, k, x=x + 520)
        g2.location = (x + 520, y - 130)
        m = b.math('MULTIPLY', g1, 0, g2, 0, x=x + 660)
        m.location = (x + 660, y - 65)
        return m

    kx = dom(0, 1, 2, -460)          # normal points along X -> use (y, z)
    kz = dom(2, 0, 1, -900)          # normal points along Z -> use (x, y)
    # a = x, or y when the surface faces along X
    a = b.fmix(p, 0, p, 1, kx, 0, x=x + 820)
    a.location = (x + 820, 120)
    # b = z, or y when the surface faces along Z
    bb = b.fmix(p, 2, p, 1, kz, 0, x=x + 820)
    bb.location = (x + 820, -120)
    sa = b.math('MULTIPLY', a, 0, vb=scale[0], x=x + 980)
    sa.location = (x + 980, 120)
    sb = b.math('MULTIPLY', bb, 0, vb=scale[1], x=x + 980)
    sb.location = (x + 980, -120)
    cmb = b.n('ShaderNodeCombineXYZ', x=x + 1140)
    b.l(sa, 0, cmb, 'X')
    b.l(sb, 0, cmb, 'Y')
    return (cmb, 0)


# ==================================================================== FLOORS

def concrete(name='floor_concrete', hexcol='7C8179',
             rough=(0.42, 0.72), scale=1.6):
    """Troweled, sealed concrete: broad tonal drift, a fine aggregate speckle
    and a polish that varies with it, so the sheen breaks up like a real
    power-floated slab instead of reading as one flat plane."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(scale,) * 3)
    drift = b.noise(v, scale=0.9, detail=4.0, rough=0.62, x=-1500)
    fine = b.noise(v, scale=26.0, detail=8.0, rough=0.75, x=-1500)
    fine.location = (-1500, -320)
    grit = b.n('ShaderNodeTexVoronoi', x=-1500, y=-640, feature='F1',
               voronoi_dimensions='3D')
    grit.inputs['Scale'].default_value = 140.0
    b.l(v[0], v[1], grit, 'Vector')

    base = srgb(hexcol)
    dark = tuple(c * 0.74 for c in base[:3])
    lite = tuple(min(1.0, c * 1.26) for c in base[:3])
    c1 = b.mix(dark, 0, lite, 0, drift, 'Fac', x=-1150)
    c2 = b.mix(c1, 0, (base[0] * 0.86, base[1] * 0.9, base[2] * 0.86), 0,
               fine, 'Fac', x=-950)
    c2.inputs['Factor'].default_value = 0.35
    b.l(fine, 0, c2, 'Factor')
    c3 = b.mix(c2, 0, (lite[0], lite[1], lite[2]), 0, grit, 'Distance', x=-760)
    c3.inputs['Factor'].default_value = 0.18

    rg = b.ramp(drift, 'Fac', [(0.15, (rough[0],) * 3), (0.85, (rough[1],) * 3)],
                x=-760)
    rg.location = (-760, -400)
    h = b.math('ADD', fine, 0, grit, 'Distance', x=-560)
    bp = b.bump(h, 0, strength=0.22, dist=0.6, x=-380)
    p = b.principled(base=c3, baseo=0, roughn=rg, rougho=0, normal=bp, spec=0.42)
    b.out(p)
    return m


def plank_floor(name='floor_plank', light='B98A52', dark='6E4522',
                bw=0.135, bl=1.35, gap=0.0016):
    """Strip oak: a real plank grid with a staggered course offset, a per-board
    tone drawn from a white-noise hash of its cell id, and grain that runs
    along the board rather than across the room."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2400)
    sp0 = b.n('ShaderNodeSeparateXYZ', x=-2240)
    b.l(tc, 'Object', sp0, 'Vector')
    row = b.math('DIVIDE', sp0, 1, vb=bw, x=-2080)
    rowf = b.math('FLOOR', row, 0, x=-1940)
    # stagger: each course slides along by a hash of its own index
    rh = b.n('ShaderNodeTexWhiteNoise', x=-1800, noise_dimensions='1D')
    b.l(rowf, 0, rh, 'W')
    shift = b.math('MULTIPLY', rh, 'Value', vb=bl, x=-1660)
    xs = b.math('ADD', sp0, 0, shift, 0, x=-1520)
    colu = b.math('DIVIDE', xs, 0, vb=bl, x=-1380)
    cmb = b.n('ShaderNodeCombineXYZ', x=-1240)
    b.l(colu, 0, cmb, 'X')
    b.l(row, 0, cmb, 'Y')

    g, sp, cell = _lattice(b, (cmb, 0), x=-1080)
    rnd = _rand(b, cell, x=-560)

    # joints
    jx = b.math('GREATER_THAN', sp, 0, vb=0.5 - gap / bl, x=-560)
    jx.location = (-560, 300)
    jy = b.math('GREATER_THAN', sp, 1, vb=0.5 - gap / bw, x=-560)
    jy.location = (-560, 160)
    joint = b.math('MAXIMUM', jx, 0, jy, 0, x=-400)

    # grain: stretched noise along the board, plus a per-board tone shift
    gv = b.vmath('MULTIPLY', cmb, 0, vb=(1.0, 26.0, 1.0), x=-1080)
    gv.location = (-1080, -420)
    grain = b.noise((gv, 0), scale=7.0, detail=9.0, rough=0.68, dist=1.3, x=-900)
    grain.location = (-900, -420)
    fine = b.noise((gv, 0), scale=48.0, detail=4.0, rough=0.5, x=-900)
    fine.location = (-900, -600)

    lo, hi = srgb(dark), srgb(light)
    tone = b.mix(lo, 0, hi, 0, rnd, 'Value', x=-720)
    tone.location = (-720, -200)
    col = b.mix(tone, 0, lo, 0, grain, 'Fac', x=-540)
    col.location = (-540, -200)
    col.inputs['Factor'].default_value = 0.55
    col2 = b.mix(col, 0, (hi[0] * 1.1, hi[1] * 1.08, hi[2]), 0, fine, 'Fac',
                 x=-380, blend='OVERLAY')
    col2.location = (-380, -200)
    col2.inputs['Factor'].default_value = 0.12
    fin = b.mix(col2, 0, (0.01, 0.008, 0.006), 0, joint, 0, x=-220)

    rg = b.ramp(grain, 'Fac', [(0.2, (0.22,) * 3), (0.8, (0.44,) * 3)], x=-380,)
    rg.location = (-380, -760)
    rg2 = b.mix(rg, 0, (0.85, 0.85, 0.85), 0, joint, 0, x=-220)
    rg2.location = (-220, -760)

    hgt = b.math('SUBTRACT', grain, 0, joint, 0, x=-60)
    hgt.location = (-60, -560)
    bp = b.bump(hgt, 0, strength=0.16, dist=0.5, x=100)
    p = b.principled(base=fin, baseo=0, roughn=rg2, rougho=0, normal=bp,
                     spec=0.5, coat=0.18, x=280)
    b.out(p)
    return m


def dot_tile(name='tile_bay', field='EDE6D6', dot='2B2723', grout='C0B7A3',
             size=0.098, gw=0.05, dr=0.115):
    """The bay's floor: small off-white square tiles with a dark diamond set
    into every four-tile junction - the standard turn-of-the-century shopfront
    floor, and what the set photographs show under the window seating."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(1 / size,) * 3)
    g, sp, cell = _lattice(b, v, x=-1500)
    edge = b.math('MAXIMUM', sp, 0, sp, 1, x=-960)
    joint = b.math('GREATER_THAN', edge, 0, vb=0.5 - gw, x=-800)
    # the diamond sits on the corner: |gx| + |gy| measured from that corner
    ix = b.math('SUBTRACT', va=0.5, b=sp, bo=0, x=-960)
    ix.location = (-960, 260)
    iy = b.math('SUBTRACT', va=0.5, b=sp, bo=1, x=-960)
    iy.location = (-960, 120)
    dia = b.math('ADD', ix, 0, iy, 0, x=-800)
    dia.location = (-800, 200)
    dmask = b.math('LESS_THAN', dia, 0, vb=dr, x=-640)

    grime = b.noise(v, scale=3.2, detail=6.0, rough=0.6, x=-1500)
    grime.location = (-1500, -520)
    spot = b.noise(v, scale=40.0, detail=5.0, x=-1500)
    spot.location = (-1500, -700)

    f = srgb(field)
    c1 = b.mix(f, 0, (f[0] * 0.82, f[1] * 0.82, f[2] * 0.80), 0, grime, 'Fac',
               x=-480)
    c2 = b.mix(c1, 0, srgb(dot), 0, dmask, 0, x=-320)
    c3 = b.mix(c2, 0, srgb(grout), 0, joint, 0, x=-160)

    rg = b.mix((0.14, 0.14, 0.14), 0, (0.70, 0.70, 0.70), 0, joint, 0, x=-160)
    rg.location = (-160, -300)
    rg2 = b.mix(rg, 0, (0.34, 0.34, 0.34), 0, spot, 'Fac', x=0)
    rg2.location = (0, -300)
    rg2.inputs['Factor'].default_value = 0.25

    h = b.math('SUBTRACT', va=1.0, b=joint, bo=0, x=-160)
    h.location = (-160, -560)
    bp = b.bump(h, 0, strength=0.5, dist=0.0022, x=40)
    p = b.principled(base=c3, baseo=0, roughn=rg2, rougho=0, normal=bp,
                     spec=0.55, coat=0.22, x=220)
    b.out(p)
    return m


# ==================================================================== WALLS

def brick(name='brick', face='6E4030', face2='4A2C20', mortar='7E7466',
          bw=0.215, bh=0.068, mort=0.011, spread=1.0):
    """Common bond brick.  Object-space so the courses stay level whatever
    the wall's azimuth, with per-brick colour, a rough face and a mortar bed
    that sits back from it.

    Two things decide whether brick reads as brick or as wrapping paper, and
    neither is the brick colour.  The first is SPREAD: a real wall runs from
    near-black overburnt headers to pale buff, and mixing between two similar
    reds gives a flat printed field however good the bond is - so the
    per-brick random drives a four-stop ramp, not a two-colour blend.  The
    second is the mortar, which wants to be a shade off the brick and thin.
    A wide cream joint turns the wall into a white grid with red confetti in
    it, which is what the first pass looked like from across the room."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2400)
    proj = wall_proj(b, x=-2300)
    scl = b.vmath('DIVIDE', proj, 0, vb=(bw, bh, 1.0), x=-1000)
    scl.location = (-1000, 400)
    sp0 = b.n('ShaderNodeSeparateXYZ', x=-860, y=400)
    b.l(scl, 0, sp0, 'Vector')
    course = b.math('FLOOR', sp0, 1, x=-720)
    course.location = (-720, 460)
    half = b.math('MULTIPLY', course, 0, vb=0.5, x=-600)
    half.location = (-600, 460)
    xs = b.math('ADD', sp0, 0, half, 0, x=-470)
    xs.location = (-470, 460)
    cmb = b.n('ShaderNodeCombineXYZ', x=-340, y=400)
    b.l(xs, 0, cmb, 'X')
    b.l(sp0, 1, cmb, 'Y')

    g, sp, cell = _lattice(b, (cmb, 0), x=-200)
    rnd = _rand(b, cell, x=340, seed=3.0)
    jx = b.math('GREATER_THAN', sp, 0, vb=0.5 - mort / bw, x=340)
    jx.location = (340, 500)
    jy = b.math('GREATER_THAN', sp, 1, vb=0.5 - mort / bh, x=340)
    jy.location = (340, 360)
    joint = b.math('MAXIMUM', jx, 0, jy, 0, x=480)

    rough_n = b.noise((tc, 'Object'), scale=160.0, detail=8.0, rough=0.72, x=-1000)
    rough_n.location = (-1000, -520)
    blot = b.noise((tc, 'Object'), scale=9.0, detail=6.0, rough=0.6, x=-1000)
    blot.location = (-1000, -700)

    f1, f2 = srgb(face), srgb(face2)

    def _sh(c, k, warm=1.0):
        return tuple(min(1.0, v * k * (warm if i == 0 else 1.0))
                     for i, v in enumerate(c[:3])) + (1.0,)

    s = spread
    tone = b.ramp(rnd, 'Value', [
        (0.00, _sh(f2, 1.0 - 0.42 * s)),          # overburnt, nearly black
        (0.34, _sh(f2, 1.0)),
        (0.66, _sh(f1, 1.0)),
        (1.00, _sh(f1, 1.0 + 0.55 * s, 1.06)),    # a few pale buff ones
    ], x=620)
    tone2 = b.mix(tone, 0, (f2[0] * 0.7, f2[1] * 0.72, f2[2] * 0.7), 0,
                  blot, 'Fac', x=760)
    tone2.inputs['Factor'].default_value = 0.4
    tone3 = b.mix(tone2, 0, (f1[0] * 1.15, f1[1] * 1.1, f1[2] * 1.05), 0,
                  rough_n, 'Fac', x=900)
    tone3.inputs['Factor'].default_value = 0.22
    col = b.mix(tone3, 0, srgb(mortar), 0, joint, 0, x=1040)

    rg = b.mix((0.62, 0.62, 0.62), 0, (0.92, 0.92, 0.92), 0, joint, 0, x=1040)
    rg.location = (1040, -260)

    hh = b.math('MULTIPLY', rough_n, 0, vb=0.35, x=620)
    hh.location = (620, -560)
    hj = b.math('SUBTRACT', hh, 0, joint, 0, x=760)
    hj.location = (760, -560)
    bp = b.bump(hj, 0, strength=0.75, dist=0.010, x=900)
    p = b.principled(base=col, baseo=0, roughn=rg, rougho=0, normal=bp,
                     spec=0.28, x=1180)
    b.out(p)
    return m


def plaster(name, hexcol, rough=0.74, bump=0.35, scale=22.0, mottle=0.30):
    """Hand-floated lime plaster - a soft trowel texture plus a slow tonal
    wander, which is what keeps a big flat wall from going dead."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(scale,) * 3)
    n1 = b.noise(v, scale=2.4, detail=8.0, rough=0.62, x=-1400)
    n2 = b.noise(v, scale=17.0, detail=6.0, rough=0.5, x=-1400)
    n2.location = (-1400, -320)
    base = srgb(hexcol)
    dk = tuple(c * (1.0 - mottle) for c in base[:3])
    lt = tuple(min(1.0, c * (1.0 + mottle * 0.8)) for c in base[:3])
    c1 = b.mix(dk, 0, lt, 0, n1, 'Fac', x=-1100)
    c2 = b.mix(c1, 0, dk, 0, n2, 'Fac', x=-920)
    c2.inputs['Factor'].default_value = 0.22
    b.l(n2, 0, c2, 'Factor')
    h = b.math('ADD', n1, 0, n2, 0, x=-740)
    bp = b.bump(h, 0, strength=bump, dist=0.9, x=-560)
    rg = b.ramp(n2, 'Fac', [(0.2, (rough - 0.06,) * 3), (0.8, (rough + 0.06,) * 3)],
                x=-740)
    rg.location = (-740, -400)
    p = b.principled(base=c2, baseo=0, roughn=rg, rougho=0, normal=bp, spec=0.3)
    b.out(p)
    return m


def paint(name, hexcol, rough=0.34, sheen=0.0, bump=0.05, scale=90.0, coat=0.0):
    """Brushed oil paint on joinery: an almost-flat colour with a faint
    orange-peel and a directional brush drag."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(scale, scale * 0.22, scale))
    n = b.noise(v, scale=6.0, detail=6.0, rough=0.5, x=-1300)
    fine = b.noise(v, scale=48.0, detail=3.0, x=-1300)
    fine.location = (-1300, -300)
    base = srgb(hexcol)
    c = b.mix(tuple(x * 0.93 for x in base[:3]), 0,
              tuple(min(1.0, x * 1.06) for x in base[:3]), 0, n, 'Fac', x=-1000)
    rg = b.ramp(n, 'Fac', [(0.2, (rough - 0.05,) * 3), (0.85, (rough + 0.05,) * 3)],
                x=-1000)
    rg.location = (-1000, -400)
    h = b.math('ADD', n, 0, fine, 0, x=-800)
    bp = b.bump(h, 0, strength=bump, dist=1.0, x=-620)
    p = b.principled(base=c, baseo=0, roughn=rg, rougho=0, normal=bp,
                     spec=0.5, coat=coat, sheen=sheen, sheen_tint=base[:3])
    b.out(p)
    return m


def iron(name='iron_green', hexcol='17372B', rough=0.42):
    """Old cast iron under many coats of paint: the paint film is smooth but
    the casting under it is not, so the highlight ripples."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(50,) * 3)
    cast = b.noise(v, scale=8.0, detail=8.0, rough=0.72, x=-1300)
    pit = b.n('ShaderNodeTexVoronoi', x=-1300, y=-320, feature='F1',
              voronoi_dimensions='3D')
    pit.inputs['Scale'].default_value = 62.0
    b.l(v[0], v[1], pit, 'Vector')
    base = srgb(hexcol)
    c = b.mix(tuple(x * 0.8 for x in base[:3]), 0,
              tuple(min(1.0, x * 1.18) for x in base[:3]), 0, cast, 'Fac', x=-1000)
    rg = b.ramp(cast, 'Fac', [(0.15, (rough - 0.1,) * 3), (0.85, (rough + 0.12,) * 3)],
                x=-1000)
    rg.location = (-1000, -420)
    h = b.math('MULTIPLY_ADD', cast, 0, x=-820)
    h.inputs[1].default_value = 0.6
    b.l(pit, 'Distance', h, 2)
    bp = b.bump(h, 0, strength=0.3, dist=0.7, x=-640)
    p = b.principled(base=c, baseo=0, roughn=rg, rougho=0, normal=bp, spec=0.55)
    b.out(p)
    return m


def wood(name, light='9A6633', dark='4A2A12', ring=34.0, scale=1.0,
         rough=(0.24, 0.46), axis='Z', coat=0.22, bump=0.14):
    """Finished cabinet timber.  Rings are a distorted radial band pattern
    read in object space, so a turned leg and a flat rail cut from the same
    material still look like the same tree."""
    m = _mat(name)
    b = NB(m)
    sc = {'X': (scale, scale * ring, scale * ring),
          'Y': (scale * ring, scale, scale * ring),
          'Z': (scale * ring, scale * ring, scale)}[axis]
    v = _obj_vec(b, scale=sc)
    warp = b.noise(v, scale=1.1, detail=6.0, rough=0.6, x=-1500)
    wv = b.vmath('ADD', v[0], v[1], x=-1320)
    b.l(warp, 'Color', wv, 1)
    w2 = b.n('ShaderNodeTexWave', x=-1160, wave_type='RINGS',
             bands_direction={'X': 'X', 'Y': 'Y', 'Z': 'Z'}[axis],
             wave_profile='SIN')
    w2.inputs['Scale'].default_value = 1.0
    w2.inputs['Distortion'].default_value = 6.0
    w2.inputs['Detail'].default_value = 3.0
    b.l(wv, 0, w2, 'Vector')
    pore = b.noise(v, scale=ring * 6.0, detail=4.0, x=-1160)
    pore.location = (-1160, -360)
    lo, hi = srgb(dark), srgb(light)
    c1 = b.ramp(w2, 'Fac', [(0.0, lo), (0.42, hi), (0.58, hi), (1.0, lo)], x=-940)
    c2 = b.mix(c1, 0, lo, 0, pore, 'Fac', x=-760)
    c2.inputs['Factor'].default_value = 0.16
    rg = b.ramp(w2, 'Fac', [(0.1, (rough[1],) * 3), (0.9, (rough[0],) * 3)], x=-940)
    rg.location = (-940, -420)
    h = b.math('ADD', w2, 'Fac', pore, 0, x=-760)
    h.location = (-760, -600)
    bp = b.bump(h, 0, strength=bump, dist=0.5, x=-580)
    p = b.principled(base=c2, baseo=0, roughn=rg, rougho=0, normal=bp,
                     spec=0.5, coat=coat)
    b.out(p)
    return m


def marble(name='marble_counter', base='9DA396', vein='4C5A4A', vein2='D8DCCE',
           scale=2.4):
    """The counter's serpentine top - a green-grey marble with two vein
    families running at a shallow angle to each other."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(scale, scale * 0.55, scale))
    warp = b.noise(v, scale=1.6, detail=8.0, rough=0.62, dist=0.0, x=-1600)
    wv = b.vmath('ADD', v[0], v[1], x=-1420)
    sc = b.vmath('SCALE', warp, 'Color', x=-1540)
    sc.inputs['Scale'].default_value = 0.55
    b.l(sc, 0, wv, 1)
    n1 = b.n('ShaderNodeTexNoise', x=-1260, noise_dimensions='3D')
    n1.inputs['Scale'].default_value = 3.0
    n1.inputs['Detail'].default_value = 9.0
    n1.inputs['Roughness'].default_value = 0.55
    b.l(wv, 0, n1, 'Vector')
    v1 = b.ramp(n1, 'Fac', [(0.44, (0, 0, 0)), (0.50, (1, 1, 1)), (0.56, (0, 0, 0))],
                x=-1060)
    n2 = b.noise((wv, 0), scale=8.0, detail=7.0, rough=0.5, x=-1260)
    n2.location = (-1260, -360)
    v2 = b.ramp(n2, 'Fac', [(0.46, (0, 0, 0)), (0.5, (1, 1, 1)), (0.54, (0, 0, 0))],
                x=-1060)
    v2.location = (-1060, -360)
    fld = b.noise(v, scale=2.2, detail=6.0, x=-1260)
    fld.location = (-1260, -700)
    bs = srgb(base)
    c0 = b.mix(bs, 0, tuple(x * 0.78 for x in bs[:3]), 0, fld, 'Fac', x=-860)
    c1 = b.mix(c0, 0, srgb(vein), 0, v1, 'Color', x=-680)
    c2 = b.mix(c1, 0, srgb(vein2), 0, v2, 'Color', x=-500)
    c2.inputs['Factor'].default_value = 0.7
    rg = b.mix((0.10, 0.10, 0.10), 0, (0.22, 0.22, 0.22), 0, v1, 'Color', x=-500)
    rg.location = (-500, -420)
    bp = b.bump(v1, 'Color', strength=0.06, dist=0.4, x=-320)
    p = b.principled(base=c2, baseo=0, roughn=rg, rougho=0, normal=bp,
                     spec=0.6, coat=0.4)
    b.out(p)
    return m


def glass(name='glass_window', tint='EAF0EE', rough=0.02, alpha=0.04,
          ior=1.52):
    m = _mat(name)
    b = NB(m)
    m.use_backface_culling = False
    # EEVEE will not refract through an alpha-BLENDED surface: it composites
    # it and leaves the transmission to a rough approximation, which turns
    # every piece of glass in the room into white fog - the storefront read as
    # frosted, the sweet jars as white plastic and the cake domes as grey
    # bowls.  Refraction in EEVEE Next is a ray-traced effect and it needs the
    # opaque (dithered) pipeline plus the raytrace flag, so both go on here
    # rather than being set per object afterwards.  Cycles ignores all three.
    for attr, val in (("surface_render_method", 'DITHERED'),
                      ("use_raytrace_refraction", True),
                      ("use_transparent_shadow", True),
                      ("thickness_mode", 'SLAB')):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    try:
        m.refraction_depth = 0.0
    except Exception:
        pass
    # Cylinder glass has a faint ripple in it.  The first version drove the
    # bump 600 mm deep over a quarter-metre noise, which is not a ripple - it
    # is a sheet of frosted bathroom glass, and it blotched out every window
    # in the storefront.
    v = _obj_vec(b, scale=(3.0,) * 3)
    rip = b.noise(v, scale=9.0, detail=3.0, rough=0.4, x=-1200)
    bp = b.bump(rip, 0, strength=0.030, dist=0.012, x=-900)
    p = b.principled(color=srgb(tint)[:3], rough=rough, transm=1.0, ior=ior,
                     normal=bp, spec=0.5)
    p.inputs['Alpha'].default_value = 1.0
    b.out(p)
    return m


def emissive(name, hexcol, strength=8.0):
    m = _mat(name)
    b = NB(m)
    e = b.n('ShaderNodeEmission', x=-200)
    e.inputs['Color'].default_value = srgb(hexcol)
    e.inputs['Strength'].default_value = strength
    b.out(e)
    return m


def lampshade(name, hexcol='F4EADA', glow='FFD9A6', strength=9.0, rough=0.30,
              transm=0.22):
    """A shade with a lamp burning inside it.

    Not a bare Emission node: a lit opal globe is still a solid object with a
    highlight on it and a rim that goes darker where it turns away, and an
    emitter alone throws all of that away and renders as a flat white
    cut-out.  This is the shade's own dielectric surface with the glow added
    on top, plus a little transmission so the thin glass reads as thin.

    `strength` is what makes the fixture look switched on when it carries no
    light data of its own - which, under the lighting rule, is most of
    them."""
    m = _mat(name)
    b = NB(m)
    # brighter through the middle of the shade than at its edge, so a globe
    # keeps its roundness instead of blowing out to an even disc
    fr = b.n('ShaderNodeFresnel', x=-600)
    fr.inputs['IOR'].default_value = 1.42
    ramp = b.n('ShaderNodeValToRGB', x=-420)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*srgb(glow)[:3], 1.0)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = tuple(c * 0.30 for c in srgb(glow)[:3]) + (1.0,)
    b.l(fr, 0, ramp, 'Fac')
    p = b.principled(color=srgb(hexcol)[:3], rough=rough, transm=transm,
                     emis=ramp, emis_str=strength, coat=0.25)
    b.out(p)
    return m


def flat(name, hexcol, rough=0.6):
    m = _mat(name)
    b = NB(m)
    p = b.principled(color=srgb(hexcol)[:3], rough=rough)
    b.out(p)
    return m


# =================================================================== TEXTILES
#
# Everything soft in the room is one of four weaves, and each is built the
# same way: a tiled cell, a motif drawn inside it by distance fields rather
# than by an image, and a bump that follows the *weave* and not the motif -
# real cloth is textured by its threads, the pattern is only dyed onto them.

def _weave(b, vec, scale=340.0, x=-1300, aniso=1.0):
    """The thread grid itself.  Two crossed sine sets at right angles, one
    stretched, so warp and weft read differently under a raking light."""
    sp = b.n('ShaderNodeSeparateXYZ', x=x)
    b.l(vec[0], vec[1], sp, 'Vector')
    wu = b.math('MULTIPLY', sp, 0, vb=scale * math.tau, x=x + 160)
    wv = b.math('MULTIPLY', sp, 1, vb=scale * math.tau / aniso, x=x + 160)
    wv.location = (x + 160, -220)
    su = b.math('SINE', wu, 0, x=x + 320)
    sv = b.math('SINE', wv, 0, x=x + 320)
    sv.location = (x + 320, -220)
    return b.math('ADD', su, 0, sv, 0, x=x + 480)


def _cell_uv(b, vec, x=-1500):
    """Per-cell coordinates with a half-drop on odd rows and the x mirrored
    about the cell centre - the two things that make a repeat read as a
    designed pattern rather than as wallpaper."""
    sp = b.n('ShaderNodeSeparateXYZ', x=x)
    b.l(vec[0], vec[1], sp, 'Vector')
    row = b.math('FLOOR', sp, 1, x=x + 160)
    half = b.math('MULTIPLY', row, 0, vb=0.5, x=x + 300)
    drop = b.math('ADD', sp, 0, half, 0, x=x + 440)
    fu = b.math('FRACT', drop, 0, x=x + 580)
    fv = b.math('FRACT', sp, 1, x=x + 580)
    fv.location = (x + 580, -220)
    cu = b.math('SUBTRACT', fu, 0, vb=0.5, x=x + 720)
    cv = b.math('SUBTRACT', fv, 0, vb=0.5, x=x + 720)
    cv.location = (x + 720, -220)
    au = b.math('ABSOLUTE', cu, 0, x=x + 860)          # mirror about the axis
    return au, cv, cu


def _ogee(b, au, cv, x=-500, w=0.34, h=0.42):
    """The pointed-arch lattice a damask is built on.  |u| against a cosine
    of v gives the lens shape; two of them, offset, give the ogee."""
    cw = b.math('MULTIPLY', cv, 0, vb=math.tau, x=x)
    cc = b.math('COSINE', cw, 0, x=x + 140)
    amp = b.math('MULTIPLY', cc, 0, vb=w, x=x + 280)
    lim = b.math('ADD', amp, 0, vb=h, x=x + 420)
    return b.math('SUBTRACT', lim, 0, au, 0, x=x + 560)


def _ell(b, au, cv, cx, cy, rx, ry, x=-400, y=0):
    """Signed inside-ness of an ellipse in cell coordinates: >0 within.
    Motifs are assembled by taking the maximum of several of these, which is
    a union - and because `au` is already mirrored, every lobe placed off the
    axis is drawn on both sides for free."""
    du = b.math('SUBTRACT', au, 0, vb=cx, x=x); du.location = (x, y)
    dv = b.math('SUBTRACT', cv, 0, vb=cy, x=x); dv.location = (x, y - 130)
    nu = b.math('DIVIDE', du, 0, vb=rx, x=x + 130); nu.location = (x + 130, y)
    nv = b.math('DIVIDE', dv, 0, vb=ry, x=x + 130); nv.location = (x + 130, y - 130)
    u2 = b.math('MULTIPLY', nu, 0, nu, 0, x=x + 260); u2.location = (x + 260, y)
    v2 = b.math('MULTIPLY', nv, 0, nv, 0, x=x + 260); v2.location = (x + 260, y - 130)
    s = b.math('ADD', u2, 0, v2, 0, x=x + 390); s.location = (x + 390, y - 65)
    r = b.math('SQRT', s, 0, x=x + 520); r.location = (x + 520, y - 65)
    o = b.math('SUBTRACT', va=1.0, b=r, bo=0, x=x + 650); o.location = (x + 650, y - 65)
    return o


def _lobe(b, au, cv, cx, cy, rx, ry, rot=0.0, p=1.35, x=-400, y=0):
    """One petal of an ornament: a rotated superellipse, >0 inside.

    An ellipse - exponent 2 - is a circle stretched, and six of them unioned
    make a flower-power print, which is exactly what the first damask came
    out as.  Every element of a real damask is POINTED: leaves come to a tip,
    the pomegranate has a nose, the scrolls taper.  An exponent below 2 is
    what produces that tip, and being able to turn each one lets the leaves
    sweep off the stem instead of sitting square to it."""
    du = b.math('SUBTRACT', au, 0, vb=cx, x=x); du.location = (x, y)
    dv = b.math('SUBTRACT', cv, 0, vb=cy, x=x); dv.location = (x, y - 120)
    if rot:
        c, s = math.cos(rot), math.sin(rot)
        a1 = b.math('MULTIPLY', du, 0, vb=c, x=x + 120); a1.location = (x + 120, y + 60)
        a2 = b.math('MULTIPLY', dv, 0, vb=s, x=x + 120); a2.location = (x + 120, y - 60)
        b1 = b.math('MULTIPLY', du, 0, vb=-s, x=x + 120); b1.location = (x + 120, y - 180)
        b2 = b.math('MULTIPLY', dv, 0, vb=c, x=x + 120); b2.location = (x + 120, y - 300)
        du = b.math('ADD', a1, 0, a2, 0, x=x + 250); du.location = (x + 250, y)
        dv = b.math('ADD', b1, 0, b2, 0, x=x + 250); dv.location = (x + 250, y - 240)
        x += 250
    nu = b.math('DIVIDE', du, 0, vb=rx, x=x + 130); nu.location = (x + 130, y)
    nv = b.math('DIVIDE', dv, 0, vb=ry, x=x + 130); nv.location = (x + 130, y - 130)
    au_ = b.math('ABSOLUTE', nu, 0, x=x + 260); au_.location = (x + 260, y)
    av_ = b.math('ABSOLUTE', nv, 0, x=x + 260); av_.location = (x + 260, y - 130)
    up = b.math('POWER', au_, 0, vb=p, x=x + 390); up.location = (x + 390, y)
    vp = b.math('POWER', av_, 0, vb=p, x=x + 390); vp.location = (x + 390, y - 130)
    s_ = b.math('ADD', up, 0, vp, 0, x=x + 520); s_.location = (x + 520, y - 65)
    r_ = b.math('POWER', s_, 0, vb=1.0 / p, x=x + 650); r_.location = (x + 650, y - 65)
    o = b.math('SUBTRACT', va=1.0, b=r_, bo=0, x=x + 780); o.location = (x + 780, y - 65)
    return o


# The ornament, as a list of (cx, cy, rx, ry, rot, exponent) in cell
# coordinates - `au` is already mirrored about the cell's axis, so anything
# with cx > 0 is drawn on both sides for nothing.  This is a pomegranate
# palmette: a pointed body on a stem, a calyx and crown above it, two pairs
# of scrolled leaves sweeping off the sides, and a bud at each shoulder.
_DAMASK_LOBES = [
    (0.000, -0.115, 0.132, 0.230, 0.00, 1.30),    # body
    (0.000,  0.150, 0.088, 0.092, 0.00, 1.55),    # calyx
    (0.082,  0.262, 0.056, 0.108, -0.48, 1.28),   # crown petals
    (0.000,  0.348, 0.038, 0.080, 0.00, 1.20),    # crown tip
    (0.244,  0.035, 0.172, 0.048, 0.56, 1.24),    # upper leaves
    (0.204, -0.238, 0.146, 0.043, -0.62, 1.24),   # lower leaves
    (0.372,  0.205, 0.042, 0.068, 0.42, 1.30),    # shoulder buds
    (0.000, -0.398, 0.021, 0.108, 0.00, 1.70),    # stem
]


def damask(name, ground='7A1418', motif='C08A34', sheen_c='E0B15E',
           scale=(4.2, 3.0), rough=0.58, bump=0.22):
    """Woven damask: a two-tone jacquard where the motif is the *same* yarn
    caught at a different angle, so it changes with the light instead of
    sitting on top like paint.

    The motif is drawn, not sampled: a pomegranate palmette assembled out of
    pointed superellipses (see `_lobe`), mirrored about the cell axis and
    repeated on a half-drop.

    Two things make it read as damask rather than as a print.  The lobes are
    pointed, so leaves taper instead of ending in a circle.  And the figure
    carries a fine CONTOUR just inside its own edge, in the ground colour -
    that line is what a jacquard produces where the float turns back into the
    weave, and without it a two-colour figure on a plain ground is a stencil
    however good its silhouette is."""
    m = _mat(name)
    b = NB(m)
    v = _tri_vec(b, scale)
    au, cv, cu = _cell_uv(b, v)
    lobes = [_lobe(b, au, cv, *spec, x=-380, y=560 - i * 420)
             for i, spec in enumerate(_DAMASK_LOBES)]
    # The ogee band that ties one repeat to the next.  Without it the
    # palmettes float on the ground as separate stencilled figures; damask is
    # a LATTICE, and the ornament sits in it rather than on it.
    og = _ogee(b, au, cv, x=-380, w=0.30, h=0.335)
    og.location = (280, 900)
    oga = b.math('ABSOLUTE', og, 0, x=420); oga.location = (420, 900)
    ogb = b.math('SUBTRACT', va=0.052, b=oga, bo=0, x=560)
    ogb.location = (560, 900)
    lobes.append(ogb)
    sil = lobes[0]
    for i, o in enumerate(lobes[1:]):
        sil = b.math('MAXIMUM', sil, 0, o, 0, x=900 + i * 130)
        sil.location = (900 + i * 130, 200)
    # break the outline on the thread grid
    burr = b.noise(v, scale=90.0, detail=4.0, rough=0.6, x=-1300)
    burr.location = (-1300, -1100)
    bo = b.math('MULTIPLY_ADD', burr, 'Fac', vb=0.055, x=-1120)
    bo.location = (-1120, -1100)
    bo.inputs[2].default_value = -0.0275
    pat = b.math('ADD', sil, 0, bo, 0, x=1900)
    pat.location = (1900, 200)
    edge = b.ramp(pat, 0, [(0.0, (0, 0, 0)), (0.020, (1, 1, 1))], x=2040)
    edge.location = (2040, 200)
    # the contour: inside the silhouette but outside a shrunken copy of it
    core = b.ramp(pat, 0, [(0.115, (0, 0, 0)), (0.150, (1, 1, 1))], x=2040)
    core.location = (2040, -80)
    band = b.math('SUBTRACT', edge, 'Color', core, 'Color', x=2180, clamp=True)
    band.location = (2180, -80)
    col = b.mix(srgb(ground)[:3], 0, srgb(motif)[:3], 0, edge, 0, x=2320)
    col.location = (2320, 200)
    gd = tuple(c * 0.46 for c in srgb(ground)[:3])
    col = b.mix(col, 0, gd, 0, band, 0, x=2460)
    col.location = (2460, 200)
    # weave bump, plus a slight relief on the motif itself (jacquard floats)
    w = _weave(b, v, scale=150.0, x=-1300, aniso=1.35)
    rel = b.math('MULTIPLY', edge, 'Color', vb=0.35, x=2320)
    rel.location = (2320, -400)
    hgt = b.math('ADD', w, 0, rel, 0, x=2460)
    hgt.location = (2460, -400)
    bmp = b.bump(hgt, 0, strength=bump, dist=0.02, x=2600)
    rr = b.fmix(rough, 0, rough - 0.16, 0, edge, 'Color', x=2320)
    rr.location = (2320, -680)
    p = b.principled(base=col, baseo=0, rough=rough, roughn=rr, rougho=0,
                     normal=bmp, sheen=0.42, sheen_tint=srgb(sheen_c)[:3],
                     spec=0.32, x=2760)
    b.out(p)
    return m


def velvet(name, hexcol='C4642A', rough=0.44, pile=0.9):
    """Cut-pile velvet.  What makes velvet velvet is that the pile leans, so
    the colour depends on the angle you catch it at: dark straight on, bright
    at a graze.  Layering weight on the Fresnel and running the sheen hot is
    what gives the hero couch its glow along the crest and the arm rolls."""
    m = _mat(name)
    b = NB(m)
    base = srgb(hexcol)[:3]
    # Scale first, because it is the whole difference between velvet and
    # vinyl.  At an object scale of 90 the fibre noise ran at 5400 cells per
    # metre - four times finer than a render pixel at any distance you would
    # ever see this couch from - so it averaged to a constant and the couch
    # came out as a smooth plastic shell.  A cut pile reads at about 2 mm.
    v = _obj_vec(b, scale=(9.0, 9.0, 9.0))
    fib = b.noise(v, scale=60.0, detail=8.0, rough=0.72, x=-1500)
    crush = b.noise(_obj_vec(b, scale=(7.0, 7.0, 7.0)), scale=3.2, detail=6.0,
                    rough=0.6, x=-1500)
    crush.location = (-1500, -340)
    # nap sheen: brightest where the surface turns away
    lw = b.n('ShaderNodeLayerWeight', x=-1100, y=320)
    lw.inputs['Blend'].default_value = 0.34
    nap = b.math('POWER', lw, 'Facing', vb=1.5, x=-940)
    nap.location = (-940, 320)
    lift = b.math('MULTIPLY', nap, 0, vb=pile, x=-800)
    lift.location = (-800, 320)
    # Crushed patches read a shade lighter, as the pile there lies flat -
    # but only just.  At 0.40 the crush was a 40 % tonal swing over a 45 mm
    # cell on top of the tufting's own shading, and the hero couch came out
    # looking stained rather than napped.
    cm = b.math('MULTIPLY', crush, 'Fac', vb=0.16, x=-1180)
    cm.location = (-1180, -340)
    # and the fibre goes into the COLOUR, not only into the roughness.  A
    # 0.1 wobble on roughness is invisible on a matte cloth; what tells the
    # eye it is looking at pile rather than at hide is that the tone itself
    # is broken up at thread scale.
    fm = b.math('MULTIPLY_ADD', fib, 'Fac', vb=0.30, x=-1180)
    fm.location = (-1180, -520)
    fm.inputs[2].default_value = -0.15
    tone = b.math('ADD', lift, 0, cm, 0, x=-780)
    tone = b.math('ADD', tone, 0, fm, 0, x=-640)
    # `hi` is the pile catching the light, not a different colour: at 1.62x
    # plus a lift every red velvet in the room averaged out to salmon, and
    # the club chairs read as blocks of foam rather than as upholstery.
    # `lo` is not a shadow colour - the renderer does the shadows.  It is how
    # dark the pile goes when it is pointing straight at you, and at 0.40 the
    # bottom of every tuft went to a muddy brown that read as a stain on the
    # gold.  In main_couch.webp the valleys are a deep amber, not a dirt mark.
    lo = tuple(c * 0.60 for c in base)
    hi = tuple(min(1.0, c * 1.30 + 0.02) for c in base)
    col = b.mix(lo, 0, hi, 0, tone, 0, x=-460)
    rr = b.math('MULTIPLY_ADD', fib, 'Fac', vb=0.16, x=-460)
    rr.location = (-460, -340)
    rr.inputs[2].default_value = rough - 0.08
    bmp = b.bump(fib, 'Fac', strength=0.32, dist=0.0035, x=-300)
    p = b.principled(base=col, baseo=0, rough=rough, roughn=rr, rougho=0,
                     normal=bmp, sheen=0.85, sheen_tint=hi, spec=0.24, x=0)
    b.out(p)
    return m


def tapestry(name, ground='24201A', a='B04A2E', bcol='55663E', c='D8B45C',
             scale=7.0):
    """Needlepoint: the floral seats on the bar stools and the wooden stools.
    Coarse enough that the stitch grid itself is the texture, with the colours
    quantised to it - a smooth gradient would give the game away."""
    m = _mat(name)
    b = NB(m)
    v = _tri_vec(b, (scale, scale))
    # quantise to the stitch grid so every colour change lands on a thread
    grid = b.vmath('MULTIPLY', v[0], v[1], vb=(30.0, 30.0, 30.0), x=-1900)
    sn = b.vmath('SNAP', grid, 0, vb=(1.0, 1.0, 1.0), x=-1760)
    dn = b.vmath('DIVIDE', sn, 0, vb=(30.0, 30.0, 30.0), x=-1620)
    # Big blooms first.  The earlier version layered three fine noises and read
    # as brown static from a metre away: on a 380 mm stool seat the flowers
    # have to be 60-80 mm across to survive, which means ONE dominant cell
    # scale with hard colour steps, not a stack of octaves.
    vor = b.n('ShaderNodeTexVoronoi', x=-1460, feature='F1',
              voronoi_dimensions='3D')
    vor.inputs['Scale'].default_value = 2.6
    b.l(dn, 0, vor, 'Vector')
    warp = b.noise((dn, 0), scale=4.0, detail=4.0, rough=0.55, x=-1460)
    warp.location = (-1460, -420)
    # petal rings: distance banded, so each bloom has a heart and an outline
    bloom = b.ramp(vor, 'Distance',
                   [(0.00, srgb(c)[:3]), (0.10, srgb(a)[:3]),
                    (0.20, srgb(bcol)[:3]), (0.30, srgb(ground)[:3])],
                   x=-1240, interp='CONSTANT')
    # which colour a given bloom takes, so the seat is not all one flower
    tint = b.ramp(vor, 'Color', [(0.30, srgb(a)[:3]), (0.55, srgb(c)[:3]),
                                 (0.80, srgb(bcol)[:3])],
                  x=-1240, interp='CONSTANT')
    tint.location = (-1240, -300)
    heart = b.ramp(vor, 'Distance', [(0.16, (1, 1, 1)), (0.18, (0, 0, 0))],
                   x=-1240, interp='CONSTANT')
    heart.location = (-1240, -620)
    col = b.mix(bloom, 0, tint, 0, heart, 0, x=-1000)
    # trailing foliage between the blooms
    leaf = b.ramp(warp, 'Fac', [(0.44, (0, 0, 0)), (0.50, (1, 1, 1))],
                  x=-1240, interp='CONSTANT')
    leaf.location = (-1240, -900)
    gap = b.math('SUBTRACT', va=1.0, b=heart, bo=0, x=-1000)
    gap.location = (-1000, -900)
    lm = b.math('MULTIPLY', leaf, 0, gap, 0, x=-860)
    lm.location = (-860, -900)
    col2 = b.mix(col, 0, srgb(bcol)[:3], 0, lm, 0, x=-680)
    col3 = b.mix(col2, 0, srgb(ground)[:3], 0, warp, 'Fac', x=-500, factor=0.22)
    # the stitches themselves: crossed diagonals, coarse
    w = _weave(b, v, scale=15.0, x=-1900, aniso=1.0)
    w.location = (-1900, -1200)
    bmp = b.bump(w, 0, strength=0.55, dist=0.012, x=-320)
    p = b.principled(base=col3, baseo=0, rough=0.78, normal=bmp, sheen=0.30,
                     sheen_tint=srgb(c)[:3], spec=0.2, x=0)
    b.out(p)
    return m


def persian(name, ground='82291B', border='1D2C46', motif='CFBC94',
            accent='2C4A36', dark='2A100C', scale=1.0, wd=(1.0, 1.0),
            phase=0.0):
    """A Serapi-type carpet, drawn rather than tiled.  Object coordinates are
    normalised to the rug's own extent, so one graph serves every rug in the
    room at its own size: concentric guard stripes and a main border round a
    field, a stepped medallion on the centre line, and four-fold symmetric
    ornament everywhere else.  The pile is a separate, much finer bump - a
    carpet is rough at thread scale and smooth at pattern scale."""
    m = _mat(name)
    b = NB(m)
    tc = b.n('ShaderNodeTexCoord', x=-2200)
    mp = b.mapping(tc, 'Object', scale=(2.0 / wd[0], 2.0 / wd[1], 1.0),
                   x=-2040)
    sp = b.n('ShaderNodeSeparateXYZ', x=-1900)
    b.l(mp, 0, sp, 'Vector')
    au = b.math('ABSOLUTE', sp, 0, x=-1760)
    av = b.math('ABSOLUTE', sp, 1, x=-1760)
    av.location = (-1760, -240)
    # d = chebyshev distance to the edge: concentric rectangles for free
    d = b.math('MAXIMUM', au, 0, av, 0, x=-1620)
    # the ornament vector: mirrored, so both halves of the rug match
    orn = b.n('ShaderNodeCombineXYZ', x=-1620, y=-420)
    b.l(au, 0, orn, 'X'); b.l(av, 0, orn, 'Y')
    vor = b.n('ShaderNodeTexVoronoi', x=-1440, y=-700, feature='F1',
              voronoi_dimensions='2D')
    vor.inputs['Scale'].default_value = 24.0
    b.l(orn, 0, vor, 'Vector')

    # The field.  A carpet's ground is not noise: it is a small ornament
    # repeated on a close lattice, and the whole difference between a Serapi
    # and a stain is that the repeat is REGULAR and FINE.  Driving the field
    # off one noise through a stepped ramp gave patches of green and cream
    # the size of a dinner plate - the right colours in the wrong shapes,
    # which reads as a printed throw rather than as a knotted carpet.
    #
    # So: a rosette on a 165 mm cell, drawn in world space so every rug in
    # the room shares the knot count instead of stretching its pattern to
    # its own size, with the cell's own random picking which of the four
    # ornament colours it is worked in.
    cellsz = 0.150
    # `phase` slides the lattice, so five rugs sharing one graph are not five
    # prints of the same carpet: the ornament lands on a different part of
    # each and the per-cell colour random reshuffles with it.
    fv = _obj_vec(b, scale=(1.0 / cellsz, 1.0 / cellsz, 1.0 / cellsz),
                  loc=(phase, phase * 0.63, phase * 0.31))
    fau, fcv, fcu = _cell_uv(b, fv)
    petals = [
        (0.000, 0.000, 0.190, 0.190, 0.00, 1.15),     # heart
        (0.000, 0.300, 0.082, 0.140, 0.00, 1.10),     # north point
        (0.000, -0.300, 0.082, 0.140, 0.00, 1.10),    # south point
        (0.320, 0.000, 0.140, 0.082, 0.00, 1.10),     # east/west points
        (0.245, 0.245, 0.078, 0.078, 0.79, 1.20),     # corner buds
        (0.245, -0.245, 0.078, 0.078, -0.79, 1.20),
    ]
    lb = [_lobe(b, fau, fcv, *s, x=-2600, y=1400 - i * 400)
          for i, s in enumerate(petals)]
    ros = lb[0]
    for i, o in enumerate(lb[1:]):
        ros = b.math('MAXIMUM', ros, 0, o, 0, x=-1100 + i * 120)
        ros.location = (-1100 + i * 120, 1400)
    # which colour this cell's rosette is worked in
    _g, _sp, fcell = _lattice(b, fv, x=-2600)
    frnd = _rand(b, fcell, x=-2300, seed=11.0)
    frnd.location = (-2300, 900)
    fcol = b.ramp(frnd, 'Value',
                  [(0.00, srgb(motif)[:3]), (0.34, srgb(border)[:3]),
                   (0.62, srgb(accent)[:3]), (0.84, srgb(dark)[:3])],
                  x=-2140, interp='CONSTANT')
    fcol.location = (-2140, 900)
    # a fine outline in the dark yarn, the way a knotted motif is fenced
    rin = b.ramp(ros, 0, [(0.0, (0, 0, 0)), (0.02, (1, 1, 1))], x=-560)
    rin.location = (-560, 1400)
    rcore = b.ramp(ros, 0, [(0.16, (0, 0, 0)), (0.20, (1, 1, 1))], x=-560)
    rcore.location = (-560, 1200)
    f1 = b.mix(srgb(ground)[:3], 0, srgb(dark)[:3], 0, rin, 'Color', x=-400)
    f1.location = (-400, 1400)
    f1 = b.mix(f1, 0, fcol, 0, rcore, 'Color', x=-260)
    f1.location = (-260, 1400)
    pal = b.ramp(vor, 'Distance', [(0.0, (1, 1, 1)), (0.07, (0, 0, 0))],
                 x=-1240)
    pal.location = (-1240, -700)
    # a faint abrash - the tonal banding a hand-dyed ground always has
    ab = b.noise((orn, 0), scale=3.2, detail=4.0, rough=0.5, x=-1440)
    ab.location = (-1440, -420)
    field = b.mix(f1, 0, tuple(c * 0.76 for c in srgb(ground)[:3]), 0,
                  ab, 'Fac', x=-1040, factor=0.30)
    # the central medallion, on an elliptical distance
    su = b.math('MULTIPLY', sp, 0, vb=2.9, x=-1900)
    su.location = (-1900, -900)
    sv = b.math('MULTIPLY', sp, 1, vb=1.75, x=-1900)
    sv.location = (-1900, -1040)
    su2 = b.math('MULTIPLY', su, 0, su, 0, x=-1760, )
    su2.location = (-1760, -900)
    sv2 = b.math('MULTIPLY', sv, 0, sv, 0, x=-1760)
    sv2.location = (-1760, -1040)
    e2 = b.math('ADD', su2, 0, sv2, 0, x=-1620)
    e2.location = (-1620, -960)
    ell = b.math('SQRT', e2, 0, x=-1480)
    ell.location = (-1480, -960)
    # notch the medallion edge so it is stepped, not a smooth oval
    ang = b.math('ARCTAN2', sp, 1, sp, 0, x=-1760)
    ang.location = (-1760, -1200)
    a8 = b.math('MULTIPLY', ang, 0, vb=8.0, x=-1620)
    a8.location = (-1620, -1200)
    ca = b.math('COSINE', a8, 0, x=-1480)
    ca.location = (-1480, -1200)
    notch = b.math('MULTIPLY_ADD', ca, 0, vb=0.055, x=-1340)
    notch.location = (-1340, -1200)
    notch.inputs[2].default_value = 0.60
    med = b.math('SUBTRACT', notch, 0, ell, 0, x=-1200)
    med.location = (-1200, -1080)
    medr = b.ramp(med, 0, [(0.0, (0, 0, 0)), (0.02, (1, 1, 1))], x=-1040)
    medr.location = (-1040, -1080)
    medc = b.mix(srgb(border)[:3], 0, srgb(motif)[:3], 0, pal, 0, x=-880)
    medc.location = (-880, -1080)
    body = b.mix(field, 0, medc, 0, medr, 0, x=-700)
    # borders: guard / main / guard, then the fringed selvedge
    g1 = b.ramp(d, 0, [(0.848, (0, 0, 0)), (0.858, (1, 1, 1))], x=-1240,
                interp='CONSTANT')
    g1.location = (-1240, 200)
    g2 = b.ramp(d, 0, [(0.952, (0, 0, 0)), (0.962, (1, 1, 1))], x=-1240,
                interp='CONSTANT')
    g2.location = (-1240, 380)
    band = b.math('SUBTRACT', g1, 0, g2, 0, x=-1040)
    band.location = (-1040, 300)
    bcol = b.mix(srgb(border)[:3], 0, srgb(motif)[:3], 0, pal, 0, x=-880)
    bcol.location = (-880, 300)
    withb = b.mix(body, 0, bcol, 0, band, 0, x=-520)
    edge = b.mix(withb, 0, srgb(dark)[:3], 0, g2, 0, x=-360)
    # pile
    fine = b.noise(_obj_vec(b, scale=(scale, scale, scale)), scale=260.0,
                   detail=6.0, rough=0.7, x=-1440)
    fine.location = (-1440, 620)
    bmp = b.bump(fine, 'Fac', strength=0.55, dist=0.010, x=-200)
    knot = b.noise(_obj_vec(b, scale=(scale, scale, scale)), scale=95.0,
                   detail=3.0, rough=0.5, x=-1440)
    knot.location = (-1440, 800)
    edge = b.mix(edge, 0, (0.0, 0.0, 0.0), 0, knot, 'Fac', blend='OVERLAY',
                 x=-280, factor=0.22)
    edge.location = (-280, 300)
    rr = b.fmix(0.92, 0, 0.80, 0, fine, "Fac", x=-360)
    rr.location = (-360, 620)
    p = b.principled(base=edge, baseo=0, rough=0.9, roughn=rr, rougho=0,
                     normal=bmp, sheen=0.22, sheen_tint=srgb(motif)[:3],
                     spec=0.16, x=0)
    b.out(p)
    return m


def leather(name, hexcol='7E7360', rough=0.46, worn=0.35):
    """Soft aged leather for the recliner: a coarse pebble grain, creases
    where it has been sat in, and a sheen that survives both."""
    m = _mat(name)
    b = NB(m)
    base = srgb(hexcol)[:3]
    # Scales are in cells-per-metre, and they matter more here than the
    # colour does.  The first version ran the pebble grain at 1600/m and the
    # creases at one every 80 mm, which is invisible grain over a swirl the
    # size of a hand: the chair came out looking like polished marble.  Real
    # upholstery leather is a 3-4 mm pebble under a 20 mm crease.
    v = _obj_vec(b, scale=(8.0, 8.0, 8.0))
    cellv = b.n('ShaderNodeTexVoronoi', x=-1500, feature='DISTANCE_TO_EDGE',
                voronoi_dimensions='3D')
    cellv.inputs['Scale'].default_value = 30.0
    b.l(v[0], v[1], cellv, 'Vector')
    fine = b.noise(v, scale=180.0, detail=6.0, rough=0.7, x=-1500)
    fine.location = (-1500, -320)
    crease = b.noise(_obj_vec(b, scale=(14.0, 14.0, 14.0)), scale=4.0,
                     detail=7.0, rough=0.72, dist=1.1, x=-1500)
    crease.location = (-1500, -640)
    grain = b.ramp(cellv, 'Distance', [(0.0, (0, 0, 0)), (0.12, (1, 1, 1))],
                   x=-1300)
    h1 = b.math('MULTIPLY', grain, 0, vb=0.7, x=-1120)
    h2 = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.3, x=-1120)
    h2.location = (-1120, -320)
    h2.inputs[2].default_value = 0.0
    hs = b.math('ADD', h1, 0, h2, 0, x=-960)
    cr = b.ramp(crease, 'Fac', [(0.40, (0, 0, 0)), (0.52, (1, 1, 1))], x=-1120)
    cr.location = (-1120, -640)
    hgt = b.mix(hs, 0, srgb('000000')[:3], 0, cr, 0, x=-800, blend='MULTIPLY')
    # Colour: worn lighter on the high grain, darker in the creases - but
    # only just.  Run at 0.62/1.28 the pebble is a two-to-one colour swing
    # per 4 mm cell, and the chair rendered as speckled granite: on real
    # upholstery hide the grain is almost entirely a BUMP and the colour
    # under it is near enough uniform.
    lo = tuple(c * 0.90 for c in base)
    hi = tuple(min(1.0, c * 1.09 + 0.01) for c in base)
    col = b.mix(lo, 0, hi, 0, grain, 0, x=-800, factor=0.5)
    col.location = (-800, 240)
    col2 = b.mix(col, 0, lo, 0, cr, 0, x=-620)
    bmp = b.bump(hgt, 0, strength=0.52, dist=0.010, x=-440)
    rr = b.fmix(rough + 0.16, 0, rough - 0.10, 0, grain, 0, x=-620)
    rr.location = (-620, -320)
    p = b.principled(base=col2, baseo=0, rough=rough, roughn=rr, rougho=0,
                     normal=bmp, sheen=0.22, sheen_tint=hi, spec=0.4, x=0)
    b.out(p)
    return m


# ===================================================================== METALS

def metal(name, hexcol='B8892E', rough=0.28, patina='2E3A28', tarnish=0.45,
          scale=6.0, aniso=0.0):
    """One graph for every metal in the room.  A real polished metal is never
    evenly polished: it is bright on the parts that get handled and dull and
    darkened in the hollows, and that unevenness is most of what tells brass
    from gold paint.  `tarnish` is how much of the surface has gone over."""
    m = _mat(name)
    b = NB(m)
    base = srgb(hexcol)[:3]
    v = _obj_vec(b, scale=(scale,) * 3)
    broad = b.noise(v, scale=2.2, detail=5.0, rough=0.6, x=-1500)
    fine = b.noise(v, scale=40.0, detail=6.0, rough=0.75, x=-1500)
    fine.location = (-1500, -320)
    # cavities hold the tarnish: pointiness is the cheap, reliable proxy
    geo = b.n('ShaderNodeNewGeometry', x=-1500, y=-640)
    pt = b.ramp(geo, 'Pointiness', [(0.42, (1, 1, 1)), (0.52, (0, 0, 0))],
                x=-1300)
    pt.location = (-1300, -640)
    dirt = b.math('MULTIPLY', broad, 'Fac', pt, 0, x=-1120)
    dm = b.math('MULTIPLY', dirt, 0, vb=tarnish * 1.8, x=-980, clamp=True)
    col = b.mix(base, 0, srgb(patina)[:3], 0, dm, 0, x=-800)
    rr = b.math('MULTIPLY_ADD', fine, 'Fac', vb=0.22, x=-980)
    rr.location = (-980, -320)
    rr.inputs[2].default_value = rough
    rr2 = b.fmix(rr, 0, 0.85, 0, dm, 0, x=-800)
    rr2.location = (-800, -320)
    bmp = b.bump(fine, 'Fac', strength=0.10, dist=0.003, x=-620)
    p = b.principled(base=col, baseo=0, rough=rough, roughn=rr2, rougho=0,
                     metal=1.0, normal=bmp, aniso=aniso, x=0)
    b.out(p)
    return m


def chrome(name='chrome', rough=0.06, tint='E8ECEF'):
    return metal(name, tint, rough=rough, patina='6A6E72', tarnish=0.18,
                 scale=10.0)


def mirror(name='mirror', tint='D8DCD6', rough=0.03, age=0.35):
    """Silvered glass with the backing going at the edges, as every mirror on
    a 1990s set does."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(3.0,) * 3)
    spot = b.noise(v, scale=6.0, detail=7.0, rough=0.7, x=-1400)
    geo = b.n('ShaderNodeNewGeometry', x=-1400, y=-320)
    pt = b.ramp(geo, 'Pointiness', [(0.45, (1, 1, 1)), (0.55, (0, 0, 0))],
                x=-1200)
    pt.location = (-1200, -320)
    fog = b.math('MULTIPLY', spot, 'Fac', pt, 0, x=-1000)
    fm = b.math('MULTIPLY', fog, 0, vb=age * 2.2, x=-860, clamp=True)
    col = b.mix(srgb(tint)[:3], 0, srgb('8A8073')[:3], 0, fm, 0, x=-700)
    rr = b.fmix(rough, 0, 0.42, 0, fm, 0, x=-700)
    rr.location = (-700, -300)
    p = b.principled(base=col, baseo=0, rough=rough, roughn=rr, rougho=0,
                     metal=1.0, x=0)
    b.out(p)
    return m


# ================================================================== SIGNAGE

def chalkboard(name='chalkboard', hexcol='1E2B24', dust=0.5):
    """Slate that has been written on and wiped a thousand times: the ghost
    of everything erased is smeared across it in arcs."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(1.4, 1.4, 1.4))
    smear = b.noise((b.mapping(v[0], v[1], scale=(1.0, 9.0, 1.0), x=-1700), 0),
                    scale=3.0, detail=6.0, rough=0.62, dist=0.8, x=-1500)
    grit = b.noise(v, scale=120.0, detail=6.0, rough=0.7, x=-1500)
    grit.location = (-1500, -320)
    sm = b.ramp(smear, 'Fac', [(0.42, (0, 0, 0)), (0.72, (1, 1, 1))], x=-1300)
    d = b.math('MULTIPLY', sm, 0, vb=dust, x=-1120)
    col = b.mix(srgb(hexcol)[:3], 0, srgb('9CA79E')[:3], 0, d, 0, x=-940)
    bmp = b.bump(grit, 'Fac', strength=0.16, dist=0.002, x=-760)
    rr = b.fmix(0.72, 0, 0.86, 0, d, 0, x=-940)
    rr.location = (-940, -300)
    p = b.principled(base=col, baseo=0, rough=0.76, roughn=rr, rougho=0,
                     normal=bmp, spec=0.3, x=0)
    b.out(p)
    return m


def neon(name, hexcol='FF2D55', strength=26.0, glass='1A1418'):
    """A neon tube.  Lit gas is not a lambert surface: it is bright straight
    through and brighter at the rim where you look along more of the column,
    so the emission rides a facing-weighted curve rather than sitting flat."""
    m = _mat(name)
    b = NB(m)
    lw = b.n('ShaderNodeLayerWeight', x=-900)
    lw.inputs['Blend'].default_value = 0.28
    rim = b.math('POWER', lw, 'Fresnel', vb=1.6, x=-740)
    lift = b.math('MULTIPLY_ADD', rim, 0, vb=strength * 0.9, x=-580)
    lift.inputs[2].default_value = strength
    e = b.n('ShaderNodeEmission', x=-380)
    e.inputs['Color'].default_value = srgb(hexcol)
    b.l(lift, 0, e, 'Strength')
    # the unlit glass wall of the tube, so it still reads as a tube when off
    p = b.principled(color=srgb(glass)[:3], rough=0.08, transm=0.0, x=-380)
    p.location = (-380, -320)
    mixs = b.n('ShaderNodeMixShader', x=-120)
    mixs.inputs['Fac'].default_value = 0.88
    b.l(p, 0, mixs, 1); b.l(e, 0, mixs, 2)
    b.out(mixs)
    return m


def img_mat(name, path, emit=0.0, alpha=False, rough=0.52):
    """The two sanctioned bitmaps: the Statue of Liberty canvas and the window
    decal.  Everything else in the build is nodes."""
    m = _mat(name)
    b = NB(m)
    img = bpy.data.images.get(name) or bpy.data.images.load(path, check_existing=True)
    tex = b.n('ShaderNodeTexImage', x=-600)
    tex.image = img
    tex.extension = 'CLIP'
    tex.interpolation = 'Cubic'
    tc = b.n('ShaderNodeTexCoord', x=-900)
    b.l(tc, 'UV', tex, 'Vector')
    p = b.principled(base=tex, baseo='Color', rough=rough, spec=0.3, x=0)
    if emit:
        b.l(tex, 'Color', p, 'Emission Color')
        p.inputs['Emission Strength'].default_value = emit
    if alpha:
        b.l(tex, 'Alpha', p, 'Alpha')
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else 'BLEND'
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
        m.use_backface_culling = False
    b.out(p)
    return m


def fabric(name, hexcol, rough=0.76, sheen=0.35, scale=200.0, aniso=1.0,
           bump=0.30, stripes=None, pitch=0.24):
    """Plain woven cloth - curtains, the fringe, upholstery linings.  The
    weave is the whole texture; the colour is flat by design.

    `stripes` turns it into a woven stripe: a list of (width, colour) bands
    repeating every `pitch` metres in world Z, which for a hung curtain is
    across its width.  The curtains beside the counter in main_couch.webp and
    full_set.jpg are a bold red / green / cream ticking, and left plain they
    were the one dead flat surface in that corner of the room."""
    m = _mat(name)
    b = NB(m)
    base = srgb(hexcol)[:3]
    v = _obj_vec(b, scale=(1.0, 1.0, 1.0))
    w = _weave(b, v, scale=scale, x=-1400, aniso=aniso)
    drift = b.noise(v, scale=4.0, detail=5.0, rough=0.6, x=-1400)
    drift.location = (-1400, -420)
    col = b.mix(tuple(c * 0.86 for c in base), 0,
                tuple(min(1.0, c * 1.12) for c in base), 0, drift, 'Fac', x=-900)
    if stripes:
        # Bands read off the object's own Z, wrapped by a modulo, so a fold
        # carries the stripe round with it instead of the stripe sliding
        # across the fold the way a screen-space pattern would.
        sep = b.n('ShaderNodeSeparateXYZ', x=-1340, y=-700)
        b.l(v[0], v[1], sep, 'Vector')
        wr = b.math('WRAP', sep, 'Z', vb=pitch, x=-1180)
        wr.location = (-1180, -700)
        wr.inputs[2].default_value = 0.0
        fr = b.math('DIVIDE', wr, 0, vb=pitch, x=-1040)
        fr.location = (-1040, -700)
        tot = float(sum(s[0] for s in stripes))
        stops, acc = [], 0.0
        for (wd, hx) in stripes:
            stops.append((acc / tot, srgb(hx)[:3]))
            acc += wd
        rmp = b.ramp(fr, 0, stops, x=-900, interp='CONSTANT')
        rmp.location = (-900, -700)
        col = b.mix(col, 0, rmp, 0, None, x=-760, factor=0.80)
    bmp = b.bump(w, 0, strength=bump, dist=0.004, x=-600)
    p = b.principled(base=col, baseo=0, rough=rough, normal=bmp, sheen=sheen,
                     sheen_tint=tuple(min(1.0, c * 1.4 + 0.08) for c in base),
                     spec=0.22, x=0)
    b.out(p)
    return m


def foliage(name, light='4E7A3A', dark='24401E', scale=40.0):
    """Leaves, as a surface rather than as geometry per blade: strong colour
    variance leaf to leaf and a waxy top coat."""
    m = _mat(name)
    b = NB(m)
    v = _obj_vec(b, scale=(scale,) * 3)
    n1 = b.noise(v, scale=6.0, detail=6.0, rough=0.65, x=-1400)
    n2 = b.noise(v, scale=34.0, detail=5.0, rough=0.6, x=-1400)
    n2.location = (-1400, -320)
    col = b.mix(srgb(dark)[:3], 0, srgb(light)[:3], 0, n1, 'Fac', x=-1000)
    col2 = b.mix(col, 0, srgb('7E9440')[:3], 0, n2, 'Fac', x=-800, factor=0.3)
    bmp = b.bump(n2, 'Fac', strength=0.3, dist=0.006, x=-600)
    p = b.principled(base=col2, baseo=0, rough=0.42, normal=bmp, coat=0.3,
                     x=0)
    b.out(p)
    return m


def petal(name, hexcol='E2621F', rough=0.55):
    """Flower petals: translucent, so they glow when a lamp is behind them."""
    m = _mat(name)
    b = NB(m)
    base = srgb(hexcol)[:3]
    v = _obj_vec(b, scale=(30.0,) * 3)
    n = b.noise(v, scale=14.0, detail=5.0, rough=0.6, x=-1300)
    col = b.mix(tuple(c * 0.7 for c in base), 0,
                tuple(min(1.0, c * 1.3 + 0.04) for c in base), 0, n, 'Fac',
                x=-900)
    p = b.principled(base=col, baseo=0, rough=rough, x=0)
    try:
        p.inputs['Subsurface Weight'].default_value = 0.35
        p.inputs['Subsurface Radius'].default_value = (0.012, 0.006, 0.003)
    except Exception:
        pass
    b.out(p)
    return m
