<template>
  <div class="map-layout">
    <div class="map-container">
      <l-map ref="map" @ready="onMapReady" v-model:zoom="zoom" :center="center" :use-global-leaflet="false"
        :zoom-snap="0.25">
        <l-tile-layer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" layer-type="base"
          name="CartoDB Dark Matter" />

        <l-marker v-if="visualizationMode === 'markers'" v-for="item in filteredItems" :key="item.uniqueId"
          :lat-lng="item.coords">
          <l-icon :icon-url="getIconUrl(item.category)" :shadow-url="shadowUrl" :icon-size="[25, 41]"
            :icon-anchor="[12, 41]" :popup-anchor="[1, -34]" />

          <l-popup>
            <div class="popup-content">
              <strong>{{ item.name }}</strong>
              <div v-if="item.description" class="popup-desc">
                <strong>Opis:</strong>
                <br />
                {{ item.description }}
              </div>
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
                Kategoria: {{ getCategoryLabel(item.category) }}
                <div class="total">Kwota: {{ formatMoney(item.amount) }} zł</div>
              </div>
            </div>
          </l-popup>
        </l-marker>

        <HeatmapLayer
          v-if="visualizationMode === 'heatmap'"
          :heatmap-data="heatmapData"
          :max-weight="heatmapMaxWeight"
          :show-legend="true"
          :intensity-multiplier="heatmapIntensity"
          :base-opacity="heatmapOpacity"
        />
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
          <button @click="toggleVisualizationMode" :class="['filter-chip', { active: visualizationMode === 'heatmap' }]"
            title="Przełącz między znacznikami a mapą ciepła">
            🔥 {{ visualizationMode === 'heatmap' ? 'Heatmapa' : 'Znaczniki' }}
          </button>
        </div>
        <div v-if="visualizationMode === 'heatmap'" class="heatmap-controls fade-in">
  <div class="control-group">
    <label>Moc natężenia: {{ heatmapIntensity }}x</label>
    <input type="range" v-model.number="heatmapIntensity" min="0.1" max="5" step="0.1" />
  </div>
  <div class="control-group">
    <label>Widoczność (Krycie): {{ Math.round(heatmapOpacity * 100) }}%</label>
    <input type="range" v-model.number="heatmapOpacity" min="0.1" max="1" step="0.05" />
  </div>
</div>
        <div class="filters">
          <button v-for="cat in filterOptions" :key="cat.value" @click="toggleFilter(cat.value)"
            :class="['filter-chip', { active: isFilterActive(cat.value) }]">
            {{ cat.label }}
          </button>
        </div>
      </div>

      <div class="items-list">
        <div v-for="item in filteredItems" :key="item.uniqueId" class="item-card" @click="flyToMarker(item.coords)">
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
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { LMap, LTileLayer, LMarker, LPopup, LIcon } from '@vue-leaflet/vue-leaflet';
import 'leaflet/dist/leaflet.css';
import HeatmapLayer from '@/components/HeatmapLayer.vue';

import fractiService, {
  type Settlement,
  type CategoryType,
  CATEGORY_LABELS,
  Category
} from '@/services/receipts.service';

const route = useRoute();
const router = useRouter();

const settlementId = (route.params.id || route.params.uuid) as string;

const zoom = ref(6);
const center = ref<[number, number]>([52.0, 19.0]);
const map = ref<any>(null);
const mapNative = ref<any>(null);

// Heatmap state
const visualizationMode = ref<'markers' | 'heatmap'>('markers');
const heatmapData = ref<any>(null);
const heatmapMaxWeight = ref<number | undefined>(undefined);
const heatmapLoading = ref(false);
let heatmapAbortController: AbortController | null = null;
const heatmapIntensity = ref(1.0);
const heatmapOpacity = ref(0.7);
// Debounce utility
const debounce = (fn: Function, delay: number) => {
  let timeout: ReturnType<typeof setTimeout>;
  return (...args: any[]) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
};

// Fetch heatmap data
const updateHeatmap = debounce(async () => {
  if (visualizationMode.value !== 'heatmap' || !mapNative.value || !currentSettlement.value) return;

  try {
    // Cancel previous request if still in progress
    if (heatmapAbortController) {
      heatmapAbortController.abort();
    }
    heatmapAbortController = new AbortController();

    const bounds = mapNative.value.getBounds();
    const bbox: [number, number, number, number] = [
      bounds.getWest(),
      bounds.getSouth(),
      bounds.getEast(),
      bounds.getNorth(),
    ];
    
    // Calculate cell size based on bbox width with min/max bounds
    // Wider bbox = larger cells (for performance)
    // Min: 0.001° (~111m) | Max: 5° (~550km)
    const bboxWidth = bounds.getEast() - bounds.getWest();
    let cellSize = bboxWidth / 100; // ~25 hexagons across viewport
    cellSize = Math.max(0.001, Math.min(5, cellSize)); // Clamp to reasonable range
    
    heatmapLoading.value = true;

    console.log('🔥 Heatmap request:', {
      settlementId: currentSettlement.value.id,
      bbox,
      cellSize: cellSize.toFixed(6),
      bboxWidth: bboxWidth.toFixed(4),
      zoom: zoom.value,
      filters: Array.from(selectedFilters.value),
    });

    const response = await fractiService.getHeatmapData(
      currentSettlement.value.id,
      bbox,
      cellSize,
      undefined,
      undefined,
      Array.from(selectedFilters.value),
      undefined
    );

    console.log('🔥 Heatmap response:', response);

    heatmapData.value = response.heatmap_points || [];
    if (heatmapData.value && heatmapData.value.length > 0) {
      heatmapMaxWeight.value = Math.max(...heatmapData.value.map((p: any) => p.weight || 0));
    } else {
      heatmapMaxWeight.value = undefined;
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      console.log('🔥 Previous heatmap request cancelled');
      return;
    }
    console.error('Heatmap error:', err);
    heatmapData.value = null;
    heatmapMaxWeight.value = undefined;
  } finally {
    heatmapLoading.value = false;
  }
}, 500);

const onMapReady = (mapInstance: any) => {
  try {
    mapNative.value = mapInstance;
    console.debug('Map ready, native map set');

    // Add event listeners for heatmap updates
    mapNative.value?.on('moveend', updateHeatmap);
    mapNative.value?.on('zoomend', updateHeatmap);
  } catch (e) {
    console.debug('onMapReady error', e);
  }
};
const shadowUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png';

const currentSettlement = ref<Settlement | null>(null);
const items = ref<any[]>([]);
const selectedFilters = ref<Set<string>>(new Set());
const loading = ref(true);
const errorMessage = ref('');

const filterOptions = computed(() => [
  { label: 'Wszystkie', value: 'ALL' },
  ...Object.values(Category).map(cat => ({
    label: CATEGORY_LABELS[cat],
    value: cat
  }))
]);

const toggleFilter = (val: string) => {
  if (val === 'ALL') {
    selectedFilters.value.clear();
    return;
  }

  if (selectedFilters.value.has(val)) {
    selectedFilters.value.delete(val);
  } else {
    selectedFilters.value.add(val);
  }
};

// Watch for filter changes and update heatmap if in heatmap mode
watch(
  () => Array.from(selectedFilters.value).sort().join(','),
  () => {
    if (visualizationMode.value === 'heatmap') {
      updateHeatmap();
    }
  }
);

const toggleVisualizationMode = () => {
  visualizationMode.value = visualizationMode.value === 'markers' ? 'heatmap' : 'markers';
  if (visualizationMode.value === 'heatmap') {
    updateHeatmap();
  }
};

const isFilterActive = (val: string) => {
  if (val === 'ALL') return selectedFilters.value.size === 0;
  return selectedFilters.value.has(val);
};

const filteredItems = computed(() => {
  if (selectedFilters.value.size === 0) return items.value;
  return items.value.filter(i => selectedFilters.value.has(i.category));
});

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

const processBackendData = (data: Settlement) => {
  const mappedItems: any[] = [];
  if (data.receipts) {
    data.receipts.forEach(r => {
      if (r.latitude && r.longitude) {
        mappedItems.push({
          uniqueId: `r-${r.id}`,
          type: 'receipt',
          name: r.merchant_name,
          description: r.description,
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
          description: p.description,
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

const goBack = () => router.push(`/settlements/`);
const goDetails = () => router.push(`/settlements/${settlementId}`);

const centerOnAveragePoint = () => {
  const leafletMap = mapNative.value || map.value?.leafletObject || map.value?.mapObject;

  if (!leafletMap) return;

  const points = items.value
    .map(i => i.coords)
    .filter(c => Array.isArray(c) && c.length === 2 && !isNaN(Number(c[0])) && !isNaN(Number(c[1])))
    .map(c => [Number(c[0]), Number(c[1])]);

  if (points.length === 0) {
    leafletMap.setView([52.0693, 19.4803], 6);
    return;
  }

  if (points.length === 1) {
    leafletMap.flyTo(points[0], 14);
    return;
  }

  let sumLat = 0;
  let sumLng = 0;

  points.forEach(p => {
    sumLat += p[0];
    sumLng += p[1];
  });

  const avgLat = sumLat / points.length;
  const avgLng = sumLng / points.length;

  const lats = points.map(p => p[0]);
  const lngs = points.map(p => p[1]);
  const maxDiffLat = Math.max(...lats) - Math.min(...lats);
  const maxDiffLng = Math.max(...lngs) - Math.min(...lngs);

  let targetZoom = 13;

  if (maxDiffLat > 2 || maxDiffLng > 2) {
    targetZoom = 6;
  } else if (maxDiffLat > 0.5 || maxDiffLng > 0.5) {
    targetZoom = 9;
  }

  leafletMap.setView([avgLat, avgLng], targetZoom);
};

const flyToMarker = (coords: [number, number]) => {
  const lat = Number(coords[0]);
  const lng = Number(coords[1]);
  if (Number.isNaN(lat) || Number.isNaN(lng)) return;

  const finalMap = mapNative.value || map.value?.leafletObject || map.value?.mapObject;

  if (finalMap && typeof finalMap.flyTo === 'function') {
    finalMap.flyTo([lat, lng], 16, { animate: true });
    return;
  }
  center.value = [lat, lng];
  zoom.value = 16;
};

const formatMoney = (val: number | string) => Number(val).toFixed(2);
const formatDate = (date: string) => date ? new Date(date).toLocaleDateString('pl-PL') : '-';
const getCategoryLabel = (cat: CategoryType) => CATEGORY_LABELS[cat] || cat;
const getCategoryIconEmoji = (cat: CategoryType) => {
  const map: Record<string, string> = { FOOD: '🍔', TRANSPORT: '🚕', ACCOMMODATION: '🏠', ENTERTAINMENT: '🎬', SHOPPING: '🛍️' };
  return map[cat] || '📍';
};

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

    const focusId = (route.query.focus as string) || null;
    let targetItem = null;

    if (focusId) {
      targetItem = items.value.find(i => i.uniqueId === focusId);
    }

    if (targetItem && targetItem.coords) {
      center.value = targetItem.coords;
      zoom.value = 16;
    } else {
      setTimeout(() => {
        centerOnAveragePoint();
      }, 100);
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
.map-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.map-container {
  flex: 1;
  position: relative;
  z-index: 1;
}

.sidebar {
  width: 380px;
  background: #1f2937;
  color: white;
  border-left: 1px solid #374151;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.3);
  z-index: 2;
  max-height: 100vh;
  overflow: hidden;
}

.sidebar-header {
  padding: 1.5rem;
  background: #111827;
  border-bottom: 1px solid #374151;
  flex-shrink: 0;
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
  transition: var(--transition-fast);
  margin-left: 4px;
}

.back-btn:hover {
  background: #374151;
  color: white;
}

.sidebar-header h2 {
  margin: 0 0 1rem 0;
  font-size: 1.25rem;
}

.filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.popup-desc {
  font-size: 0.85rem;
  font-style: italic;
  color: #4b5563;
  margin: 4px 0;
  line-height: 1.2;
}

.items-list {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.item-card {
  background: #374151;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: var(--transition-fast);
  border: 1px solid transparent;
}

.item-card:hover {
  background: #4b5563;
  transform: translateX(4px);
  border-color: #8b5cf6;
}

.card-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-icon {
  font-size: 1.5rem;
}

.item-info {
  flex: 1;
  overflow: hidden;
}

.item-title {
  font-weight: 600;
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-meta {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 2px;
}

.item-amount {
  font-weight: 700;
  color: #a78bfa;
}

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

.prod-name {
  color: #9ca3af;
}

.prod-price {
  font-weight: 500;
}

.empty-msg {
  text-align: center;
  color: #6b7280;
  margin-top: 2rem;
  font-style: italic;
}

.error-text {
  color: #ef4444;
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  margin-bottom: 1rem;
}

/* POPUP STYLE */
.popup-content {
  min-width: 180px;
  color: #1f2937;
}

.popup-meta {
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 5px;
}

.popup-divider {
  border: 0;
  border-top: 1px solid #e5e7eb;
  margin: 8px 0;
}

.products-preview ul {
  padding-left: 15px;
  margin: 5px 0;
  font-size: 0.85rem;
}

.total {
  text-align: right;
  font-weight: bold;
  margin-top: 8px;
}

/* Responsive */
@media (max-width: 1024px) {
  .map-layout {
    flex-direction: column;
    height: auto;
  }

  .map-container {
    height: 50vh;
    min-height: 400px;
    width: 100%;
  }

  .sidebar {
    width: 100%;
    border-left: none;
    border-top: 1px solid #374151;
    max-height: 50vh;
  }

  .items-list {
    max-height: calc(50vh - 200px);
  }
}

@media (max-width: 768px) {
  .map-layout {
    flex-direction: column;
    height: auto;
  }

  .map-container {
    height: 40vh;
    min-height: 300px;
    width: 100%;
    flex: none;
  }

  .sidebar {
    width: 100%;
    border-left: none;
    border-top: 2px solid #8b5cf6;
    flex: 1;
    min-height: 60vh;
  }

  .sidebar-header {
    padding: 1rem;
  }

  .sidebar-header h2 {
    font-size: 1.1rem;
  }

  .back-btn {
    font-size: 0.75rem;
    padding: 4px 8px;
    margin-bottom: 0.75rem;
  }

  .filters {
    gap: 6px;
  }

  .filter-chip {
    font-size: 0.75rem;
    padding: 3px 10px;
  }

  .items-list {
    padding: 0.75rem;
  }

  .item-card {
    padding: 10px;
  }

  .item-title {
    font-size: 0.9rem;
  }

  .item-meta {
    font-size: 0.7rem;
  }
}

@media (max-width: 480px) {
  .map-container {
    height: 35vh;
    min-height: 250px;
  }

  .sidebar {
    min-height: 65vh;
  }

  .sidebar-header {
    padding: 0.75rem;
  }

  .sidebar-header h2 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
  }

  .back-btn {
    font-size: 0.7rem;
    padding: 3px 6px;
  }

  .filters {
    gap: 4px;
  }

  .filter-chip {
    font-size: 0.7rem;
    padding: 2px 8px;
  }

  .items-list {
    padding: 0.5rem;
  }

  .item-card {
    padding: 8px;
  }

  .card-top {
    gap: 8px;
  }

  .item-icon {
    font-size: 1.2rem;
  }

  .item-title {
    font-size: 0.85rem;
  }

  .item-amount {
    font-size: 0.9rem;
  }
}
.heatmap-controls {
  background: rgba(139, 92, 246, 0.1);
  padding: 12px;
  border-radius: 8px;
  margin-top: 10px;
  margin-bottom: 10px;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.control-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-group label {
  font-size: 0.8rem;
  margin-bottom: 5px;
  color: #e5e7eb;
  font-weight: 600;
}

.control-group input[type="range"] {
  width: 100%;
  accent-color: #ef4444; /* Czerwony motyw heatmapy */
  cursor: pointer;
}

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>