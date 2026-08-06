<script setup lang="ts">
defineProps<{ modelValue: string; options: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <Select
    :model-value="modelValue || 'all'"
    @update:model-value="(value) => emit('update:modelValue', value === 'all' ? '' : String(value))"
  >
    <SelectTrigger class="w-40">
      <SelectValue placeholder="全部语言" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="all">全部语言</SelectItem>
      <SelectItem v-for="lang in options" :key="lang" :value="lang">
        {{ lang }}
      </SelectItem>
    </SelectContent>
  </Select>
</template>
