export default defineNuxtConfig({
  srcDir: 'app/',
  modules: ['@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],
  app: {
    baseURL: process.env.NUXT_APP_BASE_URL || '/',
    head: {
      htmlAttrs: { lang: 'zh-CN' },
      title: 'GitHub Star 趋势榜',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'GitHub 开源项目 Star 趋势排行榜' },
      ],
    },
  },
  runtimeConfig: {
    // Overridden at runtime by NUXT_DATABASE_URL; db.ts also falls back to DATABASE_URL.
    databaseUrl: process.env.NUXT_DATABASE_URL || process.env.DATABASE_URL || '',
    xfyunApiKey: process.env.NUXT_XFYUN_API_KEY || process.env.XFYUN_API_KEY || '',
    xfyunBaseUrl:
      process.env.NUXT_XFYUN_BASE_URL ||
      process.env.XFYUN_BASE_URL ||
      'https://spark-api-open.xf-yun.com/agent/v1/',
    xfyunModel: process.env.NUXT_XFYUN_MODEL || process.env.XFYUN_MODEL || 'spark-x',
    public: {
      siteUrl: process.env.SITE_URL || 'https://github-trend.example.com',
    },
  },

  nitro: {
    prerender: {
      routes: ['/sitemap.xml'],
    },
  },
})
