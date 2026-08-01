/** First-person player: pointer lock + WASD relative to the camera heading,
 * circle-vs-OBB collision against walls and furniture, and a walking bob.
 * No sprint, no jump; the player is just the camera. */
import * as THREE from 'three/webgpu'
import type { Obb } from '../scene/world'

const EYE = 1.62
const RADIUS = 0.24
const SPEED = 1.65 // m/s, an interior walking pace
const ACCEL = 11.0

export class PlayerControls {
  readonly camera: THREE.PerspectiveCamera
  private colliders: Obb[]
  private yaw = 0
  private pitch = 0
  private pos = new THREE.Vector2()
  private vel = new THREE.Vector2()
  private keys = new Set<string>()
  private bobPhase = 0
  private bobAmp = 0
  enabled = false

  constructor(camera: THREE.PerspectiveCamera, colliders: Obb[]) {
    this.camera = camera
    this.colliders = colliders
    window.addEventListener('keydown', (e) => {
      if (['KeyW', 'KeyA', 'KeyS', 'KeyD'].includes(e.code)) this.keys.add(e.code)
    })
    window.addEventListener('keyup', (e) => this.keys.delete(e.code))
    window.addEventListener('blur', () => this.keys.clear())
    document.addEventListener('mousemove', (e) => {
      if (!this.enabled) return
      this.yaw -= e.movementX * 0.0022
      this.pitch -= e.movementY * 0.0022
      const lim = Math.PI / 2 - 0.03
      this.pitch = Math.max(-lim, Math.min(lim, this.pitch))
    })
  }

  /** Spawn just inside the front door, looking down the flat (CAM_master). */
  spawn(x = 2.3, y = -0.55, lookX = 6.4, lookY = 3.9): void {
    this.pos.set(x, y)
    this.yaw = Math.atan2(lookY - y, lookX - x) - Math.PI / 2
    this.pitch = -0.04
    this.syncCamera(0)
  }

  update(dt: number): void {
    dt = Math.min(dt, 0.05)
    let fx = 0
    let fy = 0
    if (this.enabled) {
      if (this.keys.has('KeyW')) fy += 1
      if (this.keys.has('KeyS')) fy -= 1
      if (this.keys.has('KeyA')) fx -= 1
      if (this.keys.has('KeyD')) fx += 1
    }
    // camera-relative: forward is where the camera looks (projected to floor)
    const sin = Math.sin(this.yaw)
    const cos = Math.cos(this.yaw)
    // yaw 0 looks +Y (three -Z after our basis mapping below)
    const fwd = new THREE.Vector2(-sin, cos)
    const right = new THREE.Vector2(cos, sin)
    const wish = new THREE.Vector2(fwd.x * fy + right.x * fx, fwd.y * fy + right.y * fx)
    if (wish.lengthSq() > 1) wish.normalize()
    wish.multiplyScalar(SPEED)
    const k = 1 - Math.exp(-ACCEL * dt)
    this.vel.lerp(wish, k)
    const step = this.vel.clone().multiplyScalar(dt)
    this.pos.add(step)
    this.resolveCollisions()
    // head bob: speed-scaled, eases out when stopping
    const speed = this.vel.length()
    const target = Math.min(1, speed / SPEED)
    this.bobAmp += (target - this.bobAmp) * Math.min(1, 8 * dt)
    this.bobPhase += speed * dt * 5.6
    this.syncCamera(dt)
  }

  private resolveCollisions(): void {
    for (let iter = 0; iter < 3; iter++) {
      let pushed = false
      for (const c of this.colliders) {
        if (c.z0 > 1.55 || c.z1 < 0.25) continue
        // to collider-local frame
        const lx = (this.pos.x - c.cx) * c.cos + (this.pos.y - c.cy) * c.sin
        const ly = -(this.pos.x - c.cx) * c.sin + (this.pos.y - c.cy) * c.cos
        const qx = Math.max(-c.hw, Math.min(c.hw, lx))
        const qy = Math.max(-c.hh, Math.min(c.hh, ly))
        let dx = lx - qx
        let dy = ly - qy
        const d2 = dx * dx + dy * dy
        if (d2 >= RADIUS * RADIUS) continue
        pushed = true
        if (d2 > 1e-12) {
          const d = Math.sqrt(d2)
          const push = RADIUS - d
          dx /= d
          dy /= d
          const wx = dx * c.cos - dy * c.sin
          const wy = dx * c.sin + dy * c.cos
          this.pos.x += wx * push
          this.pos.y += wy * push
        } else {
          // centre inside the box: push out along the nearest face
          const pens = [c.hw - Math.abs(lx), c.hh - Math.abs(ly)]
          if (pens[0] < pens[1]) {
            const s = lx >= 0 ? 1 : -1
            const push = pens[0] + RADIUS
            this.pos.x += s * push * c.cos
            this.pos.y += s * push * c.sin
          } else {
            const s = ly >= 0 ? 1 : -1
            const push = pens[1] + RADIUS
            this.pos.x += s * push * -c.sin
            this.pos.y += s * push * c.cos
          }
        }
      }
      if (!pushed) break
    }
  }

  private syncCamera(dt: number): void {
    void dt
    const bobZ = Math.sin(this.bobPhase * 2.0) * 0.014 * this.bobAmp
    const bobX = Math.sin(this.bobPhase) * 0.008 * this.bobAmp
    const rollT = Math.sin(this.bobPhase) * 0.0035 * this.bobAmp
    // scene is Z-up; build the camera basis directly
    const cp = Math.cos(this.pitch)
    const dir = new THREE.Vector3(-Math.sin(this.yaw) * cp, Math.cos(this.yaw) * cp, Math.sin(this.pitch))
    const eye = new THREE.Vector3(
      this.pos.x + Math.cos(this.yaw) * bobX,
      this.pos.y + Math.sin(this.yaw) * bobX,
      EYE + bobZ,
    )
    this.camera.up.set(Math.sin(rollT) * Math.cos(this.yaw), Math.sin(rollT) * Math.sin(this.yaw), 1).normalize()
    this.camera.position.copy(eye)
    this.camera.lookAt(eye.clone().add(dir))
  }
}
