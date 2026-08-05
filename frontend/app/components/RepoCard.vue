<script setup lang="ts">
import { computed, ref } from 'vue'
import type { BoardType, LeaderboardItem, Summary } from '~/types/leaderboard'

const props = defineProps<{ item: LeaderboardItem; boardType: BoardType }>()

const growthLabels: Record<Exclude<BoardType, 'total'>, string> = {
  daily: '今日',
  weekly: '本周',
  monthly: '本月',
  yearly: '今年',
}

const summary = ref<Summary | null>(null)
const expanded = ref(false)
const loading = ref(false)
const error = ref('')
const hasSummaryLocal = ref(props.item.has_summary ?? false)

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

async function onSummaryClick() {
  if (expanded.value && summary.value) {
    expanded.value = false
    return
  }
  if (summary.value) {
    expanded.value = true
    return
  }
  loading.value = true
  error.value = ''
  try {
    const path = `/api/repos/${props.item.repo_id}/summary`
    const res = hasSummaryLocal.value
      ? await $fetch<{ repo_id: number; summary: Summary }>(path)
      : await $fetch<{ repo_id: number; summary: Summary }>(path, { method: 'POST' })
    summary.value = res.summary
    expanded.value = true
    hasSummaryLocal.value = true
  } catch {
    error.value = '概况生成失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <span class="mr-2 inline-block rounded bg-gray-100 px-1.5 py-0.5 text-xs font-semibold text-gray-500">#{{ item.rank }}</span>
        <a :href="item.html_url" target="_blank" rel="noopener" class="font-semibold text-gray-900 hover:text-blue-600">
          {{ item.repo_name }}
        </a>
        <span class="ml-2 inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
          {{ display(item.language) }}
        </span>
      </div>
      <div class="shrink-0 text-lg font-bold text-gray-900">★ {{ fmt(item.stars) }}</div>
    </div>

    <div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-sm text-gray-600">
      <span>Forks {{ fmt(item.forks) }}</span>
      <span>Open Issues {{ display(item.open_issues) }}</span>
      <span>Last Commit {{ fmtDate(item.pushed_at) }}</span>
    </div>

    <div v-if="growthKey" class="mt-2 text-sm text-gray-600">
      {{ growthLabels[growthKey] }}：
      <span class="font-medium" :class="(item.growth[growthKey] ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'">
        {{ fmtSigned(item.growth[growthKey]) }}
      </span>
    </div>

    <p class="mt-2 text-sm text-gray-500">{{ display(item.description) }}</p>

    <div class="mt-3 flex flex-wrap items-center gap-3">
      <button
        type="button"
        class="text-sm font-medium text-blue-600 hover:underline disabled:opacity-50"
        :disabled="loading"
        @click="onSummaryClick"
      >
        {{ loading ? '加载中…' : hasSummaryLocal ? '查看概况' : '生成概况' }}
      </button>
      <a :href="item.html_url" target="_blank" rel="noopener" class="text-sm font-medium text-blue-600 hover:underline">
        查看仓库 →
      </a>
    </div>

    <p v-if="error" class="mt-2 text-sm text-red-500">{{ error }}</p>

    <div v-if="expanded && summary" class="mt-3 rounded-lg bg-gray-50 p-3 text-sm leading-relaxed text-gray-700">
      <p class="font-medium text-gray-900">{{ summary.project_positioning }}</p>
      <p v-if="summary.core_features.length" class="mt-1">功能：{{ summary.core_features.join('、') }}</p>
      <p v-if="summary.use_cases.length" class="mt-1">场景：{{ summary.use_cases.join('、') }}</p>
      <p v-if="summary.tech_stack.length" class="mt-1">技术栈：{{ summary.tech_stack.join('、') }}</p>
    </div>
  </article>
</template>
