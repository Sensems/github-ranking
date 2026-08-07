<script setup lang="ts">
import type { LeaderboardPayload } from '~/types/leaderboard'
import { BOARD_META } from '~/utils/boardMeta'

const boardType = 'total' as const
const { data, error } = await useFetch<LeaderboardPayload>(`/api/leaderboards/${boardType}`)
const payload = data.value ?? { type: boardType, generated_at: null, items: [] }

useHead({
  title: `${BOARD_META[boardType].title} - GitHub Star 趋势榜`,
  meta: [{ name: 'description', content: BOARD_META[boardType].description }],
})
</script>

<template>
  <LeaderboardView :board-type="boardType" :payload="payload" :error="error" />
</template>
