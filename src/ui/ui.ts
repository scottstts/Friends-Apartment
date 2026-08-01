/** Intro, pause and unsupported-browser veils.  Clean by rule: no explanation
 * or description text, no in-game UI - the whole window is the scene.
 *
 * The design language is the apartment's own front door: the whole intro is
 * the purple door seen from the hallway - brass "20", the scrolled yellow
 * peephole frame drawn in SVG, an episode-title lockup and the six logo dots.
 * While the scene builds, the lens is dark and the dots pulse; when the game
 * is ready the light comes on behind the peephole.  Entering swings the door
 * open onto the live canvas.  Pause is the ornate doorbell over the frozen
 * frame; the unsupported-browser page is the same door with the lens unlit. */

export interface UiHooks {
  onEnter: () => void
  onResume: () => void
}

/* Door-open duration; the CSS transition below is timed to match. */
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
.veil.intro { perspective: clamp(1100px, 120vmax, 2400px); perspective-origin: 30% 50%; }
.veil.pause { z-index: 12; }
.veil.fatal { z-index: 30; }

/* ---- the door ---- */
.door {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background:
    linear-gradient(104deg, rgba(255,255,255,0) 40%, rgba(255,255,255,0.05) 49%, rgba(255,255,255,0.015) 55%, rgba(255,255,255,0) 64%),
    radial-gradient(120% 118% at 50% 32%, #6f5a9e 0%, #5b4884 40%, #46356b 72%, #342853 100%);
  transform-origin: left center;
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
  position: absolute; top: clamp(28px, 9vh, 120px); left: 0; right: 0; text-align: center;
  font-size: clamp(2.4rem, 8vmin, 10rem); letter-spacing: 0.2em; text-indent: 0.2em;
  background: linear-gradient(#f0d489, #b9903c 78%, #8d6a24);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  filter: drop-shadow(0 0.03em 0.035em rgba(18,10,36,0.7)) drop-shadow(0 -0.012em 0 rgba(255,240,200,0.18));
}
/* The unsupported-browser page has no title stack, so the numerals take the
 * open wall above the frame at full plate size. */
.fatal .doornum { top: clamp(40px, 17vh, 300px); font-size: clamp(3.2rem, 13.5vmin, 16rem); }
.underlight {
  position: absolute; left: 0; right: 0; bottom: 0; height: 12vh; pointer-events: none;
  background: radial-gradient(58% 130% at 50% 102%, rgba(255,206,120,0.28), rgba(255,206,120,0) 70%);
  opacity: 0.45; transition: opacity 1.4s ease;
}
.ready .underlight { opacity: 0.8; }
.doorshade {
  position: absolute; inset: 0; pointer-events: none; opacity: 0;
  background: linear-gradient(100deg, rgba(8,4,20,0) 30%, rgba(8,4,20,0.75) 95%);
  transition: opacity 1s ease;
}

/* ---- centre column ---- */
.stack {
  position: relative; display: flex; flex-direction: column; align-items: center;
  text-align: center; gap: clamp(18px, 4.2vh, 44px); padding: 0 24px;
  transform: translateY(1.2vh); isolation: isolate;
}
.emblem { position: relative; z-index: 1; transition: filter 0.45s ease; }
.emblem svg { display: block; overflow: visible; height: clamp(190px, 37vmin, 340px); width: auto; }
.titles { position: relative; z-index: 0; }
.fatal .emblem svg { height: clamp(160px, 30vmin, 270px); }
.intro.ready:hover .emblem, .intro.ready:focus-visible .emblem { filter: brightness(1.07); }

.lens-glow, .lens-halo { opacity: 0; transition: opacity 1.2s ease 0.1s; }
.ready .lens-glow { opacity: 0.95; }
.ready .lens-halo { opacity: 0.55; animation: breathe 4.4s ease-in-out 1.4s infinite; }
@keyframes breathe { 0%, 100% { opacity: 0.45; } 50% { opacity: 0.75; } }

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
.dots i:nth-child(1) { animation-delay: 0s; }
.dots i:nth-child(2) { animation-delay: 0.15s; }
.dots i:nth-child(3) { animation-delay: 0.3s; }
.dots i:nth-child(4) { animation-delay: 0.45s; }
.dots i:nth-child(5) { animation-delay: 0.6s; }
.dots i:nth-child(6) { animation-delay: 0.75s; }
@keyframes dotwave { 0%, 60%, 100% { opacity: 0.25; transform: none; } 30% { opacity: 1; transform: translateY(-3px); } }
.intro.ready .dots i { animation: none; opacity: 0.9; transition: opacity 0.8s ease; }

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
.ready .cta, .cta.show { opacity: 0.92; transform: none; }
.ready .cta::after, .cta.show::after { transform: scaleX(1); }
.intro.ready:hover .cta, .intro.ready:focus-visible .cta,
.pause:hover .cta, .pause:focus-visible .cta { color: #f7d98d; opacity: 1; }
.intro.ready, .pause { cursor: pointer; }

.msg {
  margin: 0; font-size: clamp(0.78rem, 2vmin, 0.95rem);
  letter-spacing: 0.42em; text-indent: 0.42em; text-transform: uppercase;
  color: #d9c9a2; max-width: 30ch; line-height: 2.1;
}

/* ---- entrances ---- */
.intro .emblem, .fatal .emblem { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.08s both; }
.intro .titles, .fatal .msg   { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.22s both; }
.intro .doornum, .fatal .doornum { animation: rise 0.95s cubic-bezier(0.16, 0.7, 0.24, 1) 0.34s both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* ---- door opening onto the scene ---- */
.intro .door { transition: transform 1.18s cubic-bezier(0.68, 0.03, 0.22, 0.99), opacity 0.3s ease 0.88s; will-change: transform; }
.intro.open { pointer-events: none; }
.intro.open .door { transform: rotateY(-87deg); opacity: 0; }
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
  .intro .emblem, .fatal .emblem, .intro .titles, .fatal .msg, .intro .doornum, .fatal .doornum,
  .intro .dots i, .ready .lens-halo, .veil.pause .stack, .pause:hover .bell svg { animation: none !important; }
  .intro .door { transition: opacity 0.45s ease; }
  .intro.open .door { transform: none; opacity: 0; }
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

/** The scrolled peephole frame.  Ids are prefixed so two instances never
 * collide.  The corner and crest scrolls are one spiral path reused under
 * mirrored transforms; a specular-lighting filter gives the flat gold fills
 * their moulded-ceramic relief. */
function frameSvg(p: string): string {
  return `
<svg viewBox="-20 -20 300 330" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="${p}gg" x1="0" y1="10" x2="0" y2="260" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#f6ce46"/><stop offset="0.55" stop-color="#e5ae24"/><stop offset="1" stop-color="#c9931a"/>
    </linearGradient>
    <radialGradient id="${p}ringG" cx="0.38" cy="0.32" r="0.75">
      <stop offset="0" stop-color="#9d7b33"/><stop offset="0.6" stop-color="#6f521d"/><stop offset="1" stop-color="#3c2b0d"/>
    </radialGradient>
    <radialGradient id="${p}lensG" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#221507"/><stop offset="0.75" stop-color="#0d0803"/><stop offset="1" stop-color="#050302"/>
    </radialGradient>
    <radialGradient id="${p}glowG" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#fff6d8"/><stop offset="0.45" stop-color="#ffd67e"/><stop offset="1" stop-color="#b97a1e" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="${p}haloG" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#ffd98c" stop-opacity="0.85"/><stop offset="1" stop-color="#ffd98c" stop-opacity="0"/>
    </radialGradient>
    <filter id="${p}mold" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="2.4" result="b"/>
      <feSpecularLighting in="b" surfaceScale="3.6" specularConstant="0.55" specularExponent="13" lighting-color="#fff1b8" result="s">
        <fePointLight x="60" y="-60" z="230"/>
      </feSpecularLighting>
      <feComposite in="s" in2="SourceAlpha" operator="in" result="si"/>
      <feFlood flood-color="#7c5a10" flood-opacity="0.9" result="dk"/>
      <feComposite in="dk" in2="SourceAlpha" operator="in" result="dkin"/>
      <feOffset in="dkin" dx="0" dy="2.4" result="dko"/>
      <feMerge><feMergeNode in="dko"/><feMergeNode in="SourceGraphic"/><feMergeNode in="si"/></feMerge>
    </filter>
    <filter id="${p}dsh" x="-25%" y="-25%" width="150%" height="160%">
      <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#140b26" flood-opacity="0.55"/>
    </filter>
    <path id="${p}vol" d="M70,-10 C56,-3 47,2 40,0 A20,20 0 0 1 0,0 A13.5,13.5 0 0 1 27,0 A8.5,8.5 0 0 1 10,0 A4.5,4.5 0 0 1 19,0"
      fill="none" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
    <path id="${p}volS" d="M52,-6 C46,-2 44,1 40,0 A20,20 0 0 1 0,0 A13.5,13.5 0 0 1 27,0 A8.5,8.5 0 0 1 10,0 A4.5,4.5 0 0 1 19,0"
      fill="none" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
    <g id="${p}corner">
      <g transform="translate(34,37) scale(1.12) translate(-34,-37)">
        <use href="#${p}vol" transform="translate(22,6.4) rotate(41.6)"/>
        <use href="#${p}vol" transform="translate(34,37) matrix(0 1 1 0 0 0) translate(-12,-30.6) rotate(41.6)"/>
        <circle cx="24" cy="30" r="6.5" stroke="none"/>
      </g>
      <rect x="-6.5" y="-17" width="13" height="34" rx="6.5" stroke="none" transform="translate(33.4,39.4) rotate(45)"/>
    </g>
    <g id="${p}crestT">
      <use href="#${p}volS" transform="translate(121,17.1) rotate(79.3) scale(0.55)"/>
      <use href="#${p}volS" transform="translate(139,17.1) scale(-1,1) rotate(79.3) scale(0.55)"/>
    </g>
    <g id="${p}crestL">
      <use href="#${p}volS" transform="translate(12.7,135.3) rotate(23.6) scale(0.55)"/>
      <use href="#${p}volS" transform="translate(12.7,154.7) scale(1,-1) rotate(-23.6) scale(0.55)"/>
    </g>
  </defs>
  <g filter="url(#${p}dsh)">
    <g filter="url(#${p}mold)" fill="url(#${p}gg)" stroke="url(#${p}gg)">
      <path stroke="none" fill-rule="evenodd" d="M64,37 h132 a30,30 0 0 1 30,30 v156 a30,30 0 0 1 -30,30 h-132 a30,30 0 0 1 -30,-30 v-156 a30,30 0 0 1 30,-30 z M90,75 h80 a18,18 0 0 1 18,18 v104 a18,18 0 0 1 -18,18 h-80 a18,18 0 0 1 -18,-18 v-104 a18,18 0 0 1 18,-18 z"/>
      <use href="#${p}corner"/>
      <use href="#${p}corner" transform="translate(260,0) scale(-1,1)"/>
      <use href="#${p}corner" transform="translate(0,290) scale(1,-1)"/>
      <use href="#${p}corner" transform="translate(260,290) scale(-1,-1)"/>
      <use href="#${p}crestT"/>
      <use href="#${p}crestT" transform="translate(0,290) scale(1,-1)"/>
      <use href="#${p}crestL"/>
      <use href="#${p}crestL" transform="translate(260,0) scale(-1,1)"/>
    </g>
    <g>
      <circle cx="130" cy="145" r="16" fill="url(#${p}ringG)"/>
      <path d="M118.7,133.7 A16,16 0 0 1 141.3,133.7" stroke="#f2dc9e" stroke-width="1.4" opacity="0.7" fill="none"/>
      <circle cx="130" cy="145" r="11" fill="#160f08"/>
      <circle cx="130" cy="145" r="8.4" fill="url(#${p}lensG)"/>
      <circle class="lens-glow" cx="130" cy="145" r="8.4" fill="url(#${p}glowG)"/>
      <ellipse cx="126.6" cy="141.2" rx="2" ry="1.3" transform="rotate(-32 126.6 141.2)" fill="#ffffff" opacity="0.8"/>
      <circle class="lens-halo" cx="130" cy="145" r="30" fill="url(#${p}haloG)"/>
    </g>
  </g>
</svg>`
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
  private hooks: UiHooks
  private isReady = false
  private opened = false
  private entered = false

  constructor(hooks: UiHooks) {
    this.hooks = hooks
    installStyles()

    this.intro = build(`
      <div class="veil intro" role="button" tabindex="0" aria-label="Enter the apartment">
        <div class="door">
          <div class="grain"></div>
          <div class="molding"></div>
          <span class="doornum">20</span>
          <div class="stack">
            <div class="emblem">${frameSvg('i')}</div>
            <div class="titles">
              <h1 aria-label="The One with the Apartment"><span class="eyebrow" aria-hidden="true">The One With</span><span class="title-main" aria-hidden="true">The Apartment</span></h1>
              <div class="dots"><i></i><i></i><i></i><i></i><i></i><i></i></div>
            </div>
            <p class="cta">Enter</p>
          </div>
          <div class="underlight"></div>
          <div class="doorshade"></div>
        </div>
      </div>`)
    activate(this.intro, () => {
      if (this.isReady && !this.opened) this.hooks.onEnter()
    })
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
    this.intro.focus({ preventScroll: true })
  }

  enterGame(): void {
    this.hidePause()
    if (this.opened) return
    this.opened = true
    this.entered = true
    if (this.isReady) {
      // Swing the door open onto the live scene, then drop the veil entirely.
      this.intro.classList.add('open')
      window.setTimeout(() => {
        this.intro.style.display = 'none'
      }, reducedMotion() ? OPEN_MS_REDUCED : OPEN_MS)
    } else {
      // Inspection bookmarks skip the doorway.
      this.intro.style.display = 'none'
    }
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
          <span class="doornum">20</span>
          <div class="stack">
            <div class="emblem">${frameSvg('f')}</div>
            <p class="msg">${msg}</p>
          </div>
        </div>
      </div>`),
    )
  }
}
