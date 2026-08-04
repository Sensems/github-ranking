export default defineNuxtConfig({
  srcDir: 'app/',
  modules: ['@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],
  app: {
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
    public: {
      siteUrl: process.env.SITE_URL || 'https://github-trend.example.com',
    },
  },
})
