/** Fixture-authored apartment 19 practical lighting from f_light.py. */
import type * as THREE from 'three/webgpu'
import { MeshData } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'
import * as P from './props'

const GAIN=0.148
const WARM:[number,number,number]=[1,0.915,0.835]
const WARM_HOT:[number,number,number]=[1,0.875,0.79]
const add=(world:World,md:MeshData,material:THREE.Material):MeshData=>world.add(md,material)

function buildMaterials():void {
  M.emissive('M_BulbGlow','FFF2E6',{strength:6})
  M.emissive('M_DomeGlow','FFF5EC',{strength:2.4})
  M.emissive('M_StripGlow','FFF2E6',{strength:3.4})
  M.metal('M_FixBrass','A8842E',{rough:0.3,grime:0.35})
  M.metal('M_FixChrome','D6DADE',{rough:0.1,grime:0.3})
  M.plastic('M_Opal','F0EADA',{rough:0.42,coat:0.2})
}

function ceilingRose(world:World,cx:number,cy:number,energy:number,z=L.CZ,shadow=true):void {
  const ring=P.lathe([[0,0],[0.155,0],[0.152,-0.014],[0.128,-0.022],[0.126,-0.03],[0,-0.032]],30)
  add(world,mlib.translate(ring,[cx,cy,z]),M.get('M_FixBrass'))
  const profile:[number,number][]=[[0,-0.02]]
  for(let i=0;i<=10;i++){const a=Math.PI*0.5*i/10;profile.push([0.148*Math.cos(a),-0.026-0.115*Math.sin(a)])}
  const dome=mlib.translate(P.lathe(profile,30),[cx,cy,z]);M.get('M_DomeGlow').userData.noShadow=true;add(world,dome,M.get('M_DomeGlow'))
  world.pointLight([cx,cy,z-0.115],energy*GAIN,WARM,0.13,{shadow,distance:5.4,shadowMapSize:512,shadowRadius:5})
}

function bulb(world:World,loc:[number,number,number],energy:number,shadow=false):void {
  const md=P.lathe([[0,0],[0.014,0.004],[0.028,0.03],[0.026,0.058],[0.014,0.076],[0,0.08]],16)
  M.get('M_BulbGlow').userData.noShadow=true
  add(world,mlib.translate(md,loc),M.get('M_BulbGlow'))
  world.pointLight([loc[0],loc[1],loc[2]+0.04],energy*GAIN,WARM,0.05,{shadow,distance:3.6,shadowMapSize:384,shadowRadius:3})
}

function sconce(world:World):void {
  const parts:MeshData[]=[]
  const plate=P.lathe([[0,0],[0.062,0],[0.06,0.012],[0.026,0.02],[0.024,0.07],[0,0.072]],20);P.faceY(plate,1);parts.push(plate)
  const bowl=P.lathe([[0,0],[0.052,0.006],[0.098,0.042],[0.132,0.106],[0.134,0.112],[0.096,0.048],[0.05,0.014],[0,0.008]],28);mlib.translate(bowl,[0,0.104,-0.016]);parts.push(bowl)
  const lamp=P.lathe([[0,0],[0.021,0.008],[0.024,0.03],[0.018,0.05],[0,0.056]],14);mlib.translate(lamp,[0,0.104,0.03]);parts.push(lamp)
  P.wallPlace(parts,'W',6.86,2.24,L.WX)
  add(world,plate,M.get('M_FixBrass'));add(world,bowl,M.get('M_Opal'));add(world,lamp,M.get('M_BulbGlow'))
  world.pointLight([L.WX+0.104,6.86,2.27],210*GAIN,WARM,0.05,{shadow:false,distance:3.1})
}

function kitchenStrips(world:World):void {
  const x0=L.K_UPPER[0]+0.03,x1=L.K_UPPER[1]-0.03,y=L.NY2-L.UPPER_D+0.1,z=L.UPPER_Z[0]-0.02
  const tube=P.rod([x0,y,z],[x1,y,z],0.013,10);M.get('M_StripGlow').userData.noShadow=true;add(world,tube,M.get('M_StripGlow'))
  for(let i=0;i<4;i++)world.pointLight([x0+(x1-x0)*(i+0.5)/4,y,z-0.03],105*GAIN/4,WARM_HOT,0.04,{shadow:false,distance:2.2})
  const [mx0,mx1]=L.K_MW
  for(const t of [0.3,0.7])add(world,mlib.bevel(mlib.box(mx0+(mx1-mx0)*t-0.055,L.NY2-0.245,L.K_MW_Z[0]-0.006,mx0+(mx1-mx0)*t+0.055,L.NY2-0.135,L.K_MW_Z[0]),0.003,2),M.get('M_StripGlow'))
  world.pointLight([(mx0+mx1)*0.5,L.NY2-0.19,L.K_MW_Z[0]-0.02],78*GAIN,WARM_HOT,0.06,{shadow:false,distance:2.2})
}

function vanity(world:World):void {
  const u=L.BA_BASIN[1],z=2.02,at=L.BA_X[1]
  const bar=mlib.box(-0.28,0.016,-0.02,0.28,0.068,0.02)
  const globes:MeshData[]=[]
  for(const i of [-1,0,1]){const globe=P.lathe([[0,0],[0.03,0.01],[0.046,0.042],[0.044,0.072],[0.026,0.092],[0,0.096]],20);mlib.rotX(globe,-Math.PI*0.5);mlib.translate(globe,[i*0.175,0.068,0]);globes.push(globe)}
  P.wallPlace([bar,...globes],'E',u,z,at)
  add(world,bar,M.get('M_FixChrome'));for(const globe of globes)add(world,globe,M.get('M_Opal'))
  world.pointLight([at-0.13,u,z],200*GAIN,WARM_HOT,0.06,{shadow:false,distance:2.7})
}

export function build(world:World):void {
  buildMaterials()
  ceilingRose(world,2.05,5.05,470)
  ceilingRose(world,2.55,2.2,420)
  ceilingRose(world,6.55,3.3,520)
  ceilingRose(world,7.3,1.3,430)
  sconce(world)
  bulb(world,[3.02,L.NY-0.44,1.52],320)
  kitchenStrips(world)
  bulb(world,[L.JO_X[0]+0.3,1.72,0.87],135)
  bulb(world,[L.CH_X[0]+0.3,3.42,0.87],135)
  ceilingRose(world,L.JO_X[0]+1.8,0.7,250,L.CZ,false)
  ceilingRose(world,L.CH_X[0]+1.8,4.6,250,L.CZ,false)
  vanity(world)
  ceilingRose(world,(L.BA_X[0]+L.BA_X[1])*0.5,(L.BA_Y[0]+L.BA_Y[1])*0.5,185,L.BA_CZ,false)
}
