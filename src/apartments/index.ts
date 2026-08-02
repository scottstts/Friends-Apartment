import type { ApartmentDefinition, ApartmentId } from './types'

const importers:Record<ApartmentId,()=>Promise<ApartmentDefinition>>={
  '19':async()=>(await import('./joey')).joeyApartment,
  '20':async()=>(await import('./monica')).monicaApartment,
}

/** Dynamic module promises are retained for the life of the page. Together
 * with the runtime's built-world cache and the browser's HTTP module cache,
 * an apartment is fetched and evaluated at most once per session. */
const definitions=new Map<ApartmentId,Promise<ApartmentDefinition>>()

export function loadApartmentDefinition(id:ApartmentId):Promise<ApartmentDefinition>{
  const cached=definitions.get(id)
  if(cached)return cached
  const request=importers[id]().catch((error)=>{
    definitions.delete(id)
    throw error
  })
  definitions.set(id,request)
  return request
}
