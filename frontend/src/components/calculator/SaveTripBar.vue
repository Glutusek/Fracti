<template>
  <div class="save-bar">
    <button
      class="save-btn"
      :disabled="store.isSaving"
      @click="handleSave"
    >
      <span v-if="store.isSaving">...</span>
      <span v-else>Zapisz</span>
    </button>

    <button
      v-if="settlementId && (store.computeResult || store.livePreview)"
      class="transfer-btn"
      :disabled="store.isSaving"
      @click="handleTransfer"
    >
      Zapisz jako wydatek w rozliczeniu
    </button>

    <div v-if="error" class="error-msg">{{ error }}</div>
    <div v-if="success" class="success-msg">{{ success }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTripCalculatorStore } from '../../stores/tripCalculator'
import { tripsService } from '../../services/trips.service'

const props = defineProps<{ settlementId: string | null }>()
const store = useTripCalculatorStore()
const router = useRouter()
const error = ref<string | null>(null)
const success = ref<string | null>(null)

async function handleSave() {
  error.value = null
  success.value = null
  try {
    await store.saveTrip()
    success.value = 'Zapisano!'
    setTimeout(() => (success.value = null), 2000)
  } catch (e: any) {
    if (e?.response?.data?.error === 'inconsistent_consumption') {
      error.value = 'Nadpisania zużywają więcej paliwa niż globalna średnia pozwala.'
    } else {
      error.value = 'Błąd zapisu. Spróbuj ponownie.'
    }
  }
}

async function handleTransfer() {
  if (!store.tripId) return
  error.value = null
  try {
    await tripsService.transferToSettlement(store.tripId)
    store.clearDraft()
    router.push(`/settlements/${props.settlementId}`)
  } catch {
    error.value = 'Nie udało się zapisać jako wydatek.'
  }
}
</script>

<style scoped>
.save-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: sticky;
  bottom: 0;
  background: #0f1420;
  padding: 12px 0 4px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.save-btn {
  width: 100%;
  background: #8b5cf6;
  color: #fff;
  border: none;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.save-btn:hover:not(:disabled) { background: #7c3aed; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.transfer-btn {
  width: 100%;
  background: rgba(34,197,94,0.12);
  color: #4ade80;
  border: 1px solid rgba(34,197,94,0.3);
  padding: 10px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}
.transfer-btn:hover:not(:disabled) { background: rgba(34,197,94,0.2); }
.error-msg {
  color: #fc8181;
  font-size: 0.8rem;
  text-align: center;
}
.success-msg {
  color: #4ade80;
  font-size: 0.8rem;
  text-align: center;
}
</style>
