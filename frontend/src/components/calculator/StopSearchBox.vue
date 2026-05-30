<template>
  <div class="stop-search">
    <input
      v-model="query"
      class="search-input"
      :placeholder="placeholder || 'Szukaj miejsca...'"
      @input="onInput"
      @keydown.down.prevent="moveSelection(1)"
      @keydown.up.prevent="moveSelection(-1)"
      @keydown.enter.prevent="selectCurrent"
      @keydown.escape="close"
      @focus="onFocus"
    />
    <ul v-if="showDropdown && results.length" class="dropdown">
      <li
        v-for="(r, i) in results"
        :key="r.place_id"
        :class="['dropdown-item', i === selectedIdx ? 'selected' : '']"
        @mousedown.prevent="selectResult(r)"
      >
        {{ r.display_name }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { NominatimResult } from '../../types/trip'
import { searchAddress } from '../../services/nominatim.service'

const props = defineProps<{
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'select', result: NominatimResult): void
}>()

const query = ref('')
const results = ref<NominatimResult[]>([])
const showDropdown = ref(false)
const selectedIdx = ref(-1)
let debounceTimer: ReturnType<typeof setTimeout> | null = null
let abortController: AbortController | null = null

function onInput() {
  selectedIdx.value = -1
  if (debounceTimer) clearTimeout(debounceTimer)
  if (query.value.length < 3) {
    results.value = []
    showDropdown.value = false
    return
  }
  debounceTimer = setTimeout(doSearch, 400)
}

async function doSearch() {
  if (abortController) abortController.abort()
  abortController = new AbortController()
  try {
    const data = await searchAddress(query.value, abortController.signal)
    results.value = data
    showDropdown.value = data.length > 0
  } catch {
    // aborted or network error
  }
}

function moveSelection(dir: 1 | -1) {
  if (!results.value.length) return
  selectedIdx.value = Math.max(
    -1,
    Math.min(results.value.length - 1, selectedIdx.value + dir),
  )
}

function selectCurrent() {
  if (selectedIdx.value >= 0) {
    const r = results.value[selectedIdx.value]
    if (r) selectResult(r)
  }
}

function selectResult(r: NominatimResult) {
  emit('select', r)
  query.value = ''
  results.value = []
  showDropdown.value = false
}

function close() {
  showDropdown.value = false
}

function onFocus() {
  if (results.value.length) showDropdown.value = true
}
</script>

<style scoped>
.stop-search {
  position: relative;
}
.search-input {
  width: 100%;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 7px 12px;
  border-radius: 6px;
  font-size: 0.875rem;
  box-sizing: border-box;
}
.search-input:focus {
  outline: none;
  border-color: #8b5cf6;
}
.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #1e2533;
  border: 1px solid rgba(139,92,246,0.3);
  border-radius: 6px;
  margin-top: 2px;
  z-index: 1000;
  max-height: 240px;
  overflow-y: auto;
  list-style: none;
  padding: 4px 0;
  margin: 4px 0 0;
}
.dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.8rem;
  color: #a0aec0;
  line-height: 1.3;
}
.dropdown-item:hover,
.dropdown-item.selected {
  background: rgba(139,92,246,0.15);
  color: #e2e8f0;
}
</style>
