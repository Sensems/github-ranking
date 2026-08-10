<script setup lang="ts">
import type { LeaderboardPayload } from '~/types/leaderboard'

const boardType = 'monthly' as const
const { data, error } = await useFetch<LeaderboardPayload>(`/api/leaderboards/${boardType}`)
const payload = data.value ?? { type: boardType, generated_at: null, items: [] }

useBoardSeo(boardType, payload.items)
</script>

<template>
  <LeaderboardView :board-type="boardType" :payload="payload" :error="error" />
</template>
