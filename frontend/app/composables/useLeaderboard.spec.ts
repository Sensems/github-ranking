import { describe, expect, it } from 'vitest'
import { useLeaderboard } from './useLeaderboard'
import type { LeaderboardItem } from '../types/leaderboard'

function item(partial: Partial<LeaderboardItem>): LeaderboardItem {
  return {
    rank: 1,
    repo_id: 1,
    repo_name: 'a/b',
    description: '',
    language: null,
    stars: 10,
    forks: 1,
    html_url: 'https://github.com/a/b',
    growth: { daily: 1, weekly: 2, monthly: 3, yearly: 4 },
    has_summary: false,
    ...partial,
  }
}

const items = [
  item({
    repo_id: 1,
    repo_name: 'vuejs/core',
    description: '渐进式前端框架',
    language: 'TypeScript',
    stars: 100,
    forks: 20,
    growth: { daily: 10, weekly: 30, monthly: 60, yearly: 300 },
    has_summary: true,
  }),
  item({
    repo_id: 2,
    repo_name: 'golang/go',
    language: 'Go',
    stars: 200,
    forks: 30,
    growth: { daily: 5, weekly: 15, monthly: 40, yearly: 200 },
  }),
]

describe('useLeaderboard', () => {
  it('filters by language', () => {
    const lb = useLeaderboard(items, 'daily')
    lb.language.value = 'Go'
    expect(lb.sorted.value.map((i) => i.repo_id)).toEqual([2])
  })

  it('searches repo name and description only', () => {
    const lb = useLeaderboard(items, 'daily')
    lb.query.value = '渐进式'
    expect(lb.sorted.value.map((i) => i.repo_id)).toEqual([1])

    lb.query.value = '响应式'
    expect(lb.sorted.value.map((i) => i.repo_id)).toEqual([])
  })

  it('sorts by growth of the active board', () => {
    const lb = useLeaderboard(items, 'daily')
    lb.sortBy.value = 'growth'
    expect(lb.sorted.value[0].repo_id).toBe(1)
  })

  it('defaults growth boards to growth sort', () => {
    const lb = useLeaderboard(items, 'daily')
    expect(lb.sortBy.value).toBe('growth')
    expect(lb.sorted.value[0].repo_id).toBe(1)
  })

  it('defaults total board to stars sort', () => {
    const lb = useLeaderboard(items, 'total')
    expect(lb.sortBy.value).toBe('stars')
    expect(lb.sorted.value[0].repo_id).toBe(2)
  })

  it('exposes unique languages', () => {
    const lb = useLeaderboard(items, 'daily')
    expect(lb.languages.value).toEqual(['Go', 'TypeScript'])
  })

  it('reports whether filters are active and total vs filtered counts', () => {
    const lb = useLeaderboard(items, 'daily')
    expect(lb.totalCount.value).toBe(2)
    expect(lb.resultCount.value).toBe(2)
    expect(lb.hasActiveFilters.value).toBe(false)

    lb.query.value = 'vue'
    expect(lb.resultCount.value).toBe(1)
    expect(lb.hasActiveFilters.value).toBe(true)

    lb.clearFilters()
    expect(lb.query.value).toBe('')
    expect(lb.language.value).toBe('')
    expect(lb.resultCount.value).toBe(2)
  })
})
