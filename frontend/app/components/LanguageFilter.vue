<script setup lang="ts">
defineProps<{ modelValue: string; options: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <div>
    <label class="sr-only" for="board-language">语言筛选</label>
    <Select
      :model-value="modelValue || 'all'"
      @update:model-value="(value) => emit('update:modelValue', value === 'all' ? '' : String(value))"
    >
      <SelectTrigger id="board-language" class="h-8 w-32 px-2.5 py-1 text-xs">
        <SelectValue placeholder="全部语言" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">全部语言</SelectItem>
        <SelectItem v-for="lang in options" :key="lang" :value="lang">
          {{ lang }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>
