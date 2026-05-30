<template>
  <div class="cost-inputs section-card">
    <div class="section-header">
      <h3>Koszty</h3>
    </div>

    <div class="input-grid">
      <div class="input-field">
        <label>Spalanie (L/100km)</label>
        <input
          type="number"
          :value="store.globalConsumption"
          min="0.1"
          step="0.1"
          @input="store.setGlobalConsumption(parseFloat(($event.target as HTMLInputElement).value) || 0)"
        />
      </div>
      <div class="input-field">
        <label>Cena paliwa (zł/L)</label>
        <input
          type="number"
          v-model.number="store.fuelPricePerL"
          min="0.01"
          step="0.01"
        />
      </div>
      <div class="input-field">
        <label>Opłaty drogowe (zł)</label>
        <input
          type="number"
          v-model.number="store.tolls"
          min="0"
          step="0.5"
        />
      </div>
    </div>

    <div class="other-costs">
      <div class="other-header">
        <span class="other-title">Opłaty dodatkowe</span>
        <button class="small-btn" @click="store.addOtherCost()">+ Dodaj</button>
      </div>
      <div v-for="oc in store.otherCosts" :key="oc.id" class="other-row">
        <input
          :value="oc.label"
          class="oc-label"
          placeholder="Opis (parking, prom...)"
          @input="oc.label = ($event.target as HTMLInputElement).value"
        />
        <input
          type="number"
          :value="oc.amount"
          class="oc-amount"
          min="0"
          step="0.5"
          @input="oc.amount = parseFloat(($event.target as HTMLInputElement).value) || 0"
        />
        <select
          :value="oc.splitScope"
          class="oc-scope"
          @change="onScopeChange(oc, $event)"
        >
          <option value="ALL">Cała trasa</option>
          <option value="LEG">Odcinek</option>
        </select>
        <select
          v-if="oc.splitScope === 'LEG'"
          :value="oc.legId ?? ''"
          class="oc-leg"
          @change="oc.legId = ($event.target as HTMLSelectElement).value"
        >
          <option value="" disabled>— wybierz odcinek —</option>
          <option v-for="(leg, i) in store.legs" :key="leg.id" :value="leg.id">
            {{ Number(i) + 1 }}. {{ stopLabel(leg.fromStopId) }} → {{ stopLabel(leg.toStopId) }}
          </option>
        </select>
        <button class="remove-btn" @click="store.removeOtherCost(oc.id)">✕</button>
      </div>
      <div v-if="!store.otherCosts.length" class="empty-hint">
        Brak opłat dodatkowych
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useTripCalculatorStore } from '../../stores/tripCalculator'
import type { OtherCost } from '../../types/trip'
const store = useTripCalculatorStore()

function onScopeChange(oc: OtherCost, e: Event) {
  const v = (e.target as HTMLSelectElement).value as 'ALL' | 'LEG'
  oc.splitScope = v
  if (v === 'LEG' && !oc.legId && store.legs.length) {
    oc.legId = store.legs[0]!.id
  }
}

function stopLabel(stopId: string): string {
  const s = store.stops.find((ss) => ss.id === stopId)
  return s?.label || `P${(s?.orderIndex ?? 0) + 1}`
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
.input-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}
.input-grid .input-field:last-child {
  grid-column: 1 / -1;
}
.input-field label {
  display: block;
  color: #a0aec0;
  font-size: 0.75rem;
  margin-bottom: 3px;
}
.input-field input {
  width: 100%;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.875rem;
  box-sizing: border-box;
}
.input-field input:focus { outline: none; border-color: #8b5cf6; }
.other-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.other-title {
  color: #a0aec0;
  font-size: 0.8rem;
  font-weight: 600;
}
.small-btn {
  background: rgba(139,92,246,0.15);
  border: 1px solid rgba(139,92,246,0.3);
  color: #8b5cf6;
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  cursor: pointer;
}
.other-row {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
  align-items: center;
}
.oc-label {
  flex: 1;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.06);
  color: #e2e8f0;
  padding: 5px 8px;
  border-radius: 5px;
  font-size: 0.8rem;
}
.oc-amount {
  width: 80px;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.06);
  color: #e2e8f0;
  padding: 5px 8px;
  border-radius: 5px;
  font-size: 0.8rem;
}
.oc-scope, .oc-leg {
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.06);
  color: #a0aec0;
  padding: 5px 6px;
  border-radius: 5px;
  font-size: 0.75rem;
}
.oc-leg { max-width: 160px; }
.other-row { flex-wrap: wrap; }
.remove-btn {
  background: transparent;
  border: none;
  color: #718096;
  cursor: pointer;
  font-size: 0.75rem;
}
.remove-btn:hover { color: #fc8181; }
.empty-hint {
  color: #4a5568;
  font-size: 0.78rem;
  text-align: center;
  padding: 6px 0;
}
</style>
