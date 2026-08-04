import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import RepoCard from './RepoCard.vue'
import type { LeaderboardItem } from '../types/leaderboard'

const item: LeaderboardItem = {
  rank: 3,
  repo_id: 1,
  repo_name: 'vuejs/core',
  description: 'Vue.js',
  language: 'TypeScript',
  stars: 12345,
  forks: 200,
  html_url: 'https://github.com/vuejs/core',
  growth: { daily: 12, weekly: null, monthly: 400, yearly: 5000 },
  summary: { project_positioning: '渐进式前端框架', core_features: ['响应式'], use_cases: ['Web 应用'], tech_stack: ['TypeScript'] },
}

describe('RepoCard', () => {
  it('renders repo name, rank, stars and growth values', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    expect(wrapper.text()).toContain('#3')
    expect(wrapper.text()).toContain('vuejs/core')
    expect(wrapper.text()).toContain('12.3k')
    expect(wrapper.text()).toContain('数据积累中')
  })

  it('falls back to description when summary missing', () => {
    const wrapper = mount(RepoCard, { props: { item: { ...item, summary: null }, boardType: 'total' } })
    expect(wrapper.text()).toContain('Vue.js')
  })

  it('links to the repository', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    expect(wrapper.find('a[href="https://github.com/vuejs/core"]').exists()).toBe(true)
  })
})
