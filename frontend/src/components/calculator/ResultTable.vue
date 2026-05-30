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
            v-for="debt in result.debts"
            :key="debt.debtor"
            :style="{ borderLeft: `4px solid ${debt.debtor_color || colorFor(debt.debtor)}` }"
          >
            <td class="p-name">{{ debt.debtor_name || nameFor(debt.debtor) }}</td>
            <td>{{ debt.breakdown.fuel }} zł</td>
            <td>{{ debt.breakdown.tolls }} zł</td>
            <td>{{ debt.breakdown.other }} zł</td>
            <td class="amount-col">{{ debt.amount }} zł</td>
          </tr>
          <tr v-if="payerRow" class="payer-row">
            <td class="p-name">{{ payerRow.name }} (płatnik)</td>
            <td colspan="3"></td>
            <td class="amount-col payer-amount">Otrzymuje: {{ payerTotal }} zł</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTripCalculatorStore } from '../../stores/tripCalculator'

const store = useTripCalculatorStore()
const result = computed(() => store.computeResult ?? store.livePreview)

function colorFor(participantId: string): string {
  return store.participants.find((p) => p.id === participantId)?.color ?? '#8b5cf6'
}

function nameFor(participantId: string): string {
  return store.participants.find((p) => p.id === participantId)?.name ?? participantId
}

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
.payer-amount { color: #4ade80; }
</style>
