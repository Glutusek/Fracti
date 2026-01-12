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
              <div class="user-avatar">{{ member.username.charAt(0).toUpperCase() }}</div>
              <div class="user-info">
                <div class="user-name">{{ member.first_name ? member.first_name : member.username }}</div>
                <div class="user-balance">
                  <span class="paid">Zapłacił: {{ formatMoney(getUserPaid(member.id)) }} zł</span>
                  <span class="owes" :class="getUserBalance(member.id) >= 0 ? 'positive' : 'negative'">
                    {{ getUserBalance(member.id) >= 0 ? 'Zwrot: ' : 'Do oddania: ' }}
                    {{ formatMoney(Math.abs(getUserBalance(member.id))) }} zł
                  </span>
                </div>
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
              <input v-model="newProduct.price" type="number" step="0.01" min="0" required />
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

          <div class="form-group">
            <label>Płatnik</label>
            <select v-model="newProduct.payer" required>
              <option :value="null" disabled>Wybierz płatnika</option>
              <option v-for="member in settlement?.members" :key="member.id" :value="member.id">
                {{ member.username }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Konsumenci</label>
            <div class="checkbox-group">
              <label v-for="member in settlement?.members" :key="member.id">
                <input type="checkbox" :value="member.id" v-model="newProduct.consumers" />
                {{ member.username }}
              </label>
            </div>
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
            <label>Konsumenci</label>
            <div class="checkbox-group">
              <label v-for="member in settlement?.members" :key="member.id">
                <input type="checkbox" :value="member.id" v-model="editingProduct.consumers" />
                {{ member.username }}
              </label>
            </div>
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
              <option v-for="member in settlement?.members" :key="member.id" :value="member.id">{{ member.username }}</option>
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
            >
              <div class="r-item-info">
                <div class="r-item-name">{{ prod.name }}</div>
                <div class="r-item-meta">
                  {{ formatMoney(prod.price) }} zł • {{ prod.consumers.length }} os.
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
              <input v-model="receiptItemForm.price" type="number" step="0.01" min="0" required />
            </div>
            <div class="form-group half">
              <label>Kategoria</label>
              <select v-model="receiptItemForm.category">
                <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Kto to zjadł?</label>
            <div class="checkbox-group">
              <label v-for="member in settlement?.members" :key="member.id">
                <input type="checkbox" :value="member.id" v-model="receiptItemForm.consumers" />
                {{ member.username }}
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
import { ref, computed, onMounted, nextTick } from 'vue';
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

const categories = fractiService.getCategoriesOptionList();

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
      payerId: product.consumers[0] || 0 // First consumer as payer
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
  router.push('/ocr-upload');
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

  // Sum from receipts
  settlement.value.receipts?.forEach(receipt => {
    if (receipt.purchaser === userId) {
      total += parseFloat(receipt.total_amount || '0');
    }
  });

  // Sum from loose products (where user is first consumer/payer)
  settlement.value.loose_products?.forEach(product => {
    if (product.consumers[0] === userId) {
      total += parseFloat(product.price || '0');
    }
  });

  return total;
};

const getUserBalance = (userId: number): number => {
  // Simplified calculation - should be more complex in production
  const paid = getUserPaid(userId);
  const totalExpenses = parseFloat(settlement.value?.total_expenses || '0');
  const membersCount = settlement.value?.members?.length || 1;
  const shouldPay = totalExpenses / membersCount;

  return paid - shouldPay;
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
  try {
    if (!newProduct.value.payer) {
      alert('Wybierz płatnika');
      return;
    }

    await fractiService.addLooseProduct({
      name: newProduct.value.name,
      description: newProduct.value.description,
      price: newProduct.value.price,
      category: newProduct.value.category,
      consumers: newProduct.value.consumers,
      latitude: newProduct.value.latitude,
      longitude: newProduct.value.longitude,
      settlement: settlement.value?.id
    });

    await loadSettlement();
    showAddProductModal.value = false;
    showToast('Dodano produkt', 'success');
  } catch (error) {
    console.error('Błąd dodawania produktu:', error);
    alert('Nie udało się dodać produktu');
  }
};

const updateProduct = async () => {
  if (!editingProduct.value) return;
  try {
    await fractiService.updateProduct(editingProduct.value.id, {
      name: editingProduct.value.name,
      description: editingProduct.value.description,
      price: editingProduct.value.price,
      category: editingProduct.value.category,
      consumers: editingProduct.value.consumers,
      latitude: editingProduct.value.latitude,
      longitude: editingProduct.value.longitude
    });
    await loadSettlement();
    showEditProductModal.value = false;
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
  try {
    const purchaseDateForApi = editingReceipt.value.purchase_date
      ? new Date(editingReceipt.value.purchase_date).toISOString()
      : undefined;

    // Automatyczne ustawienie total_amount jako suma produktów
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
    alert('Nie udało się zaktualizować paragonu');
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

  if (item) {
    // Edycja istniejącej pozycji
    receiptItemForm.value = {
      name: item.name,
      price: item.price.toString(),
      category: item.category,
      consumers: [...item.consumers]
    };
  } else {
    // Nowa pozycja - domyślnie wszyscy uczestnicy
    receiptItemForm.value = {
      name: '',
      price: '',
      category: Category.FOOD,
      consumers: settlement.value?.members?.map(m => m.id) || []
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

onMounted(() => {
  loadSettlement();
});
</script>

<style scoped>
.details-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
  color: #e5e7eb;
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
  transition: all 0.2s;
}

.back-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

.header-info {
  flex: 1;
}

.header-info h1 {
  background: linear-gradient(135deg, #ffffff 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
}

.total-cost {
  font-size: 1.1rem;
  color: #9ca3af;
}

.total-cost .amount {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
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
  padding: 2rem;
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
  gap: 1rem;
}

.timeline-item {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
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
  gap: 1rem;
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
  gap: 1rem;
  font-size: 0.85rem;
  color: #9ca3af;
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
  color: #e5e7eb;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
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
  transition: all 0.2s;
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
  color: #e5e7eb;
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
  transition: all 0.2s;
  font-size: 0.9rem;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: #e5e7eb;
}

.edit-icon-btn:hover {
  background: #8b5cf6;
  color: white;
  border-color: #8b5cf6;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
}

/* Right Column - 40% */
.right-column {
  flex: 0 0 40%;
  background: rgba(0, 0, 0, 0.2);
  border-left: 1px solid rgba(139, 92, 246, 0.2);
  padding: 2rem;
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
  transition: all 0.3s;
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
  gap: 1rem;
  margin-bottom: 1rem;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 12px;
  transition: all 0.2s;
}

.user-card:hover {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.3);
}

.user-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
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
  color: #9ca3af;
}

.user-balance .owes {
  font-weight: 600;
}

.user-balance .positive {
  color: #4ade80;
}

.user-balance .negative {
  color: #f87171;
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
  transition: all 0.2s;
  margin-top: 1rem;
}

.add-user-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
}

.modal-content {
  width: 500px;
}

.code-display {
  display: flex;
  align-items: center;
  gap: 1rem;
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
  color: #8b5cf6;
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
  transition: all 0.2s;
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
  color: #e5e7eb;
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
  transition: all 0.2s;
  font-size: 1rem;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: rgba(139, 92, 246, 0.1);
  color: #e5e7eb;
}


.action-icon-btn.edit:hover {
  background: #8b5cf6; /* Fioletowy po najechaniu */
  color: white;
  border-color: #8b5cf6;
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
  gap: 1rem;
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
  transition: all 0.2s;
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
  color: #e5e7eb;
  font-weight: 500;
}

.r-item-meta {
  font-size: 0.85rem;
  color: #9ca3af;
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
  transition: all 0.2s;
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
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(99, 102, 241, 0.1) 100%);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 10px;
  padding: 15px 20px;
  margin-top: 1rem;
  gap: 1rem;
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
  transition: all 0.2s;
  white-space: nowrap;
}

.sync-btn:hover {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: white;
  border-color: #8b5cf6;
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}

.right-actions {
  display: flex;
  gap: 1rem;
}

.modal-content .modal-actions.space-between {
  display: flex;
  gap: 1rem;
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
  gap: 1rem;
}

.modal-content .modal-actions.equal-buttons {
  display: flex;
  gap: 1rem;
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
  flex: 1; /* Przyciski zajmą po połowie szerokości */
  padding: 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
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
</style>