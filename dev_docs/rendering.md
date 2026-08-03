# Rendering

WebGPU only, TSL/NodeMaterial-driven, no WebGL fallback. The image is built to
match Blender Cycles renders of the ground-truth scenes to the naked eye.

## Resolution policy

```ts
const maxPixels = 4_000_000
const dpr = Math.min(window.devicePixelRatio, 1.7, Math.sqrt(maxPixels / (innerWidth * innerHeight)))
renderer.setPixelRatio(Math.max(1, dpr))
```

DPR is capped at 1.7 and by a 4 MP frame budget — balanced quality/perf,
re-applied on resize.

## Post chain (`src/main.ts`)

Single `PostProcessing` graph, created once over an empty scene and reused by
every scene (only `PassNode.scene` changes):

```
scenePass (MRT: output + view-space normal, MSAA samples = renderer.samples)
  ├─ depth + normal → GTAO (radius 0.32, thickness 1.25, distExp 1.5,
  │                        falloff 0.82, scale 0.9, 12 samples, full res)
  ├─ litColor = sceneColor * mix(1, ao.r, 0.34)       // 34 % AO influence
  ├─ bloom(sceneColor, strength 0.07, radius 0.5, threshold 1)
  ├─ hdr = litColor + bloom
  └─ blenderFilmicVeryHighContrast(hdr.rgb) → renderOutput(NoToneMapping)
```

Tone mapping is disabled on the renderer and in `renderOutput`
(`outputColorTransform = false`): the Filmic transform **is** the view
transform, and it must be the only one.

## Filmic view transform (`src/core/filmic.ts`)

Blender 3.6's OCIO chain — scene-linear sRGB → Filmic Log → *Very High
Contrast* look → sRGB display — reproduced in TSL:

- Log allocation constants and the highlight-desaturation threshold
  (`DESAT_START = 0.625`) come from Blender's bundled config.
- The 4096-entry look LUT is replaced by a logistic-curve fit with error
  < 4.9e-5 against the official table.

Because the look is a fixed curve, scene materials and lights are authored in
real scene-linear radiance and read correctly through it (see the radiance
hierarchy note in materials.md).

## Shadows

**Strategy** (`core/world.ts` + `main.ts`):

- All lamps are physical: Blender point-lamp watts → candela (`W / 4π`),
  `decay = 2`. Lights whose shadows do the *light-confinement* work (keeping
  light inside a room) carry real PCF shadow maps; small filler lamps get an
  EEVEE-style `distance` cutoff instead so they cannot reach through walls —
  WebGPU's default binding budget can't afford a map per lamp.
- PCF radius is kept compact (`max(2, size * 50)` cube-map texels): physical
  area-light contact shadows start sharp; a big constant kernel erases small
  props.
- `shadow.intensity` defaults to 0.72 (fixtures ≥ 9 cm) / 0.68: Cycles
  returns indirect practical-light bounce inside a cast shadow, PCF has no
  emissive-mesh GI, so fixtures carry a measured residual while the authored
  source power stays exact.
- After build, every map is rendered once and frozen (architecture.md,
  "shadow warm"); static scenes never update maps at runtime.

**The sampler-diet patch** (`src/core/shadows.ts`, imported for its side
effect at the top of `main.ts`, before any shader builds):

three's `ShadowNode` binds every shadow map twice in the lit fragment shader —
the depth comparison texture *plus* the render target's color texture, which
only matters for colored/translucent casters. Every caster here is opaque, but
the second binding costs a sampler per light and **Metal caps a fragment stage
at 16 samplers** — nine shadowed lights × 2 + the environment's 2 = 20 > 16,
blowing the pipeline on every Mac. The patch overrides
`ShadowNode.prototype.setupShadow` to keep only the depth-compare path
(identical output for opaque casters): 9 + 2 = 11 of 16. VSM (unused)
delegates to the stock implementation.

`main.ts` also raises `requiredLimits` (sampled textures / samplers per stage)
to `min(32, adapter limit)` where the adapter allows.

**Mesh contract** (`World.finalize`): every opaque mesh casts and receives.
`material.userData.noShadow` exempts transmissive glazing and emitter shells —
the depth-only path can't represent partial transmission, and treating either
as opaque would black out windows or self-occlude a practical.

## Compile/stall avoidance

Merged world-space meshes span rooms, so `frustumCulled = false` everywhere —
culling would also let a mesh dodge `compileAsync` and stall the frame it
first appears. Scene compilation is chunked (12 meshes per `compileAsync`
call) with a frame yielded between chunks.
