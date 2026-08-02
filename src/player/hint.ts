/** The contextual interaction prompt: one short serif line (plus an optional
 * second for sliding along the sofa), faded in only while a seat can be taken
 * or left or the front door offers the hallway.  Typography follows the intro
 * veil; nothing else joins it on screen. */

const CSS = `
.seat-hint {
  position: fixed; left: 50%; bottom: 9vh; transform: translateX(-50%);
  z-index: 5; pointer-events: none; text-align: center; user-select: none;
  font-family: 'Didot', 'Bodoni MT', 'Playfair Display', Georgia, 'Times New Roman', serif;
  color: rgba(239, 230, 200, 0.9); text-transform: uppercase;
  text-shadow: 0 1px 14px rgba(0, 0, 0, 0.65), 0 0 3px rgba(0, 0, 0, 0.5);
  opacity: 0; transition: opacity 0.35s ease;
}
.seat-hint.show { opacity: 1; }
.seat-hint .main { font-size: 0.82rem; letter-spacing: 0.34em; text-indent: 0.34em; }
.seat-hint .sub {
  margin-top: 0.55rem; font-size: 0.66rem; letter-spacing: 0.3em; text-indent: 0.3em;
  color: rgba(239, 230, 200, 0.62);
}
.seat-hint .k { color: #e3ac33; }
.seat-hint .sep { margin: 0 0.9em; color: rgba(227, 172, 51, 0.55); }
`

const STYLE_ID = 'friends-seat-hint'

export class SeatHint {
  private root: HTMLDivElement
  private main: HTMLDivElement
  private sub: HTMLDivElement
  private lastMain = ''
  private lastSub = ''
  private visible = false

  constructor() {
    if (!document.getElementById(STYLE_ID)) {
      const style = document.createElement('style')
      style.id = STYLE_ID
      style.textContent = CSS
      document.head.appendChild(style)
    }
    this.root = document.createElement('div')
    this.root.className = 'seat-hint'
    this.main = document.createElement('div')
    this.main.className = 'main'
    this.sub = document.createElement('div')
    this.sub.className = 'sub'
    this.sub.style.display = 'none'
    this.root.append(this.main, this.sub)
    document.body.appendChild(this.root)
  }

  /** Both arguments are fixed markup constants from seats.ts, never user data. */
  show(main: string, sub = ''): void {
    if (main !== this.lastMain) {
      this.main.innerHTML = main
      this.lastMain = main
    }
    if (sub !== this.lastSub) {
      this.sub.innerHTML = sub
      this.sub.style.display = sub ? '' : 'none'
      this.lastSub = sub
    }
    if (!this.visible) {
      this.root.classList.add('show')
      this.visible = true
    }
  }

  hide(): void {
    if (!this.visible) return
    this.root.classList.remove('show')
    this.visible = false
  }
}
