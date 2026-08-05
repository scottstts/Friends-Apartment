/** The pause veil's sound row: a horizontal master-volume slider and the
 * brass speaker that mutes, one line under Resume. No text, per the rules -
 * the slider reads by its gold fill and bead thumb, the speaker by its waves
 * or the cross that replaces them.
 *
 * The slider drives the master gain only, never a per-track level. It
 * answers a press-or-drag anywhere along its length, the scroll wheel, and
 * arrow keys when focused. The veil around the row is itself one big Resume
 * button, so every control here stops its own pointer and key events from
 * bubbling into it. Both controls mirror the same `MusicUi`, so state set
 * one way is always shown the other.
 */

import type { MusicUi } from '../audio/music'

const STYLE_ID = 'friends-sound'

const KEY_STEP = 0.05

const CSS = `
.sndrow {
  display: flex; align-items: center; justify-content: center;
  gap: clamp(14px, 2vmin, 24px);
}
.sndrow .snd, .sndrow .vol {
  appearance: none; -webkit-appearance: none;
  background: none; border: 0; margin: 0; padding: 0;
  cursor: pointer; outline: none; -webkit-tap-highlight-color: transparent;
  filter: drop-shadow(0 1px 2px rgba(10,7,3,0.6));
  opacity: 0.6; transition: opacity 0.3s ease;
}
.sndrow .snd:hover, .sndrow .snd:focus-visible,
.sndrow .vol:hover, .sndrow .vol:focus-visible { opacity: 1; }

.snd { line-height: 0; width: clamp(26px, 3.1vmin, 36px); }
.snd svg { display: block; width: 100%; height: auto; }
.snd .waves, .snd .slash {
  fill: none; stroke: #d8bd80; stroke-width: 2.4;
  stroke-linecap: round; transition: opacity 0.25s ease;
}
.snd .slash { opacity: 0; }
.sndrow.off .snd .waves { opacity: 0; }
.sndrow.off .snd .slash { opacity: 1; }
.sndrow.off .snd .horn { opacity: 0.62; }

/* ---- the slider: a recessed groove, gold fill, brass bead thumb ---- */
.vol {
  --v: 1;
  --tw: clamp(13px, 1.6vmin, 17px);
  position: relative; touch-action: none;
  width: clamp(120px, 15vmin, 180px);
  height: clamp(26px, 3.1vmin, 36px);
}
.vol .track {
  position: absolute; left: 0; right: 0; top: 50%;
  height: clamp(5px, 0.65vmin, 7px);
  transform: translateY(-50%); border-radius: 999px;
  background: linear-gradient(180deg, #120d07, #2a2113 65%, #3a2e1a);
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.75), 0 1px 1px rgba(255,244,214,0.14);
}
.vol .fill {
  position: absolute; left: 0; top: 0; bottom: 0;
  width: calc(var(--v) * 100%);
  border-radius: 999px;
  background: linear-gradient(180deg, #f0d489, #b9903c 70%, #8d6a24);
  box-shadow: 0 0 6px rgba(240,212,137,0.22);
  transition: opacity 0.25s ease;
}
.vol .thumb {
  position: absolute; top: 50%;
  left: calc(var(--v) * (100% - var(--tw)));
  width: var(--tw); aspect-ratio: 1;
  transform: translateY(-50%); border-radius: 50%;
  background: radial-gradient(circle at 38% 32%, #f7e5a5, #d9b562 50%, #93701f 90%);
  box-shadow: 0 1px 3px rgba(10,7,3,0.6), inset 0 1px 1px rgba(255,250,225,0.6), inset 0 -1px 1px rgba(46,30,4,0.5);
}
.sndrow.off .vol .fill { opacity: 0.25; }
.sndrow.off .vol .thumb { opacity: 0.55; }
`

function installStyles(): void {
  if (document.getElementById(STYLE_ID)) return
  const style = document.createElement('style')
  style.id = STYLE_ID
  style.textContent = CSS
  document.head.appendChild(style)
}

/** Cone in moulded brass, two radiating arcs, and the cross that replaces
 * them when the music is off. `p` namespaces the gradient per instance. */
function speakerSvg(p: string): string {
  return `
<svg viewBox="0 0 34 28" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="${p}gG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f0d489"/><stop offset="0.72" stop-color="#b9903c"/><stop offset="1" stop-color="#8d6a24"/>
    </linearGradient>
  </defs>
  <path class="horn" d="M2 10.5h4.6L13 4.4a1 1 0 0 1 1.7.7v16.8a1 1 0 0 1-1.7.7L6.6 17.5H2a1 1 0 0 1-1-1v-5a1 1 0 0 1 1-1z" fill="url(#${p}gG)"/>
  <g class="waves">
    <path d="M19.6 10.1a5.2 5.2 0 0 1 0 7.8"/>
    <path d="M23.6 6.6a10.2 10.2 0 0 1 0 14.8"/>
  </g>
  <g class="slash">
    <path d="M20.5 10.5 L28.5 17.5"/>
    <path d="M28.5 10.5 L20.5 17.5"/>
  </g>
</svg>`
}

/** Keep pointer and keyboard activity inside the row - the veil underneath
 * treats any click or Enter/Space as Resume. */
function contain(el: HTMLElement): void {
  for (const type of ['click', 'pointerdown', 'keydown'] as const) {
    el.addEventListener(type, (event) => event.stopPropagation())
  }
}

let instances = 0

export class SoundControls {
  readonly el: HTMLDivElement

  constructor(music: MusicUi) {
    installStyles()
    this.el = document.createElement('div')
    this.el.className = 'sndrow'

    const slider = document.createElement('div')
    slider.className = 'vol'
    slider.tabIndex = 0
    slider.setAttribute('role', 'slider')
    slider.setAttribute('aria-label', 'Music volume')
    slider.setAttribute('aria-valuemin', '0')
    slider.setAttribute('aria-valuemax', '100')
    slider.innerHTML = '<div class="track"><div class="fill"></div></div><div class="thumb"></div>'
    contain(slider)

    // Press anywhere along the groove to set, then drag; the captured
    // pointer keeps the gesture on the slider even off the veil.
    const setFromPointer = (event: PointerEvent): void => {
      const rect = slider.getBoundingClientRect()
      music.setVolume((event.clientX - rect.left) / rect.width)
    }
    let dragging = false
    slider.addEventListener('pointerdown', (event) => {
      dragging = true
      slider.setPointerCapture(event.pointerId)
      setFromPointer(event)
      event.preventDefault()
    })
    slider.addEventListener('pointermove', (event) => {
      if (dragging) setFromPointer(event)
    })
    for (const type of ['pointerup', 'pointercancel'] as const) {
      slider.addEventListener(type, () => { dragging = false })
    }
    slider.addEventListener('wheel', (event) => {
      event.preventDefault()
      event.stopPropagation()
      music.setVolume(music.volume - Math.sign(event.deltaY) * KEY_STEP)
    }, { passive: false })
    slider.addEventListener('keydown', (event) => {
      const step = { ArrowUp: KEY_STEP, ArrowRight: KEY_STEP, ArrowDown: -KEY_STEP, ArrowLeft: -KEY_STEP }[event.key]
      if (step !== undefined) music.setVolume(music.volume + step)
      else if (event.key === 'Home') music.setVolume(0)
      else if (event.key === 'End') music.setVolume(1)
      else return
      event.preventDefault()
    })

    const speaker = document.createElement('button')
    speaker.type = 'button'
    speaker.className = 'snd'
    speaker.innerHTML = speakerSvg(`s${instances++}`)
    contain(speaker)
    speaker.addEventListener('click', () => music.toggleMute())

    music.watch((muted, volume) => {
      this.el.classList.toggle('off', muted)
      speaker.setAttribute('aria-label', muted ? 'Unmute music' : 'Mute music')
      speaker.setAttribute('aria-pressed', String(muted))
      slider.style.setProperty('--v', String(volume))
      slider.setAttribute('aria-valuenow', String(Math.round(volume * 100)))
    })

    this.el.append(slider, speaker)
  }
}
