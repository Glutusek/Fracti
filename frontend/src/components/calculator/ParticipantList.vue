<template>
  <div class="participant-list section-card">
    <div class="section-header">
      <h3>Uczestnicy</h3>
      <div class="header-actions">
        <button v-if="settlementId" class="small-btn" @click="showGuestModal = true">+ Gość</button>
        <button class="small-btn" @click="showManualAdd = !showManualAdd">+ Dodaj</button>
      </div>
    </div>

    <div v-if="showManualAdd" class="manual-add">
      <input v-model="manualName" class="name-input" placeholder="Imię uczestnika..." />
      <button class="add-confirm-btn" @click="addManual">Dodaj</button>
    </div>

    <div v-if="settlementId && settlementMembers.length" class="member-select">
      <select @change="addFromSettlement" class="member-dropdown">
        <option value="">Dodaj z rozliczenia...</option>
        <option v-for="m in availableMembers" :key="m.id" :value="m.id">
          {{ m.first_name || m.username }}
        </option>
      </select>
    </div>

    <div class="participants">
      <div v-for="p in store.participants" :key="p.id" class="participant-row">
        <div class="p-color" :style="{ background: p.color }"></div>
        <div class="p-info">
          <div class="p-name">{{ p.name }}</div>
          <div class="p-stops" v-if="store.stops.length >= 2">
            <template v-if="p.isPayer">
              <span class="driver-label">Cała trasa (kierowca)</span>
            </template>
            <template v-else>
              <select
                :value="p.boardStopId"
                class="stop-select"
                @change="onBoardChange(p, $event)"
              >
                <option
                  v-for="s in boardOptionsFor(p)"
                  :key="s.id"
                  :value="s.id"
                >
                  {{ s.label || `Przystanek ${s.orderIndex + 1}` }}
                </option>
              </select>
              →
              <select
                :value="p.alightStopId"
                class="stop-select"
                @change="onAlightChange(p, $event)"
              >
                <option
                  v-for="s in alightOptionsFor(p)"
                  :key="s.id"
                  :value="s.id"
                >
                  {{ s.label || `Przystanek ${s.orderIndex + 1}` }}
                </option>
              </select>
            </template>
          </div>
        </div>
        <div class="p-actions">
          <button
            :class="['payer-btn', p.isPayer ? 'active' : '']"
            @click="store.setPayer(p.id)"
            title="Ustaw jako płatnika"
          >kierowca</button>
          <button class="remove-btn" @click="store.removeParticipant(p.id)">✕</button>
        </div>
      </div>
      <div v-if="!store.participants.length" class="empty-hint">
        Dodaj uczestników podróży
      </div>
    </div>

    <div v-if="showGuestModal" class="modal-overlay" @click.self="showGuestModal = false">
      <div class="modal-content">
        <h3>Dodaj gościa</h3>
        <input v-model="guestName" class="name-input" placeholder="Imię gościa..." autofocus />
        <div class="modal-actions">
          <button @click="showGuestModal = false">Anuluj</button>
          <button class="primary-btn" @click="addGuest">Dodaj</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTripCalculatorStore } from '../../stores/tripCalculator'
import fractiService from '../../services/receipts.service'
import type { Stop, Participant } from '../../types/trip'

const props = defineProps<{ settlementId: string | null }>()
const store = useTripCalculatorStore()

const showManualAdd = ref(false)
const showGuestModal = ref(false)
const manualName = ref('')
const guestName = ref('')
const settlementMembers = ref<Array<{ id: number; username: string; first_name?: string }>>([])

onMounted(async () => {
  if (props.settlementId) {
    try {
      const settlement = await fractiService.getSettlementDetails(props.settlementId)
      settlementMembers.value = (settlement as any).members ?? []
    } catch {}
  }
})

const availableMembers = computed(() => {
  const usedIds = new Set(store.participants.map((p) => p.userId).filter(Boolean))
  return settlementMembers.value.filter((m) => !usedIds.has(m.id))
})

function addManual() {
  if (!manualName.value.trim()) return
  store.addParticipant(null, manualName.value.trim())
  manualName.value = ''
  showManualAdd.value = false
}

function addFromSettlement(e: Event) {
  const id = parseInt((e.target as HTMLSelectElement).value)
  if (!id) return
  const member = settlementMembers.value.find((m) => m.id === id)
  if (member) store.addParticipant(member.id, member.first_name || member.username)
  ;(e.target as HTMLSelectElement).value = ''
}

function stopIdx(stopId: string): number {
  return store.stops.findIndex((s: Stop) => s.id === stopId)
}

function boardOptionsFor(p: Participant): Stop[] {
  const alightIdx = stopIdx(p.alightStopId)
  if (alightIdx < 0) return store.stops.slice(0, -1)
  return store.stops.slice(0, alightIdx)
}

function alightOptionsFor(p: Participant): Stop[] {
  const boardIdx = stopIdx(p.boardStopId)
  if (boardIdx < 0) return store.stops.slice(1)
  return store.stops.slice(boardIdx + 1)
}

function onBoardChange(p: Participant, e: Event) {
  const newId = (e.target as HTMLSelectElement).value
  p.boardStopId = newId
  const newBoardIdx = stopIdx(newId)
  const alightIdx = stopIdx(p.alightStopId)
  if (alightIdx <= newBoardIdx) {
    p.alightStopId = store.stops[newBoardIdx + 1]?.id ?? store.stops[store.stops.length - 1]?.id ?? ''
  }
}

function onAlightChange(p: Participant, e: Event) {
  const newId = (e.target as HTMLSelectElement).value
  p.alightStopId = newId
  const newAlightIdx = stopIdx(newId)
  const boardIdx = stopIdx(p.boardStopId)
  if (boardIdx >= newAlightIdx) {
    p.boardStopId = store.stops[newAlightIdx - 1]?.id ?? store.stops[0]?.id ?? ''
  }
}

async function addGuest() {
  if (!guestName.value.trim()) return
  if (props.settlementId) {
    try {
      const res = await fractiService.addGuestUser(props.settlementId, guestName.value.trim())
      store.addParticipant(res.id, res.username)
      settlementMembers.value.push({ id: res.id, username: res.username })
    } catch {}
  } else {
    store.addParticipant(null, guestName.value.trim())
  }
  guestName.value = ''
  showGuestModal.value = false
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
.header-actions { display: flex; gap: 6px; }
.small-btn {
  background: rgba(139,92,246,0.15);
  border: 1px solid rgba(139,92,246,0.3);
  color: #8b5cf6;
  padding: 4px 10px;
  border-radius: 5px;
  font-size: 0.78rem;
  cursor: pointer;
}
.small-btn:hover { background: rgba(139,92,246,0.25); }
.manual-add, .member-select {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.name-input {
  flex: 1;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.875rem;
}
.name-input:focus { outline: none; border-color: #8b5cf6; }
.add-confirm-btn {
  background: #8b5cf6;
  border: none;
  color: #fff;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
}
.member-dropdown {
  width: 100%;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.875rem;
}
.participants { display: flex; flex-direction: column; gap: 6px; }
.participant-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #1e2533;
  border-radius: 6px;
  padding: 8px;
}
.p-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 3px;
  flex-shrink: 0;
}
.p-info { flex: 1; min-width: 0; }
.p-name { font-size: 0.875rem; color: #e2e8f0; margin-bottom: 4px; }
.p-stops { display: flex; align-items: center; gap: 4px; }
.driver-label {
  font-size: 0.72rem;
  color: #4ade80;
  font-style: italic;
}
.stop-select {
  background: #0f1420;
  border: 1px solid rgba(255,255,255,0.06);
  color: #a0aec0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.72rem;
  max-width: 110px;
}
.p-actions { display: flex; gap: 4px; align-items: center; }
.payer-btn {
  font-size: 0.68rem;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: #718096;
  cursor: pointer;
}
.payer-btn.active {
  background: rgba(34,197,94,0.15);
  border-color: rgba(34,197,94,0.4);
  color: #4ade80;
}
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
  font-size: 0.8rem;
  text-align: center;
  padding: 8px 0;
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal-content {
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 24px;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.modal-content h3 { margin: 0; color: #e2e8f0; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; }
.modal-actions button {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: #a0aec0;
  cursor: pointer;
}
.primary-btn {
  background: #8b5cf6 !important;
  border-color: #8b5cf6 !important;
  color: #fff !important;
}
</style>
