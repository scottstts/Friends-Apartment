/** Entry point: WebGPU renderer (no fallback), AgX view transform, the
 * compositor bloom from rnd.py, pointer-lock player, intro/pause veils. */
import './scene/shadows'
import * as THREE from 'three/webgpu'
import { pass } from 'three/tsl'
import { bloom } from 'three/examples/jsm/tsl/display/BloomNode.js'
import { World } from './scene/world'
import { buildAll } from './scene/build'
import { PlayerControls } from './player/controls'
import { Ui } from './ui/ui'

interface GpuProbe {
  requestAdapter(): Promise<{
    limits: { maxSampledTexturesPerShaderStage: number; maxSamplersPerShaderStage: number }
  } | null>
}

async function boot(): Promise<void> {
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
  // Blender's default view transform: AgX at exposure 0
  renderer.toneMapping = THREE.AgXToneMapping
  renderer.toneMappingExposure = 1.0
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
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
  let started = false

  const ui = new Ui({
    onEnter: () => {
      if (!controls) return
      renderer.domElement.requestPointerLock()
    },
    onResume: () => {
      renderer.domElement.requestPointerLock()
    },
  })

  document.addEventListener('pointerlockchange', () => {
    const locked = document.pointerLockElement === renderer.domElement
    if (controls) controls.enabled = locked
    if (locked) {
      started = true
      ui.enterGame()
    } else if (started) {
      ui.showPause()
    }
  })

  window.addEventListener('resize', () => {
    setSize()
    camera.aspect = innerWidth / innerHeight
    camera.updateProjectionMatrix()
  })

  // Build the whole apartment (heavy, one-time) after the veil paints.
  // buildAll yields between rooms so the tab never hard-blocks.
  await new Promise((r) => setTimeout(r, 30))
  const world = new World()
  await buildAll(world)

  controls = new PlayerControls(camera, world.colliders)
  controls.spawn(2.3, -1.15, 6.4, 3.9)

  // rnd.bloom(): threshold 1.0, strength 0.18, size 0.5 - only what is
  // genuinely brighter than white blooms.
  const postProcessing = new THREE.PostProcessing(renderer)
  // fix the pass's sample count up front so the pipelines precompiled below
  // match the ones the real frames use
  const scenePass = pass(world.scene, camera, { samples: renderer.samples })
  const scenePassColor = scenePass.getTextureNode('output')
  const bloomPass = bloom(scenePassColor, 0.18, 0.5, 1.0)
  postProcessing.outputNode = scenePassColor.add(bloomPass)

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
  const clock = new THREE.Clock()
  renderer.setAnimationLoop(() => {
    const dt = clock.getDelta()
    controls!.update(dt)
    if (warmFrames < shadows.length) {
      shadows[warmFrames].needsUpdate = true
    }
    postProcessing.render()
    warmFrames++
    if (warmFrames === shadows.length + 2) {
      ui.ready()
    }
  })
}

boot()
