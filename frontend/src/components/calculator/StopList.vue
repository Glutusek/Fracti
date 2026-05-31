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
      <div v-for="(stop, idx) in store.stops" :key="stop.id" class="stop-wrap">
        <div class="stop-row">
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
              v-if="stop.history?.length"
              class="undo-btn"
              @click="store.undoStopMove(stop.id)"
              :title="`Cofnij przesunięcie (${stop.history.length}/${MAX_UNDO})`"
            >↩<sub class="undo-count">{{ stop.history.length }}</sub></button>
            <button
              class="edit-btn"
              :class="{ active: editingId === stop.id }"
              @click="toggleEdit(stop.id)"
              title="Zmień miejsce (szukaj)"
            >✎</button>
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
        <div v-if="editingId === stop.id" class="stop-edit">
          <StopSearchBox
            placeholder="Szukaj nowego miejsca..."
            @select="onReplaceSelect(stop.id, $event)"
          />
        </div>
      </div>
      <div v-if="!store.stops.length" class="empty-hint">
        Kliknij na mapę lub wyszukaj miejsce, aby dodać przystanek
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import StopSearchBox from './StopSearchBox.vue'
import { useTripCalculatorStore, MAX_UNDO } from '../../stores/tripCalculator'
import type { NominatimResult } from '../../types/trip'
import { formatAddressLabel } from '../../services/nominatim.service'

const store = useTripCalculatorStore()
const editingId = ref<string | null>(null)

function onSearchSelect(result: NominatimResult) {
  const label = formatAddressLabel(result.address, result.display_name.split(',')[0] ?? '')
  store.addStop(parseFloat(result.lat), parseFloat(result.lon), label)
}

function toggleEdit(id: string) {
  editingId.value = editingId.value === id ? null : id
}

function onReplaceSelect(id: string, result: NominatimResult) {
  const label = formatAddressLabel(result.address, result.display_name.split(',')[0] ?? '')
  store.replaceStopLocation(id, parseFloat(result.lat), parseFloat(result.lon), label)
  editingId.value = null
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
.stop-wrap {
  background: #1e2533;
  border-radius: 6px;
}
.stop-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
}
.stop-edit {
  padding: 0 8px 8px;
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
.move-btn, .remove-btn, .undo-btn, .edit-btn {
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
.undo-btn {
  color: #f6ad55;
  font-size: 0.85rem;
}
.undo-btn:hover { color: #f6e05e; }
.undo-count {
  font-size: 0.55rem;
  vertical-align: sub;
}
.edit-btn:hover { color: #8b5cf6; }
.edit-btn.active { color: #8b5cf6; }
.empty-hint {
  color: #4a5568;
  font-size: 0.8rem;
  text-align: center;
  padding: 10px 0;
}
</style>
