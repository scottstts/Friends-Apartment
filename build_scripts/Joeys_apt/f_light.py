"""f_light - the lighting, and the fixtures that justify it.

The rule for this build is that no light exists without something in the room
emitting it.  So every lamp here is created together with its housing, and the
housing is what decides where the lamp sits, how big it is, and which way it
faces - not the other way round.  There are no fill lights.  If a corner comes
out dark, the answer is a fixture that would really be there, not a floating
area light pointed at the problem.

Three families, and they have to be balanced against each other rather than
tuned one at a time:

  * The window.  These windows face north into a light well, so the key is the
    SKY, never a sun disc - a north window has no beam to cast.  It is cool,
    it is soft, and it falls off fast, which is why the far side of the room
    needs practicals at all.

  * The practicals.  Ceiling roses, a floor lamp, a sconce, the strip under the
    wall units, the light in the cooker hood.  These are warm - a 1990s
    apartment is tungsten - and they are what pushes the walls back to the
    warm greige they are actually painted, instead of the cold grey that sky
    light alone makes of them.

  * Emission.  Every shade, dome and diffuser also gets an emissive material,
    because a lamp whose shade stays dark reads as switched off however bright
    the room around it is.
"""
import bpy, math
import mlib, mats, props, L

C = "Light"

# One gain on every practical in the flat.  The RATIOS between fixtures are
# what was designed - a rose against the strip under the wall units against the
# floor lamp - and they should not have to be re-derived every time the overall
# exposure moves.  Tune this, not the individual wattages.
GAIN = 0.185

WARM = 'FFEBD2'          # tungsten through a shade, nearer 2900 K
WARM_HOT = 'FFE8CC'      # the small bright ones read a touch whiter
COOL = 'DCE8F4'


def materials():
    # the glowing surfaces carry the same warmth as the lamps inside them, or
    # the shade reads a different colour from the light it is giving off
    mats.emissive("M_BulbGlow", WARM_HOT, strength=6.0)
    mats.emissive("M_DomeGlow", WARM, strength=2.4)
    mats.emissive("M_StripGlow", WARM_HOT, strength=3.4)
    mats.metal("M_FixBrass", 'A8842E', rough=0.30, grime=0.35)
    mats.metal("M_FixChrome", 'D6DADE', rough=0.10, grime=0.30)
    mats.plastic("M_Opal", 'F0EADA', rough=0.42, coat=0.20)


def M(n):
    return mats.get(n)


def diffuser(obj):
    """A diffuser has to be transparent to SHADOW rays even though it is opaque
    to camera rays.  Leave it casting and the opal dome screens its own lamp:
    the fixture reads as brightly lit and the room under it stays dark, which
    looks exactly like a lamp that is too weak and is not."""
    obj.visible_shadow = False
    return obj


def _lamp(name, kind, loc, energy, col=WARM, size=0.12, size_y=None,
          rot=(0.0, 0.0, 0.0), spot=None, diffuse=1.0, spec=1.0):
    d = bpy.data.lights.new(name, kind)
    d.energy = energy * GAIN
    d.color = mats.srgb(col)[:3]
    d.diffuse_factor = diffuse
    d.specular_factor = spec
    if kind == 'AREA':
        d.shape = 'RECTANGLE' if size_y else 'DISK'
        d.size = size
        if size_y:
            d.size_y = size_y
    elif kind == 'POINT':
        d.shadow_soft_size = size
    elif kind == 'SPOT':
        d.shadow_soft_size = size
        d.spot_size = math.radians(spot or 90.0)
        d.spot_blend = 0.45
    ob = bpy.data.objects.new(name, d)
    mlib.put(ob, C)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


# ================================================================== fixtures

def ceiling_rose(name, cx, cy, energy=52.0, z=None):
    """A flush-mount opal dome on a moulded ring - what is actually screwed to
    the ceiling of a walk-up like this.  The dome is the emitter you SEE; the
    area light just under it is the emitter that does the work."""
    z = L.CZ if z is None else z
    ring = props.lathe(name + "_r", [(0.0, 0.0), (0.155, 0.0), (0.152, -0.014),
                                     (0.128, -0.022), (0.126, -0.030),
                                     (0.0, -0.032)], 30, C)
    mlib.translate(ring, (cx, cy, z))
    mlib.set_mat(ring, M("M_FixBrass"))

    # widest at the ceiling ring, curving down to a closed pole - the other
    # way round gives a mushroom
    prof = [(0.0, -0.020)]
    for k in range(11):
        a = math.pi * 0.5 * k / 10.0
        prof.append((0.148 * math.cos(a), -0.026 - 0.115 * math.sin(a)))
    dome = diffuser(props.lathe(name + "_d", prof, 30, C))
    mlib.translate(dome, (cx, cy, z))
    mlib.set_mat(dome, M("M_DomeGlow"))

    # an AREA light already points along -Z; adding a pi rotation about X - the
    # obvious "aim it down" - turns it round to light the ceiling void instead
    lamp = _lamp(name + "_L", 'AREA', (cx, cy, z - 0.115), energy, WARM,
                 size=0.26)
    return [ring, dome, lamp]


def sconce(name, u, z, wall, at, energy=17.0):
    """A half-shade on a bracket.  Faces into the room, throws up and down."""
    parts = []
    plate = props.lathe(name + "_p", [(0.0, 0.0), (0.062, 0.0), (0.060, 0.012),
                                      (0.026, 0.020), (0.024, 0.070),
                                      (0.0, 0.072)], 20, C)
    props.face_y(plate, 1.0)
    mlib.set_mat(plate, M("M_FixBrass"))
    parts.append(plate)
    # an opal bowl on the bracket, opening upwards - it washes the wall and the
    # ceiling above it, which is the whole point of a sconce
    bowl = props.lathe(name + "_s", [(0.0, 0.0), (0.052, 0.006), (0.098, 0.042),
                                     (0.132, 0.106), (0.134, 0.112),
                                     (0.096, 0.048), (0.050, 0.014),
                                     (0.0, 0.008)], 28, C)
    mlib.translate(bowl, (0.0, 0.104, -0.016))
    mlib.set_mat(bowl, M("M_Opal"))
    diffuser(bowl)
    parts.append(bowl)
    bulb = props.lathe(name + "_b", [(0.0, 0.0), (0.021, 0.008), (0.024, 0.030),
                                     (0.018, 0.050), (0.0, 0.056)], 14, C)
    mlib.translate(bulb, (0.0, 0.104, 0.030))
    mlib.set_mat(bulb, M("M_BulbGlow"))
    diffuser(bulb)
    parts.append(bulb)
    props.wall_place(parts, wall, u, z, at)

    # place the lamp where the bulb ended up
    b = parts[2]
    cc = sum((v.co for v in b.data.vertices), mlib.Vector((0, 0, 0)))
    cc /= len(b.data.vertices)
    parts.append(_lamp(name + "_L", 'POINT', tuple(cc), energy, WARM, size=0.05))
    return parts


def under_cabinet(name, x0, x1, y, z, energy=13.0):
    """The strip behind the wall-unit valance.  The valance board already
    exists; this is the tube it hides."""
    tube = mlib.tube_along(name + "_t", [(x0, y, z), (x1, y, z)],
                           mlib.circle(0.013, 10), cname=C)
    mlib.smooth_shade(tube, 46)
    mlib.set_mat(tube, M("M_StripGlow"))
    diffuser(tube)
    lamp = _lamp(name + "_L", 'AREA', ((x0 + x1) * 0.5, y, z - 0.014), energy,
                 WARM_HOT, size=x1 - x0, size_y=0.05)
    return [tube, lamp]


def hood_light(name, x0, x1, y, z, energy=9.0):
    """The pair of lamps in the underside of the over-range microwave."""
    out = []
    for k in (0.30, 0.70):
        xx = x0 + (x1 - x0) * k
        lens = mlib.box(name + "_g%d" % int(k * 10), xx - 0.055, y - 0.055,
                        z - 0.006, xx + 0.055, y + 0.055, z, C)
        mlib.bevel(lens, 0.003, 2, 40)
        mlib.set_mat(lens, M("M_StripGlow"))
        out.append(diffuser(lens))
    out.append(_lamp(name + "_L", 'AREA', ((x0 + x1) * 0.5, y, z - 0.012),
                     energy, WARM_HOT, size=x1 - x0 - 0.16, size_y=0.14))
    return out


def bulb_in(name, loc, energy, col=WARM, r=0.028, size=0.05):
    """A bare bulb inside a shade that already exists elsewhere in the build -
    the floor lamp, the bedside lamps.  The shade is the fixture; this is only
    the filament and the lamp that goes with it."""
    b = props.lathe(name + "_b", [(0.0, 0.0), (r * 0.5, 0.004), (r, 0.030),
                                  (r * 0.92, 0.058), (r * 0.5, 0.076),
                                  (0.0, 0.080)], 16, C)
    mlib.translate(b, loc)
    mlib.set_mat(b, M("M_BulbGlow"))
    diffuser(b)
    return [b, _lamp(name + "_L", 'POINT',
                     (loc[0], loc[1], loc[2] + 0.040), energy, col, size=size)]


def vanity_light(name, u, z, wall, at, energy=22.0, standoff=0.0):
    """A chrome bar with three opal globes over the bathroom mirror.

    `standoff` lifts the whole fitting off the wall LINE.  The bathroom walls
    are tiled, and the tiling is 13 mm of real ceramic standing proud of the
    plaster - a fitting screwed to the plaster line is behind it."""
    parts = []
    bar = mlib.box(name + "_bar", -0.28, standoff, -0.020, 0.28,
                   standoff + 0.052, 0.020, C)
    mlib.bevel(bar, 0.004, 2, 42)
    mlib.set_mat(bar, M("M_FixChrome"))
    parts.append(bar)
    for k in (-1, 0, 1):
        g = props.lathe(name + "_g%d" % (k + 1),
                        [(0.0, 0.0), (0.030, 0.010), (0.046, 0.042),
                         (0.044, 0.072), (0.026, 0.092), (0.0, 0.096)], 20, C)
        mlib.rot_x(g, math.radians(-90.0))
        mlib.translate(g, (k * 0.175, standoff + 0.052, 0.0))
        mlib.set_mat(g, M("M_Opal"))
        parts.append(diffuser(g))
    props.wall_place(parts, wall, u, z, at)
    # 'E' means the room is WEST of the wall, so the light sits at at-0.13 and
    # has to face -X; a rectangle light points along -Z, and R_y(+90) is what
    # takes -Z to -X.  The sign that looks right here is the wrong one.
    sx = -1.0 if wall == 'E' else 1.0
    parts.append(_lamp(name + "_L", 'AREA', (at + sx * 0.13, u, z), energy,
                       WARM_HOT, size=0.56, size_y=0.10,
                       rot=(0.0, math.radians(-90.0 * sx), 0.0)))
    return parts


# ================================================================== the scheme

def probe(bake=True):
    """A baked irradiance volume over the whole flat.

    Without one, EEVEE Next has no stored indirect field to fall back on and
    uses the WORLD as the ambient everywhere - so a sealed room still gets the
    full sky as a flat blue wash on every surface, no matter how thick its
    walls are.  That single missing object is what made the first lit pass come
    back cold and flat however the practicals were balanced.  With the volume
    baked, the interior is lit by what can actually reach it, which is also why
    the lamp wattages below are an order of magnitude higher than they looked
    like they needed to be.
    """
    # The type string carries an underscore - 'LIGHTPROBE' matches nothing, so
    # this loop used to remove no probe at all.  Restricted to LT_ as well:
    # spelled correctly and left unrestricted it eats the bathroom mirror's
    # reflection plane, which is built earlier in the pass.
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT_PROBE' and o.name.startswith("LT_"):
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.lightprobe_add(type='VOLUME', location=(2.60, 4.65, 1.60))
    pr = bpy.context.object
    pr.name = "LT_Probe"
    pr.scale = (6.90, 6.45, 1.85)
    d = pr.data
    # The grid must be FINER THAN THE WALLS.  At 48 x 48 x 14 the cells were
    # 0.29 m across and the walls are 0.30 thick, so a whole cell could sit
    # inside a wall, see the sky during the bake, and then bleed that sky into
    # the room - which is what put a cold blue streak down the top of four
    # corners of this flat.  The building itself is airtight (27,000 rays cast
    # from nine rooms escape it nowhere); the leak was entirely in here.
    d.resolution_x, d.resolution_y, d.resolution_z = 56, 56, 18
    d.bake_samples = 1024
    d.surfel_density = 18
    d.capture_world = True
    d.capture_indirect = True
    d.capture_emission = True
    d.influence_distance = 0.15
    # ...and the lookup steps AWAY from the surface before it samples the grid,
    # so a shading point right in a corner cannot reach the cell on the far
    # side of the wall.  This pair is what actually closes it.
    d.normal_bias = 0.80
    d.view_bias = 0.40
    # samples that land in solid geometry are thrown away and filled in from
    # their valid neighbours instead of being trusted
    d.validity_threshold = 0.30
    d.dilation_threshold = 0.75
    d.dilation_radius = 2.0
    mlib.put(pr, C)
    if bake:
        try:
            bpy.ops.object.lightprobe_cache_bake(subset='ALL')
        except Exception as e:
            print("probe bake failed:", e)
    return pr


def build(bake=True):
    mlib.purge("LT_")
    mlib.coll(C)
    materials()

    # ---- daylight ---------------------------------------------------------
    # The sky alone was blowing the room out: a full-strength physical sky is
    # an enormous source once four windows and a light well are all feeding it
    # bounce.  Pulled back to where the window reads BRIGHT against interior
    # walls that are still their own colour.
    import build_env
    build_env.world(strength=1.20, turbidity=2.4, elev=52.0, rot=200.0)

    # ---- ceiling roses ----------------------------------------------------
    # A REGULAR GRID, not fixtures dropped one at a time wherever the room
    # looked dark.  Four roses cannot cover 65 m2: the west half of this flat
    # had no overhead fixture at all - the nearest one to the entertainment
    # wall was two metres away, so everything from the bookcase to Joey's door
    # was lit by bounce, which is why that side went flat and dim.
    #
    # Columns sit on the eighth-points of the flat's width and rows on the
    # sixth-points of its depth, so every fixture is half a bay from the wall
    # behind it and a full bay from its neighbours - the layout an electrician
    # sets out, and it reads as deliberate from any angle.  Two of the twelve
    # cells fall outside the room, because the kitchen alcove stops at the jog,
    # so they are simply not built.
    COLS = [L.EX * (2 * k + 1) / 8.0 for k in range(4)]          # 1.06 .. 7.41
    ROWS = [L.SY + (L.NY - L.SY) * (2 * k + 1) / 6.0 for k in range(3)]
    for cx in COLS:
        for cy in ROWS:
            if cx > L.JX and cy > L.NY2:        # the alcove ends at the jog
                continue
            ceiling_rose("LT_Rose_%02d%02d" % (round(cx * 10), round(cy * 10)),
                         cx, cy, energy=300.0)

    # ---- practicals in the living room ------------------------------------
    sconce("LT_Sconce", 6.86, 2.24, 'W', L.WX, energy=210.0)
    bulb_in("LT_FloorLamp", (L.FLOOR_LAMP[0], L.FLOOR_LAMP[1], 1.520), 320.0)

    # ---- kitchen ----------------------------------------------------------
    under_cabinet("LT_UnderCab", L.K_UPPER[0] + 0.03, L.K_UPPER[1] - 0.03,
                  L.NY2 - L.UPPER_D + 0.10, L.UPPER_Z[0] - 0.020, energy=105.0)
    hood_light("LT_Hood", L.K_MW[0], L.K_MW[1], L.NY2 - 0.19, L.K_MW_Z[0],
               energy=78.0)

    # ---- bedrooms ---------------------------------------------------------
    bulb_in("LT_JoeyLamp", (L.JO_X[0] + 0.30, 1.72, 0.870), 135.0)
    bulb_in("LT_ChanLamp", (L.CH_X[0] + 0.30, 3.42, 0.870), 135.0)
    # dead centre of each room, which is where a bedroom's one fixture goes
    ceiling_rose("LT_RoseJ", (L.JO_X[0] + L.JO_X[1]) * 0.5,
                 (L.JO_Y[0] + L.JO_Y[1]) * 0.5, energy=290.0)
    ceiling_rose("LT_RoseC2", (L.CH_X[0] + L.CH_X[1]) * 0.5,
                 (L.CH_Y[0] + L.CH_Y[1]) * 0.5, energy=290.0)

    # ---- bathroom ---------------------------------------------------------
    vanity_light("LT_Vanity", L.BA_BASIN[1], 2.020, 'E', L.BA_X[1], energy=200.0,
                 standoff=0.016)
    ceiling_rose("LT_RoseB2", (L.BA_X[0] + L.BA_X[1]) * 0.5,
                 (L.BA_Y[0] + L.BA_Y[1]) * 0.5, energy=185.0, z=L.BA_CZ)

    probe(bake=bake)
    return len([o for o in bpy.data.objects if o.name.startswith("LT_")])
