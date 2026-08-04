<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <input
    :value="modelValue"
    type="search"
    placeholder="搜索项目/关键词"
    class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none md:w-64"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>
