/** The world outside the glass, from build_env.py: the pavement wrapping the
 * north-east corner, the street, the upper storeys and the facades opposite.
 *
 * build_env.py lights this with a daytime Nishita sky and a low sun; the
 * game's Central Perk is a night scene by direction, so the shared apartment
 * night (sky, IBL, moon, mid-ground city) replaces sky_and_sun one-for-one,
 * with the cool moonlit-window treatment apartment 19 established. */
import * as THREE from 'three/webgpu'
import type { Vec2 } from '../../lib/mesh'
import { MeshData } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import * as night from '../night'
import type { World } from '../../core/world'
import * as G from './geo'
import * as L from './layout'
import * as M from './materials'

const WALK = 3.6
const ROAD = 9

function street(world: World): void {
  const walk = M.concrete('paving', '8E8B82', [0.6, 0.85], 2.4)
  const road = M.concrete('asphalt', '3A3A3C', [0.5, 0.78], 3)
  // low contrast on purpose: nine metres away through glass, bright mortar
  // joints alias into speckle
  const fac = M.brick('brick_street', { face: '6E4636', face2: '5E3E30', mortar: '6A5A4C', spread: 0.45 })
  const fac2 = M.brick('brick_street2', { face: '7A6E5A', face2: '6A6050', mortar: '72685C', spread: 0.45 })
  const dark = M.flat('glass_dark', '14161A', 0.18)

  // pavement wrapping the corner OUTSIDE the building
  const e = L.BAY_E + L.TW
  const n = L.WC_N + L.TW
  const p: Vec2[] = [
    [L.EX + L.TW, -6],
    [e + WALK, -6],
    [e + WALK, n + WALK],
    [-6, n + WALK],
    [-6, n],
    [e, n],
    [e, L.BAY_DIAG_E],
    [L.EX + L.TW, L.BAY_N + L.TW],
  ]
  world.add(mlib.prism(G.ccw(p), -0.3, -0.02), walk)
  world.add(
    mlib.prism(
      [
        [-40, -40],
        [60, -40],
        [60, 60],
        [-40, 60],
      ],
      -0.46,
      -0.32,
    ),
    road,
  )

  // the rest of the building the shop is the ground floor of
  const up: Vec2[] = [
    [-L.TW, -L.TW],
    [L.EX, -L.TW],
    [L.EX, L.BAY_S],
    [L.BAY_E + L.TW, L.BAY_S],
    [L.BAY_E + L.TW, L.BAY_DIAG_E],
    [L.EX + L.TB, L.BAY_N],
    [L.EX + L.TB, L.WC_N + L.TW],
    [-L.TW, L.WC_N + L.TW],
  ]
  world.add(mlib.prism(G.ccw(up), L.CZ + 0.22, L.CZ + 0.22 + 12.6), fac)
  const darkPanes: MeshData[] = []
  for (let f = 0; f < 4; f++) {
    const z = L.CZ + 0.55 + f * 3.05
    for (let i = 0; i < 5; i++) {
      const y = 3.1 + i * 1.55
      darkPanes.push(mlib.box(L.BAY_E + L.TW - 0.1, y - 0.42, z, L.BAY_E + L.TW + 0.12, y + 0.42, z + 1.7))
    }
    for (let i = 0; i < 4; i++) {
      const x = 0.8 + i * 1.55
      darkPanes.push(mlib.box(x - 0.42, L.WC_N + L.TW - 0.1, z, x + 0.42, L.WC_N + L.TW + 0.12, z + 1.7))
    }
  }

  // the block opposite, across the street
  const facade = (
    x0: number,
    y0: number,
    x1: number,
    y1: number,
    h: number,
    mat: THREE.Material,
    floors: number,
    bays: number,
    axis: 'x' | 'y',
  ): void => {
    world.add(
      mlib.prism(
        [
          [x0, y0],
          [x1, y0],
          [x1, y1],
          [x0, y1],
        ],
        -0.3,
        h,
      ),
      mat,
    )
    for (let f = 0; f < floors; f++) {
      const z = 0.95 + f * 3.05
      for (let bIdx = 0; bIdx < bays; bIdx++) {
        const t = (bIdx + 0.5) / bays
        if (axis === 'x') {
          const cx = x0 + (x1 - x0) * t
          darkPanes.push(mlib.box(cx - 0.44, y0 - 0.14, z, cx + 0.44, y0 + 0.1, z + 1.62))
        } else {
          const cy = y0 + (y1 - y0) * t
          darkPanes.push(mlib.box(x0 - 0.14, cy - 0.44, z, x0 + 0.1, cy + 0.44, z + 1.62))
        }
      }
    }
  }
  const fx = L.BAY_E + WALK + ROAD
  facade(fx, -12, fx + 14, 12, 15.5, fac, 5, 5, 'y')
  facade(fx, 13, fx + 14, 30, 16.5, fac2, 5, 5, 'y')
  facade(-14, L.WC_N + WALK + ROAD, L.WC_E + 6, L.WC_N + WALK + ROAD + 14, 14, fac2, 4, 6, 'x')
  world.add(mlib.join(darkPanes), dark)
}

/** Cool skyglow through the storefront, the apartment-19 night treatment. */
function moonlitWindows(world: World): void {
  const color: [number, number, number] = [0.55, 0.66, 0.92]
  const spot = (
    px: number,
    py: number,
    pz: number,
    tx: number,
    ty: number,
    tz: number,
    strength: number,
  ): void => {
    const light = new THREE.SpotLight(new THREE.Color(...color), strength / Math.PI)
    light.position.set(px, py, pz)
    light.target.position.set(tx, ty, tz)
    light.angle = 0.56
    light.penumbra = 0.8
    light.decay = 2
    light.distance = 10
    light.castShadow = true
    light.shadow.mapSize.set(512, 512)
    light.shadow.camera.near = 0.25
    light.shadow.camera.far = 12
    light.shadow.bias = -0.0008
    light.shadow.normalBias = 0.018
    light.shadow.intensity = 0.78
    world.addLight(light)
    world.scene.add(light.target)
  }
  const zc = L.STEP + (L.STORE_SILL + L.STORE_HEAD) * 0.5 + 0.35
  for (const [a, b] of L.BAY_WIN) {
    const yc = (a + b) * 0.5
    spot(L.BAY_E + 1.3, yc, zc + 0.9, L.BAY_E - 3.2, yc, 0.55, 6.5)
  }
  const yn = (L.E_WIN_N[0] + L.E_WIN_N[1]) * 0.5
  spot(L.EX + 1.3, yn, zc + 0.7, L.EX - 3.2, yn, 0.5, 5.5)
}

export function build(world: World): void {
  street(world)
  night.build(world)
  moonlitWindows(world)
}
