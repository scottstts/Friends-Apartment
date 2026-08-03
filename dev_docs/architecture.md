# Architecture

## One runtime, three scenes

`src/main.ts` owns everything scene-agnostic: the WebGPU renderer, the post
chain, the player camera, pointer lock, and the lifecycle that turns a chosen
door on the landing into a playable scene. Each scene ships as a self-contained
module under `src/scenes/<name>/` that the runtime knows only through the
`ApartmentDefinition` contract.

```
UI door click ─→ requestEntry(id) ─→ getApartment(id) ─→ activateApartment ─→ tryEnter
                                   (import → build → compile → warm, cached)
```

## The contract (`src/scenes/types.ts`)

```ts
interface ApartmentDefinition {
  id: '19' | '20' | 'perk'
  label: string
  build(world: World): Promise<void>       // fill a fresh World, then finalize()
  spawn: { position; lookAt }              // floor-plane coords
  interactions: { seats; couches?; door }  // authored SeatSpec/CouchSpec zones
  groundHeight?(x, y): number              // raised platforms (Central Perk bay)
  activate?(scene): void                   // scene-owned background/env state
}
```

`SeatSpec` is a single chair/bed eye target; `CouchSpec` is the multi-spot
sofa choreography (three cushions, A/D scooting) driven purely by authored
numbers. Monica's definition intentionally ships an **empty** seats list: her
mature choreography predates the contract and stays hard-wired in
`player/seats.ts` (see player.md); an empty list selects that fallback.

## Registry (`src/scenes/index.ts`)

`loadApartmentDefinition(id)` maps each id to a `dynamic import()` and caches
the promise for the life of the page. Together with the runtime's built-world
cache and HTTP module cache, a scene is fetched and evaluated at most once per
session. A rejected load is evicted so a retry can succeed.

## Boot sequence (`src/main.ts`)

1. **Gates** — `isDesktopChromium(navigator)` and `'gpu' in navigator`;
   failure renders the fatal veil (`Ui.fatal`), nothing else initializes.
2. **Renderer** — `WebGPURenderer` with `requiredLimits` asking for up to 32
   sampled textures/samplers per stage (clamped to the adapter's own limits).
   Tone mapping is `NoToneMapping`: the view transform lives in the post chain
   (rendering.md). `THREE.Cache` is enabled; PCF shadow maps.
3. **Post chain** — built once over an empty `THREE.Scene`. The pass graph is
   scene-agnostic; only `scenePass.scene` is swapped when a scene activates.
4. **Shared pipeline warm-up** — after the DOM landing paints, one
   `postProcessing.render()` over the empty scene primes render targets and
   the scene-independent post shaders (`sharedPipelineReady`). A selected
   scene may download concurrently, but its compilation waits on this.

## Scene lifecycle (`getApartment`)

Per id, memoized in `built` / de-duplicated in `pending`:

1. `loadApartmentDefinition(id)` (parallel with `sharedPipelineReady`).
2. `new World()` → `definition.build(world)`. Builders yield to the event loop
   between rooms (`await tick()`) so the tab keeps breathing.
3. **Chunked compile** — every mesh is collected, then
   `renderer.compileAsync()` runs with only 12 meshes visible at a time,
   yielding a frame between chunks: shader compilation never stalls one frame.
4. **Shadow warm** (`warmApartment`) — all shadow maps are frozen
   (`autoUpdate = false`) *before* the first pass (a light left on autoUpdate
   would re-render during every other light's pass), then each map renders
   once via `needsUpdate = true` + a full `postProcessing.render()`. Static
   scenes never re-render shadow maps after this. One settled full frame then
   primes AO/bloom/presentation for this scene's content.

`activateApartment` applies `definition.activate?.()`, swaps
`scenePass.scene`, points `PlayerControls` at the scene's colliders and
ground sampler, spawns the camera, and configures the `SeatingSystem`
(lazy-imported on first use). Authored interactions are used when the
definition ships seats/couches; otherwise `undefined` selects Monica's
built-in choreography.

## Entry, pause, hallway

- `requestEntry(id)` shows the loading state and immediately requests pointer
  lock — it must happen inside the door click's transient user activation,
  while import/build continue behind the landing. `tryEnter` starts the
  render loop only when both the scene is ready *and* the pointer is locked.
- `pointerlockchange` is the single source of truth: losing lock while in
  game stops the render loop and shows the pause veil — unless the seating
  system exited via the front door (`toHallway`), which shows the landing
  again. Nothing renders while a veil is up.
- The render loop is `clock.getDelta()` → `controls.update(dt)` →
  `seats.update(dt)` → `postProcessing.render()`.

## Error handling

Any failure in load/build/compile clears the pending entry, exits pointer
lock, and lands on `Ui.fatal('Scene unavailable')`. GPU probe failures
degrade to default limits rather than blocking boot.
