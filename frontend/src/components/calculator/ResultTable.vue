<template>
  <div v-if="result" class="result-table section-card">
    <div class="section-header">
      <h3>Podział kosztów</h3>
      <div class="totals">
        <span>Razem: <strong>{{ result.total_cost }} zł</strong></span>
        <span class="sep">·</span>
        <span>{{ result.total_distance_km }} km</span>
      </div>
    </div>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Uczestnik</th>
            <th>Paliwo</th>
            <th>Opłaty</th>
            <th>Inne</th>
            <th>Razem</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in shares"
            :key="s.participantId"
            :class="{ 'payer-row': s.isPayer }"
            :style="{ borderLeft: `4px solid ${s.color}` }"
          >
            <td class="p-name">
              <span v-if="s.isPayer" class="driver-icon" title="Kierowca">🚗</span>
              <span :class="{ 'driver-name': s.isPayer }">{{ s.name }}</span>
            </td>
            <td>{{ s.fuel }} zł</td>
            <td>{{ s.tolls }} zł</td>
            <td>{{ s.other }} zł</td>
            <td class="amount-col">{{ s.total }} zł</td>
          </tr>
        </tbody>
      </table>
      <div v-if="payerRow" class="payer-summary">
        {{ payerRow.name }} otrzyma od pozostałych: <strong>{{ payerTotal }} zł</strong>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTripCalculatorStore } from '../../stores/tripCalculator'

const store = useTripCalculatorStore()
const result = computed(() => store.computeResult ?? store.livePreview)

const shares = computed(() => result.value?.participant_shares ?? [])

const payerRow = computed(() =>
  store.participants.find((p) => p.id === store.payerId),
)

const payerTotal = computed(() => {
  if (!result.value) return '0.00'
  return result.value.debts
    .reduce((acc, d) => acc + parseFloat(d.amount), 0)
    .toFixed(2)
})
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
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.section-header h3 {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.totals {
  display: flex;
  gap: 6px;
  font-size: 0.8rem;
  color: #a0aec0;
}
.totals strong { color: #e2e8f0; }
.sep { color: #4a5568; }
.table-wrapper { overflow-x: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}
th {
  color: #718096;
  padding: 4px 8px;
  text-align: right;
  font-weight: 600;
}
th:first-child { text-align: left; }
td {
  padding: 8px;
  text-align: right;
  color: #a0aec0;
  border-top: 1px solid rgba(255,255,255,0.04);
}
td.p-name {
  text-align: left;
  color: #e2e8f0;
  padding-left: 10px;
}
.amount-col {
  font-weight: 600;
  color: #e2e8f0;
}
.payer-row { background: rgba(34,197,94,0.06); }
.driver-icon { margin-right: 6px; font-size: 0.95rem; }
.driver-name { font-weight: 700; color: #f0fdf4; }
.payer-summary {
  margin-top: 10px;
  padding: 8px 10px;
  background: rgba(34,197,94,0.08);
  border: 1px solid rgba(34,197,94,0.3);
  border-radius: 6px;
  color: #4ade80;
  font-size: 0.85rem;
  text-align: center;
}
.payer-summary strong { font-size: 0.95rem; }
</style>
