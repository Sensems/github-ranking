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
    summary: null,
    ...partial,
  }
}

const items = [
  item({
    repo_id: 1,
    repo_name: 'vuejs/core',
    language: 'TypeScript',
    stars: 100,
    forks: 20,
    growth: { daily: 10, weekly: 30, monthly: 60, yearly: 300 },
    summary: { project_positioning: '前端框架', core_features: ['响应式'], use_cases: ['Web'], tech_stack: ['TS'] },
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

  it('searches repo name, description and summary text', () => {
    const lb = useLeaderboard(items, 'daily')
    lb.query.value = '响应式'
    expect(lb.sorted.value.map((i) => i.repo_id)).toEqual([1])
  })

  it('sorts by growth of the active board', () => {
    const lb = useLeaderboard(items, 'daily')
    lb.sortBy.value = 'growth'
    expect(lb.sorted.value[0].repo_id).toBe(1)
  })

  it('sorts by stars by default', () => {
    const lb = useLeaderboard(items, 'daily')
    expect(lb.sorted.value[0].repo_id).toBe(2)
  })

  it('exposes unique languages', () => {
    const lb = useLeaderboard(items, 'daily')
    expect(lb.languages.value).toEqual(['Go', 'TypeScript'])
  })
})
