<template>
  <div class="min-h-screen bg-gray-50">
    <header class="border-b border-gray-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <NuxtLink to="/" class="text-xl font-bold text-gray-900">🚀 GitHub Star 趋势榜</NuxtLink>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-6">
      <NuxtPage />
    </main>
    <footer class="border-t border-gray-200 bg-white py-4 text-center text-sm text-gray-500">
      数据来源 GitHub API · 由讯飞星辰 MaaS 提供摘要支持
    </footer>
  </div>
</template>
