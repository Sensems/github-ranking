<script setup lang="ts">
import type { BoardType } from '~/types/leaderboard'

const props = defineProps<{ modelValue: string; boardType: BoardType }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()

const growthLabel = computed(() =>
  props.boardType === 'total' ? '按今日新增' : '按增速',
)
</script>

<template>
  <div>
    <label class="sr-only" for="board-sort">排序方式</label>
    <Select
      :model-value="modelValue"
      @update:model-value="$emit('update:modelValue', String($event))"
    >
      <SelectTrigger id="board-sort" class="h-8 w-32 px-2.5 py-1 text-xs">
        <SelectValue placeholder="排序" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="stars">按 Star 数</SelectItem>
        <SelectItem value="growth">{{ growthLabel }}</SelectItem>
        <SelectItem value="forks">按 Fork 数</SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>
