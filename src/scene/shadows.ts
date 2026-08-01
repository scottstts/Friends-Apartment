/** Shadow sampler diet.  three's ShadowNode binds every shadow map twice in
 * the lit fragment shader: the depth texture (comparison sample) plus the
 * render target's color texture, which only matters for colored/translucent
 * casters.  Every caster in this scene is opaque, but the second binding
 * costs a sampler per light and Metal caps a fragment stage at 16 samplers -
 * nine shadowed lights at 2 samplers each plus the environment's 2 blows the
 * pipeline (20 > 16) on every Mac.  This override keeps the depth-compare
 * path (identical output for opaque casters) and skips the color binding:
 * one sampler per shadow, 9 + 2 = 11 of 16.  VSM (unused here) delegates to
 * the stock implementation.  Import for its side effect before any shader
 * builds. */
import * as THREE from 'three/webgpu'
import { ShadowNode } from 'three/webgpu'
import { mix, reference, renderGroup, lightShadowMatrix, shadowPositionWorld, normalWorld } from 'three/tsl'
import type { Node, NodeBuilder, RenderTarget, DepthTexture, LightShadow, Light } from 'three/webgpu'

interface ShadowFilterInputs {
  filterFn: unknown
  shadowTexture: THREE.Texture
  depthTexture: DepthTexture
  shadowCoord: Node
  shadow: LightShadow
  depthLayer: number
}

interface ShadowNodeInternals {
  light: Light
  shadow: LightShadow
  shadowMap: RenderTarget | null
  depthLayer: number
  setupRenderTarget(
    shadow: LightShadow,
    builder: NodeBuilder,
  ): { shadowMap: RenderTarget; depthTexture: DepthTexture }
  setupShadowCoord(builder: NodeBuilder, shadowPosition: Node): Node
  setupShadowFilter(builder: NodeBuilder, inputs: ShadowFilterInputs): Node
  getShadowFilterFn(type: THREE.ShadowMapType): unknown
  setupShadow(builder: NodeBuilder): Node
}

/** Runtime shapes the .d.ts does not cover. */
interface ShadowBuilder {
  renderer: { shadowMap: { type: THREE.ShadowMapType } }
  camera: { coordinateSystem: THREE.CoordinateSystem }
}

interface ShadowRuntime {
  camera: { coordinateSystem: THREE.CoordinateSystem; updateProjectionMatrix(): void }
  filterNode?: unknown
  map: RenderTarget | null
}

const refGrouped = (name: string, type: string, target: object): Node =>
  (reference(name, type, target) as unknown as { setGroup(group: unknown): Node }).setGroup(renderGroup)

const proto = ShadowNode.prototype as unknown as ShadowNodeInternals
const stockSetupShadow = proto.setupShadow

proto.setupShadow = function (this: ShadowNodeInternals, builder: NodeBuilder): Node {
  const { renderer, camera } = builder as unknown as ShadowBuilder
  if (renderer.shadowMap.type === THREE.VSMShadowMap) return stockSetupShadow.call(this, builder)

  const { light, shadow } = this
  const rt = shadow as unknown as ShadowRuntime
  const { depthTexture, shadowMap } = this.setupRenderTarget(shadow, builder)

  rt.camera.coordinateSystem = camera.coordinateSystem
  rt.camera.updateProjectionMatrix()

  const shadowIntensity = refGrouped('intensity', 'float', shadow)
  const normalBias = refGrouped('normalBias', 'float', shadow)

  const shadowPosition = lightShadowMatrix(light).mul(shadowPositionWorld.add(normalWorld.mul(normalBias)))
  const shadowCoord = this.setupShadowCoord(builder, shadowPosition)

  const filterFn = rt.filterNode ?? this.getShadowFilterFn(renderer.shadowMap.type) ?? null
  if (filterFn === null) throw new Error('THREE.WebGPURenderer: Shadow map type not supported yet.')

  const shadowNode = this.setupShadowFilter(builder, {
    filterFn,
    shadowTexture: shadowMap.texture,
    depthTexture,
    shadowCoord,
    shadow,
    depthLayer: this.depthLayer,
  })

  const shadowOutput = mix(1, shadowNode, shadowIntensity).toVar()

  this.shadowMap = shadowMap
  rt.map = shadowMap

  return shadowOutput
}
