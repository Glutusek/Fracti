<template>
  <div class="map-layout">
    <div class="map-container">
      <l-map
        ref="map"
        @ready="onMapReady"
        v-model:zoom="zoom"
        :center="center"
        :use-global-leaflet="false"
      >
        <l-tile-layer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          layer-type="base"
          name="CartoDB Dark Matter"
        />

        <l-marker
          v-for="item in filteredItems"
          :key="item.uniqueId"
          :lat-lng="item.coords"
        >
          <l-icon
            :icon-url="getIconUrl(item.category)"
            :shadow-url="shadowUrl"
            :icon-size="[25, 41]"
            :icon-anchor="[12, 41]"
            :popup-anchor="[1, -34]"
          />

          <l-popup>
            <div class="popup-content">
              <strong>{{ item.name }}</strong>
              <div class="popup-meta">
                <span>{{ formatDate(item.date) }}</span> •
                <span class="cat-label">{{ getCategoryLabel(item.category) }}</span>
              </div>

              <hr class="popup-divider" />

              <div v-if="item.type === 'receipt'" class="products-preview">
                <small>Pozycje ({{ item.products?.length || 0 }}):</small>
                <ul>
                  <li v-for="(prod, index) in item.products" :key="index">
                    {{ prod.name }} - {{ formatMoney(prod.price) }} zł
                  </li>
                </ul>
                <div class="total">Suma: {{ formatMoney(item.amount) }} zł</div>
              </div>

              <div v-else class="single-preview">
                Kategoria: {{getCategoryLabel(item.category)}}
                <div class="total">Kwota: {{ formatMoney(item.amount) }} zł</div>
              </div>
            </div>
          </l-popup>
        </l-marker>
      </l-map>
    </div>

    <div class="sidebar">
      <div class="sidebar-header">
        <button @click="goBack" class="back-btn">← Wróć do listy</button>
        <button @click="goDetails" class="back-btn">Szczegóły</button>

        <h2 v-if="currentSettlement">{{ currentSettlement.name }}</h2>

        <div v-else-if="loading" class="loading-text">
          <span class="spinner">⏳</span> Ładowanie danych...
        </div>
        <div v-else-if="errorMessage" class="error-text">
          ❌ {{ errorMessage }}
        </div>
        <div v-else class="loading-text">Brak danych.</div>

        <div class="filters">
          <button
            v-for="cat in filterOptions"
            :key="cat.value"
            @click="activeFilter = cat.value"
            :class="['filter-chip', { active: activeFilter === cat.value }]"
          >
            {{ cat.label }}
          </button>
        </div>
      </div>

      <div class="items-list">
        <div
          v-for="item in filteredItems"
          :key="item.uniqueId"
          class="item-card"
          @click="flyToMarker(item.coords)"
        >
          <div class="card-top">
            <span class="item-icon">{{ getCategoryIconEmoji(item.category) }}</span>
            <div class="item-info">
              <div class="item-title">{{ item.name }}</div>
              <div class="item-meta">
                {{ item.type === 'receipt' ? 'Paragon' : 'Produkt' }} • {{ formatDate(item.date) }}
              </div>
            </div>
            <div class="item-amount">{{ formatMoney(item.amount) }} zł</div>
          </div>

          <div v-if="item.type === 'receipt' && item.products && item.products.length > 0" class="card-products">
            <div v-for="(prod, i) in item.products" :key="i" class="product-row">
              <span class="prod-name">{{ prod.name }}</span>
              <span class="prod-price">{{ formatMoney(prod.price) }} zł</span>
            </div>
          </div>

        </div>

        <div v-if="filteredItems.length === 0" class="empty-msg">
          Brak elementów na mapie dla wybranych filtrów.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { LMap, LTileLayer, LMarker, LPopup, LIcon } from '@vue-leaflet/vue-leaflet';
import 'leaflet/dist/leaflet.css';

// Import serwisu
import fractiService, {
  type Settlement,
  type CategoryType,
  CATEGORY_LABELS,
  Category
} from '@/services/receipts.service';

const route = useRoute();
const router = useRouter();

// Pobieramy ID bezpiecznie
const settlementId = (route.params.id || route.params.uuid) as string;

// --- CONFIG MAPY ---
const zoom = ref(6);
const center = ref<[number, number]>([52.0, 19.0]);
// reference to the LMap component (vue-leaflet) to access native Leaflet map
const map = ref<any>(null);
// store native Leaflet map instance when available
const mapNative = ref<any>(null);

const onMapReady = (map: any) => {
  try {
    mapNative.value = map;
    console.debug('Map ready, native map set', { center: map.getCenter && map.getCenter(), zoom: map.getZoom && map.getZoom() });
  } catch (e) {
    console.debug('onMapReady error', e);
  }
};
const shadowUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png';

// --- STATE ---
const currentSettlement = ref<Settlement | null>(null);
const items = ref<any[]>([]);
const activeFilter = ref<string>('ALL');
const loading = ref(true);
const errorMessage = ref('');

// --- FILTROWANIE ---
const filterOptions = computed(() => [
  { label: 'Wszystkie', value: 'ALL' },
  ...Object.values(Category).map(cat => ({
    label: CATEGORY_LABELS[cat],
    value: cat
  }))
]);

const filteredItems = computed(() => {
  if (activeFilter.value === 'ALL') return items.value;
  return items.value.filter(i => i.category === activeFilter.value);
});

// --- IKONY ---
const markerIcons: Record<string, string> = {
  [Category.FOOD]: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  [Category.TRANSPORT]: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  [Category.ACCOMMODATION]: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  [Category.ENTERTAINMENT]: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  [Category.SHOPPING]: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
  [Category.SERVICES]: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
  default: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png'
};

const getIconUrl = (cat: string) => markerIcons[cat] || markerIcons.default;

// --- PRZETWARZANIE ---
const processBackendData = (data: Settlement) => {
  const mappedItems: any[] = [];

  if (data.receipts) {
    data.receipts.forEach(r => {
      if (r.latitude && r.longitude) {
        mappedItems.push({
          uniqueId: `r-${r.id}`,
          type: 'receipt',
          name: r.merchant_name,
          amount: parseFloat(r.total_amount),
          date: r.purchase_date,
          category: r.category,
          coords: [Number(r.latitude), Number(r.longitude)],
          products: r.products ? r.products.map(p => ({ name: p.name, price: p.price })) : []
        });
      }
    });
  }

  if (data.loose_products) {
    data.loose_products.forEach(p => {
      if (p.latitude && p.longitude) {
        mappedItems.push({
          uniqueId: `p-${p.id}`,
          type: 'single',
          name: p.name,
          amount: parseFloat(p.price),
          date: p.created_at,
          category: p.category,
          coords: [Number(p.latitude), Number(p.longitude)]
        });
      }
    });
  }
  return mappedItems;
};

// --- AKCJE ---
const goBack = () => router.push(`/settlements/`);
const goDetails = () => router.push(`/settlements/{${settlementId}}`);
const flyToMarker = (coords: [number, number]) => {
  const lat = Number(coords[0]);
  const lng = Number(coords[1]);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return;

  // Prefer native map captured via onMapReady, then try common refs
  const finalMap = mapNative.value || map.value?.mapObject || map.value?.map || null;

  if (finalMap && typeof finalMap.flyTo === 'function') {
    // animate and sync after movement
    finalMap.flyTo([lat, lng], 16, { animate: true });
    if (typeof finalMap.once === 'function') {
      finalMap.once('moveend', () => {
        const after = finalMap.getCenter && finalMap.getCenter();
        if (after) {
          center.value = [after.lat, after.lng];
          zoom.value = finalMap.getZoom ? finalMap.getZoom() : 16;
        }
      });
    } else {
      // fallback immediate sync
      const after = finalMap.getCenter && finalMap.getCenter();
      if (after) {
        center.value = [after.lat, after.lng];
        zoom.value = finalMap.getZoom ? finalMap.getZoom() : 16;
      }
    }
    return;
  }

  // reactive fallback
  center.value = [lat, lng];
  zoom.value = 16;
};

// (removed DOM-fallback helper) 

// marker clicks handled via sidebar/timeline; onMarkerClick removed

// --- FORMATOWANIE ---
const formatMoney = (val: number | string) => Number(val).toFixed(2);
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('pl-PL') : '-';
const getCategoryLabel = (cat: CategoryType) => CATEGORY_LABELS[cat] || cat;
const getCategoryIconEmoji = (cat: CategoryType) => {
  const map: Record<string, string> = { FOOD: '🍔', TRANSPORT: '🚕', ACCOMMODATION: '🏠', ENTERTAINMENT: '🎬', SHOPPING: '🛍️' };
  return map[cat] || '📍';
};

// --- ON MOUNTED ---
onMounted(async () => {
  if (!settlementId || settlementId === 'undefined') {
    loading.value = false;
    errorMessage.value = "Błąd: Brak ID rozliczenia w URL.";
    return;
  }

  try {
    loading.value = true;
    errorMessage.value = '';
    const data = await fractiService.getSettlementDetails(settlementId);
    currentSettlement.value = data;
    items.value = processBackendData(data);

    if (items.value.length > 0) {
      // default view
      center.value = items.value[0].coords;
      zoom.value = 12;
    }

    // If navigation included a focus query, pan to that specific item
    const focus = (route.query.focus as string) || null;
    if (focus) {
      const target = items.value.find(i => i.uniqueId === focus);
      if (target) {
        // give map some time to initialize
        setTimeout(() => flyToMarker(target.coords), 150);
      }
    }
  } catch (error: any) {
    console.error("API Error:", error);
    errorMessage.value = error.response?.data?.detail || "Nie udało się pobrać danych.";
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.map-layout { display: flex; height: calc(100vh - 80px); overflow: hidden; }
.map-container { flex: 1; position: relative; z-index: 1; }

.sidebar {
  width: 380px;
  background: #1f2937;
  color: white;
  border-left: 1px solid #374151;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 10px rgba(0,0,0,0.3);
  z-index: 2;
}

.sidebar-header {
  padding: 1.5rem;
  background: #111827;
  border-bottom: 1px solid #374151;
}

.back-btn {
  background: transparent;
  border: 1px solid #4b5563;
  color: #d1d5db;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  margin-bottom: 1rem;
  transition: all 0.2s;
  margin-left: 4px;
}
.back-btn:hover { background: #374151; color: white; }

.sidebar-header h2 { margin: 0 0 1rem 0; font-size: 1.25rem; }

/* --- ZMIANA DLA CIEBIE: FILTRY ZAWIJANE --- */
.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap; /* To sprawia, że przyciski spadają do nowej linii */
  padding-bottom: 4px;
}

.filter-chip {
  background: transparent;
  border: 1px solid #4b5563;
  color: #9ca3af;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;
}
.filter-chip.active {
  background: #8b5cf6;
  border-color: #8b5cf6;
  color: white;
}

.items-list { flex: 1; overflow-y: auto; padding: 1rem; }

.item-card {
  background: #374151;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
  border: 1px solid transparent;
}
.item-card:hover {
  background: #4b5563;
  transform: translateX(4px);
  border-color: #8b5cf6;
}

.card-top { display: flex; align-items: center; gap: 12px; }
.item-icon { font-size: 1.5rem; }
.item-info { flex: 1; overflow: hidden; }
.item-title { font-weight: 600; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-meta { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
.item-amount { font-weight: 700; color: #a78bfa; }

/* --- ZMIANA DLA CIEBIE: STYL PRODUKTÓW W SIDEBARZE --- */
.card-products {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #4b5563;
}

.product-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #d1d5db;
  margin-bottom: 4px;
}
.prod-name { color: #9ca3af; }
.prod-price { font-weight: 500; }

.empty-msg { text-align: center; color: #6b7280; margin-top: 2rem; font-style: italic; }
.error-text { color: #ef4444; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 8px; margin-bottom: 1rem; }

/* POPUP STYLE */
.popup-content { min-width: 180px; color: #1f2937; }
.popup-meta { font-size: 0.8rem; color: #6b7280; margin-bottom: 5px; }
.popup-divider { border: 0; border-top: 1px solid #e5e7eb; margin: 8px 0; }
.products-preview ul { padding-left: 15px; margin: 5px 0; font-size: 0.85rem; }
.total { text-align: right; font-weight: bold; margin-top: 8px; }
</style>