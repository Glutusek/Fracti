export interface Stop {
  id: string
  lat: number
  lng: number
  label: string
  orderIndex: number
  arrivalEta?: number
}

export interface Participant {
  id: string
  userId?: number | null
  name: string
  isPayer: boolean
  boardStopId: string
  alightStopId: string
  color: string
}

export interface Leg {
  id: string
  fromStopId: string
  toStopId: string
  distanceKm: number
  durationSec: number
  consumptionLper100: number | null
  override: boolean
}

export interface OtherCost {
  id: string
  label: string
  amount: number
  splitScope: 'ALL' | 'LEG'
  legId?: string
  paidByParticipantId?: string
}

export interface Trip {
  id?: string
  name?: string
  settlementId: string | null
  stops: Stop[]
  participants: Participant[]
  legs: Leg[]
  otherCosts: OtherCost[]
  globalConsumption: number
  fuelPricePerL: number
  tolls: number
  payerId: string
}

export interface DebtResult {
  debtor: string
  creditor: string
  debtor_name?: string
  creditor_name?: string
  debtor_color?: string
  creditor_color?: string
  amount: string
  breakdown: { fuel: string; tolls: string; other: string }
}

export interface ComputeResult {
  total_distance_km: string
  total_fuel_cost: string
  total_other_cost: string
  total_cost: string
  debts: DebtResult[]
}

export interface NominatimResult {
  place_id: number
  display_name: string
  lat: string
  lon: string
  address?: Record<string, string>
}
