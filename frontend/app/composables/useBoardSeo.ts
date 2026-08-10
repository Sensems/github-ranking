import type { BoardType, LeaderboardItem } from '~/types/leaderboard'
import { BOARD_META } from '~/utils/boardMeta'
import {
  boardCanonicalUrl,
  boardOgImageUrl,
  boardSeoTitle,
  buildBoardJsonLd,
} from '~/utils/seo'

export function useBoardSeo(boardType: BoardType, items: LeaderboardItem[] = []) {
  const config = useRuntimeConfig()
  const siteUrl =
    typeof config.public.siteUrl === 'string' && config.public.siteUrl.trim()
      ? config.public.siteUrl.trim()
      : 'https://github-trend.example.com'

  const title = boardSeoTitle(boardType)
  const description = BOARD_META[boardType].description
  const canonical = boardCanonicalUrl(siteUrl, boardType)
  const ogImage = boardOgImageUrl(siteUrl)
  const jsonLd = buildBoardJsonLd(siteUrl, boardType, items)

  useSeoMeta({
    title,
    description,
    ogTitle: title,
    ogDescription: description,
    ogType: 'website',
    ogUrl: canonical,
    ogLocale: 'zh_CN',
    ogImage,
    ogSiteName: 'GitHub Star 趋势榜',
    twitterCard: 'summary',
    twitterTitle: title,
    twitterDescription: description,
    twitterImage: ogImage,
  })

  useHead({
    link: [
      { rel: 'canonical', href: canonical },
      { rel: 'icon', type: 'image/png', href: '/logo.png' },
      { rel: 'apple-touch-icon', sizes: '180x180', href: '/logo.png' },
    ],
    script: [
      {
        key: `ld-json-${boardType}`,
        type: 'application/ld+json',
        children: JSON.stringify(jsonLd),
      },
    ],
  })
}
