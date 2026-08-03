# Geometry & the World registry

## MeshData (`src/lib/mesh.ts`)

The Blender builds work on polygon meshes (quads + n-gons) triangulated only
at render time, and every helper moves **vertices**, not object transforms —
everything lives in world space. `MeshData` mirrors that:

- `verts: Vec3[]`, `faces: number[][]` (polygons), optional `faceMat`
  (material-slot index per face), `shading` (flat, or smooth with an angle).
- Modifiers are applied **eagerly, in Blender stack order**: `solidify`,
  `subsurf`, bevel-on-box (`bevel`, `markBox`/`markPrism` scope which regions
  a bevel touches).
- `toGeometry()` runs once at the end: triangulation plus angle-based smooth
  shading into a `BufferGeometry`.

Transforms (`translate`, `rotateZ`, `rotX/Y`, `scaleMesh`, `transform4`),
`join`, `recalcNormals`, `cleanMesh` etc. all mutate MeshData in place and
return it for chaining.

## Modelling library (`src/lib/mlib.ts`)

1:1 port of the build scripts' `mlib.py` — profiles, lathes, lofts and mitred
sweeps producing real geometry: `box`, `prism`/`prismXZ`/`prismYZ`,
`panelWithHoles` (walls with openings), `loft`, `revolve`, `tubeAlong`,
`sweepRectFrame`, `sweepPlanarLoop`, `roundedRect`, `circle`, `bez`,
`cushion`, `hollowPrism`, `annularPrism`, `aperturedPrism`, plus re-exports of
the mesh ops. Central Perk carries a few set-specific additions in
`scenes/perk/geo.ts` (ports of its own `mlib.py` add-ons).

`src/lib/molding.ts` holds the mitred moulding sweep shared by the apartment
shells: `offsetPolyline` (right-hand offset with mitred corners) and
`runMolding` (sweep a closed `(z, depth-into-room)` profile along a plan
path; interior on the right of travel).

`src/lib/color.ts` holds `blackbody(kelvin)` — CIE-integrated Planckian
radiator tint in linear sRGB, used to color practical lights everywhere.

## Deterministic scatter (`src/lib/rng.ts`)

`PyRandom` reproduces CPython's `random.Random` (MT19937 plus CPython method
semantics) **bit for bit**. The Blender builds seed `random.Random(n)` to
scatter shelf clutter, jitter chairs and pick palette entries; identical
generator output is part of scene parity — the same jar lands on the same
shelf. When porting, preserve the **RNG call order** of the Python source; an
extra or skipped draw shifts every scatter after it.

## World (`src/core/world.ts`)

The Blender builds parent ~750 objects into collections; drawing that many
meshes individually would be absurd. `World` is the port's scene registry:

- `add(md, material, opts)` drops a MeshData into a **per-material bucket**;
  `finalize()` merges each bucket (`mlib.join`) into a single `THREE.Mesh` —
  same world-space vertices, far fewer draws.
- `opts.at` keeps a mesh separate with a position offset — rugs, whose
  materials read object-space coordinates from a centred mesh.
- `addMulti(md, mats)` splits a `faceMat`-tagged mesh (Blender face-material
  walls) into per-slot buckets.
- `remove(md, mat)` un-registers an unfinalized mesh — dressing builders use
  it for the same deterministic post-scatter culls as the Blender object
  collection.
- `addLight` / `pointLight` register lights (kept in `world.lights` so the
  runtime can warm and freeze their shadow maps). `pointLight` implements the
  Blender energy conversion and the shadow policy described in rendering.md.
- Finalize also feeds each material's `userData.generatedBox` with the merged
  geometry's bounding box — the port of Blender's *Generated* texture
  coordinates for the botanical plate materials.

## Collision model

Colliders are analytic, not mesh-derived at runtime: 2-D oriented boxes
(`Obb { cx, cy, hw, hh, cos, sin, z0, z1 }`) on the floor plane with a
vertical extent so low plinths don't block at chest height.

- `box2` (axis-aligned), `obb` (rotated), `colliderFromMesh` (mesh footprint
  + optional pad, via `opts.collide`/`collidePad` on `add`).
- `wallCollider(p0, p1, t, gaps)` covers a wall run with pass-through gaps
  (doorways) measured from `p0` — walkways stay clear by construction.

The player resolves against these as a circle (player.md). Scenes register
wall colliders alongside the wall geometry so every doorway stays passable;
the player is enclosed entirely by authored colliders.
