# Developer Docs

Three.js WebGPU + TSL port of three procedural Blender sets from *Friends* —
Monica's apartment (20), Chandler and Joey's apartment (19), and Central Perk —
playable first-person from a shared hallway landing.

The ground truth for every scene is `build_scripts/` (read-only Blender MCP
sources, one subdirectory per set). The port's contract is **end-result
parity**: technical parity wherever it guarantees the same render (geometry,
layout, material patterns, light energies), and a different technical
articulation only where the pipelines genuinely diverge — every such deviation
is user-directed, never silent.

## Documents

| Doc | Covers |
| --- | --- |
| [architecture.md](architecture.md) | Boot flow, scene registry and contract, build → compile → warm → activate lifecycle |
| [rendering.md](rendering.md) | WebGPU renderer, post chain (GTAO, bloom, Filmic), shadow strategy and GPU budgets |
| [geometry-and-world.md](geometry-and-world.md) | MeshData pipeline, modelling helpers, the `World` registry, colliders, RNG parity |
| [materials.md](materials.md) | TSL ports of Blender shading nodes, the procedural material library, material conventions |
| [scenes.md](scenes.md) | The three scenes: file maps, build-script correspondence, the shared night, parity rules |
| [player.md](player.md) | First-person controls, collision, seating choreography, interaction hints |
| [ui.md](ui.md) | The hallway landing, pause, loading and fatal veils |

## Source map

```
src/
  main.ts            entry: renderer, post chain, scene lifecycle, pointer lock
  core/              runtime shared by every scene
    world.ts           World: mesh buckets, colliders, lights, finalize()
    shadows.ts         side-effect patch: one sampler per shadow map (Metal cap)
    filmic.ts          Blender Filmic (Very High Contrast) view transform in TSL
    platform.ts        desktop-Chromium gate
  lib/               geometry & math helpers (no scene knowledge)
    mesh.ts            MeshData core, modifiers, triangulation → BufferGeometry
    mlib.ts            modelling helpers, 1:1 port of build_scripts mlib.py
    molding.ts         mitred moulding sweeps (offsetPolyline, runMolding)
    color.ts           blackbody(kelvin) → linear-sRGB light tint
    rng.ts             CPython-compatible random.Random (MT19937)
  mats/              shared procedural material library
    tsl.ts             TSL ports of Blender shading nodes (noise, brick, ramp…)
    mats.ts            named material builders, ported node graph by node graph
  player/            first-person systems
    controls.ts        pointer-lock WASD walker, circle-vs-OBB collision, head bob
    seats.ts           seating choreography (sit/stand/scoot), door-exit zones
    hint.ts            the single contextual prompt line
  ui/
    ui.ts              procedural hallway landing, pause, loading, fatal veils
  scenes/
    index.ts           lazy registry: ApartmentId → dynamic import, cached
    types.ts           ApartmentDefinition contract + interaction specs
    night.ts           shared night exterior (sky, moon, IBL, mid-ground city)
    monica/            apartment 20 (port of build_scripts/Monicas_apt)
    joey/              apartment 19 (port of build_scripts/Joeys_apt)
    perk/              Central Perk (port of build_scripts/Central_Perk)
```

Static images (the few supplied poster/painting textures and UI art) live in
`public/`; everything else — geometry, materials, sky — is procedural.

## Working rules

- `build_scripts/` is read-only and authoritative; parity deviations require
  explicit user approval. The night conversion and the practical-lighting
  budget are the standing approved deviations (see scenes.md).
- WebGPU + TSL first-class, no WebGL fallback.
- Run `npm run lint` and `npm run typecheck` after every coding task.
- No dev server / browser inspection from the agent; the user verifies
  visually. No commits from the agent.
