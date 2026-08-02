import type { ApartmentDefinition, ApartmentId } from './types'
import { joeyApartment } from './joey'
import { monicaApartment } from './monica'

export const APARTMENTS:Record<ApartmentId,ApartmentDefinition>={
  '19':joeyApartment,
  '20':monicaApartment,
}
