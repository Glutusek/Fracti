<template>
  <div class="trip-calculator-layout">
    <div class="trip-header">
      <h1>Kalkulator transportu</h1>
      <ModeToggle v-model="mode" />
      <div class="trip-load">
        <select
          v-if="savedTrips.length"
          :value="props.tripId ?? ''"
          class="load-select"
          @change="onTripChange"
        >
          <option value="">— Wybierz zapisaną podróż —</option>
          <option v-for="t in savedTrips" :key="t.id" :value="t.id">
            {{ t.name }} ({{ formatDate(t.created_at) }})
          </option>
        </select>
        <button class="new-btn" @click="newTrip">+ Nowa</button>
        <button
          v-if="store.tripId"
          class="del-btn"
          title="Usuń aktualną podróż"
          @click="deleteCurrent"
        >🗑</button>
      </div>
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
import { useRouter } from 'vue-router'
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
import { tripsService, type TripListItem } from '../services/trips.service'

const props = defineProps<{ settlementId: string | null; tripId?: string | null }>()
const store = useTripCalculatorStore()
const router = useRouter()
const mode = ref<'simple' | 'advanced'>('simple')
const savedTrips = ref<TripListItem[]>([])

async function refreshList() {
  try {
    const res = await tripsService.list(props.settlementId ?? undefined)
    savedTrips.value = res.data
  } catch {
    savedTrips.value = []
  }
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('pl-PL', {
      day: '2-digit',
      month: '2-digit',
    })
  } catch {
    return iso
  }
}

async function onTripChange(e: Event) {
  const id = (e.target as HTMLSelectElement).value
  if (!id) return
  router.push(props.settlementId
    ? `/settlements/${props.settlementId}/trip-calculator/${id}`
    : `/trip-calculator/${id}`)
}

function newTrip() {
  store.reset()
  store.clearDraft()
  router.push(props.settlementId
    ? `/settlements/${props.settlementId}/trip-calculator`
    : '/trip-calculator')
}

async function deleteCurrent() {
  if (!store.tripId) return
  if (!confirm(`Usunąć podróż "${store.tripName}"?`)) return
  try {
    await tripsService.delete(store.tripId)
    store.reset()
    store.clearDraft()
    await refreshList()
    router.push(props.settlementId
      ? `/settlements/${props.settlementId}/trip-calculator`
      : '/trip-calculator')
  } catch {
    alert('Nie udało się usunąć podróży.')
  }
}

onMounted(async () => {
  store.settlementId = props.settlementId
  await refreshList()
  if (props.tripId) {
    try {
      await store.loadTripById(props.tripId)
      mode.value = 'advanced'
      return
    } catch {
      store.reset()
      store.settlementId = props.settlementId
      return
    }
  }
  const restored = store.loadDraft(props.settlementId)
  if (!restored) {
    store.reset()
    store.settlementId = props.settlementId
  }
})

watch(() => store.tripId, () => {
  refreshList()
})

watch(() => props.tripId, async (id) => {
  if (id) {
    try {
      await store.loadTripById(id)
      mode.value = 'advanced'
    } catch {
      store.reset()
    }
  } else {
    store.reset()
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
.trip-load {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}
.load-select,
.new-btn,
.del-btn {
  height: 34px;
  box-sizing: border-box;
  border-radius: 6px;
  font-size: 0.85rem;
  line-height: 1;
  display: inline-flex;
  align-items: center;
}
.load-select {
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.12);
  color: #e2e8f0;
  padding: 0 10px;
  max-width: 260px;
}
.load-select:focus { outline: none; border-color: #8b5cf6; }
.new-btn {
  background: rgba(139,92,246,0.15);
  border: 1px solid rgba(139,92,246,0.35);
  color: #8b5cf6;
  padding: 0 12px;
  font-weight: 600;
  cursor: pointer;
}
.new-btn:hover { background: rgba(139,92,246,0.25); }
.del-btn {
  background: transparent;
  border: 1px solid rgba(245,101,101,0.35);
  color: #fc8181;
  padding: 0 9px;
  cursor: pointer;
}
.del-btn:hover { background: rgba(245,101,101,0.15); }
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
