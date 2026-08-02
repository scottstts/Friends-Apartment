# Monica's apartment — build scripts

The `.blend` is a **pure function of this directory**. Nothing is modelled by
hand and nothing is imported: every mesh is built from profiles in code, every
material is a node graph, and the parquet is real per-piece geometry. Editing a
script and rebuilding reproduces the scene exactly, in about ten seconds and
roughly 750 objects.

`ref_images/` is the authority. The floor plan is rough layout only; the set
photographs are ground truth for everything else. Where this build departs from
them, it says so — see *Deliberate deviations* below.

## Rebuilding

`build_all.go(load)` takes a **loader callable** (it does not take a bool), which
it applies to each name in `MODS` so modules can be re-imported cleanly from
inside a running Blender. `build_shell.build()` opens with `mlib.purge()`, so a
rebuild always starts from an empty scene.

```python
import build_all, importlib
build_all.go(importlib.reload)
```

Order matters: shell → openings → exterior → sky/sun → rooms → dressing →
cameras. Dressing routines assume the casework they sit on already exists.

## The scripts

### Foundations

| Script | What it does |
| --- | --- |
| `L.py` | Every layout constant in metres. Origin is the inside face of the west (front-door) wall; **+X** east toward the bedrooms, **+Y** north toward the big window, **+Z** up. Holds wall lines, opening positions, furniture anchors and the palette. Change a room's size here, not in the builders. |
| `mlib.py` | Modelling helpers. Lofts, revolves, sweeps, prisms, booleans, bevels, and the transform helpers. **These move vertices, not objects** — a consequence that matters constantly, because it means object and generated texture coordinates end up in world space. `bake_surface_attr` exists for the cases where a texture must stay pinned to a curved surface anyway. |
| `mats.py` | Every material, as node graphs. `NB` is a small builder over Blender's node tree. Contains the shared `wood()`, plus `metal`, `fabric`, `gingham`, `floral_chintz`, `damask`, `wicker`, `perforated`, `plaster`, `brick_wall`, `subway_tile`, `velvet`, `pane`, `emissive`. |
| `props.py` | Reusable dressing that is not room-specific: crockery, jars, bottles, stemware, plants, framed art, curtains, lampshades, bulbs and lights. `fill_shelf` scatters a believable shelf. |

### Shell and structure

| Script | What it does |
| --- | --- |
| `build_shell.py` | Floor, walls, ceilings, mouldings, the exposed kitchen timber. Owns the shell materials. |
| `s_walls.py` | Wall/ceiling solids and mouldings. Each wall is one closed solid whose *inner* face lands exactly on its line in `L.py`. |
| `s_floor.py` | The parquet, as real geometry — one slab per piece. Tile module is a square with four mitred border strips, a central lozenge and four corner triangles; each piece gets its own grain direction via generated UVs and its own tone via a colour attribute. |
| `s_openings.py` | Door and window joinery: linings in the reveal, mitred architraves proud of the wall, sashes, glazing bars, hardware. |
| `build_openings.py` | Places every door and window into the shell, plus the front door's ironmongery and the alcove blind. |
| `build_env.py` | The exterior world seen through the windows — facades, the light well, the street, the landing outside the front door — plus sky and sun. |

### Rooms

| Script | What it does |
| --- | --- |
| `f_kitchen.py` | Turquoise casework, butcher block, the pro range, double sink, fridge, open shelving, the hanging pot rack, the rattan pendant, the ceiling dome. |
| `f_dining.py` | Round pedestal table and the mismatched chairs (hoop-back Windsors, one bentwood). |
| `f_living.py` | Sofa and armchair, slipper chair, ottoman, coffee table, glass table, Aubusson rug, the waterfall credenza, TV, window seat, art, drapes, sconces and the ceiling fitting. |
| `f_beds.py` | Both bedrooms, and `dress_hall()` — which is what actually dresses the bathroom and corridor. |
| `f_extra.py` | Small appliances and clutter: coffee maker, mixer, toaster, knife block, dish rack, paper towel, the door-wall hook and strap-hung frame. |

### Tools

| Script | What it does |
| --- | --- |
| `build_all.py` | The pipeline. `MODS`, `go()`, the camera set, and `fill()` — deliberately empty, see below. |
| `view.py` | Camera helpers. |
| `rnd.py` | Render helpers and output paths. |

### Not in the build

`f_hall.py` is **dead code**. It is not in `MODS` and nothing calls it. The live
bathroom and corridor dressing is `f_beds.dress_hall()`. Edits to `f_hall.py`
have no effect; delete it or wire it up, but do not assume it runs.

---

# Lighting rules

## The rule

**Every light in the scene must be justified by a visible object that could
plausibly emit it.** A lamp, a chandelier, a sconce, an overhead fixture, a
bulb, a window, the sun. No light may be placed simply because a corner renders
too dark.

This is the ordinary discipline of set lighting, and it is what makes a render
read as a photograph of a room rather than as a room with lights aimed at it.
A viewer cannot name the rule, but they can always tell when it has been broken:
a shadow falls the wrong way, a wall has a bright patch with nothing to explain
it, and the image quietly stops being believable.

In practice:

- **Every `POINT` / `AREA` / `SPOT` light needs a fixture at or beside its
  position** — inside the shade, at the bulb, behind the diffuser.
- **Daylight is fixed to real apertures.** The `SUN` plus the exterior sky is
  the source; anything standing in for sky through a specific window sits
  *outside* that window, aimed through it, never inside the room.
- **No "fill" lights.** `build_all.fill()` is empty on purpose. If a room is too
  dark, the fixture that lights it is missing, is in the wrong place, or is not
  bright enough. Fix the fixture.
- **Bulbs are modelled and emissive**, so a fixture reads as lit from its own
  geometry and not only from the invisible lamp inside it.
- **Audit in Cycles.** EEVEE approximates bounce and shadowing, so a scene can
  look acceptable there while breaking the rule. Cycles shows the true light
  transport, including whether a fixture's own geometry is blocking it.

The audit is mechanical: for every non-sun light, find the nearest mesh. If it
is further than a few centimetres, that light has no source.

## Deliberate deviations from the reference photos

The set photographs show **no ceiling and therefore no ceiling lights** — the
sets were built open to the studio roof and lit from the grid above, which is
why the reference frames stop at the picture rail.

This build has a real ceiling at `L.CZ = 3.26`, so it also needs the fixtures a
real apartment would hang from it. Two are added that no photo can confirm:

- `LR_ceiling` — semi-flush brass-and-opal fitting over the living room, on
  `L.AXIS` with the sofa, coffee table, rug and TV. The room's key light.
  Deliberately an ordinary fitting of the period rather than a chandelier: this
  is a rented walk-up, and a candle chandelier would read as a far grander flat
  than the one the photographs show.
- `K_ceiling` — a plain schoolhouse opal dome over the kitchen floor.

Both follow the design language already set by the wall sconces. Every other
object in the flat is still held to the photographs.
