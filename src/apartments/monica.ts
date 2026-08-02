import * as L from '../lib/L'
import { buildAll } from '../scene/build'
import type { ApartmentDefinition } from './types'

/** Adapter around the existing apartment 20 modules; its scene remains fully
 * separate while the apartment runtime can select it through one contract. */
export const monicaApartment:ApartmentDefinition={
  id:'20',
  label:"Monica and Rachel's apartment",
  build:buildAll,
  spawn:{position:[2.3,-1.15],lookAt:[6.4,3.9]},
  // The mature apartment-20 choreography remains in player/seats.ts. An empty
  // list selects those established couch/chair/bed targets without copying
  // scene-private dimensions into this adapter.
  interactions:{seats:[],door:{point:[0.42,(L.FD_Y[0]+L.FD_Y[1])/2],radius:0.8}},
  cameras:{},
}
