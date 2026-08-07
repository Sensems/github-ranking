<script setup lang="ts">
import { computed, ref } from 'vue'
import { Badge } from '~/components/ui/badge'
import { Button } from '~/components/ui/button'
import { Card, CardContent } from '~/components/ui/card'
import type { BoardType, LeaderboardItem, Summary } from '~/types/leaderboard'

const props = defineProps<{ item: LeaderboardItem; boardType: BoardType }>()

const growthLabels: Record<Exclude<BoardType, 'total'>, string> = {
  daily: '今日',
  weekly: '本周',
  monthly: '本月',
  yearly: '今年',
}

const summary = ref<Summary | null>(props.item.summary ?? null)
const loading = ref(false)
const error = ref('')

const growthKey = computed(() => (props.boardType === 'total' ? null : props.boardType))

function fmt(n: number | null | undefined): string {
  if (n == null) return '—'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

function fmtSigned(n: number | null | undefined): string {
  if (n == null) return '数据积累中'
  return n >= 0 ? `+${n.toLocaleString('en-US')}` : n.toLocaleString('en-US')
}

function display(v: string | number | null | undefined): string {
  if (v == null || v === '') return '—'
  return String(v)
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toISOString().slice(0, 10)
}

async function onGenerateSummary() {
  if (summary.value || loading.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await $fetch<{ repo_id: number; summary: Summary }>(
      `/api/repos/${props.item.repo_id}/summary`,
      { method: 'POST' },
    )
    summary.value = res.summary
  } catch {
    error.value = '概况生成失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Card
    class="flex h-full flex-col transition-[translate,box-shadow] duration-200 ease-out hover:-translate-y-1 hover:shadow-md"
  >
    <CardContent class="flex h-full flex-col gap-3 space-y-0 p-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <Badge variant="secondary" class="mr-2">#{{ item.rank }}</Badge>
          <a
            :href="item.html_url"
            target="_blank"
            rel="noopener"
            class="font-semibold text-foreground transition-colors hover:text-primary"
          >
            {{ item.repo_name }}
          </a>
          <Badge variant="outline" class="ml-2">{{ display(item.language) }}</Badge>
        </div>
        <div class="shrink-0 text-lg font-bold">★ {{ fmt(item.stars) }}</div>
      </div>

      <div class="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
        <span>Forks {{ fmt(item.forks) }}</span>
        <span>Open Issues {{ display(item.open_issues) }}</span>
        <span>Last Commit {{ fmtDate(item.pushed_at) }}</span>
      </div>

      <div v-if="growthKey" class="text-sm text-muted-foreground">
        {{ growthLabels[growthKey] }}：
        <span
          class="font-medium"
          :class="(item.growth[growthKey] ?? 0) >= 0 ? 'text-growth-positive' : 'text-growth-negative'"
        >
          {{ fmtSigned(item.growth[growthKey]) }}
        </span>
      </div>

      <p class="line-clamp-3 text-sm text-muted-foreground">{{ display(item.description) }}</p>

      <Transition name="summary">
        <div
          v-if="summary"
          class="rounded-lg bg-muted p-3 text-sm leading-relaxed text-foreground"
        >
          <p class="font-medium">{{ summary.project_positioning }}</p>
          <p v-if="summary.core_features.length" class="mt-1 line-clamp-2">
            功能：{{ summary.core_features.join('、') }}
          </p>
          <p v-if="summary.use_cases.length" class="mt-1 line-clamp-2">
            场景：{{ summary.use_cases.join('、') }}
          </p>
          <p v-if="summary.tech_stack.length" class="mt-1 line-clamp-1">
            技术栈：{{ summary.tech_stack.join('、') }}
          </p>
        </div>
      </Transition>

      <div class="mt-auto flex flex-wrap items-center gap-3 pt-1">
        <Button
          v-if="!summary"
          type="button"
          variant="link"
          class="h-auto px-0"
          :disabled="loading"
          @click="onGenerateSummary"
        >
          {{ loading ? '加载中…' : '生成概况' }}
        </Button>
        <Button as-child variant="link" class="h-auto px-0">
          <a :href="item.html_url" target="_blank" rel="noopener">查看仓库 →</a>
        </Button>
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>
    </CardContent>
  </Card>
</template>
