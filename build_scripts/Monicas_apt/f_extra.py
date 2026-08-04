"""Extra dressing: kitchen small appliances, the window wreath, dish rack,
paper towel, knife block - the clutter that makes this kitchen read."""
import bpy, math, random
from mathutils import Matrix
import mlib, mats, L, props as P

C = "Kitchen"
CTR_H = L.CTR_H


def coffee_maker(name, loc, rotz=0.0, cname=C):
    blk = mats.paint('appl_black', '232323', rough=0.30, coat=0.35)
    chr_ = mats.get('metal_chrome')
    gl = mats.get('glass_thick') or mats.pane('glass_thick')
    parts = []
    body = mlib.prism(name + "_b", mlib.rounded_rect(0.155, 0.190, 0.030, 4),
                      0.0, 0.135, cname)
    mlib.bevel(body, 0.006, 2, 45)
    parts.append((body, blk))
    tower = mlib.prism(name + "_t", mlib.rounded_rect(0.150, 0.105, 0.026, 4),
                       0.135, 0.360, cname)
    mlib.bevel(tower, 0.008, 2, 45)
    mlib.translate(tower, (0, 0.042, 0))
    parts.append((tower, blk))
    plate = mlib.revolve(name + "_p", [(0.0, 0.0), (0.062, 0.0), (0.062, 0.006),
                                       (0.0, 0.006)], 20, cname=cname)
    mlib.translate(plate, (0, -0.035, 0.135))
    parts.append((plate, chr_))
    carafe = mlib.revolve(name + "_c", [(0.0, 0.0), (0.058, 0.004), (0.062, 0.020),
                                        (0.060, 0.130), (0.052, 0.150),
                                        (0.048, 0.160), (0.044, 0.158),
                                        (0.046, 0.135), (0.0, 0.130)], 22,
                          cname=cname)
    mlib.smooth_shade(carafe, 34)
    mlib.translate(carafe, (0, -0.035, 0.141))
    parts.append((carafe, gl))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.rotate_z(ob, rotz)
        mlib.translate(ob, loc)
        objs.append(ob)
    return objs


def stand_mixer(name, loc, rotz=0.0, cname=C):
    body = mats.paint('appl_cream', 'E4DFD2', rough=0.16, coat=0.55)
    chr_ = mats.get('metal_chrome')
    parts = []
    base = mlib.revolve(name + "_bs", [(0.0, 0.0), (0.090, 0.004), (0.094, 0.020),
                                       (0.086, 0.050), (0.070, 0.062),
                                       (0.0, 0.064)], 24, cname=cname)
    mlib.smooth_shade(base, 34)
    parts.append((base, body))
    col = mlib.prism(name + "_col", mlib.rounded_rect(0.070, 0.085, 0.026, 4),
                     0.060, 0.245, cname)
    mlib.bevel(col, 0.010, 2, 45)
    mlib.translate(col, (-0.052, 0, 0))
    parts.append((col, body))
    head = mlib.prism(name + "_hd", mlib.rounded_rect(0.240, 0.082, 0.036, 4),
                      0.200, 0.290, cname)
    mlib.bevel(head, 0.014, 2, 45)
    mlib.translate(head, (0.026, 0, 0))
    parts.append((head, body))
    bowl = mlib.revolve(name + "_bw", [(0.0, 0.0), (0.048, 0.0), (0.072, 0.040),
                                       (0.086, 0.100), (0.090, 0.140),
                                       (0.086, 0.140), (0.082, 0.100),
                                       (0.068, 0.042), (0.044, 0.006),
                                       (0.0, 0.006)], 26, cname=cname)
    mlib.smooth_shade(bowl, 32)
    mlib.translate(bowl, (0.052, 0, 0.058))
    parts.append((bowl, chr_))
    beat = mlib.revolve(name + "_be", [(0.0, 0.0), (0.026, 0.030), (0.030, 0.070),
                                       (0.010, 0.090), (0.010, 0.110),
                                       (0.0, 0.110)], 12, cname=cname)
    mlib.translate(beat, (0.052, 0, 0.090))
    parts.append((beat, chr_))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.rotate_z(ob, rotz)
        mlib.translate(ob, loc)
        objs.append(ob)
    return objs


def dish_rack(name, loc, rotz=0.0, cname=C, n=7):
    wire = mats.metal('metal_wire', 'B8BCC0', rough=0.24, bump=0.05)
    parts = []
    w, d, h = 0.34, 0.26, 0.115
    for s in (-1, 1):
        parts.append(mlib.tube_along(name + "_f",
                                    [(-w / 2, s * d / 2, 0.0), (w / 2, s * d / 2, 0.0)],
                                    mlib.circle(0.0035, 6), cname))
        parts.append(mlib.tube_along(name + "_f2",
                                    [(-w / 2, s * d / 2, h), (w / 2, s * d / 2, h)],
                                    mlib.circle(0.0035, 6), cname))
    for i in range(n):
        xx = -w / 2 + 0.03 + i * (w - 0.06) / (n - 1)
        parts.append(mlib.tube_along(name + "_r%d" % i,
                                     [(xx, -d / 2, 0.0), (xx, -d / 2 + 0.03, h),
                                      (xx, d / 2 - 0.03, h), (xx, d / 2, 0.0)],
                                     mlib.circle(0.0032, 6), cname))
    ob = mlib.join(parts, name, cname)
    mlib.smooth_shade(ob, 40)
    mlib.set_mat(ob, wire)
    mlib.rotate_z(ob, rotz)
    mlib.translate(ob, loc)
    out = [ob]
    # plates standing in the rack
    pm = mats.paint('plate_white', 'EFEADC', rough=0.14, coat=0.55)
    for i in range(4):
        pl = mlib.revolve(name + "_pl%d" % i, [(0.0, 0.0), (0.052, 0.0),
                                               (0.090, 0.006), (0.108, 0.014),
                                               (0.108, 0.019), (0.086, 0.012),
                                               (0.048, 0.005), (0.0, 0.005)],
                          22, cname=cname)
        mlib.rot_y(pl, math.pi / 2)
        mlib.smooth_shade(pl, 32)
        mlib.set_mat(pl, pm)
        # sitting in the rack, not through the worktop: at 0.10 a 108 mm plate
        # reached 8 mm below the rack's own base and so 6 mm into the counter
        mlib.translate(pl, (-0.09 + i * 0.055, 0.0, 0.116))
        mlib.rotate_z(pl, rotz)
        mlib.translate(pl, loc)
        out.append(pl)
    return out


def knife_block(name, loc, rotz=0.0, cname=C):
    wd = mats.wood('wood_block', ('CDA062', 'A0742E', '6C4A18'), ring=22,
                   warp=0.10, warp_scale=1.4, distort=1.4, bump=0.16, axis='XY')
    steel = mats.get('metal_chrome')
    parts = []
    b = mlib.prism_xz(name + "_b", [(-0.055, 0.0), (0.055, 0.0), (0.055, 0.235),
                                    (-0.020, 0.290), (-0.055, 0.270)],
                      -0.055, 0.055, cname)
    mlib.bevel(b, 0.005, 2, 45)
    parts.append((b, wd))
    for i in range(4):
        hl = mlib.prism_xz(name + "_h%d" % i,
                           [(-0.006, 0.0), (0.006, 0.0), (0.008, 0.095),
                            (-0.008, 0.095)], -0.011, 0.011, cname)
        mlib.rot_y(hl, math.radians(11))
        mlib.translate(hl, (0.006 - i * 0.004, -0.036 + i * 0.024, 0.268))
        parts.append((hl, mats.paint('handle_black', '1C1A18', rough=0.32)))
    objs = []
    for ob, mm in parts:
        mlib.set_mat(ob, mm)
        mlib.rotate_z(ob, rotz)
        mlib.translate(ob, loc)
        objs.append(ob)
    return objs


def paper_towel(name, loc, cname=C, hang=None):
    """`hang` is the underside of the shelf it swings from.  Without it the rod
    was pinned at the shelf's own height and the roll ran straight through the
    board - 116 mm of towel occupying the same space as 20 mm of pine."""
    pm = mats.paint('paper_white', 'F0EDE4', rough=0.62)
    chrome = mats.get('metal_chrome')
    if hang is not None:
        loc = (loc[0], loc[1], hang - 0.058 - 0.014)
    parts = []
    rod = mlib.revolve(name + "_rod", [(0.0, 0.0), (0.008, 0.0), (0.008, 0.30),
                                       (0.0, 0.30)], 10, cname=cname)
    mlib.rot_x(rod, -math.pi / 2)
    mlib.set_mat(rod, chrome)
    parts.append(rod)
    roll = mlib.revolve(name + "_roll", [(0.024, 0.0), (0.058, 0.0), (0.058, 0.245),
                                        (0.024, 0.245)], 24, cname=cname)
    mlib.rot_x(roll, -math.pi / 2)
    mlib.translate(roll, (0, 0.028, 0))
    mlib.smooth_shade(roll, 24)
    mlib.set_mat(roll, pm)
    parts.append(roll)
    if hang is not None:
        # the two straps it actually hangs by
        for sy in (0.004, 0.296):
            br = mlib.tube_along(name + "_br",
                                 [(0.0, sy, 0.0), (0.0, sy, hang - loc[2] - 0.004),
                                  (-0.026, sy, hang - loc[2] + 0.002)],
                                 mlib.circle(0.006, 8), cname)
            mlib.smooth_shade(br, 36)
            mlib.set_mat(br, chrome)
            parts.append(br)
    for o in parts:
        mlib.translate(o, loc)
    return parts


def wreath(name, loc, r=0.15, cname=C):
    leaf = mats.paint('wreath_green', '3E5A2E', rough=0.48, variation=0.16)
    rng = random.Random(4)
    parts = []
    ring = mlib.tube_along(name + "_r",
                           [(r * math.cos(a), 0.0, r * math.sin(a))
                            for a in [i * math.tau / 30 for i in range(30)]],
                           mlib.circle(0.012, 7), cname, close_path=True)
    parts.append(ring)
    for i in range(46):
        a = rng.uniform(0, math.tau)
        rr = r * rng.uniform(0.86, 1.16)
        lf = P.leaf_blade(name + "_l", rng.uniform(0.035, 0.065),
                          rng.uniform(0.014, 0.024), 4, cname, curl=0.2)
        mlib.rot_x(lf, rng.uniform(-1.4, 1.4))
        mlib.rotate_z(lf, rng.uniform(0, 6.28))
        mlib.translate(lf, (rr * math.cos(a), rng.uniform(-0.02, 0.02),
                            rr * math.sin(a)))
        parts.append(lf)
    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, leaf)
    mlib.translate(ob, loc)
    return ob


def toaster(name, loc, rotz=0.0, cname=C):
    chr_ = mats.get('metal_chrome')
    body = mlib.prism(name + "_b", mlib.rounded_rect(0.135, 0.235, 0.040, 5),
                      0.010, 0.165, cname)
    mlib.bevel(body, 0.010, 2, 45)
    mlib.smooth_shade(body, 40)
    mlib.set_mat(body, chr_)
    slots = []
    for s in (-1, 1):
        sl = mlib.box(name + "_s", -0.030, s * 0.045 - 0.014, 0.155, 0.030,
                      s * 0.045 + 0.014, 0.168, cname)
        mlib.set_mat(sl, mats.paint('slot_dark', '191817', rough=0.5))
        slots.append(sl)
    for o in [body] + slots:
        mlib.rotate_z(o, rotz)
        mlib.translate(o, loc)
    return [body] + slots


def coat_hook(name, loc, cname=C):
    """Black wrought double hook on the wall beside the door: a back plate and
    two scrolled arms, both reaching out and turning up - the lower one
    further out than the upper, so a coat on it hangs clear."""
    parts = []
    pl = mlib.prism_yz(name + "_pl", [(-0.016, -0.052), (0.016, -0.052),
                                      (0.021, -0.030), (0.021, 0.030),
                                      (0.016, 0.052), (-0.016, 0.052),
                                      (-0.021, 0.030), (-0.021, -0.030)],
                       0.0, 0.010, cname)
    parts.append(pl)
    for (z0, reach, tip) in ((0.032, 0.068, 0.040), (-0.028, 0.092, 0.048)):
        pts = []
        for i in range(13):
            t = i / 12.0
            pts.append((0.008 + reach * math.sin(t * 1.35),
                        0.0,
                        z0 + tip * (1.0 - math.cos(t * 2.05)) * 0.62
                        - reach * 0.22 * t * t))
        arm = mlib.tube_along(name + "_a", pts, mlib.circle(0.0058, 8), cname,
                              up=(0, 1, 0))
        mlib.smooth_shade(arm, 40)
        parts.append(arm)
    ob = mlib.join(parts, name, cname)
    mlib.set_mat(ob, mats.paint('iron_hook_black', '1A1A1C', rough=0.42,
                                bump=0.10, noise=300))
    mlib.translate(ob, loc)
    return ob


def strap_frame(name, loc, cname=C, w=0.205, h=0.145):
    """Small dark frame slung from a leather strap up to a single nail, with a
    pair of bullion tassels off its lower edge.  The strap makes a triangle and
    the tassels hang plumb - it is the hanging that identifies this object, not
    the frame."""
    parts = []
    # rails held to 18 mm: the moulding grows *outward* from w/2, so a 30 mm
    # section put the frame's true width 60 mm over its nominal one and it
    # overhung the door's rough opening
    prof = [(0.0, 0.0), (0.0, 0.020), (0.006, 0.026), (0.014, 0.026),
            (0.018, 0.020), (0.018, 0.0)]
    fr = mlib.sweep_rect_frame(name + "_fr", w, h, prof, cname, depth_axis="Y")
    mlib.set_mat(fr, mats.wood('wood_frame_dark', ('4A3220', '3A2616', '281809'),
                               ring=30.0, warp=0.02, distort=0.3, bump=0.10,
                               rough=(0.30, 0.46), axis='XZ'))
    parts.append((fr, None))
    pane = mlib.box(name + "_pn", -w / 2 + 0.020, 0.008, -h / 2 + 0.020,
                    w / 2 - 0.020, 0.013, h / 2 - 0.020, cname)
    mlib.set_mat(pane, mats.paint('frame_mount_pale', 'D9D6CA', rough=0.42))
    parts.append((pane, None))
    # the strap: up from each top corner to one nail above the middle
    NAIL = (0.0, 0.006, h / 2 + 0.135)
    lea = mats.paint('leather_strap', '6B4A2C', rough=0.62, bump=0.14, noise=340)
    for s in (-1, 1):
        a = (s * (w / 2 - 0.016), 0.004, h / 2 - 0.006)
        st = mlib.tube_along(name + "_sp%d" % (s > 0),
                             [a, ((a[0] + NAIL[0]) * 0.5, 0.005,
                                  (a[2] + NAIL[2]) * 0.5), NAIL],
                             mlib.rounded_rect(0.011, 0.0035, 0.0015, seg=2),
                             cname, up=(0, 1, 0))
        mlib.smooth_shade(st, 40)
        mlib.set_mat(st, lea)
        parts.append((st, None))
    gold = mats.metal('metal_tassel_gold', 'B9922F', rough=0.42, bump=0.06)
    for s in (-1, 1):
        tx = s * w * 0.24
        cd = mlib.tube_along(name + "_tc%d" % (s > 0),
                             [(tx, 0.006, -h / 2 + 0.004),
                              (tx, 0.006, -h / 2 - 0.030)],
                             mlib.circle(0.0022, 6), cname)
        mlib.set_mat(cd, gold)
        parts.append((cd, None))
        # head, then a skirt of threads falling straight down
        hd = mlib.revolve(name + "_th%d" % (s > 0),
                          [(0.0, 0.0), (0.011, -0.006), (0.013, -0.016),
                           (0.009, -0.024), (0.0, -0.026)], 14, cname=cname)
        mlib.translate(hd, (tx, 0.006, -h / 2 - 0.028))
        mlib.smooth_shade(hd, 40)
        mlib.set_mat(hd, gold)
        parts.append((hd, None))
        sk = mlib.revolve(name + "_ts%d" % (s > 0),
                          [(0.010, 0.0), (0.015, -0.020), (0.016, -0.044),
                           (0.012, -0.056), (0.0, -0.058)], 16, cname=cname)
        mlib.translate(sk, (tx, 0.006, -h / 2 - 0.048))
        mlib.smooth_shade(sk, 44)
        mlib.set_mat(sk, gold)
        parts.append((sk, None))
    for ob, _ in parts:
        # built in XZ facing +Y; the west wall faces +X, so swing it a quarter turn
        mlib.rotate_z(ob, -math.pi / 2)
        mlib.translate(ob, loc)
    return [o for o, _ in parts]


def build():
    (dxc, dyc), cl = L.chamfer_dir()
    inw = math.atan2(-dxc, dyc)          # facing into the room off the chamfer
    # north-run counter: coffee maker, mixer, toaster, knife block
    # The three of them shifted east and closed up.  The coffee maker stood at
    # 1.28, which is where the dish rack has to be - hard by the sink - and the
    # rack was cutting through it.  Packing them together also opens one real
    # 250 mm stretch of bare counter in the corner by the fridge, which is the
    # only place left on a 1.33 m run for the loose crockery to stand.
    coffee_maker("X_coffee", (1.50, L.NY - 0.34, CTR_H), math.radians(4))
    stand_mixer("X_mixer", (1.75, L.NY - 0.34, CTR_H), math.radians(-14))
    toaster("X_toaster", (2.01, L.NY - 0.34, CTR_H), math.radians(8))
    # The sink's rim runs from u = 0.324 to u = 1.104 along the chamfer, so
    # both of these were standing on it: the block's near corner was 100 mm
    # inside the rim and the rack straddled it by 106 mm.  They sit on the
    # worktop each side of it now, the rack carried round onto the north run's
    # corner because 320 mm of chamfer is not enough for a 340 mm rack.
    kp = L.chamfer_pt(0.155, 0.30)
    knife_block("X_knives", (kp[0], kp[1], CTR_H), inw + math.radians(10))
    # chamfer counter beside the sink: dish rack + paper towel
    # far enough past the sink's rim (which ends at u = 1.104) that the 8 deg
    # skew on the rack does not swing its near corner back over the steel
    p = L.chamfer_pt(1.30, 0.34)
    # +4 mm, not +2: the base rails are 3.5 mm tubes drawn on their centreline,
    # so at +2 the wire was buried a millimetre and a half in the butcher block
    dish_rack("X_rack", (p[0], p[1], CTR_H + 0.004), inw + math.radians(-8))
    paper_towel("X_ptowel", (0.095, L.KIT_WEDGE[0] + 0.30, 0.0), hang=1.34)
    # (a wreath used to hang in the kitchen window.  kitchen2 shows that window
    # square on and entirely unobstructed - swagged curtain, plain glazing, the
    # pendant in front of it - so there is nothing to hang there.)
    # (there were two glazed plates hung on the brick here.  Nothing hangs on
    # that pier on the set - it is bare brick, which is exactly what gives the
    # pot rack something to read against - and the pair sat right behind the
    # rack, so the colander was lost against a white disc.)
    # the lavender wall north of the front door: coat hook and hanging frame
    # the strip of plaster between the door casing and the brick is only about
    # 190 mm here, so both pieces are sized to sit inside it
    my = (L.FD_Y[1] + L.W_PLASTER[1]) * 0.5
    coat_hook("X_hook", (0.020, my + 0.012, 1.800), cname="Openings")
    strap_frame("X_strapfr", (0.020, my, 1.385), cname="Openings",
                w=0.136, h=0.104)
    print("extra dressing built")
