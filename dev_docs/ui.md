# UI

Two modules — `src/ui/ui.ts` holds the four veils (intro landing, pause,
loading, unsupported-browser/fatal) and `src/ui/sound.ts` the pause veil's
sound row. Design rules are strict: **no explanation or description text, no
in-game UI** — the whole window is the scene. The theme music (audio.md) is
scene-scoped and its transport is driven entirely by the pointer-lock
lifecycle in `main.ts`; the veils only host the sound row.

## The landing

The design language is the building's own hallway, drawn procedurally (CSS 3D
planes + inline SVG; the only bitmaps are the small emblem/icon files in
`public/`):

- The camera stands inside the corridor: floor from the bottom edge, aged
  plaster-and-wainscot walls converging left and right.
- The green front doors hang on the side walls facing each other — Chandler
  and Joey's **19** left, Monica's **20** right — each carrying only its brass
  number and doorbell.
- The corridor ends at the landing: a blind-drawn window glowing on the far
  wall, the radiator beneath it, and beside apartment 19 the hallway turns
  left with warm light washing around the corner. That turn is the third
  doorway: a small gold arrow over the coffee-house sign and name (the one
  labelled element, an icon + "Central Perk"), and taking it goes down to the
  coffee house.

States (CSS classes on the intro veil):

- **building** — the six logo dots pulse while a scene builds.
- **ready** — dots settle, a band of hallway light passes over each door,
  underlight warms beneath both apartments; doorways lean forward on hover.
- **loading / loadingperk** — a chosen doorway fades the landing to black
  (`OPEN_MS = 900` total; the CSS transitions sum to it) and the black lifts
  into the scene. Door hotspots are pointer-disabled until ready and during
  loading.

Texture comes from data-URI SVG grain plus low-frequency stain blotches
multiplied over the render — no photo assets.

## Flow hooks

`new Ui({ onEnter, onResume, music })`:

| Method | Called by | Effect |
| --- | --- | --- |
| `ready()` | boot | enables the doors (`.ready`) |
| `beginLoading(id)` | `requestEntry` | loading state for that doorway |
| `finishLoading()` | scene ready or failed | clears loading state |
| `enterGame()` | pointer lock acquired | fades the veil out; scene visible |
| `showPause()` | pointer lock lost in game | pause veil |
| `showHallway()` | front-door exit | back to the landing |
| `hidePause()` | resume | — |
| `static fatal(msg)` | boot gates / scene failure | terminal page |

`onEnter(id)` is wired to `requestEntry` in `main.ts`; clicking a door must
synchronously request pointer lock (transient user activation), so the UI
calls straight into it. `onResume` re-requests pointer lock from the pause
veil.

The veils carry no transport state. `main.ts` pairs the music with the same
pointer-lock transitions that drive them: scene entry `begin()`s the loop,
the Esc that shows the pause veil `pause()`s it, the re-lock that hides the
veil `resume()`s it, and the hallway exit that shows the landing `reset()`s
it. `music` is the narrow `MusicUi` surface the pause veil's sound row
mirrors - mute and master volume only (audio.md).

## Pause & fatal

- **Pause** — the ornate doorbell rendered over the frozen frame (the render
  loop stops while unlocked, and so does the music). No text beyond what the
  landing already established. The whole veil is one Resume button, with one
  exception: the sound row under Resume — a horizontal master-volume slider
  and the brass mute speaker on one line — which stops its own pointer and
  key events so interacting with it never resumes the scene.
- **Fatal** (`Ui.fatal`) — the peephole-frame art (`decoration.png`) hung
  over a green door, with the single short message passed in ("Desktop
  Chromium required", "WebGPU required", "Scene unavailable"). Terminal:
  nothing else is interactive.

## Adding UI

Don't, unless directed. The seat hint (`player/hint.ts`) is the only in-game
overlay and follows the landing's typography (serif, uppercase, wide
tracking, gold accents `#e3ac33`). Any new surface must inherit that language
and the no-redundant-text rule.
