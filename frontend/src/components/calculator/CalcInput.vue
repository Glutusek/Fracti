<template>
  <div class="calc-input">
    <label>{{ label }}</label>
    <input
      type="number"
      :value="modelValue"
      :min="min"
      :step="step"
      @input="$emit('update:modelValue', parseFloat(($event.target as HTMLInputElement).value) || 0)"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: number
  label: string
  min?: number
  step?: number
}>()
defineEmits<{ (e: 'update:modelValue', val: number): void }>()
</script>

<style scoped>
.calc-input label {
  display: block;
  color: #a0aec0;
  font-size: 0.8rem;
  margin-bottom: 4px;
}
.calc-input input {
  width: 100%;
  background: #1e2533;
  border: 1px solid rgba(255,255,255,0.1);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}
.calc-input input:focus {
  outline: none;
  border-color: #8b5cf6;
}
</style>
