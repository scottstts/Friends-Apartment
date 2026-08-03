import type * as THREE from 'three/webgpu'
import type { World } from '../scene/world'

export type ApartmentId = '19' | '20' | 'perk'

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

/** A multi-spot sofa: E sits, A/D slide one cushion at a time, exactly the
 * apartment-20 couch choreography driven by authored numbers. */
export interface CouchSpec {
  center: [number, number]
  /** Direction the sitter faces, radians on the floor plane. */
  facing: number
  /** Cushion pitch: eye-spot spacing along the couch axis. */
  pitch: number
  /** Eye offset forward of the couch centre line. */
  forwardOffset: number
  eyeZ: number
  radius: number
  /** Approach-zone line distance in front of the centre. */
  frontDist: number
  /** Approaches less than this far in front of centre count as behind. */
  behindMin: number
  /** Authored stand-up pockets, one per spot (the middle is a fallback). */
  stands: [[number, number], [number, number], [number, number]]
}

export interface ApartmentInteractions {
  seats: SeatSpec[]
  couches?: CouchSpec[]
  door: { point: [number, number]; radius: number }
}

export interface ApartmentDefinition {
  id: ApartmentId
  label: string
  build(world: World): Promise<void>
  spawn: { position: [number, number]; lookAt: [number, number] }
  interactions: ApartmentInteractions
  /** Walkable floor height at (x, y); flat apartments omit it. */
  groundHeight?(x: number, y: number): number
  /** Apply apartment-owned background/environment state before rendering. */
  activate?(scene: THREE.Scene): void
}
