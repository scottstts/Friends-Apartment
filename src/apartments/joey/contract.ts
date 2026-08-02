import type { CameraSpec } from '../types'

/** Observable visual contract derived only from build_scripts/Joeys_apt. */
export const JOEY_VISUAL_CONTRACT = {
  subject: "Chandler and Joey's apartment 19",
  identity: [
    'stepped north wall with the kitchen pulled south into a shallow alcove',
    'cool moonlit night ambience from the north-facing light well against warm practical fixtures',
    'continuous 12-inch five-finger mosaic parquet through living room and bedrooms',
    'yellow couch, two inward-splayed black recliners, entertainment wall and foosball table',
    'cream-and-putty L-shaped kitchen with vintage range, retro fridge and peninsula stools',
    'five-horizontal-panel open interior doors and greige applied wall mouldings',
  ],
  materialSeparation: [
    'honey oak parquet remains distinct from painted trim and cabinet timber',
    'black leather recliners retain broad coated highlights without reading as plastic',
    'brass, chrome, enamel, clear glass and glazed ceramic remain distinct before bloom',
    'poster art uses the supplied image assets without substitution',
  ],
  invariants: [
    'the JX/NY2 reflex corner owns no overlapping wall volume',
    'the peninsula turns on the jog wall and the counter reaches the east wall without a gap',
    'both recliners face west toward the entertainment unit and splay toward each other',
    'all door and window openings remain passable and their casings do not intersect the leaves',
    'the front-door threshold is floored and the player remains enclosed by authored colliders',
    'apartment 19 owns its scene, material cache, layout constants and interaction anchors',
  ],
  allowedDivergences: [
    'User-approved: replace the Blender build daytime physical sky with apartment 20\'s night sky, moon and distant-city ambience while retaining apartment 19 exterior geometry and fixture-authored practical lighting.',
  ] as string[],
  frameBudgetMs: 16.7,
} as const

/** Deterministic parity views from build_scripts/Joeys_apt/build_all.py. */
export const JOEY_CAMERAS = {
  full: { location: [7.72, -2.55, 2.8], target: [2.45, 4.3, 0.92], lens: 22 },
  living: { location: [2.9, 2.85, 1.58], target: [6.95, 4.4, 1], lens: 20 },
  kitchen: { location: [2.45, 1.15, 1.55], target: [5.52, 4.75, 1.05], lens: 18 },
  couch: { location: [2.35, 3.85, 1.62], target: [1.45, 6.95, 0.82], lens: 22 },
  ne: { location: [7.97, 3.95, 1.72], target: [1.2, 1.4, 0.95], lens: 20 },
  nw: { location: [0.55, 6.8, 1.72], target: [7.22, 1.1, 0.95], lens: 20 },
  se: { location: [7.97, 0.55, 1.72], target: [1.1, 6.4, 1.05], lens: 20 },
  sw: { location: [0.52, 0.55, 1.72], target: [6.92, 4, 1.05], lens: 20 },
  wallN: { location: [2.05, 3.2, 1.42], target: [2.05, 7.3, 1.42], lens: 26 },
  wallW: { location: [3.4, 3.05, 1.42], target: [0, 3.05, 1.42], lens: 26 },
  wallE: { location: [4.62, 2.1, 1.42], target: [8.47, 2.1, 1.42], lens: 26 },
  wallS: { location: [4.5, 3.8, 1.42], target: [4.5, 0, 1.42], lens: 26 },
  wallKitchen: { location: [6.55, 1.7, 1.45], target: [6.55, 4.9, 1.45], lens: 26 },
  island: { location: [3.35, 2.1, 1.52], target: [5.4, 4.3, 0.98], lens: 28 },
  range: { location: [7.02, 2.15, 1.5], target: [7.02, 4.9, 1.12], lens: 35 },
  fridge: { location: [6.72, 2.45, 1.55], target: [7.98, 4.85, 1.3], lens: 32 },
  entertainment: { location: [3.45, 2.9, 1.36], target: [0.05, 3.3, 0.92], lens: 30 },
  recliners: { location: [4.9, 2.2, 1.48], target: [2.2, 3.5, 0.72], lens: 32 },
  foosball: { location: [5.4, 0.62, 1.52], target: [7.06, 1.55, 0.8], lens: 30 },
  frontDoor: { location: [5.65, 1.95, 1.55], target: [8.47, 2.58, 1.2], lens: 30 },
  bathDoor: { location: [4.04, 4.7, 1.52], target: [4.04, 7.3, 1.2], lens: 32 },
  windows: { location: [1.58, 4.6, 1.48], target: [1.58, 7.3, 1.4], lens: 26 },
  sofa: { location: [1.58, 5.3, 1.2], target: [1.58, 7.05, 0.62], lens: 35 },
  dog: { location: [2.2, 5.05, 1.3], target: [0.34, 6.46, 0.62], lens: 40 },
  sink: { location: [5.95, 3.3, 1.42], target: [6.15, 4.55, 0.9], lens: 38 },
  phone: { location: [7.05, 3.05, 1.52], target: [8.42, 3.72, 1.44], lens: 42 },
  vanity: { location: [4.1, 8.4, 1.42], target: [5.55, 9.1, 0.92], lens: 30 },
  chandler: { location: [-1.05, 3.15, 1.58], target: [-2.55, 6.48, 1.25], lens: 20 },
  joey: { location: [-0.7, 2.05, 1.58], target: [-3.5, 0.05, 1.05], lens: 18 },
  bathroom: { location: [4.04, 7.05, 1.55], target: [3.7, 10.55, 1.05], lens: 20 },
  near: { location: [4.9, 2.2, 1.48], target: [2.2, 3.5, 0.72], lens: 32 },
  far: { location: [7.32, 0.9, 2.75], target: [2.5, 5.2, 0.85], lens: 18 },
  noPost: { location: [2.9, 2.85, 1.58], target: [6.95, 4.4, 1], lens: 20 },
} satisfies Record<string, CameraSpec>
