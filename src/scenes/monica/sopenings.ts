/** Doors, windows, casings, sashes, glazing, hardware - port of s_openings.py. */
import * as mlib from '../../lib/mlib'
import { MeshData, type Vec2 } from '../../lib/mesh'

/** Map local (x,y,z) so local +X -> xdir (2D), +Y -> ydir, +Z -> up. */
export function place(ob: MeshData, origin: [number, number, number], xdir: Vec2, ydir?: Vec2): MeshData {
  let [ux, uy] = xdir
  const n = Math.hypot(ux, uy)
  ux /= n
  uy /= n
  let vx: number, vy: number
  if (!ydir) {
    vx = -uy
    vy = ux
  } else {
    ;[vx, vy] = ydir
    const n2 = Math.hypot(vx, vy)
    vx /= n2
    vy /= n2
  }
  mlib.transform4(ob, [
    [ux, vx, 0, origin[0]],
    [uy, vy, 0, origin[1]],
    [0, 0, 1, origin[2]],
    [0, 0, 0, 1],
  ])
  mlib.recalcNormals(ob)
  return ob
}

// --------------------------------------------------------------------- casings

export function casingProfile(cw = 0.095, proud = 0.024): Vec2[] {
  const h = cw * 0.5
  return [
    [-h, 0.0012],
    [-h, proud * 1.1],
    [-h + 0.008, proud * 1.3],
    [-h + 0.017, proud * 1.3],
    [-h + 0.023, proud * 0.88],
    [h - 0.02, proud * 0.72],
    [h - 0.014, proud * 0.98],
    [h - 0.004, proud * 0.98],
    [h, proud * 0.55],
    [h, 0.0012],
  ]
}

/** Mitred architrave around an opening of clear size w x h whose bottom sits
 * at local z = 0.  Built in the XZ plane, +Y proud into the room.
 * sides=3 -> two legs and a head (no threshold). */
export function casing(w: number, h: number, cw = 0.095, proud = 0.024, sides = 3, prof?: Vec2[]): MeshData {
  const p = prof ?? casingProfile(cw, proud)
  const hw = w * 0.5 + cw * 0.5
  const r2 = Math.SQRT2
  if (sides === 4) {
    const ob = mlib.sweepRectFrame(w + cw, h + cw, p)
    mlib.translate(ob, [0, 0, h * 0.5])
    mlib.recalcNormals(ob)
    return ob
  }
  const top = h + cw * 0.5
  const corners: [number, number, [number, number], number][] = [
    [-hw, 0.0, [-1.0, 0.0], 1.0],
    [-hw, top, [-0.70711, 0.70711], r2],
    [hw, top, [0.70711, 0.70711], r2],
    [hw, 0.0, [1.0, 0.0], 1.0],
  ]
  const rings = corners.map(([cx, cz, [ox, oz], sc]) =>
    p.map(([a, b]) => [cx + ox * a * sc, b, cz + oz * a * sc] as [number, number, number]),
  )
  return mlib.loft(rings, { closeV: true, capStart: true, capEnd: true })
}

/** Box lining inside a reveal: two jambs + head, set flush with the reveal. */
export function lining(w: number, h: number, depth: number, t = 0.026): MeshData {
  return mlib.join([
    mlib.box(-w / 2, 0.0, 0.0, -w / 2 + t, depth, h),
    mlib.box(w / 2 - t, 0.0, 0.0, w / 2, depth, h),
    mlib.box(-w / 2, 0.0, h - t, w / 2, depth, h),
  ])
}

// ----------------------------------------------------------------------- doors

export function flushDoor(w: number, h: number, t = 0.042): MeshData {
  const ob = mlib.box(-w / 2, 0.0, 0.0, w / 2, t, h)
  mlib.bevel(ob, 0.003, 2)
  return ob
}

/** Stile-and-rail door.  Panels are housed behind the frame. */
export function panelDoor(
  w: number,
  h: number,
  t = 0.042,
  rows: number[] = [0.3, 0.3, 0.2, 0.2],
  stile = 0.115,
  rail = 0.115,
  mid = 0.085,
): MeshData {
  const tot = rows.reduce((a, b) => a + b, 0)
  const innerH = h - 2 * rail - (rows.length - 1) * mid
  const holes: [number, number, number, number][] = []
  let z = rail
  for (const r of rows) {
    const hh = innerH * (r / tot)
    holes.push([stile, z, w - stile, z + hh])
    z += hh + mid
  }
  const frame = mlib.panelWithHoles(w, h, t, holes)
  mlib.translate(frame, [-w / 2, 0, 0])
  const parts: MeshData[] = [frame]
  for (const [x0, z0, x1, z1] of holes) {
    const pt = 0.016
    const pan = mlib.box(x0 - 0.014 - w / 2, t * 0.34, z0 - 0.014, x1 + 0.014 - w / 2, t * 0.34 + pt, z1 + 0.014)
    mlib.bevel(pan, 0.004, 2)
    parts.push(pan)
    // sticking (bead) around the opening, front face
    const bd = mlib.sweepRectFrame(x1 - x0 + 0.013, z1 - z0 + 0.013, [
      [-0.0075, 0.0006],
      [0.0075, 0.0006],
      [0.0075, 0.0075],
      [0.002, 0.0115],
      [-0.0075, 0.01],
    ])
    mlib.translate(bd, [(x0 + x1) / 2 - w / 2, 0.0, (z0 + z1) / 2])
    mlib.recalcNormals(bd)
    parts.push(bd)
  }
  return mlib.join(parts)
}

// --------------------------------------------------------------------- windows

export interface SteelWindowOpts {
  frameW?: number
  frameD?: number
  mullW?: number
  munW?: number
  munD?: number
  colsPerBay?: number
  glassBack?: number
}

/** Multi-pane steel/timber window.  Local: XZ plane centred at (0, *, h/2),
 * +Y into the room.  bays = list of relative widths.  Returns [frame, glass]. */
export function steelWindow(w: number, h: number, bays: number[], rows: number, o: SteelWindowOpts = {}): [MeshData, MeshData] {
  const { frameW = 0.052, frameD = 0.062, mullW = 0.04, munW = 0.02, munD = 0.026, colsPerBay = 2, glassBack = 0.012 } = o
  const parts: MeshData[] = []
  const hw = w / 2
  const hh = h / 2
  const fp: Vec2[] = [
    [-frameW / 2, 0.0],
    [frameW / 2, 0.0],
    [frameW / 2, frameD],
    [-frameW / 2, frameD],
  ]
  const of = mlib.sweepRectFrame(w - frameW, h - frameW, fp)
  mlib.translate(of, [0, 0, hh])
  parts.push(of)
  const tot = bays.reduce((a, b) => a + b, 0)
  const xs: number[] = [-hw]
  let acc = 0
  for (const bb of bays) {
    acc += bb
    xs.push(-hw + (w * acc) / tot)
  }
  for (const x of xs.slice(1, -1)) {
    parts.push(mlib.box(x - mullW / 2, 0.0, frameW, x + mullW / 2, frameD, h - frameW))
  }
  for (let k = 0; k < bays.length; k++) {
    const x0 = xs[k] + (k === 0 ? frameW : mullW / 2)
    const x1 = xs[k + 1] - (k === bays.length - 1 ? frameW : mullW / 2)
    const bw = x1 - x0
    for (let c = 1; c < colsPerBay; c++) {
      const xc = x0 + (bw * c) / colsPerBay
      parts.push(mlib.box(xc - munW / 2, 0.0, frameW, xc + munW / 2, munD, h - frameW))
    }
    for (let r = 1; r < rows; r++) {
      const zc = frameW + ((h - 2 * frameW) * r) / rows
      parts.push(mlib.box(x0, 0.0, zc - munW / 2, x1, munD, zc + munW / 2))
    }
  }
  const fr = mlib.join(parts)
  mlib.bevel(fr, 0.0022, 2)
  const gl = mlib.box(-hw + frameW * 0.4, -glassBack - 0.004, frameW * 0.4, hw - frameW * 0.4, -glassBack, h - frameW * 0.4)
  return [fr, gl]
}

// ------------------------------------------------------------------- hardware

/** Brass knob on a rectangular back plate; axis along +Y. */
export function knobSet(): MeshData {
  const parts: MeshData[] = []
  const plate = mlib.prism(mlib.roundedRect(0.048, 0.135, 0.012, 4), 0.0, 0.005)
  mlib.rotX(plate, -Math.PI / 2)
  parts.push(plate)
  const prof: Vec2[] = [
    [0.0, 0.004],
    [0.014, 0.006],
    [0.017, 0.014],
    [0.011, 0.021],
    [0.014, 0.026],
    [0.027, 0.035],
    [0.031, 0.047],
    [0.024, 0.057],
    [0.013, 0.063],
    [0.0, 0.065],
  ]
  const kn = mlib.revolve(prof, 24)
  mlib.rotX(kn, -Math.PI / 2)
  parts.push(kn)
  const kh = mlib.prism(mlib.roundedRect(0.011, 0.024, 0.004, 3), 0.0, 0.006)
  mlib.rotX(kh, -Math.PI / 2)
  mlib.translateMesh(kh, [0, 0, -0.04])
  parts.push(kh)
  const ob = mlib.join(parts)
  mlib.smoothShade(ob, 34)
  return ob
}
