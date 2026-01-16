<template>
  <div class="ocr-page">
    <div class="ocr-container">

      <div class="header">
        <button @click="goBack" class="back-btn">← Powrót</button>
        <h1>Nowy Paragon</h1>
      </div>

      <div class="section-card">
        <h2 class="section-title">1. Wybierz rozliczenie</h2>
        <div class="settlement-selector">
          <select v-model="selectedSettlementId" @change="handleSettlementChange">
            <option :value="null" disabled>-- Wybierz grupę --</option>
            <option v-for="s in settlements" :key="s.id" :value="s.id">{{ s.name }}</option>
            <option value="NEW_SETTLEMENT">➕ Utwórz nowe rozliczenie...</option>
          </select>
        </div>

        <div v-if="showNewSettlementForm" class="new-settlement-form fade-in">
          <h3>Nowa grupa rozliczeniowa</h3>
          <div class="form-group">
            <label>Nazwa</label>
            <input v-model="newSettlement.name" placeholder="np. Wyjazd Mazury" />
          </div>
          <div class="form-group">
            <label>Opis</label>
            <input v-model="newSettlement.description" placeholder="Opcjonalny opis" />
          </div>
          <div class="form-actions">
            <button @click="createSettlement" class="btn-primary small">Utwórz i wybierz</button>
            <button @click="cancelNewSettlement" class="btn-secondary small">Anuluj</button>
          </div>
        </div>
      </div>

      <div v-if="canEditForm" class="section-card fade-in">
        <h2 class="section-title">2. Dane Paragonu</h2>

        <div class="form-grid">
           <div class="form-group">
             <label>Sklep</label>
             <input v-model="receiptData.merchant_name" placeholder="Nazwa sklepu" />
           </div>

            <div class="form-group">
           <label>Opis (opcjonalnie)</label>
           <textarea
             v-model="receiptData.description"
             rows="2"
             placeholder="Dodatkowy opis, np. 'Wyjazd służbowy'"
           ></textarea>
            </div>


           <div class="form-row">
             <div class="form-group half">
               <label>Data</label>
               <input type="date" v-model="receiptData.purchase_date" />
             </div>
             <div class="form-group half">
               <label>Płatnik</label>
               <select v-model="receiptData.purchaser">
                 <option :value="null" disabled>Kto płacił?</option>
                 <option v-for="m in settlementMembers" :key="m.id" :value="m.id">{{ m.username }}</option>
               </select>
             </div>
           </div>


           <div class="form-group">
              <label>Lokalizacja (opcjonalnie)</label>
              <div id="map-ocr" class="mini-map"></div>
              <div class="coords-display" v-if="receiptData.latitude && receiptData.longitude">
                  📍 {{ receiptData.latitude.toFixed(5) }}, {{ receiptData.longitude.toFixed(5) }}
              </div>
           </div>
        </div>
      </div>

      <div v-if="canEditForm" class="section-card fade-in">
        <h2 class="section-title">3. Pozycje</h2>

        <div class="ocr-trigger-section">
            <input ref="fileInput" type="file" accept="image/*" hidden @change="handleFileSelect" />

            <button class="ocr-upload-btn" @click="triggerFileInput" :disabled="isAnalyzing">
                <span class="icon">📸</span>
                <div class="text-content">
                    <span class="main-text" v-if="!isAnalyzing">Wczytaj pozycje ze zdjęcia</span>
                    <span class="main-text" v-else>Analizowanie... ({{ pollingAttempts }})</span>
                    <span class="sub-text">Automatycznie odczytaj produkty i ceny</span>
                </div>
            </button>
        </div>

        <div class="products-manager">
          <div class="pm-header">
            <h3>Lista produktów ({{ receiptProducts.length }})</h3>
            <button @click="openProductModal(null)" class="btn-text">+ Dodaj ręcznie</button>
          </div>

          <div v-if="receiptProducts.length === 0" class="empty-products">
            Brak pozycji. Dodaj ręcznie lub zeskanuj paragon powyżej.
          </div>

          <div v-else class="products-list">
             <div v-for="(prod, idx) in receiptProducts" :key="idx" class="product-row">

                <div class="qty-badge" v-if="prod.quantity > 1 && isInteger(prod.quantity)">
                  {{ parseInt(prod.quantity) }}x
                </div>

                <div class="prod-info">
                   <div class="prod-name">
                     {{ prod.name }}
                     <span v-if="!isInteger(prod.quantity)" class="weight-label">
                       ({{ prod.quantity }} kg/l)
                     </span>
                   </div>
                   <div class="prod-cat">{{ getCategoryLabel(prod.category) }} • 👥 {{ prod.consumers.length }}</div>
                </div>

                <div class="prod-price">{{ prod.price.toFixed(2) }} zł</div>
                <div class="prod-actions">
                   <button @click="openProductModal(idx)" class="btn-mini edit">✏️</button>
                   <button @click="confirmRemoveProduct(idx)" class="btn-mini delete">🗑️</button>
                </div>
             </div>

             <div class="products-total">
                <span class="total-label">Suma:</span>
                <span class="total-value">{{ calculateTotal().toFixed(2) }} zł</span>
             </div>
          </div>
        </div>

        <div class="final-actions">
           <button @click="submitReceipt" class="btn-save" :disabled="isUploading">
              <span v-if="isUploading">Zapisywanie...</span>
              <span v-else>💾 Zapisz Paragon</span>
           </button>
        </div>
      </div>

    </div>

    <div v-if="showCropperModal" class="modal-overlay z-high">
       <div class="modal-content large">
          <h3>Przytnij paragon</h3>
          <p class="hint-text">Zaznacz obszar zawierający listę zakupów.</p>
          <cropper
            ref="cropperRef"
            class="cropper-container"
            :src="originalImageUrl"
            :stencil-props="{ aspectRatio: undefined }"
          />
          <div class="modal-actions">
             <button @click="cancelCrop">Anuluj</button>
             <button @click="applyCropAndAnalyze" class="primary">✂️ Przytnij i Analizuj</button>
          </div>
       </div>
    </div>

    <div v-if="showOcrOverlay && ocrResult" class="ocr-overlay">
       <div class="ocr-header">
          <h2>Wyniki analizy</h2>
          <div class="ocr-instruct">Kliknij na pozycje, które chcesz dodać (Zielone = Wybrane)</div>
          <button @click="closeOcrOverlay" class="close-overlay">✕</button>
       </div>

       <div class="ocr-workspace">
          <div class="img-container" :style="{ width: ocrResult.image_dim.width + 'px', height: ocrResult.image_dim.height + 'px' }">
             <img :src="croppedImageUrl || ''" class="overlay-bg" alt="Przycięty paragon" />

             <template v-for="(item, idx) in ocrResult.items" :key="idx">
               <div
                 class="ocr-box"
                 :class="{ 'selected': selectedOcrIndices.has(idx) }"
                 v-if="item.box"
                 :style="getBoxStyle(item.box)"
                 @click="toggleOcrItem(idx)"
               >
                 <div class="tooltip">{{ item.name }} ({{ item.price }} zł)</div>
               </div>
             </template>

          </div>
       </div>

       <div class="ocr-footer">
          <div class="selection-summary">
             Wybrano: <strong>{{ selectedOcrIndices.size }}</strong> pozycji
          </div>
          <div class="ocr-footer-actions">
             <button @click="selectAllOcr" class="btn-secondary-outline">
               Zaznacz wszystkie
             </button>

             <button @click="importOcrItems" class="btn-import-glow" :disabled="selectedOcrIndices.size === 0">
               📥 Importuj do listy
             </button>
          </div>
       </div>
    </div>

    <div v-if="showProductModal" class="modal-overlay z-high">
       <div class="modal-content small">
          <h3>{{ editingProductIndex !== null ? 'Edytuj pozycję' : 'Dodaj pozycję' }}</h3>
          <form @submit.prevent="saveProduct">
             <div class="form-group">
                <label>Nazwa</label>
                <input v-model="productForm.name" required />
             </div>

             <div class="form-row">
                <div class="form-group half">
                   <label>Cena (Całość)</label>
                   <input
                     type="number"
                     step="0.01"
                     v-model="productForm.price"
                     @input="handlePriceChange"
                     required
                   />
                </div>
                <div class="form-group half">
                   <label>Ilość</label>
                   <input
                     type="number"
                     step="0.001"
                     v-model="productForm.quantity"
                     @input="handleQuantityChange"
                     required
                   />
                </div>
             </div>

             <div class="hint-text" style="margin-top: -10px; margin-bottom: 10px; font-size: 0.8rem; color: #9ca3af;">
               Cena jedn.: {{ (productForm.unitPrice || 0).toFixed(2) }} zł
             </div>

             <div class="form-group">
                <label>Kategoria</label>
                <select v-model="productForm.category">
                   <option v-for="c in categories" :key="c.value" :value="c.value">{{ c.label }}</option>
                </select>
             </div>

             <div class="form-group">
                <label>Konsumenci (kto płaci za tę część?)</label>
                <div class="checkbox-group">
                   <label v-for="member in settlementMembers" :key="member.id">
                      <input type="checkbox" :value="member.id" v-model="productForm.consumers" />
                      {{ member.username }}
                   </label>
                </div>
                <p v-if="settlementMembers.length === 0" class="hint-error">Brak członków w grupie.</p>
             </div>

             <div class="modal-actions">
                <button type="button" @click="showProductModal = false">Anuluj</button>
                <button type="submit" class="primary">Zapisz</button>
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

    <div v-if="errorMessage" class="toast error">{{ errorMessage }}</div>
    <div v-if="successMessage" class="toast success">{{ successMessage }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import fractiService, { type Settlement, type User, Category, CATEGORY_LABELS } from '@/services/receipts.service';
import { Cropper } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const router = useRouter();

// --- STATE ---
const settlements = ref<Settlement[]>([]);
const selectedSettlementId = ref<string | number | null>(null);
const settlementMembers = ref<User[]>([]);
const showNewSettlementForm = ref(false);
const newSettlement = ref({ name: '', description: '' });

const fileInput = ref<HTMLInputElement|null>(null);
const originalImageUrl = ref<string|null>(null);
const croppedImageUrl = ref<string|null>(null);
const showCropperModal = ref(false);
const cropperRef = ref<any>(null);
const isAnalyzing = ref(false);
const pollingAttempts = ref(0);
const ocrResult = ref<any>(null);
const showOcrOverlay = ref(false);
const selectedOcrIndices = ref<Set<number>>(new Set());

const receiptProducts = ref<any[]>([]);
const receiptData = ref({
  merchant_name: '',
  description: '',
  purchase_date: new Date().toISOString().split('T')[0],
  purchaser: null as number | null,
  latitude: null as number | null,
  longitude: null as number | null
});

const showProductModal = ref(false);
const editingProductIndex = ref<number | null>(null);
const productForm = ref({
  name: '',
  price: '',
  quantity: 1,
  unitPrice: 0,
  category: Category.FOOD,
  consumers: [] as number[]
});

const showConfirmModal = ref(false);
const confirmMessage = ref('');
const confirmSubMessage = ref('');
const pendingDeleteAction = ref<(() => void) | null>(null);

const isUploading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');
const categories = fractiService.getCategoriesOptionList();
let mapInstance: L.Map | null = null;
let markerInstance: L.Marker | null = null;

// --- COMPUTED ---
const canEditForm = computed(() => {
  return selectedSettlementId.value !== null && selectedSettlementId.value !== 'NEW_SETTLEMENT';
});

// --- LIFECYCLE ---
onMounted(async () => {
  try {
    settlements.value = await fractiService.getSettlements();
  } catch (e) {
    console.error(e);
  }
});

// --- HELPER METHODS ---
const isInteger = (num: number | string) => {
  const n = parseFloat(String(num));
  return Number.isInteger(n);
};

// --- METHODS: Settlement ---
const handleSettlementChange = async () => {
  if (selectedSettlementId.value === 'NEW_SETTLEMENT') {
    showNewSettlementForm.value = true;
    settlementMembers.value = [];
  } else if (selectedSettlementId.value) {
    showNewSettlementForm.value = false;
    try {
      const s = await fractiService.getSettlementDetails(selectedSettlementId.value as string);
      settlementMembers.value = s.members;
      receiptData.value.purchaser = null;
      nextTick(() => initMap('map-ocr'));
    } catch (e) { console.error(e); }
  }
};

const createSettlement = async () => {
  try {
    const s = await fractiService.createSettlement(newSettlement.value);
    settlements.value.push(s);
    selectedSettlementId.value = s.id;
    settlementMembers.value = s.members;
    showNewSettlementForm.value = false;
    nextTick(() => initMap('map-ocr'));
  } catch (e) { alert('Błąd tworzenia grupy'); }
};

const cancelNewSettlement = () => {
  selectedSettlementId.value = null;
  showNewSettlementForm.value = false;
};

// --- METHODS: OCR Process ---
const triggerFileInput = () => fileInput.value?.click();

const handleFileSelect = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (ev) => {
      originalImageUrl.value = ev.target?.result as string;
      showCropperModal.value = true;
    };
    reader.readAsDataURL(file);
  }
  if (fileInput.value) fileInput.value.value = '';
};

const cancelCrop = () => {
  showCropperModal.value = false;
  originalImageUrl.value = null;
};

const applyCropAndAnalyze = () => {
  const { canvas } = cropperRef.value.getResult();
  if (canvas) {
    canvas.toBlob(async (blob: Blob) => {
      croppedImageUrl.value = URL.createObjectURL(blob);
      showCropperModal.value = false;
      await analyzeReceiptImage(blob);
    }, 'image/jpeg');
  }
};

const analyzeReceiptImage = async (blob: Blob) => {
  isAnalyzing.value = true;
  pollingAttempts.value = 0;

  try {
    const formData = new FormData();
    formData.append('image', blob, 'receipt.jpg');
    const { task_id } = await fractiService.analyzeReceipt(formData);
    await pollResult(task_id);

  } catch (e) {
    console.error(e);
    errorMessage.value = "Błąd wysyłania zdjęcia.";
    isAnalyzing.value = false;
  }
};

const pollResult = async (taskId: string) => {
  const interval = setInterval(async () => {
    pollingAttempts.value++;
    try {
       const res = await fractiService.getOCRResult(taskId);
       if (res.status === 'SUCCESS') {
         clearInterval(interval);
         isAnalyzing.value = false;
         const items = res.data.items || [];

         if (items.length === 0) {
             errorMessage.value = "OCR zakończony, ale nie znaleziono żadnych produktów.";
             return;
         }

         items.forEach((item: any) => {
            receiptProducts.value.push({
              name: item.name,
              price: item.price,
              quantity: item.quantity || 1,
              category: Category.FOOD,
              consumers: [] // Nie przypisuj automatycznie - użytkownik musi wybrać
            });
         });

         successMessage.value = `Sukces! Dodano ${items.length} pozycji. Sprawdź i popraw w razie potrzeby.`;
         setTimeout(() => successMessage.value = '', 4000);
       } else if (res.status === 'FAILURE') {
         clearInterval(interval);
         isAnalyzing.value = false;
         errorMessage.value = "Analiza OCR nie powiodła się.";
       }

       if (pollingAttempts.value > 30) {
         clearInterval(interval);
         isAnalyzing.value = false;
         errorMessage.value = "Timeout analizy.";
       }
    } catch (e) {
       clearInterval(interval);
       isAnalyzing.value = false;
    }
  }, 10000);
};

// --- METHODS: Overlay Logic ---
const getBoxStyle = (box: any) => {
  if (!ocrResult.value || !box) return { display: 'none' };
  const dim = ocrResult.value.image_dim;
  return {
    left: (box.x / dim.width) * 100 + '%',
    top: (box.y / dim.height) * 100 + '%',
    width: (box.w / dim.width) * 100 + '%',
    height: (box.h / dim.height) * 100 + '%'
  };
};

const toggleOcrItem = (idx: number) => {
  if (selectedOcrIndices.value.has(idx)) selectedOcrIndices.value.delete(idx);
  else selectedOcrIndices.value.add(idx);
};

const selectAllOcr = () => {
  ocrResult.value.items.forEach((_:any, i:number) => selectedOcrIndices.value.add(i));
};

const importOcrItems = () => {
  selectedOcrIndices.value.forEach(idx => {
    const item = ocrResult.value.items[idx];
    receiptProducts.value.push({
      name: item.name,
      price: item.price,
      quantity: item.quantity || 1,
      category: Category.FOOD,
      consumers: settlementMembers.value.map(u => u.id)
    });
  });
  showOcrOverlay.value = false;
  selectedOcrIndices.value.clear();
  successMessage.value = "Dodano produkty do listy.";
  setTimeout(() => successMessage.value = '', 2000);
};

const closeOcrOverlay = () => {
  showOcrOverlay.value = false;
};

// --- METHODS: Product Management (CRUD) ---
const openProductModal = (idx: number | null) => {
  editingProductIndex.value = idx;
  if (idx !== null) {
    const p = receiptProducts.value[idx];
    const qty = p.quantity || 1;
    const priceVal = parseFloat(p.price);

    productForm.value = {
      name: p.name,
      price: p.price.toString(),
      quantity: qty,
      unitPrice: priceVal / qty,
      category: p.category,
      consumers: [...p.consumers]
    };
  } else {
    productForm.value = {
      name: '', price: '', quantity: 1, unitPrice: 0,
      category: Category.FOOD,
      consumers: [] // Nie przypisuj automatycznie - użytkownik musi wybrać
    };
  }
  showProductModal.value = true;
};

const handleQuantityChange = () => {
  const qty = parseFloat(String(productForm.value.quantity));
  if (productForm.value.unitPrice > 0 && !isNaN(qty)) {
    const newTotal = productForm.value.unitPrice * qty;
    productForm.value.price = newTotal.toFixed(2);
  }
};

const handlePriceChange = () => {
  const price = parseFloat(productForm.value.price);
  const qty = parseFloat(String(productForm.value.quantity)) || 1;
  if (!isNaN(price)) {
    productForm.value.unitPrice = price / qty;
  }
};

const saveProduct = () => {
  const payload = {
    name: productForm.value.name,
    price: parseFloat(productForm.value.price),
    quantity: parseFloat(String(productForm.value.quantity)) || 1,
    category: productForm.value.category,
    consumers: productForm.value.consumers
  };

  if (editingProductIndex.value !== null) {
    receiptProducts.value[editingProductIndex.value] = payload;
  } else {
    receiptProducts.value.push(payload);
  }
  showProductModal.value = false;
};

const openConfirmModal = (title: string, subTitle: string, action: () => void) => {
  confirmMessage.value = title;
  confirmSubMessage.value = subTitle;
  pendingDeleteAction.value = action;
  showConfirmModal.value = true;
};

const handleConfirmDelete = () => {
  if (pendingDeleteAction.value) pendingDeleteAction.value();
  showConfirmModal.value = false;
  pendingDeleteAction.value = null;
};

const confirmRemoveProduct = (idx: number) => {
  openConfirmModal(
    'Usunąć pozycję?',
    `Czy na pewno chcesz usunąć "${receiptProducts.value[idx].name}"?`,
    () => {
      receiptProducts.value.splice(idx, 1);
    }
  );
};

const calculateTotal = () => {
  return receiptProducts.value.reduce((acc, p) => acc + p.price, 0);
};

const getCategoryLabel = (cat: string) => CATEGORY_LABELS[cat as Category] || cat;

// --- METHODS: Map & Submit ---
const initMap = (elId: string) => {
  if (mapInstance) mapInstance.remove();
  const el = document.getElementById(elId);
  if (!el) return;

  mapInstance = L.map(elId).setView([52.2297, 21.0122], 13);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19
  }).addTo(mapInstance);

  mapInstance.on('click', (e: L.LeafletMouseEvent) => {
    if (markerInstance) markerInstance.setLatLng(e.latlng);
    else markerInstance = L.marker(e.latlng).addTo(mapInstance!);
    receiptData.value.latitude = e.latlng.lat;
    receiptData.value.longitude = e.latlng.lng;
  });
};

const submitReceipt = async () => {
  if (!receiptData.value.merchant_name) {
    errorMessage.value = "Uzupełnij nazwę sklepu!";
    setTimeout(() => errorMessage.value = '', 3000);
    return;
  }

  const totalAmount = calculateTotal();
  isUploading.value = true;

  try {
    const fd = new FormData();
    // 1. Obsługa zdjęcia (Crop)
    if (croppedImageUrl.value) {
       const resp = await fetch(croppedImageUrl.value);
       const blob = await resp.blob();
       fd.append('image', blob, 'receipt_crop.jpg');
    }

    // 2. Dane podstawowe paragonu
    fd.append('merchant_name', receiptData.value.merchant_name);
    if (receiptData.value.description) fd.append('description', receiptData.value.description);
    fd.append('purchase_date', receiptData.value.purchase_date);
    fd.append('total_amount', totalAmount.toString());
    fd.append('category', 'SHOPPING');

    // 3. Obsługa ID Użytkownika (Purchaser)
    if (receiptData.value.purchaser) {
        fd.append('purchaser', receiptData.value.purchaser.toString());
    } else {
    }
    if (selectedSettlementId.value && selectedSettlementId.value !== 'PERSONAL' && selectedSettlementId.value !== 'NEW_SETTLEMENT') {
      fd.append('settlement', String(selectedSettlementId.value));
    }

    // 5. Lokalizacja
    if (receiptData.value.latitude && receiptData.value.longitude) {
      fd.append('latitude', receiptData.value.latitude.toString());
      fd.append('longitude', receiptData.value.longitude.toString());
    }

    const receipt = await fractiService.createReceipt(fd);

    for (const prod of receiptProducts.value) {


      const safePrice = parseFloat(String(prod.price)).toFixed(2);

      const safeQuantity = parseFloat(String(prod.quantity || 1)).toFixed(3);

      const safeConsumers = Array.isArray(prod.consumers) ? prod.consumers : [];

      let safeSettlement = undefined;
      if (selectedSettlementId.value && selectedSettlementId.value !== 'PERSONAL' && selectedSettlementId.value !== 'NEW_SETTLEMENT') {
          safeSettlement = String(selectedSettlementId.value);
      }

      // Payload do wysyłki
      const itemPayload = {
         name: prod.name,
         price: safePrice,
         quantity: safeQuantity,
         category: prod.category || 'FOOD',
         consumers: safeConsumers,
         settlement: safeSettlement
      };

      // Debug: Zobacz w konsoli przeglądarki co dokładnie leci, jeśli znowu będzie błąd
      console.log("Wysyłanie produktu:", itemPayload);

      await fractiService.addReceiptItem(receipt.id, itemPayload);
    }

    successMessage.value = "Paragon zapisany pomyślnie!";
    setTimeout(() => {
      if (selectedSettlementId.value && selectedSettlementId.value !== 'PERSONAL') {
        router.push(`/settlements/${selectedSettlementId.value}`);
      } else {
        router.push('/settlements');
      }
    }, 1500);

  } catch (e: any) {
    console.error("Błąd zapisu:", e);
    // Wyświetl szczegóły błędu z backendu jeśli dostępne
    if (e.response && e.response.data) {
        console.error("Detale błędu:", e.response.data);
        errorMessage.value = `Błąd zapisu: ${JSON.stringify(e.response.data)}`;
    } else {
        errorMessage.value = "Błąd zapisu paragonu.";
    }
  } finally {
    isUploading.value = false;
  }
};

const goBack = () => router.back();
</script>

<style scoped>
.ocr-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
  color: #e5e7eb;
  padding: 2rem;
  font-family: 'Inter', sans-serif;
}
.ocr-container { max-width: 800px; margin: 0 auto; }
.header { display: flex; align-items: center; gap: 1.5rem; margin-bottom: 2rem; }
.header h1 {
  font-size: 2rem;
  background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}
.back-btn {
  background: rgba(139,92,246,0.1); border: 1px solid rgba(139,92,246,0.3);
  color: #a78bfa; padding: 8px 16px; border-radius: 8px; cursor: pointer;
}
.section-title {
  color: #c4b5fd; font-size: 1.1rem; text-transform: uppercase;
  letter-spacing: 1px; margin: 0 0 1.5rem 0;
  border-bottom: 1px solid rgba(139,92,246,0.2); padding-bottom: 0.5rem;
}
.settlement-selector select {
  width: 100%; padding: 12px; background: #1e1b4b;
  border: 1px solid #4c1d95; color: white; border-radius: 8px; font-size: 1rem;
}
.new-settlement-form {
  margin-top: 1rem; background: rgba(139,92,246,0.1); padding: 1rem; border-radius: 8px;
}
.form-actions { display: flex; gap: 10px; margin-top: 10px; }
.form-grid { display: grid; gap: 1rem; }
.form-group label { display: block; margin-bottom: 4px; }
.form-row { display: flex; gap: 1rem; }
.form-group.half { flex: 1; }
.mini-map { height: 150px; margin-top: 5px; }
.ocr-trigger-section { margin-bottom: 1.5rem; }
.ocr-upload-btn {
  width: 100%; display: flex; align-items: center; justify-content: center;
  gap: 1rem; background: rgba(139, 92, 246, 0.1);
  border: 2px dashed rgba(139, 92, 246, 0.4); border-radius: 12px;
  padding: 1.5rem; cursor: pointer; transition: all 0.3s; text-align: left;
}
.ocr-upload-btn:hover { background: rgba(139, 92, 246, 0.2); border-color: #8b5cf6; }
.ocr-upload-btn .icon { font-size: 2rem; }
.ocr-upload-btn .main-text { font-weight: bold; color: #e5e7eb; font-size: 1.1rem; }
.ocr-upload-btn .sub-text { font-size: 0.9rem; color: #9ca3af; }
.products-manager {
  background: rgba(0,0,0,0.2); border-radius: 12px; padding: 1rem;
  border: 1px solid rgba(139,92,246,0.2);
}
.pm-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.btn-text { background: none; border: none; color: #a78bfa; cursor: pointer; text-decoration: underline; }
.products-list { display: flex; flex-direction: column; gap: 8px; }
.product-row {
  display: flex; justify-content: space-between; align-items: center;
  background: rgba(139,92,246,0.1); padding: 8px 12px; border-radius: 8px;
}
.prod-info { flex: 1; }
.prod-name { font-weight: 600; color: #fff; }
.prod-cat { font-size: 0.8rem; color: #9ca3af; }
.prod-price { font-weight: 700; color: #a78bfa; margin: 0 1rem; }
.prod-actions { display: flex; gap: 6px; }
.btn-mini {
  width: 32px; height: 32px; border-radius: 6px; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.btn-mini.edit { background: rgba(59,130,246,0.2); color: #60a5fa; }
.btn-mini.delete { background: rgba(239,68,68,0.2); color: #f87171; }
.products-total {
  margin-top: 1rem; padding-top: 1rem; border-top: 2px solid rgba(139, 92, 246, 0.3);
  display: flex; justify-content: space-between; align-items: center;
}
.total-label { font-size: 1.1rem; font-weight: 600; color: #c4b5fd; text-transform: uppercase; letter-spacing: 1px; }
.total-value {
  font-size: 1.5rem; font-weight: 700;
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.final-actions { margin-top: 2rem; }
.btn-save {
  width: 100%; padding: 14px; background: #22c55e; color: white;
  border: none; border-radius: 10px; font-size: 1.2rem; font-weight: bold;
  cursor: pointer; box-shadow: 0 4px 15px rgba(34,197,94,0.4);
}
.btn-save:hover { background: #16a34a; }
.btn-save:disabled { opacity: 0.6; cursor: wait; }
.center-text { margin-bottom: 2rem; }
.full-confirm {
  flex: 1; display: flex; justify-content: center; align-items: center; gap: 0.5rem;
  background: rgba(220, 38, 38, 0.2) !important; border: 1px solid #ef4444 !important;
}
.full-confirm:hover { background: #dc2626 !important; color: white !important; }
.ocr-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 3000;
  background: rgba(0,0,0,0.95); display: flex; flex-direction: column;
}
.ocr-header {
  padding: 1rem 2rem; background: #1e1b4b; border-bottom: 1px solid #4c1d95;
  display: flex; justify-content: space-between; align-items: center;
}
.ocr-workspace {
  flex: 1; width: 100%; overflow: auto; padding: 2rem;
  display: flex; justify-content: center; align-items: flex-start;
}
.img-container { position: relative; }
.overlay-bg { width: 100%; height: 100%; display: block; }
.ocr-box {
  position: absolute; border: 2px solid yellow; background: rgba(255,255,0,0.15);
  cursor: pointer; transition: all 0.2s;
}
.ocr-box.selected { border-color: #22c55e; background: rgba(34,197,94,0.3); }
.tooltip {
  position: absolute; bottom: 100%; left: 0; background: black; color: white;
  font-size: 0.7rem; padding: 2px 4px; pointer-events: none;
}
.close-overlay { background: none; border: none; color: white; font-size: 2rem; cursor: pointer; }
.ocr-footer {
  width: 100%; padding: 1.5rem 2rem; background: rgba(15, 23, 42, 0.95);
  border-top: 1px solid rgba(139, 92, 246, 0.3); display: flex;
  justify-content: space-between; align-items: center; backdrop-filter: blur(10px);
}
.ocr-footer-actions { display: flex; gap: 1rem; align-items: center; }
.selection-summary { color: #e5e7eb; font-size: 1rem; }
.selection-summary strong { color: #22c55e; font-size: 1.1rem; }
.btn-secondary-outline {
  background: transparent; border: 1px solid rgba(167, 139, 250, 0.3);
  color: #c4b5fd; padding: 10px 18px; border-radius: 10px; font-size: 0.95rem;
  cursor: pointer; transition: all 0.3s ease;
}
.btn-secondary-outline:hover {
  border-color: #a78bfa; background: rgba(139, 92, 246, 0.1); color: white;
  transform: translateY(-1px);
}
.btn-import-glow {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white;
  border: none; padding: 12px 24px; border-radius: 10px; font-weight: 600;
  font-size: 1rem; cursor: pointer; display: flex; align-items: center; gap: 8px;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-import-glow:hover:not(:disabled) {
  transform: translateY(-2px); box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5); filter: brightness(1.1);
}
.btn-import-glow:disabled {
  background: #374151; color: #9ca3af; cursor: not-allowed; box-shadow: none; transform: none; opacity: 0.7;
}

.qty-badge {
  background: rgba(139, 92, 246, 0.3); color: #c4b5fd; font-weight: bold;
  padding: 4px 8px; border-radius: 6px; margin-right: 10px;
  font-size: 0.9rem; border: 1px solid rgba(139, 92, 246, 0.5);
}
.weight-label {
  font-size: 0.85rem; color: #9ca3af; font-weight: normal; margin-left: 6px;
}
.modal-content button {
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.3);
  background: transparent;
  color: #c4b5fd;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.95rem;
  font-weight: 500;
}

.modal-content button:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: #a78bfa;
  color: white;
}

.modal-content button.primary {
  background: #22c55e;
  border-color: #22c55e;
  color: white;
  font-weight: 600;
}

.modal-content button.primary:hover {
  background: #16a34a;
  border-color: #16a34a;
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

.modal-content button.danger-btn {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #fca5a5;
}

.modal-content button.danger-btn:hover {
  background: #ef4444;
  color: white;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}
.modal-actions.space-between {
  justify-content: space-between;
}
.btn-secondary {
  background: transparent;
  border: 1px solid rgba(139, 92, 246, 0.3);
  color: #c4b5fd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.btn-secondary:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: #a78bfa;
  color: white;
}
.btn-primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  border: none;
  color: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 10px rgba(139, 92, 246, 0.2);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}
button.small {
  padding: 8px 16px;
  font-size: 0.85rem;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
</style>