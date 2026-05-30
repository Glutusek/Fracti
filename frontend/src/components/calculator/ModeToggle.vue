<template>
  <div class="mode-toggle">
    <button
      :class="['mode-btn', modelValue === 'simple' ? 'active' : '']"
      @click="$emit('update:modelValue', 'simple')"
    >
      Prosty
    </button>
    <button
      :class="['mode-btn', modelValue === 'advanced' ? 'active' : '']"
      @click="$emit('update:modelValue', 'advanced')"
    >
      Zaawansowany (Mapa)
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: 'simple' | 'advanced' }>()
defineEmits<{ (e: 'update:modelValue', val: 'simple' | 'advanced'): void }>()
</script>

<style scoped>
.mode-toggle {
  display: flex;
  gap: 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(139, 92, 246, 0.4);
  width: fit-content;
}
.mode-btn {
  padding: 8px 20px;
  background: transparent;
  color: #a0aec0;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}
.mode-btn.active {
  background: #8b5cf6;
  color: #fff;
}
.mode-btn:hover:not(.active) {
  background: rgba(139, 92, 246, 0.1);
  color: #e2e8f0;
}
</style>
