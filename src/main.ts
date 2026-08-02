/** WebGPU apartment runtime: two scene-owned worlds, shared first-person
 * controls and image pipeline, and hallway-driven scene selection. */
import './scene/shadows'
import * as THREE from 'three/webgpu'
import { mix, mrt, normalView, output, pass, renderOutput, vec4 } from 'three/tsl'
import { bloom } from 'three/examples/jsm/tsl/display/BloomNode.js'
import { ao } from 'three/examples/jsm/tsl/display/GTAONode.js'
import { APARTMENTS } from './apartments'
import type { ApartmentDefinition, ApartmentId } from './apartments/types'
import { World } from './scene/world'
import { PlayerControls } from './player/controls'
import { SeatingSystem } from './player/seats'
import { Ui } from './ui/ui'
import { applyCameraBookmark, inspectionFromUrl } from './scene/cameras'
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

async function boot():Promise<void> {
  if(!isDesktopChromium(navigator)){Ui.fatal('Desktop Chromium required');return}
  const inspection=inspectionFromUrl()
  if(!('gpu' in navigator)){Ui.fatal('WebGPU required');return}

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
  renderer.shadowMap.enabled=inspection?.shadows??true
  renderer.shadowMap.type=THREE.PCFShadowMap
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
  let started=false
  let toHallway=false
  let selectedId:ApartmentId=inspection?.apartment??'20'
  let selectApartment:(id:ApartmentId)=>void=(id)=>{selectedId=id}

  const ui=new Ui({
    onEnter:(id)=>{selectApartment(id);renderer.domElement.requestPointerLock()},
    onResume:()=>renderer.domElement.requestPointerLock(),
  })

  window.addEventListener('resize',()=>{
    setSize();camera.aspect=innerWidth/innerHeight
    if(inspection)applyCameraBookmark(camera,inspection.view,inspection.apartment)
    else camera.updateProjectionMatrix()
  })

  // Each apartment owns an independent World/Scene/material namespace. They
  // are both built behind the landing so choosing a door never incurs a room
  // construction hitch or cross-apartment mesh/material leakage.
  await new Promise((resolve)=>setTimeout(resolve,30))
  const built=new Map<ApartmentId,BuiltApartment>()
  for(const id of ['20','19'] as const){
    const definition=APARTMENTS[id]
    const world=new World()
    await definition.build(world)
    const meshes:THREE.Mesh[]=[]
    world.scene.traverse((object)=>{if((object as THREE.Mesh).isMesh)meshes.push(object as THREE.Mesh)})
    built.set(id,{definition,world,meshes})
  }

  const initial=built.get(selectedId)!
  controls=new PlayerControls(camera,initial.world.colliders)
  controls.spawn(...initial.definition.spawn.position,...initial.definition.spawn.lookAt)
  if(!inspection)seats=new SeatingSystem(controls,camera,()=>{toHallway=true;document.exitPointerLock()},selectedId==='19'?initial.definition.interactions:undefined)
  if(inspection){applyCameraBookmark(camera,inspection.view,inspection.apartment);ui.enterGame()}

  const postProcessing=new THREE.PostProcessing(renderer)
  const scenePass=pass(initial.world.scene,camera,{samples:renderer.samples})
  scenePass.setMRT(mrt({output,normal:normalView}))
  const scenePassColor=scenePass.getTextureNode('output')
  const scenePassNormal=scenePass.getTextureNode('normal')
  const scenePassDepth=scenePass.getTextureNode('depth')
  let litColor:THREE.Node=scenePassColor
  if(inspection?.ao!==false){
    const gtaoPass=ao(scenePassDepth,scenePassNormal,camera)
    gtaoPass.resolutionScale=1;gtaoPass.radius.value=0.32;gtaoPass.thickness.value=1.25
    gtaoPass.distanceExponent.value=1.5;gtaoPass.distanceFallOff.value=0.82
    gtaoPass.scale.value=0.9;gtaoPass.samples.value=12
    litColor=scenePassColor.mul(mix(1,gtaoPass.getTextureNode().r,0.34))
  }
  const bloomPass=bloom(scenePassColor,0.07,0.5,1)
  const hdrOutput=inspection?.bloom===false?litColor:litColor.add(bloomPass)
  if(inspection?.grade!==false){
    const displayLinear=blenderFilmicVeryHighContrast(hdrOutput.rgb)
    postProcessing.outputColorTransform=false
    postProcessing.outputNode=renderOutput(vec4(displayLinear,hdrOutput.a),THREE.NoToneMapping,renderer.outputColorSpace)
  }else postProcessing.outputNode=hdrOutput

  selectApartment=(id:ApartmentId):void=>{
    const apartment=built.get(id)
    if(!apartment)return
    selectedId=id
    scenePass.scene=apartment.world.scene
    controls?.setColliders(apartment.world.colliders)
    controls?.spawn(...apartment.definition.spawn.position,...apartment.definition.spawn.lookAt)
    seats?.configure(id==='19'?apartment.definition.interactions:undefined)
  }
  selectApartment(selectedId)

  // Compile both apartment material sets against the same final render target.
  // Scene selection later only swaps PassNode.scene; it does not rebuild post.
  renderer.setRenderTarget(scenePass.renderTarget)
  const chunk=12
  for(const id of ['20','19'] as const){
    const apartment=built.get(id)!
    scenePass.scene=apartment.world.scene
    for(let i=0;i<apartment.meshes.length;i+=chunk){
      apartment.meshes.forEach((mesh,index)=>{mesh.visible=index>=i&&index<i+chunk})
      await renderer.compileAsync(apartment.world.scene,camera)
      await new Promise((resolve)=>setTimeout(resolve,0))
    }
    for(const mesh of apartment.meshes)mesh.visible=true
  }
  renderer.setRenderTarget(null)
  selectApartment(selectedId)

  type WarmTask={id:ApartmentId;shadow:THREE.LightShadow}
  const warmTasks:WarmTask[]=[]
  for(const id of ['20','19'] as const){
    for(const light of built.get(id)!.world.lights){
      if(light.castShadow&&light.shadow){light.shadow.autoUpdate=false;warmTasks.push({id,shadow:light.shadow})}
    }
  }
  let warmIndex=0
  let settleFrames=0
  let ready=false
  let rendering=false
  const clock=new THREE.Clock(false)

  const stopRendering=():void=>{if(!rendering)return;renderer.setAnimationLoop(null);clock.stop();rendering=false}
  const renderFrame=():void=>{
    const dt=clock.getDelta()
    if(!ready){
      if(warmIndex<warmTasks.length){
        const task=warmTasks[warmIndex++]
        scenePass.scene=built.get(task.id)!.world.scene
        task.shadow.needsUpdate=true
      }else{
        scenePass.scene=built.get(selectedId)!.world.scene
        settleFrames++
      }
      postProcessing.render()
      if(warmIndex>=warmTasks.length&&settleFrames>=2){
        ready=true;selectApartment(selectedId);ui.ready()
        if(document.pointerLockElement!==renderer.domElement)stopRendering()
      }
      return
    }
    if(!inspection&&controls?.enabled)controls.update(dt)
    seats?.update(dt)
    postProcessing.render()
  }
  const startRendering=():void=>{if(rendering)return;rendering=true;clock.start();renderer.setAnimationLoop(renderFrame)}

  document.addEventListener('pointerlockchange',()=>{
    const locked=document.pointerLockElement===renderer.domElement
    if(controls)controls.enabled=locked
    if(locked){started=true;ui.enterGame();startRendering()}
    else if(started){
      stopRendering()
      if(toHallway){toHallway=false;ui.showHallway()}else ui.showPause()
    }
  })
  startRendering()
}

boot()
