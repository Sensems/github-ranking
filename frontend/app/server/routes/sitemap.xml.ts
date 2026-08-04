export default defineEventHandler((event) => {
  const config = useRuntimeConfig()
  const base = config.public.siteUrl.replace(/\/$/, '')
  const pages = ['', '/daily', '/weekly', '/monthly', '/yearly']
  const urls = pages
    .map((p) => `  <url><loc>${base}${p}/</loc></url>`)
    .join('\n')
  setHeader(event, 'content-type', 'text/xml; charset=utf-8')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>`
})
