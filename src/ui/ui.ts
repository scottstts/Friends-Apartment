/** Intro, pause and unsupported-browser veils.  Clean by rule: no explanation
 * or description text, no in-game UI - the whole window is the scene.
 *
 * The design language is the building's own hallway, drawn procedurally
 * (CSS 3D planes + inline SVG, no photos): the camera stands inside the
 * corridor, so the floor runs from the bottom edge of the window, the aged
 * plaster-and-wainscot walls converge from the left and right edges, and the
 * green front doors hang on those side walls facing each other - Chandler
 * and Joey's 19 on the left, Monica's 20 on the right - each carrying only
 * its brass number and doorbell.  The corridor ends at the landing: a
 * blind-drawn window glowing on the far wall, the radiator beneath it, and
 * beside apartment 19 the hallway turns left, warm light washing around the
 * corner and across the floor.  That turn is the third doorway - a small
 * gold arrow over the coffee-house sign and its name wait before it, and
 * taking it goes down to the coffee house.
 *
 * While the scene builds the six logo dots pulse; when the game is ready the
 * dots settle, a band of hallway light passes over each door and the
 * underlight warms beneath both apartments.  A hovered doorway leans
 * forward, frame and all; choosing one fades the landing to black and lifts
 * the black into the apartment scene.  Choosing the turn instead fades both
 * front doors while the arrow and the destination's name hold the floor.
 * Walking back to the front door in game returns to this landing.  Pause is
 * the ornate doorbell over the frozen frame; the unsupported-browser page
 * hangs the peephole-frame art over a green door. */

import type { ApartmentId } from '../scenes/types'
import type { MusicUi } from '../audio/music'
import { SoundControls } from './sound'

export interface UiHooks {
  onEnter: (apartment: ApartmentId) => void
  onResume: () => void
  /** Backs the pause veil's mute-and-volume row; the transport itself is
   * driven by the pointer-lock lifecycle in main.ts, not by the veils. */
  music: MusicUi
}

/* Fade-to-black-then-scene duration; the CSS transitions below sum to it. */
const OPEN_MS = 900

const GRAIN =
  'url(\'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="180" height="180" filter="url(%23n)" opacity="0.05"/></svg>\')'

/* Low-frequency blotches multiplied over the render - the water stains and
 * grime of an old stairwell. */
const PATINA =
  'url(\'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="640" height="640"><filter id="p"><feTurbulence type="fractalNoise" baseFrequency="0.011 0.016" numOctaves="3" seed="11" stitchTiles="stitch"/><feColorMatrix type="matrix" values="0 0 0 0 0.24 0 0 0 0 0.20 0 0 0 0 0.11 0.8 0.5 0 0 0"/></filter><rect width="640" height="640" filter="url(%23p)" opacity="0.55"/></svg>\')'

/* Shared wall elevation: 111vh tall (0.5vh overlap past ceiling and floor
 * junctions), plaster above the chair rail at 73vh, panelled wainscot below,
 * baseboard from 105.5vh.  The corridor itself: horizon 45vh from the top,
 * floor 60vh below it, ceiling 50vh above it, half-width 50vw + 10vh so the
 * near cross-section always overshoots the window frame. */
const WALL_BANDS = `
    linear-gradient(180deg, #90816a, #6a5d4b) 0 72.2vh / 100% 1.6vh no-repeat,
    linear-gradient(90deg, rgba(0,0,0,0.14) 0 1px, rgba(255,244,220,0.05) 1px 2px, rgba(0,0,0,0) 2px) 0 74vh / 22.4vh 31.5vh repeat-x,
    linear-gradient(180deg, #211a0e 0vh, #57482a 12vh, #a08748 34vh, #cdb271 56vh, #d8c07c 73vh, #7b6d59 73vh, #665a48 95vh, #574c3d 105.5vh, #362d23 105.5vh, #241d16 111vh)`

const CSS = `
:root { color-scheme: dark; }
html, body { margin: 0; height: 100%; overflow: hidden; background: #16110b; }
canvas { display: block; }

.veil {
  position: fixed; inset: 0; z-index: 10;
  user-select: none; -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent; outline: none;
  font-family: 'Didot', 'Bodoni MT', 'Playfair Display', Georgia, 'Times New Roman', serif;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
  color: #f1e9d4;
}
/* The corridor is narrower than the window; the walls, floor and ceiling
 * extend --zf forward past the camera plane so their near ends still sweep
 * out beyond the frame edges. */
.veil.intro {
  background: #000;
  --P: 120vh;
  --hz: 45vh;
  --fdrop: 60vh;
  --crise: 50vh;
  --hw: calc(33vw + 7vh);
  --zf: 45vh;
  --depth: 280vh;
  --dh: 83.5vh;
  --dw: calc(var(--dh) * 0.45);
  --dnear: 12vh;
}
.veil.pause { z-index: 12; }
.veil.fatal { z-index: 30; }

/* ---- door material (the hallway pair and the fatal page) ---- */
.door {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background:
    linear-gradient(104deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.05) 49%, rgba(255,255,255,0.015) 55%, rgba(255,255,255,0) 64%),
    radial-gradient(120% 118% at 50% 32%, #5a8a4e 0%, #477140 40%, #34572e 72%, #264323 100%);
}
.grain { position: absolute; inset: 0; pointer-events: none; background-image: ${GRAIN}; background-size: 180px; }
.molding {
  position: absolute; inset: clamp(16px, 3.2vmin, 34px); pointer-events: none;
  border: 1px solid rgba(228,244,214,0.09); border-radius: 3px;
  box-shadow:
    inset 0 1px 2px rgba(8,16,6,0.55), inset 0 -1px 1px rgba(255,251,235,0.05),
    0 1px 1px rgba(255,251,235,0.05), 0 -1px 2px rgba(8,16,6,0.45);
}
.molding::after {
  content: ''; position: absolute; inset: 9px;
  border: 1px solid rgba(228,244,214,0.05); border-radius: 2px;
}
.doornum {
  position: absolute; top: calc(var(--dh) * 0.075); left: 0; right: 0; text-align: center;
  font-size: calc(var(--dh) * 0.125); letter-spacing: 0.2em; text-indent: 0.2em;
  background: linear-gradient(#f0d489, #b9903c 78%, #8d6a24);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 0.03em 0.035em rgba(10,18,8,0.7)) drop-shadow(0 -0.012em 0 rgba(255,240,200,0.18));
}
.peep {
  position: absolute; top: calc(var(--dh) * 0.245); left: 50%;
  width: calc(var(--dh) * 0.095); transform: translateX(-50%); pointer-events: none;
}
.peep svg { display: block; width: 100%; height: auto; }
.underlight {
  position: absolute; left: 0; right: 0; bottom: 0; height: calc(var(--dh) * 0.1); pointer-events: none;
  background: radial-gradient(58% 130% at 50% 102%, rgba(255,206,120,0.28), rgba(255,206,120,0) 70%);
  opacity: 0.45; transition: opacity 1.4s ease;
}
.ready .underlight { opacity: 0.8; }

/* ---- the corridor: one-point perspective from inside ---- */
.hall {
  position: absolute; inset: 0; background: #16110b;
  transition: opacity 0.35s ease;
}
/* The 3D scene never takes the pointer - hit-testing across intersecting
 * preserve-3d planes is unreliable, so clicks land on the screen-space
 * hotspots layered above instead. */
.view { position: absolute; inset: 0; perspective: var(--P); perspective-origin: 50% var(--hz); pointer-events: none; }
.room { position: absolute; inset: 0; transform-style: preserve-3d; }
.plane { position: absolute; }
/* Walls stay flat 3D planes - the doorways are painted onto them rather
 * than z-offset, so opacity animations (entrance rise, loading dim) never
 * toggle preserve-3d flattening and nothing snaps when they end. */
.wall {
  top: calc(var(--hz) - var(--crise) - 0.5vh);
  height: calc(var(--fdrop) + var(--crise) + 1vh);
  width: calc(var(--depth) + var(--zf));
}
/* The left wall stops 60vh short of the far wall - the hallway turns left
 * there towards the coffee house, so its cut end carries a lit corner rim
 * over a band of corner shadow. */
.wall.left {
  left: calc(50% - var(--hw));
  width: calc(var(--depth) + var(--zf) - 60vh);
  transform-origin: 0 50%; transform: rotateY(90deg) translateX(calc(-1 * var(--zf)));
}
.wall.right {
  left: calc(50% + var(--hw) - var(--depth) - var(--zf));
  transform-origin: 100% 50%; transform: rotateY(-90deg) translateX(var(--zf));
}
/* The wall paint rides a backing layer with the doorway's footprint cut out
 * (two mask layers, exclude-composited), so each opening is a true hole in
 * the plaster: a dimming door fades over hallway darkness instead of
 * revealing wainscot bands through itself.  The hole tucks 0.6vh inside the
 * casing so the resting door always overlaps its edges. */
.wall::before {
  content: ''; position: absolute; inset: 0;
  mask-image: linear-gradient(#000 0 0), linear-gradient(#000 0 0);
  mask-size: 100% 100%, calc(var(--dw) + var(--dh) * 0.06 - 1.2vh) calc(var(--dh) * 1.045 - 0.7vh);
  mask-repeat: no-repeat;
  mask-composite: exclude;
}
.wall.left::before {
  mask-position: 0 0, left calc(var(--zf) + var(--dnear) - var(--dh) * 0.03 + 0.6vh) bottom 0.6vh;
  background:
    linear-gradient(to left, rgba(255,216,150,0.22) 0 0.8vh, rgba(255,216,150,0) 2vh),
    linear-gradient(to left, rgba(20,14,6,0) 0.8vh, rgba(20,14,6,0.38) 2.6vh, rgba(20,14,6,0) 9vh),
    linear-gradient(90deg, rgba(20,14,6,0.45), rgba(20,14,6,0.1) 45%, rgba(255,236,185,0.1) 100%),${WALL_BANDS};
}
.wall.right::before {
  mask-position: 0 0, right calc(var(--zf) + var(--dnear) - var(--dh) * 0.03 + 0.6vh) bottom 0.6vh;
  background:
    linear-gradient(to right, rgba(20,14,6,0.4), rgba(20,14,6,0) 7vh),
    linear-gradient(270deg, rgba(20,14,6,0.45), rgba(20,14,6,0.1) 45%, rgba(255,236,185,0.1) 100%),${WALL_BANDS};
}
/* Floor and ceiling reach 60vh past the left wall so the far strip of them
 * reads as the branch hallway's floor and ceiling through the turn; the
 * warm pool at the opening is the coffee house's light spilling around the
 * corner. */
.floorp {
  left: calc(50% - var(--hw) - 60vh); width: calc(2 * var(--hw) + 61vh);
  top: calc(var(--hz) + var(--fdrop)); height: calc(var(--depth) + var(--zf));
  transform-origin: 50% 0; transform: rotateX(-90deg) translateY(calc(-1 * var(--zf)));
  /* The leftward overhang exists only for the branch corridor, so it is
   * clipped back to the far 60vh seen through the turn; the stretch hidden
   * behind the left wall would otherwise show through the doorway hole. */
  clip-path: polygon(60vh 0, 100% 0, 100% 100%, 0 100%, 0 calc(100% - 60vh), 60vh calc(100% - 60vh));
  background:
    radial-gradient(90vh 55vh at 60vh calc(100% - 25vh), rgba(255,208,125,0.2), rgba(255,208,125,0.05) 45%, rgba(255,208,125,0) 70%),
    radial-gradient(60vh 40vh at 40% 55%, rgba(40,36,30,0.25), rgba(40,36,30,0) 70%),
    radial-gradient(70vh 45vh at 75% 35%, rgba(40,36,30,0.2), rgba(40,36,30,0) 70%),
    linear-gradient(to right, rgba(10,8,5,0.35), rgba(10,8,5,0) 14vh),
    linear-gradient(to left, rgba(10,8,5,0.35), rgba(10,8,5,0) 14vh),
    linear-gradient(180deg, #55504a 0%, #6e6a62 45%, #8d897f 100%);
}
.ceiling {
  left: calc(50% - var(--hw) - 60vh); width: calc(2 * var(--hw) + 61vh);
  top: calc(var(--hz) - var(--crise) - var(--depth) - var(--zf)); height: calc(var(--depth) + var(--zf));
  transform-origin: 50% 100%; transform: rotateX(90deg) translateY(var(--zf));
  /* Same trim as the floor: this plane hangs bottom-up, so its far branch
   * strip is y 0-60vh and the wall-hidden overhang is clipped away. */
  clip-path: polygon(0 0, 100% 0, 100% 100%, 60vh 100%, 60vh 60vh, 0 60vh);
  background: linear-gradient(0deg, #191307, #40331a);
}
/* The far wall continues 60vh leftward past the corridor - the stretch seen
 * through the turn, washed by light from around the corner. */
.farwall {
  left: calc(50% - var(--hw) - 60vh); width: calc(2 * var(--hw) + 61vh);
  top: calc(var(--hz) - var(--crise) - 0.5vh);
  height: calc(var(--fdrop) + var(--crise) + 1vh);
  overflow: hidden;
  transform: translateZ(calc(-1 * var(--depth)));
  background:
    linear-gradient(to right, rgba(255,222,160,0.3), rgba(255,214,140,0.12) 30vh, rgba(255,214,140,0) 62vh),
    linear-gradient(to left, rgba(0,0,0,0.3), rgba(0,0,0,0) 10vh),
    linear-gradient(180deg, rgba(0,0,0,0.35), rgba(0,0,0,0) 12%),${WALL_BANDS};
}
.farwall > svg { position: absolute; left: calc(var(--hw) + 60vh); bottom: 0; height: 100%; width: 90vh; transform: translateX(-50%); }
.bayglow { opacity: 0.8; transition: opacity 0.6s ease; }

/* ---- the doorways, hung on the side walls ---- */
.doorway {
  position: absolute; bottom: 0.5vh; width: var(--dw); height: var(--dh);
  transform-origin: 50% 100%;
  transition: transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1);
  outline: none;
}
.wall.left .doorway { left: calc(var(--zf) + var(--dnear)); }
.wall.right .doorway { right: calc(var(--zf) + var(--dnear)); }
/* Painted wood casing, slightly proud of the plaster; the frame leans with
 * the whole doorway on hover. */
.doorway::before {
  content: ''; position: absolute; z-index: 0;
  inset: calc(var(--dh) * -0.045) calc(var(--dh) * -0.03) -0.5vh;
  border-radius: 3px;
  background: linear-gradient(180deg, #5e5040, #463b2d 60%, #332a1f);
  box-shadow:
    inset 0 0 0 2px rgba(20,14,8,0.5), inset 0 2px 3px rgba(255,240,210,0.1),
    0 calc(var(--dh) * 0.03) calc(var(--dh) * 0.06) rgba(10,7,3,0.5);
}
.intro .door {
  z-index: 2; border-radius: 3px; overflow: hidden;
  box-shadow: 0 calc(var(--dh) * 0.02) calc(var(--dh) * 0.05) rgba(10,7,3,0.45);
}
.intro .molding { inset: calc(var(--dh) * 0.032); }
/* Ready: the hallway light passes over each door once. */
.intro .door::after {
  content: ''; position: absolute; inset: 0; pointer-events: none; opacity: 0;
  background: linear-gradient(115deg, rgba(255,244,214,0) 32%, rgba(255,244,214,0.13) 46%, rgba(255,244,214,0.04) 53%, rgba(255,244,214,0) 64%);
  transform: translateX(-135%);
}
.intro.ready .door::after { animation: sheen 1.6s cubic-bezier(0.3, 0, 0.25, 1) 0.15s both; }
.intro.ready .wall.right .door::after { animation-delay: 0.35s; }
@keyframes sheen {
  0% { transform: translateX(-135%); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateX(135%); opacity: 0; }
}

/* ---- screen-space finish over the render ---- */
.patina {
  position: absolute; inset: 0; pointer-events: none;
  background-image: ${PATINA}; background-size: 640px;
  mix-blend-mode: multiply; opacity: 0.4;
}
/* Underlight pools by the doors, the glow at the hallway turn, the window's
 * warmth on the floor and the hallway vignette. */
.vign {
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(24vw 8vh at 20vw 90vh, rgba(255,199,110,0.15), rgba(255,199,110,0) 70%),
    radial-gradient(24vw 8vh at 80vw 90vh, rgba(255,199,110,0.15), rgba(255,199,110,0) 70%),
    radial-gradient(20vh 30vh at calc(50% - 12vw) 56vh, rgba(255,205,125,0.12), rgba(255,205,125,0) 70%),
    radial-gradient(52vh 30vh at 50% 58vh, rgba(255,236,185,0.07), rgba(255,236,185,0) 70%),
    radial-gradient(130% 105% at 50% 42%, rgba(0,0,0,0) 50%, rgba(10,7,3,0.62) 100%);
}

/* ---- the hallway-turn hotspot, round to Central Perk ---- */
.bay { position: absolute; left: 33vw; right: 33vw; top: 30vh; bottom: 25vh; outline: none; transition: opacity 0.3s ease; }
/* Screen-space click targets covering each door's projected footprint. */
.hot { position: absolute; top: 22vh; bottom: 2.5vh; width: calc(var(--hw) * 0.24); outline: none; }
.hot19 { left: calc(50% - var(--hw) * 0.93); }
.hot20 { right: calc(50% - var(--hw) * 0.93); }
/* The quiet invitation down the hall: a gold arrow breathing towards the
 * turn, above the destination's name. */
.wayup {
  position: absolute; left: 0; right: 0; bottom: 8vh;
  display: flex; justify-content: center; pointer-events: none;
  opacity: 0; transform: translateY(6px);
  transition: opacity 0.9s ease 0.45s, transform 0.9s ease 0.45s;
}
.wayup svg { height: 3.8vh; width: auto; filter: drop-shadow(0 1px 2px rgba(10,7,3,0.6)); }
.ready .wayup { opacity: 0.85; transform: none; }
.intro.ready .wayup svg { animation: drift 2.4s ease-in-out infinite; }
@keyframes drift {
  0%, 100% { transform: translateY(0); opacity: 0.75; }
  50% { transform: translateY(-0.7vh); opacity: 1; }
}
.intro.ready .bay:hover .wayup { opacity: 1; }
.intro:not(.ready) .bay, .intro:not(.ready) .hot, .intro.loading .bay { pointer-events: none; }
/* Once a front door is chosen the third destination leaves the stage; when
 * the turn itself is taken, the arrow and the name keep the floor instead. */
.intro.loading19 .bay, .intro.loading20 .bay, .intro.open .bay { opacity: 0; }
.intro.ready .bay { cursor: pointer; }
.intro.ready:has(.bay:hover) .bayglow { opacity: 1; }
.intro.loadingperk .bayglow { animation: perkpulse 1.15s ease-in-out infinite; }
/* The surviving arrow and name hold still while the coffee house loads. */
.intro.loadingperk .wayup svg { animation: none; }
@keyframes perkpulse { 0%, 100% { opacity: 0.8; } 40% { opacity: 1; } }

/* ---- centre column (fatal page) ---- */
/* The fatal page keeps the earlier purple door; the hallway pair stays green. */
.fatal .door {
  background:
    linear-gradient(104deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.05) 49%, rgba(255,255,255,0.015) 55%, rgba(255,255,255,0) 64%),
    radial-gradient(120% 118% at 50% 32%, #6f5a9e 0%, #5b4884 40%, #46356b 72%, #342853 100%);
}
.stack {
  position: relative; display: flex; flex-direction: column; align-items: center;
  text-align: center; gap: clamp(18px, 4.2vh, 44px); padding: 0 24px;
  transform: translateY(1.2vh); isolation: isolate;
}
/* decoration.png's art rides high on its square canvas; the negative margins
 * make the stack hug the visible frame. */
.fatal .emblem {
  --fh: clamp(270px, 50vmin, 455px);
  display: block; height: var(--fh); width: auto;
  margin: calc(var(--fh) * -0.08) 0 calc(var(--fh) * -0.31);
}

.titles { position: absolute; left: 0; right: 0; top: 4.5vh; text-align: center; pointer-events: none; }
h1 { margin: 0; }
.eyebrow {
  display: block; margin-bottom: clamp(10px, 1.8vh, 18px);
  font-size: clamp(0.66rem, 1.6vmin, 0.84rem); font-weight: 400;
  letter-spacing: 0.6em; text-indent: 0.6em; text-transform: uppercase;
  color: #cbb37f; opacity: 0.92;
}
.title-main {
  display: block; font-size: clamp(1.7rem, 4.6vw, 3.3rem); font-weight: 400;
  letter-spacing: 0.17em; text-indent: 0.17em; text-transform: uppercase;
  white-space: nowrap; text-shadow: 0 2px 22px rgba(20,12,4,0.55);
}
.dots { display: flex; justify-content: center; gap: clamp(12px, 1.6vw, 17px); margin-top: clamp(14px, 2.6vh, 24px); }
.dots i { width: 6px; height: 6px; border-radius: 50%; opacity: 0.25; }
.dots i:nth-child(3n+1) { background: #e2574b; }
.dots i:nth-child(3n+2) { background: #5d8fd3; }
.dots i:nth-child(3n)   { background: #f0c64a; }
.intro .dots i { animation: dotwave 1.5s ease-in-out infinite; }
.dots i:nth-child(1) { --dot-delay: 0s; animation-delay: var(--dot-delay); }
.dots i:nth-child(2) { --dot-delay: 0.15s; animation-delay: var(--dot-delay); }
.dots i:nth-child(3) { --dot-delay: 0.3s; animation-delay: var(--dot-delay); }
.dots i:nth-child(4) { --dot-delay: 0.45s; animation-delay: var(--dot-delay); }
.dots i:nth-child(5) { --dot-delay: 0.6s; animation-delay: var(--dot-delay); }
.dots i:nth-child(6) { --dot-delay: 0.75s; animation-delay: var(--dot-delay); }
@keyframes dotwave { 0%, 60%, 100% { opacity: 0.25; transform: none; } 30% { opacity: 1; transform: translateY(-3px); } }
/* Loading done: one unified settle in place of the wave. */
.intro.ready .dots i { animation: settle 0.55s ease both; opacity: 0.9; transition: opacity 0.8s ease; }
@keyframes settle {
  0% { opacity: 0.25; transform: none; }
  45% { opacity: 1; transform: translateY(-2.5px); }
  100% { opacity: 0.9; transform: none; }
}

.cta {
  margin: 0; font-size: clamp(0.72rem, 1.7vmin, 0.86rem);
  letter-spacing: 0.55em; text-indent: 0.55em; text-transform: uppercase;
  color: #ebc76f; opacity: 0; transform: translateY(6px);
  transition: opacity 0.9s ease 0.45s, transform 0.9s ease 0.45s, color 0.3s ease;
}
.cta::after {
  content: ''; display: block; height: 1px; width: 6.2em; margin: 0.85em auto 0;
  background: linear-gradient(90deg, transparent, rgba(233,193,92,0.85), transparent);
  transform: scaleX(0); transition: transform 1s cubic-bezier(0.2, 0.7, 0.2, 1) 0.7s;
}
.cta.show { opacity: 0.92; transform: none; }
.cta.show::after { transform: scaleX(1); }
/* The destination on the floor before the turn. */
.perk {
  position: absolute; left: 0; right: 0; bottom: 0.5vh;
  pointer-events: none; text-align: center;
  font-size: clamp(0.66rem, 1.55vmin, 0.8rem); letter-spacing: 0.42em; text-indent: 0.42em;
  transform-origin: 50% 100%;
  transition: opacity 0.5s ease, transform 0.4s cubic-bezier(0.22, 0.61, 0.36, 1), color 0.3s ease;
}
.perk span { display: block; }
/* The sign and the name sit as one centred piece; every reveal, hover and
 * loading state styles the parent, so the pair always moves together. */
.perk .row { display: flex; align-items: center; justify-content: center; gap: 0.9em; }
.perkicon { height: 2.8em; width: auto; filter: drop-shadow(0 1px 2px rgba(10,7,3,0.6)); }
.ready .perk { opacity: 0.92; transform: none; }
.ready .perk::after { transform: scaleX(1); }
.intro.ready .bay:hover .perk { color: #f7d98d; opacity: 1; transform: translateY(-0.35vh) scale(1.055); }
.intro.ready .hot { cursor: pointer; }
.pause:hover .cta, .pause:focus-visible .cta { color: #f7d98d; opacity: 1; }
.intro.ready:has(.hot19:hover) .d19 .underlight,
.intro.ready:has(.hot20:hover) .d20 .underlight { opacity: 0.95; }
/* A hovered doorway leans forward off the wall, casing and all - hover only,
 * so the keyboard focus parked on 20 never enlarges it by itself. */
.intro.ready:has(.hot19:hover) .doorway.left,
.intro.ready:has(.hot20:hover) .doorway.right { transform: scale(1.045); }
.intro.loading { cursor: wait; }
.intro.loading .hot { pointer-events: none; cursor: wait; }
.intro.loading .dots i { animation: dotwave 1.5s ease-in-out infinite; animation-delay: var(--dot-delay); }
.intro.loading19 .doorway.right, .intro.loading20 .doorway.left,
.intro.loadingperk .doorway.left, .intro.loadingperk .doorway.right { opacity: 0.52; transition: opacity 0.45s ease; }
.intro.loading19 .d19 .underlight, .intro.loading20 .d20 .underlight { animation: loadglow 1.15s ease-in-out infinite; }
@keyframes loadglow { 0%, 100% { opacity: 0.48; } 50% { opacity: 1; } }
.pause { cursor: pointer; }

.msg {
  margin: 0; font-size: clamp(0.78rem, 2vmin, 0.95rem);
  letter-spacing: 0.42em; text-indent: 0.42em; text-transform: uppercase;
  color: #d9c9a2; max-width: 30ch; line-height: 2.1;
}

/* ---- entrances ---- */
.intro .view { animation: fadein 0.9s ease both; }
@keyframes fadein { from { opacity: 0; } to { opacity: 1; } }
.intro .titles { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.08s both; }
/* Backwards fill: once risen these must release the cascade, or the filled
 * final keyframe would pin opacity over the loading dims above. */
.intro .doorway.left { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.22s backwards; }
.intro .bay { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.28s backwards; }
.intro .doorway.right { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.34s backwards; }
.fatal .emblem { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.08s both; }
.fatal .msg { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.22s both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* ---- chosen apartment: fade out to black, then fade the scene in ---- */
.intro.open { pointer-events: none; }
.intro.open .hall { opacity: 0; }
.veil.intro.open { opacity: 0; transition: opacity 0.45s ease 0.4s; }

/* ---- pause: doorbell over the frozen frame ---- */
.veil.pause {
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(rgba(52,42,26,0.38), rgba(22,16,9,0.55));
  -webkit-backdrop-filter: blur(16px) brightness(0.62) saturate(0.9);
  backdrop-filter: blur(16px) brightness(0.62) saturate(0.9);
  visibility: visible; transition: opacity 0.3s ease;
}
.veil.pause .stack { gap: clamp(18px, 3.4vh, 30px); transform: none; }
.veil.pause:not(.hidden) .stack { animation: rise 0.45s cubic-bezier(0.16, 0.7, 0.24, 1) both; }
.bell svg { display: block; height: clamp(110px, 19vmin, 168px); width: auto; }
.pause:hover .bell svg { animation: ringwig 0.6s ease; transform-origin: 50% 42%; }
@keyframes ringwig { 0%, 100% { transform: rotate(0); } 25% { transform: rotate(2.4deg); } 55% { transform: rotate(-2deg); } 80% { transform: rotate(1.2deg); } }

.veil.hidden {
  opacity: 0; visibility: hidden; pointer-events: none;
  transition: opacity 0.3s ease, visibility 0s 0.35s;
}

@media (prefers-reduced-motion: reduce) {
  .intro .view, .intro .titles, .intro .doorway.left, .intro .doorway.right, .intro .bay,
  .intro.loadingperk .bayglow, .intro.ready .wayup svg, .fatal .emblem, .fatal .msg,
  .intro .dots i, .intro .door::after, .veil.pause .stack, .pause:hover .bell svg { animation: none !important; }
}
`

const STYLE_ID = 'friends-ui'

function installStyles(): void {
  if (document.getElementById(STYLE_ID)) return
  const style = document.createElement('style')
  style.id = STYLE_ID
  style.textContent = CSS
  document.head.appendChild(style)
}

/** n beads of radius r on a circle - the doorbell's ornament rings. */
function beadRing(cx: number, cy: number, R: number, n: number, r: number): string {
  return Array.from({ length: n }, (_, i) => {
    const a = (i / n) * Math.PI * 2 - Math.PI / 2
    return `<circle cx="${(cx + R * Math.cos(a)).toFixed(1)}" cy="${(cy + R * Math.sin(a)).toFixed(1)}" r="${r}"/>`
  }).join('')
}

/** The ornate brass doorbell, beads and dome under the same moulded-relief
 * treatment as the frame - the pause emblem, and small on each front door. */
function bellSvg(p: string): string {
  return `
<svg viewBox="0 0 200 216" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="${p}bodyG" cx="0.42" cy="0.34" r="0.72">
      <stop offset="0" stop-color="#e8c56f"/><stop offset="0.55" stop-color="#b8913a"/><stop offset="1" stop-color="#6b4c15"/>
    </radialGradient>
    <radialGradient id="${p}domeG" cx="0.4" cy="0.35" r="0.75">
      <stop offset="0" stop-color="#f7e5a5"/><stop offset="0.45" stop-color="#d9b562"/><stop offset="0.85" stop-color="#93701f"/><stop offset="1" stop-color="#6b4c12"/>
    </radialGradient>
    <filter id="${p}moldB" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="2.2" result="b"/>
      <feSpecularLighting in="b" surfaceScale="3.2" specularConstant="0.5" specularExponent="14" lighting-color="#ffedbb" result="s">
        <fePointLight x="55" y="20" z="190"/>
      </feSpecularLighting>
      <feComposite in="s" in2="SourceAlpha" operator="in" result="si"/>
      <feFlood flood-color="#453008" flood-opacity="0.85" result="dk"/>
      <feComposite in="dk" in2="SourceAlpha" operator="in" result="dkin"/>
      <feOffset in="dkin" dx="0" dy="2" result="dko"/>
      <feMerge><feMergeNode in="dko"/><feMergeNode in="SourceGraphic"/><feMergeNode in="si"/></feMerge>
    </filter>
    <filter id="${p}dshB" x="-25%" y="-25%" width="150%" height="160%">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#140b26" flood-opacity="0.55"/>
    </filter>
  </defs>
  <g filter="url(#${p}dshB)">
    <g filter="url(#${p}moldB)" fill="#c49b45">
      ${beadRing(100, 104, 75.5, 22, 5.8)}
      <circle cx="100" cy="104" r="71" fill="url(#${p}bodyG)"/>
      <g fill="#9a7729">${beadRing(100, 104, 38.5, 18, 3.2)}</g>
    </g>
    <circle cx="100" cy="104" r="56" stroke="#5f4413" stroke-width="2" opacity="0.55" fill="none"/>
    <circle cx="100" cy="104" r="50" stroke="#f2d998" stroke-width="1.3" opacity="0.5" fill="none"/>
    <circle cx="100" cy="104" r="31" fill="url(#${p}domeG)"/>
    <circle cx="100" cy="104" r="31" stroke="#422d08" stroke-opacity="0.55" stroke-width="1.4" fill="none"/>
    <ellipse cx="90" cy="94" rx="7.5" ry="4.6" transform="rotate(-30 90 94)" fill="#ffffff" opacity="0.82"/>
  </g>
</svg>`
}

/** The far wall of the corridor as a flat elevation (the browser adds the
 * perspective): the blind-drawn window over its sill, the radiator on the
 * baseboard, plaster stains, and the daylight glow that answers a hover on
 * the stairwell.  10 units per vh; the floor junction sits at y 1105. */
function farSvg(p: string): string {
  const slats = Array.from({ length: 10 }, (_, i) => {
    const y = 236 + i * 36
    return `<rect x="297" y="${y}" width="306" height="26" fill="#d3c29a"/><rect x="297" y="${y + 21}" width="306" height="5" fill="#8f815f" opacity="0.5"/>`
  }).join('')
  const columns = Array.from({ length: 8 }, (_, i) => {
    const x = 325 + i * 32
    return `<rect x="${x}" y="840" width="26" height="240" rx="12" fill="url(#${p}radG)"/><ellipse cx="${x + 13}" cy="845" rx="10" ry="5" fill="#78624a" opacity="0.5"/>`
  }).join('')
  return `
<svg viewBox="0 0 900 1110" preserveAspectRatio="xMidYMax meet" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="${p}radG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#5c4d3e"/><stop offset="0.55" stop-color="#40352a"/><stop offset="1" stop-color="#2d241c"/>
    </linearGradient>
    <linearGradient id="${p}sillG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#7d684c"/><stop offset="0.5" stop-color="#5a4a31"/><stop offset="1" stop-color="#3b3023"/>
    </linearGradient>
    <radialGradient id="${p}glowG">
      <stop offset="0" stop-color="#ffedb8" stop-opacity="0.16"/><stop offset="1" stop-color="#ffedb8" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="${p}glow2G">
      <stop offset="0" stop-color="#ffe9b0" stop-opacity="0.12"/><stop offset="1" stop-color="#ffe9b0" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="${p}shadG">
      <stop offset="0" stop-color="#0d0a06" stop-opacity="0.5"/><stop offset="1" stop-color="#0d0a06" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <ellipse cx="330" cy="300" rx="170" ry="90" fill="#57451f" opacity="0.08"/>
  <ellipse cx="620" cy="260" rx="140" ry="80" fill="#57451f" opacity="0.06"/>

  <rect x="267" y="168" width="366" height="550" fill="#493c2e"/>
  <rect x="267" y="168" width="366" height="550" fill="none" stroke="#2c2418" stroke-opacity="0.6" stroke-width="5"/>
  <rect x="297" y="198" width="306" height="490" fill="#ffe9b0"/>
  <rect x="297" y="624" width="306" height="64" fill="#fff3cf"/>
  <rect x="297" y="198" width="306" height="38" fill="#cdbd94"/>
  <rect x="297" y="236" width="306" height="6" fill="#8f815f" opacity="0.6"/>
  ${slats}
  <rect x="297" y="598" width="306" height="26" fill="#c6b68d"/>
  <polygon points="297,198 410,198 297,470" fill="#ffffff" opacity="0.05"/>
  <rect x="294" y="195" width="312" height="496" fill="none" stroke="#7e6849" stroke-opacity="0.45" stroke-width="4"/>
  <rect x="246" y="718" width="408" height="34" fill="url(#${p}sillG)"/>
  <rect x="246" y="752" width="408" height="10" fill="#17100a" opacity="0.35"/>
  <rect x="285" y="762" width="330" height="28" fill="#43382a"/>
  <rect x="310" y="790" width="10" height="70" fill="#17100a" opacity="0.05"/>
  <rect x="575" y="790" width="8" height="55" fill="#17100a" opacity="0.05"/>

  <ellipse cx="450" cy="1102" rx="170" ry="20" fill="url(#${p}shadG)"/>
  <rect x="340" y="1076" width="26" height="26" fill="#33291f"/>
  <rect x="534" y="1076" width="26" height="26" fill="#33291f"/>
  ${columns}
  <rect x="317" y="812" width="266" height="30" rx="14" fill="#4c3f33"/>
  <rect x="330" y="817" width="240" height="5" fill="#78624a" opacity="0.45"/>
  <rect x="288" y="1048" width="16" height="14" fill="#3a2f24"/>
  <circle cx="302" cy="1055" r="15" fill="#55462f"/>

  <g class="bayglow">
    <ellipse cx="450" cy="440" rx="430" ry="400" fill="url(#${p}glowG)"/>
    <ellipse cx="450" cy="450" rx="250" ry="250" fill="url(#${p}glowG)"/>
    <ellipse cx="450" cy="830" rx="190" ry="40" fill="url(#${p}glow2G)"/>
  </g>
</svg>`
}

function build(html: string): HTMLDivElement {
  const t = document.createElement('template')
  t.innerHTML = html.trim()
  return t.content.firstElementChild as HTMLDivElement
}

/** Click or Enter/Space - both count as the engagement gesture pointer lock
 * needs. */
function activate(target: HTMLElement, fn: () => void): void {
  target.addEventListener('click', fn)
  target.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      fn()
    }
  })
}

export class Ui {
  private intro: HTMLDivElement
  private pause: HTMLDivElement
  private enterDoors: Record<ApartmentId, HTMLElement>
  private hooks: UiHooks
  private isReady = false
  private opened = false
  private entered = false
  private loading = false
  private hideTimer = 0
  private selected: ApartmentId = '20'

  constructor(hooks: UiHooks) {
    this.hooks = hooks
    installStyles()

    this.intro = build(`
      <div class="veil intro">
        <div class="hall">
          <div class="view">
            <div class="room">
              <div class="plane ceiling"></div>
              <div class="plane floorp"></div>
              <div class="plane wall left">
                <div class="doorway left">
                  <div class="door d19">
                    <div class="molding"></div>
                    <span class="doornum">19</span>
                    <div class="peep" aria-hidden="true">${bellSvg('p19')}</div>
                    <div class="underlight"></div>
                  </div>
                </div>
              </div>
              <div class="plane wall right">
                <div class="doorway right">
                  <div class="door d20">
                    <div class="molding"></div>
                    <span class="doornum">20</span>
                    <div class="peep" aria-hidden="true">${bellSvg('p20')}</div>
                    <div class="underlight"></div>
                  </div>
                </div>
              </div>
              <div class="plane farwall">${farSvg('f')}</div>
            </div>
          </div>
          <div class="patina" aria-hidden="true"></div>
          <div class="vign" aria-hidden="true"></div>
          <div class="grain"></div>
          <header class="titles">
            <h1 aria-label="The One with the Apartments"><span class="eyebrow" aria-hidden="true">The One With</span><span class="title-main" aria-hidden="true">The Apartments</span></h1>
            <div class="dots"><i></i><i></i><i></i><i></i><i></i><i></i></div>
          </header>
          <div class="hot hot19" role="button" tabindex="0" aria-label="Enter apartment 19"></div>
          <div class="hot hot20" role="button" tabindex="0" aria-label="Enter apartment 20"></div>
          <div class="bay" role="button" tabindex="0" aria-label="Enter Central Perk">
            <div class="wayup" aria-hidden="true"><svg viewBox="0 0 28 40" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="awG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0d489"/><stop offset="1" stop-color="#b9903c"/></linearGradient></defs><g fill="none" stroke="url(#awG)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14 37 V9"/><path d="M5 18 L14 7 L23 18"/></g></svg></div>
            <p class="cta perk"><span class="row"><img class="perkicon" src="/central_perk_icon.png" alt="" draggable="false"><span class="main">Central Perk</span></span></p>
          </div>
        </div>
      </div>`)
    this.enterDoors = {
      '19': this.intro.querySelector('.hot19') as HTMLElement,
      '20': this.intro.querySelector('.hot20') as HTMLElement,
      'perk': this.intro.querySelector('.bay') as HTMLElement,
    }
    for (const id of ['19', '20', 'perk'] as const) {
      activate(this.enterDoors[id], () => {
        if (!this.isReady || this.opened || this.loading) return
        this.selected = id
        this.hooks.onEnter(id)
      })
    }
    document.body.appendChild(this.intro)

    this.pause = build(`
      <div class="veil pause hidden" role="button" tabindex="0" aria-label="Resume">
        <div class="stack">
          <div class="bell">${bellSvg('b')}</div>
          <p class="cta show">Resume</p>
        </div>
      </div>`)
    activate(this.pause, () => {
      if (!this.pause.classList.contains('hidden')) this.hooks.onResume()
    })
    // Mute and volume, one line under Resume; the row contains its own
    // events so the veil's whole-surface Resume never fires from it.
    ;(this.pause.querySelector('.stack') as HTMLElement).appendChild(
      new SoundControls(hooks.music).el,
    )
    document.body.appendChild(this.pause)
  }

  ready(): void {
    this.isReady = true
    this.intro.classList.add('ready')
    this.enterDoors[this.selected].focus({ preventScroll: true })
  }

  beginLoading(id:ApartmentId):void {
    this.loading=true
    this.selected=id
    this.intro.classList.remove('loading19','loading20','loadingperk')
    this.intro.classList.add('loading',`loading${id}`)
    this.intro.setAttribute('aria-busy','true')
  }

  finishLoading():void {
    this.loading=false
    this.intro.classList.remove('loading','loading19','loading20','loadingperk')
    this.intro.removeAttribute('aria-busy')
    if(!this.opened&&this.intro.style.display!=='none')this.enterDoors[this.selected].focus({preventScroll:true})
  }

  enterGame(): void {
    this.hidePause()
    this.finishLoading()
    if (this.opened) return
    this.opened = true
    this.entered = true
    if (this.isReady) {
      // Fade the landing to black, lift the black onto the scene, then drop
      // the veil for good.
      this.enterDoors[this.selected].blur()
      this.intro.classList.add('open')
      this.hideTimer = window.setTimeout(() => {
        this.intro.style.display = 'none'
      }, OPEN_MS)
    } else {
      // Inspection bookmarks skip the doorway.
      this.intro.style.display = 'none'
    }
  }

  /** Back out onto the landing (the E exit at the front door): the veil
   * returns closed, ready to choose a door again. */
  showHallway(): void {
    if (!this.entered) return
    this.hidePause()
    window.clearTimeout(this.hideTimer)
    this.opened = false
    this.loading = false
    this.intro.classList.remove('open', 'loading', 'loading19', 'loading20', 'loadingperk')
    this.intro.removeAttribute('aria-busy')
    this.intro.style.display = ''
    if (this.isReady) this.enterDoors[this.selected].focus({ preventScroll: true })
  }

  showPause(): void {
    if (!this.entered) return
    this.pause.classList.remove('hidden')
    this.pause.focus({ preventScroll: true })
  }

  hidePause(): void {
    this.pause.classList.add('hidden')
  }

  static fatal(msg: string): void {
    installStyles()
    document.body.appendChild(
      build(`
      <div class="veil fatal">
        <div class="door">
          <div class="grain"></div>
          <div class="molding"></div>
          <div class="stack">
            <img class="emblem" src="/decoration.png" alt="" draggable="false">
            <p class="msg">${msg}</p>
          </div>
        </div>
      </div>`),
    )
  }
}
