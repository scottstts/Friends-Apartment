/** Deterministic ports of build_scripts/build_all.py's Blender cameras.
 *
 * The game remains first-person by default. A `?view=<name>` query selects a
 * fixed inspection camera, which makes browser captures directly comparable
 * with the authoritative Blender renders. `?post=0` keeps the same HDR scene
 * pass and output transform while removing bloom. `?ao=0`, `?shadows=0`,
 * and `?grade=0` expose the remaining image-pipeline stages independently.
 */
import * as THREE from 'three/webgpu'

interface CameraSpec {
  location: [number, number, number]
  target: [number, number, number]
  lens: number
}

const CAMERAS = {
  master: { location: [2.3, -1.15, 1.64], target: [6.4, 3.9, 1.2], lens: 19 },
  kitchen: { location: [5.2, 0.85, 1.58], target: [0.4, 3.55, 1.2], lens: 24 },
  living: { location: [2.95, -0.85, 1.54], target: [7.9, 3.1, 1.15], lens: 25 },
  window: { location: [4.1, 0.7, 1.58], target: [6.5, 5.9, 1.4], lens: 27 },
  hall: { location: [4.1, 2.3, 1.58], target: [3.9, 5.9, 1.35], lens: 28 },
  dine: { location: [3.95, -0.1, 1.44], target: [1.65, 2.85, 0.8], lens: 32 },
  tv: { location: [6.1, 2.2, 1.45], target: [8.6, 3.2, 1.3], lens: 34 },
  door: { location: [3.3, 2.7, 1.55], target: [0.0, 0.1, 1.3], lens: 30 },
  wide: { location: [1.4, -1.15, 2.1], target: [7.4, 4.4, 1.0], lens: 15 },
  beam: { location: [6.6, -0.6, 1.62], target: [1.6, 3.9, 1.6], lens: 24 },
  monica: { location: [7.1, 5.3, 1.55], target: [10.8, 4.6, 1.1], lens: 24 },
  rachel: { location: [7.4, 1.55, 1.55], target: [11.2, 0.9, 1.05], lens: 24 },
  mon_in: { location: [9.1, 3.3, 1.55], target: [11.4, 5.2, 1.0], lens: 22 },
  rac_in: { location: [9.1, 2.2, 1.55], target: [11.4, 0.3, 1.0], lens: 22 },
  slipper: { location: [6.55, -0.72, 1.38], target: [7.95, -2.23, 0.55], lens: 38 },
  slipper_far: { location: [5.35, 0.25, 1.52], target: [7.95, -2.23, 0.62], lens: 42 },
  bed_foot: { location: [7.92, -1.18, 1.42], target: [10.28, -1.25, 0.58], lens: 38 },
} satisfies Record<string, CameraSpec>

export type CameraBookmark = keyof typeof CAMERAS

export interface InspectionMode {
  view: CameraBookmark
  bloom: boolean
  shadows: boolean
  grade: boolean
  ao: boolean
}

export function inspectionFromUrl(url = window.location.href): InspectionMode | null {
  const params = new URL(url).searchParams
  const view = params.get('view')
  if (!view || !(view in CAMERAS)) return null
  return {
    view: view as CameraBookmark,
    bloom: params.get('post') !== '0',
    shadows: params.get('shadows') !== '0',
    grade: params.get('grade') !== '0',
    ao: params.get('ao') !== '0',
  }
}

/** Match Blender's default 36 mm sensor with AUTO/HORIZONTAL sensor fit. */
export function applyCameraBookmark(camera: THREE.PerspectiveCamera, bookmark: CameraBookmark): void {
  const spec = CAMERAS[bookmark]
  const horizontalFov = 2 * Math.atan(36 / (2 * spec.lens))
  camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(horizontalFov / 2) / camera.aspect))
  camera.position.set(...spec.location)
  camera.up.set(0, 0, 1)
  camera.lookAt(...spec.target)
  camera.updateProjectionMatrix()
}
