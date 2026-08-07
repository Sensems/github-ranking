<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <div class="w-full md:w-52">
    <label class="sr-only" for="board-search">搜索项目或关键词</label>
    <Input
      id="board-search"
      :model-value="modelValue"
      type="search"
      placeholder="搜索项目/关键词"
      class="h-8 w-full px-2.5 py-1 text-xs"
      @update:model-value="$emit('update:modelValue', String($event))"
    />
  </div>
</template>
