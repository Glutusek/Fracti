<template>
    <div class="heatmap-container" v-if="styledHeatmapData && styledHexagonsWithData.length > 0">
        <!-- Render empty hexagons as non-interactive layer (much faster) -->
        <l-polygon v-for="hexagon in styledEmptyHexagons" :key="hexagon.hexagon_id" :lat-lngs="hexagon.latLngs"
            :color="'#999'" :fill-color="'#7cb342'" :fill-opacity="gridFillOpacity" :opacity="gridOpacity" :weight="0.8"
            :interactive="false" :pointer-events="'none'" />

        <!-- Render hexagons with data as interactive polygons (with popups) -->
        <l-polygon v-for="hexagon in styledHexagonsWithData" :key="hexagon.hexagon_id" :lat-lngs="hexagon.latLngs"
            :color="hexagon.color" :fill-color="hexagon.color" :fill-opacity="hexagon.opacity" :opacity="0.8"
            :weight="1">
            <l-popup>
                <div class="hexagon-popup">
                    <strong>Wydatki w obszarze</strong>
                    <div class="total-amount">{{ hexagon.formattedWeight }} zł</div>
                    <div v-if="hexagon.point_count > 0" class="point-count">
                        {{ hexagon.point_count }} {{ hexagon.point_count === 1 ? 'pozycja' : 'pozycji' }}
                    </div>

                    <div v-if="hexagon.items && hexagon.items.length > 0" class="items-list">
                        <div class="items-title">Szczegóły:</div>
                        <div v-for="(item, idx) in hexagon.items" :key="idx" class="item" :class="item.type">
                            <div class="item-header">
                                <span class="item-type">{{ item.type === 'receipt' ? '🧾' : '📦' }}</span>
                                <div class="item-name">{{ item.name }}</div>
                            </div>
                            <div class="item-details">
                                <span class="item-amount">{{ Number(item.amount).toFixed(2) }} zł</span>
                                <span class="item-category">{{ translateCategory(item.category) }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </l-popup>
        </l-polygon>

        <div class="heatmap-legend" v-if="showLegend">
            <div class="legend-title">Intensywność wydatków</div>
            <div v-for="(item, index) in colorLegend" :key="index" class="legend-item">
                <div class="legend-color" :style="{ backgroundColor: item.color }"></div>
                <span class="legend-label">{{ item.label }}</span>
            </div>
            <div class="legend-stats">
                <small>Wyświetlono: {{ styledHexagonsWithData.length }} komórek z danymi</small>
            </div>
        </div>
    </div>

    <div v-else class="heatmap-empty">
        Brak danych heatmapy
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { LPolygon, LPopup } from '@vue-leaflet/vue-leaflet';
import {
    calculateIntensity,
    intensityToColor,
    intensityToOpacity,
    generateColorScaleLegend,
} from '@/utils/heatmapColorScale';

interface HeatmapPoint {
    hexagon_id: string;
    geometry: GeoJSON.Polygon;
    weight: number;
    center_lat: number;
    center_lng: number;
    point_count: number;
    items?: Array<{
        type: 'receipt' | 'product';
        id: string;
        name: string;
        amount: number;
        category: string;
        date: string;
        description?: string;
    }>;
}

interface Props {
    heatmapData: HeatmapPoint[] | null;
    maxWeight?: number;
    showLegend?: boolean;
    intensityMultiplier?: number;
    baseOpacity?: number;
}

const props = withDefaults(defineProps<Props>(), {
    maxWeight: undefined,
    showLegend: true,
    intensityMultiplier: 1.0,
    baseOpacity: 0.7,
});

// Dynamiczny limit z uwzględnieniem suwaka mocy (Mnożnik natężenia)
const effectiveMaxWeight = computed(() => {
    let max = 1;
    if (props.maxWeight !== undefined) {
        max = props.maxWeight;
    } else if (props.heatmapData && props.heatmapData.length > 0) {
        max = Math.max(...props.heatmapData.map(h => h.weight));
    }

    // Suwak "intensityMultiplier" obniża próg
    return Math.max(max, 0.0001) / props.intensityMultiplier;
});

// Renderujemy to przez Computed, żeby Vue widziało ruch suwaka
const styledHeatmapData = computed(() => {
    if (!props.heatmapData) return [];

    return props.heatmapData.map(hexagon => {
        const intensity = calculateIntensity(hexagon.weight, effectiveMaxWeight.value);

        let rawLatLngs: Array<[number, number]> = [];
        if (hexagon.geometry && hexagon.geometry.coordinates && hexagon.geometry.coordinates[0]) {
             rawLatLngs = hexagon.geometry.coordinates[0]
                .filter((coord): coord is [number, number] => Array.isArray(coord) && coord.length === 2)
                .map(([lon, lat]) => [lat, lon]);
        }

        return {
            ...hexagon,
            latLngs: rawLatLngs,
            color: intensityToColor(intensity),
            opacity: Math.min(1, Math.max(0, intensityToOpacity(intensity) * props.baseOpacity)),
            formattedWeight: hexagon.weight.toFixed(2)
        };
    });
});

// Split hexagons into empty and with data for optimized rendering
const styledEmptyHexagons = computed(() => {
    return styledHeatmapData.value.filter(h => h && (h.weight === 0 || h.weight < 0.01));
});

const styledHexagonsWithData = computed(() => {
    return styledHeatmapData.value.filter(h => h && h.weight > 0.01);
});

// Grid opacity based on baseOpacity slider
const gridOpacity = computed(() => {
    return Math.max(0.08, props.baseOpacity * 0.35);
});

const gridFillOpacity = computed(() => {
    return Math.max(0.1, props.baseOpacity * 0.35);
});

const colorLegend = computed(() => {
    return generateColorScaleLegend(effectiveMaxWeight.value, 5, 'zł');
});

// Tłumaczenie kategorii na polski
const categoryTranslations: { [key: string]: string } = {
    'food': 'Jedzenie',
    'groceries': 'Artykuły spożywcze',
    'restaurant': 'Restauracja',
    'cafe': 'Kawiarnia',
    'shopping': 'Zakupy',
    'clothing': 'Odzież',
    'electronics': 'Elektronika',
    'accommodation': 'Noclegi',
    'hotel': 'Hotel',
    'transport': 'Transport',
    'taxi': 'Taxi',
    'gas': 'Paliwo',
    'entertainment': 'Rozrywka',
    'cinema': 'Kino',
    'theater': 'Teatr',
    'sports': 'Sport',
    'health': 'Zdrowie',
    'pharmacy': 'Apteka',
    'doctor': 'Lekarz',
    'services': 'Usługi',
    'other': 'Inne',
    // Uppercase variations
    'FOOD': 'Jedzenie',
    'GROCERIES': 'Artykuły spożywcze',
    'RESTAURANT': 'Restauracja',
    'CAFE': 'Kawiarnia',
    'SHOPPING': 'Zakupy',
    'CLOTHING': 'Odzież',
    'ELECTRONICS': 'Elektronika',
    'ACCOMMODATION': 'Noclegi',
    'HOTEL': 'Hotel',
    'TRANSPORT': 'Transport',
    'TAXI': 'Taxi',
    'GAS': 'Paliwo',
    'ENTERTAINMENT': 'Rozrywka',
    'CINEMA': 'Kino',
    'THEATER': 'Teatr',
    'SPORTS': 'Sport',
    'HEALTH': 'Zdrowie',
    'PHARMACY': 'Apteka',
    'DOCTOR': 'Lekarz',
    'SERVICES': 'Usługi',
    'OTHER': 'Inne',
};

const translateCategory = (category: string | null | undefined): string => {
    if (!category) return 'Inne';

    const trimmed = category.trim();

    // Spróbuj najpierw oryginalną wartość (ACCOMMODATION, Shopping, itd.)
    if (categoryTranslations[trimmed]) {
        return categoryTranslations[trimmed];
    }

    // Spróbuj znormalizowaną (lowercase)
    const normalized = trimmed.toLowerCase();
    if (categoryTranslations[normalized]) {
        return categoryTranslations[normalized];
    }

    // Fallback: Title Case (rozdziela underscore i spacje)
    return trimmed
        .toLowerCase()
        .replace(/_/g, ' ')
        .split(' ')
        .filter(word => word.length > 0)
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};
</script>

<style scoped>
.heatmap-container {
    position: relative;
    width: 100%;
    height: 100%;
}

.heatmap-empty {
    padding: 20px;
    text-align: center;
    color: #999;
    font-size: 14px;
}

.heatmap-legend {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(17, 24, 39, 0.95);
    border: 1px solid rgba(139, 92, 246, 0.5);
    border-radius: 8px;
    padding: 12px;
    max-width: 200px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    z-index: 400;
    font-size: 12px;
    color: #e5e7eb;
}

.legend-title {
    font-weight: bold;
    margin-bottom: 8px;
    color: #a78bfa;
}

.legend-item {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    gap: 8px;
}

.legend-color {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    flex-shrink: 0;
}

.legend-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.legend-stats {
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.2);
    color: #9ca3af;
    font-size: 11px;
}

.hexagon-popup-container {
    z-index: 1000;
}

.hexagon-popup {
    padding: 12px;
    min-width: 250px;
    font-size: 13px;
    color: #1f2937;
    background: #ffffff;
    border-radius: 6px;
}

.hexagon-popup strong {
    display: block;
    margin-bottom: 2px;
    color: #059669;
    font-size: 14px;
}

.hexagon-popup .popup-header {
    margin-bottom: 8px;
}

.hexagon-popup .point-count {
    margin-bottom: 8px;
    color: #6b7280;
    font-size: 12px;
}

.hexagon-popup .total-amount {
    font-weight: bold;
    color: #059669;
    font-size: 15px;
    margin-top: 2px;
}

.items-list {
    margin-top: 8px;
    border-top: 1px solid #e5e7eb;
    padding-top: 8px;
    max-height: 300px;
    overflow-y: auto;
}

.items-title {
    font-size: 11px;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.item {
    margin-bottom: 6px;
    padding: 6px 8px;
    background: #f9fafb;
    border-left: 3px solid #d1d5db;
    border-radius: 3px;
    font-size: 12px;
}

.item.receipt {
    border-left-color: #3b82f6;
    background: #eff6ff;
}

.item.product {
    border-left-color: #f59e0b;
    background: #fffbf0;
}

.item-header {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    margin-bottom: 4px;
}

.item-type {
    font-size: 14px;
    flex-shrink: 0;
}

.item-name {
    font-weight: 500;
    color: #1f2937;
    word-break: break-word;
    flex: 1;
}

.item-details {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #6b7280;
    flex-wrap: wrap;
}

.item-amount {
    font-weight: 600;
    color: #059669;
}

.item-category {
    color: #6b7280;
    background: #e5e7eb;
    padding: 2px 6px;
    border-radius: 2px;
}
</style>