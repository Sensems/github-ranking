<script setup lang="ts">
import type { BoardType, LeaderboardItem } from '~/types/leaderboard'

defineProps<{ item: LeaderboardItem; boardType: BoardType }>()

const growthKeys = ['daily', 'weekly', 'monthly', 'yearly'] as const
const growthLabels: Record<string, string> = {
  daily: '今日',
  weekly: '本周',
  monthly: '本月',
  yearly: '今年',
}

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
</script>

<template>
  <article class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <span class="mr-2 inline-block rounded bg-gray-100 px-1.5 py-0.5 text-xs font-semibold text-gray-500">#{{ item.rank }}</span>
        <a :href="item.html_url" target="_blank" rel="noopener" class="font-semibold text-gray-900 hover:text-blue-600">
          {{ item.repo_name }}
        </a>
        <span v-if="item.language" class="ml-2 inline-block rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
          {{ item.language }}
        </span>
      </div>
      <div class="shrink-0 text-lg font-bold text-gray-900">★ {{ fmt(item.stars) }}</div>
    </div>

    <div class="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-sm text-gray-600">
      <span v-for="k in growthKeys" :key="k">
        {{ growthLabels[k] }}：
        <span class="font-medium" :class="(item.growth[k] ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ fmtSigned(item.growth[k]) }}
        </span>
      </span>
    </div>

    <p v-if="item.summary" class="mt-2 text-sm leading-relaxed text-gray-700">
      <span class="font-medium text-gray-900">{{ item.summary.project_positioning }}</span>
      <span v-if="item.summary.core_features.length" class="ml-1">功能：{{ item.summary.core_features.join('、') }}</span>
    </p>
    <p v-else-if="item.description" class="mt-2 text-sm text-gray-500">{{ item.description }}</p>
    <p v-else class="mt-2 text-sm text-gray-400">暂无摘要</p>

    <div class="mt-3">
      <a :href="item.html_url" target="_blank" rel="noopener" class="text-sm font-medium text-blue-600 hover:underline">
        查看仓库 →
      </a>
    </div>
  </article>
</template>
