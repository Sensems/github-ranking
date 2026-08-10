import { BOARD_CANONICAL_PATH } from '../../utils/seo'
import type { BoardType } from '../../types/leaderboard'

const BOARDS: BoardType[] = ['total', 'daily', 'weekly', 'monthly', 'yearly']

export default defineEventHandler((event) => {
  const config = useRuntimeConfig()
  const base = String(config.public.siteUrl || 'https://github-trend.example.com').replace(
    /\/$/,
    '',
  )
  const urls = BOARDS.map((board) => {
    const path = BOARD_CANONICAL_PATH[board]
    const loc = path === '/' ? `${base}/` : `${base}${path}`
    return `  <url>\n    <loc>${loc}</loc>\n    <changefreq>daily</changefreq>\n  </url>`
  }).join('\n')
  setHeader(event, 'content-type', 'text/xml; charset=utf-8')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>`
})
