/** Intro and pause overlays.  Clean by rule: no explanation or description
 * text, no in-game UI - the whole window is the scene. */

export interface UiHooks {
  onEnter: () => void
  onResume: () => void
}

const CSS = `
:root { color-scheme: dark; }
html, body { margin: 0; height: 100%; overflow: hidden; background: #0e0c16; }
canvas { display: block; }
.veil {
  position: fixed; inset: 0; z-index: 10;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(120% 140% at 50% 30%, #3d3763 0%, #262143 46%, #141126 100%);
  transition: opacity 0.6s ease;
  font-family: 'Didot', 'Bodoni MT', 'Playfair Display', Georgia, 'Times New Roman', serif;
  color: #efe6c8;
}
.veil.hidden { opacity: 0; pointer-events: none; }
.veil .frame {
  position: relative;
  padding: 4.2rem 4.6rem;
  border: 3px solid #e3ac33;
  outline: 1px solid rgba(227, 172, 51, 0.45);
  outline-offset: 7px;
  box-shadow: 0 0 60px rgba(0,0,0,0.45), inset 0 0 34px rgba(0,0,0,0.25);
  background: rgba(20, 17, 38, 0.25);
  text-align: center;
}
.veil .peep {
  position: absolute; top: -34px; left: 50%; transform: translateX(-50%);
  width: 16px; height: 16px; border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #f0d9a0, #7a5c1e 70%);
  box-shadow: 0 0 0 3px #e3ac33, 0 0 18px rgba(227,172,51,0.35);
}
.veil h1 {
  margin: 0;
  font-size: clamp(1.6rem, 4.2vw, 3.1rem);
  font-weight: 400;
  letter-spacing: 0.34em;
  text-indent: 0.34em;
  text-transform: uppercase;
  white-space: nowrap;
}
.veil h1 em { font-style: italic; letter-spacing: 0.12em; text-indent: 0; }
.veil .rule {
  width: 38%; height: 1px; margin: 1.6rem auto;
  background: linear-gradient(90deg, transparent, #e3ac33, transparent);
}
.veil button {
  appearance: none; cursor: pointer;
  font: inherit; font-size: 0.95rem; letter-spacing: 0.5em; text-indent: 0.5em;
  color: #141126; background: #e3ac33;
  border: none; padding: 0.72rem 2.4rem;
  transition: background 0.25s ease, transform 0.15s ease, opacity 0.4s ease;
}
.veil button:hover:enabled { background: #f2c14e; transform: translateY(-1px); }
.veil button:disabled { opacity: 0.28; cursor: default; }
.veil.pause .frame { padding: 3rem 3.6rem; }
.fatal {
  position: fixed; inset: 0; z-index: 20;
  display: flex; align-items: center; justify-content: center;
  background: #141126; color: #efe6c8;
  font-family: Georgia, serif; letter-spacing: 0.2em; text-transform: uppercase;
}
`

export class Ui {
  private intro: HTMLDivElement
  private pause: HTMLDivElement
  private enterBtn: HTMLButtonElement
  private hooks: UiHooks

  constructor(hooks: UiHooks) {
    this.hooks = hooks
    const style = document.createElement('style')
    style.textContent = CSS
    document.head.appendChild(style)

    this.intro = document.createElement('div')
    this.intro.className = 'veil'
    this.intro.innerHTML = `
      <div class="frame">
        <div class="peep"></div>
        <h1>The One With <em>the</em> Apartment</h1>
        <div class="rule"></div>
        <button disabled></button>
      </div>`
    this.enterBtn = this.intro.querySelector('button')!
    this.enterBtn.textContent = '· · ·'
    this.enterBtn.addEventListener('click', () => this.hooks.onEnter())
    document.body.appendChild(this.intro)

    this.pause = document.createElement('div')
    this.pause.className = 'veil pause hidden'
    this.pause.innerHTML = `
      <div class="frame">
        <div class="peep"></div>
        <div class="rule" style="margin-top:0"></div>
        <button>Resume</button>
      </div>`
    this.pause.querySelector('button')!.addEventListener('click', () => this.hooks.onResume())
    document.body.appendChild(this.pause)
  }

  ready(): void {
    this.enterBtn.disabled = false
    this.enterBtn.textContent = 'Enter'
  }

  enterGame(): void {
    this.intro.classList.add('hidden')
    this.pause.classList.add('hidden')
  }

  showPause(): void {
    if (!this.intro.classList.contains('hidden')) return
    this.pause.classList.remove('hidden')
  }

  hidePause(): void {
    this.pause.classList.add('hidden')
  }

  static fatal(msg: string): void {
    const d = document.createElement('div')
    d.className = 'fatal'
    d.textContent = msg
    document.body.appendChild(d)
  }
}
