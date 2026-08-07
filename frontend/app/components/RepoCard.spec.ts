import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
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
  open_issues: 42,
  pushed_at: '2026-07-14T19:25:58Z',
  html_url: 'https://github.com/vuejs/core',
  growth: { daily: 12, weekly: null, monthly: 400, yearly: 5000 },
  has_summary: false,
}

const sampleSummary = {
  project_positioning: '渐进式前端框架',
  core_features: ['响应式'],
  use_cases: ['Web 应用'],
  tech_stack: ['TypeScript'],
}

describe('RepoCard', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('renders rank, name, stars, forks, language, open issues, description, last commit', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    const text = wrapper.text()
    expect(text).toContain('#3')
    expect(text).toContain('vuejs/core')
    expect(text).toContain('12.3k')
    expect(text).toContain('200')
    expect(text).toContain('TypeScript')
    expect(text).toContain('42')
    expect(text).toContain('Vue.js')
    expect(text).toContain('2026-07-14')
  })

  it('shows em dash for missing open issues, language, and last commit', () => {
    const wrapper = mount(RepoCard, {
      props: {
        item: {
          ...item,
          language: null,
          open_issues: undefined,
          pushed_at: null,
          description: '',
        },
        boardType: 'total',
      },
    })
    expect(wrapper.text()).toMatch(/—/)
    expect(wrapper.text()).not.toContain('TypeScript')
    expect(wrapper.text()).not.toContain('2026-07-14')
  })

  it('hides growth row on total board', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'total' } })
    expect(wrapper.text()).not.toContain('今日')
    expect(wrapper.text()).not.toContain('本周')
    expect(wrapper.text()).not.toContain('本月')
    expect(wrapper.text()).not.toContain('今年')
  })

  it('shows only matching growth window on daily board', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    expect(wrapper.text()).toContain('今日')
    expect(wrapper.text()).toContain('+12')
    expect(wrapper.text()).not.toContain('本周')
    expect(wrapper.text()).not.toContain('本月')
    expect(wrapper.text()).not.toContain('今年')
  })

  it('shows summary inline when item.summary is present and hides generate button', () => {
    const wrapper = mount(RepoCard, {
      props: {
        item: { ...item, has_summary: true, summary: sampleSummary },
        boardType: 'daily',
      },
    })
    expect(wrapper.text()).toContain('渐进式前端框架')
    expect(wrapper.text()).toContain('响应式')
    expect(wrapper.text()).not.toContain('生成概况')
    expect(wrapper.text()).not.toContain('查看概况')
  })

  it('shows 生成概况 when summary is missing', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    expect(wrapper.text()).toContain('生成概况')
    expect(wrapper.text()).not.toContain('渐进式前端框架')
  })

  it('POSTs summary on generate and reveals positioning', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      repo_id: 1,
      summary: sampleSummary,
    })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    expect(wrapper.text()).not.toContain('渐进式前端框架')

    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith('/api/repos/1/summary', { method: 'POST' })
    expect(wrapper.text()).toContain('渐进式前端框架')
    expect(wrapper.text()).toContain('响应式')
    expect(wrapper.text()).not.toContain('生成概况')
  })

  it('links to the repository', () => {
    const wrapper = mount(RepoCard, { props: { item, boardType: 'daily' } })
    expect(wrapper.find('a[href="https://github.com/vuejs/core"]').exists()).toBe(true)
  })
})
