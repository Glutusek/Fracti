<template>
  <div class="details-container">
    <div class="header">
      <button @click="goBack" class="back-btn">← Powrót</button>
      <div class="header-info">
        <h1>{{ settlement?.name || 'Ładowanie...' }}</h1>
        <div v-if="settlement?.description" class="settlement-description">
         Opis: {{ settlement.description }}
        </div>
        <div class="total-cost">
          Łączny koszt: <span class="amount">{{ formatMoney(settlement?.total_expenses) }} zł</span>
        </div>
      </div>
    </div>

    <div class="content-split">
      <div class="left-column">
        <div class="timeline-header">
          <h2>Historia wydatków</h2>
          <span class="count">{{ totalItemsCount }} pozycji</span>
        </div>

        <div v-if="loading" class="state-msg">
          <div class="spinner"></div> Ładowanie...
        </div>

        <div v-else-if="combinedTimeline.length === 0" class="state-msg empty">
          Brak wydatków w tym rozliczeniu
        </div>

        <div v-else class="timeline">
          <div
            v-for="item in combinedTimeline"
            :key="item.type + '-' + item.id"
            class="timeline-item"
            :class="{ 'is-receipt': item.type === 'receipt', 'is-expanded': expandedReceipts.has(item.id) }"
          >
            <div class="item-main" @click="openOnMap(item)">

              <div class="item-icon">
                {{ item.type === 'receipt' ? '🧾' : '🛒' }}
              </div>

              <div class="item-info">
                <div class="item-name">{{ item.name }}</div>
                <div class="item-meta">
                  <span class="date">{{ formatDate(item.date) }}</span>
                  <span class="payer">Płatnik: {{ getUserName(item.payerId) }}</span>
                </div>
              </div>

              <div class="item-right-panel">
                <div class="item-amount">{{ formatMoney(item.amount) }} zł</div>

                <button v-if="item.latitude && item.longitude" class="action-icon-btn map" @click.stop="openOnMap(item)" title="Pokaż na mapie">
                  🗺️
                </button>

                <button class="action-icon-btn edit" @click.stop="editItem(item)" title="Edytuj">
                  ✏️
                </button>

                <button v-if="item.type === 'receipt'" class="action-icon-btn expand" @click.stop="toggleReceipt(item.id)">
                  {{ expandedReceipts.has(item.id) ? '▲' : '▼' }}
                </button>
              </div>
            </div>

            <div v-if="item.type === 'receipt' && expandedReceipts.has(item.id)" class="receipt-products">
              <div v-for="product in item.products" :key="product.id" class="product-item">
                <div class="product-info">
                  <div class="product-name">{{ product.name }}</div>
                  <div class="product-meta">
                    <span class="category-tag">{{ CATEGORY_LABELS[product.category] }}</span>
                    <span class="consumers-tag">👥 {{ product.consumers.length }}</span>
                  </div>
                </div>
                <div class="product-right">
                  <div class="product-amount">{{ formatMoney(product.price) }} zł</div>
                  <button class="edit-icon-btn" @click.stop="openReceiptItemModal(product, item.id)" title="Edytuj pozycję">✏️</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-column">
        <div class="action-panel">
          <button @click="goToMap" class="action-btn map-btn">
            🗺️ Mapa
          </button>
          <button @click="addReceipt" class="action-btn receipt-btn">
            📸 Dodaj Paragon
          </button>
          <button @click="openAddProductModal" class="action-btn product-btn">
            🛒 Dodaj Produkt
          </button>
        </div>

        <div class="users-section">
          <h3>Uczestnicy ({{ settlement?.members?.length || 0 }})</h3>
          <div class="users-list">
              <div v-for="member in settlement?.members" :key="member.id" class="user-card">

                <div class="user-avatar">
                  {{ (member.first_name || member.username).charAt(0).toUpperCase() }}
                </div>

                <div class="user-info">
                  <div class="user-name">
                    {{ member.first_name ? member.first_name : member.username }}
                    <span v-if="member.id === settlement?.owner_id" title="Właściciel grupy" style="margin-left:5px; cursor:help">👑</span>
                  </div>

                  <div class="user-balance">
                    <span class="paid">Zapłacił: {{ formatMoney(getUserPaid(member.id)) }} zł</span>
                  </div>
                </div>

                <button
                  v-if="member.id !== settlement?.owner_id"
                  @click="tryRemoveMember(member)"
                  class="remove-user-btn"
                  title="Usuń z grupy"
                >
                  ⛔
                </button>

              </div>
            </div>

            <!-- Sekcja zobowiązań netto -->
            <div v-if="calculateNetDebts().length > 0" class="debts-section">
              <h3>💰 Rozliczenia</h3>
              <div class="debts-list">
                <div v-for="(debt, index) in calculateNetDebts()" :key="index" class="debt-item">

                  <div class="debt-row-top">
                    <div class="debt-from-user">
                      <div class="user-avatar-small">{{ debt.fromName.charAt(0).toUpperCase() }}</div>
                      <div class="debt-name">{{ debt.fromName }}</div>
                    </div>

                    <div class="debt-center">
                      <div class="arrow-icon">→</div>
                      <div class="action-label">oddaje</div>
                    </div>

                    <div class="debt-to-user">
                      <div class="debt-name">{{ debt.toName }}</div>
                      <div class="user-avatar-small">{{ debt.toName.charAt(0).toUpperCase() }}</div>
                    </div>
                  </div>

                  <div class="debt-row-bottom">
                    <div class="debt-amount-box">
                      <div class="debt-amount">{{ formatMoney(debt.amount) }}</div>
                      <div class="debt-currency">zł</div>
                    </div>

                    <button class="settle-btn" @click="settleDebtTransaction(debt)" title="Potwierdź rozliczenie">
                      ✓
                    </button>
                  </div>

                </div>
              </div>
            </div>
            <div v-else class="debts-section">
              <h3>💰 Rozliczenia</h3>
              <div class="empty-state">✓ Wszyscy są rozliczeni!</div>
            </div>

            <!-- Sekcja wykonanych rozliczeń -->
            <div v-if="settlement?.debt_settlements && settlement.debt_settlements.length > 0" class="settled-debts-section">
              <h3>✅ Wykonane rozliczenia</h3>
              <div class="settled-debts-list">
                <div v-for="debt in settlement.debt_settlements" :key="debt.id" class="settled-debt-item">
                  <div class="settled-debt-from-user">
                    <div class="user-avatar-small">{{ debt.from_user_name?.charAt(0).toUpperCase() }}</div>
                    <div class="settled-debt-name">{{ debt.from_user_name }}</div>
                  </div>
                  
                  <div class="settled-debt-center">
                    <div class="arrow-icon">→</div>
                    <div class="action-label">oddał</div>
                  </div>
                  
                  <div class="settled-debt-to-user">
                    <div class="settled-debt-name">{{ debt.to_user_name }}</div>
                    <div class="user-avatar-small">{{ debt.to_user_name?.charAt(0).toUpperCase() }}</div>
                  </div>
                  
                  <div class="settled-debt-amount-box">
                    <div class="settled-debt-amount">{{ formatMoney(debt.amount) }}</div>
                    <div class="settled-debt-currency">zł</div>
                  </div>

                  <div class="settled-debt-date">
                    {{ formatDate(debt.settled_at) }}
                  </div>
                  
                  <button class="undo-settle-btn" @click="undoSettleDebtTransaction(debt)" title="Cofnij rozliczenie">
                    ↶
                  </button>
                </div>
              </div>
            </div>

            <div class="user-actions-row">
              <button @click="showAddUserModal = true" class="add-user-btn">
                🔗 Zaproś kodem
              </button>
              <button @click="showAddGuestModal = true" class="add-user-btn">
                👤 Dodaj gościa
              </button>
            </div>
        </div>
      </div>
    </div>

    <div v-if="showAddProductModal" class="modal-overlay" @click="showAddProductModal = false">
      <div class="modal-content" @click.stop>
        <h2>Dodaj Produkt</h2>
        <form @submit.prevent="createLooseProduct">
          <div class="form-group">
            <label>Nazwa produktu</label>
            <input v-model="newProduct.name" required />
          </div>
          <div class="form-group">
            <label>Opis (opcjonalnie)</label>
            <textarea v-model="newProduct.description" rows="2" placeholder="Dodatkowy opis..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>Cena (zł)</label>
              <input v-model="newProduct.price" type="number" step="0.01" required />
            </div>
            <div class="form-group half">
              <label>Kategoria</label>
              <select v-model="newProduct.category">
                <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Lokalizacja zakupu (Kliknij na mapie)</label>
            <div id="map-add" class="modal-map"></div>
            <div class="coords-display" v-if="newProduct.latitude && newProduct.longitude">
              📍 Wybrano: {{ newProduct.latitude.toFixed(6) }}, {{ newProduct.longitude.toFixed(6) }}
            </div>
          </div>

          <div class="form-group" :class="{ 'has-error': addProductFormErrors.payer }">
            <label>Płatnik</label>
            <select v-model="newProduct.payer">
              <option :value="null" disabled>Wybierz płatnika</option>
              <option v-for="member in settlement?.members" :key="member.id" :value="member.id">
                {{ (member.first_name && member.first_name.trim() !== '') ? member.first_name : member.username }}
              </option>
            </select>
            <span v-if="addProductFormErrors.payer" class="error-text">{{ addProductFormErrors.payer }}</span>
          </div>

          <div class="form-group" :class="{ 'has-error': addProductFormErrors.consumers }">
            <label>Konsumenci</label>
            <div class="checkbox-group">
              <label v-for="member in settlement?.members" :key="member.id">
                <input type="checkbox" :value="member.id" v-model="newProduct.consumers" />
                {{ (member.first_name && member.first_name.trim() !== '') ? member.first_name : member.username }}
              </label>
            </div>
            <span v-if="addProductFormErrors.consumers" class="error-text">{{ addProductFormErrors.consumers }}</span>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddProductModal = false">Anuluj</button>
            <button type="submit" class="primary">Dodaj</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showAddUserModal" class="modal-overlay" @click="showAddUserModal = false">
      <div class="modal-content small" @click.stop>
        <h2>Kod zaproszenia</h2>
        <p class="info-text">Udostępnij ten kod innym użytkownikom, aby mogli dołączyć do rozliczenia:</p>
        <div class="code-display">
          <span class="code">{{ settlement?.join_code }}</span>
          <button @click="copyCode" class="copy-btn" type="button">
            {{ codeCopied ? '✓ Skopiowano' : '📋 Kopiuj' }}
          </button>
        </div>
        <div class="modal-actions">
          <button type="button" @click="showAddUserModal = false" class="primary">Zamknij</button>
        </div>
      </div>
    </div>

    <div v-if="showEditProductModal && editingProduct" class="modal-overlay" @click="showEditProductModal = false">
      <div class="modal-content" @click.stop>
        <h2>Edytuj Produkt</h2>
        <form @submit.prevent="updateProduct">
          <div class="form-group">
            <label>Nazwa produktu</label>
            <input v-model="editingProduct.name" required />
          </div>
          <div class="form-group">
            <label>Opis</label>
            <textarea v-model="editingProduct.description" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group half">
              <label>Cena</label>
              <input v-model="editingProduct.price" type="number" step="0.01" />
            </div>
            <div class="form-group half">
              <label>Kategoria</label>
              <select v-model="editingProduct.category">
                <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Lokalizacja</label>
            <div id="map-edit-prod" class="modal-map"></div>
            <div class="coords-display" v-if="editingProduct.latitude && editingProduct.longitude">
              📍 {{ editingProduct.latitude.toFixed(6) }}, {{ editingProduct.longitude.toFixed(6) }}
            </div>
          </div>

          <div class="form-group">
            <label>Płatnik</label>
            <select v-model="editingProduct.purchaser">
              <option :value="null" disabled>Wybierz płatnika</option>
              <option v-for="member in settlement?.members" :key="member.id" :value="member.id">
                {{ (member.first_name && member.first_name.trim() !== '') ? member.first_name : member.username }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Konsumenci</label>
            <div class="checkbox-group" :class="{ 'has-error': editProductFormErrors.consumers }">
              <label v-for="member in settlement?.members" :key="member.id">
                <input type="checkbox" :value="member.id" v-model="editingProduct.consumers" />
                {{ (member.first_name && member.first_name.trim() !== '') ? member.first_name : member.username }}
              </label>
            </div>
            <span v-if="editProductFormErrors.consumers" class="error-text">{{ editProductFormErrors.consumers }}</span>
          </div>

          <div class="modal-actions space-between">
            <button type="button" class="danger-btn" @click="deleteLooseProduct">
              🗑️ Usuń
            </button>
            <div class="right-actions">
              <button type="button" @click="showEditProductModal = false">Anuluj</button>
              <button type="submit" class="primary">Zapisz</button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showEditReceiptModal && editingReceipt" class="modal-overlay" @click="showEditReceiptModal = false">
      <div class="modal-content" @click.stop>
        <h2>Edytuj Paragon</h2>

        <div class="modal-section-title">Dane ogólne</div>
        <form @submit.prevent="updateReceipt">
          <div class="form-group">
            <label>Sklep</label>
            <input v-model="editingReceipt.merchant_name" required />
          </div>
          <div class="form-group">
            <label>Opis paragonu</label>
            <textarea v-model="editingReceipt.description" rows="2" placeholder="Np. zakupy na grilla"></textarea>
          </div>
          <div class="form-group">
            <label>Lokalizacja sklepu</label>
            <div id="map-edit-receipt" class="modal-map"></div>
            <div class="coords-display" v-if="editingReceipt.latitude && editingReceipt.longitude">
              📍 {{ editingReceipt.latitude.toFixed(6) }}, {{ editingReceipt.longitude.toFixed(6) }}
            </div>
          </div>

          <div class="form-group">
            <label>Data i godzina</label>
            <input v-model="editingReceipt.purchase_date" type="datetime-local" />
          </div>

          <div class="form-group">
            <label>Płatnik</label>
            <select v-model="editingReceipt.purchaser">
              <option v-for="member in settlement?.members" :key="member.id" :value="member.id">
                {{ (member.first_name && member.first_name.trim() !== '') ? member.first_name : member.username }}
              </option>
            </select>
          </div>

          <hr class="modal-divider" />

          <div class="modal-section-header">
            <div class="modal-section-title">Pozycje na paragonie</div>
            <button type="button" class="add-item-btn" @click="openReceiptItemModal(null, editingReceipt.id)">
              + Dodaj pozycję
            </button>
          </div>

          <div class="receipt-items-list">
            <div v-if="!editingReceipt.products || editingReceipt.products.length === 0" class="empty-list">
              Brak pozycji. Dodaj coś!
            </div>
            <div
              v-for="prod in editingReceipt.products"
              :key="prod.id"
              class="receipt-list-item"
              :class="{ 'has-error': editReceiptErrors[prod.id] }"
            >
              <div class="r-item-info">
                <div class="r-item-name">{{ prod.name }}</div>

                <div v-if="editReceiptErrors[prod.id]" class="error-text-mini">
                   ⚠️ {{ editReceiptErrors[prod.id] }}
                </div>

                <div class="r-item-meta">
                  {{ formatMoney(prod.price) }} zł •
                  <span :class="{'text-red': !prod.consumers.length}">
                    {{ prod.consumers.length }} os.
                  </span>
                </div>
              </div>
              <div class="r-item-actions">
                <button class="icon-btn edit" @click="openReceiptItemModal(prod, editingReceipt.id)">✏️</button>
                <button class="icon-btn delete" @click="deleteReceiptItem(prod.id)">🗑️</button>
              </div>
            </div>
          </div>

          <div class="calculated-total-box">
            <div class="calc-label">Suma pozycji:</div>
            <div class="calc-value">{{ formatMoney(calculatedReceiptTotal) }} zł</div>
          </div>

          <div class="modal-actions equal-buttons mt-4">
            <button type="button" class="danger-btn" @click="deleteReceipt">
              🗑️ Usuń
            </button>
            <button type="button" @click="showEditReceiptModal = false">Anuluj</button>
            <button type="submit" class="primary">📝 Zapisz</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showReceiptItemModal" class="modal-overlay z-high" @click="showReceiptItemModal = false">
      <div class="modal-content small" @click.stop>
        <h2>{{ editingReceiptItem?.id ? 'Edytuj pozycję' : 'Nowa pozycja' }}</h2>

        <form @submit.prevent="saveReceiptItem">
          <div class="form-group">
            <label>Nazwa produktu</label>
            <input v-model="receiptItemForm.name" required placeholder="np. Chipsy" />
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>Cena (zł)</label>
              <input v-model="receiptItemForm.price" type="number" step="0.01" required />
            </div>
            <div class="form-group half">
              <label>Kategoria</label>
              <select v-model="receiptItemForm.category">
                <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Konsumenci</label>
            <div class="checkbox-group">
              <label v-for="member in settlement?.members" :key="member.id">
                <input type="checkbox" :value="member.id" v-model="receiptItemForm.consumers" />
                {{ (member.first_name && member.first_name.trim() !== '') ? member.first_name : member.username }}
              </label>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" @click="showReceiptItemModal = false">Anuluj</button>
            <button type="submit" class="primary">
              {{ editingReceiptItem?.id ? 'Zaktualizuj' : 'Dodaj' }}
            </button>
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
          <button type="button" class="danger-btn full-confirm" @click="handleConfirmDelete">
            🗑️ Tak, usuń
          </button>
        </div>
      </div>
    </div>
    <div v-if="toastMessage" class="toast" :class="toastType">{{ toastMessage }}</div>
    <div v-if="showAddGuestModal" class="modal-overlay" @click="showAddGuestModal = false">
    <div class="modal-content small" @click.stop>
      <h2>Dodaj Użytkownika Roboczego</h2>
      <p class="info-text">
        Stwórz lokalnego użytkownika (np. "Babcia", "Dzieci"), którego możesz przypisywać do wydatków bez konieczności rejestracji.
      </p>

      <form @submit.prevent="createGuestUser">
        <div class="form-group">
          <label>Nazwa wyświetlana</label>
          <input
            v-model="guestName"
            placeholder="np. Marek (bez apki)"
            required
            autofocus
          />
        </div>

        <div class="modal-actions">
          <button type="button" @click="showAddGuestModal = false">Anuluj</button>
          <button type="submit" class="primary">Dodaj</button>
        </div>
      </form>
    </div>
</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import fractiService, { type Settlement, type Receipt, type Product, CATEGORY_LABELS, Category } from '@/services/receipts.service';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const router = useRouter();
const route = useRoute();

// State
const settlement = ref<Settlement | null>(null);
const loading = ref(true);
const expandedReceipts = ref<Set<number>>(new Set());
const showAddProductModal = ref(false);
const showAddUserModal = ref(false);
const showEditProductModal = ref(false);
const showEditReceiptModal = ref(false);
const showReceiptItemModal = ref(false);
const codeCopied = ref(false);
const showConfirmModal = ref(false);
const confirmMessage = ref('');
const confirmSubMessage = ref('');
const showAddGuestModal = ref(false);
const guestName = ref('');
// Map instances
let mapInstance: L.Map | null = null;
let markerInstance: L.Marker | null = null;

const newProduct = ref({
  name: '',
  description: '',
  price: '',
  category: Category.FOOD,
  payer: null as number | null,
  consumers: [] as number[],
  latitude: null as number | null,
  longitude: null as number | null
});

const pendingDeleteAction = ref<(() => Promise<void>) | null>(null);
const editingProduct = ref<Product | null>(null);
const editingReceipt = ref<Receipt | null>(null);
const editingReceiptItem = ref<Product | null>(null);
const currentReceiptId = ref<number | null>(null);
const receiptItemForm = ref({
  name: '',
  price: '',
  category: Category.FOOD,
  consumers: [] as number[]
});

const addProductFormErrors = ref<{
  payer?: string;
  consumers?: string;
}>({});
const editProductFormErrors = ref<{
  consumers?: string;
}>({});

const editReceiptErrors = ref<Record<number, string>>({});

const categories = fractiService.getCategoriesOptionList();

watch(
  () => newProduct.value.payer,
  (newVal) => {
    if (newVal !== null && newVal !== undefined && addProductFormErrors.value.payer) {
      addProductFormErrors.value.payer = undefined;
    }
  }
);

watch(
  () => newProduct.value.consumers,
  (newConsumers) => {
    if (newConsumers && newConsumers.length > 0 && addProductFormErrors.value.consumers) {
      addProductFormErrors.value.consumers = undefined;
    }
  }
);

watch(
  () => editingProduct.value?.consumers,
  (newConsumers) => {
    if (newConsumers && newConsumers.length > 0 && editProductFormErrors.value.consumers) {
      editProductFormErrors.value.consumers = undefined;
    }
  }
);

// Computed
const calculatedReceiptTotal = computed(() => {
  if (!editingReceipt.value?.products) return 0;
  return editingReceipt.value.products.reduce((sum, product) => {
    return sum + parseFloat(product.price.toString() || '0');
  }, 0);
});
const combinedTimeline = computed(() => {
  if (!settlement.value) return [];

  const items: Array<{
    id: number;
    type: 'receipt' | 'product';
    name: string;
    amount: string;
    date: string;
    payerId: number;
    products?: Product[];
  }> = [];

  // Add receipts
        settlement.value.receipts?.forEach(receipt => {
          items.push({
            id: receipt.id,
            type: 'receipt',
            name: receipt.merchant_name,
            amount: receipt.total_amount,
            date: receipt.purchase_date || new Date().toISOString(),
            latitude: receipt.latitude ?? null,
            longitude: receipt.longitude ?? null,
            payerId: receipt.purchaser,
            products: receipt.products || []
          });
        });

  // Add loose products
  settlement.value.loose_products?.forEach(product => {
    items.push({
      id: product.id,
      type: 'product',
      name: product.name,
      amount: product.price,
      date: product.created_at,
      latitude: product.latitude ?? null,
      longitude: product.longitude ?? null,
      payerId: product.purchaser || 0
    });
  });


  return items.sort((a, b) => {
    const ta = isNaN(new Date(a.date).getTime()) ? 0 : new Date(a.date).getTime();
    const tb = isNaN(new Date(b.date).getTime()) ? 0 : new Date(b.date).getTime();
    return tb - ta;
  });
});

const totalItemsCount = computed(() => {
  return (settlement.value?.receipts?.length || 0) + (settlement.value?.loose_products?.length || 0);
});

// Methods
const goBack = () => {
  router.push('/settlements');
};

const goToMap = () => {
  router.push(`/map/${settlement.value?.id}`);
};

const openOnMap = (item: { type: string; id: number; }) => {
  // focus key matches MapView uniqueId format: r-<id> or p-<id>
  const uniqueId = item.type === 'receipt' ? `r-${item.id}` : `p-${item.id}`;
  router.push({ name: 'map-settlement', params: { uuid: settlement.value?.id }, query: { focus: uniqueId } });
};

const addReceipt = () => {
  if (settlement.value?.id) {
    router.push({
      path: '/ocr-upload',
      query: { settlementId: settlement.value.id }
    });
  } else {
    router.push('/ocr-upload');
  }
};

const toggleReceipt = (id: number) => {
  if (expandedReceipts.value.has(id)) {
    expandedReceipts.value.delete(id);
  } else {
    expandedReceipts.value.add(id);
  }
};

const getUserName = (userId: number): string => {
  const user = settlement.value?.members?.find(m => m.id === userId);
  return user?.first_name || user?.username || 'Nieznany';
};

const getUserPaid = (userId: number): number => {
  if (!settlement.value) return 0;

  let total = 0;

  settlement.value.receipts?.forEach(receipt => {
    if (receipt.purchaser === userId) {
      total += parseFloat(receipt.total_amount || '0');
    }
  });

  settlement.value.loose_products?.forEach(product => {
    if (product.purchaser === userId) {
      total += parseFloat(product.price || '0');
    }
  });

  return total;
};

const getUserExpenses = (userId: number): number => {
  if (!settlement.value) return 0;

  let total = 0;

  settlement.value.receipts?.forEach(receipt => {
    if (!receipt.products || receipt.products.length === 0) {
      const receiptCost = parseFloat(receipt.total_amount || '0');
      const membersCount = settlement.value?.members?.length || 1;
      total += receiptCost / membersCount;
    } else {
      receipt.products?.forEach(product => {
        if (product.consumers?.includes(userId)) {
          const consumersCount = product.consumers?.length || 1;
          const productCost = parseFloat(product.price || '0');
          total += parseFloat((productCost / consumersCount).toFixed(2));
        }
      });
    }
  });

  // Loose products - sumuj te, które konsumował
  settlement.value.loose_products?.forEach(product => {
    if (product.consumers?.includes(userId)) {
      const consumersCount = product.consumers?.length || 1;
      const productCost = parseFloat(product.price || '0');
      // Zaokrąglij do 2 miejsc po przecinku
      total += parseFloat((productCost / consumersCount).toFixed(2));
    }
  });

  return parseFloat(total.toFixed(2));
};

const getUserBalance = (userId: number): number => {
  // Balance = co zapłacił - ile powinien zapłacić
  const paid = getUserPaid(userId);
  const shouldPay = getUserExpenses(userId);

  return paid - shouldPay;
};

// Oblicz zobowiązania netto między parami osób
const calculateNetDebts = (): Array<{from: number, to: number, amount: number, fromName: string, toName: string}> => {
  if (!settlement.value) return [];

  // Zbierz wszystkie już rozliczone długi
  const settledDebts = new Set<string>();
  settlement.value.debt_settlements?.forEach(ds => {
    const key = `${ds.from_user}-${ds.to_user}-${ds.amount}`;
    settledDebts.add(key);
  });

  // Najpierw oblicz wszystkie bilanse
  const balances: { [key: number]: number } = {};
  
  settlement.value.members?.forEach(member => {
    balances[member.id] = getUserBalance(member.id);
  });

  // Algorytm uproszczenia długów: łącz długi między parami
  const debts: Array<{from: number, to: number, amount: number, fromName: string, toName: string}> = [];
  const members = settlement.value.members || [];

  // Przejdź przez każdą parę
  for (let i = 0; i < members.length; i++) {
    for (let j = i + 1; j < members.length; j++) {
      const memberA = members[i];
      const memberB = members[j];
      
      const balanceA = balances[memberA.id];
      const balanceB = balances[memberB.id];
      
      // Jeśli A ma ujemny bilans (komuś jest winny) i B ma dodatni (jemu ktoś jest winny)
      // To możemy bezpośrednio przesunąć długi
      if (balanceA < 0 && balanceB > 0) {
        // A jest winny B
        const amount = Math.min(Math.abs(balanceA), balanceB);
        if (amount > 0.01) {
          const debtKey = `${memberA.id}-${memberB.id}-${amount.toFixed(2)}`;
          
          // Sprawdź czy ten dług nie został już rozliczony
          if (!settledDebts.has(debtKey)) {
            debts.push({
              from: memberA.id,
              to: memberB.id,
              amount: parseFloat(amount.toFixed(2)),
              fromName: memberA.first_name || memberA.username,
              toName: memberB.first_name || memberB.username
            });
          }
          
          balances[memberA.id] += amount;
          balances[memberB.id] -= amount;
        }
      } else if (balanceA > 0 && balanceB < 0) {
        // B jest winny A
        const amount = Math.min(balanceA, Math.abs(balanceB));
        if (amount > 0.01) {
          const debtKey = `${memberB.id}-${memberA.id}-${amount.toFixed(2)}`;
          
          // Sprawdź czy ten dług nie został już rozliczony
          if (!settledDebts.has(debtKey)) {
            debts.push({
              from: memberB.id,
              to: memberA.id,
              amount: parseFloat(amount.toFixed(2)),
              fromName: memberB.first_name || memberB.username,
              toName: memberA.first_name || memberA.username
            });
          }
          
          balances[memberA.id] -= amount;
          balances[memberB.id] += amount;
        }
      }
    }
  }

  return debts;
};

const formatMoney = (val: string | number | undefined): string => {
  if (!val) return '0.00';
  return Number(val).toFixed(2);
};

const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString('pl-PL', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const createGuestUser = async () => {
  if (!guestName.value || !settlement.value) return;

  try {
    loading.value = true;
    await fractiService.addGuestUser(settlement.value.id, guestName.value);

    await loadSettlement();

    showAddGuestModal.value = false;
    guestName.value = '';
    showToast('Dodano użytkownika roboczego', 'success');
  } catch (e) {
    console.error(e);
    showToast('Błąd dodawania użytkownika', 'error');
  } finally {
    loading.value = false;
  }
};

const settleDebtTransaction = async (debt: any) => {
  if (!settlement.value) return;

  try {
    await fractiService.settleDebt(
      settlement.value.id,
      debt.from,
      debt.to,
      debt.amount
    );
    
    showToast(`Rozliczenie potwierdzone! ${debt.fromName} oddał ${debt.toName} ${debt.amount} zł`, 'success');
    await loadSettlement();
  } catch (e) {
    console.error('Błąd przy zatwierdzaniu rozliczenia:', e);
    showToast('Nie udało się potwierdzić rozliczenia', 'error');
  }
};

const undoSettleDebtTransaction = async (debt: any) => {
  if (!settlement.value) return;

  try {
    await fractiService.undoSettleDebt(settlement.value.id, debt.id);
    
    showToast(`Cofnięto rozliczenie: ${debt.from_user_name} → ${debt.to_user_name}`, 'success');
    await loadSettlement();
  } catch (e) {
    console.error('Błąd przy cofaniu rozliczenia:', e);
    showToast('Nie udało się cofnąć rozliczenia', 'error');
  }
};

const tryRemoveMember = (member: any) => {
  // Sprawdź czy użytkownik ma jakiekolwiek zobowiązania w liście długów
  const debts = calculateNetDebts();
  const userHasDebts = debts.some(debt => debt.from === member.id || debt.to === member.id);

  if (userHasDebts) {
    const name = member.first_name || member.username;
    showToast(`Nie można usunąć. Użytkownik "${name}" musi być rozliczony.`, 'error');
    return;
  }

  const name = member.first_name || member.username;

  openConfirmModal(
    'Usunąć uczestnika?',
    `Czy na pewno chcesz usunąć "${name}" z grupy?`,
    async () => {
      try {
        if (!settlement.value) return;

        await fractiService.removeMember(settlement.value.id, member.id);

        await loadSettlement(); // Odśwież listę po usunięciu
        showToast(`Użytkownik ${name} został usunięty`, 'success');
      } catch (e: any) {
        console.error(e);
        const errorMsg = e.response?.data?.error || 'Błąd podczas usuwania użytkownika';
        showToast(errorMsg, 'error');
      }
    }
  );
};

const toDatetimeLocal = (dateString: string | null | undefined): string => {
  if (!dateString) return '';
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const toastMessage = ref('');
const toastType = ref<'success' | 'error'>('success');
const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
  toastMessage.value = msg;
  toastType.value = type;
  setTimeout(() => (toastMessage.value = ''), 2500);
};

// --- MAP LOGIC ---

const initMap = (elementId: string, lat: number | null, lng: number | null, onUpdate: (lat: number, lng: number) => void) => {
  if (mapInstance) {
    mapInstance.remove();
    mapInstance = null;
  }

  // Domyślna pozycja (np. Warszawa) lub pozycja produktu
  const startLat = lat || 52.2297;
  const startLng = lng || 21.0122;
  const zoom = lat ? 15 : 6;

  mapInstance = L.map(elementId).setView([startLat, startLng], zoom);

  // Ciemny motyw mapy CartoDB Dark Matter
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap contributors, © CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(mapInstance);

  // Dodaj marker jeśli mamy współrzędne
  if (lat && lng) {
    markerInstance = L.marker([lat, lng]).addTo(mapInstance);
  }

  // Kliknięcie na mapę
  mapInstance.on('click', (e: L.LeafletMouseEvent) => {
    const { lat, lng } = e.latlng;

    // Aktualizuj marker
    if (markerInstance) {
      markerInstance.setLatLng([lat, lng]);
    } else {
      markerInstance = L.marker([lat, lng]).addTo(mapInstance!);
    }

    // Wywołaj callback, żeby zaktualizować dane w formularzu
    onUpdate(lat, lng);
  });
};

const openAddProductModal = async () => {
  newProduct.value = {
    name: '',
    price: '',
    category: Category.FOOD,
    payer: null,
    consumers: [],
    latitude: null,
    longitude: null
  };
  addProductFormErrors.value = {};
  showAddProductModal.value = true;

  // Czekamy aż modal się wyrenderuje, żeby DIV mapy istniał
  await nextTick();
  initMap('map-add', null, null, (lat, lng) => {
    newProduct.value.latitude = lat;
    newProduct.value.longitude = lng;

  });
};

const editItem = async (item: any) => {
  if (item.type === 'receipt') {
    const receipt = settlement.value?.receipts?.find(r => r.id === item.id);
    if (receipt) {
    const srcDate = receipt.purchase_date || new Date().toISOString();
    editingReceipt.value = { ...receipt, purchase_date: toDatetimeLocal(srcDate as any) };
      showEditReceiptModal.value = true;

      await nextTick();
      initMap('map-edit-receipt', receipt.latitude ?? null, receipt.longitude ?? null, (lat, lng) => {
        if (editingReceipt.value) {
          editingReceipt.value.latitude = lat;
          editingReceipt.value.longitude = lng;
        }
      });
    }
  } else {
    // To jest loose product
    const product = settlement.value?.loose_products?.find(p => p.id === item.id);
    if (product) await editProduct(product);
  }
};

const editProduct = async (product: Product) => {
  editingProduct.value = { ...product }; // Kopia
  editProductFormErrors.value = {};
  showEditProductModal.value = true;

  await nextTick();
  initMap('map-edit-prod', product.latitude ?? null, product.longitude ?? null, (lat, lng) => {
    if (editingProduct.value) {
      editingProduct.value.latitude = lat;
      editingProduct.value.longitude = lng;
    }
  });
};

const copyCode = async () => {
  if (settlement.value?.join_code) {
    try {
      await navigator.clipboard.writeText(settlement.value.join_code);
      codeCopied.value = true;
      setTimeout(() => {
        codeCopied.value = false;
      }, 2000);
    } catch (error) {
      console.error('Błąd kopiowania:', error);
    }
  }
};

const createLooseProduct = async () => {
  addProductFormErrors.value = {};
  let hasErrors = false;

  if (!newProduct.value.payer) {
    addProductFormErrors.value.payer = 'Pole "Płatnik" jest wymagane';
    hasErrors = true;
  }

  if (!newProduct.value.consumers || newProduct.value.consumers.length === 0) {
    addProductFormErrors.value.consumers = 'Wybierz co najmniej jednego konsumenta';
    hasErrors = true;
  }

  if (hasErrors) {
    return;
  }

  try {
    await fractiService.addLooseProduct({
      name: newProduct.value.name,
      description: newProduct.value.description,
      price: newProduct.value.price,
      category: newProduct.value.category,
      consumers: newProduct.value.consumers,
      purchaser: newProduct.value.payer,
      latitude: newProduct.value.latitude,
      longitude: newProduct.value.longitude,
      settlement: settlement.value?.id
    });

    await loadSettlement();
    showAddProductModal.value = false;
    addProductFormErrors.value = {};
    newProduct.value = {
      name: '',
      description: '',
      price: '',
      category: Category.FOOD,
      payer: null,
      consumers: [],
      latitude: null,
      longitude: null
    };
    showToast('Dodano produkt', 'success');
  } catch (error) {
    console.error('Błąd dodawania produktu:', error);
    alert('Nie udało się dodać produktu');
  }
};

const updateProduct = async () => {
  if (!editingProduct.value) return;
  
  // Czyszczenie poprzednich błędów
  editProductFormErrors.value = {};
  let hasErrors = false;

  // Walidacja konsumentów
  if (!editingProduct.value.consumers || editingProduct.value.consumers.length === 0) {
    editProductFormErrors.value.consumers = 'Wybierz co najmniej jednego konsumenta';
    hasErrors = true;
  }

  if (hasErrors) {
    return;
  }

  try {
    await fractiService.updateProduct(editingProduct.value.id, {
      name: editingProduct.value.name,
      description: editingProduct.value.description,
      price: editingProduct.value.price,
      category: editingProduct.value.category,
      consumers: editingProduct.value.consumers,
      purchaser: editingProduct.value.purchaser,
      latitude: editingProduct.value.latitude,
      longitude: editingProduct.value.longitude
    });
    await loadSettlement();
    showEditProductModal.value = false;
    editProductFormErrors.value = {};
  } catch (e) {
    console.error('Błąd aktualizacji produktu:', e);
    alert('Nie udało się zaktualizować produktu');
  }
};


const deleteLooseProduct = () => {
  if (!editingProduct.value) return;


  openConfirmModal(
    'Usunąć produkt?',
    `Czy na pewno chcesz trwale usunąć "${editingProduct.value.name}"?`,
    async () => {
      // To jest logika, która wykona się dopiero po potwierdzeniu
      if (!editingProduct.value) return;
      try {
        await fractiService.deleteProduct(editingProduct.value.id);
        showEditProductModal.value = false; // Zamknij modal edycji
        editingProduct.value = null;
        await loadSettlement();
        showToast('Usunięto produkt', 'success');
      } catch (e) {
        console.error('Błąd usuwania produktu:', e);
        alert('Wystąpił błąd podczas usuwania.');
      }
    }
  );
};

const updateReceipt = async () => {
  if (!editingReceipt.value) return;

  editReceiptErrors.value = {};
  let hasErrors = false;

  if (!editingReceipt.value.merchant_name || editingReceipt.value.merchant_name.trim() === '') {
    showToast('Podaj nazwę sklepu', 'error');
    return;
  }

  if (editingReceipt.value.products) {
    editingReceipt.value.products.forEach(prod => {
      if (!prod.consumers || prod.consumers.length === 0) {
        editReceiptErrors.value[prod.id] = 'Przypisz konsumentów!';
        hasErrors = true;
      }
    });
  }

  if (hasErrors) {
    showToast('Uzupełnij brakujących konsumentów na liście', 'error');
    return;
  }

  try {
    const purchaseDateForApi = editingReceipt.value.purchase_date
      ? new Date(editingReceipt.value.purchase_date).toISOString()
      : undefined;

    const calculatedTotal = calculatedReceiptTotal.value;

    await fractiService.updateReceipt(editingReceipt.value.id, {
      merchant_name: editingReceipt.value.merchant_name,
      description: editingReceipt.value.description,
      total_amount: calculatedTotal.toString(),
      purchase_date: purchaseDateForApi,
      purchaser: editingReceipt.value.purchaser,
      latitude: editingReceipt.value.latitude,
      longitude: editingReceipt.value.longitude
    });

    await loadSettlement();
    showEditReceiptModal.value = false;
    showToast('Zapisano pomyślnie', 'success');

    const refreshedReceipt = settlement.value?.receipts?.find(r => r.id === editingReceipt.value?.id);
    if (refreshedReceipt) {
      const srcDate = refreshedReceipt.purchase_date || new Date().toISOString();
      editingReceipt.value = { ...refreshedReceipt, purchase_date: toDatetimeLocal(srcDate as any) };
    }
  } catch (e) {
    console.error('Błąd aktualizacji paragonu:', e);
    showToast('Nie udało się zaktualizować paragonu', 'error');
  }
};

const openConfirmModal = (title: string, subTitle: string, action: () => Promise<void>) => {
  confirmMessage.value = title;
  confirmSubMessage.value = subTitle;
  pendingDeleteAction.value = action;
  showConfirmModal.value = true;
};
const handleConfirmDelete = async () => {
  if (pendingDeleteAction.value) {
    await pendingDeleteAction.value();
  }
  showConfirmModal.value = false;
  pendingDeleteAction.value = null;
};
// NOWA FUNKCJA USUWANIA PARAGONU
const deleteReceipt = async () => {
 if (!editingReceipt.value) return;

  openConfirmModal(
    'Usunąć paragon?',
    'Zostanie usunięty paragon oraz WSZYSTKIE przypisane do niego pozycje. Tej operacji nie można cofnąć.',
    async () => {
      if (!editingReceipt.value) return;
      try {
        await fractiService.deleteReceipt(editingReceipt.value.id);
        showEditReceiptModal.value = false; // Zamknij modal edycji
        editingReceipt.value = null;
        await loadSettlement();
        showToast('Usunięto paragon', 'success');
      } catch (e) {
        console.error('Błąd usuwania paragonu:', e);
        alert('Wystąpił błąd podczas usuwania.');
      }
    }
  );
};

const openReceiptItemModal = (item: Product | null, receiptId: number) => {
  currentReceiptId.value = receiptId;
  editingReceiptItem.value = item;
  if (item && editReceiptErrors.value[item.id]) {
    delete editReceiptErrors.value[item.id];
  }
  if (item) {
    // Edycja istniejącej pozycji
    receiptItemForm.value = {
      name: item.name,
      price: item.price.toString(),
      category: item.category,
      consumers: [...item.consumers]
    };
  } else {
    // Nowa pozycja - bez domyślnych konsumentów
    receiptItemForm.value = {
      name: '',
      price: '',
      category: Category.FOOD,
      consumers: []
    };
  }
  showReceiptItemModal.value = true;
};

const saveReceiptItem = async () => {
  if (!currentReceiptId.value) return;

  try {
    const payload = {
      name: receiptItemForm.value.name,
      price: parseFloat(receiptItemForm.value.price),
      category: receiptItemForm.value.category,
      consumers: receiptItemForm.value.consumers
    };

    if (editingReceiptItem.value) {
      // UPDATE istniejącego
      await fractiService.updateReceiptItem(editingReceiptItem.value.id, payload);
    } else {
      // TWORZENIE nowego
      await fractiService.addReceiptItem(currentReceiptId.value, payload);
    }

    await loadSettlement();

    // Odśwież lokalny stan edytowanego paragonu
    const refreshedReceipt = settlement.value?.receipts?.find(r => r.id === currentReceiptId.value);
    if (refreshedReceipt) {
      editingReceipt.value = { ...refreshedReceipt };

      // Automatycznie zaktualizuj total_amount paragonu jako sumę produktów
      const newTotal = refreshedReceipt.products?.reduce((sum, p) => sum + parseFloat(p.price.toString() || '0'), 0) || 0;
      await fractiService.updateReceipt(currentReceiptId.value, {
        total_amount: newTotal.toString()
      });
      await loadSettlement();
    }

    showReceiptItemModal.value = false;
  } catch (e) {
    console.error('Błąd zapisu pozycji:', e);
    alert('Nie udało się zapisać pozycji');
  }
};

const deleteReceiptItem = async (itemId: number) => {
  openConfirmModal(
    'Usunąć pozycję?',
    'Pozycja zniknie z tego paragonu.',
    async () => {
        try {
          await fractiService.deleteReceiptItem(itemId);
          await loadSettlement();
          if (editingReceipt.value) {
            editingReceipt.value.products = editingReceipt.value.products.filter(p => p.id !== itemId);

            // Automatycznie zaktualizuj total_amount paragonu jako sumę produktów
            const newTotal = editingReceipt.value.products?.reduce((sum, p) => sum + parseFloat(p.price.toString() || '0'), 0) || 0;
            await fractiService.updateReceipt(editingReceipt.value.id, {
              total_amount: newTotal.toString()
            });
            await loadSettlement();
          }
          showToast('Usunięto pozycję', 'success');
        } catch (e) {
          console.error(e);
        }
    }
  );
};

const loadSettlement = async () => {
  const settlementId = route.params.id as string;
  if (!settlementId) return;

  try {
    loading.value = true;
    settlement.value = await fractiService.getSettlementDetails(settlementId);
  } catch (error) {
    console.error('Błąd ładowania rozliczenia:', error);
  } finally {
    loading.value = false;
  }
};

// --- WATCHERS - Kontrola scrollu body'ego gdy modal jest otwarty ---
const isAnyModalOpen = () => {
  return showAddProductModal.value || showAddUserModal.value || showEditProductModal.value || 
         showEditReceiptModal.value || showReceiptItemModal.value || showConfirmModal.value || 
         showAddGuestModal.value;
};

watch(
  [showAddProductModal, showAddUserModal, showEditProductModal, showEditReceiptModal, 
   showReceiptItemModal, showConfirmModal, showAddGuestModal],
  () => {
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
  }
);

onMounted(() => {
  loadSettlement();
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
.details-container {
  flex: 1;
  background: var(--gradient-page-dark);
  color: var(--text-primary);
}

/* Header */
.header {
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  padding: 1.5rem 2rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.back-btn {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #a78bfa;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition-fast);
}

.back-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

.header-info {
  flex: 1;
}

.header-info h1 {
  background: var(--gradient-card);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.total-cost {
  font-size: 1.1rem;
  color: var(--text-secondary);
}

.total-cost .amount {
  font-size: 1.5rem;
  font-weight: 700;
  background: var(--gradient-button);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Content Split */
.content-split {
  display: flex;
  min-height: calc(100vh - 120px);
}

/* Left Column - 60% */
.left-column {
  flex: 0 0 60%;
  padding: var(--spacing-lg);
  overflow-y: auto;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.timeline-header h2 {
  color: #f3f4f6;
  font-size: 1.5rem;
  margin: 0;
}

.timeline-header .count {
  background: rgba(139, 92, 246, 0.2);
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.9rem;
  color: #c4b5fd;
}

/* Timeline Items */
.timeline {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.timeline-item {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  overflow: hidden;
  transition: var(--transition-normal);
}

.timeline-item:hover {
  border-color: rgba(139, 92, 246, 0.4);
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.2);
}

.timeline-item.is-expanded {
  border-color: rgba(139, 92, 246, 0.5);
  background: rgba(139, 92, 246, 0.08);
}

.item-main {
  display: flex;
  align-items: center;
  padding: 1.25rem;
  cursor: pointer;
  gap: var(--spacing-md);
}

.item-icon {
  font-size: 2rem;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 10px;
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #f3f4f6;
  margin-bottom: 0.25rem;
}

.item-meta {
  display: flex;
  gap: var(--spacing-md);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.item-amount {
  font-size: 1.3rem;
  font-weight: 700;
  color: #a78bfa;
  margin-right: 1rem;
}

.expand-btn {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: var(--text-primary);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.expand-btn:hover {
  background: rgba(139, 92, 246, 0.3);
}

/* Receipt Products */
.receipt-products {
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(139, 92, 246, 0.2);
  padding: 0.5rem;
}

.product-item {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  margin: 0.5rem;
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 8px;
  transition: var(--transition-fast);
}

.product-item:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
}

.product-info {
  flex: 1;
}

.product-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.product-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.product-meta .category-tag,
.product-meta .consumers-tag {
  background: rgba(139, 92, 246, 0.15);
  padding: 2px 8px;
  border-radius: 6px;
  color: #c4b5fd;
}

.product-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.product-amount {
  font-weight: 600;
  color: #a78bfa;
  font-size: 1.1rem;
}

.edit-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-fast);
  font-size: 0.9rem;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: var(--text-primary);
}

.edit-icon-btn:hover {
  background: var(--color-purple);
  color: white;
  border-color: var(--color-purple);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
}

/* Right Column - 40% */
.right-column {
  flex: 0 0 40%;
  background: rgba(0, 0, 0, 0.2);
  border-left: 1px solid rgba(139, 92, 246, 0.2);
  padding: var(--spacing-lg);
  overflow-y: auto;
}

/* Action Panel */
.action-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.action-btn {
  padding: 12px 20px;
  border-radius: 10px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-normal);
  text-align: left;
  font-size: 1rem;
}

.map-btn {
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.map-btn:hover {
  background: rgba(99, 102, 241, 0.3);
  transform: translateX(5px);
}

.receipt-btn {
  background: rgba(168, 85, 247, 0.15);
  color: #c4b5fd;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.receipt-btn:hover {
  background: rgba(168, 85, 247, 0.25);
  transform: translateX(5px);
}

.product-btn {
  background: rgba(139, 92, 246, 0.15);
  color: #c4b5fd;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.product-btn:hover {
  background: rgba(139, 92, 246, 0.25);
  transform: translateX(5px);
}

/* Users Section */
.users-section {
  margin-top: 2rem;
}

.users-section h3 {
  color: #a78bfa;
  font-size: 1.2rem;
  margin-bottom: 1rem;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: 1rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: 1rem;
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  transition: var(--transition-fast);
}

.user-card:hover {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.3);
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--gradient-button);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.user-info {
  flex: 1;
}

.user-name {
  font-weight: 600;
  color: #f3f4f6;
  margin-bottom: 0.5rem;
}

.user-balance {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
}

.user-balance .paid {
  color: var(--text-secondary);
}

.user-balance .owes {
  font-weight: 600;
}

.user-balance .positive {
  color: var(--color-green-light);
}

.user-balance .negative {
  color: #f87171;
}

/* Sekcja zobowiązań */
.debts-section {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: var(--gradient-card-ultra-subtle);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
}

.debts-section h3 {
  color: #c4b5fd;
  font-size: 1.3rem;
  margin-bottom: 1.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.debts-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.debt-item {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: var(--gradient-overlay-dark);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 10px;
  transition: var(--transition-normal);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.debt-item > .debt-amount-box {
  grid-column: 1 / 2;
}

.debt-item > .settle-btn {
  grid-column: 2 / 4;
}

.debt-row-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.debt-row-bottom {
  display: flex;
  gap: 10px;
  width: 100%;
}

.debt-item:hover {
  background: var(--gradient-overlay-darker);
  border-color: rgba(139, 92, 246, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.2);
}

.debt-from-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.debt-to-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-direction: row-reverse;
}

.user-avatar-small {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--gradient-button);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.debt-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
  min-width: 80px;
}

.debt-from-user .debt-name {
  color: #fca5a5;
}

.debt-to-user .debt-name {
  color: #86efac;
}

.debt-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-self: center;
  gap: 2px;
}

.arrow-icon {
  font-size: 1.2rem;
  color: var(--text-secondary);
  font-weight: bold;
}

.action-label {
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.debt-amount-box {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: var(--gradient-warning);
  padding: 0.5rem;
  border-radius: 10px;
  border: 2px solid rgba(245, 158, 11, 0.4);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.2);
  transition: var(--transition-fast);
  cursor: default;
  min-height: 50px;
}

.debt-amount {
  font-weight: 800;
  color: #fbbf24;
  font-size: 1.4rem;
}

.debt-currency {
  font-weight: 600;
  color: #fcd34d;
  font-size: 0.95rem;
}

.empty-state {
  padding: 1rem;
  text-align: center;
  color: var(--color-green-light);
  font-weight: 600;
}

.add-user-btn {
  width: 100%;
  padding: 12px;
  background: rgba(139, 92, 246, 0.1);
  border: 1px dashed rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: var(--transition-fast);
  margin-top: 1rem;
}

.add-user-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

.modal-content {
  width: 90vw;
  max-width: 500px;
  box-sizing: border-box;
}

.code-display {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  background: rgba(0, 0, 0, 0.3);
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  margin-bottom: 1.5rem;
}

.code-display .code {
  flex: 1;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-purple);
  letter-spacing: 2px;
  font-family: monospace;
}

.copy-btn {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: var(--transition-fast);
  white-space: nowrap;
}

.copy-btn:hover {
  background: rgba(139, 92, 246, 0.3);
  border-color: rgba(139, 92, 246, 0.5);
}

.location-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.location-inputs input {
  width: 100%;
}

/* Form - użyj globalnych styli z App.vue */

.hint {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #6b7280;
}

/* Modal actions - użyj globalnych styli */

/* Responsive */
@media (max-width: 1024px) {
  .content-split {
    flex-direction: column;
  }

  .left-column,
  .right-column {
    flex: 1 1 100%;
  }

  .right-column {
    border-left: none;
    border-top: 1px solid rgba(139, 92, 246, 0.2);
  }
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .header {
    padding: 1rem;
    gap: var(--spacing-md);
    flex-direction: column;
    align-items: flex-start;
  }

  .header-info h1 {
    font-size: 1.5rem;
  }

  .header-info {
    width: 100%;
  }

  .content-split {
    flex-direction: column;
    min-height: auto;
  }

  .left-column,
  .right-column {
    flex: 1 1 100%;
    padding: 1.5rem 1rem;
  }

  .right-column {
    border-left: none;
    border-top: 1px solid rgba(139, 92, 246, 0.2);
  }

  .timeline-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .timeline-header h2 {
    font-size: 1.2rem;
  }

  .item-main {
    padding: 1rem;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  .item-icon {
    font-size: 1.5rem;
    width: 40px;
    height: 40px;
  }

  .item-info {
    min-width: 0;
  }

  .item-name {
    font-size: 1rem;
  }

  .item-meta {
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.75rem;
  }

  .item-right-panel {
    width: 100%;
    justify-content: space-between;
    margin-top: 0.5rem;
  }

  .item-amount {
    margin-right: 0;
    font-size: 1.1rem;
  }

  .action-panel {
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .action-btn {
    padding: 10px 16px;
    font-size: 0.9rem;
  }

  .users-section {
    margin-top: 1.5rem;
  }

  .user-card {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  .user-avatar {
    width: 40px;
    height: 40px;
    font-size: 1.2rem;
    flex-shrink: 0;
  }

  .user-info {
    min-width: 0;
  }

  .user-name {
    font-size: 0.95rem;
    margin-bottom: 0.25rem;
  }

  .user-balance {
    font-size: 0.75rem;
    gap: 0.15rem;
  }

  .remove-user-btn {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
    margin-left: auto;
  }

  .debts-section {
    margin-top: 1rem;
    padding: 1rem;
  }

  .debts-section h3 {
    font-size: 1.1rem;
  }

  .debt-item {
    grid-template-columns: 1fr;
    gap: 0.75rem;
    padding: 0.75rem;
  }

  .debt-from-user,
  .debt-to-user {
    width: 100%;
    justify-content: space-between;
  }

  .debt-center {
    flex-direction: row;
    gap: 0.5rem;
    width: 100%;
    justify-content: center;
    padding: 0.5rem 0;
    border-top: 1px solid rgba(139, 92, 246, 0.2);
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
  }

  .action-label {
    display: none;
  }

  .arrow-icon {
    font-size: 1rem;
  }

  .user-avatar-small {
    width: 32px;
    height: 32px;
    font-size: 0.85rem;
  }

  .debt-name {
    font-size: 0.9rem;
    min-width: 60px;
  }

  .debt-amount-box {
    width: 100%;
    justify-content: center;
    gap: 6px;
    padding: 0.6rem;
  }

  .debt-amount {
    font-size: 1.2rem;
  }

  .debt-currency {
    font-size: 0.85rem;
  }

  .product-item {
    flex-wrap: wrap;
    padding: 0.5rem 0.75rem;
    margin: 0.25rem;
  }

  .product-info {
    width: 100%;
  }

  .product-name {
    font-size: 0.95rem;
  }

  .product-meta {
    font-size: 0.7rem;
    gap: 0.25rem;
  }

  .product-right {
    width: 100%;
    justify-content: space-between;
    margin-top: 0.5rem;
  }

  .product-amount {
    font-size: 1rem;
  }

  .modal-content {
    width: 90vw;
    max-width: 500px;
    max-height: 85vh;
    padding: 1.25rem;
    border-radius: 12px;
  }

  .modal-map {
    height: 150px;
  }

  .form-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .form-group {
    width: 100%;
  }

  .form-group.half {
    flex: 1 1 100%;
  }

  input[type="text"],
  input[type="email"],
  input[type="password"],
  input[type="number"],
  textarea,
  select {
    font-size: 16px;
  }

  .checkbox-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .add-user-btn {
    margin-top: 0.75rem;
    padding: 10px;
    font-size: 0.85rem;
  }

  .back-btn {
    padding: 6px 12px;
    font-size: 0.9rem;
  }
}

/* Extra small screens */
@media (max-width: 480px) {
  .header {
    padding: 0.75rem;
  }

  .header-info h1 {
    font-size: 1.25rem;
  }

  .left-column,
  .right-column {
    padding: 1rem 0.75rem;
  }

  .timeline-header h2 {
    font-size: 1rem;
  }

  .item-main {
    padding: 0.75rem;
  }

  .item-name {
    font-size: 0.95rem;
  }

  .item-amount {
    font-size: 1rem;
  }

  .action-btn {
    padding: 8px 12px;
    font-size: 0.8rem;
  }

  .user-name {
    font-size: 0.9rem;
  }

  .product-item {
    padding: 0.4rem 0.6rem;
    margin: 0.15rem;
  }

  .product-name {
    font-size: 0.9rem;
  }

  .debt-item {
   padding: 0.75rem;
    gap: 0.75rem;
  }

  .debt-row-top {
    font-size: 0.9rem;
  }

  .debt-from-user,
  .debt-to-user {
    width: 100%;
    gap: 0.5rem;
  }

  .debt-amount-box, .settle-btn {
    min-height: 45px;
    font-size: 1.1rem;
  }

  .user-avatar-small {
    width: 28px;
    height: 28px;
    font-size: 0.8rem;
  }

  .debt-name {
    font-size: 0.85rem;
    min-width: 50px;
  }

  .debt-center {
    flex-direction: row;
    gap: 0.3rem;
    padding: 0.4rem 0;
  }

  .arrow-icon {
    font-size: 0.9rem;
  }

  .debt-amount-box {
    width: 100%;
    padding: 0.5rem;
  }

  .debt-amount {
    font-size: 1.1rem;
  }

  .debt-currency {
    font-size: 0.8rem;
  }

  .modal-content {
    width: 95vw;
    max-width: 95vw;
    padding: 0.75rem;
    max-height: 80vh;
    border-radius: 10px;
  }

  .modal-map {
    height: 120px;
  }

  .form-group {
    margin-bottom: 0.8rem;
  }

  .form-group label {
    font-size: 0.85rem;
  }

  input[type="text"],
  input[type="email"],
  input[type="password"],
  input[type="number"],
  textarea,
  select {
    padding: 8px 10px;
    font-size: 14px;
    max-width: 100%;
  }

  .modal-actions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .modal-actions button {
    width: 100%;
    padding: 8px;
    font-size: 0.85rem;
  }

  .checkbox-group label {
    font-size: 0.85rem;
    padding: 0.4rem 0;
  }
}
select {
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a78bfa' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1em;
  padding-right: 2.5rem; /* Miejsce na strzałkę */
  cursor: pointer;
}


select option {
  background-color: #1e1b4b;
  color: var(--text-primary);
  padding: 10px;
}
.item-right-panel {
  display: flex;
  align-items: center;
  gap: 0.75rem; /* Odstęp między ceną a guzikami */
}

/* Wspólny styl dla guzików akcji (Ołówek i Strzałka) */
.action-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-fast);
  font-size: 1rem;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: var(--text-primary);
  transition: var(--transition-fast);
}


.action-icon-btn.edit:hover {
  background: var(--color-purple); /* Fioletowy po najechaniu */
  color: white;
  border-color: var(--color-purple);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
}


.action-icon-btn.expand:hover {
  background: rgba(139, 92, 246, 0.25);
  border-color: rgba(139, 92, 246, 0.5);
}
.expand-btn {
  display: none;
}

/* Map Styles */
.modal-map {
  height: 200px;
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  margin-top: 0.5rem;
  z-index: 1;
}

.coords-display {
  font-size: 0.8rem;
  color: #a78bfa;
  margin-top: 4px;
  text-align: right;
}

.form-row {
  display: flex;
  gap: var(--spacing-md);
}

.form-group.half {
  flex: 1;
}

/* --- STYLE DLA MODALA EDYCJI PARAGONU --- */
.modal-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.modal-section-title {
  color: #a78bfa;
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.modal-divider {
  border: 0;
  border-top: 1px solid rgba(139, 92, 246, 0.3);
  margin: 1.5rem 0;
}

.add-item-btn {
  background: rgba(139, 92, 246, 0.2);
  border: 1px dashed rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: var(--transition-fast);
}

.add-item-btn:hover {
  background: rgba(139, 92, 246, 0.3);
  color: white;
}

/* Lista pozycji w modalu */
.receipt-items-list {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.receipt-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.receipt-list-item:last-child {
  border-bottom: none;
}

.r-item-info {
  flex: 1;
}

.r-item-name {
  color: var(--text-primary);
  font-weight: 500;
}

.r-item-meta {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.r-item-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 30px;
  height: 30px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  transition: var(--transition-fast);
}

.icon-btn.edit {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.icon-btn.delete {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.icon-btn:hover {
  filter: brightness(1.2);
  transform: scale(1.05);
}

.empty-list {
  padding: 20px;
  text-align: center;
  color: #6b7280;
  font-style: italic;
}

.full-width {
  width: 100%;
}

.mt-4 {
  margin-top: 1rem;
}

/* Z-INDEX dla zagnieżdżonego modala */
.z-high {
  z-index: 200 !important;
  background: rgba(0,0,0,0.85);
}

/* Box z obliczoną sumą */
.calculated-total-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--gradient-card-subtle);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 10px;
  padding: 15px 20px;
  margin-top: 1rem;
  gap: var(--spacing-md);
}

.calc-label {
  color: #9ca3af;
  font-size: 0.9rem;
  font-weight: 500;
}

.calc-value {
  flex: 1;
  text-align: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: 0.5px;
}

.sync-btn {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: var(--transition-fast);
  white-space: nowrap;
}

.sync-btn:hover {
  background: var(--gradient-button);
  color: white;
  border-color: var(--color-purple);
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}

.right-actions {
  display: flex;
  gap: var(--spacing-md);
}

.modal-content .modal-actions.space-between {
  display: flex;
  gap: var(--spacing-md);
  align-items: center;
}
.modal-content .modal-actions.space-between > .danger-btn,
.modal-content .modal-actions.space-between .right-actions > button {
  flex: 1 1 0;
  min-width: 0;
}
.modal-content .modal-actions.space-between > .danger-btn,
.modal-content .modal-actions.space-between .right-actions > button,
.modal-content .modal-actions.space-between > button {
  height: 44px;
  padding: 10px 12px;
  box-sizing: border-box;
}
.modal-content .modal-actions.space-between .right-actions {
  display: flex;
  gap: var(--spacing-md);
}

.modal-content .modal-actions.equal-buttons {
  display: flex;
  gap: var(--spacing-md);
}
.modal-content .modal-actions.equal-buttons > button {
  flex: 1 1 0;
  min-width: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 12px;
  height: 44px;
  box-sizing: border-box;
}

.settlement-description {
  color: #9ca3af;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
  max-width: 600px;
  line-height: 1.5;
  font-style: italic;
}
user-actions-row {
  display: flex;
  gap: 10px;
  margin-top: 1rem;
}

.add-user-btn, .add-guest-btn {
  flex: 1;
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: var(--transition-fast);
  font-size: 0.9rem;
}

.add-user-btn {
  background: rgba(139, 92, 246, 0.1);
  border: 1px dashed rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
}
.add-user-btn:hover {
  background: rgba(139, 92, 246, 0.2);
}
.remove-user-btn {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  transition: var(--transition-fast);
  margin-left: 10px;
}

.remove-user-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: #ef4444;
  color: #fff;
  transform: scale(1.05);
}

.form-group.has-error input,
.form-group.has-error select,
.form-group.has-error textarea {
  border-color: #ef4444 !important;
  border-width: 2px !important;
  background-color: rgba(239, 68, 68, 0.05);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  transition: var(--transition-fast);
}

.form-group.has-error input:focus,
.form-group.has-error select:focus,
.form-group.has-error textarea:focus {
  outline: none;
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2);
}

.error-text {
  display: block;
  color: #ef4444;
  font-size: 0.85rem;
  margin-top: 4px;
  font-weight: 500;
  animation: slideDown 0.3s ease-out;
}



.form-group.has-error label {
  color: #fca5a5;
}

.checkbox-group.has-error {
  border: 2px solid #ef4444;
  border-radius: 8px;
  padding: 12px;
  background-color: rgba(239, 68, 68, 0.05);
}

.settle-btn {
  flex: 1;
  min-width: 0;
  background: var(--gradient-success-light);
  border: 2px solid rgba(34, 197, 94, 0.5);
  color: #86efac;
  padding: 1rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  transition: var(--transition-fast);
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
  min-height: 50px;
  box-sizing: border-box;
  margin: 0;
}

.settle-btn:hover {
  background: var(--gradient-success);
  border-color: var(--color-green);
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(34, 197, 94, 0.4);
}

.settle-btn:active {
  transform: scale(0.95);
}

.settled-debts-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--gradient-success-ultra-subtle);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 12px;
}

.settled-debts-section h3 {
  color: #86efac;
  font-size: 1.3rem;
  margin-bottom: 1.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.settled-debts-list {
  display: grid;
  gap: 12px;
}

.settled-debt-item {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto auto;
  gap: 0.75rem;
  padding: 12px;
  background: rgba(34, 197, 94, 0.05);
  border: 1px solid rgba(34, 197, 94, 0.15);
  border-radius: 8px;
  transition: var(--transition-fast);
}

.settled-debt-item > .settled-debt-date {
  grid-column: 1 / 2;
  grid-row: 2;
}

.settled-debt-item > .settled-debt-amount-box {
  grid-column: 2 / 3;
  grid-row: 2;
}

.settled-debt-item > .undo-settle-btn {
  grid-column: 3 / 4;
  grid-row: 2;
}

.settled-debt-item:hover {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
}

.settled-debt-from-user,
.settled-debt-to-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.settled-debt-from-user {
  justify-content: flex-start;
}

.settled-debt-to-user {
  justify-content: flex-end;
}

.settled-debt-name {
  font-size: 0.9rem;
  color: #d1d5db;
  font-weight: 500;
}

.settled-debt-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.settled-debt-amount-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: var(--gradient-success-ultra-subtle);
  padding: 1rem;
  border-radius: 10px;
  border: 2px solid rgba(34, 197, 94, 0.3);
  box-shadow: 0 2px 8px rgba(34, 197, 94, 0.2);
  min-height: 50px;
}

.settled-debt-amount {
  font-size: 1.2rem;
  font-weight: 700;
  color: #86efac;
}

.settled-debt-currency {
  font-size: 0.75rem;
  color: #6ee7b7;
  font-weight: 500;
}

.settled-debt-date {
  font-size: 0.85rem;
  color: #9ca3af;
  text-align: center;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient-card-subtle);
  padding: 1rem;
  border-radius: 10px;
  border: 2px solid rgba(139, 92, 246, 0.3);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.15);
  min-height: 50px;
  font-weight: 600;
}

.undo-settle-btn {
  background: var(--gradient-success-light);
  border: 2px solid rgba(239, 68, 68, 0.5);
  color: #fca5a5;
  padding: 1rem;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: var(--transition-fast);
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
  min-height: 50px;
  transition: var(--transition-fast);
}

.undo-settle-btn:hover {
  background: var(--gradient-success);
  border-color: #ef4444;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
}

.undo-settle-btn:active {
  transform: scale(0.95);
}
</style>