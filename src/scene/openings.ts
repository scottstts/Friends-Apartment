/** Assemble every door and window into the shell - port of build_openings.py. */
import type * as THREE from 'three/webgpu'
import * as L from '../lib/L'
import * as mlib from '../lib/mlib'
import { MeshData } from '../lib/mesh'
import * as mats from '../mats/mats'
import * as O from './sopenings'
import type { MatSet } from './shell'
import type { World } from './world'

function rad(d: number): number {
  return (d * Math.PI) / 180
}

function swingLeaf(
  w: World,
  width: number,
  h: number,
  hinge: [number, number],
  closedDir: [number, number],
  angle: number,
  M: MatSet,
  leafMat: THREE.Material,
  t = 0.042,
  rows: number[] = [0.3, 0.3, 0.2, 0.2],
): void {
  const leaf = O.panelDoor(width, h, t, rows, 0.11, 0.12, 0.082)
  mlib.rotateZ(leaf, Math.PI / 2)
  mlib.translate(leaf, [0.0, width / 2, 0.01])
  const knobs: MeshData[] = []
  for (const [sx, ang] of [
    [0.004, Math.PI / 2],
    [-t - 0.004, -Math.PI / 2],
  ] as [number, number][]) {
    const kn = O.knobSet()
    mlib.rotateZ(kn, ang)
    mlib.translate(kn, [sx, width - 0.125, 1.0])
    knobs.push(kn)
  }
  const base = Math.atan2(closedDir[1], closedDir[0]) - Math.PI / 2
  const theta = base - rad(angle)
  mlib.rotateZ(leaf, theta)
  mlib.translate(leaf, [hinge[0], hinge[1], 0.0])
  w.add(leaf, leafMat)
  for (const kn of knobs) {
    mlib.rotateZ(kn, theta)
    mlib.translate(kn, [hinge[0], hinge[1], 0.0])
    w.add(kn, M.brass)
  }
  // collider for the standing-open leaf
  const ax = -Math.sin(theta)
  const ay = Math.cos(theta)
  w.obb(hinge[0] + (ax * width) / 2, hinge[1] + (ay * width) / 2, width / 2, t / 2 + 0.01, Math.atan2(ay, ax))
}

export function mkMats(): MatSet {
  const M: MatSet = {}
  M.door_purple = mats.paint('paint_door_purple', L.DOOR_PURPLE, { rough: 0.3, coat: 0.3, variation: 0.02 })
  M.trim = mats.get('paint_lav_trim') ?? mats.paint('paint_lav_trim', L.LAV_TRIM)
  M.turq = mats.paint('paint_turquoise', L.TURQ, { rough: 0.3, coat: 0.22 })
  M.green_door = mats.paint('paint_green_door', L.GREEN_DOOR, { rough: 0.28, coat: 0.25 })
  M.gold = mats.paint('paint_gold_frame', L.GOLD, { rough: 0.34, coat: 0.3 })
  M.brass = mats.metal('metal_brass', 'B08D3A', { rough: 0.22, bump: 0.05 })
  M.chrome = mats.metal('metal_chrome', 'D8DCE0', { rough: 0.1, bump: 0.02 })
  M.steel_dk = mats.metal('metal_steel_dark', '3A322C', { rough: 0.34, bump: 0.06 })
  M.glass = mats.pane('glass_clear', { rough: 0.018, baseAlpha: 0.05, edge: 0.62 })
  M.glass_frost = mats.pane('glass_frosted', { tint: 'E4E8E2', rough: 0.5, baseAlpha: 0.8, edge: 0.18, bumpn: 280.0 })
  M.glass_dark = mats.pane('glass_dark', { tint: '2C2F36', rough: 0.06, baseAlpha: 0.62, edge: 0.34 })
  M.stone = mats.plaster('stone_sill', '8D897E', { rough: 0.62, bump: 0.5, scale: 48 })
  M.blind = mats.wood('blind_matchstick', ['DCC096', 'D3B78C', 'C9AC82'], {
    ring: 24.0,
    warp: 0.004,
    warpScale: 3.0,
    distort: 0.04,
    blotch: 0.16,
    bump: 0.2,
    rough: [0.52, 0.7],
    aniso: 0.0,
    axis: 'YZ',
    translucent: 0.34,
    grainRelief: 0.05,
  })
  return M
}

export function build(w: World, M?: MatSet): MatSet {
  M = M ?? mkMats()

  // ============================================================ FRONT DOOR
  {
    const width = L.FD_Y[1] - L.FD_Y[0]
    const top = L.FD_TOP
    const cy = (L.FD_Y[0] + L.FD_Y[1]) * 0.5
    const ln = O.lining(width, top, L.TW, 0.024)
    O.place(ln, [0.0, cy, 0.0], [0, 1], [-1, 0])
    w.add(ln, M.trim)
    const cs = O.casing(width, top, 0.1, 0.026)
    O.place(cs, [0.0, cy, 0.0], [0, 1], [1, 0])
    w.add(cs, M.trim)
    const cs2 = O.casing(width, top, 0.07, 0.016)
    O.place(cs2, [-L.TW, cy, 0.0], [0, 1], [-1, 0])
    w.add(cs2, M.trim)
    // transom: head rail + sash
    const hr = mlib.box(-width / 2, 0.0, L.FD_H, width / 2, L.TW, L.FD_H + 0.075)
    O.place(hr, [0.0, cy, 0.0], [0, 1], [-1, 0])
    w.add(hr, M.trim)
    const [tf, tg] = O.steelWindow(width - 0.048, top - L.FD_H - 0.085, [1], 1, {
      frameW: 0.048,
      frameD: 0.055,
      colsPerBay: 1,
      glassBack: 0.008,
    })
    for (const [o, mm] of [
      [tf, M.trim],
      [tg, M.glass_dark],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.FD_H + 0.085])
      O.place(o, [0.0, cy, 0.0], [0, 1], [-1, 0])
      w.add(o, mm)
    }
    // leaf
    const lw = width - 0.055
    const lh = L.FD_H - 0.03
    const leaf = O.flushDoor(lw, lh, 0.044)
    mlib.translate(leaf, [0, 0.075, 0.012])
    O.place(leaf, [0.0, cy, 0.0], [0, 1], [-1, 0])
    w.add(leaf, M.door_purple)
    // the yellow frame + peephole boss + hardware (all on the leaf face)
    const fx = -0.075
    const FW = 0.3
    const FH = 0.34
    const prof: [number, number][] = [
      [0.0, 0.0015],
      [0.0, 0.017],
      [0.006, 0.0225],
      [0.0155, 0.025],
      [0.0245, 0.0215],
      [0.03, 0.013],
      [0.0325, 0.006],
      [0.034, 0.0025],
      [0.034, 0.0015],
    ]
    const fr = mlib.sweepRectFrame(FW, FH, prof)
    mlib.smoothShade(fr, 34)
    O.place(fr, [fx, cy, 1.545], [0, 1], [1, 0])
    w.add(fr, M.gold)
    // spyhole above the frame
    const ph = mlib.revolve(
      [
        [0.0, 0.0],
        [0.009, 0.0],
        [0.009, 0.006],
        [0.005, 0.008],
        [0.0, 0.008],
      ],
      16,
    )
    mlib.rotX(ph, -Math.PI / 2)
    O.place(ph, [fx, cy, 1.79], [0, 1], [1, 0])
    w.add(ph, M.brass)
    // knocker: back-plate and ring
    const kp = mlib.revolve(
      [
        [0.0, 0.0],
        [0.034, 0.0],
        [0.034, 0.007],
        [0.026, 0.013],
        [0.0, 0.015],
      ],
      24,
    )
    mlib.rotX(kp, -Math.PI / 2)
    mlib.smoothShade(kp, 40)
    O.place(kp, [fx, cy, 1.29], [0, 1], [1, 0])
    w.add(kp, M.brass)
    const ring = mlib.tubeAlong(
      Array.from({ length: 20 }, (_, k) => {
        const a = (k * Math.PI * 2) / 20
        return [0.03 * Math.cos(a), 0.03 * Math.sin(a), 0.0] as [number, number, number]
      }),
      mlib.circle(0.0055, 8),
      { closePath: true },
    )
    mlib.rotX(ring, -Math.PI / 2)
    mlib.translate(ring, [0.0, 0.0, -0.036])
    mlib.smoothShade(ring, 38)
    O.place(ring, [fx + 0.013, cy, 1.29], [0, 1], [1, 0])
    w.add(ring, M.brass)
    const kn = O.knobSet()
    O.place(kn, [fx, L.FD_Y[0] + 0.11, 1.0], [0, 1], [1, 0])
    w.add(kn, M.brass)
    // the stack of locks up the latch stile
    for (const [zz, rr2] of [
      [1.415, 0.026],
      [1.135, 0.022],
    ] as [number, number][]) {
      const db = mlib.revolve(
        [
          [0.0, 0.0],
          [rr2 * 1.35, 0.0],
          [rr2 * 1.35, 0.008],
          [rr2, 0.014],
          [rr2, 0.03],
          [rr2 * 0.45, 0.036],
          [0.0, 0.038],
        ],
        18,
      )
      mlib.rotX(db, -Math.PI / 2)
      mlib.smoothShade(db, 40)
      O.place(db, [fx, L.FD_Y[0] + 0.105, zz], [0, 1], [1, 0])
      w.add(db, M.brass)
    }
    const sb = mlib.prism(mlib.roundedRect(0.115, 0.048, 0.008, 3), 0.0, 0.009)
    mlib.rotX(sb, -Math.PI / 2)
    O.place(sb, [fx, L.FD_Y[0] + 0.095, 1.265], [0, 1], [1, 0])
    w.add(sb, M.brass)
    const cpl = mlib.prism(mlib.roundedRect(0.03, 0.075, 0.008, 3), 0.0, 0.007)
    mlib.rotX(cpl, -Math.PI / 2)
    O.place(cpl, [fx, L.FD_Y[0] + 0.085, 1.585], [0, 1], [1, 0])
    w.add(cpl, M.brass)
    const slack: [number, number, number][] = [[0.0, 0.0, 0.0]]
    for (let k = 1; k < 9; k++) {
      const t = k / 8.0
      slack.push([-0.012 - 0.01 * Math.sin(t * Math.PI), 0.105 * t, -0.055 * Math.sin(t * Math.PI) - 0.004 * t])
    }
    const chn = mlib.tubeAlong(slack, mlib.circle(0.0035, 6))
    mlib.smoothShade(chn, 38)
    O.place(chn, [fx, L.FD_Y[0] + 0.085, 1.585], [0, 1], [1, 0])
    w.add(chn, M.brass)
  }

  // ========================================================= KITCHEN WINDOW
  {
    const { dir, len: cl } = L.chamferDir()
    const [dxc, dyc] = dir
    const kw = L.KW_U[1] - L.KW_U[0]
    const kh = L.KW_Z[1] - L.KW_Z[0]
    const kc = L.chamferPt((L.KW_U[0] + L.KW_U[1]) * 0.5, 0.0)
    const inw: [number, number] = [dyc, -dxc]
    const kl = O.lining(kw, kh, L.TW, 0.022)
    O.place(kl, [kc[0], kc[1], L.KW_Z[0]], [dxc, dyc], [-inw[0], -inw[1]])
    w.add(kl, M.turq)
    const kcs = O.casing(kw, kh, 0.105, 0.022, 4)
    mlib.translate(kcs, [0, 0, -kh * 0.5])
    O.place(kcs, [kc[0], kc[1], L.KW_Z[0] + kh * 0.5], [dxc, dyc], inw)
    w.add(kcs, M.turq)
    const [kf, kg] = O.steelWindow(kw - 0.03, kh - 0.03, [1], 4, {
      frameW: 0.05,
      frameD: 0.062,
      munW: 0.026,
      munD: 0.03,
      colsPerBay: 2,
      glassBack: 0.014,
    })
    for (const [o, mm] of [
      [kf, M.turq],
      [kg, M.glass],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.KW_Z[0] + 0.015])
      O.place(o, [kc[0], kc[1], 0.0], [dxc, dyc], [-inw[0], -inw[1]])
      w.add(o, mm)
    }
    const sl = mlib.box(-kw / 2 - 0.05, 0.0, -0.05, kw / 2 + 0.05, 0.18, 0.0)
    mlib.bevel(sl, 0.006, 2)
    O.place(sl, [kc[0], kc[1], L.KW_Z[0]], [dxc, dyc], [-inw[0], -inw[1]])
    w.add(sl, M.stone)
    void cl
  }

  // ============================================================ HUGE WINDOW
  {
    const bw = L.BW_X[1] - L.BW_X[0]
    const bcx = (L.BW_X[0] + L.BW_X[1]) * 0.5
    const slopeLen = (L.BW_HEAD - L.BW_SILL) / Math.cos(L.BW_TILT)
    const [bf, bg] = O.steelWindow(bw - 0.02, slopeLen - 0.01, [1, 1.15, 1], 7, {
      frameW: 0.068,
      frameD: 0.075,
      mullW: 0.055,
      munW: 0.026,
      munD: 0.032,
      colsPerBay: 2,
      glassBack: 0.018,
    })
    for (const [o, mm] of [
      [bf, M.steel_dk],
      [bg, M.glass],
    ] as [MeshData, THREE.Material][]) {
      // One continuous near-vertical window; its head leans south into the room.
      mlib.rotX(o, L.BW_TILT)
      O.place(o, [bcx, 0.0, 0.0], [1, 0], [0, 1])
      mlib.translate(o, [0, L.AL_Y[1] - 0.008, L.BW_SILL + 0.006])
      w.add(o, mm)
    }
    // Triangular plaster reveals close the leaned glazing at each jamb.
    for (const [a, b] of [
      [L.BW_X[0] - 0.075, L.BW_X[0] + 0.012],
      [L.BW_X[1] - 0.012, L.BW_X[1] + 0.075],
    ] as [number, number][]) {
      w.add(
        mlib.prismYZ(
          [
            [L.NYW, L.BW_SILL],
            [L.NYW, L.BW_HEAD],
            [L.NYW - L.BW_LEAN, L.BW_HEAD],
          ],
          a,
          b,
        ),
        mats.get('wall_lavender')!,
      )
    }
    // stone sill inside + out
    const si = mlib.box(L.BW_X[0] - 0.06, L.AL_Y[1] - 0.02, L.BW_SILL - 0.055, L.BW_X[1] + 0.06, L.AL_Y[1] + L.TW + 0.1, L.BW_SILL)
    mlib.bevel(si, 0.008, 2)
    w.add(si, M.stone)
    // Matchstick blinds hang down the upper half of the single leaned window.
    const PITCH = 0.0175
    const SLAT = 0.0128
    const THK = 0.0075
    const spans: [number, number][] = [
      [L.BW_X[0] + 0.03, L.BW_X[0] + bw / 3 - 0.02],
      [L.BW_X[0] + bw / 3 + 0.02, L.BW_X[0] + (2 * bw) / 3 - 0.02],
      [L.BW_X[0] + (2 * bw) / 3 + 0.02, L.BW_X[1] - 0.03],
    ]
    spans.forEach(([a, b], i) => {
      const t = i !== 1 ? 0.5 : 0.58
      const uy = Math.sin(L.BW_TILT)
      const uz = -Math.cos(L.BW_TILT)
      const ny = uz
      const nz = -uy
      const y0 = L.NYW - L.BW_LEAN + ny * 0.055
      const z0 = L.BW_HEAD - 0.055
      const run = slopeLen * t
      const slats: MeshData[] = []
      const n = Math.max(2, Math.floor(run / PITCH))
      for (let k = 0; k < n; k++) {
        const s0 = k * PITCH
        const s1 = Math.min(s0 + SLAT, run)
        const quad: [number, number][] = []
        for (const [s, o] of [
          [s0, -THK / 2],
          [s1, -THK / 2],
          [s1, THK / 2],
          [s0, THK / 2],
        ] as [number, number][]) {
          quad.push([y0 + uy * s + ny * o, z0 + uz * s + nz * o])
        }
        slats.push(mlib.prismYZ(quad, a, b))
      }
      for (const [s, hh] of [
        [-0.012, 0.026],
        [run + 0.004, 0.03],
      ] as [number, number][]) {
        const quad: [number, number][] = [
          [y0 + uy * s + ny * -0.011, z0 + uz * s + nz * -0.011],
          [y0 + uy * (s + hh) + ny * -0.011, z0 + uz * (s + hh) + nz * -0.011],
          [y0 + uy * (s + hh) + ny * 0.011, z0 + uz * (s + hh) + nz * 0.011],
          [y0 + uy * s + ny * 0.011, z0 + uz * s + nz * 0.011],
        ]
        slats.push(mlib.prismYZ(quad, a, b))
      }
      w.add(mlib.join(slats), M.blind)
    })
  }

  // ================= BATHROOM DOOR (hallway west wall, faces east) ========
  {
    const bdw = L.BD_Y[1] - L.BD_Y[0]
    const bdc = (L.BD_Y[0] + L.BD_Y[1]) * 0.5
    const bl = O.lining(bdw, L.BD_H, 0.16, 0.022)
    O.place(bl, [L.HALL_X[0], bdc, 0.0], [0, -1], [-1, 0])
    w.add(bl, M.trim)
    const bcs = O.casing(bdw, L.BD_H, 0.09, 0.022)
    O.place(bcs, [L.HALL_X[0], bdc, 0.0], [0, -1], [1, 0])
    w.add(bcs, M.trim)
    // Pivot on the jamb arris so the leaf can stand back against its own wall;
    // 165 degrees leaves clearance behind the knob and keeps the basin clear.
    swingLeaf(w, bdw - 0.05, L.BD_H - 0.028, [L.HALL_WW[0] - 0.006, L.BD_Y[1] - 0.024], [0.0, -1.0], 165.0, M, M.trim, 0.04)
  }

  // ============ CLOSET DOOR (green, head of the hallway, faces south) =====
  {
    const clw = L.CL_X[1] - L.CL_X[0]
    const clc = (L.CL_X[0] + L.CL_X[1]) * 0.5
    const cll = O.lining(clw, L.CL_H, 0.3, 0.022)
    O.place(cll, [clc, L.NW_Y, 0.0], [1, 0], [0, 1])
    w.add(cll, M.green_door)
    const clcs = O.casing(clw, L.CL_H, 0.092, 0.024)
    O.place(clcs, [clc, L.NW_Y, 0.0], [1, 0], [0, -1])
    w.add(clcs, M.green_door)
    const cld = O.panelDoor(clw - 0.05, L.CL_H - 0.028, 0.04, [0.28, 0.28, 0.22, 0.22], 0.108, 0.118, 0.082)
    mlib.translate(cld, [0, 0.04, 0.01])
    O.place(cld, [clc, L.NW_Y, 0.0], [1, 0], [0, 1])
    w.add(cld, M.green_door)
    const kn3 = O.knobSet()
    O.place(kn3, [L.CL_X[1] - 0.13, L.NW_Y - 0.04, 1.0], [1, 0], [0, -1])
    w.add(kn3, M.brass)
  }

  // ============ RACHEL'S DOORWAY: cased opening + transom =================
  {
    const TWALL = L.EXW - L.EX
    const cdw = L.CD_Y[1] - L.CD_Y[0]
    const cdc = (L.CD_Y[0] + L.CD_Y[1]) * 0.5
    const cl2 = O.lining(cdw, L.CD_TOP, TWALL, 0.024)
    O.place(cl2, [L.EX, cdc, 0.0], [0, -1], [1, 0])
    w.add(cl2, M.trim)
    const ccs = O.casing(cdw, L.CD_TOP, 0.1, 0.026)
    O.place(ccs, [L.EX, cdc, 0.0], [0, -1], [-1, 0])
    w.add(ccs, M.trim)
    const ccs2 = O.casing(cdw, L.CD_TOP, 0.075, 0.018)
    O.place(ccs2, [L.EXW, cdc, 0.0], [0, -1], [1, 0])
    w.add(ccs2, M.trim)
    const hr2 = mlib.box(-cdw / 2, 0.0, L.CD_H, cdw / 2, TWALL, L.CD_H + 0.075)
    O.place(hr2, [L.EX, cdc, 0.0], [0, -1], [1, 0])
    w.add(hr2, M.trim)
    const [tf2, tg2] = O.steelWindow(cdw - 0.048, L.CD_TOP - L.CD_H - 0.085, [1], 1, {
      frameW: 0.046,
      frameD: 0.05,
      colsPerBay: 1,
      glassBack: 0.008,
    })
    for (const [o, mm] of [
      [tf2, M.trim],
      [tg2, M.glass_frost],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.CD_H + 0.085])
      O.place(o, [L.EX, cdc, 0.0], [0, -1], [1, 0])
      w.add(o, mm)
    }
    // Rachel's leaf, standing open into her room (hinged on the north jamb)
    swingLeaf(w, cdw - 0.055, L.CD_H - 0.03, [L.EX + 0.052, L.CD_Y[1] - 0.028], [0.0, -1.0], -104.0, M, M.trim)
  }

  // ===== MONICA'S BEDROOM DOOR: south of the alcove, with frosted transom ===
  {
    const TWALL = L.EXW - L.EX
    const mdw = L.MD_Y[1] - L.MD_Y[0]
    const mdc = (L.MD_Y[0] + L.MD_Y[1]) * 0.5
    const ml2 = O.lining(mdw, L.MD_TOP, TWALL, 0.024)
    O.place(ml2, [L.EX, mdc, 0.0], [0, -1], [1, 0])
    w.add(ml2, M.trim)
    const mcs = O.casing(mdw, L.MD_TOP, 0.095, 0.024)
    O.place(mcs, [L.EX, mdc, 0.0], [0, -1], [-1, 0])
    w.add(mcs, M.trim)
    const mcs2 = O.casing(mdw, L.MD_TOP, 0.08, 0.02)
    O.place(mcs2, [L.EXW, mdc, 0.0], [0, -1], [1, 0])
    w.add(mcs2, M.trim)
    const hr3 = mlib.box(-mdw / 2, 0.0, L.MD_H, mdw / 2, TWALL, L.MD_H + 0.075)
    O.place(hr3, [L.EX, mdc, 0.0], [0, -1], [1, 0])
    w.add(hr3, M.trim)
    const [tf3, tg3] = O.steelWindow(mdw - 0.048, L.MD_TOP - L.MD_H - 0.085, [1], 1, {
      frameW: 0.046,
      frameD: 0.05,
      colsPerBay: 1,
      glassBack: 0.008,
    })
    for (const [o, mm] of [
      [tf3, M.trim],
      [tg3, M.glass_frost],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, L.MD_H + 0.085])
      O.place(o, [L.EX, mdc, 0.0], [0, -1], [1, 0])
      w.add(o, mm)
    }
    // left standing open, swinging east into the bedroom (hinged south jamb)
    swingLeaf(w, mdw - 0.055, L.MD_H - 0.03, [L.EX + 0.052, L.MD_Y[0] + 0.028], [0.0, 1.0], 104.0, M, M.trim)
  }

  // ============================= bedroom windows ==========================
  for (const cy of [L.RB_WIN_Y, L.MB_WIN_Y]) {
    const bw = 1.24
    const bh = 1.38
    const wl = O.lining(bw, bh, L.TW, 0.022)
    mlib.translate(wl, [0, 0, 0.86])
    O.place(wl, [L.EXT_E, cy, 0.0], [0, 1], [1, 0])
    w.add(wl, M.trim)
    const wcs = O.casing(bw, bh, 0.09, 0.02, 4)
    mlib.translate(wcs, [0, 0, 0.86 + bh * 0.5])
    O.place(wcs, [L.EXT_E, cy, 0.0], [0, 1], [-1, 0])
    w.add(wcs, M.trim)
    const [wf, wg] = O.steelWindow(bw - 0.03, bh - 0.03, [1], 3, {
      frameW: 0.048,
      frameD: 0.06,
      munW: 0.024,
      munD: 0.028,
      colsPerBay: 2,
      glassBack: 0.014,
    })
    for (const [o, mm] of [
      [wf, M.trim],
      [wg, M.glass],
    ] as [MeshData, THREE.Material][]) {
      mlib.translate(o, [0, 0, 0.875])
      O.place(o, [L.EXT_E, cy, 0.0], [0, 1], [1, 0])
      w.add(o, mm)
    }
    const sl2 = mlib.box(-bw / 2 - 0.06, -0.02, -0.055, bw / 2 + 0.06, 0.2, 0.0)
    mlib.bevel(sl2, 0.006, 2)
    mlib.translate(sl2, [0, 0, 0.86])
    O.place(sl2, [L.EXT_E, cy, 0.0], [0, 1], [1, 0])
    w.add(sl2, M.stone)
  }
  return M
}
