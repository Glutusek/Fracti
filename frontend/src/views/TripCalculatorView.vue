<template>
  <div class="trip-calculator-layout">
    <div class="trip-header">
      <h1>Kalkulator transportu</h1>
      <ModeToggle v-model="mode" />
    </div>

    <div v-if="mode === 'simple'" class="simple-wrapper">
      <SimpleCalculator />
    </div>

    <div v-else class="advanced-layout">
      <div class="map-panel">
        <RouteMap />
      </div>
      <div class="sidebar-panel">
        <div class="trip-name-row">
          <input
            v-model="store.tripName"
            class="trip-name-input"
            placeholder="Nazwa podróży..."
          />
        </div>

        <StopList />
        <ParticipantList :settlement-id="settlementId" />
        <CostInputs />
        <LegConsumptionTable v-if="store.legs.length > 0" />

        <div v-if="store.inconsistencyError" class="error-banner">
          Twoje nadpisania zużywają więcej paliwa niż globalna średnia pozwala.
          Zwiększ spalanie globalne lub zmniejsz nadpisania.
        </div>

        <ResultTable v-if="store.computeResult || store.livePreview" />
        <SaveTripBar :settlement-id="settlementId" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import ModeToggle from '../components/calculator/ModeToggle.vue'
import SimpleCalculator from '../components/calculator/SimpleCalculator.vue'
import RouteMap from '../components/calculator/RouteMap.vue'
import StopList from '../components/calculator/StopList.vue'
import ParticipantList from '../components/calculator/ParticipantList.vue'
import CostInputs from '../components/calculator/CostInputs.vue'
import LegConsumptionTable from '../components/calculator/LegConsumptionTable.vue'
import ResultTable from '../components/calculator/ResultTable.vue'
import SaveTripBar from '../components/calculator/SaveTripBar.vue'
import { useTripCalculatorStore } from '../stores/tripCalculator'

const props = defineProps<{ settlementId: string | null }>()
const store = useTripCalculatorStore()
const mode = ref<'simple' | 'advanced'>('simple')

onMounted(() => {
  store.settlementId = props.settlementId
  const restored = store.loadDraft(props.settlementId)
  if (!restored) {
    store.reset()
    store.settlementId = props.settlementId
  }
})

watch(() => props.settlementId, (id) => {
  store.settlementId = id
})
</script>

<style scoped>
.trip-calculator-layout {
  min-height: 100vh;
  background: #0f1420;
  color: #e2e8f0;
  padding: 20px;
  box-sizing: border-box;
}
.trip-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.trip-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}
.simple-wrapper {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}
.advanced-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
}
.map-panel {
  flex: 1;
  min-height: 400px;
  border-radius: 12px;
  overflow: hidden;
}
.sidebar-panel {
  width: 380px;
  flex-shrink: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.trip-name-input {
  width: 100%;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 1rem;
  box-sizing: border-box;
}
.trip-name-input:focus {
  outline: none;
  border-color: #8b5cf6;
}
.error-banner {
  background: rgba(245, 101, 101, 0.15);
  border: 1px solid rgba(245, 101, 101, 0.4);
  border-radius: 8px;
  padding: 12px;
  color: #fc8181;
  font-size: 0.875rem;
}

@media (max-width: 1024px) {
  .advanced-layout {
    flex-direction: column;
    height: auto;
  }
  .map-panel {
    height: 50vh;
  }
  .sidebar-panel {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .trip-calculator-layout {
    padding: 12px;
  }
  .map-panel {
    height: 40vh;
  }
}
</style>
