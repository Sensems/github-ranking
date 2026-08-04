<script setup lang="ts">
import monthlyData from '~/data/leaderboards/monthly.json'
import { useLeaderboard } from '~/composables/useLeaderboard'
import type { LeaderboardPayload } from '~/types/leaderboard'

const payload = monthlyData as LeaderboardPayload
const { query, language, sortBy, languages, sorted } = useLeaderboard(payload.items, 'monthly')
useHead({
  title: '月增速榜 - GitHub Star 趋势榜',
  meta: [{ name: 'description', content: '当月 Star 增速最快的 Top 100 开源项目' }],
})
</script>

<template>
  <div>
    <LeaderboardTabs />
    <h1 class="mb-4 text-lg font-bold text-gray-900">月增速榜</h1>
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <SearchBox v-model="query" />
      <LanguageFilter v-model="language" :options="languages" />
      <SortSelect v-model="sortBy" />
    </div>
    <div class="grid gap-4">
      <RepoCard v-for="item in sorted" :key="item.repo_id" :item="item" board-type="monthly" />
    </div>
  </div>
</template>
