"""f_extra - the pieces that do not belong to a room so much as to the flat:
the foosball table, the bookcase, the wall telephone, the hockey sticks.

The foosball table is the second most recognisable object in this apartment
after the recliners, and it is almost all thin metal: eight chrome rods, four
chrome legs, and twenty-six little men.  Modelled loosely it turns into a black
box with sticks through it, so the rods get real handles, real bearings and
real score sliders, and the men get shoulders and feet.
"""
import bpy, math, random
from mathutils import Vector
import mlib, mats, props, L

C = "Extra"


def materials():
    mats.plastic("M_FoosCase", '1A1A1E', rough=0.40, coat=0.22)
    mats.paint("M_FoosField", '2C7C44', rough=0.42, coat=0.22, brush=0.75)
    mats.paint("M_FoosLine", 'E8E6DE', rough=0.36, coat=0.30)
    mats.plastic("M_FoosRed", 'B32820', rough=0.30, coat=0.40)
    mats.plastic("M_FoosBlue", '1E4FA0', rough=0.30, coat=0.40)
    mats.plastic("M_FoosGrip", '141416', rough=0.52, coat=0.10)
    mats.metal("M_Rod", 'D2D6DA', rough=0.10, brush=0.35, grime=0.25)
    # the corner shelf tower is the same pale stock as the wall unit
    mats.wood("M_ShelfWood", ['C2A472', 'D6C098', 'A68450'], ring=6.0,
              axis='Z', warp=0.42, rough=(0.26, 0.48), coat=0.24,
              grain_relief=0.05)
    for nm, col in (("Book1", '7A2A24'), ("Book2", '234A6E'), ("Book3", '2E5A3C'),
                    ("Book4", 'B08A3A'), ("Book5", '4A3468'), ("Book6", '8A4420'),
                    ("Book7", 'D8D0BC'), ("Book8", '2C2A28')):
        mats.paper("M_" + nm, col, rough=0.48, gloss=0.22)
    mats.wood("M_StickWood", ['A8804A', 'C6A268', '7E5A2E'], ring=40.0,
              axis='Z', rough=(0.28, 0.50), coat=0.20, scale=2.0)
    mats.plastic("M_StickTape", '1C1C1F', rough=0.62)
    # mop yarn: cotton, grubby, and very rough - it is the one thing in the
    # flat that should not catch a highlight anywhere
    mats.fabric("M_MopYarn", 'C8C0AC', rough=0.96, weave=180.0, sheen=0.12,
                bump=0.9, fuzz=1.6)
    mats.plastic("M_PhoneWhite", 'E8E4D8', rough=0.34, coat=0.28)
    mats.plastic("M_Plinth", 'E2DED2', rough=0.42, coat=0.12)


def M(n):
    return mats.get(n)


# ================================================================== foosball

def _man(name, col):
    """One player: a torso with shoulders, a head, and a pair of feet.  Small,
    but there are twenty-six of them and they are all in silhouette."""
    body = props.lathe(name + "_b", [
        (0.0, 0.0), (0.020, 0.0), (0.021, 0.014), (0.014, 0.022),
        (0.015, 0.048), (0.021, 0.058), (0.023, 0.072), (0.018, 0.082),
        (0.010, 0.086), (0.011, 0.092), (0.017, 0.100), (0.016, 0.112),
        (0.008, 0.118), (0.0, 0.119)], 14, C, smooth=54)
    foot = mlib.rounded_box(name + "_f", -0.030, -0.014, 0.0, 0.030, 0.014,
                            0.012, r=0.006, cname=C)
    ob = mlib.join([body, foot], name, C)
    mlib.set_mat(ob, M(col))
    return ob


def foosball():
    out = []
    HL, HW = L.FOOS_L * 0.5, L.FOOS_W * 0.5
    deck, top = 0.780, 0.900
    rodz = 0.862

    # cabinet: four walls round a sunken field, not one hollowed block
    for (nm, a0, b0, a1, b1) in (
            ("end0", -HL, -HW, -HL + 0.052, HW),
            ("end1", HL - 0.052, -HW, HL, HW),
            ("sid0", -HL + 0.052, -HW, HL - 0.052, -HW + 0.052),
            ("sid1", -HL + 0.052, HW - 0.052, HL - 0.052, HW)):
        w = mlib.box("X_Foos_" + nm, a0, b0, 0.620, a1, b1, top, C)
        mlib.bevel(w, 0.004, 2, 42)
        mlib.set_mat(w, M("M_FoosCase"))
        out.append(w)
    # The cabinet floor stops 14 mm BELOW the deck so the green playfield sits
    # on it.  Run to the same z and the two tops are coplanar, same-facing and
    # exactly coincident - and the black one wins, which is why the pitch was
    # rendering black.
    base = mlib.box("X_FoosFloor", -HL + 0.050, -HW + 0.050, 0.618,
                    HL - 0.050, HW - 0.050, deck - 0.014, C)
    mlib.set_mat(base, M("M_FoosCase"))
    out.append(base)
    field = mlib.box("X_FoosField", -HL + 0.052, -HW + 0.052, deck - 0.016,
                     HL - 0.052, HW - 0.052, deck, C)
    mlib.set_mat(field, M("M_FoosField"))
    out.append(field)
    for (a0, a1, b0, b1) in ((-0.004, 0.004, -HW + 0.052, HW - 0.052),
                             (-HL + 0.052, HL - 0.052, -0.003, 0.003)):
        ln = mlib.box("X_FoosLine", a0, b0, deck, a1, b1, deck + 0.0022, C)
        mlib.set_mat(ln, M("M_FoosLine"))
        out.append(ln)
    ctr = props.torus("X_FoosCircle", 0.145, 0.0022, 40, 6, C, cz=deck + 0.001)
    mlib.set_mat(ctr, M("M_FoosLine"))
    out.append(ctr)

    # legs, with a stretcher between each pair
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (HL - 0.095), sy * (HW - 0.095)
            lg = mlib.tube_along("X_FoosLeg", [(lx, ly, 0.030), (lx, ly, 0.625)],
                                 mlib.circle(0.026, 12), cname=C)
            mlib.smooth_shade(lg, 46)
            mlib.set_mat(lg, M("M_Rod"))
            out.append(lg)
            ft = props.lathe("X_FoosFoot", [(0.0, 0.0), (0.034, 0.0),
                                            (0.032, 0.018), (0.020, 0.030),
                                            (0.0, 0.032)], 14, C)
            mlib.translate(ft, (lx, ly, 0.0))
            mlib.set_mat(ft, M("M_FoosGrip"))
            out.append(ft)
        st = mlib.tube_along("X_FoosBrace",
                             [(sx * (HL - 0.095), -HW + 0.095, 0.180),
                              (sx * (HL - 0.095), HW - 0.095, 0.180)],
                             mlib.circle(0.016, 10), cname=C)
        mlib.smooth_shade(st, 46)
        mlib.set_mat(st, M("M_Rod"))
        out.append(st)

    # eight rods: goalie, defence, midfield, attack, alternating sides
    layout = [(-0.525, 1, 'M_FoosRed'), (-0.375, 2, 'M_FoosRed'),
              (-0.225, 3, 'M_FoosBlue'), (-0.075, 5, 'M_FoosRed'),
              (0.075, 5, 'M_FoosBlue'), (0.225, 3, 'M_FoosRed'),
              (0.375, 2, 'M_FoosBlue'), (0.525, 1, 'M_FoosBlue')]
    for i, (rx, n, col) in enumerate(layout):
        side = -1 if col == 'M_FoosRed' else 1
        r0, r1 = -HW - 0.055, HW + 0.055
        if side < 0:
            r0 -= 0.235
        else:
            r1 += 0.235
        rod = mlib.tube_along("X_FoosRod%d" % i, [(rx, r0, rodz), (rx, r1, rodz)],
                              mlib.circle(0.0075, 10), cname=C)
        mlib.smooth_shade(rod, 46)
        mlib.set_mat(rod, M("M_Rod"))
        out.append(rod)
        grip = props.lathe("X_FoosGrip%d" % i, [
            (0.0, 0.0), (0.022, 0.004), (0.024, 0.026), (0.019, 0.075),
            (0.024, 0.130), (0.022, 0.150), (0.0, 0.154)], 16, C)
        # the grip's BASE goes at the rod end, then it grows outward - place it
        # by its centre and it hangs 150 mm off the end of the rod
        props.face_y(grip, -1.0, (rx, r0 + 0.154, rodz)) if side < 0 else \
            props.face_y(grip, 1.0, (rx, r1 - 0.154, rodz))
        mlib.set_mat(grip, M("M_FoosGrip"))
        out.append(grip)
        for k in range(n):
            py = (k - (n - 1) * 0.5) * (2 * HW - 0.16) / max(n, 2)
            mn = _man("X_FoosMan%d_%d" % (i, k), col)
            mlib.translate(mn, (rx, py, deck + 0.001))
            out.append(mn)

    # score sliders: a thin rod along each side rail with five beads on it
    for sy in (-1, 1):
        sr = mlib.tube_along("X_FoosScoreRod", [(-HL + 0.09, sy * (HW - 0.026), top + 0.020),
                                                (HL - 0.09, sy * (HW - 0.026), top + 0.020)],
                             mlib.circle(0.0035, 8), cname=C)
        mlib.smooth_shade(sr, 46)
        mlib.set_mat(sr, M("M_Rod"))
        out.append(sr)
        for k in range(5):
            bd = props.torus("X_FoosBead", 0.011, 0.0055, 14, 6, C)
            mlib.rot_y(bd, math.pi * 0.5)
            mlib.translate(bd, (-HL + 0.14 + k * 0.048, sy * (HW - 0.026),
                                top + 0.020))
            mlib.set_mat(bd, M("M_FoosGrip"))
            out.append(bd)

    grp = mlib.join(out, "X_Foosball", C)
    mlib.rotate_z(grp, math.radians(L.FOOS_ROT))
    mlib.translate(grp, (L.FOOS_C[0], L.FOOS_C[1], 0.0))
    return [grp]


# ================================================================== west wall

def bookcase():
    """The open shelf tower.  It belongs in the SOUTH-WEST corner, tight to the
    fourth wall, which is where full_set.jpg puts it - carrying the model
    sloop, the framed pictures and a row of boxes.  Standing next to Chandler's
    door, where the first pass put it, it is not in any reference frame at all
    and the open door leaf cuts it in half."""
    out = []
    y0, y1 = L.SY + 0.16, L.SY + 1.04
    x0, x1 = L.WX + 0.026, L.WX + 0.026 + 0.330
    z1 = 1.90
    shelves = (0.40, 0.76, 1.12, 1.48)
    parts = [mlib.box("X_BcL", x0, y0, 0.0, x1, y0 + 0.024, z1, C),
             mlib.box("X_BcR", x0, y1 - 0.024, 0.0, x1, y1, z1, C),
             mlib.box("X_BcB", x0, y0 + 0.024, 0.0, x0 + 0.020, y1 - 0.024, z1, C),
             mlib.box("X_BcT", x0 + 0.020, y0 + 0.024, z1 - 0.022, x1,
                      y1 - 0.024, z1, C),
             mlib.box("X_BcF", x0 + 0.020, y0 + 0.024, 0.055, x1,
                      y1 - 0.024, 0.077, C)]
    for i, sz in enumerate(shelves):
        parts.append(mlib.box("X_BcS%d" % i, x0 + 0.020, y0 + 0.024, sz - 0.011,
                              x1, y1 - 0.024, sz + 0.011, C))
    ob = mlib.join(parts, "X_Bookcase", C)
    mlib.bevel(ob, 0.003, 2, 42)
    mlib.set_mat(ob, M("M_ShelfWood"))
    out.append(ob)

    rnd = random.Random(77)
    cols = ["M_Book1", "M_Book2", "M_Book3", "M_Book4", "M_Book5", "M_Book6",
            "M_Book7", "M_Book8", "M_FoosRed", "M_FoosBlue", "M_ShelfWood"]
    # front-of-shelf, spines out, like the wall unit
    front = x1 - 0.014
    for sz in (0.077,) + shelves:
        y = y0 + 0.06
        while y < y1 - 0.14:
            k = rnd.random()
            if k < 0.62:
                bw = rnd.uniform(0.024, 0.042)
                ob = mlib.box("X_BcBook", front - rnd.uniform(0.15, 0.20), y,
                              sz + 0.011, front, y + bw,
                              sz + 0.011 + rnd.uniform(0.19, 0.28), C)
                mlib.bevel(ob, 0.0015, 2, 44)
            elif k < 0.82:
                bw = 0.10
                ob = props.boxprop("X_BcBox", front - 0.080, y + 0.05,
                                   sz + 0.011, 0.16, 0.095,
                                   rnd.uniform(0.10, 0.16), C)
            else:
                bw = 0.13
                ob = props.jar("X_BcJar", front - 0.058, y + 0.065, sz + 0.011,
                               r=0.055, h=rnd.uniform(0.12, 0.17), cname=C)
            mlib.set_mat(ob, M(cols[rnd.randrange(len(cols))]))
            out.append(ob)
            y += bw + rnd.uniform(0.012, 0.030)
    out += boat(x0 + 0.16, (y0 + y1) * 0.5, z1)
    return out


def boat(cx, cy, z):
    """A model sloop on top of the bookcase."""
    out = []
    hull = props.sweep_var("X_BoatHull", [
        (cx, cy - 0.235, z + 0.052), (cx, cy - 0.170, z + 0.044),
        (cx, cy - 0.040, z + 0.038), (cx, cy + 0.110, z + 0.040),
        (cx, cy + 0.205, z + 0.052)],
        [(0.018, 0.014), (0.048, 0.044), (0.058, 0.052), (0.044, 0.044),
         (0.014, 0.016)], 12, C, smooth=60)
    mlib.set_mat(hull, M("M_PhoneWhite"))
    out.append(hull)
    mast = mlib.tube_along("X_BoatMast", [(cx, cy - 0.02, z + 0.070),
                                          (cx, cy - 0.02, z + 0.400)],
                           mlib.circle(0.0045, 8), cname=C)
    mlib.smooth_shade(mast, 46)
    mlib.set_mat(mast, M("M_StickWood"))
    out.append(mast)
    sail = mlib.mesh_obj("X_BoatSail",
                         [(cx - 0.002, cy - 0.022, z + 0.395),
                          (cx - 0.002, cy - 0.022, z + 0.095),
                          (cx - 0.002, cy + 0.168, z + 0.105)],
                         [(0, 1, 2)], C)
    mlib.solidify(sail, 0.003, offset=0)
    mlib.set_mat(sail, M("M_PhoneWhite"))
    out.append(sail)
    return out


# The white riser that stands beside the peninsula in living_room.webp is a
# STAGE block - it is there to lift a camera or an actor, not because the
# apartment has one - and in the model it read as an unexplained white box
# fouling the barstools.  Deliberately not built.


# ================================================================== east wall

def wall_phone():
    """The white wall telephone on the pier between the fridge and the front
    door.

    A wall phone is a shallow BODY screwed flat to the plaster with the keypad
    on its face, and a handset that hangs VERTICALLY down that face on a hook
    at the top, covering the middle of the keys.  The first pass had the body
    and the handset side by side with the keypad hanging off the edge, which is
    a desk phone stood on end.

    The handset itself is two cups joined by a narrow waisted grip - that
    silhouette is the whole read of the object at this distance - and it hangs
    proud of the face, so it throws its own shadow onto the body.
    """
    out = []
    y, z = L.PHONE_Y, 1.44
    x = L.EX
    XF = x - 0.070                      # the body's front face
    HX = XF - 0.032                     # the handset's axis

    body = mlib.rounded_box("X_PhoneBody", XF, y - 0.086, z - 0.135,
                            x - 0.004, y + 0.086, z + 0.135, r=0.016, cname=C)
    mlib.bevel(body, 0.004, 3, 42)
    mlib.smooth_shade(body, 34)
    mlib.set_mat(body, M("M_PhoneWhite"))
    out.append(body)

    # recessed keypad well, then twelve keys standing in it
    well = mlib.box("X_PhoneWell", XF, y - 0.050, z - 0.104,
                    XF + 0.009, y + 0.050, z + 0.078, C)
    mlib.bevel(well, 0.002, 2, 40)
    mlib.set_mat(well, M("M_FoosGrip"))
    out.append(well)
    for r in range(4):
        for c in range(3):
            ky = y - 0.032 + c * 0.032
            kz = z + 0.062 - r * 0.044
            k = mlib.box("X_PhoneKey%d%d" % (r, c), XF - 0.002, ky - 0.0125,
                         kz - 0.0165, XF + 0.005, ky + 0.0125, kz + 0.0165, C)
            mlib.bevel(k, 0.0018, 2, 40)
            mlib.set_mat(k, M("M_PhoneWhite"))
            out.append(k)

    # the hook the earpiece hangs on, and the rest the mouthpiece sits against
    hook = mlib.rounded_box("X_PhoneHook", XF - 0.030, y - 0.021, z + 0.100,
                            XF + 0.002, y + 0.021, z + 0.124, r=0.008, cname=C)
    mlib.bevel(hook, 0.003, 2, 42)
    mlib.set_mat(hook, M("M_PhoneWhite"))
    out.append(hook)
    rest = mlib.rounded_box("X_PhoneRest", XF - 0.018, y - 0.024, z - 0.128,
                            XF + 0.002, y + 0.024, z - 0.108, r=0.007, cname=C)
    mlib.bevel(rest, 0.003, 2, 42)
    mlib.set_mat(rest, M("M_PhoneWhite"))
    out.append(rest)

    # the handset: earpiece cup, waisted grip, mouthpiece cup, hanging down
    hs = props.sweep_var("X_PhoneHS", [
        (HX, y, z + 0.146), (HX - 0.001, y, z + 0.116),
        (HX - 0.002, y, z + 0.066), (HX - 0.003, y, z + 0.004),
        (HX - 0.002, y, z - 0.060), (HX - 0.001, y, z - 0.112),
        (HX, y, z - 0.142)],
        [(0.030, 0.031), (0.031, 0.032), (0.017, 0.018), (0.0145, 0.0155),
         (0.017, 0.018), (0.031, 0.032), (0.029, 0.030)], 20, C, smooth=60)
    mlib.set_mat(hs, M("M_PhoneWhite"))
    out.append(hs)
    for (zz, nm) in ((z + 0.140, "ear"), (z - 0.136, "mouth")):
        cup = props.lathe("X_PhoneCup_" + nm, [
            (0.0, 0.0), (0.024, 0.0), (0.026, 0.005), (0.022, 0.010),
            (0.0, 0.010)], 22, C)
        props.face_x(cup, -1.0, (HX - 0.024, y, zz))
        mlib.set_mat(cup, M("M_FoosGrip"))
        out.append(cup)

    # the coiled cord, out of the body's bottom edge and hanging in a helix
    coil = []
    for k in range(96):
        t = k / 95.0
        a = t * math.tau * 9.0
        coil.append((XF - 0.010 - 0.024 * (1.0 - math.cos(a)) * 0.5,
                     y + 0.044 + 0.028 * math.sin(a),
                     z - 0.152 - t * 0.36))
    cd = mlib.tube_along("X_PhoneCord", coil, mlib.circle(0.0040, 6), cname=C)
    mlib.smooth_shade(cd, 52)
    mlib.set_mat(cd, M("M_PhoneWhite"))
    out.append(cd)
    tail = mlib.tube_along("X_PhoneCordT", [
        (XF - 0.006, y + 0.044, z - 0.128), (XF - 0.010, y + 0.044, z - 0.152)],
        mlib.circle(0.0040, 6), cname=C)
    mlib.smooth_shade(tail, 52)
    mlib.set_mat(tail, M("M_PhoneWhite"))
    out.append(tail)
    return out


def _mop_head(name, cx, cy, ztop, drop, seed=3, n_out=34, n_in=22):
    """A yarn mop head: a ferrule, a core, and a bundle of strands hanging the
    full drop with a ragged hem.

    The strands are what make a mop a mop - a single tapered solid is a golf
    club, which is exactly what the first version of this object was, and no
    amount of shaping the solid fixes it, because the read comes from the
    silhouette being ragged rather than smooth.

    Hung on a wall the yarn hangs PLUMB and barely spreads: it flares from the
    ferrule's 32 mm to about 55 at the hem and no further, and every strand
    ends at its own height.
    """
    rng = random.Random(seed)
    parts = []
    # the pressed metal ferrule that clamps the yarn to the handle
    fer = props.lathe(name + "_f", [(0.0, 0.0), (0.021, 0.0), (0.023, 0.012),
                                    (0.031, 0.022), (0.032, 0.070),
                                    (0.024, 0.084), (0.0, 0.086)], 18, C)
    mlib.translate(fer, (cx, cy, ztop - 0.070))
    mlib.set_mat(fer, M("M_Rod"))
    parts.append(fer)
    # a core, so the head is not see-through between the strands - stopped
    # well short of the hem, where the strands are all that should be left
    core = props.sweep_var(name + "_c", [
        (cx, cy, ztop - 0.010), (cx, cy, ztop - 0.070),
        (cx, cy, ztop - drop * 0.42), (cx, cy, ztop - drop * 0.66)],
        [(0.024, 0.024), (0.030, 0.030), (0.032, 0.032), (0.028, 0.028)],
        16, C, smooth=54)
    mlib.set_mat(core, M("M_MopYarn"))
    parts.append(core)

    def strands(count, r0, flare0, flare1, rad, tag):
        for k in range(count):
            a = math.tau * k / count + rng.uniform(-0.09, 0.09)
            drift = rng.uniform(-0.26, 0.26)
            flare = rng.uniform(flare0, flare1)
            ln = drop * rng.uniform(0.82, 1.0)      # the hem is never level

            def at(t, rr, aa):
                return (cx + rr * math.cos(aa), cy + rr * math.sin(aa), t)
            path = [at(ztop - 0.014, r0 * 0.70, a),
                    at(ztop - 0.062, r0, a + drift * 0.10),
                    at(ztop - ln * 0.38, r0 * 1.04 + flare * 0.26,
                       a + drift * 0.34),
                    at(ztop - ln * 0.72, r0 * 1.08 + flare * 0.66,
                       a + drift * 0.68),
                    at(ztop - ln, r0 * 1.10 + flare, a + drift)]
            s = mlib.tube_along(name + tag + str(k), path,
                                mlib.circle(rad, 6), cname=C)
            mlib.smooth_shade(s, 50)
            mlib.set_mat(s, M("M_MopYarn"))
            parts.append(s)

    strands(n_out, 0.025, 0.012, 0.032, 0.0040, "_s")
    strands(n_in, 0.013, 0.006, 0.020, 0.0036, "_t")
    return parts


def mops():
    """Two mops HUNG on the wall beside the bathroom door.

    Hung, they are plumb.  Propped against the wall they were vertical enough
    to read as hanging and tilted enough to look wrong doing it, which is the
    worst of both - so they are properly hung instead: a bracket each, the
    handle's own end ring over the hook, and the head swinging clear of the
    floor.  The bracket stands 78 mm off the plaster, which is what gives the
    yarn room to hang without brushing the wall.
    """
    out = []
    HK = 1.780                 # the hooks' height
    STAND = 0.078              # how far the hook holds the handle off the wall
    FZ = 0.335                 # where the ferrule grips the handle
    for i, (bx, hl, drop) in enumerate(((3.12, 1.404, 0.330),
                                        (3.31, 1.462, 0.352))):
        parts = []
        # the bracket: a rose screwed to the plaster and a J-hook off it
        rose = props.lathe("X_MopRs%d" % i, [(0.0, 0.0), (0.020, 0.0),
                                             (0.021, 0.005), (0.016, 0.009),
                                             (0.0, 0.010)], 16, C)
        props.face_y(rose, -1.0, (bx, L.NY, HK))
        mlib.set_mat(rose, M("M_Rod"))
        parts.append(rose)
        hook = mlib.tube_along("X_MopHk%d" % i, [
            (bx, L.NY - 0.004, HK), (bx, L.NY - STAND * 0.62, HK),
            (bx, L.NY - STAND - 0.008, HK - 0.010),
            (bx, L.NY - STAND - 0.014, HK - 0.030),
            (bx, L.NY - STAND, HK - 0.044),
            (bx, L.NY - STAND + 0.020, HK - 0.040)],
            mlib.circle(0.0038, 8), cname=C)
        mlib.smooth_shade(hook, 48)
        mlib.set_mat(hook, M("M_Rod"))
        parts.append(hook)

        # The mop itself hangs PLUMB from the hook's throat.  Everything below
        # is built about the handle's axis and then dropped so the end ring
        # lands on the hook, which is what fixes its height.
        by = L.NY - STAND
        zr = HK - 0.026                       # the ring's centre, on the hook
        base = zr - (hl + 0.050)              # local z -> world z
        handle = mlib.tube_along("X_MopH%d" % i, [
            (bx, by, base + FZ - 0.090), (bx, by, base + 0.620),
            (bx, by, base + 1.020), (bx, by, base + hl)],
            mlib.circle(0.0125, 12), cname=C)
        mlib.smooth_shade(handle, 46)
        mlib.set_mat(handle, M("M_StickWood"))
        parts.append(handle)
        cap = props.lathe("X_MopC%d" % i, [(0.0, 0.0), (0.0128, 0.0),
                                           (0.0132, 0.030), (0.0100, 0.042),
                                           (0.0, 0.046)], 14, C)
        mlib.translate(cap, (bx, by, base + hl - 0.004))
        mlib.set_mat(cap, M("M_StickTape"))
        parts.append(cap)
        # the end ring, in the YZ plane so it can actually sit over the hook -
        # a ring in the plane of the wall could not be threaded onto it
        ring = props.torus("X_MopR%d" % i, 0.0092, 0.0024, 16, 6, C,
                           cx=bx, cy=by, cz=zr)
        mlib.rot_y(ring, math.pi * 0.5, (bx, by, zr))
        mlib.set_mat(ring, M("M_Rod"))
        parts.append(ring)
        parts += _mop_head("X_MopHd%d" % i, bx, by, base + FZ, drop,
                           seed=11 + i * 7)
        out += parts
    return out


# ================================================================== build

def build():
    mlib.purge("X_")
    mlib.coll(C)
    materials()
    foosball()
    bookcase()
    wall_phone()
    mops()
    return len([o for o in bpy.data.objects if o.name.startswith("X_")])
