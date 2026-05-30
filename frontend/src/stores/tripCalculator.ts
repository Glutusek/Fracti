import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Stop, Participant, Leg, OtherCost, ComputeResult } from '../types/trip'
import { rebalanceLegs, computeShares } from '../utils/tripCalc'
import { tripsService } from '../services/trips.service'

const PALETTE = [
  '#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6',
  '#ef4444', '#8b5cf6', '#14b8a6', '#f97316', '#84cc16',
]

function genId() {
  return crypto.randomUUID()
}

function nextColor(existing: string[]): string {
  const used = new Set(existing)
  return PALETTE.find((c) => !used.has(c)) ?? PALETTE[0] ?? '#8b5cf6'
}

export const useTripCalculatorStore = defineStore('tripCalculator', () => {
  const tripId = ref<string | null>(null)
  const settlementId = ref<string | null>(null)
  const tripName = ref('Nowa podróż')
  const globalConsumption = ref(7)
  const fuelPricePerL = ref(6.5)
  const tolls = ref(0)
  const stops = ref<Stop[]>([])
  const participants = ref<Participant[]>([])
  const legs = ref<Leg[]>([])
  const otherCosts = ref<OtherCost[]>([])
  const payerId = ref<string>('')
  const computeResult = ref<ComputeResult | null>(null)
  const isSaving = ref(false)
  const isComputing = ref(false)
  const inconsistencyError = ref<string | null>(null)

  const legParticipantMap = computed(() => {
    const map: Record<string, string[]> = {}
    for (const p of participants.value) {
      const boardIdx = stops.value.findIndex((s) => s.id === p.boardStopId)
      const alightIdx = stops.value.findIndex((s) => s.id === p.alightStopId)
      for (const leg of legs.value) {
        const fromIdx = stops.value.findIndex((s) => s.id === leg.fromStopId)
        if (fromIdx >= boardIdx && fromIdx < alightIdx) {
          if (!map[leg.id]) map[leg.id] = []
          map[leg.id]!.push(p.id)
        }
      }
    }
    return map
  })

  const livePreview = computed<ComputeResult | null>(() => {
    if (participants.value.length < 1 || legs.value.length < 1) return null
    const pids = participants.value.map((p) => p.id)
    const shares = computeShares(
      legs.value,
      pids,
      legParticipantMap.value,
      globalConsumption.value,
      fuelPricePerL.value,
      tolls.value,
      otherCosts.value.map((oc) => ({
        amount: oc.amount,
        splitScope: oc.splitScope,
        legId: oc.legId,
        paidByParticipantId: oc.paidByParticipantId,
      })),
    )
    const totalDist = legs.value.reduce((a, l) => a + l.distanceKm, 0)
    const totalFuel = legs.value.reduce((a, l) => {
      const cons = l.consumptionLper100 ?? globalConsumption.value
      return a + (l.distanceKm * cons / 100) * fuelPricePerL.value
    }, 0)
    const totalOther = otherCosts.value.reduce((a, oc) => a + oc.amount, 0)
    const totalCost = totalFuel + tolls.value + totalOther

    const payer = participants.value.find((p) => p.id === payerId.value)
    const debts = shares
      .filter((s) => s.participantId !== payerId.value && s.total > 0)
      .map((s) => {
        const p = participants.value.find((pp) => pp.id === s.participantId)
        return {
          debtor: s.participantId,
          creditor: payerId.value,
          debtor_name: p?.name || s.participantId,
          creditor_name: payer?.name || payerId.value,
          debtor_color: p?.color || '',
          creditor_color: payer?.color || '',
          amount: s.total.toFixed(2),
          breakdown: {
            fuel: s.fuel.toFixed(2),
            tolls: s.tolls.toFixed(2),
            other: s.other.toFixed(2),
          },
        }
      })

    return {
      total_distance_km: totalDist.toFixed(3),
      total_fuel_cost: totalFuel.toFixed(2),
      total_other_cost: totalOther.toFixed(2),
      total_cost: totalCost.toFixed(2),
      debts,
    }
  })

  const stopParticipantMap = computed(() => {
    const map: Record<string, string[]> = {}
    const firstId = stops.value[0]?.id
    for (const p of participants.value) {
      if (p.boardStopId && p.boardStopId !== firstId) {
        if (!map[p.boardStopId]) map[p.boardStopId] = []
        map[p.boardStopId]!.push(p.id)
      }
    }
    if (firstId) {
      map[firstId] = participants.value
        .filter((p) => p.boardStopId === firstId)
        .map((p) => p.id)
    }
    return map
  })

  const stopAlightMap = computed(() => {
    const map: Record<string, string[]> = {}
    const lastId = stops.value[stops.value.length - 1]?.id
    for (const p of participants.value) {
      if (p.alightStopId && p.alightStopId !== lastId) {
        if (!map[p.alightStopId]) map[p.alightStopId] = []
        map[p.alightStopId]!.push(p.id)
      }
    }
    return map
  })

  function rebuildLegs(newStops: Stop[], preserveOverrides: Record<string, Leg>) {
    const result: Leg[] = []
    for (let i = 0; i < newStops.length - 1; i++) {
      const from = newStops[i]!
      const to = newStops[i + 1]!
      const key = `${from.id}-${to.id}`
      const existing = preserveOverrides[key]
      result.push(
        existing ?? {
          id: genId(),
          fromStopId: from.id,
          toStopId: to.id,
          distanceKm: 0,
          durationSec: 0,
          consumptionLper100: null,
          override: false,
        },
      )
    }
    return result
  }

  function addStop(lat: number, lng: number, label = 'Punkt') {
    const prevLastId = stops.value[stops.value.length - 1]?.id
    const stop: Stop = {
      id: genId(),
      lat,
      lng,
      label,
      orderIndex: stops.value.length,
    }
    stops.value.push(stop)
    if (prevLastId) {
      for (const p of participants.value) {
        if (p.alightStopId === prevLastId) {
          p.alightStopId = stop.id
        }
      }
    }
    _syncLegs()
  }

  function insertStopAfter(prevIdx: number, lat: number, lng: number, label = 'Punkt') {
    const stop: Stop = { id: genId(), lat, lng, label, orderIndex: 0 }
    stops.value.splice(prevIdx + 1, 0, stop)
    stops.value.forEach((s, i) => (s.orderIndex = i))
    _syncLegs()
    return stop.id
  }

  function moveStop(stopId: string, direction: -1 | 1) {
    const idx = stops.value.findIndex((s) => s.id === stopId)
    if (idx === -1) return
    const newIdx = idx + direction
    if (newIdx < 0 || newIdx >= stops.value.length) return
    const arr = [...stops.value]
    ;[arr[idx], arr[newIdx]] = [arr[newIdx]!, arr[idx]!]
    stops.value = arr.map((s, i) => ({ ...s, orderIndex: i }))
    _syncLegs()
  }

  function removeStop(stopId: string) {
    const idx = stops.value.findIndex((s) => s.id === stopId)
    if (idx === -1) return
    stops.value.splice(idx, 1)
    stops.value.forEach((s, i) => (s.orderIndex = i))
    for (const p of participants.value) {
      if (p.boardStopId === stopId) p.boardStopId = stops.value[0]?.id ?? ''
      if (p.alightStopId === stopId)
        p.alightStopId = stops.value[stops.value.length - 1]?.id ?? ''
    }
    _syncLegs()
  }

  function updateStopLatLng(stopId: string, lat: number, lng: number) {
    const s = stops.value.find((s) => s.id === stopId)
    if (s) { s.lat = lat; s.lng = lng }
  }

  function updateStopLabel(stopId: string, label: string) {
    const s = stops.value.find((s) => s.id === stopId)
    if (s) s.label = label
  }

  function reorderStops(newOrder: Stop[]) {
    stops.value = newOrder.map((s, i) => ({ ...s, orderIndex: i }))
    _syncLegs()
  }

  function _syncLegs() {
    const overrideMap: Record<string, Leg> = {}
    for (const l of legs.value) {
      overrideMap[`${l.fromStopId}-${l.toStopId}`] = l
    }
    legs.value = rebuildLegs(stops.value, overrideMap)
    enforcePayerCoverage()
    _rebalance()
  }

  function _rebalance() {
    const result = rebalanceLegs(legs.value, globalConsumption.value)
    if (result.error) {
      inconsistencyError.value = result.error
    } else {
      inconsistencyError.value = null
      legs.value = result.legs
    }
  }

  function setGlobalConsumption(val: number) {
    globalConsumption.value = val
    for (const l of legs.value) {
      if (!l.override) l.consumptionLper100 = null
    }
    _rebalance()
  }

  function setLegConsumption(legId: string, val: number | null) {
    const leg = legs.value.find((l) => l.id === legId)
    if (!leg) return
    if (val === null) {
      leg.consumptionLper100 = null
      leg.override = false
    } else {
      leg.consumptionLper100 = val
      leg.override = true
    }
    _rebalance()
  }

  function addParticipant(userId?: number | null, name?: string, color?: string) {
    const id = genId()
    const c = color ?? nextColor(participants.value.map((p) => p.color))
    participants.value.push({
      id,
      userId: userId ?? null,
      name: name ?? '',
      isPayer: participants.value.length === 0,
      boardStopId: stops.value[0]?.id ?? '',
      alightStopId: stops.value[stops.value.length - 1]?.id ?? '',
      color: c,
    })
    if (participants.value.length === 1) payerId.value = id
  }

  function removeParticipant(id: string) {
    const idx = participants.value.findIndex((p) => p.id === id)
    if (idx === -1) return
    participants.value.splice(idx, 1)
    if (payerId.value === id && participants.value.length > 0) {
      setPayer(participants.value[0]!.id)
    }
  }

  function setPayer(id: string) {
    payerId.value = id
    const firstId = stops.value[0]?.id ?? ''
    const lastId = stops.value[stops.value.length - 1]?.id ?? ''
    for (const p of participants.value) {
      p.isPayer = p.id === id
      if (p.isPayer) {
        p.boardStopId = firstId
        p.alightStopId = lastId
      }
    }
  }

  function enforcePayerCoverage() {
    const payer = participants.value.find((p) => p.id === payerId.value)
    if (!payer) return
    payer.boardStopId = stops.value[0]?.id ?? ''
    payer.alightStopId = stops.value[stops.value.length - 1]?.id ?? ''
  }

  function addOtherCost(label = '', amount = 0, splitScope: 'ALL' | 'LEG' = 'ALL') {
    otherCosts.value.push({ id: genId(), label, amount, splitScope })
  }

  function removeOtherCost(id: string) {
    const idx = otherCosts.value.findIndex((c) => c.id === id)
    if (idx !== -1) otherCosts.value.splice(idx, 1)
  }

  function updateLegsFromOsrm(route: any) {
    if (route.legs) {
      for (let i = 0; i < route.legs.length; i++) {
        const leg = legs.value[i]
        if (!leg) continue
        leg.distanceKm = Math.round((route.legs[i].distance / 1000) * 1000) / 1000
        leg.durationSec = route.legs[i].duration ?? 0
        if (!leg.override) leg.consumptionLper100 = null
      }
      _rebalance()
    }
  }

  function syncWaypointsFromLRM(waypoints: Array<{ latLng: { lat: number; lng: number } | null }>) {
    waypoints.forEach((wp, i) => {
      if (stops.value[i] && wp.latLng) {
        stops.value[i].lat = wp.latLng.lat
        stops.value[i].lng = wp.latLng.lng
      }
    })
  }

  function buildBulkPayload() {
    const stopsPayload = stops.value.map((s) => ({
      order: s.orderIndex,
      name: s.label,
      latitude: s.lat,
      longitude: s.lng,
    }))
    const participantsPayload = participants.value.map((p) => ({
      user: p.userId ?? null,
      guest_label: p.userId ? '' : p.name,
      color: p.color,
    }))
    const payerIndex = participants.value.findIndex((p) => p.id === payerId.value)
    const legsPayload = legs.value.map((l, i) => {
      const fromIdx = stops.value.findIndex((s) => s.id === l.fromStopId)
      const toIdx = stops.value.findIndex((s) => s.id === l.toStopId)
      const participantIndices = (legParticipantMap.value[l.id] ?? []).map((pid) =>
        participants.value.findIndex((p) => p.id === pid),
      )
      return {
        order: i,
        from_stop_index: fromIdx,
        to_stop_index: toIdx,
        distance_km: l.distanceKm,
        duration_seconds: l.durationSec,
        consumption_l_per_100km: l.consumptionLper100 ?? globalConsumption.value,
        consumption_override: l.override,
        participant_indices: participantIndices,
      }
    })
    const otherCostsPayload = otherCosts.value.map((c) => {
      const legOrder =
        c.splitScope === 'LEG' && c.legId
          ? legs.value.findIndex((l) => l.id === c.legId)
          : null
      return {
        label: c.label,
        amount: c.amount,
        split_scope: c.splitScope,
        leg_order: legOrder !== null && legOrder >= 0 ? legOrder : null,
      }
    })

    return {
      name: tripName.value,
      settlement: settlementId.value ?? null,
      global_consumption_l_per_100km: globalConsumption.value,
      fuel_price_per_liter: fuelPricePerL.value,
      total_tolls: tolls.value,
      payer_index: payerIndex >= 0 ? payerIndex : null,
      stops: stopsPayload,
      participants: participantsPayload,
      legs: legsPayload,
      other_costs: otherCostsPayload,
    }
  }

  async function saveTrip() {
    isSaving.value = true
    try {
      const payload = buildBulkPayload()
      if (!tripId.value) {
        const res = await tripsService.create({ name: tripName.value, settlement: settlementId.value })
        tripId.value = res.data.id
      }
      await tripsService.bulkUpdate(tripId.value, payload)
      _saveDraft()
    } finally {
      isSaving.value = false
    }
  }

  async function compute(): Promise<ComputeResult | null> {
    if (!tripId.value) return null
    isComputing.value = true
    try {
      const res = await tripsService.previewCompute(tripId.value)
      computeResult.value = res.data
      return res.data
    } finally {
      isComputing.value = false
    }
  }

  function initFromSettlement(id: string, members: Array<{ id: number; username: string; first_name?: string }>) {
    settlementId.value = id
    participants.value = []
    for (const m of members) {
      addParticipant(m.id, m.first_name || m.username)
    }
  }

  function _saveDraft() {
    const key = `trip-calc-draft-${settlementId.value ?? 'standalone'}`
    localStorage.setItem(key, JSON.stringify({
      tripId: tripId.value,
      tripName: tripName.value,
      globalConsumption: globalConsumption.value,
      fuelPricePerL: fuelPricePerL.value,
      tolls: tolls.value,
      stops: stops.value,
      participants: participants.value,
      legs: legs.value,
      otherCosts: otherCosts.value,
      payerId: payerId.value,
    }))
  }

  function loadDraft(sId: string | null) {
    const key = `trip-calc-draft-${sId ?? 'standalone'}`
    const raw = localStorage.getItem(key)
    if (!raw) return false
    try {
      const d = JSON.parse(raw)
      tripId.value = d.tripId ?? null
      tripName.value = d.tripName ?? 'Nowa podróż'
      globalConsumption.value = d.globalConsumption ?? 7
      fuelPricePerL.value = d.fuelPricePerL ?? 6.5
      tolls.value = d.tolls ?? 0
      stops.value = d.stops ?? []
      participants.value = d.participants ?? []
      legs.value = d.legs ?? []
      otherCosts.value = d.otherCosts ?? []
      payerId.value = d.payerId ?? ''
      return true
    } catch {
      return false
    }
  }

  function clearDraft() {
    const key = `trip-calc-draft-${settlementId.value ?? 'standalone'}`
    localStorage.removeItem(key)
  }

  async function loadTripById(id: string) {
    const res = await tripsService.get(id)
    const t = res.data
    reset()
    tripId.value = t.id
    tripName.value = t.name
    settlementId.value = t.settlement
    globalConsumption.value = parseFloat(t.global_consumption_l_per_100km)
    fuelPricePerL.value = parseFloat(t.fuel_price_per_liter)
    tolls.value = parseFloat(t.total_tolls)

    const stopIdMap: Record<string, string> = {}
    stops.value = t.stops
      .sort((a: any, b: any) => a.order - b.order)
      .map((s: any, i: number) => {
        const localId = genId()
        stopIdMap[s.id] = localId
        return {
          id: localId,
          lat: s.latitude,
          lng: s.longitude,
          label: s.name || 'Punkt',
          orderIndex: i,
        }
      })

    const participantIdMap: Record<string, string> = {}
    participants.value = t.participants.map((p: any) => {
      const localId = genId()
      participantIdMap[p.id] = localId
      return {
        id: localId,
        userId: p.user ?? null,
        name: p.display_name || p.guest_label || '',
        isPayer: t.payer === p.id,
        boardStopId: stops.value[0]?.id ?? '',
        alightStopId: stops.value[stops.value.length - 1]?.id ?? '',
        color: p.color || nextColor([]),
      }
    })
    if (t.payer && participantIdMap[t.payer]) {
      payerId.value = participantIdMap[t.payer]!
    } else if (participants.value.length) {
      payerId.value = participants.value[0]!.id
    }

    legs.value = t.legs
      .sort((a: any, b: any) => a.order - b.order)
      .map((lg: any) => ({
        id: genId(),
        fromStopId: stopIdMap[lg.from_stop] ?? '',
        toStopId: stopIdMap[lg.to_stop] ?? '',
        distanceKm: parseFloat(lg.distance_km),
        durationSec: lg.duration_seconds,
        consumptionLper100: lg.consumption_override
          ? parseFloat(lg.consumption_l_per_100km)
          : null,
        override: lg.consumption_override,
      }))

    for (const p of t.participants) {
      const localPid = participantIdMap[p.id]
      if (!localPid) continue
      const part = participants.value.find((pp) => pp.id === localPid)
      if (!part) continue
      let firstLegIdx = -1
      let lastLegIdx = -1
      t.legs.forEach((lg: any, i: number) => {
        if (lg.participants?.some((lp: any) => lp.id === p.id)) {
          if (firstLegIdx === -1) firstLegIdx = i
          lastLegIdx = i
        }
      })
      if (firstLegIdx >= 0) {
        const sortedLegs = [...t.legs].sort((a: any, b: any) => a.order - b.order)
        const fromStop = sortedLegs[firstLegIdx]?.from_stop
        const toStop = sortedLegs[lastLegIdx]?.to_stop
        if (fromStop && stopIdMap[fromStop]) part.boardStopId = stopIdMap[fromStop]
        if (toStop && stopIdMap[toStop]) part.alightStopId = stopIdMap[toStop]
      }
    }

    otherCosts.value = t.other_costs.map((oc: any) => ({
      id: genId(),
      label: oc.label,
      amount: parseFloat(oc.amount),
      splitScope: oc.split_scope,
      legId: undefined,
    }))
  }

  function hasDraft(sId?: string | null): boolean {
    if (sId !== undefined) {
      const key = `trip-calc-draft-${sId ?? 'standalone'}`
      return !!localStorage.getItem(key)
    }
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)
      if (k && k.startsWith('trip-calc-draft-')) return true
    }
    return false
  }

  function reset() {
    tripId.value = null
    tripName.value = 'Nowa podróż'
    globalConsumption.value = 7
    fuelPricePerL.value = 6.5
    tolls.value = 0
    stops.value = []
    participants.value = []
    legs.value = []
    otherCosts.value = []
    payerId.value = ''
    computeResult.value = null
    inconsistencyError.value = null
  }

  return {
    tripId,
    settlementId,
    tripName,
    globalConsumption,
    fuelPricePerL,
    tolls,
    stops,
    participants,
    legs,
    otherCosts,
    payerId,
    computeResult,
    isSaving,
    isComputing,
    inconsistencyError,
    legParticipantMap,
    stopParticipantMap,
    stopAlightMap,
    livePreview,
    addStop,
    insertStopAfter,
    moveStop,
    removeStop,
    updateStopLatLng,
    updateStopLabel,
    reorderStops,
    setGlobalConsumption,
    setLegConsumption,
    addParticipant,
    removeParticipant,
    setPayer,
    addOtherCost,
    removeOtherCost,
    updateLegsFromOsrm,
    syncWaypointsFromLRM,
    saveTrip,
    compute,
    initFromSettlement,
    loadDraft,
    clearDraft,
    loadTripById,
    hasDraft,
    reset,
  }
})
