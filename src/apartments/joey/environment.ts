/** Apartment 19 light well plus the user-approved shared apartment-20 night. */
import * as THREE from 'three/webgpu'
import * as mlib from '../../lib/mlib'
import type { MeshData } from '../../lib/mesh'
import type { World } from '../../scene/world'
import * as night from '../../scene/night'
import * as L from './layout'
import * as M from './materials'

function facade(world: World): void {
  M.plaster('M_BrickOut', '7A4B3C', { rough: 0.94, bump: 0.7, patch: 0.22, scale: 0.6 })
  M.plaster('M_Areaway', '5A5550', { rough: 0.95, bump: 0.5, patch: 0.3, scale: 0.5 })
  M.clearGlass('M_WinDark', '10161C', { rough: 0.06 })
  const y0 = L.NY + 8.4
  const x0 = L.BED_W - L.TW - 7.6
  world.add(mlib.box(-18, y0, -7, 17, y0 + 1.6, 18), M.get('M_BrickOut'))
  world.add(mlib.box(x0 - 1.6, -9, -7, x0, y0 + 1.6, 18), M.get('M_BrickOut'))
  const windows: MeshData[] = []
  for (let gx = -6; gx < 9; gx++) {
    for (let gz = 0; gz < 7; gz++) {
      const x = -3.2 + gx * 1.9
      const z = -1.2 + gz * 2.7
      if (z >= -0.4) windows.push(mlib.box(x, y0 - 0.1, z, x + 1.05, y0 + 0.02, z + 1.55))
    }
  }
  for (let gy = -4; gy < 8; gy++) {
    for (let gz = 0; gz < 7; gz++) {
      const y = -6 + gy * 1.9
      const z = -1.2 + gz * 2.7
      if (z >= -0.4) windows.push(mlib.box(x0 - 0.02, y, z, x0 + 0.1, y + 1.05, z + 1.55))
    }
  }
  world.add(mlib.join(windows), M.get('M_WinDark'))
  world.add(mlib.box(-18, -9, -7.1, 17, y0 + 0.1, -7), M.get('M_Areaway'))
}

function moonlitWindows(world: World): void {
  const color: [number, number, number] = [0.55, 0.66, 0.92]
  const addNorth = (x: number, y: number, z: number, strength: number): void => {
    const light = new THREE.SpotLight(new THREE.Color(...color), strength / Math.PI)
    light.position.set(x, y + 1.25, z + 0.28)
    light.target.position.set(x, y - 3.4, z - 0.2)
    light.angle = 0.54
    light.penumbra = 0.78
    light.decay = 2
    light.distance = 9
    light.castShadow = true
    light.shadow.mapSize.set(768, 768)
    light.shadow.camera.near = 0.25
    light.shadow.camera.far = 12
    light.shadow.bias = -0.0008
    light.shadow.normalBias = 0.018
    light.shadow.intensity = 0.78
    world.addLight(light)
    world.scene.add(light.target)
  }
  addNorth((L.WIN_A[0] + L.WIN_A[1]) * 0.5, L.NY, (L.WIN_SILL + L.WIN_HEAD) * 0.5, 7.5)
  addNorth((L.WIN_B[0] + L.WIN_B[1]) * 0.5, L.NY, (L.WIN_SILL + L.WIN_HEAD) * 0.5, 7.5)
  for (const [a, b] of L.CH_WIN) addNorth((a + b) * 0.5, L.CH_Y[1], (L.WIN_SILL + L.WIN_HEAD) * 0.5, 5.5)
  // Joey's side window faces west; rotate the same cool light-well treatment.
  const side = new THREE.SpotLight(new THREE.Color(...color), 5.5 / Math.PI)
  side.position.set(L.BED_W - 1.25, (L.JO_WIN[0] + L.JO_WIN[1]) * 0.5, 1.75)
  side.target.position.set(L.BED_W + 3.2, (L.JO_WIN[0] + L.JO_WIN[1]) * 0.5, 1.28)
  side.angle = 0.55
  side.penumbra = 0.78
  side.decay = 2
  side.distance = 9
  side.castShadow = true
  side.shadow.mapSize.set(768, 768)
  side.shadow.camera.near = 0.25
  side.shadow.camera.far = 12
  side.shadow.bias = -0.0008
  side.shadow.normalBias = 0.018
  side.shadow.intensity = 0.78
  world.addLight(side)
  world.scene.add(side.target)
}

export function build(world: World): void {
  facade(world)
  // This is the same TSL sky/IBL, moon, skyline and mid-ground city system as
  // apartment 20. It is the one explicit departure from Joey's Blender build.
  night.build(world)
  moonlitWindows(world)
}
