<template>
  <div class="simple-calc">
    <div class="mode-select">
      <label>Tryb kalkulacji</label>
      <select v-model="mode">
        <option value="TRIP_COST">Koszt podróży</option>
        <option value="DISTANCE">Odległość</option>
        <option value="CONSUMPTION_RATE">Spalanie</option>
        <option value="FUEL_NEEDED">Wymagane paliwo</option>
      </select>
    </div>

    <div class="inputs">
      <template v-if="mode === 'TRIP_COST'">
        <CalcInput v-model="distanceKm" label="Dystans (km)" />
        <CalcInput v-model="consumption" label="Spalanie (L/100km)" />
        <CalcInput v-model="pricePerLiter" label="Cena paliwa (zł/L)" />
        <CalcInput v-model="nPersons" label="Liczba osób" :min="1" :step="1" />
      </template>
      <template v-else-if="mode === 'DISTANCE'">
        <CalcInput v-model="liters" label="Paliwo (L)" />
        <CalcInput v-model="consumption" label="Spalanie (L/100km)" />
        <CalcInput v-model="pricePerLiter" label="Cena paliwa (zł/L)" />
      </template>
      <template v-else-if="mode === 'CONSUMPTION_RATE'">
        <CalcInput v-model="distanceKm" label="Dystans (km)" />
        <CalcInput v-model="liters" label="Paliwo (L)" />
        <CalcInput v-model="pricePerLiter" label="Cena paliwa (zł/L)" />
      </template>
      <template v-else-if="mode === 'FUEL_NEEDED'">
        <CalcInput v-model="distanceKm" label="Dystans (km)" />
        <CalcInput v-model="consumption" label="Spalanie (L/100km)" />
        <CalcInput v-model="pricePerLiter" label="Cena paliwa (zł/L)" />
      </template>
    </div>

    <div v-if="result" class="result-box">
      <div v-if="mode === 'TRIP_COST'">
        <div class="result-primary">{{ result.total_cost }} zł</div>
        <div class="result-secondary">{{ result.per_person }} zł / osoba</div>
        <div class="result-secondary">{{ result.fuel_liters }} L paliwa</div>
      </div>
      <div v-else-if="mode === 'DISTANCE'">
        <div class="result-primary">{{ result.distance_km }} km</div>
        <div class="result-secondary">{{ result.distance_miles }} mil</div>
        <div class="result-secondary">Koszt: {{ result.total_cost }} zł</div>
      </div>
      <div v-else-if="mode === 'CONSUMPTION_RATE'">
        <div class="result-primary">{{ result.consumption_l_per_100km }} L/100km</div>
        <div class="result-secondary">Koszt: {{ result.total_cost }} zł</div>
      </div>
      <div v-else-if="mode === 'FUEL_NEEDED'">
        <div class="result-primary">{{ result.fuel_liters }} L</div>
        <div class="result-secondary">Koszt: {{ result.total_cost }} zł</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { computeSimple } from '../../utils/tripCalc'
import CalcInput from './CalcInput.vue'

const mode = ref<'TRIP_COST' | 'DISTANCE' | 'CONSUMPTION_RATE' | 'FUEL_NEEDED'>('TRIP_COST')
const distanceKm = ref(100)
const consumption = ref(7)
const pricePerLiter = ref(6.5)
const nPersons = ref(1)
const liters = ref(10)

const result = computed(() => {
  try {
    return computeSimple(mode.value, {
      distance_km: distanceKm.value,
      consumption: consumption.value,
      price_per_liter: pricePerLiter.value,
      n: nPersons.value,
      liters: liters.value,
    })
  } catch {
    return null
  }
})
</script>

<style scoped>
.simple-calc {
  max-width: 480px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.mode-select label {
  display: block;
  color: #a0aec0;
  font-size: 0.8rem;
  margin-bottom: 4px;
}
.mode-select select {
  width: 100%;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.9rem;
}
.inputs {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.result-box {
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}
.result-primary {
  font-size: 2rem;
  font-weight: 700;
  color: #8b5cf6;
}
.result-secondary {
  color: #a0aec0;
  font-size: 0.9rem;
  margin-top: 4px;
}
</style>
