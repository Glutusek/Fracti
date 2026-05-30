import type { Leg } from '../types/trip'

export interface RebalanceResult {
  legs: Leg[]
  error?: string
}

export function rebalanceLegs(
  legs: Leg[],
  globalConsumption: number,
): RebalanceResult {
  if (!legs.length) return { legs }

  const D = legs.reduce((acc, l) => acc + l.distanceKm, 0)
  if (D === 0) return { legs }

  const target = globalConsumption * D

  const overridden = legs.filter((l) => l.override && l.consumptionLper100 !== null)
  const free = legs.filter((l) => !l.override || l.consumptionLper100 === null)

  const fixedSum = overridden.reduce(
    (acc, l) => acc + l.distanceKm * (l.consumptionLper100 ?? globalConsumption),
    0,
  )

  if (!free.length) {
    return {
      legs: legs.map((l) => ({ ...l, consumptionLper100: l.consumptionLper100 })),
    }
  }

  const remaining = target - fixedSum
  if (remaining < 0) {
    return {
      legs,
      error: 'inconsistent_consumption',
    }
  }

  const freeDist = free.reduce((acc, l) => acc + l.distanceKm, 0)
  const newCons = freeDist > 0 ? remaining / freeDist : globalConsumption

  if (newCons < 0) {
    return { legs, error: 'inconsistent_consumption' }
  }

  return {
    legs: legs.map((l) =>
      l.override && l.consumptionLper100 !== null
        ? l
        : { ...l, consumptionLper100: Math.round(newCons * 1000) / 1000 },
    ),
  }
}

export interface ParticipantShare {
  participantId: string
  fuel: number
  tolls: number
  other: number
  total: number
}

export function computeShares(
  legs: Leg[],
  participantIds: string[],
  legParticipants: Record<string, string[]>,
  globalConsumption: number,
  fuelPricePerL: number,
  totalTolls: number,
  otherCosts: { amount: number; splitScope: 'ALL' | 'LEG'; legId?: string; paidByParticipantId?: string }[],
): ParticipantShare[] {
  const fuel: Record<string, number> = {}
  const tolls: Record<string, number> = {}
  const other: Record<string, number> = {}
  participantIds.forEach((id) => {
    fuel[id] = 0
    tolls[id] = 0
    other[id] = 0
  })

  const D = legs.reduce((acc, l) => acc + l.distanceKm, 0)

  for (const leg of legs) {
    const present = legParticipants[leg.id] ?? []
    if (!present.length) continue
    const cons = leg.consumptionLper100 ?? globalConsumption
    const liters = (leg.distanceKm * cons) / 100
    const legFuelCost = liters * fuelPricePerL
    const legTollCost = D > 0 ? (totalTolls * leg.distanceKm) / D : 0
    const n = present.length
    for (const pid of present) {
      if (pid in fuel) {
        fuel[pid] = (fuel[pid] ?? 0) + legFuelCost / n
        tolls[pid] = (tolls[pid] ?? 0) + legTollCost / n
      }
    }
  }

  for (const oc of otherCosts) {
    const pool =
      oc.splitScope === 'ALL'
        ? participantIds
        : (legParticipants[oc.legId ?? ''] ?? participantIds)
    if (!pool.length) continue
    const share = oc.amount / pool.length
    for (const pid of pool) {
      if (pid in other) other[pid] = (other[pid] ?? 0) + share
    }
  }

  return participantIds.map((id) => {
    const f = fuel[id] ?? 0
    const t = tolls[id] ?? 0
    const o = other[id] ?? 0
    return {
      participantId: id,
      fuel: round2(f),
      tolls: round2(t),
      other: round2(o),
      total: round2(f + t + o),
    }
  })
}

function round2(n: number): number {
  return Math.round(n * 100) / 100
}

export function computeSimple(
  mode: 'TRIP_COST' | 'DISTANCE' | 'CONSUMPTION_RATE' | 'FUEL_NEEDED',
  params: Record<string, number>,
): Record<string, number> {
  const { distance_km = 0, consumption = 0, price_per_liter = 0, liters = 0, n = 1 } = params

  if (mode === 'TRIP_COST') {
    const fuel = (consumption / 100) * distance_km
    const cost = fuel * price_per_liter
    return { total_cost: round2(cost), per_person: round2(cost / n), fuel_liters: round2(fuel) }
  }
  if (mode === 'DISTANCE') {
    const dist = consumption > 0 ? liters / (consumption / 100) : 0
    return { distance_km: round2(dist), distance_miles: round2(dist * 0.621371), total_cost: round2(liters * price_per_liter) }
  }
  if (mode === 'CONSUMPTION_RATE') {
    const rate = distance_km > 0 ? (liters / distance_km) * 100 : 0
    return { consumption_l_per_100km: Math.round(rate * 1000) / 1000, total_cost: round2(liters * price_per_liter) }
  }
  if (mode === 'FUEL_NEEDED') {
    const fuel = (consumption / 100) * distance_km
    return { fuel_liters: round2(fuel), total_cost: round2(fuel * price_per_liter) }
  }
  return {}
}
