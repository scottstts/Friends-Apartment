"""Joinery for every hole the shell leaves: storefront glazing, the entrance
doors, the interior openings and the back-of-house doors.

Each opening is built in the wall's own frame - u along the wall, v up, w into
the wall's thickness - so the same routine serves the square walls and the
45-degree entrance diagonal without any special-casing.

Nothing here is a plane laid on a wall.  A lining sits in the reveal, the
architrave stands proud of the plaster, the sash sits back inside the lining
and the glass sits back inside the sash, so every part has real thickness and
a real shadow line.
"""
import bpy, math, importlib
from mathutils import Vector
import mlib as M
import mats as T
import L
import build_shell as S

importlib.reload(M); importlib.reload(T); importlib.reload(L)

C = "Openings"


class Wallf:
    """The local frame of a straight wall: p0 -> p1 along u, +Z up, and w
    running from the wall's inner face into its thickness."""

    def __init__(self, p0, p1, t, side=+1):
        A, B = Vector((p0[0], p0[1], 0.0)), Vector((p1[0], p1[1], 0.0))
        self.d = (B - A)
        self.len = self.d.length
        self.d /= self.len
        self.n = Vector((-self.d.y, self.d.x, 0.0)) * side
        self.A = A
        self.t = t

    def P(self, u, v, w=0.0):
        p = self.A + self.d * u + self.n * w
        return (p.x, p.y, v)

    def prism(self, name, quad, w0, w1, cname=C):
        """Extrude a (u, v) polygon through the wall's thickness."""
        pts = [self.P(u, v, w0) for (u, v) in quad]
        pts2 = [self.P(u, v, w1) for (u, v) in quad]
        n = len(quad)
        faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, j + n, i + n))
        ob = M.mesh_obj(name, pts + pts2, faces, cname)
        M.recalc_normals(ob)
        return ob

    def board(self, name, u0, v0, u1, v1, w0, w1, cname=C):
        return self.prism(name, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)],
                          w0, w1, cname)


# ------------------------------------------------------------------ pieces

def lining(F, nm, u0, z0, u1, z1, d=0.03, sill=False):
    """The four boards that line a reveal.  They sit `d` in from each face so
    the plaster returns onto them rather than meeting them flush.

    The head and sill run the full width and the jambs stop against them, the
    way a joiner would actually cut them.  Running all four full length - as
    this did at first - overlaps them at the four corners, and every one of
    those overlaps is a coplanar face pair."""
    out = []
    w0, w1 = d, F.t - d
    jz0 = z0 + (0.032 if sill else 0.0)
    jz1 = z1 - 0.028
    out.append(F.board(nm + "_jL", u0, jz0, u0 + 0.028, jz1, w0, w1))
    out.append(F.board(nm + "_jR", u1 - 0.028, jz0, u1, jz1, w0, w1))
    out.append(F.board(nm + "_hd", u0, jz1, u1, z1, w0, w1))
    if sill:
        out.append(F.board(nm + "_sl", u0, z0, u1, z0 + 0.032, w0, w1))
    return out


def architrave(F, nm, u0, u1, z0, z1, wide=0.075, proj=0.022, w=0.0, foot=True):
    """A mitred casing standing proud of the wall face at w."""
    a, b = u0 - wide, u1 + wide
    c, e = z0 - (wide if foot else 0.0), z1 + wide
    # four mitred boards rather than one n-gon with a hole in it
    out = []
    segs = [((a, c), (b, c), (u1, z0), (u0, z0)) if foot else None,
            ((a, c), (u0, z0), (u0, z1), (a, e)),
            ((a, e), (u0, z1), (u1, z1), (b, e)),
            ((b, c), (b, e), (u1, z1), (u1, z0))]
    for i, s in enumerate(segs):
        if s is None:
            continue
        out.append(F.prism(nm + "_a%d" % i, list(s), w - proj, w))
    return out


def sash(F, nm, u0, u1, z0, z1, cols=1, rows=1, w=0.0, rail=0.052,
         bar=0.022, depth=0.048, glassmat=None, framemat=None):
    """A glazed sash: stiles, rails, glazing bars, and one pane of glass per
    light set back inside them."""
    out = []
    wf0, wf1 = w, w + depth
    out.append(F.board(nm + "_s0", u0, z0, u0 + rail, z1, wf0, wf1))
    out.append(F.board(nm + "_s1", u1 - rail, z0, u1, z1, wf0, wf1))
    out.append(F.board(nm + "_r0", u0 + rail, z0, u1 - rail, z0 + rail, wf0, wf1))
    out.append(F.board(nm + "_r1", u0 + rail, z1 - rail, u1 - rail, z1, wf0, wf1))
    iu0, iu1 = u0 + rail, u1 - rail
    iz0, iz1 = z0 + rail, z1 - rail
    for i in range(1, cols):
        u = iu0 + (iu1 - iu0) * i / cols
        out.append(F.board(nm + "_bv%d" % i, u - bar / 2, iz0, u + bar / 2, iz1,
                           wf0 + 0.006, wf1))
    for j in range(1, rows):
        z = iz0 + (iz1 - iz0) * j / rows
        out.append(F.board(nm + "_bh%d" % j, iu0, z - bar / 2, iu1, z + bar / 2,
                           wf0 + 0.006, wf1))
    if framemat:
        for o in out:
            M.set_mat(o, framemat)
    g = F.board(nm + "_glass", iu0 + 0.004, iz0 + 0.004, iu1 - 0.004,
                iz1 - 0.004, wf0 + 0.014, wf0 + 0.020)
    if glassmat:
        M.set_mat(g, glassmat)
    out.append(g)
    return out


def panel_door(F, nm, u0, u1, z0, z1, w=0.0, th=0.045, glazed=True,
               woodmat=None, glassmat=None, brassmat=None, hinge_left=True):
    """A shop door: a big single light over a raised bottom panel, with real
    stiles and rails and a proper bolection round the glass."""
    out = []
    st = 0.11
    br = 0.24          # bottom rail
    lr = 0.09
    out.append(F.board(nm + "_st0", u0, z0, u0 + st, z1, w, w + th))
    out.append(F.board(nm + "_st1", u1 - st, z0, u1, z1, w, w + th))
    out.append(F.board(nm + "_bot", u0 + st, z0, u1 - st, z0 + br, w, w + th))
    out.append(F.board(nm + "_lok", u0 + st, z0 + br + 0.86, u1 - st,
                       z0 + br + 0.86 + lr, w, w + th))
    out.append(F.board(nm + "_top", u0 + st, z1 - lr, u1 - st, z1, w, w + th))
    # the lower panel, set back on both faces with a bevelled field
    out.append(F.board(nm + "_pnl", u0 + st - 0.012, z0 + 0.05,
                       u1 - st + 0.012, z0 + br + 0.86,
                       w + 0.012, w + th - 0.012))
    if woodmat:
        for o in out:
            M.set_mat(o, woodmat)
    if glazed:
        g = F.board(nm + "_glass", u0 + st - 0.006, z0 + br + 0.86 + lr - 0.006,
                    u1 - st + 0.006, z1 - lr + 0.006, w + 0.016, w + 0.022)
        if glassmat:
            M.set_mat(g, glassmat)
        out.append(g)
    else:
        # A blank door needs a PANEL where the light would have been.  Left
        # out, the stiles and rails frame a hole and you look straight
        # through the leaf at the brickwork behind - which reads exactly like
        # a glazed door, only worse, because the "glass" is perfectly clear.
        up = F.board(nm + "_upnl", u0 + st - 0.012, z0 + br + 0.86 + lr,
                     u1 - st + 0.012, z1 - lr, w + 0.012, w + th - 0.012)
        if woodmat:
            M.set_mat(up, woodmat)
        out.append(up)
    # handle: a long brass pull, on the leading stile
    hu = (u1 - st * 0.5) if hinge_left else (u0 + st * 0.5)
    for k in (0, 1):
        ww = w - 0.028 if k == 0 else w + th + 0.028
        bar = M.tube_along(nm + "_pull%d" % k,
                           [F.P(hu, z0 + 0.86, ww), F.P(hu, z0 + 1.24, ww)],
                           M.circle(0.011, 12), cname=C)
        M.smooth_shade(bar, 40)
        M.set_mat(bar, brassmat)
        out.append(bar)
        for zz in (z0 + 0.86, z0 + 1.24):
            st2 = M.tube_along(nm + "_pl%d_%s" % (k, zz),
                               [F.P(hu, zz, w if k == 0 else w + th),
                                F.P(hu, zz, ww)],
                               M.circle(0.009, 10), cname=C)
            M.smooth_shade(st2, 40)
            M.set_mat(st2, brassmat)
            out.append(st2)
    return out


# ------------------------------------------------------------------ the build

def build():
    M.coll(C)
    mats = S.MATS
    green = mats['joinery']
    gl = mats['glass']
    wd = mats['wood_dark']
    brass = T.paint('metal_brass', 'BE9A4A', rough=0.24, coat=0.35)
    S.MATS['brass'] = brass

    # ---------------------------------------------------------- window bay
    F = Wallf((L.BAY_E, L.BAY_S), (L.BAY_E, L.BAY_DIAG_E), L.TW, side=-1)
    z0, z1 = L.STEP + L.STORE_SILL, L.STORE_HEAD
    for i, (a, b) in enumerate(L.BAY_WIN):
        u0, u1 = a - L.BAY_S, b - L.BAY_S
        for o in lining(F, "BayW%d" % i, u0, z0, u1, z1, sill=True):
            M.set_mat(o, green)
        for o in architrave(F, "BayW%d" % i, u0, u1, z0, z1, 0.062, 0.020, 0.0,
                            foot=False):
            M.set_mat(o, green)
        sill = F.board("BayW%d_stool" % i, u0, z0 - 0.055,
                       u1, z0 + 0.032, -0.075, -0.001)
        M.set_mat(sill, green)
        M.bevel(sill, 0.006, 2, 50)
        sash(F, "BayW%d" % i, u0 + 0.03, u1 - 0.03, z0 + 0.03, z1 - 0.03,
             cols=2, rows=1, w=L.TW * 0.42, glassmat=gl, framemat=green)
    # transom band over the whole east wall
    tu0, tu1 = L.TRAN_U
    for o in lining(F, "BayT", tu0, L.TRAN_BOT, tu1, L.TRAN_TOP):
        M.set_mat(o, green)
    sash(F, "BayT", tu0 + 0.02, tu1 - 0.02, L.TRAN_BOT + 0.02, L.TRAN_TOP - 0.02,
         cols=5, rows=1, w=L.TW * 0.42, glassmat=gl, framemat=green)

    # ---------------------------------------------------------- the entrance
    (dx, dy), dl = L.diag_dir()
    D = Wallf(L.DIAG_A, L.DIAG_B, L.TW, side=+1)
    eu0, eu1 = L.ENTRY_U
    for o in lining(D, "Entry", eu0, L.STEP, eu1, L.ENTRY_H):
        M.set_mat(o, green)
    for o in architrave(D, "Entry", eu0, eu1, L.STEP, L.ENTRY_H, 0.085, 0.026,
                        0.0, foot=False):
        M.set_mat(o, green)
    mid = (eu0 + eu1) * 0.5
    panel_door(D, "EntryL", eu0 + 0.03, mid - 0.005, L.STEP + 0.01,
               L.ENTRY_H - 0.03, w=L.TW * 0.5, woodmat=wd, glassmat=gl,
               brassmat=brass, hinge_left=True)
    panel_door(D, "EntryR", mid + 0.005, eu1 - 0.03, L.STEP + 0.01,
               L.ENTRY_H - 0.03, w=L.TW * 0.5, woodmat=wd, glassmat=gl,
               brassmat=brass, hinge_left=False)
    for o in lining(D, "EntryT", eu0, L.TRAN_BOT, eu1, L.TRAN_TOP):
        M.set_mat(o, green)
    sash(D, "EntryT", eu0 + 0.02, eu1 - 0.02, L.TRAN_BOT + 0.02,
         L.TRAN_TOP - 0.02, cols=3, rows=1, w=L.TW * 0.42, glassmat=gl,
         framemat=green)
    # the shop window on the far side of the doors, towards the corner
    su0, su1 = L.DIAG_WIN
    for o in lining(D, "DiagW", su0, L.STEP + L.STORE_SILL, su1, L.STORE_HEAD):
        M.set_mat(o, green)
    sash(D, "DiagW", su0 + 0.03, su1 - 0.03, L.STEP + L.STORE_SILL + 0.03,
         L.STORE_HEAD - 0.03, cols=1, rows=1, w=L.TW * 0.42, glassmat=gl,
         framemat=green)

    # ------------------------------------------- street windows, main room
    E = Wallf((L.EX, -L.TW), (L.EX, L.BAY_S), L.TW, side=-1)
    u0, u1 = L.TW + L.E_WIN_S[0], L.TW + L.E_WIN_S[1]
    for o in lining(E, "EWinS", u0, L.STORE_SILL, u1, L.STORE_HEAD, sill=True):
        M.set_mat(o, green)
    for o in architrave(E, "EWinS", u0, u1, L.STORE_SILL, L.STORE_HEAD,
                        0.062, 0.020, 0.0, foot=False):
        M.set_mat(o, green)
    sash(E, "EWinS", u0 + 0.03, u1 - 0.03, L.STORE_SILL + 0.03,
         L.STORE_HEAD - 0.03, cols=2, rows=2, w=L.TW * 0.42, glassmat=gl,
         framemat=green)

    E2 = Wallf((L.EX, L.PIER[1]), (L.EX, L.NY + L.TP), L.TW, side=-1)
    u0, u1 = L.E_WIN_N[0] - L.PIER[1], L.E_WIN_N[1] - L.PIER[1]
    for o in lining(E2, "EWinN", u0, L.STORE_SILL, u1, L.STORE_HEAD, sill=True):
        M.set_mat(o, green)
    for o in architrave(E2, "EWinN", u0, u1, L.STORE_SILL, L.STORE_HEAD,
                        0.062, 0.020, 0.0, foot=False):
        M.set_mat(o, green)
    sash(E2, "EWinN", u0 + 0.03, u1 - 0.03, L.STORE_SILL + 0.03,
         L.STORE_HEAD - 0.03, cols=2, rows=2, w=L.TW * 0.42, glassmat=gl,
         framemat=green)

    # ------------------------------------ the doorway through to the lobby
    N = Wallf((0.0, L.NY), (L.EX + L.TW, L.NY), L.TP, side=+1)
    a, b = L.LOBBY_DR
    for o in lining(N, "Lobby", a, 0.0, b, L.LOBBY_H):
        M.set_mat(o, green)
    for o in architrave(N, "Lobby", a, b, 0.0, L.LOBBY_H, 0.085, 0.026, 0.0,
                        foot=False):
        M.set_mat(o, green)

    # ---------------------------------------------------------- back of house
    K = Wallf((L.KIT_CH[1][0], L.KIT_N), (-L.TW, L.KIT_N), L.TP, side=-1)
    a = L.KIT_CH[1][0] - L.KIT_DR[1]
    b = L.KIT_CH[1][0] - L.KIT_DR[0]
    for o in lining(K, "KitD", a, 0.0, b, L.DOOR_H):
        M.set_mat(o, green)
    for o in architrave(K, "KitD", a, b, 0.0, L.DOOR_H, 0.07, 0.020,
                        L.TP + 0.020,
                        foot=False):
        M.set_mat(o, green)
    panel_door(K, "KitDoor", a + 0.03, b - 0.03, 0.012, L.DOOR_H - 0.03,
               w=L.TP * 0.5, glazed=False, woodmat=wd, brassmat=brass)

    KS = Wallf((L.EX + 0.22, 0.0), (0.0, 0.0), L.TW, side=+1)
    a = L.EX + 0.22 - L.KIT_WIN[1]
    b = L.EX + 0.22 - L.KIT_WIN[0]
    for o in lining(KS, "KitW", a, 1.05, b, 2.30, sill=True):
        M.set_mat(o, green)
    sash(KS, "KitW", a + 0.03, b - 0.03, 1.08, 2.27, cols=2, rows=2,
         w=L.TW * 0.42, glassmat=gl, framemat=green)

    # both lavatory doors come off the hallway's north side
    H = Wallf((0.0, L.HALL_N), (L.WC_E, L.HALL_N), L.TP, side=+1)
    for nm, (a, b) in zip(("G", "L"), L.WC_DOORS):
        for o in lining(H, "WC" + nm, a, 0.0, b, L.DOOR_H):
            M.set_mat(o, green)
        for o in architrave(H, "WC" + nm, a, b, 0.0, L.DOOR_H, 0.07, 0.020,
                            0.0, foot=False):
            M.set_mat(o, green)
        panel_door(H, "WCDoor" + nm, a + 0.03, b - 0.03, 0.012,
                   L.DOOR_H - 0.03, w=L.TP * 0.5, glazed=False, woodmat=wd,
                   brassmat=brass)

    NW = Wallf((L.WC_E, L.WC_N), (0.0, L.WC_N), L.TW, side=-1)
    for i, (a, b) in enumerate([(L.WC_E - w1, L.WC_E - w0)
                                for (w0, w1) in L.WC_WIN]):
        for o in lining(NW, "WCw%d" % i, a, 1.35, b, 2.35, sill=True):
            M.set_mat(o, green)
        sash(NW, "WCw%d" % i, a + 0.025, b - 0.025, 1.375, 2.325, cols=1,
             rows=2, w=L.TW * 0.42, glassmat=gl, framemat=green)

    print("openings:", len([o for o in bpy.data.objects
                            if o.users_collection and
                            o.users_collection[0].name == C]))
