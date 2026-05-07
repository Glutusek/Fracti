<template>
    <div class="heatmap-container" v-if="styledHeatmapData && styledHeatmapData.length > 0">
        <l-polygon
            v-for="hexagon in styledHeatmapData"
            :key="hexagon.hexagon_id"
            :lat-lngs="hexagon.latLngs"
            :color="hexagon.color"
            :fill-color="hexagon.color"
            :fill-opacity="hexagon.opacity"
            :opacity="0.1"
            :weight="1"
        >
            <l-popup>
                <div class="hexagon-popup">
                    <strong>Wydatki w obszarze</strong>
                    <div>{{ hexagon.formattedWeight }} zł</div>
                    <div v-if="hexagon.point_count > 0" class="small">
                        ({{ hexagon.point_count }} {{ hexagon.point_count === 1 ? 'pozycja' : 'pozycji' }})
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
             rawLatLngs = hexagon.geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);
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

const colorLegend = computed(() => {
    return generateColorScaleLegend(effectiveMaxWeight.value, 5, 'zł');
});
</script>

<style scoped>
.heatmap-container { position: relative; width: 100%; height: 100%; }
.heatmap-empty { padding: 20px; text-align: center; color: #999; font-size: 14px; }
.heatmap-legend {
    position: absolute; bottom: 20px; right: 20px; background: rgba(17, 24, 39, 0.95);
    border: 1px solid rgba(139, 92, 246, 0.5); border-radius: 8px; padding: 12px;
    max-width: 200px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5); z-index: 400; font-size: 12px;
    color: #e5e7eb;
}
.legend-title { font-weight: bold; margin-bottom: 8px; color: #a78bfa; }
.legend-item { display: flex; align-items: center; margin-bottom: 6px; gap: 8px; }
.legend-color { width: 20px; height: 20px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.2); flex-shrink: 0; }
.legend-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hexagon-popup { padding: 8px; min-width: 200px; font-size: 13px; color: #e5e7eb; }
.hexagon-popup strong { display: block; margin-bottom: 4px; color: #a78bfa; }
.hexagon-popup .small { margin-top: 4px; color: #9ca3af; font-size: 11px; }
</style>