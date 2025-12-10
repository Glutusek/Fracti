<template>

  <div class="map-layout">
    <div class="map-container">
      <l-map
        ref="map"
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
          :key="item.id"
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
                <span>{{ item.date }}</span> •
                <span :class="['tag', item.category]">{{ item.category }}</span>
              </div>

              <hr class="popup-divider" />

              <div v-if="item.type === 'receipt'" class="products-preview">
                <small>Pozycje na paragonie:</small>
                <ul>
                  <li v-for="(prod, index) in item.products" :key="index">
                    {{ prod.name }} - {{ prod.price }} zł
                  </li>
                </ul>
                <div class="total">Suma: {{ item.amount }} zł</div>
              </div>

              <div v-else class="single-preview">
                Opis: {{ item.description || 'Brak opisu' }}
                <div class="total">Kwota: {{ item.amount }} zł</div>
              </div>
            </div>
          </l-popup>
        </l-marker>
      </l-map>
    </div>

    <div class="sidebar">
      <div class="sidebar-header">
        <h2>Aktualne Rozliczenie</h2>
        <div class="actions-row">
          <router-link to="/ocr" class="btn-scan">📷 Skanuj Paragon</router-link>
          <button class="btn-add" @click="addManualItem">📍 Dodaj Pozycję</button>
        </div>

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
          :key="item.id"
          class="item-card"
          @click="flyToMarker(item.coords)"
        >
          <template v-if="item.type === 'receipt'">
            <div class="card-header">
              <span class="store-name">🧾 {{ item.name }}</span>
              <span class="amount">{{ item.amount }} zł</span>
            </div>
            <div class="card-products">
              <div v-for="(prod, i) in item.products" :key="i" class="product-row">
                <span>{{ prod.name }}</span>
                <span>{{ prod.price }} zł</span>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="card-header">
              <span class="item-name">📍 {{ item.name }}</span>
              <span class="amount">{{ item.amount }} zł</span>
            </div>
            <div class="card-desc">{{ item.description }}</div>
          </template>

          <div class="card-footer">
            <span class="date">{{ item.date }}</span>
            <span :class="['category-badge', item.category]">{{ item.category }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { LMap, LTileLayer, LMarker, LPopup, LIcon } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'

// --- TYPY DANYCH (TypeScript) ---
interface Product {
  name: string;
  price: number;
}

interface ExpenseItem {
  id: number;
  type: 'receipt' | 'single'; // KLUCZOWE: Rozróżnienie typów
  name: string; // Nazwa sklepu (paragon) lub nazwa wydatku (pojedynczy)
  amount: number;
  date: string;
  category: 'food' | 'transport' | 'entertainment' | 'other';
  coords: [number, number];
  products?: Product[]; // Tylko dla paragonów
  description?: string; // Tylko dla pojedynczych
}

// --- KONFIGURACJA MAPY ---
const zoom = ref(13)
const center = ref([54.352, 18.646]) // Gdańsk
const activeFilter = ref('all')

// --- IKONY ---
const shadowUrl = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png'
const markerIcons: any = {
  food: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  transport: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  entertainment: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  default: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png'
}
const getIconUrl = (cat: string) => markerIcons[cat] || markerIcons.default

// --- DANE (MOCKUP) ---
const items = ref<ExpenseItem[]>([
  // 1. To jest CAŁY PARAGON (Jeden marker, wiele produktów)
  {
    id: 1,
    type: 'receipt',
    name: 'Biedronka',
    amount: 45.50,
    date: '2024-12-08',
    category: 'food',
    coords: [54.35, 18.64],
    products: [
      { name: 'Mleko', price: 3.50 },
      { name: 'Chleb', price: 4.00 },
      { name: 'Ser żółty', price: 12.00 },
      { name: 'Warzywa', price: 26.00 }
    ]
  },
  // 2. To jest POJEDYNCZY WYDATEK (Jeden marker, brak pod-produktów)
  {
    id: 2,
    type: 'single',
    name: 'Uber do pracy',
    amount: 25.00,
    date: '2024-12-08',
    category: 'transport',
    coords: [54.36, 18.65],
    description: 'Spóźniłem się na autobus'
  },
  // 3. Kolejny PARAGON
  {
    id: 3,
    type: 'receipt',
    name: 'Multikino',
    amount: 90.00,
    date: '2024-12-07',
    category: 'entertainment',
    coords: [54.34, 18.63],
    products: [
      { name: 'Bilety x2', price: 60.00 },
      { name: 'Popcorn duży', price: 30.00 }
    ]
  }
])

const filterOptions = [
  { label: 'Wszystkie', value: 'all' },
  { label: 'Spożywcze', value: 'food' },
  { label: 'Transport', value: 'transport' },
]

// --- LOGIKA ---
const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value
  return items.value.filter(i => i.category === activeFilter.value)
})

const flyToMarker = (coords: [number, number]) => {
  center.value = coords
  zoom.value = 15
}

const addManualItem = () => {
  alert('Otworzyć modal dodawania pojedynczego wydatku?')
}
</script>

<style scoped>
/* UKŁAD */
.map-layout { display: flex; height: calc(100vh - 73px); overflow: hidden; }
.map-container { flex: 2; position: relative; z-index: 1; }
.sidebar { flex: 1; background: #111827; border-left: 1px solid rgba(139, 92, 246, 0.2); display: flex; flex-direction: column; min-width: 350px; }

/* HEADER SIDEBARA */
.sidebar-header { padding: 1.5rem; background: rgba(17, 24, 39, 0.95); box-shadow: 0 4px 6px rgba(0,0,0,0.3); z-index: 2; }
.sidebar-header h2 { color: white; margin: 0 0 1rem 0; font-size: 1.25rem; }

.actions-row { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
.btn-scan, .btn-add { flex: 1; padding: 0.6rem; border-radius: 8px; text-align: center; font-weight: 600; border: none; cursor: pointer; color: white; text-decoration: none; font-size: 0.9rem; transition: 0.2s; }
.btn-scan { background: #8b5cf6; }
.btn-scan:hover { background: #7c3aed; }
.btn-add { background: rgba(255,255,255,0.1); }
.btn-add:hover { background: rgba(255,255,255,0.15); }

/* FILTRY */
.filters { display: flex; gap: 0.5rem; overflow-x: auto; padding-bottom: 0.5rem; }
.filter-chip { background: transparent; border: 1px solid #374151; color: #9ca3af; padding: 0.25rem 0.75rem; border-radius: 99px; cursor: pointer; white-space: nowrap; }
.filter-chip.active { border-color: #8b5cf6; color: #a78bfa; background: rgba(139, 92, 246, 0.1); }

/* LISTA */
.items-list { flex: 1; overflow-y: auto; padding: 1rem; }
.item-card { background: rgba(31, 41, 55, 0.5); border: 1px solid rgba(255,255,255,0.05); padding: 1rem; border-radius: 12px; margin-bottom: 0.75rem; cursor: pointer; transition: 0.2s; }
.item-card:hover { border-color: #8b5cf6; transform: translateX(2px); }

.card-header { display: flex; justify-content: space-between; font-weight: bold; color: white; margin-bottom: 0.5rem; }
.card-desc { color: #9ca3af; font-size: 0.9rem; margin-bottom: 0.5rem; font-style: italic; }

/* STYL DLA PRODUKTÓW W PARAGONIE */
.card-products { background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.85rem; }
.product-row { display: flex; justify-content: space-between; color: #d1d5db; margin-bottom: 0.25rem; }

.card-footer { display: flex; justify-content: space-between; font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem; }
.category-badge { text-transform: capitalize; }
.category-badge.food { color: #34d399; }
.category-badge.transport { color: #f87171; }
.category-badge.entertainment { color: #60a5fa; }

/* POPUP MAPY */
.popup-content { color: #1f2937; min-width: 150px; }
.popup-meta { font-size: 0.8rem; color: #6b7280; margin-bottom: 0.5rem; }
.popup-divider { border: 0; border-top: 1px solid #e5e7eb; margin: 0.5rem 0; }
.products-preview ul { padding-left: 1.2rem; margin: 0; font-size: 0.85rem; }
.total { font-weight: bold; margin-top: 0.5rem; text-align: right; }
</style>