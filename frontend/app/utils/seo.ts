import type { BoardType, LeaderboardItem } from '~/types/leaderboard'
import { BOARD_META } from '~/utils/boardMeta'

export const BOARD_CANONICAL_PATH: Record<BoardType, string> = {
  total: '/',
  daily: '/daily/',
  weekly: '/weekly/',
  monthly: '/monthly/',
  yearly: '/yearly/',
}

export function normalizeSiteUrl(siteUrl: string): string {
  return siteUrl.replace(/\/$/, '')
}

export function boardCanonicalUrl(siteUrl: string, boardType: BoardType): string {
  const base = normalizeSiteUrl(siteUrl)
  const path = BOARD_CANONICAL_PATH[boardType]
  return path === '/' ? `${base}/` : `${base}${path}`
}

export function boardOgImageUrl(siteUrl: string): string {
  return `${normalizeSiteUrl(siteUrl)}/logo.png`
}

export function boardSeoTitle(boardType: BoardType): string {
  return `${BOARD_META[boardType].title} - GitHub Star 趋势榜`
}

export function buildBoardJsonLd(
  siteUrl: string,
  boardType: BoardType,
  items: LeaderboardItem[],
  maxItems = 10,
) {
  const base = normalizeSiteUrl(siteUrl)
  const pageUrl = boardCanonicalUrl(siteUrl, boardType)
  const meta = BOARD_META[boardType]
  const graph: Record<string, unknown>[] = [
    {
      '@type': 'WebSite',
      name: 'GitHub Star 趋势榜',
      url: `${base}/`,
      inLanguage: 'zh-CN',
    },
    {
      '@type': 'WebPage',
      name: boardSeoTitle(boardType),
      description: meta.description,
      url: pageUrl,
      isPartOf: { '@type': 'WebSite', url: `${base}/` },
    },
  ]

  const top = items.slice(0, maxItems)
  if (top.length > 0) {
    graph.push({
      '@type': 'ItemList',
      name: meta.title,
      description: meta.description,
      url: pageUrl,
      numberOfItems: top.length,
      itemListElement: top.map((item, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: item.repo_name,
        url: item.html_url,
      })),
    })
  }

  return {
    '@context': 'https://schema.org',
    '@graph': graph,
  }
}
