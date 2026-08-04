<script setup lang="ts">
import totalData from '~/data/leaderboards/total.json'
import { useLeaderboard } from '~/composables/useLeaderboard'
import type { LeaderboardPayload } from '~/types/leaderboard'

const payload = totalData as LeaderboardPayload
const { query, language, sortBy, languages, sorted } = useLeaderboard(payload.items, 'total')
useHead({
  title: '总 Star 榜 - GitHub Star 趋势榜',
  meta: [{ name: 'description', content: 'GitHub Star 总数最高的 Top 100 开源项目' }],
})
</script>

<template>
  <div>
    <LeaderboardTabs />
    <h1 class="mb-4 text-lg font-bold text-gray-900">总 Star 榜</h1>
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <SearchBox v-model="query" />
      <LanguageFilter v-model="language" :options="languages" />
      <SortSelect v-model="sortBy" />
    </div>
    <div class="grid gap-4">
      <RepoCard v-for="item in sorted" :key="item.repo_id" :item="item" board-type="total" />
    </div>
  </div>
</template>
