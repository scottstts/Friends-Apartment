# Player

The player is just the camera: no mesh, no sprint, no jump. Pointer lock +
WASD relative to where the camera looks, with authored collision and seating
choreography.

## Walker (`src/player/controls.ts`)

- **Pose** — Z-up. `applyPose(camera, x, y, z, yaw, pitch, roll)` builds the
  camera basis directly from yaw/pitch (optional up-vector roll) and is
  shared with the seating system so handovers are exact. Eye height
  `EYE = 1.62`.
- **Movement** — WASD projected onto the floor along the camera heading;
  `SPEED = 1.65 m/s` (interior walking pace), velocity eased by
  `1 − e^(−11·dt)`. `dt` is clamped to 50 ms. Keys clear on window blur.
- **Look** — mouse Δ × 0.0022 rad; pitch clamped just short of ±90°.
- **Collision** — circle (radius 0.24) vs the scene's `Obb[]`, up to three
  push-out iterations per frame; a collider is skipped when its vertical
  range is outside 0.25–1.55 m (low plinths and high soffits don't block).
  Deepest-axis push-out handles the centre-inside-box case.
- **Ground** — scenes with platforms provide `groundHeight(x, y)`
  (Central Perk's bay); the walker eases `floorZ` toward the sampled target
  (9/s) so steps ramp rather than snap.
- **Head bob** — speed-scaled amplitude (eases 8/s), phase advances
  `speed × 5.6`; vertical `sin(2φ) × 0.014`, lateral `sin(φ) × 0.008`, up
  roll `sin(φ) × 0.0035`. Stops smoothly with the walker.
- **Flags** — `external`: a director (the seating system) owns the camera;
  walking, collision and bob stand down. `lookLocked`: mouse look suspended
  during scripted transitions. `enabled` mirrors pointer-lock state.

## Seating (`src/player/seats.ts`)

`SeatingSystem(controls, camera, onDoor, interactions?)` runs its own state
machine over the walker.

**Targets.** Two kinds:

- `chairTarget` — single eye position + facing (chairs, beds).
- `couchTarget` — a `CouchSpec`: three cushion spots along the couch axis,
  approach-zone geometry (front line distance, behind threshold), authored
  stand-up pockets per spot, and A/D scooting one cushion at a time.

Where they come from: scenes that author `interactions` (joey's recliners,
perk's hero couch + armchair) get targets built from those specs
(`buildApartmentTargets`). Monica ships an empty list, which selects
`buildTargets()` — the original apartment-20 choreography hard-wired from her
layout constants (`scenes/monica/L.ts`): sofa (three cushions), window
armchair, slipper chair, both beds. This is a deliberate, documented coupling
from before the contract existed; the constants file lives with her scene and
this module imports it directly.

**Choreography.** Sitting eases over 1.3 s, standing 1.05 s, scoots 0.62 s,
with a custom bezier ease, a dip toward the cushion, a lean-forward push-up on
rising, and a seated breathing sway. During transitions the system sets
`controls.external` / `lookLocked` and drives `applyPose` itself; on standing
it `place()`s the walker at the authored stand pocket so control hand-back is
seamless.

**Door exit.** Each definition authors a front-door zone
(`interactions.door`); inside it the hint offers the hallway and E calls the
`onDoor` callback — `main.ts` sets `toHallway` and exits pointer lock, which
routes the pointerlockchange handler to the landing instead of the pause veil.

**Hints** (`src/player/hint.ts`) — one serif uppercase line (plus an optional
second for couch scooting), fixed near the bottom, fading in only while a
seat/stand/door action is available: `Press E to sit`, `A/D to move
left/right`, etc. Key letters are gold `<span class="k">`. Content is fixed
markup constants from seats.ts, never user data. This is the only in-game
overlay, per the no-UI rule.
