<template>
  <div class="leg-table section-card">
    <details>
      <summary class="table-title">Spalanie per odcinek</summary>
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Odcinek</th>
              <th>Dystans</th>
              <th>L/100km</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="leg in store.legs" :key="leg.id">
              <td class="leg-label">
                {{ stopLabel(leg.fromStopId) }} → {{ stopLabel(leg.toStopId) }}
              </td>
              <td class="leg-dist">{{ leg.distanceKm.toFixed(1) }} km</td>
              <td>
                <div class="cons-cell">
                  <input
                    type="number"
                    class="cons-input"
                    :class="{ overridden: leg.override }"
                    :value="leg.consumptionLper100 ?? store.globalConsumption"
                    :placeholder="String(store.globalConsumption)"
                    min="0.1"
                    step="0.1"
                    @input="onInput(leg.id, $event)"
                    @change="onInput(leg.id, $event)"
                  />
                  <button
                    v-if="leg.override"
                    class="reset-btn"
                    title="Przywróć średnią globalną"
                    @click="store.setLegConsumption(leg.id, null)"
                  >✕</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import { useTripCalculatorStore } from '../../stores/tripCalculator'
const store = useTripCalculatorStore()

function stopLabel(stopId: string): string {
  const s = store.stops.find((s) => s.id === stopId)
  return s?.label || `P${(s?.orderIndex ?? 0) + 1}`
}

function onInput(legId: string, e: Event) {
  const val = parseFloat((e.target as HTMLInputElement).value)
  if (isNaN(val) || (e.target as HTMLInputElement).value === '') {
    store.setLegConsumption(legId, null)
  } else {
    store.setLegConsumption(legId, val)
  }
}
</script>

<style scoped>
.section-card {
  background: #141926;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 14px;
}
summary.table-title {
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  color: #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  list-style: none;
  user-select: none;
}
summary.table-title::before {
  content: '▶ ';
  font-size: 0.65rem;
  color: #8b5cf6;
}
details[open] summary.table-title::before {
  content: '▼ ';
}
.table-wrapper {
  overflow-x: auto;
  margin-top: 10px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
th {
  color: #718096;
  padding: 4px 6px;
  text-align: left;
  font-weight: 600;
}
td {
  padding: 5px 6px;
  color: #a0aec0;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.leg-label { color: #e2e8f0; font-size: 0.75rem; }
.leg-dist { color: #718096; white-space: nowrap; }
.cons-input {
  width: 80px;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.06);
  color: #a0aec0;
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 0.8rem;
}
.cons-input.overridden {
  border-color: rgba(139,92,246,0.5);
  color: #c4b5fd;
}
.cons-input:focus { outline: none; border-color: #8b5cf6; }
.cons-cell { display: flex; align-items: center; gap: 4px; }
.reset-btn {
  background: transparent;
  border: none;
  color: #718096;
  cursor: pointer;
  font-size: 0.7rem;
  padding: 2px 4px;
  line-height: 1;
}
.reset-btn:hover { color: #fc8181; }
</style>
