import { describe, expect, it } from 'vitest'
import type { LeaderboardItem } from '../types/leaderboard'
import {
  boardCanonicalUrl,
  boardOgImageUrl,
  boardSeoTitle,
  buildBoardJsonLd,
  normalizeSiteUrl,
} from './seo'

const sampleItem = (name: string, rank: number): LeaderboardItem => ({
  rank,
  repo_id: rank,
  repo_name: name,
  description: 'desc',
  language: 'TypeScript',
  stars: 1000,
  forks: 10,
  html_url: `https://github.com/${name}`,
  growth: { daily: 1, weekly: 2, monthly: 3, yearly: 4 },
})

describe('seo helpers', () => {
  it('normalizes site url and builds canonical / og image urls', () => {
    expect(normalizeSiteUrl('https://example.com/')).toBe('https://example.com')
    expect(boardCanonicalUrl('https://example.com/', 'total')).toBe('https://example.com/')
    expect(boardCanonicalUrl('https://example.com', 'daily')).toBe('https://example.com/daily/')
    expect(boardOgImageUrl('https://example.com/')).toBe('https://example.com/logo.png')
  })

  it('builds board title from BOARD_META', () => {
    expect(boardSeoTitle('weekly')).toBe('周增速榜 - GitHub Star 趋势榜')
  })

  it('builds JSON-LD with WebSite/WebPage and ItemList when items exist', () => {
    const ld = buildBoardJsonLd('https://example.com', 'daily', [
      sampleItem('a/b', 1),
      sampleItem('c/d', 2),
    ])
    expect(ld['@context']).toBe('https://schema.org')
    const graph = ld['@graph'] as Array<Record<string, unknown>>
    expect(graph.some((n) => n['@type'] === 'WebSite')).toBe(true)
    expect(graph.some((n) => n['@type'] === 'WebPage')).toBe(true)
    const list = graph.find((n) => n['@type'] === 'ItemList') as {
      itemListElement: Array<{ position: number; name: string; url: string }>
    }
    expect(list.numberOfItems).toBe(2)
    expect(list.itemListElement[0]).toMatchObject({
      position: 1,
      name: 'a/b',
      url: 'https://github.com/a/b',
    })
  })

  it('omits ItemList when there are no items', () => {
    const ld = buildBoardJsonLd('https://example.com', 'total', [])
    const graph = ld['@graph'] as Array<Record<string, unknown>>
    expect(graph.some((n) => n['@type'] === 'ItemList')).toBe(false)
  })

  it('caps ItemList at 10 entries', () => {
    const items = Array.from({ length: 15 }, (_, i) => sampleItem(`org/r${i}`, i + 1))
    const ld = buildBoardJsonLd('https://example.com', 'total', items)
    const list = (ld['@graph'] as Array<Record<string, unknown>>).find(
      (n) => n['@type'] === 'ItemList',
    ) as { numberOfItems: number; itemListElement: unknown[] }
    expect(list.numberOfItems).toBe(10)
    expect(list.itemListElement).toHaveLength(10)
  })
})
