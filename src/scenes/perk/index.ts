/** Central Perk: the coffee house downstairs, ported from
 * build_scripts/Central_Perk/ at the same parity bar as apartments 19/20.
 *
 * The player enters through the storefront doors on the bay platform, so the
 * definition carries the build's own ground() as its floor-height sampler.
 * Interactions: the hero couch (three spots, A/D scooting), the wing-back
 * armchair beside it, and the entrance doors back out to the landing. */
import type { ApartmentDefinition } from '../types'
import * as L from './layout'
import * as shell from './shell'
import * as openings from './openings'
import * as environment from './environment'
import * as dress from './dress'

const tick = (): Promise<void> => new Promise((resolve) => setTimeout(resolve, 0))

/** Just inside the entrance doors, on the platform. */
const SPAWN = L.diagPt(1.69, 0.9)
/** The hint zone in front of the closed doors. */
const DOOR = L.diagPt(1.69, 0.45)

// The couch faces south (-Y); its sitter's left runs east, so KeyA slides
// east exactly as the hint reads.  Cushion top ~0.45 sunk under weight plus
// a seated torso puts the eyes at 1.10.
const COUCH_FACING = -Math.PI / 2
// The armchair faces west (-X) across the coffee table.
const CHAIR_FACING = Math.PI

export const perkApartment: ApartmentDefinition = {
  id: 'perk',
  label: 'Central Perk',
  async build(world) {
    shell.build(world)
    await tick()
    openings.build(world)
    await tick()
    environment.build(world)
    await tick()
    await dress.build(world)
    await tick()
    world.finalize()
  },
  spawn: { position: [SPAWN[0], SPAWN[1]], lookAt: [L.SOFA_C[0], L.SOFA_C[1] - 0.4] },
  groundHeight: (x, y) => L.ground(x, y),
  interactions: {
    seats: [
      {
        center: [L.RECLINER_C[0], L.RECLINER_C[1]],
        facing: CHAIR_FACING,
        eyeZ: 1.13,
        stand: [5.8, 3.88],
        radius: 0.85,
        anchor: [L.RECLINER_C[0] - 0.5, L.RECLINER_C[1]],
        forwardOffset: 0.02,
      },
    ],
    couches: [
      {
        center: [L.SOFA_C[0], L.SOFA_C[1]],
        facing: COUCH_FACING,
        pitch: (L.SOFA_L - 2 * 0.205) / 3,
        forwardOffset: 0.08,
        eyeZ: 1.1,
        radius: 0.85,
        frontDist: 0.9,
        behindMin: 0.45,
        stands: [
          [3.72, 4.62],
          [L.SOFA_C[0], L.SOFA_C[1] - 0.9],
          [6.14, 5.58],
        ],
      },
    ],
    door: { point: [DOOR[0], DOOR[1]], radius: 0.86 },
  },
}
