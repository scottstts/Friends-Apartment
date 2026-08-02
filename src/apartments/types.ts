import type * as THREE from 'three/webgpu'
import type { World } from '../scene/world'

export type ApartmentId = '19' | '20'

export interface CameraSpec {
  location: [number, number, number]
  target: [number, number, number]
  lens: number
}

export interface SeatSpec {
  center: [number, number]
  /** Model-facing direction in radians on the apartment floor plane. */
  facing: number
  eyeZ: number
  stand: [number, number]
  radius: number
  anchor?: [number, number]
  forwardOffset?: number
}

export interface ApartmentInteractions {
  seats: SeatSpec[]
  door: { point: [number, number]; radius: number }
}

export interface ApartmentDefinition {
  id: ApartmentId
  label: string
  build(world: World): Promise<void>
  spawn: { position: [number, number]; lookAt: [number, number] }
  interactions: ApartmentInteractions
  cameras: Readonly<Record<string, CameraSpec>>
  /** Apply apartment-owned background/environment state before rendering. */
  activate?(scene: THREE.Scene): void
}
