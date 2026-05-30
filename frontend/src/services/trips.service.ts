import apiClient from './api'
import type { ComputeResult } from '../types/trip'

export interface TripListItem {
  id: string
  name: string
  trip_date: string | null
  settlement: string | null
  total_cost: string | null
  total_distance_km: string | null
  currency: string
  created_at: string
}

export interface TripDetail {
  id: string
  name: string
  description: string
  settlement: string | null
  trip_date: string | null
  global_consumption_l_per_100km: string
  fuel_price_per_liter: string
  currency: string
  total_tolls: string
  payer: string | null
  stops: any[]
  participants: any[]
  legs: any[]
  other_costs: any[]
  debts: any[]
  total_cost: string | null
  total_distance_km: string | null
  total_fuel_cost: string | null
  total_other_cost: string | null
}

export const tripsService = {
  list(settlementId?: string | null): Promise<{ data: TripListItem[] }> {
    const params = settlementId ? { settlement: settlementId } : {}
    return apiClient.get('/trips/', { params })
  },

  get(id: string): Promise<{ data: TripDetail }> {
    return apiClient.get(`/trips/${id}/`)
  },

  create(payload: { name: string; settlement?: string | null }): Promise<{ data: TripDetail }> {
    return apiClient.post('/trips/', payload)
  },

  bulkUpdate(id: string, payload: Record<string, unknown>): Promise<{ data: TripDetail }> {
    return apiClient.put(`/trips/${id}/`, payload)
  },

  delete(id: string): Promise<void> {
    return apiClient.delete(`/trips/${id}/`)
  },

  compute(id: string): Promise<{ data: ComputeResult }> {
    return apiClient.post(`/trips/${id}/compute/`)
  },

  previewCompute(id: string): Promise<{ data: ComputeResult }> {
    return apiClient.post(`/trips/${id}/preview-compute/`)
  },

  transferToSettlement(id: string): Promise<{ data: { receipt: string } }> {
    return apiClient.post(`/trips/${id}/transfer-to-settlement/`)
  },

  simpleCalculate(
    mode: string,
    params: Record<string, unknown>,
  ): Promise<{ data: Record<string, string> }> {
    return apiClient.post('/trips/calculator/simple/', { mode, ...params })
  },
}
