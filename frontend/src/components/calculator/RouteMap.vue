<template>
  <div class="route-map-wrapper">
    <l-map
      :zoom="6"
      :center="[52.0, 19.0]"
      :use-global-leaflet="false"
      style="width: 100%; height: 100%"
      @ready="onMapReady"
    >
      <l-tile-layer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        layer-type="base"
        name="CartoDB Dark Matter"
      />
    </l-map>
    <div v-if="isRouting" class="routing-overlay">
      <div class="routing-spinner"></div>
      <div class="routing-label">Wyznaczanie trasy...</div>
    </div>
    <div v-if="routingError" class="routing-error-toast">
      Nie udało się wyznaczyć trasy. Spróbuj ponownie.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'
import L from 'leaflet'
import { useTripCalculatorStore } from '../../stores/tripCalculator'
import { reverseGeocode } from '../../services/nominatim.service'

const OSRM_URL = 'http://localhost:5000/route/v1/driving'

// Cursor within this many px of a stop marker suppresses the route-split ghost.
const STOP_HIT_RADIUS_SQ = 22 ** 2

const store = useTripCalculatorStore()
const mapNative = ref<L.Map | null>(null)
const isRouting = ref(false)
const routingError = ref(false)
let mouseDownPos: { x: number; y: number } | null = null
let routePolyline: L.Polyline | null = null
let routeAbortCtrl: AbortController | null = null

const stopMarkerLayer = L.layerGroup()
const stopMarkers: Map<string, L.Marker> = new Map()

let routeCoords: L.LatLng[] = []
let routePx: L.Point[] = []
let routePxDirty = true
let legBreaks: number[] = []
let hoverGhost: L.Marker | null = null
let isGhostDragging = false
let currentHoverLeg = -1
let mousemoveRaf = 0
let pendingMouseEvent: L.LeafletMouseEvent | null = null

function invalidateRoutePx() {
  routePxDirty = true
}

function ensureRoutePx() {
  if (!routePxDirty || !mapNative.value) return
  routePx = routeCoords.map((c) => mapNative.value!.latLngToContainerPoint(c))
  routePxDirty = false
}

function makeGhostIcon(): L.DivIcon {
  return L.divIcon({
    className: '',
    html: '<div class="ghost-pin">+</div>',
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  })
}

function hideGhost() {
  if (hoverGhost && mapNative.value) {
    mapNative.value.removeLayer(hoverGhost)
  }
  hoverGhost = null
}

function ensureGhost(latlng: L.LatLng) {
  if (!mapNative.value) return
  if (!hoverGhost) {
    hoverGhost = L.marker(latlng, {
      icon: makeGhostIcon(),
      draggable: true,
      autoPan: false,
      opacity: 0.85,
    })
    hoverGhost.on('dragstart', () => {
      isGhostDragging = true
      mapNative.value?.dragging.disable()
    })
    hoverGhost.on('dragend', async () => {
      mapNative.value?.dragging.enable()
      const pos = hoverGhost!.getLatLng()
      const idx = currentHoverLeg
      isGhostDragging = false
      hideGhost()
      if (idx >= 0) {
        const newId = store.insertStopAfter(idx, pos.lat, pos.lng)
        try {
          const label = await reverseGeocode(pos.lat, pos.lng)
          store.updateStopLabel(newId, label)
        } catch {}
      }
    })
    hoverGhost.addTo(mapNative.value as any)
  } else {
    hoverGhost!.setLatLng(latlng)
  }
}

function nearestOnRoute(
  target: L.LatLng,
): { point: L.LatLng; segIdx: number } | null {
  if (routeCoords.length < 2 || !mapNative.value) return null
  ensureRoutePx()
  const tp = mapNative.value.latLngToContainerPoint(target)
  let bestX = 0,
    bestY = 0,
    bestSeg = 0,
    bestDSq = Infinity
  for (let i = 0; i < routePx.length - 1; i++) {
    const a = routePx[i]!
    const b = routePx[i + 1]!
    const dx = b.x - a.x
    const dy = b.y - a.y
    const len2 = dx * dx + dy * dy
    let t = len2 === 0 ? 0 : ((tp.x - a.x) * dx + (tp.y - a.y) * dy) / len2
    t = Math.max(0, Math.min(1, t))
    const px = a.x + t * dx
    const py = a.y + t * dy
    const ddSq = (px - tp.x) ** 2 + (py - tp.y) ** 2
    if (ddSq < bestDSq) {
      bestDSq = ddSq
      bestX = px
      bestY = py
      bestSeg = i
    }
  }
  if (bestDSq > 900) return null
  return {
    point: mapNative.value.containerPointToLatLng(L.point(bestX, bestY)),
    segIdx: bestSeg,
  }
}

// True if the cursor is close (in screen px) to an existing stop marker, so the
// route-split ghost should yield and let the stop's own drag handler take over.
function nearStopPx(target: L.LatLng): boolean {
  if (!mapNative.value) return false
  const tp = mapNative.value.latLngToContainerPoint(target)
  for (const stop of store.stops) {
    const sp = mapNative.value.latLngToContainerPoint(L.latLng(stop.lat, stop.lng))
    const dSq = (sp.x - tp.x) ** 2 + (sp.y - tp.y) ** 2
    if (dSq < STOP_HIT_RADIUS_SQ) return true
  }
  return false
}

function legFromSegment(segIdx: number): number {
  for (let i = 0; i < legBreaks.length - 1; i++) {
    const next = legBreaks[i + 1] ?? Infinity
    if (segIdx < next) return i
  }
  return Math.max(0, legBreaks.length - 2)
}

function makeStopIcon(
  idx: number,
  boardIds: string[],
  alightIds: string[],
): L.DivIcon {
  const renderBadge = (id: string, kind: 'board' | 'alight') => {
    const p = store.participants.find((pp) => pp.id === id)
    if (!p) return ''
    const cls = kind === 'board' ? 'pax-badge' : 'pax-badge alight'
    const style =
      kind === 'board'
        ? `background:${p.color}`
        : `background:transparent;border:2px solid ${p.color};color:${p.color}`
    return `<span class="${cls}" style="${style}">${p.name.charAt(0).toUpperCase()}</span>`
  }
  const boardHtml = boardIds.slice(0, 3).map((id) => renderBadge(id, 'board')).join('')
  const alightHtml = alightIds.slice(0, 3).map((id) => renderBadge(id, 'alight')).join('')
  const stripHtml =
    `<div class="pax-strip">${boardHtml}</div>` +
    (alightHtml ? `<div class="pax-strip alight-strip">${alightHtml}</div>` : '')
  return L.divIcon({
    className: '',
    html: `<div class="stop-pin"><div class="stop-number">${idx + 1}</div>${stripHtml}</div>`,
    iconSize: [36, 56],
    iconAnchor: [18, 14],
  })
}

function rebuildStopMarkers() {
  if (!mapNative.value) return

  // Remove markers for deleted stops
  const currentIds = new Set(store.stops.map((s) => s.id))
  for (const [id, marker] of stopMarkers) {
    if (!currentIds.has(id)) {
      stopMarkerLayer.removeLayer(marker)
      stopMarkers.delete(id)
    }
  }

  // Add/update markers
  store.stops.forEach((stop, idx) => {
    const boardIds = store.stopParticipantMap[stop.id] ?? []
    const alightIds = store.stopAlightMap[stop.id] ?? []
    const icon = makeStopIcon(idx, boardIds, alightIds)
    const latlng = L.latLng(stop.lat, stop.lng)

    if (stopMarkers.has(stop.id)) {
      const m = stopMarkers.get(stop.id)!
      m.setLatLng(latlng)
      m.setIcon(icon)
    } else {
      const m = L.marker(latlng, { icon, draggable: true, autoPan: false })
      m.on('dragstart', () => {
        mapNative.value?.dragging.disable()
        store.beginStopMove(stop.id)
      })
      m.on('dragend', async () => {
        mapNative.value?.dragging.enable()
        const pos = m.getLatLng()
        store.updateStopLatLng(stop.id, pos.lat, pos.lng)
        updateRoutingWaypoints({ fit: false })
        try {
          const label = await reverseGeocode(pos.lat, pos.lng)
          store.updateStopLabel(stop.id, label)
        } catch {}
      })
      stopMarkerLayer.addLayer(m)
      stopMarkers.set(stop.id, m)
    }
  })
}

function clearRoutePolyline() {
  if (routePolyline && mapNative.value) {
    mapNative.value.removeLayer(routePolyline)
  }
  routePolyline = null
}

async function updateRoutingWaypoints(opts: { fit?: boolean } = { fit: true }) {
  if (!mapNative.value) return

  clearRoutePolyline()
  routeCoords = []
  legBreaks = []
  hideGhost()

  if (store.stops.length < 2) return

  routeAbortCtrl?.abort()
  routeAbortCtrl = new AbortController()

  const coords = store.stops.map((s) => `${s.lng},${s.lat}`).join(';')
  const url = `${OSRM_URL}/${coords}?overview=full&geometries=geojson&steps=false`

  isRouting.value = true
  routingError.value = false

  try {
    const res = await fetch(url, { signal: routeAbortCtrl.signal })
    if (!res.ok) throw new Error(`OSRM ${res.status}`)
    const data = await res.json()
    if (data.code !== 'Ok' || !data.routes?.length) throw new Error(data.code ?? 'no route')

    const mapInst = mapNative.value
    if (!mapInst) return

    const route = data.routes[0]
    const latlngs: [number, number][] = route.geometry.coordinates.map(
      (c: [number, number]) => [c[1], c[0]],
    )

    mapInst.invalidateSize()
    routePolyline = L.polyline(latlngs as L.LatLngExpression[], {
      color: '#8b5cf6',
      weight: 5,
      opacity: 0.85,
      renderer: L.svg(),
    }).addTo(mapInst as any)

    routeCoords = latlngs.map((ll) => L.latLng(ll[0], ll[1]))
    invalidateRoutePx()
    legBreaks = data.waypoints.map((w: any) => {
      const wlat = w.location[1]
      const wlng = w.location[0]
      let bestI = 0
      let bestD = Infinity
      for (let i = 0; i < routeCoords.length; i++) {
        const rc = routeCoords[i]!
        const d = (rc.lat - wlat) ** 2 + (rc.lng - wlng) ** 2
        if (d < bestD) {
          bestD = d
          bestI = i
        }
      }
      return bestI
    })

    if (opts.fit) {
      requestAnimationFrame(() => {
        if (!routePolyline || !mapNative.value) return
        try {
          const b = routePolyline.getBounds()
          if (b.isValid()) {
            mapNative.value.fitBounds(b, { padding: [40, 40] })
          }
        } catch (e) {
          console.warn('fitBounds skipped:', e)
        }
      })
    }

    store.updateLegsFromOsrm({
      legs: route.legs,
      waypoints: data.waypoints.map((w: any) => ({
        latLng: { lat: w.location[1], lng: w.location[0] },
      })),
      coordinates: latlngs.map((ll) => ({ lat: (ll as number[])[0], lng: (ll as number[])[1] })),
    })

    isRouting.value = false
  } catch (err: any) {
    if (err.name === 'AbortError') return
    console.error('Routing error:', err)
    isRouting.value = false
    routingError.value = true
    setTimeout(() => (routingError.value = false), 4000)
  }
}

function onMapReady(map: L.Map) {
  mapNative.value = map
  stopMarkerLayer.addTo(map)

  map.on('mousedown', (e: L.LeafletMouseEvent) => {
    mouseDownPos = { x: e.containerPoint.x, y: e.containerPoint.y }
  })

  map.on('mousemove', (e: L.LeafletMouseEvent) => {
    if (isGhostDragging) return
    pendingMouseEvent = e
    if (mousemoveRaf) return
    mousemoveRaf = requestAnimationFrame(() => {
      mousemoveRaf = 0
      const ev = pendingMouseEvent
      pendingMouseEvent = null
      if (!ev) return
      if (routeCoords.length < 2) {
        hideGhost()
        currentHoverLeg = -1
        return
      }
      const near = nearestOnRoute(ev.latlng)
      if (near && !nearStopPx(ev.latlng)) {
        ensureGhost(near.point)
        currentHoverLeg = legFromSegment(near.segIdx)
      } else {
        hideGhost()
        currentHoverLeg = -1
      }
    })
  })

  map.on('moveend zoomend resize', invalidateRoutePx)

  map.on('click', async (e: L.LeafletMouseEvent) => {
    if (mouseDownPos) {
      const dx = e.containerPoint.x - mouseDownPos.x
      const dy = e.containerPoint.y - mouseDownPos.y
      if (Math.sqrt(dx * dx + dy * dy) > 5) return
    }

    store.addStop(e.latlng.lat, e.latlng.lng)
    const lastStop = store.stops[store.stops.length - 1]
    if (lastStop) {
      try {
        const label = await reverseGeocode(e.latlng.lat, e.latlng.lng)
        store.updateStopLabel(lastStop.id, label)
      } catch {
        // keep default label
      }
    }
    rebuildStopMarkers()
    updateRoutingWaypoints()
  })

  if (store.stops.length > 0) {
    rebuildStopMarkers()
  }
  if (store.stops.length >= 2) {
    requestAnimationFrame(() => updateRoutingWaypoints())
  }
}

watch(
  () => [store.stopParticipantMap, store.stopAlightMap],
  () => rebuildStopMarkers(),
  { deep: true },
)

watch(
  () => store.stops.map((s) => `${s.id}:${s.lat},${s.lng}`).join('|'),
  () => {
    rebuildStopMarkers()
    updateRoutingWaypoints({ fit: false })
  },
)

onBeforeUnmount(() => {
  routeAbortCtrl?.abort()
  if (mousemoveRaf) cancelAnimationFrame(mousemoveRaf)
  clearRoutePolyline()
  hideGhost()
  stopMarkerLayer.clearLayers()
})
</script>

<style>
.stop-pin {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stop-number {
  width: 28px;
  height: 28px;
  background: #8b5cf6;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
  border: 2px solid #fff;
}
.pax-strip {
  display: flex;
  gap: 2px;
  margin-top: 2px;
}
.pax-badge {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  color: #fff;
  font-size: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-sizing: border-box;
}
.pax-badge.alight {
  background: transparent !important;
}
.alight-strip { margin-top: 1px; opacity: 0.95; }
.ghost-pin {
  width: 18px;
  height: 18px;
  background: #fff;
  border: 2px solid #8b5cf6;
  border-radius: 50%;
  color: #8b5cf6;
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 14px;
  text-align: center;
  cursor: grab;
}
.ghost-pin:active { cursor: grabbing; }
</style>

<style scoped>
.route-map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}
.routing-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 500;
}
.routing-label {
  color: #e2e8f0;
  font-size: 0.875rem;
  font-weight: 600;
  background: rgba(15,20,32,0.85);
  padding: 6px 14px;
  border-radius: 6px;
}
.routing-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(139,92,246,0.3);
  border-top-color: #8b5cf6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.routing-error-toast {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #fc8181;
  color: #1a1a2e;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  z-index: 600;
}
</style>
