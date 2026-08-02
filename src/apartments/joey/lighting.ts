/** Fixture-authored apartment 19 practical lighting from f_light.py. */
import type * as THREE from 'three/webgpu'
import { MeshData } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { srgbTriple } from '../../mats/tsl'
import { blackbody } from '../../scene/props'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'
import * as P from './props'

const GAIN=0.185
const WARM=srgbTriple('FFEBD2')
// User-tuned: every fixture emissive (and the sconce lamp) shares one warmth.
export const GLOW_K=3000
const invSrgb=(u:number):number=>u<=0.0031308?u*12.92:1.055*u**(1/2.4)-0.055
export const bbHex=(kelvin:number):string=>blackbody(kelvin).map((c)=>Math.round(invSrgb(c)*255).toString(16).padStart(2,'0')).join('')
const watts=(value:number):number=>value/GAIN
const add=(world:World,md:MeshData,material:THREE.Material):MeshData=>world.add(md,material)

function buildMaterials():void {
  const glow=bbHex(GLOW_K)
  M.emissive('M_BulbGlow',glow,{strength:6})
  M.emissive('M_DomeGlow',glow,{strength:2.4})
  M.emissive('M_StripGlow',glow,{strength:3.4})
  M.emissive('M_OpalGlow',glow,{strength:2.4,rough:0.42,base:'F0EADA'})
  M.plastic('M_Opal','F0EADA',{rough:0.42,coat:0.2})
  M.metal('M_FixBrass','A8842E',{rough:0.3,grime:0.35})
  M.metal('M_FixChrome','D6DADE',{rough:0.1,grime:0.3})
}

function ceilingRose(world:World,cx:number,cy:number,energy:number,z=L.CZ,shadow=true,size=0.13):void {
  const ring=P.lathe([[0,0],[0.155,0],[0.152,-0.014],[0.128,-0.022],[0.126,-0.03],[0,-0.032]],30)
  add(world,mlib.translate(ring,[cx,cy,z]),M.get('M_FixBrass'))
  const profile:[number,number][]=[[0,-0.02]]
  for(let i=0;i<=10;i++){const a=Math.PI*0.5*i/10;profile.push([0.148*Math.cos(a),-0.026-0.115*Math.sin(a)])}
  const dome=mlib.translate(P.lathe(profile,30),[cx,cy,z]);M.get('M_DomeGlow').userData.noShadow=true;add(world,dome,M.get('M_DomeGlow'))
  world.pointLight([cx,cy,z-0.115],energy*GAIN,WARM,size,{shadow,distance:5.4,shadowMapSize:512,shadowRadius:5})
}

function lampBulb(world:World,loc:[number,number,number]):void {
  const md=P.lathe([[0,0],[0.014,0.004],[0.028,0.03],[0.026,0.058],[0.014,0.076],[0,0.08]],16)
  M.get('M_BulbGlow').userData.noShadow=true
  add(world,mlib.translate(md,loc),M.get('M_BulbGlow'))
}

function sconce(world:World):void {
  const plate=P.lathe([[0,0],[0.062,0],[0.06,0.012],[0.026,0.02],[0.024,0.07],[0,0.072]],20);P.faceY(plate,1)
  const bowl=P.lathe([[0,0],[0.052,0.006],[0.098,0.042],[0.132,0.106],[0.134,0.112],[0.096,0.048],[0.05,0.014],[0,0.008]],28);mlib.translate(bowl,[0,0.104,-0.016])
  const bulb=P.lathe([[0,0],[0.021,0.008],[0.024,0.03],[0.018,0.05],[0,0.056]],14);mlib.translate(bulb,[0,0.104,0.03])
  P.wallPlace([plate,bowl,bulb],'W',6.86,2.24,L.WX)
  // f_light.py diffuser(): the opal bowl must not screen its own lamp.
  M.get('M_Opal').userData.noShadow=true;M.get('M_BulbGlow').userData.noShadow=true
  add(world,plate,M.get('M_FixBrass'));add(world,bowl,M.get('M_Opal'));add(world,bulb,M.get('M_BulbGlow'))
  // The POINT lamp sits at the placed bulb's vertex centroid, as in f_light.py.
  let cx=0,cy=0,cz=0
  for(const v of bulb.verts){cx+=v[0];cy+=v[1];cz+=v[2]}
  const n=bulb.verts.length
  // User-tuned from f_light.py's 210 W @ WARM (~2900 K): +30% power, GLOW_K warmth.
  world.pointLight([cx/n,cy/n,cz/n],273*GAIN,blackbody(GLOW_K),0.05,{distance:5.4})
}

function kitchenStrips(world:World):void {
  const x0=L.K_UPPER[0]+0.03,x1=L.K_UPPER[1]-0.03,y=L.NY2-L.UPPER_D+0.1,z=L.UPPER_Z[0]-0.02
  const tube=P.rod([x0,y,z],[x1,y,z],0.013,10);M.get('M_StripGlow').userData.noShadow=true;add(world,tube,M.get('M_StripGlow'))
  const [mx0,mx1]=L.K_MW
  for(const t of [0.3,0.7])add(world,mlib.bevel(mlib.box(mx0+(mx1-mx0)*t-0.055,L.NY2-0.245,L.K_MW_Z[0]-0.006,mx0+(mx1-mx0)*t+0.055,L.NY2-0.135,L.K_MW_Z[0]),0.003,2),M.get('M_StripGlow'))
}

function vanity(world:World):void {
  const u=L.BA_BASIN[1],z=2.02,at=L.BA_X[1]
  const bar=mlib.box(-0.28,0.016,-0.02,0.28,0.068,0.02)
  const globes:MeshData[]=[]
  for(const i of [-1,0,1]){const globe=P.lathe([[0,0],[0.03,0.01],[0.046,0.042],[0.044,0.072],[0.026,0.092],[0,0.096]],20);mlib.rotX(globe,-Math.PI*0.5);mlib.translate(globe,[i*0.175,0.068,0]);globes.push(globe)}
  P.wallPlace([bar,...globes],'E',u,z,at)
  add(world,bar,M.get('M_FixChrome'));for(const globe of globes)add(world,globe,M.get('M_OpalGlow'))
}

export function build(world:World):void {
  buildMaterials()
  ceilingRose(world,(L.WX+L.JX)*0.5,(L.SY+L.NY)*0.5,watts(300),L.CZ,true,0.1)
  ceilingRose(world,(L.JX+L.EX)*0.5,(L.SY+L.NY2)*0.5,watts(250),L.CZ,true,0.1)
  sconce(world)
  lampBulb(world,[L.FLOOR_LAMP[0],L.FLOOR_LAMP[1],1.52])
  kitchenStrips(world)
  lampBulb(world,[L.JO_X[0]+0.3,1.72,0.87])
  lampBulb(world,[L.CH_X[0]+0.3,3.42,0.87])
  ceilingRose(world,(L.JO_X[0]+L.JO_X[1])*0.5,(L.JO_Y[0]+L.JO_Y[1])*0.5,290,L.CZ,false)
  ceilingRose(world,(L.CH_X[0]+L.CH_X[1])*0.5,(L.CH_Y[0]+L.CH_Y[1])*0.5,290,L.CZ,false)
  vanity(world)
  ceilingRose(world,(L.BA_X[0]+L.BA_X[1])*0.5,(L.BA_Y[0]+L.BA_Y[1])*0.5,185,L.BA_CZ,false)
}
