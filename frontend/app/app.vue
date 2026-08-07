<template>
  <div class="min-h-screen bg-background text-foreground">
    <header class="border-b border-border bg-card">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <NuxtLink
          to="/"
          class="text-xl font-semibold tracking-tight text-foreground transition-colors hover:text-primary"
        >
          GitHub Star 趋势榜
        </NuxtLink>
      </div>
    </header>
    <main class="mx-auto max-w-6xl px-4 py-6">
      <NuxtPage :transition="{ name: 'board-page', mode: 'out-in' }" />
    </main>
    <footer class="border-t border-border bg-card py-4 text-center text-sm text-muted-foreground">
      数据来源 GitHub API · 由讯飞星辰 MaaS 提供摘要支持
    </footer>
  </div>
</template>
