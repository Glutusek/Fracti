<template>
  <div class="stop-list section-card">
    <div class="section-header">
      <h3>Przystanki</h3>
    </div>

    <StopSearchBox
      placeholder="Dodaj przystanek (szukaj lub kliknij mapę)..."
      @select="onSearchSelect"
    />

    <div class="stops">
      <div v-for="(stop, idx) in store.stops" :key="stop.id" class="stop-row">
        <div class="stop-index">{{ idx + 1 }}</div>
        <div class="stop-label">
          <input
            :value="stop.label"
            class="stop-label-input"
            @input="store.updateStopLabel(stop.id, ($event.target as HTMLInputElement).value)"
          />
          <span class="stop-coords">{{ stop.lat.toFixed(4) }}, {{ stop.lng.toFixed(4) }}</span>
        </div>
        <div class="stop-actions">
          <button
            class="move-btn"
            :disabled="idx === 0"
            @click="store.moveStop(stop.id, -1)"
            title="W górę"
          >▲</button>
          <button
            class="move-btn"
            :disabled="idx === store.stops.length - 1"
            @click="store.moveStop(stop.id, 1)"
            title="W dół"
          >▼</button>
          <button class="remove-btn" @click="store.removeStop(stop.id)" title="Usuń">✕</button>
        </div>
      </div>
      <div v-if="!store.stops.length" class="empty-hint">
        Kliknij na mapę lub wyszukaj miejsce, aby dodać przystanek
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StopSearchBox from './StopSearchBox.vue'
import { useTripCalculatorStore } from '../../stores/tripCalculator'
import type { NominatimResult } from '../../types/trip'
import { formatAddressLabel } from '../../services/nominatim.service'

const store = useTripCalculatorStore()

function onSearchSelect(result: NominatimResult) {
  const label = formatAddressLabel(result.address, result.display_name.split(',')[0] ?? '')
  store.addStop(parseFloat(result.lat), parseFloat(result.lon), label)
}
</script>

<style scoped>
.section-card {
  background: #141926;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 14px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.section-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.stops {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stop-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1e2533;
  border-radius: 6px;
  padding: 6px 8px;
}
.stop-index {
  width: 22px;
  height: 22px;
  background: #8b5cf6;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}
.stop-label {
  flex: 1;
  min-width: 0;
}
.stop-label-input {
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 0.875rem;
  width: 100%;
  outline: none;
  padding: 0;
}
.stop-coords {
  font-size: 0.7rem;
  color: #4a5568;
  display: block;
}
.stop-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.move-btn, .remove-btn {
  background: transparent;
  border: none;
  color: #718096;
  cursor: pointer;
  font-size: 0.7rem;
  padding: 2px 4px;
  line-height: 1;
}
.move-btn:hover:not(:disabled) { color: #8b5cf6; }
.move-btn:disabled { opacity: 0.25; cursor: not-allowed; }
.remove-btn:hover { color: #fc8181; }
.empty-hint {
  color: #4a5568;
  font-size: 0.8rem;
  text-align: center;
  padding: 10px 0;
}
</style>
