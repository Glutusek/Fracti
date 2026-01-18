<template>
  <div class="settlements-container">
    <div class="header">
      <h1>Moje Grupy Rozliczeniowe</h1>
      <div class="header-actions">
        <button @click="showJoinModal = true" class="join-btn">
          🔗 Dołącz do rozliczenia
        </button>
        <button @click="goToOCR" class="ocr-btn">
          📸 Skanuj paragon
        </button>
        <button @click="showCreateModal = true" class="create-btn">
          + Nowe rozliczenie
        </button>
      </div>
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
            <button @click.stop="goToDetails(settlement.id)" class="btn-details" title="Zobacz szczegóły">
              📋 Szczegóły
            </button>

            <button @click.stop="goToMap(settlement.id)" class="btn-map" title="Zobacz na mapie">
              🗺️ Mapa
            </button>

            <button @click.stop="openEditModal(settlement)" class="btn-edit" title="Ustawienia grupy">
              ⚙️
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
                  <span class="item-date">{{ formatDate(product.created_at) }}</span>
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
          <input v-model="newSettlementDescription" placeholder="Opis (opcjonalnie)" />
          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false">Anuluj</button>
            <button type="submit" class="primary">Utwórz</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showJoinModal" class="modal-overlay" @click="showJoinModal = false">
      <div class="modal-content" @click.stop>
        <h2>Dołącz do rozliczenia</h2>
        <form @submit.prevent="joinSettlement">
          <input v-model="joinCode" placeholder="Wpisz kod zaproszenia" required />
          <div class="modal-actions">
            <button type="button" @click="showJoinModal = false">Anuluj</button>
            <button type="submit" class="primary">Dołącz</button>
          </div>
        </form>
      </div>
    </div>

  </div>
  <div v-if="showEditModal" class="modal-overlay" @click="showEditModal = false">
  <div class="modal-content" @click.stop>
    <h2>Edytuj Rozliczenie</h2>
    <form @submit.prevent="updateSettlement">
      <div class="form-group">
        <label>Nazwa</label>
        <input v-model="editingSettlement.name" required />
      </div>
      <div class="form-group">
        <label>Opis</label>
        <input v-model="editingSettlement.description" placeholder="Krótki opis" />
      </div>

      <div class="modal-actions space-between">
        <button type="button" class="danger-btn" @click="confirmDeleteSettlement">
          🗑️ Usuń grupę
        </button>
        <div class="right-actions">
          <button type="button" @click="showEditModal = false">Anuluj</button>
          <button type="submit" class="primary">Zapisz</button>
        </div>
      </div>
    </form>
  </div>
</div>

<div v-if="showConfirmModal" class="modal-overlay z-max" @click="showConfirmModal = false">
  <div class="modal-content small alert-box" @click.stop>
    <div class="alert-icon">⚠️</div>
    <h2>{{ confirmMessage }}</h2>
    <p class="info-text center-text">{{ confirmSubMessage }}</p>

    <div class="modal-actions space-between mt-4">
      <button type="button" @click="showConfirmModal = false" class="ghost-btn">
        Anuluj
      </button>
      <button type="button" class="danger-btn full-confirm" @click="handleConfirmAction">
        🗑️ Tak, usuń
      </button>
    </div>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
// Importujemy Twój serwis API (ten z FractiApiService)
import fractiService, { type Settlement, CATEGORY_LABELS } from '@/services/receipts.service';

const router = useRouter();

// --- STATE ---
const settlements = ref<Settlement[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showCreateModal = ref(false);
const showJoinModal = ref(false);
const newSettlementName = ref('');
const newSettlementDescription = ref('');
const joinCode = ref('');
const showEditModal = ref(false);
const editingSettlement = ref({ id: '', name: '', description: '' });
const showConfirmModal = ref(false);
const confirmMessage = ref('');
const confirmSubMessage = ref('');
const pendingDeleteAction = ref<(() => Promise<void>) | null>(null);

// Przechowujemy ID rozwiniętych kafelków (Set jest szybszy niż Array)
const expandedSet = ref<Set<string>>(new Set());

// --- WATCHERS - Kontrola scrollu body'ego gdy modal jest otwarty ---
const isAnyModalOpen = () => {
  return showCreateModal.value || showJoinModal.value || showEditModal.value || showConfirmModal.value;
};

watch([showCreateModal, showJoinModal, showEditModal, showConfirmModal], () => {
  if (isAnyModalOpen()) {
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.width = '100%';
    document.documentElement.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
    document.body.style.position = '';
    document.body.style.width = '';
    document.documentElement.style.overflow = '';
  }
});

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

const goToDetails = (id: string) => {
  router.push(`/settlements/${id}`);
};

const goToOCR = () => {
  router.push('/ocr-upload');
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
    const newSettlement = await fractiService.createSettlement({
      name: newSettlementName.value,
      description: newSettlementDescription.value
    });
    settlements.value.unshift(newSettlement);
    showCreateModal.value = false;
    newSettlementName.value = '';
    newSettlementDescription.value = '';
  } catch (e) {
    console.error('Błąd tworzenia rozliczenia:', e);
    alert('Błąd tworzenia rozliczenia');
  }
};

const joinSettlement = async () => {
  try {
    await fractiService.joinSettlement(joinCode.value);
    await loadSettlements();
    showJoinModal.value = false;
    joinCode.value = '';
  } catch (e) {
    alert('Błąd dołączania do rozliczenia');
  }
};

const openEditModal = (settlement: Settlement) => {
  editingSettlement.value = {
    id: settlement.id,
    name: settlement.name,
    description: settlement.description || ''
  };
  showEditModal.value = true;
};

const updateSettlement = async () => {
  try {
    await fractiService.updateSettlement(editingSettlement.value.id, {
      name: editingSettlement.value.name,
      description: editingSettlement.value.description
    });

    await loadSettlements();
    showEditModal.value = false;
  } catch (e) {
    console.error('Błąd edycji:', e);
    alert('Nie udało się zaktualizować rozliczenia.');
  }
};

const confirmDeleteSettlement = () => {
  confirmMessage.value = 'Usunąć rozliczenie?';
  confirmSubMessage.value = `Czy na pewno chcesz usunąć grupę "${editingSettlement.value.name}"? Zostaną usunięte wszystkie paragony i produkty z nią powiązane.`;

  pendingDeleteAction.value = async () => {
    try {
      await fractiService.deleteSettlement(editingSettlement.value.id);
      showEditModal.value = false;
      await loadSettlements();
    } catch (e) {
      console.error('Błąd usuwania:', e);
      alert('Nie udało się usunąć rozliczenia.');
    }
  };

  showConfirmModal.value = true;
};

const handleConfirmAction = async () => {
  if (pendingDeleteAction.value) {
    await pendingDeleteAction.value();
  }
  showConfirmModal.value = false;
  pendingDeleteAction.value = null;
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

onUnmounted(() => {
  // Resetuj overflow przy opuszczaniu komponentu
  document.body.style.overflow = '';
  document.body.style.position = '';
  document.body.style.width = '';
  document.documentElement.style.overflow = '';
});
</script>

<style scoped>
/* KONTENER GŁÓWNY */
.settlements-container {
  flex: 1;
  background: var(--gradient-page-dark);
  padding: var(--spacing-lg);
  font-family: 'Inter', sans-serif;
  color: var(--text-primary);
}

.header {
  max-width: 900px;
  margin: 0 auto 2rem auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-wrapper {
  max-width: 900px;
  margin: 0 auto;
}

.header h1 {
  background: var(--gradient-card);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2.5rem;
  font-weight: 700;
}

.header-actions {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}

.join-btn {
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.3);
  padding: 12px 24px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: var(--transition-normal);
  box-shadow: 0 3px 15px rgba(99, 102, 241, 0.2);
}

.join-btn:hover {
  transform: translateY(-2px);
  background: rgba(99, 102, 241, 0.25);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 5px 25px rgba(99, 102, 241, 0.4);
}

.ocr-btn {
  background: rgba(168, 85, 247, 0.15);
  color: #c4b5fd;
  border: 1px solid rgba(168, 85, 247, 0.3);
  padding: 12px 24px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: var(--transition-normal);
  box-shadow: 0 3px 15px rgba(168, 85, 247, 0.2);
}

.ocr-btn:hover {
  transform: translateY(-2px);
  background: rgba(168, 85, 247, 0.25);
  border-color: rgba(168, 85, 247, 0.5);
  box-shadow: 0 5px 25px rgba(168, 85, 247, 0.4);
}

.create-btn {
  background: var(--gradient-button);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: var(--transition-normal);
  box-shadow: 0 5px 20px rgba(139, 92, 246, 0.3);
}
.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.5);
}

/* LOADING / ERROR STATE - nadpisania */
.state-msg {
  max-width: 900px;
  margin: 0 auto;
}
.state-msg .hint { color: #6b7280; margin-top: 0.5rem; }

/* KARTA ROZLICZENIA */
.settlement-card {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 16px;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  transition: var(--transition-normal);
  overflow: hidden;
}

.settlement-card:hover {
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.4);
  border-color: rgba(139, 92, 246, 0.4);
  transform: translateY(-3px);
}

.settlement-card.is-expanded {
  border-color: rgba(139, 92, 246, 0.6);
  background: rgba(139, 92, 246, 0.08);
}

/* GŁÓWNY WIERSZ KARTY */
.card-main {
  display: flex;
  align-items: center;
  padding: 1.5rem;
  background: transparent;
}

.info-section { flex: 1; }
.info-section h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.3rem;
  color: #f3f4f6;
  font-weight: 600;
}
.meta {
  font-size: 0.85rem;
  color: var(--text-secondary);
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
  align-items: center;
}
.members-pill {
  background: rgba(139, 92, 246, 0.2);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
}
.desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin: 0;
  font-style: italic;
}

.amount-section {
  text-align: right;
  padding: 0 1.5rem;
  min-width: 120px;
}
.amount-section .label {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.amount-section .value {
  font-size: 1.4rem;
  font-weight: 700;
  background: var(--gradient-button);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.actions-section {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  border-left: 1px solid rgba(139, 92, 246, 0.2);
  padding-left: 1rem;
}

/* PRZYCISKI */
.btn-details {
  background: rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
  border: 1px solid rgba(139, 92, 246, 0.3);
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: var(--transition-fast);
}
.btn-details:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
  transform: translateY(-2px);
}

.btn-map {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.3);
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: var(--transition-fast);
}
.btn-map:hover {
  background: rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.5);
  transform: translateY(-2px);
}

.btn-expand {
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  color: var(--text-secondary);
  transition: var(--transition-normal);
}
.btn-expand:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.5);
  color: var(--text-primary);
}
.btn-expand.rotated {
  transform: rotate(180deg);
  background: rgba(139, 92, 246, 0.2);
  color: #f3f4f6;
}

/* ROZWIJANE SZCZEGÓŁY */
.card-details {
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(139, 92, 246, 0.2);
  animation: slideDown 0.3s ease-out;
}

.details-inner { padding: 1.5rem; }

.sub-section { margin-bottom: 1.5rem; }
.sub-section h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  text-transform: uppercase;
  color: #a78bfa;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.sub-section ul { list-style: none; padding: 0; margin: 0; }
.sub-section li {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  font-size: 0.95rem;
  align-items: center;
}
.sub-section li:last-child { border-bottom: none; }

.item-name { font-weight: 500; color: var(--text-primary); }
.item-cat {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-left: 10px;
  background: rgba(139, 92, 246, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
}
.item-date {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-left: 6px;
  margin-right: auto;
  background: rgba(139, 92, 246, 0.1);
  padding: 2px 8px;
  border-radius: 6px;
}
.item-price { font-weight: 600; color: #a78bfa; }

.no-items {
  font-style: italic;
  color: #6b7280;
  text-align: center;
  padding: 1.5rem;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 8px;
}

/* MODAL - nadpisania dla Settlements */
.modal-content {
  width: 400px;
}
.modal-content h2 {
  font-size: 1.5rem;
}
.modal-content input {
  margin-bottom: 1rem;
}
.btn-edit {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-fast);
  font-size: 1.1rem;
}

.btn-edit:hover {
  background: rgba(139, 92, 246, 0.25);
  transform: rotate(45deg); /* Fajny efekt obrotu przy najechaniu */
  border-color: rgba(139, 92, 246, 0.6);
}

/* Układ w modalu - nadpisanie */
.modal-actions.space-between {
  margin-top: 1.5rem;
}

.right-actions {
  display: flex;
  gap: 10px;
}

.center-text {
  font-size: 0.95rem;
  margin-bottom: 1.5rem;
}

.full-confirm {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  background: rgba(220, 38, 38, 0.2) !important;
  border: 1px solid #ef4444 !important;
}
.full-confirm:hover {
  background: #dc2626 !important;
  color: white !important;
}
.modal-content input {
  width: 100%;
  padding: 12px;
  margin-bottom: 1rem;
  background: #0f172a; /* Ciemne tło */
  border: 1px solid rgba(139, 92, 246, 0.3); /* Fioletowa ramka */
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s, box-shadow 0.3s;
  box-sizing: border-box;
}

.modal-content input:focus {
  border-color: var(--color-purple);
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-actions button {
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: transparent;
  color: #c4b5fd;
  cursor: pointer;
  font-size: 0.95rem;
  transition: var(--transition-fast);
}

.modal-actions button:hover {
  background: rgba(139, 92, 246, 0.1);
  color: white;
  border-color: #a78bfa;
}

.modal-actions button.primary {
  background: var(--gradient-button);
  border: none;
  color: white;
  font-weight: 600;
}

.modal-actions button.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

/* Responsive */
@media (max-width: 1024px) {
  .settlements-container {
    padding: 1.5rem;
  }

  .header {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .header h1 {
    font-size: 1.75rem;
  }

  .header-actions {
    flex-direction: row;
    width: 100%;
    gap: 0.75rem;
  }

  .header-actions button {
    flex: 1;
  }

  .settlement-card {
    flex-direction: column;
  }

  .card-main {
    flex-direction: column;
  }

  .info-section,
  .amount-section {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .settlements-container {
    padding: 1rem;
  }

  .header {
    padding: 1rem;
  }

  .header h1 {
    font-size: 1.5rem;
  }

  .create-btn,
  .join-btn,
  .ocr-btn {
    padding: 10px 12px;
    font-size: 0.85rem;
  }

  .settlement-card {
    flex-direction: column;
    padding: 1rem;
  }

  .card-main {
    flex-direction: column;
    gap: 0.75rem;
  }

  .info-section {
    width: 100%;
  }

  .info-section h2 {
    font-size: 1.2rem;
  }

  .amount-section {
    width: 100%;
    text-align: left;
    padding: 0.75rem;
    background: rgba(139, 92, 246, 0.1);
    border-radius: 8px;
  }

  .actions-section {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .actions-section button {
    padding: 8px 12px;
    font-size: 0.8rem;
    width: 100%;
  }

  .desc {
    font-size: 0.9rem;
  }

  .meta {
    font-size: 0.8rem;
    gap: 0.5rem;
  }

  .card-expanded {
    flex-direction: column;
  }

  .members-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 90vw;
    max-width: 400px;
    padding: 1rem;
    max-height: 80vh;
    overflow-y: auto;
    box-sizing: border-box;
  }

  .modal-content h2 {
    font-size: 1.3rem;
    margin-bottom: 1rem;
  }

  .modal-content input {
    padding: 10px;
    font-size: 16px;
    margin-bottom: 1rem;
  }

  .modal-actions {
    flex-direction: column;
    gap: 0.75rem;
  }

  .modal-actions button {
    width: 100%;
    padding: 10px;
  }
}

@media (max-width: 480px) {
  .settlements-container {
    padding: 0.75rem;
  }

  .header {
    padding: 0.75rem;
  }

  .header h1 {
    font-size: 1.25rem;
  }

  .create-btn,
  .join-btn,
  .ocr-btn {
    padding: 8px 10px;
    font-size: 0.75rem;
    width: 100%;
  }

  .settlement-card {
    padding: 0.75rem;
  }

  .info-section h2 {
    font-size: 1.1rem;
  }

  .meta {
    font-size: 0.75rem;
  }

  .amount-section .value {
    font-size: 1.1rem;
  }

  .members-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95vw;
    max-width: 95vw;
    padding: 1rem;
    max-height: 75vh;
    overflow-y: auto;
    box-sizing: border-box;
  }

  .modal-content h2 {
    font-size: 1.2rem;
    margin-bottom: 0.75rem;
  }

  .modal-content input {
    padding: 10px;
    margin-bottom: 1rem;
    font-size: 16px;
  }

  .modal-actions {
    margin-top: 1rem;
  }

  .modal-actions button {
    font-size: 0.9rem;
    padding: 10px;
  }

  button {
    font-size: 14px;
  }

  input, textarea {
    font-size: 16px;
  }
}
</style>