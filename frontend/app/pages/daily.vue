<script setup lang="ts">
import { useLeaderboard } from '~/composables/useLeaderboard'
import type { LeaderboardPayload } from '~/types/leaderboard'

const { data, error } = await useFetch<LeaderboardPayload>('/api/leaderboards/daily')
const payload = data.value ?? { type: 'daily', generated_at: null, items: [] }
const { query, language, sortBy, languages, sorted } = useLeaderboard(payload.items, 'daily')
useHead({
  title: '日增速榜 - GitHub Star 趋势榜',
  meta: [{ name: 'description', content: '当日 Star 增速最快的 Top 100 开源项目' }],
})
</script>

<template>
  <div>
    <LeaderboardTabs />
    <div class="mb-2 flex items-baseline justify-between">
      <h1 class="text-lg font-bold text-gray-900">日增速榜</h1>
      <span v-if="payload.generated_at" class="text-xs text-gray-400">数据更新于 {{ payload.generated_at }}</span>
    </div>
    <div
      v-if="error"
      class="rounded-xl border border-dashed border-red-200 bg-white p-12 text-center text-sm text-red-500"
    >
      加载失败，请稍后重试。
    </div>
    <template v-else>
      <div class="mb-4 flex flex-wrap items-center gap-2">
        <SearchBox v-model="query" />
        <LanguageFilter v-model="language" :options="languages" />
        <SortSelect v-model="sortBy" />
      </div>
      <div v-if="sorted.length" class="grid gap-4 md:grid-cols-2">
        <RepoCard v-for="item in sorted" :key="item.repo_id" :item="item" board-type="daily" />
      </div>
      <div v-else class="rounded-xl border border-dashed border-gray-300 bg-white p-12 text-center text-sm text-gray-400">
        该榜单暂无数据（历史数据积累中），请明天再来看看。
      </div>
    </template>
  </div>
</template>
