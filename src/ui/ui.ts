/** Intro, pause and unsupported-browser veils.  Clean by rule: no explanation
 * or description text, no in-game UI - the whole window is the scene.
 *
 * The design language is the building's own hallway: the intro is the two
 * front doors seen from the landing, plain purple panels carrying only their
 * brass numbers - Chandler and Joey's 19 on the left, Monica's 20 on the
 * right - below the episode-title lockup and the six logo dots.  While the
 * scene builds the dots pulse; when the game is ready the dots settle, a
 * band of hallway light passes over each door and the underlight warms
 * beneath both apartments. A hovered door leans forward; the chosen door
 * swings open and the hallway falls through onto its apartment scene.
 * Walking back to the front door in game returns to this
 * landing.  Pause is the ornate doorbell over the frozen frame; the
 * unsupported-browser page hangs the peephole-frame art over the door. */

import type { ApartmentId } from '../apartments/types'

export interface UiHooks {
  onEnter: (apartment: ApartmentId) => void
  onResume: () => void
}

/* Door-open duration; the CSS transitions below are timed to match. */
const OPEN_MS = 1300
const OPEN_MS_REDUCED = 520

const GRAIN =
  'url(\'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="180" height="180"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="180" height="180" filter="url(%23n)" opacity="0.05"/></svg>\')'

const CSS = `
:root { color-scheme: dark; }
html, body { margin: 0; height: 100%; overflow: hidden; background: #191330; }
canvas { display: block; }

.veil {
  position: fixed; inset: 0; z-index: 10;
  user-select: none; -webkit-user-select: none;
  -webkit-tap-highlight-color: transparent; outline: none;
  font-family: 'Didot', 'Bodoni MT', 'Playfair Display', Georgia, 'Times New Roman', serif;
  -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
  color: #f1e9d4;
}
/* One knob sizes the whole landing: door height, and everything scales off it. */
.veil.intro { --dh: min(58vh, 75vw); }
.veil.pause { z-index: 12; }
.veil.fatal { z-index: 30; }

/* ---- door material (the hallway pair and the fatal page) ---- */
.door {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background:
    linear-gradient(104deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.05) 49%, rgba(255,255,255,0.015) 55%, rgba(255,255,255,0) 64%),
    radial-gradient(120% 118% at 50% 32%, #6f5a9e 0%, #5b4884 40%, #46356b 72%, #342853 100%);
}
.grain { position: absolute; inset: 0; pointer-events: none; background-image: ${GRAIN}; background-size: 180px; }
.molding {
  position: absolute; inset: clamp(16px, 3.2vmin, 34px); pointer-events: none;
  border: 1px solid rgba(240,232,255,0.08); border-radius: 3px;
  box-shadow:
    inset 0 1px 2px rgba(16,9,32,0.55), inset 0 -1px 1px rgba(255,251,240,0.05),
    0 1px 1px rgba(255,251,240,0.05), 0 -1px 2px rgba(16,9,32,0.45);
}
.molding::after {
  content: ''; position: absolute; inset: 9px;
  border: 1px solid rgba(240,232,255,0.045); border-radius: 2px;
}
.doornum {
  position: absolute; top: calc(var(--dh) * 0.055); left: 0; right: 0; text-align: center;
  font-size: calc(var(--dh) * 0.125); letter-spacing: 0.2em; text-indent: 0.2em;
  background: linear-gradient(#f0d489, #b9903c 78%, #8d6a24);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 0.03em 0.035em rgba(18,10,36,0.7)) drop-shadow(0 -0.012em 0 rgba(255,240,200,0.18));
}
.underlight {
  position: absolute; left: 0; right: 0; bottom: 0; height: calc(var(--dh) * 0.1); pointer-events: none;
  background: radial-gradient(58% 130% at 50% 102%, rgba(255,206,120,0.28), rgba(255,206,120,0) 70%);
  opacity: 0.45; transition: opacity 1.4s ease;
}
.ready .underlight { opacity: 0.8; }
.doorshade {
  position: absolute; inset: 0; pointer-events: none; opacity: 0;
  background: linear-gradient(100deg, rgba(8,4,20,0) 30%, rgba(8,4,20,0.75) 95%);
  transition: opacity 1s ease;
}

/* ---- the landing: title lockup over the two front doors ---- */
.hall {
  position: absolute; inset: 0; padding: 0 24px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: calc(var(--dh) * 0.085);
  background: radial-gradient(95% 72% at 50% 30%, #2b2152 0%, #1c1537 55%, #110c24 100%);
  transform-origin: calc(50% + var(--dh) * 0.375) 58%;
  transition: transform 1.15s cubic-bezier(0.55, 0.06, 0.28, 0.99), opacity 0.42s ease 0.8s;
  will-change: transform;
}
.doors { position: relative; display: flex; gap: calc(var(--dh) * 0.3); }
.doorway { position: relative; width: calc(var(--dh) * 0.45); height: var(--dh); perspective: 1500px; }
.doorway.left { perspective-origin: 130% 50%; }
.doorway.right { perspective-origin: -30% 50%; }
.intro .door {
  border-radius: 4px; overflow: hidden;
  box-shadow: 0 calc(var(--dh) * 0.045) calc(var(--dh) * 0.09) rgba(8,4,18,0.55), 0 2px 8px rgba(8,4,18,0.5);
}
.intro .molding { inset: calc(var(--dh) * 0.032); }
/* Doors face each other across the hall, receding towards its centre. */
.intro .door { transition: transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1); }
.doorway.left .door { transform-origin: right center; transform: rotateY(13deg); }
.doorway.right .door { transform-origin: left center; transform: rotateY(-13deg); will-change: transform; }
.d19, .d20 { outline: none; }
/* Ready: the hallway light passes over each door once. */
.intro .door::after {
  content: ''; position: absolute; inset: 0; pointer-events: none; opacity: 0;
  background: linear-gradient(115deg, rgba(255,244,214,0) 32%, rgba(255,244,214,0.13) 46%, rgba(255,244,214,0.04) 53%, rgba(255,244,214,0) 64%);
  transform: translateX(-135%);
}
.intro.ready .door::after { animation: sheen 1.6s cubic-bezier(0.3, 0, 0.25, 1) 0.15s both; }
.intro.ready .doorway.right .door::after { animation-delay: 0.35s; }
@keyframes sheen {
  0% { transform: translateX(-135%); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateX(135%); opacity: 0; }
}

/* ---- centre column (fatal page) ---- */
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

.titles { text-align: center; }
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
  white-space: nowrap; text-shadow: 0 2px 22px rgba(16,8,36,0.5);
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
/* Not a control - the quiet word between the doors once the game is ready. */
.enter { position: absolute; left: 0; right: 0; top: calc(50% - 0.95em); text-align: center; pointer-events: none; }
.ready .enter { opacity: 0.92; transform: none; }
.ready .enter::after { transform: scaleX(1); }
.intro.ready .d19, .intro.ready .d20 { cursor: pointer; }
.pause:hover .cta, .pause:focus-visible .cta { color: #f7d98d; opacity: 1; }
.intro.ready .door:hover .underlight { opacity: 0.95; }
/* A hovered door leans forward off its hinge - hover only, so the keyboard
 * focus parked on 20 never enlarges it by itself. */
.intro.ready .doorway.left .door:hover { transform: rotateY(13deg) scale(1.045); }
.intro.ready .doorway.right .door:hover { transform: rotateY(-13deg) scale(1.045); }
.intro.loading { cursor: wait; }
.intro.loading .door { pointer-events: none; cursor: wait; }
.intro.loading .enter { opacity: 0.28; }
.intro.loading .dots i { animation: dotwave 1.5s ease-in-out infinite; animation-delay: var(--dot-delay); }
.intro.loading19 .doorway.right, .intro.loading20 .doorway.left { opacity: 0.52; transition: opacity 0.45s ease; }
.intro.loading19 .d19 .underlight, .intro.loading20 .d20 .underlight { animation: loadglow 1.15s ease-in-out infinite; }
@keyframes loadglow { 0%, 100% { opacity: 0.48; } 50% { opacity: 1; } }
.pause { cursor: pointer; }

.msg {
  margin: 0; font-size: clamp(0.78rem, 2vmin, 0.95rem);
  letter-spacing: 0.42em; text-indent: 0.42em; text-transform: uppercase;
  color: #d9c9a2; max-width: 30ch; line-height: 2.1;
}

/* ---- entrances ---- */
.intro .titles { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.08s both; }
.intro .doorway.left { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.22s both; }
.intro .doorway.right { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.34s both; }
.fatal .emblem { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.08s both; }
.fatal .msg { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.22s both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* ---- chosen apartment door opening onto its scene ---- */
.intro.open { pointer-events: none; }
.intro.open .hall { transform: scale(2.1); opacity: 0; }
.intro.open19 .hall { transform-origin: calc(50% - var(--dh) * 0.375) 58%; }
.intro.open20 .hall { transform-origin: calc(50% + var(--dh) * 0.375) 58%; }
.intro.open19 .doorway.left .door {
  transform: rotateY(87deg);
  transition: transform 1.18s cubic-bezier(0.68, 0.03, 0.22, 0.99);
}
.intro.open20 .doorway.right .door {
  transform: rotateY(-87deg);
  transition: transform 1.18s cubic-bezier(0.68, 0.03, 0.22, 0.99);
}
.intro.open .doorshade { opacity: 0.65; }

/* ---- pause: doorbell over the frozen frame ---- */
.veil.pause {
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(rgba(40,30,66,0.38), rgba(20,14,40,0.55));
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
  .intro .titles, .intro .doorway.left, .intro .doorway.right, .fatal .emblem, .fatal .msg,
  .intro .dots i, .intro .door::after, .veil.pause .stack, .pause:hover .bell svg { animation: none !important; }
  .intro .hall { transition: opacity 0.45s ease; }
  .intro.open .hall { transform: none; opacity: 0; }
  .intro.open19 .doorway.left .door { transform: rotateY(13deg); transition: none; }
  .intro.open20 .doorway.right .door { transform: rotateY(-13deg); transition: none; }
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

/** The ornate brass doorbell from the door, beads and dome under the same
 * moulded-relief treatment as the frame. */
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

function reducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
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
          <div class="grain"></div>
          <header class="titles">
            <h1 aria-label="The One with the Apartments"><span class="eyebrow" aria-hidden="true">The One With</span><span class="title-main" aria-hidden="true">The Apartments</span></h1>
            <div class="dots"><i></i><i></i><i></i><i></i><i></i><i></i></div>
          </header>
          <div class="doors">
            <div class="doorway left">
              <div class="door d19" role="button" tabindex="0" aria-label="Enter apartment 19">
                <div class="grain"></div>
                <div class="molding"></div>
                <span class="doornum">19</span>
                <div class="underlight"></div>
                <div class="doorshade"></div>
              </div>
            </div>
            <p class="cta enter" aria-hidden="true">Enter</p>
            <div class="doorway right">
              <div class="door d20" role="button" tabindex="0" aria-label="Enter apartment 20">
                <div class="grain"></div>
                <div class="molding"></div>
                <span class="doornum">20</span>
                <div class="underlight"></div>
                <div class="doorshade"></div>
              </div>
            </div>
          </div>
        </div>
      </div>`)
    this.enterDoors = {
      '19': this.intro.querySelector('.d19') as HTMLElement,
      '20': this.intro.querySelector('.d20') as HTMLElement,
    }
    for (const id of ['19', '20'] as const) {
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
    this.intro.classList.remove('loading19','loading20')
    this.intro.classList.add('loading',`loading${id}`)
    this.intro.setAttribute('aria-busy','true')
  }

  finishLoading():void {
    this.loading=false
    this.intro.classList.remove('loading','loading19','loading20')
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
      // Swing the selected door open and fall through it, then drop the veil.
      // Blur first: a keyboard entry would otherwise hold :focus-visible,
      // whose straightened hover pose outranks the swing.
      this.enterDoors[this.selected].blur()
      this.intro.classList.add('open', `open${this.selected}`)
      this.hideTimer = window.setTimeout(() => {
        this.intro.style.display = 'none'
      }, reducedMotion() ? OPEN_MS_REDUCED : OPEN_MS)
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
    this.intro.classList.remove('open', 'open19', 'open20', 'loading', 'loading19', 'loading20')
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
