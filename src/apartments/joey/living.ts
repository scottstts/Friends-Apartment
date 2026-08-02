/** Apartment 19 living room, ported from build_scripts/Joeys_apt/f_living.py. */
import type * as THREE from 'three/webgpu'
import { MeshData, type Vec3 } from '../../lib/mesh'
import * as mlib from '../../lib/mlib'
import { PyRandom } from '../../lib/rng'
import type { World } from '../../scene/world'
import * as L from './layout'
import * as M from './materials'
import * as P from './props'

const add = (world: World, md: MeshData, material: THREE.Material, collide = false): MeshData => world.add(md, material, { collide })
const rounded = (x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, radius = 0.012): MeshData =>
  mlib.bevel(mlib.box(x0, y0, z0, x1, y1, z1), radius, 3)

function buildMaterials(): void {
  M.leather('M_YellowLeather', 'E3C41C', { rough: 0.42, crease: 0.85, grain: 0.5, coat: 0.26, wear: 0.1 })
  M.leather('M_BlackLeather', '15151A', { rough: 0.44, crease: 1.05, grain: 0.42, coat: 0.16 })
  M.wood('M_TableWood', ['9A6634', 'B98A4E', '6E421F'], { ring: 8, axis: 'Y', warp: 0.85, rough: [0.24, 0.46], coat: 0.3, grainRelief: 0.07 })
  M.wood('M_DarkWood', ['4A2C18', '6B4224', '331C0E'], { ring: 9, axis: 'Z', warp: 0.45, rough: [0.26, 0.48], coat: 0.22, grainRelief: 0.06 })
  M.wood('M_EntWood', ['C6A876', 'DCC79E', 'AA8A54'], { ring: 7.5, axis: 'Z', warp: 0.26, rough: [0.24, 0.44], coat: 0.26, grainRelief: 0.045, scale: 0.9 })
  M.wood('M_EntBack', ['B49A70', 'C6B08A', '9A8058'], { ring: 5, axis: 'Z', warp: 0.35, rough: [0.3, 0.5], coat: 0.1, grainRelief: 0.04, scale: 0.9 })
  M.wood('M_EntTop', ['CCAE7C', 'DEC69A', 'B08C58'], { ring: 6, axis: 'Y', warp: 0.4, rough: [0.22, 0.42], coat: 0.32, grainRelief: 0.05 })
  M.metal('M_Steel', 'B9BDC2', { rough: 0.2, brush: 0.5, grime: 0.3 })
  M.metal('M_Bronze', '4A3E30', { rough: 0.36, grime: 0.45 })
  M.paint('M_TableSlate', '74787A', { rough: 0.46, coat: 0.1, brush: 0.3 })
  M.plastic('M_TableCap', 'EAE4D6', { rough: 0.36, coat: 0.22 })
  M.plastic('M_TVCase', '232326', { rough: 0.42, coat: 0.2 })
  M.plastic('M_Screen', '20242A', { rough: 0.07, coat: 0.7 })
  M.plastic('M_TVBezel', '3A3A3E', { rough: 0.44, coat: 0.2 })
  M.clearGlass('M_TableGlass', 'E8F0F1', { rough: 0.02 })
  M.diamond('M_Curtain', 'C9B084', { ink: 'A38F62', pitch: 0.128, rough: 0.76 })
  M.fabric('M_Cushion1', '6E5E86', { rough: 0.72, weave: 300, sheen: 0.45 })
  M.fabric('M_Cushion2', 'B8B2A2', { rough: 0.78, weave: 320, sheen: 0.35 })
  M.fabric('M_Cushion3', '3C4A5E', { rough: 0.74, weave: 310, sheen: 0.4 })
  M.carpet('M_RugCream', 'DCD4C0', { rough: 0.94 })
  M.carpet('M_RugOrange', 'AE7440', { rough: 0.94 })
  M.carpet('M_RugMaroon', '7A3A32', { rough: 0.94 })
  M.carpet('M_RugGrey', '9A9384', { rough: 0.94 })
  M.carpet('M_RugDark', '5A4E42', { rough: 0.94 })
  M.carpet('M_MatWhite', 'E4E0D6', { rough: 0.94 })
  M.carpet('M_MatRed', 'AE2B26', { rough: 0.94 })
  M.paint('M_LampShade', 'E6E2D6', { rough: 0.55 })
  M.picture('M_ArtLaurel', '/Laurel_and_Hardy_poster.jpeg', { rough: 0.4, gloss: 0.28 })
  M.picture('M_ArtVendetta', '/Vendetta_poster.jpg', { rough: 0.36, gloss: 0.34 })
  M.picture('M_ArtDieHard', '/die_hard.jpeg', { rough: 0.38, gloss: 0.3 })
  M.paper('M_ArtA', '2A2622', { rough: 0.34, gloss: 0.45 })
  M.paper('M_ArtB', 'B0A48C', { rough: 0.4, gloss: 0.35 })
  M.paper('M_MagA', 'B8503A', { rough: 0.3, gloss: 0.6 })
  M.paper('M_MagB', '2E6E8A', { rough: 0.3, gloss: 0.6 })
  M.fabric('M_PlantGreen', '3C6E3A', { rough: 0.62, weave: 180, sheen: 0.55, bump: 0.3 })
  for (const [name, color] of [['M_ToyRed','C0342A'],['M_ToyBlue','2A56A0'],['M_ToyGreen','2E7A44'],['M_ToyYellow','D8A81E']]) M.plastic(name, color, { rough: 0.24, coat: 0.45 })
  M.fabric('M_PengBlack', '1C1C22', { rough: 0.88, weave: 420, sheen: 0.55, fuzz: 1 })
  M.fabric('M_PengWhite', 'E4E0D4', { rough: 0.88, weave: 420, sheen: 0.55, fuzz: 1 })
  M.fabric('M_PengBeak', 'D8901E', { rough: 0.72, weave: 380, sheen: 0.4 })
  M.plastic('M_PengEye', '141014', { rough: 0.14, coat: 0.65 })
}

function transform(parts: MeshData[], location: [number, number], rotation = 0, z = 0): void {
  for (const md of parts) {
    if (rotation) mlib.rotateZ(md, rotation)
    mlib.translate(md, [location[0], location[1], z])
  }
}

function buildCouch(world: World): void {
  const halfLength = L.SOFA_L * 0.5
  const halfDepth = L.SOFA_D * 0.5
  const leather: MeshData[] = [rounded(-halfLength, -halfDepth, 0.115, halfLength, halfDepth, 0.292, 0.03)]
  for (const side of [-1, 1]) {
    const x = side * (halfLength - 0.105)
    leather.push(P.sweepVar([[x,-halfDepth+0.01,0.492],[x,-halfDepth+0.055,0.492],[x,0,0.494],[x,halfDepth-0.055,0.492],[x,halfDepth-0.01,0.492]], [[0.07,0.034],[0.098,0.07],[0.104,0.076],[0.098,0.07],[0.07,0.034]], 18))
    leather.push(rounded(x - 0.104, -halfDepth, 0.272, x + 0.104, halfDepth, 0.5, 0.026))
  }
  leather.push(P.sweepVar([[-halfLength+0.15,halfDepth-0.115,0.726],[-halfLength+0.205,halfDepth-0.115,0.726],[0,halfDepth-0.115,0.73],[halfLength-0.205,halfDepth-0.115,0.726],[halfLength-0.15,halfDepth-0.115,0.726]], [[0.056,0.05],[0.078,0.066],[0.082,0.07],[0.078,0.066],[0.056,0.05]], 18))
  leather.push(rounded(-halfLength + 0.15, halfDepth - 0.19, 0.268, halfLength - 0.15, halfDepth - 0.04, 0.74, 0.024))
  for (const side of [-1, 1]) leather.push(mlib.translate(mlib.cushion(0.762, 0.66, 0.15, 0.058, 6), [side * 0.384, -0.048, 0.28]))
  transform(leather, L.SOFA_C)
  for (const md of leather) add(world, md, M.get('M_YellowLeather'))
  world.obb(L.SOFA_C[0], L.SOFA_C[1], halfLength, halfDepth, 0, 0, 0.8)

  for (const [dx, dy] of [[-halfLength+0.11,-halfDepth+0.1],[halfLength-0.11,-halfDepth+0.1],[-halfLength+0.11,halfDepth-0.1],[halfLength-0.11,halfDepth-0.1]]) {
    const foot = P.lathe([[0,0],[0.021,0],[0.024,0.02],[0.026,0.108],[0,0.115]], 14)
    add(world, mlib.translate(foot, [L.SOFA_C[0] + dx, L.SOFA_C[1] + dy, 0]), M.get('M_Steel'))
  }
  const pillows: [MeshData, string][] = []
  for (const [size, lean, yaw, dx, material] of [[0.36,66,-12,-0.6,'M_Cushion2'],[0.33,72,9,-0.26,'M_Cushion3']] as const) {
    const pillow = P.pillow(size, size, 0.135)
    mlib.rotX(pillow, lean * Math.PI / 180)
    mlib.rotateZ(pillow, yaw * Math.PI / 180)
    mlib.translate(pillow, [L.SOFA_C[0] + dx, L.SOFA_C[1] + 0.176, 0.43 + size * 0.5 * Math.sin(lean * Math.PI / 180)])
    pillows.push([pillow, material])
  }
  for (const [md, material] of pillows) add(world, md, M.get(material))
}

function buildRecliner(world: World, location: [number, number], degrees: number): void {
  const leather: MeshData[] = [
    rounded(-0.5,-0.442,0.13,0.45,0.442,0.3,0.032), rounded(-0.48,-0.31,0.288,0.34,0.31,0.345,0.026), rounded(-0.545,-0.3,0.14,-0.462,0.3,0.436,0.03),
  ]
  for (const side of [-1, 1]) {
    const y = side * 0.372
    leather.push(P.sweepVar([[-0.545,y,0.502],[-0.497,y,0.512],[-0.419,y,0.518],[0.1,y,0.52],[0.38,y,0.522],[0.464,y,0.514]], [[0.06,0.06],[0.088,0.098],[0.1,0.108],[0.1,0.108],[0.098,0.108],[0.072,0.086]], 20))
    leather.push(rounded(-0.492, y - 0.098, 0.286, 0.46, y + 0.098, 0.474, 0.024))
  }
  leather.push(mlib.translate(mlib.cushion(0.76, 0.605, 0.122, 0.062, 7), [-0.055, 0, 0.318]))
  for (const [z, x, rz] of [[0.516,0.3,0.098],[0.684,0.328,0.098],[0.852,0.356,0.098],[1,0.378,0.086]]) leather.push(P.sweepVar([[x,-0.336,z],[x,-0.286,z],[x,0,z],[x,0.286,z],[x,0.336,z]], [[0.086,rz*0.6],[0.108,rz*0.94],[0.112,rz],[0.108,rz*0.94],[0.086,rz*0.6]], 20))
  leather.push(rounded(0.258,-0.348,0.322,0.47,0.348,1.048,0.032))
  const wood = [rounded(-0.47,-0.4,0,0.42,0.4,0.14,0.028), P.rod([0.28,0.462,0.4],[0.33,0.556,0.418],0.01,8)]
  const knob = P.lathe([[0,0],[0.026,0.004],[0.028,0.026],[0,0.034]],14)
  mlib.rotX(knob, -72 * Math.PI / 180)
  wood.push(mlib.translate(knob, [0.33,0.556,0.418]))
  const angle = degrees * Math.PI / 180
  transform(leather, location, angle, 0.025)
  transform(wood, location, angle, 0.025)
  for (const md of leather) add(world, md, M.get('M_BlackLeather'))
  for (const md of wood) add(world, md, M.get('M_DarkWood'))
  world.obb(location[0], location[1], 0.55, 0.46, angle, 0, 1.1)
}

function buildTables(world: World): void {
  const [cx, cy] = L.COFFEE_C
  const width = 1.16
  const depth = 0.52
  const topZ = 0.405
  add(world, mlib.translate(rounded(-width/2,-depth/2,topZ-0.11,width/2,depth/2,topZ-0.014,0.004), [cx,cy,0]), M.get('M_TableWood'), true)
  add(world, mlib.translate(P.worktop(-width/2-0.011,-depth/2-0.011,width/2+0.011,depth/2+0.011,topZ,{thickness:0.017,radius:0.007}), [cx,cy,0]), M.get('M_TableSlate'))
  for (const sx of [-1,1]) for (const sy of [-1,1]) {
    const x = cx + sx * (width/2 - 0.014)
    const y = cy + sy * (depth/2 - 0.008)
    add(world, rounded(x-0.05,y-0.044,0.262,x+0.05,y+0.044,topZ-0.02,0.016), M.get('M_TableCap'))
    for (const [ex,ey] of [[sx*0.088,sy*0.014],[sx*0.014,sy*0.088]]) add(world, mlib.tubeAlong([[x,y,0.272],[x+ex*0.24,y+ey*0.24,0.196],[x+ex*0.6,y+ey*0.6,0.104],[x+ex,y+ey,0.005]], mlib.circle(0.0058,8)), M.get('M_Bronze'))
  }
  const [gx, gy] = L.GLASS_T
  for (const [r,z] of [[0.235,0.505],[0.205,0.235]]) add(world, mlib.translate(P.lathe([[0,0],[r-0.006,0],[r,0.005],[r-0.006,0.01],[0,0.01]],36), [gx,gy,z]), M.get('M_TableGlass'))
  for (let i=0;i<3;i++) {
    const a = Math.PI*2*i/3+0.4
    add(world, P.rod([gx+0.185*Math.cos(a),gy+0.185*Math.sin(a),0],[gx+0.135*Math.cos(a),gy+0.135*Math.sin(a),0.505],0.011,10), M.get('M_Steel'))
  }
  add(world, P.torus(0.152,0.008,30,8,[gx,gy,0.235]), M.get('M_Steel'))
  const remote = rounded(gx-0.095,gy-0.028,0.515,gx+0.095,gy+0.028,0.536,0.01)
  mlib.rotateZ(remote,0.5,[gx,gy])
  add(world,remote,M.get('M_TVCase'))

  const [sx,sy]=L.SIDE_T
  for (const [r,z] of [[0.245,0.56],[0.215,0.29]]) add(world, mlib.translate(P.lathe([[0,0],[r-0.014,0],[r,0.008],[r-0.006,0.019],[0,0.019]],32),[sx,sy,z]),M.get('M_LampShade'))
  add(world,mlib.translate(P.lathe([[0,0],[0.075,0],[0.072,0.014],[0.03,0.04],[0.028,0.54],[0.036,0.56],[0,0.562]],20),[sx,sy,0]),M.get('M_Steel'),true)
}

function buildRugs(world: World): void {
  const rug = P.rug(L.RUG_C[0],L.RUG_C[1],L.RUG_WH[0],L.RUG_WH[1],(u,v)=> {
    if (u<0.035||u>0.965||v<0.022||v>0.978) return 4
    if (u>=0.06&&u<=0.46&&v>=0.6&&v<=0.885) return 1
    if (u>=0.54&&u<=0.94&&v>=0.055&&v<=0.285) return 2
    if ((u>=0.1&&u<=0.52&&v>=0.085&&v<=0.32)||(u>=0.58&&u<=0.93&&v>=0.615&&v<=0.775)) return 3
    return 0
  },{cell:0.032,thickness:0.013,z0:0.012})
  world.addMulti(rug,[M.get('M_RugCream'),M.get('M_RugOrange'),M.get('M_RugMaroon'),M.get('M_RugGrey'),M.get('M_RugDark')])
  const mat = P.rug(1.3,L.NY-1.66,1.22,0.8,(u,v)=>u<0.06||u>0.94||v<0.09||v>0.91?0:(Math.abs((u*7)%1-0.5)*2>0.55&&Math.floor(v*5)%2===0?1:0),{cell:0.02,thickness:0.011,z0:0.012})
  world.addMulti(mat,[M.get('M_MatWhite'),M.get('M_MatRed')])
}

function buildTelevision(world: World, x0: number, cy: number, z0: number, width=0.78, height=0.575, depth=0.48): void {
  const rings = [[x0+depth,0.5*width,0.5*height],[x0+0.1,0.5*width,0.5*height],[x0+0.055,0.44*width,0.44*height],[x0,0.4*width,0.4*height]].map(([x,ry,rz])=>mlib.roundedRect(ry*2,rz*2,0.045,5).map(([y,z])=>[x,cy+y,z0+height*0.5+z] as Vec3))
  const casing=mlib.loft(rings,{closeV:true,capStart:true,capEnd:true}); mlib.smoothShade(casing,34)
  add(world,casing,M.get('M_TVCase'))
  const bezel=mlib.prismYZ(mlib.roundedRect(width-0.062,height-0.126,0.044,5).map(([y,z])=>[cy+y,z0+height*0.5+0.026+z]),x0+depth-0.02,x0+depth+0.008)
  const screen=mlib.prismYZ(mlib.roundedRect(width-0.104,height-0.168,0.038,5).map(([y,z])=>[cy+y,z0+height*0.5+0.026+z]),x0+depth-0.026,x0+depth+0.002)
  add(world,mlib.bevel(bezel,0.005,3),M.get('M_TVBezel'))
  add(world,mlib.bevel(screen,0.004,3),M.get('M_Screen'))
}

function buildEntertainment(world: World): void {
  const [y0,y1]=L.ENT_Y
  const x0=L.WX+0.026, x1=x0+L.ENT_D
  const thickness=0.02, zBase=0.1, zMid=0.615, zTop=1.56
  const ya=y0+0.66, yb=y1-0.6
  const parts: MeshData[]=[]
  for (const y of [y0,ya,yb,y1-thickness]) parts.push(mlib.box(x0,y,zBase,x1,y+thickness,zTop))
  for (const z of [zBase,zMid,zTop-thickness]) parts.push(mlib.box(x0+0.016,y0,z,x1,y1,z+thickness))
  for (const z of [0.865,1.11,1.33]) parts.push(mlib.box(x0+0.016,y0+thickness,z-0.009,x1,ya,z+0.009))
  for (const z of [0.925,1.245]) parts.push(mlib.box(x0+0.016,yb+thickness,z-0.009,x1,y1-thickness,z+0.009))
  add(world,mlib.bevel(mlib.join(parts),0.0025,2),M.get('M_EntWood'),true)
  add(world,rounded(x0+0.003,y0+0.004,zBase+0.004,x0+0.019,y1-0.004,zTop-0.004,0.002),M.get('M_EntBack'))
  add(world,rounded(x0+0.01,y0-0.014,zTop,x1+0.02,y1+0.014,zTop+0.042,0.005),M.get('M_EntWood'))
  add(world,rounded(x0+0.006,y0+0.026,0,x1-0.06,y1-0.026,0.104,0.003),M.get('M_TVCase'))
  for (const [a,b,za,zb] of [[y0+thickness+0.005,ya-0.005,zBase+0.035,zMid-0.02],[yb+thickness+0.005,y1-thickness-0.005,zBase+0.035,zMid-0.02],[yb+thickness+0.005,y1-thickness-0.005,zMid+0.017,zTop-thickness-0.016]]) {
    add(world,mlib.bevel(mlib.prismYZ(mlib.roundedRect(b-a,zb-za,0.008,3).map(([y,z])=>[(a+b)*0.5+y,(za+zb)*0.5+z]),x1,x1+0.019),0.0025,2),M.get('M_EntWood'))
    add(world,rounded(x1+0.019,a+0.028,zb-0.044,x1+0.026,b-0.028,zb-0.022,0.003),M.get('M_TVCase'))
  }
  const rng=new PyRandom(31)
  const shelfMats=['M_Cushion1','M_Cushion3','M_ArtB','M_MagA','M_MagB','M_LampShade']
  for (const z of [zMid+thickness,0.884,1.129,1.349]) {
    let y=y0+thickness+0.04
    while (y<ya-0.11) {
      const width=rng.uniform(0.026,0.044)
      add(world,rounded(x1-rng.uniform(0.15,0.21),y,z,x1-0.016,y+width,z+rng.uniform(0.15,0.2),0.0015),M.get(rng.choice(shelfMats)))
      y+=width+rng.uniform(0.01,0.026)
    }
  }
  buildTelevision(world,x0+0.03,(ya+yb)*0.5,zMid+0.02)
  add(world,rounded(x0+0.055,(ya+yb)*0.5-0.215,zBase+0.028,x0+0.415,(ya+yb)*0.5+0.215,zBase+0.12,0.01),M.get('M_TVCase'))
  const topZ=zTop+0.042
  const topRng=new PyRandom(83)
  for (let i=0;i<3;i++) {
    const book=rounded(x0+0.075,y0+1.12,topZ+i*0.03,x0+0.075+topRng.uniform(0.22,0.27),y0+1.12+topRng.uniform(0.15,0.185),topZ+i*0.03+0.028,0.002)
    mlib.rotateZ(book,topRng.uniform(-0.13,0.13),[x0+0.19,y0+1.2]); add(world,book,M.get(['M_Cushion1','M_MagA','M_Cushion3'][i]))
  }
  add(world,P.boxProp(x0+0.185,y0+1.86,topZ,0.26,0.175,0.115,0.09),M.get('M_DarkWood'))
  add(world,P.boxProp(x0+0.185,y0+1.86,topZ+0.115,0.276,0.19,0.022,0.09),M.get('M_DarkWood'))
}

function buildCurtains(world: World): void {
  const panels:[[number,number],[number,number],[number,number]]=[[0.185,0.665],[1.25,1.905],[2.52,3.01]]
  for (let i=0;i<panels.length;i++) {
    const [a,b]=panels[i]
    add(world,P.drape(a,b,L.NY-0.115,0.03,L.ROD_Z-0.07,{folds:Math.max(4,Math.floor((b-a)/0.115)),amplitude:0.052,nz:16,seed:7+i*5}),M.get('M_Curtain'))
  }
  add(world,P.rod([L.ROD_X[0]-0.1,L.NY-0.13,L.ROD_Z],[L.ROD_X[1]+0.1,L.NY-0.13,L.ROD_Z],0.0145,14),M.get('M_Bronze'))
  for (const x of [0.3,1.58,2.86]) add(world,P.rod([x,L.NY-0.012,L.ROD_Z],[x,L.NY-0.13,L.ROD_Z],0.009,10),M.get('M_Bronze'))
}

function addArt(world: World, width:number,height:number,wall:'W'|'E',u:number,z:number,at:number,picture:string,frame='M_DarkWood',moulding=0.03):void {
  const [fr,art]=P.frameArt(width,height,0.028,moulding,0.006,0.019)
  P.wallPlace([fr,art],wall,u,z,at)
  add(world,fr,M.get(frame)); add(world,art,M.get(picture))
}

function buildArtAndDressing(world: World): void {
  addArt(world,0.92,0.604,'W',(L.ENT_Y[0]+L.ENT_Y[1])*0.5,2.285,L.WX,'M_ArtLaurel','M_DarkWood',0.044)
  addArt(world,0.69,0.981,'E',1.05,1.615,L.EX,'M_ArtDieHard','M_DarkWood',0.03)
  addArt(world,0.6,0.937,'W',6.34,1.62,L.WX,'M_ArtVendetta','M_TVCase',0.028)
  for (const [i,dx,dy,rz,mat] of [[0,-0.3,-0.06,0.18,'M_MagA'],[1,-0.16,0.05,-0.3,'M_MagB'],[2,0.24,-0.03,0.42,'M_MagA']] as const) {
    const magazine=mlib.box(-0.105,-0.14,i*0.007,0.105,0.14,i*0.007+0.006); mlib.rotateZ(magazine,rz); mlib.translate(magazine,[L.COFFEE_C[0]+dx,L.COFFEE_C[1]+dy,0.405]); add(world,magazine,M.get(mat))
  }
  add(world,P.bowl(L.COFFEE_C[0]+0.02,L.COFFEE_C[1]+0.06,0.405,0.095,0.055),M.get('M_LampShade'))
}

function buildPenguin(world: World): void {
  const parts: [MeshData,string][]=[
    [P.sweepVar([[0,0,0.008],[0.012,0,0.06],[0.016,0,0.14],[0.01,0,0.225],[-0.002,0,0.295],[-0.008,0,0.345],[-0.004,0,0.392],[0.006,0,0.426],[0,0,0.444]],[[0.055,0.045],[0.102,0.096],[0.122,0.118],[0.116,0.112],[0.096,0.092],[0.082,0.08],[0.082,0.08],[0.06,0.058],[0.016,0.016]],22),'M_PengBlack'],
    [P.sweepVar([[-0.07,0,0.062],[-0.098,0,0.14],[-0.102,0,0.215],[-0.086,0,0.278],[-0.066,0,0.312]],[[0.06,0.026],[0.078,0.032],[0.074,0.032],[0.058,0.026],[0.038,0.018]],18),'M_PengWhite'],
    [P.sweepVar([[-0.072,0,0.374],[-0.104,0,0.366],[-0.128,0,0.358]],[[0.026,0.017],[0.017,0.011],[0.005,0.004]],12),'M_PengBeak'],
  ]
  const angle=136*Math.PI/180
  for (const [md,mat] of parts) {mlib.rotateZ(md,angle); mlib.translate(md,[L.SOFA_C[0]-0.7,L.SOFA_C[1]-0.06,0.428]); add(world,md,M.get(mat))}
}

function buildFloorLamp(world: World): void {
  const [cx,cy]=L.FLOOR_LAMP
  add(world,mlib.translate(P.lathe([[0,0],[0.135,0],[0.138,0.01],[0.12,0.02],[0.026,0.03],[0.024,0.05],[0,0.052]],24),[cx,cy,0]),M.get('M_Steel'),true)
  add(world,P.rod([cx,cy,0.04],[cx,cy,1.64],0.0145,12),M.get('M_Steel'))
  add(world,mlib.translate(P.lathe([[0,0],[0.154,0],[0.152,0.007],[0.113,0.198],[0.111,0.205],[0.15,0.011],[0,0.011]],30),[cx,cy,1.5]),M.get('M_LampShade'))
}

export function build(world: World): void {
  buildMaterials()
  buildCouch(world)
  buildRecliner(world,L.REC_A,L.REC_ROT_A)
  buildRecliner(world,L.REC_B,L.REC_ROT_B)
  buildTables(world)
  buildRugs(world)
  buildEntertainment(world)
  buildCurtains(world)
  buildArtAndDressing(world)
  buildPenguin(world)
  buildFloorLamp(world)
}
