/** Text objects for the chalk menu and the SERVICE plate.
 *
 * Blender sets these with its bundled sans and converts to mesh; the port
 * tessellates the same glyph outlines from three's bundled sans typeface.
 * Meshes are produced in the XY plane (x right, y up) extruded +/- `extrude`
 * along z, exactly the frame Blender FONT objects start in, so the callers'
 * rotX/rotateZ choreography carries over verbatim.
 */
import * as THREE from 'three/webgpu'
import { Font } from 'three/examples/jsm/loaders/FontLoader.js'
import helvetiker from 'three/examples/fonts/helvetiker_regular.typeface.json'
import { MeshData, type Vec2, type Vec3, recalcNormals } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'

interface GlyphData {
  ha: number
}
interface FontData {
  resolution: number
  glyphs: Record<string, GlyphData>
}

const font = new Font(helvetiker as unknown as ConstructorParameters<typeof Font>[0])
const fontData = helvetiker as unknown as FontData

export interface TextOpts {
  extrude?: number
  align?: 'LEFT' | 'CENTER'
  alignY?: 'TOP' | 'CENTER'
  spacing?: number
  curveSegments?: number
}

/** One word/line of text as a closed solid, centred per `align`. */
export function textMesh(body: string, size: number, opts: TextOpts = {}): MeshData {
  const { extrude = 0.01, align = 'CENTER', alignY = 'CENTER', spacing = 1, curveSegments = 3 } = opts
  const scale = size / fontData.resolution
  const parts: MeshData[] = []
  let pen = 0
  for (const ch of body) {
    const glyph = fontData.glyphs[ch]
    const advance = (glyph ? glyph.ha : fontData.resolution * 0.5) * scale * spacing
    if (ch !== ' ' && glyph) {
      const shapes = font.generateShapes(ch, size)
      for (const shape of shapes) {
        const md = shapeToMesh(shape, extrude, curveSegments)
        mlib.translate(md, [pen, 0, 0])
        parts.push(md)
      }
    }
    pen += advance
  }
  const md = parts.length ? mlib.join(parts) : new MeshData()
  if (!md.verts.length) return md
  const xs = md.verts.map((v) => v[0])
  const ys = md.verts.map((v) => v[1])
  const x0 = Math.min(...xs)
  const x1 = Math.max(...xs)
  const y0 = Math.min(...ys)
  const y1 = Math.max(...ys)
  const dx = align === 'CENTER' ? -(x0 + x1) / 2 : -x0
  const dy = alignY === 'CENTER' ? -(y0 + y1) / 2 : -y1
  mlib.translate(md, [dx, dy, 0])
  return md
}

function shapeToMesh(shape: THREE.Shape, extrude: number, curveSegments: number): MeshData {
  const points = shape.extractPoints(curveSegments)
  const contour = points.shape
  const holes = points.holes
  if (THREE.ShapeUtils.isClockWise(contour)) contour.reverse()
  for (const hole of holes) if (!THREE.ShapeUtils.isClockWise(hole)) hole.reverse()
  const tris = THREE.ShapeUtils.triangulateShape(contour, holes)
  const flat: THREE.Vector2[] = [...contour]
  for (const hole of holes) flat.push(...hole)
  const n = flat.length
  const verts: Vec3[] = []
  for (const p of flat) verts.push([p.x, p.y, extrude])
  for (const p of flat) verts.push([p.x, p.y, -extrude])
  const faces: number[][] = []
  for (const [a, b, c] of tris) {
    faces.push([a, b, c])
    faces.push([c + n, b + n, a + n])
  }
  const walls = (loop: THREE.Vector2[], offset: number): void => {
    const m = loop.length
    for (let i = 0; i < m; i++) {
      const a = offset + i
      const b = offset + ((i + 1) % m)
      faces.push([b, a, a + n, b + n])
    }
  }
  let off = 0
  walls(contour, off)
  off += contour.length
  for (const hole of holes) {
    walls(hole, off)
    off += hole.length
  }
  const md = MeshData.from(verts, faces)
  recalcNormals(md)
  return md
}

export type { Vec2 }
