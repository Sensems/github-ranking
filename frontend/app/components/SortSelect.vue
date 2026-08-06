<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <Select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', String($event))"
  >
    <SelectTrigger class="w-40">
      <SelectValue placeholder="排序" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="stars">按 Star 数</SelectItem>
      <SelectItem value="growth">按增速</SelectItem>
      <SelectItem value="forks">按 Fork 数</SelectItem>
    </SelectContent>
  </Select>
</template>
