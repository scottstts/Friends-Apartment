import type { ApartmentDefinition } from '../types'
import * as L from './layout'
import { JOEY_CAMERAS } from './contract'
import * as shell from './shell'
import * as openings from './openings'
import * as environment from './environment'
import * as kitchen from './kitchen'
import * as living from './living'
import * as extra from './extra'
import * as rooms from './rooms'
import * as lighting from './lighting'

const tick=():Promise<void>=>new Promise((resolve)=>setTimeout(resolve,0))
const radians=(degrees:number):number=>degrees*Math.PI/180

export const joeyApartment:ApartmentDefinition={
  id:'19',
  label:"Chandler and Joey's apartment",
  async build(world){
    shell.build(world);await tick()
    openings.build(world);await tick()
    environment.build(world);await tick()
    kitchen.build(world);await tick()
    living.build(world);await tick()
    extra.build(world);await tick()
    rooms.build(world);await tick()
    lighting.build(world);await tick()
    world.finalize()
  },
  spawn:{position:[L.EX-0.72,(L.FD_Y[0]+L.FD_Y[1])*0.5],lookAt:[4.65,3.55]},
  interactions:{
    seats:[
      {
        center:L.REC_A,
        facing:Math.PI+radians(L.REC_ROT_A),
        eyeZ:1.245,
        stand:[L.REC_A[0]+Math.cos(Math.PI+radians(L.REC_ROT_A))*0.98,L.REC_A[1]+Math.sin(Math.PI+radians(L.REC_ROT_A))*0.98],
        radius:0.88,
        forwardOffset:0.015,
      },
      {
        center:L.REC_B,
        facing:Math.PI+radians(L.REC_ROT_B),
        eyeZ:1.245,
        stand:[L.REC_B[0]+Math.cos(Math.PI+radians(L.REC_ROT_B))*0.98,L.REC_B[1]+Math.sin(Math.PI+radians(L.REC_ROT_B))*0.98],
        radius:0.88,
        forwardOffset:0.015,
      },
    ],
    door:{point:[L.EX-0.52,(L.FD_Y[0]+L.FD_Y[1])*0.5],radius:0.86},
  },
  cameras:JOEY_CAMERAS,
}
