import { computed, ref } from 'vue'
import type { BoardType, LeaderboardItem } from '~/types/leaderboard'

export function useLeaderboard(items: LeaderboardItem[], boardType: BoardType) {
  const query = ref('')
  const language = ref('')
  const sortBy = ref<'stars' | 'growth' | 'forks'>('stars')

  const languages = computed(() =>
    [...new Set(items.map((i) => i.language).filter((l): l is string => Boolean(l)))].sort(),
  )

  const summaryText = (item: LeaderboardItem): string =>
    item.summary
      ? [item.summary.project_positioning, ...item.summary.core_features, ...item.summary.use_cases, ...item.summary.tech_stack].join(' ')
      : ''

  const filtered = computed(() => {
    let list = items
    if (language.value) {
      list = list.filter((i) => i.language === language.value)
    }
    const q = query.value.trim().toLowerCase()
    if (q) {
      list = list.filter((i) =>
        [i.repo_name, i.description, summaryText(i)].join(' ').toLowerCase().includes(q),
      )
    }
    return list
  })

  const growthKey = boardType === 'total' ? 'daily' : boardType
  const sorted = computed(() => {
    const list = [...filtered.value]
    if (sortBy.value === 'growth') {
      list.sort((a, b) => (b.growth[growthKey] ?? 0) - (a.growth[growthKey] ?? 0))
    } else {
      const key = sortBy.value
      list.sort((a, b) => b[key] - a[key])
    }
    return list
  })

  return { query, language, sortBy, languages, filtered, sorted }
}
