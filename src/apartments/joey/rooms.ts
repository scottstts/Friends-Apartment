/** Apartment 19 bedrooms and bathroom from build_scripts/Joeys_apt/f_beds.py. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec2, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'
import type { World } from '../../scene/world'
import * as L from './layout'
import { bbHex, GLOW_K } from './lighting'
import * as M from './materials'
import * as P from './props'

const add=(world:World,md:MeshData,material:THREE.Material,collide=false):MeshData=>world.add(md,material,{collide})
const rounded=(x0:number,y0:number,z0:number,x1:number,y1:number,z1:number,r=0.012):MeshData=>mlib.bevel(mlib.box(x0,y0,z0,x1,y1,z1),r,3)

function buildMaterials():void {
  M.wood('M_BedWood',['6A4526','8C6236','4A2C16'],{ring:26,axis:'X',rough:[0.26,0.48],coat:0.26,grainRelief:0.1,scale:1.4})
  M.wood('M_BedWood2',['3E2A1C','5C4026','281810'],{ring:30,axis:'Y',rough:[0.28,0.5],coat:0.22,grainRelief:0.1,scale:1.4})
  M.fabric('M_Duvet1','39506E',{rough:0.76,weave:280,sheen:0.4})
  M.fabric('M_Duvet2','6E4A3A',{rough:0.78,weave:260,sheen:0.35})
  M.fabric('M_Sheet','E2DED0',{rough:0.8,weave:340,sheen:0.45})
  M.fabric('M_Mattress','D8D2C2',{rough:0.84,weave:380,sheen:0.3})
  M.enamel('M_Sanitary','F4F3EE',{rough:0.055,tint:'E6E6E0'})
  M.metal('M_BathChrome','DCE0E4',{rough:0.06,grime:0.35})
  M.metal('M_MirrorGlass','F4F6F7',{rough:0.015,grime:0.1})
  M.paint('M_VanityPaint','D8D2C2',{rough:0.3,coat:0.22})
  M.stone('M_VanityTop','EDEAE0',{vein:'C6BEB0',rough:0.14,scale:2})
  M.plastic('M_ShowerCurtain','DCE4E2',{rough:0.42,coat:0.1,bump:0.14})
  M.plastic('M_LampBase','2A2622',{rough:0.42})
  M.emissive('M_ShadeCream',bbHex(GLOW_K),{strength:1.6,rough:0.62,base:'E8E0CC'})
  M.carpet('M_BedRug','7A6A52',{rough:0.94})
  M.carpet('M_BedRug2','4E5A66',{rough:0.94})
  M.carpet('M_BathMat','C8D2CE',{rough:0.95,pile:1.3})
  M.fabric('M_Towel','DCE4E2',{rough:0.92,weave:240,sheen:0.3,bump:0.75,fuzz:1.2})
  M.fabric('M_Towel2','8AA8B4',{rough:0.92,weave:240,sheen:0.3,bump:0.75,fuzz:1.2})
  M.fabric('M_Clothes','6A4A3C',{rough:0.8,weave:300,sheen:0.35})
  M.fabric('M_Clothes2','3E5266',{rough:0.8,weave:300,sheen:0.35})
  M.wood('M_ChairWood',['7A5230','9C7044','54351C'],{ring:12,axis:'Z',warp:0.8,rough:[0.26,0.48],coat:0.24,grainRelief:0.07})
  M.plastic('M_BinPlastic','2A2C30',{rough:0.44,coat:0.15})
  M.plastic('M_BottleA','2E6E6A',{rough:0.18,coat:0.55})
  M.plastic('M_BottleB','B8607A',{rough:0.18,coat:0.55})
  M.plastic('M_BottleC','D8C24E',{rough:0.18,coat:0.55})
  M.paper('M_PosterA','9C4A34',{rough:0.34,gloss:0.45})
  M.paper('M_PosterB','2E5A7A',{rough:0.34,gloss:0.45})
  M.plastic('M_DuckYellow','E8B71A',{rough:0.28,coat:0.45})
  M.plastic('M_DuckBill','E07A16',{rough:0.32,coat:0.4})
  M.plastic('M_DuckEye','18140E',{rough:0.22,coat:0.55})
}

function place(md:MeshData,cx:number,cy:number,rotation=0,z=0):MeshData {if(rotation)mlib.rotateZ(md,rotation);return mlib.translate(md,[cx,cy,z])}

function buildBed(world:World,cx:number,cy:number,duvet:string):void {
  const width=1.44,length=2.02,half=width*0.5
  add(world,place(rounded(-length*0.5-0.055,-half-0.03,0,length*-0.5+0.01,half+0.03,0.86,0.024),cx,cy,0,0.024),M.get('M_BedWood'))
  add(world,place(rounded(length*0.5-0.01,-half-0.03,0,length*0.5+0.055,half+0.03,0.43,0.024),cx,cy,0,0.024),M.get('M_BedWood'))
  add(world,place(rounded(-length*0.5,-half-0.028,0.17,length*0.5,half+0.028,0.3,0.004),cx,cy,0,0.024),M.get('M_BedWood'),true)
  add(world,place(rounded(-length*0.5+0.01,-half,0.3,length*0.5-0.01,half,0.52,0.045),cx,cy,0,0.024),M.get('M_Mattress'))
  const levels:[number,number,number][]=[[-length*0.5+0.16,half+0.01,0.56],[-length*0.5+0.3,half+0.03,0.585],[0.1,half+0.045,0.575],[length*0.5-0.1,half+0.045,0.565],[length*0.5+0.03,half+0.03,0.52]]
  const rings=levels.map(([x,ry,z])=>mlib.roundedRect(ry*2,0.23,0.072,6).map(([y,dz])=>[x,y,z+dz] as Vec3))
  const cover=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true});mlib.smoothShade(cover,42);add(world,place(cover,cx,cy,0,0.024),M.get(duvet))
  add(world,place(rounded(-length*0.5+0.16,-half-0.012,0.52,-length*0.5+0.34,half+0.012,0.585,0.028),cx,cy,0,0.024),M.get('M_Sheet'))
  for(const side of [-1,1]){
    const pillow=P.pillow(0.62,0.4,0.15);mlib.rotX(pillow,12*Math.PI/180);mlib.rotateZ(pillow,Math.PI*0.5);mlib.translate(pillow,[cx-length*0.5+0.28,cy+side*half*0.45,0.569]);add(world,pillow,M.get('M_Sheet'))
  }
}

function buildNightstand(world:World,cx:number,cy:number):void {
  add(world,rounded(cx-0.23,cy-0.2,0.095,cx+0.23,cy+0.2,0.585,0.004),M.get('M_BedWood2'),true)
  for(let i=0;i<2;i++) add(world,rounded(cx-0.21,cy-0.218,0.125+i*0.225,cx+0.21,cy-0.198,0.32+i*0.225,0.004),M.get('M_BedWood2'))
  add(world,mlib.translate(P.lathe([[0,0],[0.072,0],[0.068,0.014],[0.03,0.04],[0.024,0.055],[0.036,0.15],[0.028,0.21],[0,0.212]],20),[cx,cy,0.585]),M.get('M_LampBase'))
  add(world,mlib.translate(P.lathe([[0,0],[0.13,0],[0.128,0.006],[0.092,0.186],[0.09,0.192],[0.126,0.01],[0,0.01]],26),[cx,cy,0.775]),M.get('M_ShadeCream'))
}

function buildDresser(world:World,cx:number,cy:number,rotation:number):void {
  const width=1.16,depth=0.48,height=0.82
  const parts:MeshData[]=[rounded(-width/2,-depth/2,0.09,width/2,depth/2,height,0.004),P.worktop(-width/2-0.018,-depth/2-0.018,width/2+0.018,depth/2+0.018,height+0.026,{thickness:0.026,radius:0.008})]
  const span=(height-0.135)/3
  for(let i=0;i<3;i++)parts.push(rounded(-width/2+0.022,-depth/2-0.018,0.115+i*span,width/2-0.022,-depth/2+0.002,0.115+(i+1)*span-0.014,0.004))
  for(let i=0;i<parts.length;i++){place(parts[i],cx,cy,rotation);add(world,parts[i],M.get(i===1?'M_BedWood':'M_BedWood2'),i===0)}
  const rng=new PyRandom(51)
  for(let i=0;i<3;i++)add(world,P.bottle(cx-0.2+i*0.085,cy+0.02,0.848,0.028,rng.uniform(0.115,0.165),0.01),M.get(['M_BottleA','M_BottleB','M_BottleC'][i]))
}

function buildBedroomDressing(world:World):void {
  const rugs:[[number,number,string],[number,number,string]]=[[-1.05,0.62,'M_BedRug'],[-1.05,4.55,'M_BedRug2']]
  for(const [cx,cy,material] of rugs){const rug=P.rug(cx,cy,1.1,1.85,(u,v)=>u<0.055||u>0.945||v<0.075||v>0.925?1:0,{cell:0.035,thickness:0.012,z0:0.012});world.addMulti(rug,[M.get(material),M.get(material==='M_BedRug'?'M_BedRug2':'M_BedRug')])}
  for(const [u,z,at,material] of [[1.78,1.62,L.JO_X[0],'M_PosterA'],[5.42,1.62,L.CH_X[0],'M_PosterB']] as const){const [frame,art]=P.frameArt(0.62,0.88,0.024,0.026,0.008,0.019);P.wallPlace([frame,art],'W',u,z,at);add(world,frame,M.get('M_BedWood2'));add(world,art,M.get(material))}
  for(const [cx,cy] of [[L.JO_X[0]+0.36,L.JO_Y[0]+0.34],[L.CH_X[0]+0.36,L.CH_Y[1]-0.34]]) add(world,mlib.translate(P.lathe([[0,0],[0.116,0],[0.122,0.012],[0.135,0.38],[0.14,0.4],[0.132,0.4],[0.127,0.38],[0.111,0.014],[0,0.01]],24),[cx,cy,0]),M.get('M_BinPlastic'),true)
}

function buildBedrooms(world:World):void {
  buildBed(world,L.JO_X[0]+1.12,0.62,'M_Duvet2')
  buildNightstand(world,L.JO_X[0]+0.3,1.72)
  buildDresser(world,L.JO_X[0]+1.55,L.JO_Y[0]+0.28,Math.PI)
  buildBed(world,L.CH_X[0]+1.12,4.55,'M_Duvet1')
  buildNightstand(world,L.CH_X[0]+0.3,3.42)
  buildDresser(world,L.CH_X[0]+1.7,L.CH_Y[1]-0.3,0)
  buildBedroomDressing(world)
}

/** Rectangular stone slab with the authoritative oval through-cut from
 * f_beds.py. Every angular sample owns both an ellipse point and the point
 * where the same ray meets the outer rectangle, so the top is one continuous
 * annular surface instead of four strips with exposed square corners. */
function vanityTopWithOvalCutout(
  x0:number,y0:number,x1:number,y1:number,z0:number,z1:number,
  cx:number,cy:number,axisX:number,axisY:number,segments=56,
):MeshData {
  const cornerAngles:[[number,number],[number,number],[number,number],[number,number]]=[
    [x1,y1],[x0,y1],[x0,y0],[x1,y0],
  ]
  const angles=[
    ...Array.from({length:segments},(_,i)=>Math.PI*2*i/segments),
    ...cornerAngles.map(([x,y])=>(Math.atan2(y-cy,x-cx)+Math.PI*2)%(Math.PI*2)),
  ].sort((a,b)=>a-b).filter((angle,index,list)=>index===0||Math.abs(angle-list[index-1])>1e-10)
  const outer:Vec2[]=[]
  const inner:Vec2[]=[]
  for(const angle of angles){
    const c=Math.cos(angle),s=Math.sin(angle)
    let distance=Number.POSITIVE_INFINITY
    if(Math.abs(c)>1e-9)distance=Math.min(distance,((c>0?x1:x0)-cx)/c)
    if(Math.abs(s)>1e-9)distance=Math.min(distance,((s>0?y1:y0)-cy)/s)
    outer.push([cx+c*distance,cy+s*distance])
    inner.push([cx+axisX*c,cy+axisY*s])
  }
  return mlib.aperturedPrism(outer,inner,z0,z1,0.004,3)
}

function buildVanity(world:World):void {
  const x1=L.BA_X[1],x0=x1-0.56,[y0,y1]=L.BA_VAN_Y,side=0.018
  const body=mlib.join([mlib.box(x0,y0,0.1,x1,y0+side,0.84),mlib.box(x0,y1-side,0.1,x1,y1,0.84),mlib.box(x1-side,y0+side,0.1,x1,y1-side,0.84),mlib.box(x0,y0+side,0.1,x1-side,y1-side,0.118),mlib.box(x0,y0+side,0.79,x0+side,y1-side,0.84)])
  add(world,mlib.bevel(body,0.003,2),M.get('M_VanityPaint'),true)
  const doorWidth=(y1-y0)*0.5-0.02
  for(let i=0;i<2;i++){
    const y=y0+0.012+i*(y1-y0)*0.5
    const door=P.cabinetDoor(doorWidth,0.64,0.019,0.052,0.014,0.007)
    mlib.rotateZ(door,-Math.PI*0.5);mlib.translate(door,[x0-0.004,y+doorWidth,0.15]);add(world,door,M.get('M_VanityPaint'))
    const knob=P.knob(0.014,0.012)
    P.faceX(knob,-1,[x0-0.002,y+(i?0.045:doorWidth-0.045),0.7])
    add(world,knob,M.get('M_BathChrome'))
  }
  const [bx,by]=L.BA_BASIN,top=0.876
  add(world,vanityTopWithOvalCutout(x0-0.02,y0-0.02,x1,y1+0.02,top-0.036,top,bx,by,0.176,0.141),M.get('M_VanityTop'))
  const basin=P.lathe([[0,0],[0.06,0.004],[0.115,0.04],[0.15,0.086],[0.163,0.116],[0.168,0.128],[0.212,0.134],[0.213,0.146],[0.204,0.15],[0.164,0.14],[0.158,0.126],[0.144,0.086],[0.106,0.04],[0.052,0.014],[0,0.012]],36);mlib.scaleMesh(basin,[1,0.8,1]);add(world,mlib.translate(basin,[bx,by,top-0.138]),M.get('M_Sanitary'))
  add(world,mlib.translate(P.lathe([[0,0],[0.022,0],[0.022,0.004],[0,0.004]],18),[bx,by,top-0.126]),M.get('M_BathChrome'))
  const tx=x1-0.058
  add(world,mlib.translate(P.lathe([[0,0],[0.036,0],[0.034,0.01],[0.019,0.026],[0.018,0.098],[0.024,0.106],[0,0.108]],20),[tx,by,top]),M.get('M_BathChrome'))
  add(world,mlib.tubeAlong([[tx,by,top+0.104],[tx-0.062,by,top+0.126],[tx-0.118,by,top+0.092]],mlib.circle(0.014,12)),M.get('M_BathChrome'))
  for(const side of [-1,1])add(world,mlib.translate(P.lathe([[0,0],[0.026,0],[0.024,0.008],[0.01,0.014],[0.009,0.038],[0.02,0.046],[0.019,0.056],[0,0.058]],16),[tx,by+side*0.086,top]),M.get('M_BathChrome'))
  const [frame,mirror]=P.frameArt(1,0.78,0.03,0.038,0.008,0.019);P.wallPlace([frame,mirror],'E',by,1.52,L.BA_X[1]);add(world,frame,M.get('M_VanityPaint'));add(world,mirror,M.get('M_MirrorGlass'))
}

function buildWc(world:World):void {
  const [wx,wy]=L.BA_WC,back=L.BA_X[1]-0.009
  const specs:[number,number,number,number,number][]=[[0.235,0.29,0.055,0.006,0.105],[0.215,0.262,0.055,0.088,0.092],[0.232,0.256,0.06,0.172,0.056],[0.286,0.282,0.075,0.256,0.024],[0.346,0.312,0.09,0.332,0.008],[0.386,0.332,0.105,0.38,0],[0.394,0.338,0.108,0.396,0],[0.352,0.3,0.098,0.39,0],[0.318,0.272,0.09,0.338,0.002],[0.268,0.228,0.078,0.288,0.008],[0.188,0.164,0.058,0.248,0.016],[0.086,0.076,0.03,0.23,0.022]]
  const rings=specs.map(([dy,dx,r,z,ox])=>mlib.roundedRect(dy,dx,r,5).map(([y,x])=>[wx+ox+x,wy+y,z] as Vec3))
  const pan=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true});mlib.smoothShade(pan,46);add(world,pan,M.get('M_Sanitary'),true)
  add(world,rounded(back-0.205,wy-0.222,0.43,back,wy+0.222,0.8,0.026),M.get('M_Sanitary'))
  add(world,rounded(back-0.218,wy-0.234,0.8,back,wy+0.234,0.824,0.014),M.get('M_Sanitary'))
  const seat=P.torus(0.176,0.03,44,10,[wx,wy,0.412]);mlib.scaleMesh(seat,[1.11,0.9,0.42],[wx,wy,0.412]);add(world,seat,M.get('M_Sanitary'))
  const lid=P.lathe([[0,0],[0.15,0],[0.19,0.008],[0.204,0.02],[0.2,0.03],[0.15,0.034],[0,0.034]],40);mlib.scaleMesh(lid,[1.11,0.9,1]);add(world,mlib.translate(lid,[wx,wy,0.424]),M.get('M_Sanitary'))
}

function buildTub(world:World):void {
  const [x0,x1]=L.BA_TUB_X,y1=L.BA_Y[1],y0=y1-0.735,top=0.56,cx=(x0+x1)*0.5,cy=(y0+y1)*0.5,width=x1-x0,depth=y1-y0
  const profile:[number,number,number,number][]=[[width-0.052,depth-0.052,0.048,0.004],[width-0.006,depth-0.01,0.058,0.09],[width,depth,0.066,0.3],[width,depth,0.066,top-0.012],[width-0.003,depth-0.003,0.066,top],[width-0.15,depth-0.146,0.1,top-0.01],[width-0.172,depth-0.166,0.11,top-0.082],[width-0.24,depth-0.216,0.14,0.226],[width-0.37,depth-0.296,0.15,0.136],[width-0.53,depth-0.376,0.15,0.116]]
  const rings=profile.map(([w,d,r,z])=>mlib.roundedRect(w,d,r,6).map(([x,y])=>[cx+x,cy+y,z] as Vec3))
  const tub=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true});mlib.smoothShade(tub,44);add(world,tub,M.get('M_Sanitary'),true)
  add(world,mlib.translate(P.lathe([[0,0],[0.04,0],[0.038,0.014],[0.02,0.03],[0.019,0.09],[0.026,0.098],[0,0.1]],18),[x0+0.24,y1-0.036,top-0.006]),M.get('M_BathChrome'))
  add(world,mlib.tubeAlong([[x0+0.24,y1-0.036,top+0.078],[x0+0.24,y1-0.13,top+0.086],[x0+0.24,y1-0.18,top+0.052]],mlib.circle(0.017,10)),M.get('M_BathChrome'))
  add(world,mlib.tubeAlong([[x0+0.24,y1-0.03,top+0.05],[x0+0.24,y1-0.03,1.96],[x0+0.24,y1-0.15,2.02]],mlib.circle(0.012,10)),M.get('M_BathChrome'))
  add(world,P.rod([x0-0.01,y0+0.03,2.06],[x1+0.01,y0+0.03,2.06],0.013,12),M.get('M_BathChrome'))
  add(world,P.drape(x0+0.02,x1-0.02,y0+0.03,0.32,2.03,{folds:9,amplitude:0.038,nz:14,seed:13}),M.get('M_ShowerCurtain'))
  const bathMat=P.rug(cx,y0-0.42,0.78,0.52,()=>0,{cell:0.03,thickness:0.016,pile:0.0022,z0:0.017});add(world,bathMat,M.get('M_BathMat'))
  for(const [i,material] of ['M_BottleA','M_BottleB','M_BottleC'].entries())add(world,P.bottle(x1-0.46+i*0.076,y1-0.044,0.551,0.024,0.13+i*0.018,0.009),M.get(material))
}

function buildDuck(world:World):void {
  const cx=L.BA_X[1]-0.135,cy=L.BA_WC[1]+0.128,cz=0.824,angle=22*Math.PI/180
  const parts:[[MeshData,string],[MeshData,string]]=[
    [P.sweepVar([[0.082,0,0.024],[0.058,0,0.044],[0.014,0,0.052],[-0.03,0,0.046],[-0.056,0,0.048],[-0.064,0,0.068],[-0.058,0,0.09],[-0.042,0,0.1],[-0.03,0,0.098]],[[0.014,0.011],[0.04,0.032],[0.05,0.044],[0.041,0.042],[0.03,0.032],[0.025,0.026],[0.022,0.023],[0.019,0.02],[0.012,0.012]],18),'M_DuckYellow'],
    [P.sweepVar([[-0.04,0,0.086],[-0.064,0,0.082],[-0.084,0,0.079],[-0.094,0,0.078]],[[0.017,0.011],[0.019,0.009],[0.016,0.006],[0.01,0.004]],14),'M_DuckBill'],
  ]
  for(const [md,material] of parts){mlib.rotateZ(md,angle);mlib.translate(md,[cx,cy,cz]);add(world,md,M.get(material))}
}

function buildBathroom(world:World):void {
  buildTub(world)
  buildVanity(world)
  buildWc(world)
  buildDuck(world)
  const y0=L.BA_Y[0]+0.72,y1=L.BA_Y[0]+1.6
  add(world,P.rod([L.BA_X[0]+0.058,y0,1.18],[L.BA_X[0]+0.058,y1,1.18],0.011,12),M.get('M_BathChrome'))
  add(world,P.drape(y0+0.05,y0+0.38,L.BA_X[0]+0.07,0.61,1.176,{folds:4,amplitude:0.028,nz:11,seed:31,axis:'Y',thickness:0.011}),M.get('M_Towel'))
  add(world,P.drape(y0+0.46,y0+0.82,L.BA_X[0]+0.07,0.61,1.176,{folds:4,amplitude:0.028,nz:11,seed:38,axis:'Y',thickness:0.011}),M.get('M_Towel2'))
}

export function build(world:World):void {
  buildMaterials()
  buildBedrooms(world)
  buildBathroom(world)
}
