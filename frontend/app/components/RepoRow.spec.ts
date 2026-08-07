import { mount, flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import RepoRow from './RepoRow.vue'
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

describe('RepoRow', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('renders rank, name, stars, forks, language, open issues, description, last commit', () => {
    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'daily', maxGrowth: 100 },
    })
    const text = wrapper.text()
    expect(text).toContain('#03')
    expect(text).toContain('vuejs/core')
    expect(text).toContain('12.3k')
    expect(text).toContain('200')
    expect(text).toContain('TypeScript')
    expect(text).toContain('42')
    expect(text).toContain('Vue.js')
    expect(text).toContain('2026-07-14')
  })

  it('applies accent border class for top-3 ranks', () => {
    const top = mount(RepoRow, {
      props: { item: { ...item, rank: 1 }, boardType: 'total', maxGrowth: 0 },
    })
    expect(top.classes()).toContain('board-row-card--rank-1')

    const mid = mount(RepoRow, {
      props: { item: { ...item, rank: 3 }, boardType: 'total', maxGrowth: 0 },
    })
    expect(mid.classes()).toContain('board-row-card--rank-3')

    const rest = mount(RepoRow, {
      props: { item: { ...item, rank: 4 }, boardType: 'total', maxGrowth: 0 },
    })
    expect(rest.classes()).not.toContain('board-row-card--rank-1')
    expect(rest.classes()).not.toContain('board-row-card--rank-3')
  })

  it('shows em dash for missing open issues, language, and last commit', () => {
    const wrapper = mount(RepoRow, {
      props: {
        item: {
          ...item,
          language: null,
          open_issues: undefined,
          pushed_at: null,
          description: '',
        },
        boardType: 'total',
        maxGrowth: 0,
      },
    })
    expect(wrapper.text()).toMatch(/—/)
    expect(wrapper.text()).not.toContain('TypeScript')
    expect(wrapper.text()).not.toContain('2026-07-14')
  })

  it('hides growth cell on total board', () => {
    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'total', maxGrowth: 100 },
    })
    expect(wrapper.find('[data-testid="growth-cell"]').exists()).toBe(false)
  })

  it('shows growth value and bar on daily board', () => {
    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'daily', maxGrowth: 100 },
    })
    expect(wrapper.find('[data-testid="growth-cell"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('+12')
    expect(wrapper.find('[data-testid="growth-bar"]').exists()).toBe(true)
  })

  it('keeps cached summary collapsed until 查看概况 is clicked', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      repo_id: 1,
      summary: sampleSummary,
    })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = mount(RepoRow, {
      props: {
        item: { ...item, has_summary: true },
        boardType: 'daily',
        maxGrowth: 100,
      },
    })
    expect(wrapper.text()).toContain('查看概况')
    expect(wrapper.text()).not.toContain('渐进式前端框架')

    await wrapper.get('[data-testid="summary-action"]').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith('/api/repos/1/summary')
    expect(wrapper.text()).toContain('渐进式前端框架')
    expect(wrapper.text()).toContain('收起概况')
  })

  it('shows 生成概况 when summary is missing', () => {
    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'daily', maxGrowth: 100 },
    })
    expect(wrapper.text()).toContain('生成概况')
    expect(wrapper.text()).not.toContain('渐进式前端框架')
  })

  it('POSTs summary on generate and reveals positioning', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      repo_id: 1,
      summary: sampleSummary,
    })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'daily', maxGrowth: 100 },
    })
    expect(wrapper.text()).not.toContain('渐进式前端框架')

    await wrapper.get('[data-testid="summary-action"]').trigger('click')
    await flushPromises()

    expect(fetchMock).toHaveBeenCalledWith('/api/repos/1/summary', { method: 'POST' })
    expect(wrapper.text()).toContain('渐进式前端框架')
    expect(wrapper.text()).toContain('收起概况')
  })

  it('renders overview panels with section labels and feature list', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      repo_id: 1,
      summary: sampleSummary,
    })
    vi.stubGlobal('$fetch', fetchMock)

    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'daily', maxGrowth: 100 },
    })
    await wrapper.get('[data-testid="summary-action"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="summary-panel"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('项目定位')
    expect(wrapper.text()).toContain('功能')
    expect(wrapper.text()).toContain('场景')
    expect(wrapper.text()).toContain('技术栈')
    expect(wrapper.findAll('[data-testid="summary-feature"]').length).toBe(1)
  })

  it('links to the repository', () => {
    const wrapper = mount(RepoRow, {
      props: { item, boardType: 'daily', maxGrowth: 100 },
    })
    expect(wrapper.find('a[href="https://github.com/vuejs/core"]').exists()).toBe(true)
  })
})
