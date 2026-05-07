<template>
    <div v-if="routeLatLngs.length > 1">
        <l-polyline
            :lat-lngs="routeLatLngs"
            color="#f43f5e"
            :weight="4"
            dash-array="10, 10"
            line-join="round"
        />
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { LPolyline } from '@vue-leaflet/vue-leaflet';

// Interfejs zgodny z Twoimi odfiltrowanymi danymi z MapView
interface RouteItem {
    coords: [number, number];
    date: string;
    [key: string]: any;
}

interface Props {
    items: RouteItem[];
}

const props = defineProps<Props>();

// Złota zasada: sortujemy kopię tablicy chronologicznie po dacie (od najstarszego do najnowszego)
const sortedItems = computed(() => {
    if (!props.items || props.items.length === 0) return [];

    return [...props.items]
        // Bierzemy tylko te punkty, które mają poprawne koordynaty i datę
        .filter(item => item.coords && item.coords.length === 2 && item.date)
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
});

// Wyciągamy same współrzędne dla Polyline Leafleta
const routeLatLngs = computed(() => {
    return sortedItems.value.map(item => item.coords);
});
</script>