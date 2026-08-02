/** Apartment 19 signature props from build_scripts/Joeys_apt/f_extra.py. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'
import * as P from './props'

const add=(world:World,md:MeshData,material:THREE.Material,collide=false):MeshData=>world.add(md,material,{collide})
const rounded=(x0:number,y0:number,z0:number,x1:number,y1:number,z1:number,r=0.012):MeshData=>mlib.bevel(mlib.box(x0,y0,z0,x1,y1,z1),r,3)

function buildMaterials():void {
  M.plastic('M_FoosCase','1A1A1E',{rough:0.4,coat:0.22})
  M.paint('M_FoosField','2C7C44',{rough:0.42,coat:0.22,brush:0.75})
  M.paint('M_FoosLine','E8E6DE',{rough:0.36,coat:0.3})
  M.plastic('M_FoosRed','B32820',{rough:0.3,coat:0.4})
  M.plastic('M_FoosBlue','1E4FA0',{rough:0.3,coat:0.4})
  M.plastic('M_FoosGrip','141416',{rough:0.52,coat:0.1})
  M.metal('M_Rod','D2D6DA',{rough:0.1,brush:0.35,grime:0.25})
  M.wood('M_ShelfWood',['C2A472','D6C098','A68450'],{ring:6,axis:'Z',warp:0.42,rough:[0.26,0.48],coat:0.24,grainRelief:0.05})
  for (const [name,color] of [['Book1','7A2A24'],['Book2','234A6E'],['Book3','2E5A3C'],['Book4','B08A3A'],['Book5','4A3468'],['Book6','8A4420'],['Book7','D8D0BC'],['Book8','2C2A28']]) M.paper(`M_${name}`,color,{rough:0.48,gloss:0.22})
  M.wood('M_StickWood',['A8804A','C6A268','7E5A2E'],{ring:40,axis:'Z',rough:[0.28,0.5],coat:0.2,scale:2})
  M.plastic('M_StickTape','1C1C1F',{rough:0.62})
  M.fabric('M_MopYarn','C8C0AC',{rough:0.96,weave:180,sheen:0.12,bump:0.9,fuzz:1.6})
  M.plastic('M_PhoneWhite','E8E4D8',{rough:0.34,coat:0.28})
}

type Part=[MeshData,string]
function foosMan(material:string):MeshData {
  const body=P.lathe([[0,0],[0.02,0],[0.021,0.014],[0.014,0.022],[0.015,0.048],[0.021,0.058],[0.023,0.072],[0.018,0.082],[0.01,0.086],[0.011,0.092],[0.017,0.1],[0.016,0.112],[0.008,0.118],[0,0.119]],14)
  const md=mlib.join([body,rounded(-0.03,-0.014,0,0.03,0.014,0.012,0.006)])
  md.colorName=material
  return md
}

function buildFoosball(world:World):void {
  const halfLength=L.FOOS_L*0.5, halfWidth=L.FOOS_W*0.5
  const deck=0.78,top=0.9,rodZ=0.862
  const parts:Part[]=[]
  for (const [x0,y0,x1,y1] of [[-halfLength,-halfWidth,-halfLength+0.052,halfWidth],[halfLength-0.052,-halfWidth,halfLength,halfWidth],[-halfLength+0.052,-halfWidth,halfLength-0.052,-halfWidth+0.052],[-halfLength+0.052,halfWidth-0.052,halfLength-0.052,halfWidth]]) parts.push([rounded(x0,y0,0.62,x1,y1,top,0.004),'M_FoosCase'])
  parts.push([mlib.box(-halfLength+0.05,-halfWidth+0.05,0.618,halfLength-0.05,halfWidth-0.05,deck-0.014),'M_FoosCase'])
  parts.push([mlib.box(-halfLength+0.052,-halfWidth+0.052,deck-0.016,halfLength-0.052,halfWidth-0.052,deck),'M_FoosField'])
  parts.push([mlib.box(-0.004,-halfWidth+0.052,deck,0.004,halfWidth-0.052,deck+0.0022),'M_FoosLine'],[mlib.box(-halfLength+0.052,-0.003,deck,halfLength-0.052,0.003,deck+0.0022),'M_FoosLine'],[P.torus(0.145,0.0022,40,6,[0,0,deck+0.001]),'M_FoosLine'])
  for (const sx of [-1,1]) for (const sy of [-1,1]) {
    const x=sx*(halfLength-0.095),y=sy*(halfWidth-0.095)
    parts.push([P.rod([x,y,0.03],[x,y,0.625],0.026,12),'M_Rod'])
    parts.push([mlib.translate(P.lathe([[0,0],[0.034,0],[0.032,0.018],[0.02,0.03],[0,0.032]],14),[x,y,0]),'M_FoosGrip'])
  }
  const layout:[number,number,string][]=[[-0.525,1,'M_FoosRed'],[-0.375,2,'M_FoosRed'],[-0.225,3,'M_FoosBlue'],[-0.075,5,'M_FoosRed'],[0.075,5,'M_FoosBlue'],[0.225,3,'M_FoosRed'],[0.375,2,'M_FoosBlue'],[0.525,1,'M_FoosBlue']]
  for (const [x,count,material] of layout) {
    const side=material==='M_FoosRed'?-1:1
    let y0=-halfWidth-0.055,y1=halfWidth+0.055
    if (side<0)y0-=0.235;else y1+=0.235
    parts.push([P.rod([x,y0,rodZ],[x,y1,rodZ],0.0075,10),'M_Rod'])
    const grip=P.lathe([[0,0],[0.022,0.004],[0.024,0.026],[0.019,0.075],[0.024,0.13],[0.022,0.15],[0,0.154]],16)
    P.faceY(grip,side<0?-1:1,[x,side<0?y0+0.154:y1-0.154,rodZ]); parts.push([grip,'M_FoosGrip'])
    for(let i=0;i<count;i++){
      const y=(i-(count-1)*0.5)*(2*halfWidth-0.16)/Math.max(count,2)
      parts.push([mlib.translate(foosMan(material),[x,y,deck+0.001]),material])
    }
  }
  for(const sy of [-1,1]){
    parts.push([P.rod([-halfLength+0.09,sy*(halfWidth-0.026),top+0.02],[halfLength-0.09,sy*(halfWidth-0.026),top+0.02],0.0035,8),'M_Rod'])
    for(let i=0;i<5;i++){const bead=P.torus(0.011,0.0055,14,6);mlib.rotY(bead,Math.PI*0.5);mlib.translate(bead,[-halfLength+0.14+i*0.048,sy*(halfWidth-0.026),top+0.02]);parts.push([bead,'M_FoosGrip'])}
  }
  const angle=L.FOOS_ROT*Math.PI/180
  for(const [md,material] of parts){mlib.rotateZ(md,angle);mlib.translate(md,[L.FOOS_C[0],L.FOOS_C[1],0]);add(world,md,M.get(material))}
  world.obb(L.FOOS_C[0],L.FOOS_C[1],halfLength,halfWidth,angle,0,1)
}

function buildBookcase(world:World):void {
  const y0=L.SY+0.16,y1=L.SY+1.04,x0=L.WX+0.026,x1=x0+0.33,z1=1.9
  const shelves=[0.4,0.76,1.12,1.48]
  const pieces=[mlib.box(x0,y0,0,x1,y0+0.024,z1),mlib.box(x0,y1-0.024,0,x1,y1,z1),mlib.box(x0,y0+0.024,0,x0+0.02,y1-0.024,z1),mlib.box(x0+0.02,y0+0.024,z1-0.022,x1,y1-0.024,z1),mlib.box(x0+0.02,y0+0.024,0.055,x1,y1-0.024,0.077),...shelves.map(z=>mlib.box(x0+0.02,y0+0.024,z-0.011,x1,y1-0.024,z+0.011))]
  add(world,mlib.bevel(mlib.join(pieces),0.003,2),M.get('M_ShelfWood'),true)
  const rng=new PyRandom(77), materials=['M_Book1','M_Book2','M_Book3','M_Book4','M_Book5','M_Book6','M_Book7','M_Book8','M_FoosRed','M_FoosBlue','M_ShelfWood']
  const front=x1-0.014
  for(const z of [0.077,...shelves]){
    let y=y0+0.06
    while(y<y1-0.14){
      const width=rng.uniform(0.024,0.042)
      add(world,rounded(front-rng.uniform(0.15,0.2),y,z+0.011,front,y+width,z+0.011+rng.uniform(0.19,0.28),0.0015),M.get(rng.choice(materials)))
      y+=width+rng.uniform(0.012,0.03)
    }
  }
  const cx=x0+0.16,cy=(y0+y1)*0.5
  add(world,P.sweepVar([[cx,cy-0.235,z1+0.052],[cx,cy-0.17,z1+0.044],[cx,cy-0.04,z1+0.038],[cx,cy+0.11,z1+0.04],[cx,cy+0.205,z1+0.052]],[[0.018,0.014],[0.048,0.044],[0.058,0.052],[0.044,0.044],[0.014,0.016]],12),M.get('M_PhoneWhite'))
  add(world,P.rod([cx,cy-0.02,z1+0.07],[cx,cy-0.02,z1+0.4],0.0045,8),M.get('M_StickWood'))
  const sail=MeshData.from([[cx-0.002,cy-0.022,z1+0.395],[cx-0.002,cy-0.022,z1+0.095],[cx-0.002,cy+0.168,z1+0.105]],[[0,1,2]]);mlib.solidify(sail,0.003);add(world,sail,M.get('M_PhoneWhite'))
}

function buildPhone(world:World):void {
  const y=L.PHONE_Y,z=1.44,x=L.EX,front=x-0.07,handX=front-0.032
  add(world,rounded(front,y-0.086,z-0.135,x-0.004,y+0.086,z+0.135,0.016),M.get('M_PhoneWhite'))
  // WebGPU cannot resolve the Blender well/body faces when both begin at XF.
  // Keep the well recessed behind the keys but 0.8 mm proud of the body plane.
  const wellFront=front-0.0008
  add(world,rounded(wellFront,y-0.05,z-0.104,front+0.009,y+0.05,z+0.078,0.002),M.get('M_FoosGrip'))
  for(let row=0;row<4;row++)for(let col=0;col<3;col++)add(world,rounded(front-0.0032,y-0.032+col*0.032-0.0125,z+0.062-row*0.044-0.0165,front+0.005,y-0.032+col*0.032+0.0125,z+0.062-row*0.044+0.0165,0.0018),M.get('M_PhoneWhite'))
  add(world,P.sweepVar([[handX,y,z+0.146],[handX-0.001,y,z+0.116],[handX-0.002,y,z+0.066],[handX-0.003,y,z+0.004],[handX-0.002,y,z-0.06],[handX-0.001,y,z-0.112],[handX,y,z-0.142]],[[0.03,0.031],[0.031,0.032],[0.017,0.018],[0.0145,0.0155],[0.017,0.018],[0.031,0.032],[0.029,0.03]],20),M.get('M_PhoneWhite'))
  const coil:Vec3[]=Array.from({length:96},(_,i)=>{const t=i/95,a=t*Math.PI*18;return[front-0.01-0.012*(1-Math.cos(a)),y+0.044+0.028*Math.sin(a),z-0.152-t*0.36]})
  add(world,mlib.tubeAlong(coil,mlib.circle(0.004,6)),M.get('M_PhoneWhite'))
}

function buildMopHead(world:World,cx:number,cy:number,top:number,drop:number,seed:number):void {
  const ferrule=P.lathe([[0,0],[0.021,0],[0.023,0.012],[0.031,0.022],[0.032,0.07],[0.024,0.084],[0,0.086]],18)
  add(world,mlib.translate(ferrule,[cx,cy,top-0.07]),M.get('M_Rod'))

  add(world,P.sweepVar(
    [[cx,cy,top-0.01],[cx,cy,top-0.07],[cx,cy,top-drop*0.42],[cx,cy,top-drop*0.66]],
    [[0.024,0.024],[0.03,0.03],[0.032,0.032],[0.028,0.028]],16,[0,0,1],true,54,
  ),M.get('M_MopYarn'))

  const rng=new PyRandom(seed)
  const addStrands=(count:number,r0:number,flare0:number,flare1:number,radius:number):void=>{
    for(let k=0;k<count;k++){
      const angle=Math.PI*2*k/count+rng.uniform(-0.09,0.09)
      const drift=rng.uniform(-0.26,0.26)
      const flare=rng.uniform(flare0,flare1)
      const length=drop*rng.uniform(0.82,1)
      const at=(z:number,r:number,a:number):Vec3=>[cx+r*Math.cos(a),cy+r*Math.sin(a),z]
      const path:Vec3[]=[
        at(top-0.014,r0*0.7,angle),
        at(top-0.062,r0,angle+drift*0.1),
        at(top-length*0.38,r0*1.04+flare*0.26,angle+drift*0.34),
        at(top-length*0.72,r0*1.08+flare*0.66,angle+drift*0.68),
        at(top-length,r0*1.1+flare,angle+drift),
      ]
      const strand=mlib.tubeAlong(path,mlib.circle(radius,6))
      mlib.smoothShade(strand,50)
      add(world,strand,M.get('M_MopYarn'))
    }
  }
  addStrands(34,0.025,0.012,0.032,0.004)
  addStrands(22,0.013,0.006,0.02,0.0036)
}

function buildMops(world:World):void {
  const hookHeight=1.78
  const stand=0.078
  const ferruleHeight=0.335
  const specs:[number,number,number][]=[[3.12,1.404,0.33],[3.31,1.462,0.352]]
  for(let i=0;i<specs.length;i++){
    const [bx,handleLength,drop]=specs[i]
    const rose=P.lathe([[0,0],[0.02,0],[0.021,0.005],[0.016,0.009],[0,0.01]],16)
    P.faceY(rose,-1,[bx,L.NY,hookHeight])
    add(world,rose,M.get('M_Rod'))

    const hook=mlib.tubeAlong([
      [bx,L.NY-0.004,hookHeight],
      [bx,L.NY-stand*0.62,hookHeight],
      [bx,L.NY-stand-0.008,hookHeight-0.01],
      [bx,L.NY-stand-0.014,hookHeight-0.03],
      [bx,L.NY-stand,hookHeight-0.044],
      [bx,L.NY-stand+0.02,hookHeight-0.04],
    ],mlib.circle(0.0038,8))
    mlib.smoothShade(hook,48)
    add(world,hook,M.get('M_Rod'))

    const by=L.NY-stand
    const ringZ=hookHeight-0.026
    const base=ringZ-(handleLength+0.05)
    const handle=mlib.tubeAlong([
      [bx,by,base+ferruleHeight-0.09],
      [bx,by,base+0.62],
      [bx,by,base+1.02],
      [bx,by,base+handleLength],
    ],mlib.circle(0.0125,12))
    mlib.smoothShade(handle,46)
    add(world,handle,M.get('M_StickWood'))

    const cap=P.lathe([[0,0],[0.0128,0],[0.0132,0.03],[0.01,0.042],[0,0.046]],14)
    add(world,mlib.translate(cap,[bx,by,base+handleLength-0.004]),M.get('M_StickTape'))

    const ring=P.torus(0.0092,0.0024,16,6,[bx,by,ringZ])
    mlib.rotY(ring,Math.PI*0.5,[bx,by,ringZ])
    add(world,ring,M.get('M_Rod'))

    buildMopHead(world,bx,by,base+ferruleHeight,drop,11+i*7)
  }
}

export function build(world:World):void {
  buildMaterials()
  buildFoosball(world)
  buildBookcase(world)
  buildPhone(world)
  buildMops(world)
}
