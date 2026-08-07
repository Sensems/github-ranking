<script setup lang="ts">
import { useLeaderboard } from '~/composables/useLeaderboard'
import type { LeaderboardPayload } from '~/types/leaderboard'

const { data, error } = await useFetch<LeaderboardPayload>('/api/leaderboards/yearly')
const payload = data.value ?? { type: 'yearly', generated_at: null, items: [] }
const { query, language, sortBy, languages, sorted } = useLeaderboard(payload.items, 'yearly')
useHead({
  title: '年增速榜 - GitHub Star 趋势榜',
  meta: [{ name: 'description', content: '当年 Star 增速最快的 Top 100 开源项目' }],
})
</script>

<template>
  <div class="board-page">
    <LeaderboardTabs />
    <div class="mb-2 flex items-baseline justify-between">
      <h1 class="text-lg font-semibold text-foreground">年增速榜</h1>
      <span v-if="payload.generated_at" class="text-xs text-muted-foreground">数据更新于 {{ payload.generated_at }}</span>
    </div>
    <Alert v-if="error" variant="destructive">
      <AlertDescription>加载失败，请稍后重试。</AlertDescription>
    </Alert>
    <template v-else>
      <div class="board-toolbar mb-4 flex flex-wrap items-center gap-2">
        <SearchBox v-model="query" />
        <LanguageFilter v-model="language" :options="languages" />
        <SortSelect v-model="sortBy" />
      </div>
      <div v-if="sorted.length" class="board-grid grid gap-4 md:grid-cols-2">
        <div
          v-for="(item, index) in sorted"
          :key="item.repo_id"
          :style="{ '--stagger': index }"
        >
          <RepoCard :item="item" board-type="yearly" />
        </div>
      </div>
      <Alert v-else>
        <AlertDescription>该榜单暂无数据（历史数据积累中），请明天再来看看。</AlertDescription>
      </Alert>
    </template>
  </div>
</template>
