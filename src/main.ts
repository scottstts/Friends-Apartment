/** Entry point: WebGPU renderer (no fallback), Blender Filmic view, the
 * compositor bloom from rnd.py, pointer-lock player, intro/pause veils. */
import './scene/shadows'
import * as THREE from 'three/webgpu'
import { mix, mrt, normalView, output, pass, renderOutput, vec4 } from 'three/tsl'
import { bloom } from 'three/examples/jsm/tsl/display/BloomNode.js'
import { ao } from 'three/examples/jsm/tsl/display/GTAONode.js'
import { World } from './scene/world'
import { buildAll } from './scene/build'
import { PlayerControls } from './player/controls'
import { SeatingSystem } from './player/seats'
import { Ui } from './ui/ui'
import { applyCameraBookmark, inspectionFromUrl } from './scene/cameras'
import { blenderFilmicVeryHighContrast } from './filmic'
import { isDesktopChromium } from './platform'

interface GpuProbe {
  requestAdapter(): Promise<{
    limits: { maxSampledTexturesPerShaderStage: number; maxSamplersPerShaderStage: number }
  } | null>
}

async function boot(): Promise<void> {
  if (!isDesktopChromium(navigator)) {
    Ui.fatal('Desktop Chromium required')
    return
  }
  const inspection = inspectionFromUrl()
  if (!('gpu' in navigator)) {
    Ui.fatal('WebGPU required')
    return
  }
  // The scene binds ten-plus shadow maps and the environment in one fragment
  // stage; ask for elevated binding limits where the adapter offers them
  // (clamped to what it supports, so the device request can never fail).
  let requiredLimits: Record<string, number> = {}
  try {
    const adapter = await (navigator as unknown as { gpu: GpuProbe }).gpu.requestAdapter()
    if (adapter) {
      requiredLimits = {
        maxSampledTexturesPerShaderStage: Math.min(32, adapter.limits.maxSampledTexturesPerShaderStage),
        maxSamplersPerShaderStage: Math.min(32, adapter.limits.maxSamplersPerShaderStage),
      }
    }
  } catch {
    requiredLimits = {}
  }
  const renderer = new THREE.WebGPURenderer({ antialias: true, requiredLimits } as ConstructorParameters<
    typeof THREE.WebGPURenderer
  >[0])
  try {
    await renderer.init()
  } catch {
    Ui.fatal('WebGPU required')
    return
  }
  // The reference renders use Filmic / Very High Contrast at exposure 0.
  // Three has no Blender Filmic operator, so the exact view is applied in the
  // final TSL image pipeline below.
  renderer.toneMapping = THREE.NoToneMapping
  renderer.toneMappingExposure = 1.0
  renderer.shadowMap.enabled = inspection?.shadows ?? true
  // WebGPU's PCFSoft path has a fixed one-texel kernel and ignores a light's
  // authored shadow radius. The regular PCF path uses a rotated Vogel disk,
  // so the finite fixture/sun sizes below can produce visible soft penumbrae.
  renderer.shadowMap.type = THREE.PCFShadowMap
  document.body.appendChild(renderer.domElement)

  const setSize = (): void => {
    const maxPixels = 4_000_000
    const dpr = Math.min(window.devicePixelRatio, 1.7, Math.sqrt(maxPixels / (innerWidth * innerHeight)))
    renderer.setPixelRatio(Math.max(1, dpr))
    renderer.setSize(innerWidth, innerHeight)
  }
  setSize()

  const camera = new THREE.PerspectiveCamera(66, innerWidth / innerHeight, 0.02, 300)
  camera.up.set(0, 0, 1)

  let controls: PlayerControls | null = null
  let seats: SeatingSystem | null = null
  let started = false
  // E at the front door: the next pointer-lock exit opens the hallway veil
  // instead of the pause veil.
  let toHallway = false

  const ui = new Ui({
    onEnter: () => {
      if (!controls) return
      renderer.domElement.requestPointerLock()
    },
    onResume: () => {
      renderer.domElement.requestPointerLock()
    },
  })

  window.addEventListener('resize', () => {
    setSize()
    camera.aspect = innerWidth / innerHeight
    if (inspection) applyCameraBookmark(camera, inspection.view)
    else camera.updateProjectionMatrix()
  })

  // Build the whole apartment (heavy, one-time) after the veil paints.
  // buildAll yields between rooms so the tab never hard-blocks.
  await new Promise((r) => setTimeout(r, 30))
  const world = new World()
  await buildAll(world)

  controls = new PlayerControls(camera, world.colliders)
  controls.spawn(2.3, -1.15, 6.4, 3.9)
  if (!inspection)
    seats = new SeatingSystem(controls, camera, () => {
      toHallway = true
      document.exitPointerLock()
    })
  if (inspection) {
    applyCameraBookmark(camera, inspection.view)
    ui.enterGame()
  }

  // Blender Glare's 0.18 strength maps to a substantially lower additive
  // response in Three's bloom pyramid. Keep the authoritative threshold and
  // radius, with the strength calibrated by fixed-camera output parity.
  const postProcessing = new THREE.PostProcessing(renderer)
  // fix the pass's sample count up front so the pipelines precompiled below
  // match the ones the real frames use
  const scenePass = pass(world.scene, camera, { samples: renderer.samples })
  scenePass.setMRT(
    mrt({
      output,
      normal: normalView,
    }),
  )
  const scenePassColor = scenePass.getTextureNode('output')
  const scenePassNormal = scenePass.getTextureNode('normal')
  const scenePassDepth = scenePass.getTextureNode('depth')
  let litColor: THREE.Node = scenePassColor
  if (inspection?.ao !== false) {
    // Cycles' indirect transport supplies tight grounding at furniture feet
    // and wall/floor junctions. Full-resolution GTAO recovers a restrained
    // local visibility term, preventing broad practical-light masks from
    // doing the contact-shadow pass's job.
    const gtaoPass = ao(scenePassDepth, scenePassNormal, camera)
    gtaoPass.resolutionScale = 1
    gtaoPass.radius.value = 0.32
    gtaoPass.thickness.value = 1.25
    gtaoPass.distanceExponent.value = 1.5
    gtaoPass.distanceFallOff.value = 0.82
    gtaoPass.scale.value = 0.9
    gtaoPass.samples.value = 12
    litColor = scenePassColor.mul(mix(1, gtaoPass.getTextureNode().r, 0.34))
  }
  const bloomPass = bloom(scenePassColor, 0.07, 0.5, 1.0)
  const hdrOutput = inspection?.bloom === false ? litColor : litColor.add(bloomPass)
  if (inspection?.grade !== false) {
    // Bloom stays in scene-linear HDR, exactly as Blender's compositor does;
    // the Filmic view and its look own all final contrast and colour handling.
    const displayLinear = blenderFilmicVeryHighContrast(hdrOutput.rgb)
    postProcessing.outputColorTransform = false
    postProcessing.outputNode = renderOutput(
      vec4(displayLinear, hdrOutput.a),
      THREE.NoToneMapping,
      renderer.outputColorSpace,
    )
  } else {
    postProcessing.outputNode = hdrOutput
  }

  // ~180 procedural WGSL pipelines would freeze the tab for a very long time
  // if the first frame compiled them synchronously.  Precompile them with the
  // async pipeline path in small visibility chunks (yielding between), against
  // the exact render context the frame uses: the real scene (its environment
  // is part of the shader code) rendered into the scene pass target.
  const meshes: THREE.Mesh[] = []
  world.scene.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) meshes.push(o as THREE.Mesh)
  })
  renderer.setRenderTarget(scenePass.renderTarget)
  const CHUNK = 12
  for (let i = 0; i < meshes.length; i += CHUNK) {
    meshes.forEach((m, k) => {
      m.visible = k >= i && k < i + CHUNK
    })
    await renderer.compileAsync(world.scene, camera)
    await new Promise((r) => setTimeout(r, 0))
  }
  for (const m of meshes) m.visible = true
  renderer.setRenderTarget(null)

  // Static scene, static lights: shadow maps start frozen and each light
  // renders its map exactly once, one light per frame, so no single frame
  // pays for all 90-odd cube-face passes at once.
  const shadows: THREE.LightShadow[] = []
  for (const l of world.lights) {
    if (l.castShadow && l.shadow) {
      l.shadow.autoUpdate = false
      shadows.push(l.shadow)
    }
  }
  let warmFrames = 0
  let ready = false
  let rendering = false
  const clock = new THREE.Clock(false)

  const stopRendering = (): void => {
    if (!rendering) return
    renderer.setAnimationLoop(null)
    clock.stop()
    rendering = false
  }

  const renderFrame = (): void => {
    const dt = clock.getDelta()
    if (!inspection && controls?.enabled) controls.update(dt)
    seats?.update(dt)
    if (warmFrames < shadows.length) {
      shadows[warmFrames].needsUpdate = true
    }
    postProcessing.render()
    warmFrames++
    if (!ready && warmFrames === shadows.length + 2) {
      ready = true
      ui.ready()
      // The intro and inspection views retain this fully warmed static frame.
      // Gameplay rendering begins only after pointer lock is acquired.
      if (document.pointerLockElement !== renderer.domElement) stopRendering()
    }
  }

  const startRendering = (): void => {
    if (rendering) return
    rendering = true
    clock.start()
    renderer.setAnimationLoop(renderFrame)
  }

  document.addEventListener('pointerlockchange', () => {
    const locked = document.pointerLockElement === renderer.domElement
    if (controls) controls.enabled = locked
    if (locked) {
      started = true
      ui.enterGame()
      startRendering()
    } else if (started) {
      stopRendering()
      if (toHallway) {
        toHallway = false
        ui.showHallway()
      } else {
        ui.showPause()
      }
    }
  })

  // Warm the static shadow maps and final image once behind the loading veil.
  // Once ready, no frames are scheduled until the player enters the game.
  startRendering()
}

boot()
