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

// f_beds.py: nothing hung on a bathroom wall sits on the wall LINE (tiling is
// 13 mm proud), and everything in the room stands on the tile top, 14.5 mm
// proud of the parquet datum the rest of the flat is set out from.
const TILE_F=0.013
const BFL=0.0145
const TUBH=0.56

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

/** f_beds.py _pan_ring: an EGG section, widest `waist` of the way from the back. */
function panRing(hw:number,yb:number,yf:number,z:number,n=44,waist=0.38):Vec3[] {
  const cy=yb+(yf-yb)*waist
  const ring:Vec3[]=[]
  for(let i=0;i<n;i++){
    const a=Math.PI*2*i/n,c=Math.cos(a)
    ring.push([hw*Math.sin(a),c>=0?cy+(yf-cy)*c:cy+(cy-yb)*c,z])
  }
  return ring
}

function buildWc(world:World):void {
  const RIM=0.395,SEAT_T=0.019,LID_T=0.026
  const SHELF_Z=RIM+SEAT_T+LID_T+0.007
  const TANK_Z=SHELF_Z+0.31,TLID_Z=SHELF_Z+0.34
  const HW=0.185,YB=-0.118,YF=0.352
  const SY=-0.254,WALL=-0.364
  const rings=[
    panRing(0.118,-0.29,0.15,0),
    panRing(0.112,-0.288,0.144,0.024),
    panRing(0.09,-0.28,0.11,0.13),
    panRing(0.1,-0.276,0.138,0.208),
    panRing(0.14,-0.24,0.226,0.284),
    panRing(0.174,-0.172,0.314,0.356),
    panRing(HW,YB,YF,RIM-0.014),
    panRing(HW,YB,YF,RIM),
    panRing(0.152,YB+0.022,0.282,RIM-0.004),
    panRing(0.132,YB+0.038,0.252,0.347),
    panRing(0.102,YB+0.064,0.192,0.282),
    panRing(0.064,YB+0.098,0.118,0.228),
    panRing(0.032,YB+0.122,0.062,0.202),
  ]
  const pan=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true});mlib.smoothShade(pan,44)
  const shelf=mlib.loft([
    mlib.roundedRect(0.196,0.204,0.046,4).map(([x,y])=>[x,y-0.25,0.17] as Vec3),
    mlib.roundedRect(0.25,0.212,0.044,4).map(([x,y])=>[x,y-0.246,0.29] as Vec3),
    mlib.roundedRect(0.31,0.19,0.036,4).map(([x,y])=>[x,y-0.257,0.396] as Vec3),
    mlib.roundedRect(0.33,0.176,0.03,4).map(([x,y])=>[x,y-0.264,SHELF_Z] as Vec3),
  ],{closeV:true,capStart:true,capEnd:true})
  mlib.bevel(shelf,0.008,2);mlib.smoothShade(shelf,46)
  const flat=mlib.prism(mlib.roundedRect(0.32,0.09,0.026,3),0.32,RIM);mlib.translate(flat,[0,-0.15,0]);mlib.bevel(flat,0.008,2)
  const tank=mlib.prism(mlib.roundedRect(0.428,0.196,0.026,4),SHELF_Z-0.006,TANK_Z);mlib.translate(tank,[0,SY,0]);mlib.bevel(tank,0.012,3)
  const tlid=mlib.prism(mlib.roundedRect(0.452,0.22,0.03,4),TANK_Z,TLID_Z);mlib.translate(tlid,[0,SY,0]);mlib.bevel(tlid,0.009,3)
  const body=mlib.join([pan,shelf,flat,tank,tlid])
  // Seat and lid follow the rim's own outline (constant overhang all round).
  const plan=panRing(HW,YB,YF,0).map((v)=>[v[0],v[1]] as Vec2)
  const cyw=YB+(YF-YB)*0.38
  const ring2d=(k:number,dy=0):Vec2[]=>plan.map(([x,y])=>[x*k,cyw+(y-cyw)*k+dy] as Vec2)
  const seat=mlib.annularPrism(ring2d(1.008),ring2d(0.66,0.03),RIM,RIM+SEAT_T,0.006,3);mlib.smoothShade(seat,40)
  const slid=mlib.loft([
    ring2d(1.018).map(([x,y])=>[x,y,RIM+SEAT_T] as Vec3),
    ring2d(1.014).map(([x,y])=>[x,y,RIM+SEAT_T+LID_T*0.62] as Vec3),
    ring2d(0.93).map(([x,y])=>[x,y,RIM+SEAT_T+LID_T] as Vec3),
  ],{closeV:true,capStart:true,capEnd:true})
  mlib.bevel(slid,0.008,3);mlib.smoothShade(slid,44)
  const seatLid=mlib.join([seat,slid])
  const TKF=SY+0.098
  const esc=mlib.revolve([[0,0],[0.02,0],[0.019,0.014],[0.01,0.02],[0,0.02]],14);mlib.rotX(esc,-Math.PI*0.5);mlib.translate(esc,[-0.128,TKF-0.004,TANK_Z-0.072])
  const lever=mlib.tubeAlong([[-0.128,TKF+0.016,TANK_Z-0.072],[-0.128,TKF+0.024,TANK_Z-0.074],[-0.052,TKF+0.028,TANK_Z-0.102]],mlib.roundedRect(0.022,0.008,0.004,2))
  const stop=mlib.revolve([[0,0],[0.022,0],[0.022,0.052],[0.03,0.058],[0.03,0.07],[0,0.07]],14);mlib.rotX(stop,-Math.PI*0.5);mlib.translate(stop,[-0.242,WALL,0.19])
  const sup=mlib.bez([WALL+0.068,0.19],[WALL+0.2,0.198],[WALL+0.16,0.34],[WALL+0.076,SHELF_Z-0.024],10)
  const last=sup.length-1
  const supply=mlib.tubeAlong(sup.map(([sy,sz],i)=>[-0.242+0.057*(i/last),sy,sz] as Vec3),mlib.circle(0.0095,10))
  const nut=mlib.revolve([[0,0],[0.021,0],[0.021,0.03],[0,0.03]],12);mlib.translate(nut,[-0.185,sup[last][0],SHELF_Z-0.034])
  const fittings=[esc,lever,stop,supply,nut]
  for(const sx of [-0.076,0.076]){
    const hinge=mlib.revolve([[0,0],[0.013,0],[0.013,0.054],[0,0.054]],12)
    mlib.rotY(hinge,Math.PI*0.5);mlib.translate(hinge,[sx-0.027,-0.15,RIM+0.013]);fittings.push(hinge)
  }
  const chrome=mlib.join(fittings);mlib.smoothShade(chrome,38)
  // Quarter turn faces local +Y into the room (-X), tank against the tiles;
  // cx clears the tank LID's back, which overhangs the cistern by 12 mm.
  const cx=L.BA_X[1]-TILE_F-0.366,cy=L.BA_WC[1]
  for(const [md,material,collide] of [[body,'M_Sanitary',true],[seatLid,'M_Sanitary',false],[chrome,'M_BathChrome',false]] as const){
    mlib.rotateZ(md,Math.PI*0.5);mlib.translate(md,[cx,cy,BFL]);add(world,md,M.get(material),collide)
  }
}

function buildTub(world:World):void {
  // The tub stands on the bathroom tile: profile z is off its own underside,
  // the whole shell lifted by BFL, rim-mounted fittings riding on `top`.
  const [x0,x1]=L.BA_TUB_X,y1=L.BA_Y[1],y0=y1-0.735,top=TUBH+BFL,cx=(x0+x1)*0.5,cy=(y0+y1)*0.5,width=x1-x0,depth=y1-y0
  const profile:[number,number,number,number][]=[[width-0.052,depth-0.052,0.048,0],[width-0.006,depth-0.01,0.058,0.086],[width,depth,0.066,0.296],[width,depth,0.066,TUBH-0.012],[width-0.003,depth-0.003,0.066,TUBH],[width-0.15,depth-0.146,0.1,TUBH-0.01],[width-0.172,depth-0.166,0.11,TUBH-0.082],[width-0.24,depth-0.216,0.14,0.222],[width-0.37,depth-0.296,0.15,0.132],[width-0.53,depth-0.376,0.15,0.112]]
  const rings=profile.map(([w,d,r,z])=>mlib.roundedRect(w,d,r,6).map(([x,y])=>[cx+x,cy+y,z+BFL] as Vec3))
  const tub=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true});mlib.smoothShade(tub,44);add(world,tub,M.get('M_Sanitary'),true)
  add(world,mlib.translate(P.lathe([[0,0],[0.026,0],[0.026,0.004],[0,0.004]],18),[x0+0.24,cy,0.114+BFL]),M.get('M_BathChrome'))
  add(world,mlib.translate(P.lathe([[0,0],[0.04,0],[0.038,0.014],[0.02,0.03],[0.019,0.09],[0.026,0.098],[0,0.1]],18),[x0+0.24,y1-0.036,top-0.006]),M.get('M_BathChrome'))
  add(world,mlib.tubeAlong([[x0+0.24,y1-0.036,top+0.078],[x0+0.24,y1-0.13,top+0.086],[x0+0.24,y1-0.18,top+0.052]],mlib.circle(0.017,10)),M.get('M_BathChrome'))
  add(world,mlib.tubeAlong([[x0+0.24,y1-0.03,top+0.05],[x0+0.24,y1-0.03,1.96],[x0+0.24,y1-0.15,2.02]],mlib.circle(0.012,10)),M.get('M_BathChrome'))
  add(world,P.rod([x0-0.01,y0+0.03,2.06],[x1+0.01,y0+0.03,2.06],0.013,12),M.get('M_BathChrome'))
  add(world,P.drape(x0+0.02,x1-0.02,y0+0.03,0.32,2.03,{folds:9,amplitude:0.038,nz:14,seed:13}),M.get('M_ShowerCurtain'))
  const bathMat=P.rug(cx,y0-0.42,0.78,0.52,()=>0,{cell:0.03,thickness:0.016,pile:0.0022,z0:0.017});add(world,bathMat,M.get('M_BathMat'))
  for(const [i,material] of ['M_BottleA','M_BottleB','M_BottleC'].entries())add(world,P.bottle(x1-0.46+i*0.076,y1-0.044,top-0.009,0.024,0.13+i*0.018,0.009),M.get(material))
}

/** f_beds.py _duck_ring: a true ellipse held perpendicular to the spine,
 * centre offset so it reaches `up` above and `dn` below while staying smooth. */
function duckRing(px:number,pz:number,tx:number,tz:number,hw:number,dn:number,up:number,n=30):Vec3[] {
  const ux=tz,uz=-tx
  const o=(up-dn)*0.5,h=(up+dn)*0.5
  const ring:Vec3[]=[]
  for(let i=0;i<n;i++){
    const a=Math.PI*2*i/n,d=o+h*Math.cos(a)
    ring.push([px+ux*d,hw*Math.sin(a),pz+uz*d])
  }
  return ring
}

function buildDuck(world:World):void {
  // On the cistern lid, turned along it (the lid is 220 deep, the duck 170 long).
  const cx=L.BA_X[1]-TILE_F-0.145,cy=L.BA_WC[1]+0.08,cz=0.787,angle=104*Math.PI/180
  // (spine x, spine z, half width, below the spine, above it)
  const prof:[number,number,number,number,number][]=[
    [0.05,0.058,0.007,0.007,0.006],
    [0.041,0.051,0.019,0.016,0.013],
    [0.028,0.041,0.03,0.025,0.021],
    [0.014,0.033,0.037,0.03,0.024],
    [-0.006,0.03,0.04,0.028,0.025],
    [-0.024,0.033,0.038,0.027,0.024],
    [-0.038,0.043,0.032,0.023,0.022],
    [-0.046,0.059,0.025,0.02,0.019],
    [-0.05,0.075,0.022,0.018,0.018],
    [-0.053,0.089,0.026,0.024,0.024],
    [-0.055,0.101,0.029,0.028,0.027],
    [-0.055,0.112,0.022,0.02,0.02],
    [-0.054,0.12,0.009,0.008,0.008],
  ]
  const rings=prof.map(([px,pz,hw,dn,up],k)=>{
    const a=prof[Math.max(k-1,0)],b=prof[Math.min(k+1,prof.length-1)]
    const tx=b[0]-a[0],tz=b[1]-a[1],ln=Math.hypot(tx,tz)||1
    return duckRing(px,pz,tx/ln,tz/ln,hw,dn,up)
  })
  const body=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true});mlib.smoothShade(body,70)
  // The bill: flat and wide, rounded rectangles on their side.
  const billProf:[number,number,number,number,number][]=[
    [-0.068,0.031,0.017,0.006,0.0985],
    [-0.086,0.037,0.014,0.005,0.0968],
    [-0.1,0.035,0.011,0.004,0.0952],
    [-0.112,0.026,0.009,0.004,0.094],
    [-0.119,0.011,0.006,0.002,0.0933],
  ]
  const bill=mlib.loft(billProf.map(([x,w,h,r,zc])=>mlib.roundedRect(w,h,r,4).map(([a,b])=>[x,a,zc+b] as Vec3)),{closeV:true,capStart:true,capEnd:true})
  mlib.bevel(bill,0.0012,2);mlib.smoothShade(bill,58)
  const parts:[MeshData,string][]=[[body,'M_DuckYellow'],[bill,'M_DuckBill']]
  for(const s of [-1,1]){
    const eye=P.lathe([[0,0],[0.0035,0],[0.0055,0.003],[0.005,0.006],[0,0.007]],12)
    P.faceY(eye,s,[-0.058,s*0.024,0.105])
    parts.push([eye,'M_DuckEye'])
  }
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
