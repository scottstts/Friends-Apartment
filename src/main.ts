/** WebGPU apartment runtime: shared renderer and image pipeline at startup,
 * apartment-owned worlds imported, built, compiled and cached only after the
 * corresponding hallway door is chosen. */
import './scene/shadows'
import * as THREE from 'three/webgpu'
import { mix, mrt, normalView, output, pass, renderOutput, vec4 } from 'three/tsl'
import { bloom } from 'three/examples/jsm/tsl/display/BloomNode.js'
import { ao } from 'three/examples/jsm/tsl/display/GTAONode.js'
import { loadApartmentDefinition } from './apartments'
import type { ApartmentDefinition, ApartmentId } from './apartments/types'
import { World } from './scene/world'
import { PlayerControls } from './player/controls'
import type { SeatingSystem } from './player/seats'
import { Ui } from './ui/ui'
import { blenderFilmicVeryHighContrast } from './filmic'
import { isDesktopChromium } from './platform'

interface GpuProbe {
  requestAdapter():Promise<{limits:{maxSampledTexturesPerShaderStage:number;maxSamplersPerShaderStage:number}}|null>
}

interface BuiltApartment {
  definition:ApartmentDefinition
  world:World
  meshes:THREE.Mesh[]
}

const nextFrame=():Promise<void>=>new Promise((resolve)=>requestAnimationFrame(()=>resolve()))

async function boot():Promise<void> {
  if(!isDesktopChromium(navigator)){Ui.fatal('Desktop Chromium required');return}
  if(!('gpu' in navigator)){Ui.fatal('WebGPU required');return}
  let requestEntry:(id:ApartmentId)=>void=()=>undefined
  let requestResume:()=>void=()=>undefined
  const ui=new Ui({
    onEnter:(id)=>requestEntry(id),
    onResume:()=>requestResume(),
  })

  let requiredLimits:Record<string,number>={}
  try{
    const adapter=await (navigator as unknown as {gpu:GpuProbe}).gpu.requestAdapter()
    if(adapter)requiredLimits={
      maxSampledTexturesPerShaderStage:Math.min(32,adapter.limits.maxSampledTexturesPerShaderStage),
      maxSamplersPerShaderStage:Math.min(32,adapter.limits.maxSamplersPerShaderStage),
    }
  }catch{requiredLimits={}}

  const renderer=new THREE.WebGPURenderer({antialias:true,requiredLimits} as ConstructorParameters<typeof THREE.WebGPURenderer>[0])
  try{await renderer.init()}catch{Ui.fatal('WebGPU required');return}
  renderer.toneMapping=THREE.NoToneMapping
  renderer.toneMappingExposure=1
  renderer.shadowMap.enabled=true
  renderer.shadowMap.type=THREE.PCFShadowMap
  THREE.Cache.enabled=true
  document.body.appendChild(renderer.domElement)

  const setSize=():void=>{
    const maxPixels=4_000_000
    const dpr=Math.min(window.devicePixelRatio,1.7,Math.sqrt(maxPixels/(innerWidth*innerHeight)))
    renderer.setPixelRatio(Math.max(1,dpr));renderer.setSize(innerWidth,innerHeight)
  }
  setSize()

  const camera=new THREE.PerspectiveCamera(66,innerWidth/innerHeight,0.02,300)
  camera.up.set(0,0,1)
  let controls:PlayerControls|null=null
  let seats:SeatingSystem|null=null
  let active:BuiltApartment|null=null
  let entryTarget:ApartmentId|null=null
  let entryReady=false
  let started=false
  let toHallway=false
  let rendering=false
  const requestPointerLock=():void=>{
    try{void renderer.domElement.requestPointerLock().catch(()=>undefined)}catch{/* Unsupported options/permissions stay on the landing. */}
  }
  requestResume=()=>{if(active)requestPointerLock()}

  // The pass graph is apartment-agnostic and can be created over an empty
  // scene. Only PassNode.scene changes after an apartment cache entry exists.
  const emptyScene=new THREE.Scene()
  const postProcessing=new THREE.PostProcessing(renderer)
  const scenePass=pass(emptyScene,camera,{samples:renderer.samples})
  scenePass.setMRT(mrt({output,normal:normalView}))
  const scenePassColor=scenePass.getTextureNode('output')
  const scenePassNormal=scenePass.getTextureNode('normal')
  const scenePassDepth=scenePass.getTextureNode('depth')
  const gtaoPass=ao(scenePassDepth,scenePassNormal,camera)
  gtaoPass.resolutionScale=1;gtaoPass.radius.value=0.32;gtaoPass.thickness.value=1.25
  gtaoPass.distanceExponent.value=1.5;gtaoPass.distanceFallOff.value=0.82
  gtaoPass.scale.value=0.9;gtaoPass.samples.value=12
  const litColor:THREE.Node=scenePassColor.mul(mix(1,gtaoPass.getTextureNode().r,0.34))
  const bloomPass=bloom(scenePassColor,0.07,0.5,1)
  const hdrOutput=litColor.add(bloomPass)
  const displayLinear=blenderFilmicVeryHighContrast(hdrOutput.rgb)
  postProcessing.outputColorTransform=false
  postProcessing.outputNode=renderOutput(vec4(displayLinear,hdrOutput.a),THREE.NoToneMapping,renderer.outputColorSpace)

  // Prime render targets and apartment-independent post shaders after the DOM
  // landing has painted. A selected apartment may download concurrently, but
  // its geometry/material compilation waits for this shared work to finish.
  let sharedPipelineError:unknown=null
  const sharedPipelineReady=(async()=>{
    await nextFrame()
    scenePass.scene=emptyScene
    postProcessing.render()
    await nextFrame()
  })().catch((error)=>{sharedPipelineError=error})

  const clock=new THREE.Clock(false)
  const stopRendering=():void=>{if(!rendering)return;renderer.setAnimationLoop(null);clock.stop();rendering=false}
  const renderFrame=():void=>{
    const dt=clock.getDelta()
    if(controls?.enabled)controls.update(dt)
    seats?.update(dt)
    postProcessing.render()
  }
  const startRendering=():void=>{if(rendering)return;rendering=true;clock.start();renderer.setAnimationLoop(renderFrame)}

  const poseForBuild=(definition:ApartmentDefinition):void=>{
    const [x,y]=definition.spawn.position
    const [lookX,lookY]=definition.spawn.lookAt
    camera.position.set(x,y,1.62)
    camera.up.set(0,0,1)
    camera.lookAt(lookX,lookY,1.58)
    camera.updateProjectionMatrix()
  }

  async function compileApartment(apartment:BuiltApartment):Promise<void>{
    const {world,meshes,definition}=apartment
    poseForBuild(definition)
    const previousScene=scenePass.scene
    const visible=meshes.map((mesh)=>mesh.visible)
    scenePass.scene=world.scene
    renderer.setRenderTarget(scenePass.renderTarget)
    try{
      const chunkSize=12
      for(let start=0;start<meshes.length;start+=chunkSize){
        meshes.forEach((mesh,index)=>{mesh.visible=visible[index]&&index>=start&&index<start+chunkSize})
        await renderer.compileAsync(world.scene,camera)
        await nextFrame()
      }
    }finally{
      meshes.forEach((mesh,index)=>{mesh.visible=visible[index]})
      renderer.setRenderTarget(null)
      scenePass.scene=previousScene
    }
  }

  async function warmApartment(apartment:BuiltApartment):Promise<void>{
    if(!renderer.shadowMap.enabled)return
    const previousScene=scenePass.scene
    scenePass.scene=apartment.world.scene
    try{
      // Freeze every map before the first warm-up pass: a light still on
      // autoUpdate re-renders its map during every earlier light's pass.
      for(const light of apartment.world.lights)if(light.castShadow&&light.shadow)light.shadow.autoUpdate=false
      for(const light of apartment.world.lights){
        if(!light.castShadow||!light.shadow)continue
        light.shadow.needsUpdate=true
        postProcessing.render()
        await nextFrame()
      }
      // One settled full-scene frame primes the shared AO/bloom/presentation
      // passes after the apartment-specific material and shadow compilation.
      postProcessing.render()
      await nextFrame()
    }finally{scenePass.scene=previousScene}
  }

  const built=new Map<ApartmentId,BuiltApartment>()
  const pending=new Map<ApartmentId,Promise<BuiltApartment>>()
  const getApartment=(id:ApartmentId):Promise<BuiltApartment>=>{
    const cached=built.get(id)
    if(cached)return Promise.resolve(cached)
    const existing=pending.get(id)
    if(existing)return existing
    const request=(async()=>{
      const definitionRequest=loadApartmentDefinition(id)
      const [definition]=await Promise.all([definitionRequest,sharedPipelineReady])
      if(sharedPipelineError!==null)throw sharedPipelineError
      await nextFrame()
      const world=new World()
      await definition.build(world)
      const meshes:THREE.Mesh[]=[]
      world.scene.traverse((object)=>{if((object as THREE.Mesh).isMesh)meshes.push(object as THREE.Mesh)})
      const apartment={definition,world,meshes}
      await compileApartment(apartment)
      await warmApartment(apartment)
      built.set(id,apartment)
      return apartment
    })().catch((error)=>{
      pending.delete(id)
      throw error
    })
    pending.set(id,request)
    void request.then(()=>pending.delete(id))
    return request
  }

  const activateApartment=async(apartment:BuiltApartment):Promise<void>=>{
    apartment.definition.activate?.(apartment.world.scene)
    scenePass.scene=apartment.world.scene
    if(!controls)controls=new PlayerControls(camera,apartment.world.colliders)
    else controls.setColliders(apartment.world.colliders)
    controls.spawn(...apartment.definition.spawn.position,...apartment.definition.spawn.lookAt)
    const interactions=apartment.definition.interactions.seats.length?apartment.definition.interactions:undefined
    if(!seats){
      const {SeatingSystem:Seats}=await import('./player/seats')
      seats=new Seats(controls,camera,()=>{toHallway=true;document.exitPointerLock()},interactions)
    }else seats.configure(interactions)
    active=apartment
    controls.enabled=document.pointerLockElement===renderer.domElement
  }

  const tryEnter=():void=>{
    if(!entryReady||!entryTarget||active?.definition.id!==entryTarget)return
    if(document.pointerLockElement!==renderer.domElement)return
    entryReady=false
    entryTarget=null
    started=true
    ui.enterGame()
    startRendering()
  }

  requestEntry=(id)=>{
    entryTarget=id
    entryReady=false
    ui.beginLoading(id)
    // Pointer lock must be requested while the door click still owns transient
    // user activation; scene import/compilation continues behind the landing.
    requestPointerLock()
    void (async()=>{
      try{
        const apartment=await getApartment(id)
        if(entryTarget!==id)return
        await activateApartment(apartment)
        if(entryTarget!==id)return
        entryReady=true
        ui.finishLoading()
        tryEnter()
      }catch{
        if(entryTarget!==id)return
        entryTarget=null
        entryReady=false
        started=false
        stopRendering()
        ui.finishLoading()
        if(document.pointerLockElement===renderer.domElement)document.exitPointerLock()
        Ui.fatal('Scene unavailable')
      }
    })()
  }

  window.addEventListener('resize',()=>{
    setSize();camera.aspect=innerWidth/innerHeight
    camera.updateProjectionMatrix()
  })

  document.addEventListener('pointerlockchange',()=>{
    const locked=document.pointerLockElement===renderer.domElement
    if(controls)controls.enabled=locked&&!!active
    if(locked){
      if(entryTarget)tryEnter()
      else if(started&&active){ui.enterGame();startRendering()}
      return
    }
    if(entryTarget)return
    if(started){
      stopRendering()
      if(toHallway){toHallway=false;ui.showHallway()}else ui.showPause()
    }
  })

  ui.ready()
}

void boot()
