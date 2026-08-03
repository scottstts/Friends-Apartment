# Scenes

Each scene is a directory under `src/scenes/` exporting an
`ApartmentDefinition` from its `index.ts`. Scene modules own their layout
constants, geometry, materials, interactions and colliders; they share only
`core/`, `lib/`, `mats/` and the night backdrop.

## Shared night (`src/scenes/night.ts`)

A **user-directed deviation** used by all three scenes: the ground-truth
builds light their exteriors with a daytime Nishita sky (`build_env.py`); the
game plays at night. The exterior *sets* (facades, street, parapets) remain
the faithful `build_env` ports in each scene; `night.ts` replaces only what
lies beyond them:

- a procedural sky node on the renderer background: light-pollution gradient
  pooled toward Midtown, footprint-aware star field, small moon with haze
  halo, two hashed skyline layers — background pixels only, no geometry or
  textures;
- the same gradient baked once on the CPU into a small equirect used as
  `scene.environment`, so interior fill and glazing reflections agree with
  the windows;
- a merged unlit ring of mid-ground blocks at 55–160 m so looking down lands
  on rooftops;
- **MOON replaces SUN one-for-one** — same rig and shadow budget as the day
  port's sun, lunar energy, and the `backlight` translucency rig re-pointed
  at it. All hashes are seeded constants; the sky is deterministic.

Monica's `build.ts` keeps the day port alive as the parity baseline
(`env.skyAndSun` stays, unused) and passes `night.KW_SKYGLOW` into the
kitchen-window skylight panel.

## Monica's apartment — `scenes/monica/` (id `'20'`)

The original port; ground truth `build_scripts/Monicas_apt/`.

| File | Port of | Notes |
| --- | --- | --- |
| `index.ts` | — | contract adapter; spawn + front-door zone; empty seats list selects the built-in choreography in `player/seats.ts` |
| `L.ts` | `L.py` | layout constants (metres); origin at the west wall's inside face; +X east, +Y north, +Z up |
| `build.ts` | `build_all.py` `go()` | shell → openings → exterior → night → rooms → dressing; yields between rooms |
| `shell.ts` | `build_shell.py` | floor/walls/ceilings/mouldings/beam; wall colliders registered beside geometry |
| `walls.ts` | `s_walls.py` | wall panels, face-material assignment, moulding profiles (sweeps re-exported from `lib/molding.ts`) |
| `floor.ts` | `s_floor.py` | parquet, one slab per piece |
| `sopenings.ts` | `s_openings.py` | door/window/casing/sash/glazing components |
| `openings.ts` | `build_openings.py` | assembles every door and window into the shell |
| `env.ts` | `build_env.py` | exterior set seen through the windows + day sky/sun (parity baseline) |
| `kitchen.ts` | `f_kitchen.py` | turquoise casework, range, sink, fridge, shelving |
| `dining.ts` | `f_dining.py` | pedestal table + mismatched chairs |
| `living.ts` | `f_living.py` | sofa, armchairs, TV wall, rug, chandelier |
| `beds.ts` | `f_beds.py` | both bedrooms; `dressHall()` carries the hall/bathroom dressing (`f_hall.py` scope) |
| `extra.ts` | `f_extra.py` | small appliances and wall dressing |
| `props.ts` | `props.py` | reusable lathed/lofted prop builders + shelf filler with exact RNG call order (`blackbody` re-exported from `lib/color.ts`) |

## Chandler & Joey's apartment — `scenes/joey/` (id `'19'`)

Ground truth `build_scripts/Joeys_apt/`. Fully contained: own layout,
materials, props and interaction anchors.

| File | Port of / role |
| --- | --- |
| `index.ts` | contract: build order, spawn, both recliner seats, front-door zone |
| `contract.ts` | `JOEY_VISUAL_CONTRACT` — machine-checkable statement of identity/invariants/approved divergences derived from the build scripts |
| `layout.ts` | `L.py` dimensions |
| `shell.ts` / `walls.ts` / `floor.ts` / `tiles.ts` | `build_shell.py` / `s_walls.py` / `s_floor.py` (mosaic parquet) / `s_tile.py` (bathroom tiles, one slab per tile) |
| `joinery.ts` / `openings.ts` | `s_openings.py` five-panel doors + double-hung windows / `build_openings.py` placement |
| `kitchen.ts` / `living.ts` / `rooms.ts` / `extra.ts` | `f_kitchen.py` / `f_living.py` / `f_beds.py` / `f_extra.py` |
| `lighting.ts` | `f_light.py` — fixture-authored practicals (uses `lib/color.ts` blackbody) |
| `environment.ts` | light well + the approved shared night |
| `materials.ts` / `props.ts` | `mats.py` / `props.py` |

Approved divergences (recorded in `contract.ts`): the shared night replaces
the daytime sky, and only ceiling/under-cabinet fixtures own analytic lights —
every other fixture keeps an emissive bulb but no light, holding the shadow
budget.

## Central Perk — `scenes/perk/` (id `'perk'`)

Ground truth `build_scripts/Central_Perk/`. The only scene with non-flat
ground: the window bay is a raised platform, so the definition exports
`groundHeight` (`L.ground`) and the player steps up onto it.

| File | Port of / role |
| --- | --- |
| `index.ts` | contract: spawn on the platform inside the doors, hero-couch `CouchSpec` (three spots, A/D scooting), wing-back armchair, entrance-door zone |
| `layout.ts` | `L.py` + `ground()` sampler |
| `geo.ts` | Central-Perk-specific `mlib.py` add-ons the shared lib doesn't carry |
| `shell.ts` | `build_shell.py`: floors, bay platform, cast-iron columns/beams |
| `openings.ts` | `build_openings.py`: storefront glazing, entrance + back-of-house doors |
| `environment.ts` | `build_env.py` street corner + the shared night |
| `counter.ts` / `seating.ts` / `tables.ts` / `props.ts` | `f_counter.py` / `f_seating.py` (camelback couch with real diamond buttoning) / `f_tables.py` / `f_props.py` (every light created by the thing that emits it) |
| `dress.ts` | `f_layout.py` — placement pass: rugs first, every piece at its `L.py` anchor, settled onto whatever it stands on |
| `materials.ts` | `mats.py`, cache keys perk-prefixed |
| `text.ts` | chalk menu + SERVICE plate via `FontLoader` + bundled helvetiker typeface |

## Parity rules when touching a scene

1. `build_scripts/` is read-only and the only authority; never run Blender.
2. Match the ground truth's geometry, layout, material patterns and light
   energies technically; match the *render* where pipelines diverge
   (shadows, GI residuals, view transform).
3. Preserve Python RNG call order (geometry-and-world.md).
4. Any new deviation needs explicit user approval; record joey-side ones in
   `contract.ts`.
5. Cameras in the build scripts are out of scope; the player camera is the
   only camera.
