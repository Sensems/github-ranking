<script setup lang="ts">
const tabs = [
  { to: '/', label: '总排名' },
  { to: '/daily', label: '日增速' },
  { to: '/weekly', label: '周增速' },
  { to: '/monthly', label: '月增速' },
  { to: '/yearly', label: '年增速' },
] as const

const route = useRoute()

function isActive(to: string) {
  return route.path === to
}

function preserveQuery(to: string) {
  const { q, lang } = route.query
  const query: Record<string, string> = {}
  if (typeof q === 'string' && q) query.q = q
  if (typeof lang === 'string' && lang) query.lang = lang
  return { path: to, query }
}
</script>

<template>
  <nav aria-label="榜单切换" class="min-w-0">
    <ul class="flex flex-wrap items-center gap-1 sm:gap-2">
      <li v-for="tab in tabs" :key="tab.to">
        <NuxtLink
          :to="preserveQuery(tab.to)"
          class="inline-flex h-10 items-center border-b-2 px-2 text-sm font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          :class="
            isActive(tab.to)
              ? 'border-primary text-foreground'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          "
          :aria-current="isActive(tab.to) ? 'page' : undefined"
        >
          {{ tab.label }}
        </NuxtLink>
      </li>
    </ul>
  </nav>
</template>
