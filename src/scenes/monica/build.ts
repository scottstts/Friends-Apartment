/** Full build of the apartment - port of build_all.py's go().
 * Order matters: shell -> openings -> exterior -> sky/sun -> rooms ->
 * dressing.  fill() stays deliberately empty (no unsourced lights), and the
 * bloom lives in the post chain (rnd.bloom's compositor pass).
 */
import type { World } from '../../core/world'
import * as shell from './shell'
import * as openings from './openings'
import * as env from './env'
import * as night from '../night'
import * as kitchen from './kitchen'
import * as dining from './dining'
import * as living from './living'
import * as beds from './beds'
import * as extra from './extra'

const tick = (): Promise<void> => new Promise((r) => setTimeout(r, 0))

/** Async so the tab keeps breathing between the room builds. */
export async function buildAll(w: World): Promise<void> {
  shell.build(w)
  await tick()
  openings.build(w)
  await tick()
  // Night conversion (user-directed deviation): the exterior set is still the
  // build_env.py port; night.ts swaps only the world beyond it — sky, moon and
  // city ambience in place of env.skyAndSun(w, 0.145, 2.4), which stays as the
  // day parity baseline.
  env.build(w, { kwSkylight: night.KW_SKYGLOW })
  night.build(w)
  await tick()
  kitchen.build(w)
  await tick()
  dining.build(w)
  await tick()
  living.build(w)
  await tick()
  beds.build(w)
  beds.dressHall(w)
  extra.build(w)
  await tick()
  w.finalize()
}
