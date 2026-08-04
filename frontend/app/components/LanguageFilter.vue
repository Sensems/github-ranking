<script setup lang="ts">
defineProps<{ modelValue: string; options: string[] }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <select
    :value="modelValue"
    class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
    @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
  >
    <option value="">全部语言</option>
    <option v-for="lang in options" :key="lang" :value="lang">{{ lang }}</option>
  </select>
</template>
