<template>
  <div class="settlements-container">
    <div class="header">
      <h1>Moje Grupy Rozliczeniowe</h1>
      <button @click="showCreateModal = true" class="create-btn">
        + Nowe rozliczenie
      </button>
    </div>

    <div v-if="loading" class="state-msg">
      <div class="spinner"></div> Ładowanie rozliczeń...
    </div>
    <div v-else-if="error" class="state-msg error">{{ error }}</div>

    <div v-else-if="settlements.length === 0" class="state-msg empty">
      <p>Nie należysz jeszcze do żadnej grupy.</p>
      <p class="hint">Utwórz nową grupę, aby zacząć.</p>
    </div>

    <div v-else class="list-wrapper">
      <div
        v-for="settlement in settlements"
        :key="settlement.id"
        class="settlement-card"
        :class="{ 'is-expanded': expandedSet.has(settlement.id) }"
      >
        <div class="card-main">
          <div class="info-section">
            <h2>{{ settlement.name }}</h2>
            <div class="meta">
              <span class="date">{{ formatDate(settlement.created_at) }}</span>
              <span class="members-pill">👤 {{ settlement.members.length }} os.</span>
            </div>
            <p v-if="settlement.description" class="desc">{{ settlement.description }}</p>
          </div>

          <div class="amount-section">
            <span class="label">Razem:</span>
            <span class="value">{{ formatMoney(settlement.total_expenses) }} zł</span>
          </div>

          <div class="actions-section">
            <button @click.stop="goToMap(settlement.id)" class="btn-map" title="Zobacz na mapie">
              🗺️ Mapa
            </button>

            <button
              @click.stop="toggleExpand(settlement.id)"
              class="btn-expand"
              :class="{ 'rotated': expandedSet.has(settlement.id) }"
            >
              ▼
            </button>
          </div>
        </div>

        <div v-if="expandedSet.has(settlement.id)" class="card-details">
          <div class="details-inner">

            <div v-if="settlement.receipts && settlement.receipts.length > 0" class="sub-section">
              <h4>🧾 Paragony ({{ settlement.receipts.length }})</h4>
              <ul>
                <li v-for="receipt in settlement.receipts" :key="receipt.id">
                  <span class="item-name">{{ receipt.merchant_name }}</span>
                  <span class="item-date">{{ formatDate(receipt.purchase_date) }}</span>
                  <span class="item-price">{{ formatMoney(receipt.total_amount) }} zł</span>
                </li>
              </ul>
            </div>

            <div v-if="settlement.loose_products && settlement.loose_products.length > 0" class="sub-section">
              <h4>🍎 Luźne produkty ({{ settlement.loose_products.length }})</h4>
              <ul>
                <li v-for="product in settlement.loose_products" :key="product.id">
                  <span class="item-name">{{ product.name }}</span>
                  <span class="item-cat">{{ CATEGORY_LABELS[product.category] }}</span>
                  <span class="item-price">{{ formatMoney(product.price) }} zł</span>
                </li>
              </ul>
            </div>

            <div v-if="(!settlement.receipts?.length) && (!settlement.loose_products?.length)" class="no-items">
              Brak wydatków w tym rozliczeniu.
            </div>

          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal-content" @click.stop>
        <h2>Nowe rozliczenie</h2>
        <form @submit.prevent="createSettlement">
          <input v-model="newSettlementName" placeholder="Nazwa (np. Wyjazd w góry)" required />
          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false">Anuluj</button>
            <button type="submit" class="primary">Utwórz</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
// Importujemy Twój serwis API (ten z FractiApiService)
import fractiService, { type Settlement, CATEGORY_LABELS } from '@/services/receipts.service';

const router = useRouter();

// --- STATE ---
const settlements = ref<Settlement[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showCreateModal = ref(false);
const newSettlementName = ref('');

// Przechowujemy ID rozwiniętych kafelków (Set jest szybszy niż Array)
const expandedSet = ref<Set<string>>(new Set());

// --- ACTIONS ---

const loadSettlements = async () => {
  try {
    loading.value = true;
    // Używamy metody z Twojej klasy FractiApiService
    settlements.value = await fractiService.getSettlements();
  } catch (err: any) {
    console.error(err);
    error.value = "Nie udało się załadować listy rozliczeń.";
  } finally {
    loading.value = false;
  }
};

const goToMap = (id: string) => {
  router.push(`/map/${id}`);
};

const toggleExpand = (id: string) => {
  if (expandedSet.value.has(id)) {
    expandedSet.value.delete(id);
  } else {
    expandedSet.value.add(id);
  }
};

const createSettlement = async () => {
  try {
    const newSettlement = await fractiService.createSettlement({ name: newSettlementName.value });
    settlements.value.unshift(newSettlement);
    showCreateModal.value = false;
    newSettlementName.value = '';
  } catch (e) {
    alert('Błąd tworzenia rozliczenia');
  }
};

// --- HELPERS ---

const formatMoney = (val: string | number | undefined) => {
  if (!val) return '0.00';
  return Number(val).toFixed(2);
};

const formatDate = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('pl-PL', {
    day: 'numeric', month: 'short', year: 'numeric'
  });
};

onMounted(() => {
  loadSettlements();
});
</script>

<style scoped>
/* KONTENER GŁÓWNY */
.settlements-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  font-family: 'Inter', sans-serif;
  color: #1f2937;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.create-btn {
  background: #8b5cf6;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}
.create-btn:hover { background: #7c3aed; }

/* LOADING / ERROR STATE */
.state-msg { text-align: center; padding: 3rem; color: #6b7280; }
.state-msg.error { color: #ef4444; }

/* KARTA ROZLICZENIA */
.settlement-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  transition: box-shadow 0.2s, border-color 0.2s;
  overflow: hidden; /* Ważne dla animacji rozwijania */
}

.settlement-card:hover {
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  border-color: #d1d5db;
}

.settlement-card.is-expanded {
  border-color: #8b5cf6;
}

/* GŁÓWNY WIERSZ KARTY */
.card-main {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  background: white;
}

.info-section { flex: 1; }
.info-section h2 { margin: 0 0 0.25rem 0; font-size: 1.1rem; }
.meta { font-size: 0.85rem; color: #6b7280; display: flex; gap: 10px; margin-bottom: 4px; }
.desc { font-size: 0.9rem; color: #4b5563; margin: 0; font-style: italic; }

.amount-section {
  text-align: right;
  padding: 0 1.5rem;
  min-width: 100px;
}
.amount-section .label { display: block; font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; }
.amount-section .value { font-size: 1.2rem; font-weight: 700; color: #111827; }

.actions-section {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  border-left: 1px solid #f3f4f6;
  padding-left: 1rem;
}

/* PRZYCISKI */
.btn-map {
  background: #e0f2fe;
  color: #0284c7;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background 0.2s;
}
.btn-map:hover { background: #bae6fd; }

.btn-expand {
  background: transparent;
  border: 1px solid #e5e7eb;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  color: #6b7280;
  transition: all 0.3s ease;
}
.btn-expand:hover { background: #f9fafb; border-color: #d1d5db; }
.btn-expand.rotated { transform: rotate(180deg); background: #f3f4f6; color: #111827; }

/* ROZWIJANE SZCZEGÓŁY */
.card-details {
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 0.3s ease-out;
}

.details-inner { padding: 1.25rem; }

.sub-section { margin-bottom: 1.5rem; }
.sub-section h4 { margin: 0 0 0.5rem 0; font-size: 0.9rem; text-transform: uppercase; color: #6b7280; letter-spacing: 0.5px; }

.sub-section ul { list-style: none; padding: 0; margin: 0; }
.sub-section li {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.95rem;
}
.sub-section li:last-child { border-bottom: none; }

.item-name { font-weight: 500; }
.item-date, .item-cat { font-size: 0.85rem; color: #9ca3af; margin-right: auto; margin-left: 10px; }
.item-price { font-weight: 600; color: #374151; }

.no-items { font-style: italic; color: #9ca3af; text-align: center; padding: 1rem; }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* PROSTY MODAL */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal-content { background: white; padding: 2rem; border-radius: 12px; width: 400px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
.modal-content input { width: 100%; padding: 10px; margin-bottom: 1rem; border: 1px solid #d1d5db; border-radius: 6px; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.modal-actions button { padding: 8px 16px; cursor: pointer; border-radius: 6px; border: 1px solid #d1d5db; background: white; }
.modal-actions button.primary { background: #8b5cf6; color: white; border: none; }
</style>