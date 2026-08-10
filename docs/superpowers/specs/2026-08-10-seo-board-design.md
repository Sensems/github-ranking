# Board SEO Design (Option B + brand assets)

**Date:** 2026-08-10  
**Status:** Approved

## Goal

Improve crawlability and share previews for「GitHub Star 趋势榜」without adding `@nuxtjs/seo`. Cover per-board meta (including Open Graph / Twitter), canonical URLs, `robots.txt`, sitemap polish, JSON-LD `ItemList`, and brand logo used as favicon + header + `og:image`.

## Scope

| In | Out |
|----|-----|
| `useBoardSeo` composable + page wiring | `@nuxtjs/seo` / heavy SEO modules |
| OG/Twitter meta, canonical (path only) | Indexing filter query variants (`?q`/`lang`/`sort`) |
| JSON-LD `ItemList` (Top 10) | Per-repo detail pages |
| `robots.txt`, sitemap polish | Dedicated 1200×630 marketing OG art (logo reused for now) |
| `public/logo.png` as favicon, header mark, `og:image` | Changing board copy/product name |

## Assets

- Source logo → `frontend/app/public/logo.png` (required with `srcDir: 'app/'`; root `frontend/public` is not copied)
- Absolute OG URL: `{siteUrl}/logo.png` (from `runtimeConfig.public.siteUrl`)
- Header replaces the current SVG trend icon with `<img src="/logo.png" …>`
- `link rel="icon"` → `/logo.png`

## Composable: `useBoardSeo(boardType, items?)`

- Title: `{BOARD_META[type].title} - GitHub Star 趋势榜`
- Description: `BOARD_META[type].description`
- Canonical: `{siteUrl}{path}` with trailing-slash policy matching sitemap (`/`, `/daily/`, …)
- `useSeoMeta`: `ogTitle`, `ogDescription`, `ogType=website`, `ogUrl`, `ogLocale=zh_CN`, `ogImage`, `twitterCard=summary`, `twitterTitle`, `twitterDescription`, `twitterImage`
- JSON-LD via `useHead` script `type=application/ld+json`:
  - Always: `WebSite` (name + url)
  - When items exist: `ItemList` with up to 10 `ListItem` (`position`, `name`=repo_name, `url`=html_url)

## Discovery

- `server/routes/robots.txt.ts`: `Allow: /`, `Disallow: /api/`, `Sitemap: {siteUrl}/sitemap.xml`
- `sitemap.xml`: keep five board URLs; align trailing slash with canonical; optional `lastmod` from latest known date if cheap, else omit

## Config / env

- Document production `SITE_URL` (and Nuxt public override) in `.env.example`
- Default placeholder remains for local; production must set the real origin

## Testing

- Unit-test `useBoardSeo` helpers (canonical path, JSON-LD shape) if extracted
- Smoke: pages still render; existing board tests pass
