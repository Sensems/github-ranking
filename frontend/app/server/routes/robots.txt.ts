export default defineEventHandler((event) => {
  const config = useRuntimeConfig()
  const base = String(config.public.siteUrl || 'https://github-trend.example.com').replace(
    /\/$/,
    '',
  )
  setHeader(event, 'content-type', 'text/plain; charset=utf-8')
  return [
    'User-agent: *',
    'Allow: /',
    'Disallow: /api/',
    '',
    `Sitemap: ${base}/sitemap.xml`,
    '',
  ].join('\n')
})
