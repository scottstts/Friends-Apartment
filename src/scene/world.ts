/** Scene registry.  The Blender build parents ~750 objects into collections;
 * here every MeshData lands in a per-material bucket and each bucket merges
 * into one Mesh at finalize() — same world-space vertices, far fewer draws.
 * Rugs (whose materials read object-space from a centred mesh) stay separate.
 */
import * as THREE from 'three/webgpu'
import { MeshData, toGeometry, type Vec3 } from '../lib/mesh'
import * as mlib from '../lib/mlib'

export interface Obb {
  cx: number
  cy: number
  hw: number
  hh: number
  cos: number
  sin: number
  /** vertical extent, so low plinths do not block at chest height etc. */
  z0: number
  z1: number
}

export interface AddOpts {
  /** register the mesh's 2D footprint as a collider */
  collide?: boolean
  /** grow/shrink the auto collider footprint */
  collidePad?: number
  /** keep as its own Mesh with this position offset (rugs) */
  at?: Vec3
}

export class World {
  scene = new THREE.Scene()
  private buckets = new Map<THREE.Material, MeshData[]>()
  private separate: { md: MeshData; mat: THREE.Material; at: Vec3 }[] = []
  colliders: Obb[] = []
  lights: THREE.Light[] = []

  add(md: MeshData, mat: THREE.Material, opts: AddOpts = {}): MeshData {
    if (opts.collide) this.colliderFromMesh(md, opts.collidePad ?? 0)
    if (opts.at) {
      this.separate.push({ md, mat, at: opts.at })
      return md
    }
    let list = this.buckets.get(mat)
    if (!list) {
      list = []
      this.buckets.set(mat, list)
    }
    list.push(md)
    return md
  }

  /** Multi-material object (face_mat walls): split faces per material slot. */
  addMulti(md: MeshData, mats: THREE.Material[], opts: AddOpts = {}): void {
    if (opts.collide) this.colliderFromMesh(md, opts.collidePad ?? 0)
    const per: MeshData[] = mats.map(() => new MeshData())
    const remap: Map<number, number>[] = mats.map(() => new Map())
    md.faces.forEach((f, fi) => {
      const slot = Math.min(md.faceMat ? (md.faceMat[fi] ?? 0) : 0, mats.length - 1)
      const tgt = per[slot]
      const rm = remap[slot]
      const nf: number[] = []
      for (const vi of f) {
        let nvi = rm.get(vi)
        if (nvi === undefined) {
          nvi = tgt.verts.length
          tgt.verts.push([...md.verts[vi]] as Vec3)
          rm.set(vi, nvi)
        }
        nf.push(nvi)
      }
      tgt.faces.push(nf)
    })
    per.forEach((p, i) => {
      if (p.faces.length === 0) return
      p.shading = md.shading
      this.add(p, mats[i])
    })
  }

  colliderFromMesh(md: MeshData, pad = 0): void {
    let x0 = Infinity,
      y0 = Infinity,
      x1 = -Infinity,
      y1 = -Infinity,
      z0 = Infinity,
      z1 = -Infinity
    for (const v of md.verts) {
      x0 = Math.min(x0, v[0])
      y0 = Math.min(y0, v[1])
      x1 = Math.max(x1, v[0])
      y1 = Math.max(y1, v[1])
      z0 = Math.min(z0, v[2])
      z1 = Math.max(z1, v[2])
    }
    if (!isFinite(x0)) return
    this.box2(x0 - pad, y0 - pad, x1 + pad, y1 + pad, z0, z1)
  }

  /** Axis-aligned 2D box collider. */
  box2(x0: number, y0: number, x1: number, y1: number, z0 = 0, z1 = 3): void {
    this.colliders.push({
      cx: (x0 + x1) / 2,
      cy: (y0 + y1) / 2,
      hw: (x1 - x0) / 2,
      hh: (y1 - y0) / 2,
      cos: 1,
      sin: 0,
      z0,
      z1,
    })
  }

  /** Rotated 2D box collider. */
  obb(cx: number, cy: number, hw: number, hh: number, angle: number, z0 = 0, z1 = 3): void {
    this.colliders.push({ cx, cy, hw, hh, cos: Math.cos(angle), sin: Math.sin(angle), z0, z1 })
  }

  /** Wall run p0->p1 of thickness t on the outward (left-of-travel) side,
   * split by pass-through gaps [u0, u1] measured from p0. */
  wallCollider(p0: [number, number], p1: [number, number], t: number, gaps: [number, number][] = []): void {
    const dx = p1[0] - p0[0]
    const dy = p1[1] - p0[1]
    const ln = Math.hypot(dx, dy)
    if (ln < 1e-6) return
    const ang = Math.atan2(dy, dx)
    const ux = dx / ln
    const uy = dy / ln
    // outward = left of travel (interior sits on the right)
    const nx = -uy
    const ny = ux
    const spans: [number, number][] = []
    let u = 0
    const sorted = [...gaps].sort((a, b) => a[0] - b[0])
    for (const [g0, g1] of sorted) {
      if (g0 > u) spans.push([u, g0])
      u = Math.max(u, g1)
    }
    if (u < ln) spans.push([u, ln])
    for (const [a, b] of spans) {
      const mid = (a + b) / 2
      const cx = p0[0] + ux * mid + (nx * t) / 2
      const cy = p0[1] + uy * mid + (ny * t) / 2
      this.obb(cx, cy, (b - a) / 2, t / 2, ang)
    }
  }

  addLight(l: THREE.Light): THREE.Light {
    this.lights.push(l)
    this.scene.add(l)
    return l
  }

  /** Blender POINT lamp: energy in W -> candela = W / 4pi.
   *
   * WebGPU's default binding limits allow ~16 sampled textures per shader
   * stage, and every live shadow map costs one.  The lights whose shadows do
   * the light-confinement work keep real maps; small filler lamps instead get
   * an EEVEE-style influence cutoff so they cannot reach through walls. */
  pointLight(
    loc: Vec3,
    energy: number,
    color: [number, number, number],
    size = 0.05,
    opts: { shadow?: boolean; distance?: number } = {},
  ): THREE.PointLight {
    const l = new THREE.PointLight(new THREE.Color(...color), energy / (4 * Math.PI))
    l.position.set(...loc)
    l.decay = 2
    if (opts.distance !== undefined) l.distance = opts.distance
    if (opts.shadow !== false) {
      l.castShadow = true
      l.shadow.mapSize.set(512, 512)
      l.shadow.camera.near = 0.04
      l.shadow.camera.far = 14
      l.shadow.bias = -0.0015
      l.shadow.normalBias = 0.015
      l.shadow.radius = Math.max(1, size * 40)
    }
    this.addLight(l)
    return l
  }

  finalize(): void {
    for (const [mat, list] of this.buckets) {
      const merged = mlib.join(list)
      const geo = toGeometry(merged)
      const mesh = new THREE.Mesh(geo, mat)
      mesh.castShadow = !mat.userData.noShadow
      mesh.receiveShadow = true
      mesh.matrixAutoUpdate = false
      // merged world-space chunks span rooms; culling would also let a mesh
      // dodge shader precompilation and stall the frame it first appears
      mesh.frustumCulled = false
      // botanical plates: feed the merged bbox to the Generated-coord uniforms
      if (mat.userData.generatedBox) {
        geo.computeBoundingBox()
        const bb = geo.boundingBox!
        const gb = mat.userData.generatedBox as { min: THREE.Vector3; size: THREE.Vector3 }
        gb.min.copy(bb.min)
        gb.size.copy(bb.max).sub(bb.min)
      }
      this.scene.add(mesh)
    }
    for (const { md, mat, at } of this.separate) {
      const geo = toGeometry(md)
      const mesh = new THREE.Mesh(geo, mat)
      mesh.castShadow = !mat.userData.noShadow
      mesh.receiveShadow = true
      mesh.frustumCulled = false
      mesh.position.set(...at)
      this.scene.add(mesh)
    }
    this.buckets.clear()
    this.separate.length = 0
  }
}
