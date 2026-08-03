# Materials

Fully procedural: no image textures except the handful of supplied poster/
painting files in `public/`. Every Blender material is ported **node graph by
node graph** into TSL `MeshPhysicalNodeMaterial`.

## Blender-node ports (`src/mats/tsl.ts`)

TSL implementations of the shading nodes the ground-truth materials are built
from, matching Blender's numeric behaviour:

| Helper | Blender node |
| --- | --- |
| `mapping(p, scale, rot, loc)` | Mapping (same order of operations) |
| `bnoise` / `bnoise3` | Noise Texture (fBM accumulation, roughness, distortion) |
| `wave(p, opts)` | Wave Texture (bands/rings, profiles) |
| `brickTex(p, opts)` | Brick Texture (returns `tint` + `fac`, Blender offsets) |
| `voronoi(p, scale, …)` | Voronoi (distance + color + position outputs) |
| `ramp(fac, stops, interp)` / `rampF` | ColorRamp (LINEAR / CONSTANT / B_SPLINE) |
| `layerWeightFacing(blend)` | Layer Weight (facing) |
| `bumpNormal(height, strength, dist)` | Bump |

The underlying gradient noise is MaterialX perlin, which shares
Blender-noise's range and character. `srgb`/`srgbColor`/`srgbTriple` convert
hex authoring colors to linear; `N` is the pragmatic `any`-typed node alias
used throughout TSL code.

**Porting rule (from a fixed prior decision):** when a Blender node's input
socket is *linked*, the socket's default value is dead — port the full linked
expression, not the kwarg/default.

## Material library (`src/mats/mats.ts`)

Named builders with a global cache (`get(name)` / each builder registers by
name — Central Perk prefixes its cache keys `perk*` so scene libraries can't
collide). `principled(opts)` maps Principled BSDF conventions; on top of it:
`wood`, `paint`, `plaster`, `brickWall`, `subwayTile`, `metal`, `wicker`,
`gingham`, `perforated`, `pane` (glazing), `emissive`, `fabric`, `damask`,
`velvet`, `floralChintz`, `botanical` (Generated-coordinate plate art),
`foliage`.

Scene-specific libraries (`scenes/joey/materials.ts`,
`scenes/perk/materials.ts`) port their own `mats.py` on top of the shared
builders and TSL helpers; Monica's materials are built inline in her room
modules, which predate the scene split.

## Conventions

- **`userData.noShadow`** — set on transmissive glazing and emitter shells;
  `World.finalize` exempts them from shadow casting (rendering.md explains
  why).
- **`userData.generatedBox`** — `{ min, size }` Vector3 uniforms a material
  reads to emulate Blender *Generated* coordinates; `World.finalize` fills it
  from the merged geometry's bounding box.
- **`backlight`** (`mats.ts`) — a small uniform rig (`dirToSun`, `sunColor`,
  `skyAmb`) for thin-surface translucency (blinds, shades, leaves). The
  active environment writes it: the night build points it at the moon with
  the baked sky's average as ambience.
- **Radiance hierarchy** — materials and lights are authored in scene-linear
  radiance against the Filmic view (rendering.md) with bloom thresholded at
  ~0.5: practicals ~0.2–0.8, lit windows ~0.5–2, night horizon glow ~0.09,
  zenith ~0.003. Keep new emitters inside this hierarchy or they'll bloom (or
  vanish) wrongly.
- **Light tints** come from `blackbody(kelvin)` (`src/lib/color.ts`), so a
  fixture's color and its energy stay independently authorable.
