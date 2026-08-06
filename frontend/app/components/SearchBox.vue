<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <Input
    :model-value="modelValue"
    type="search"
    placeholder="搜索项目/关键词"
    class="w-full md:w-64"
    @update:model-value="$emit('update:modelValue', String($event))"
  />
</template>
