<template>
    <div class="heatmap-container" v-if="heatmapData && heatmapData.length > 0">
        <!-- Hexagon polygons rendered as Leaflet polygons -->
        <l-polygon v-for="hexagon in heatmapData" :key="hexagon.hexagon_id"
            :lat-lngs="hexagonToLatLngs(hexagon.geometry)" :color="getHexagonColor(hexagon.weight)"
            :fillOpacity="getHexagonOpacity(hexagon.weight)" :weight="1">
            <l-popup>
                <div class="hexagon-popup">
                    <strong>Wydatki w obszarze</strong>
                    <div>{{ formatWeight(hexagon.weight) }} zł</div>
                    <div v-if="hexagon.point_count > 0" class="small">
                        ({{ hexagon.point_count }} {{ hexagon.point_count === 1 ? 'pozycja' : 'pozycji' }})
                    </div>
                </div>
            </l-popup>
        </l-polygon>

        <!-- Heatmap legend -->
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
}

const props = withDefaults(defineProps<Props>(), {
    maxWeight: undefined,
    showLegend: true,
});

// Calculate max weight from data if not provided
const effectiveMaxWeight = computed(() => {
    if (props.maxWeight !== undefined) {
        return props.maxWeight;
    }
    if (!props.heatmapData || props.heatmapData.length === 0) {
        return 1;
    }
    return Math.max(...props.heatmapData.map(h => h.weight));
});

// Generate color legend
const colorLegend = computed(() => {
    return generateColorScaleLegend(effectiveMaxWeight.value, 5, 'zł');
});

// Convert GeoJSON polygon to Leaflet LatLng array
function hexagonToLatLngs(geometry: GeoJSON.Polygon): Array<[number, number]> {
    if (!geometry || !geometry.coordinates || !geometry.coordinates[0]) {
        return [];
    }
    // GeoJSON uses [lon, lat], Leaflet uses [lat, lon]
    return geometry.coordinates[0].map(([lon, lat]) => [lat, lon]);
}

// Get color for hexagon based on weight
function getHexagonColor(weight: number): string {
    const intensity = calculateIntensity(weight, effectiveMaxWeight.value);
    return intensityToColor(intensity);
}

// Get opacity for hexagon
function getHexagonOpacity(weight: number): number {
    const intensity = calculateIntensity(weight, effectiveMaxWeight.value);
    return intensityToOpacity(intensity);
}

// Format weight for display
function formatWeight(weight: number): string {
    return weight.toFixed(2);
}
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
    bottom: 20px;
    right: 20px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 12px;
    max-width: 200px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    z-index: 400;
    font-size: 12px;
}

.legend-title {
    font-weight: bold;
    margin-bottom: 8px;
    color: #333;
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
    border-radius: 2px;
    border: 1px solid #ccc;
    flex-shrink: 0;
}

.legend-label {
    color: #666;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.hexagon-popup {
    padding: 8px;
    min-width: 200px;
    font-size: 13px;
}

.hexagon-popup strong {
    display: block;
    margin-bottom: 4px;
    color: #333;
}

.hexagon-popup .small {
    margin-top: 4px;
    color: #999;
    font-size: 11px;
}
</style>
