<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAppColorMode } from '~/composables/useColorMode'
import { useBoardGeneratedAt } from '~/composables/useBoardGeneratedAt'
import { formatGeneratedAt } from '~/utils/boardMeta'

const { mode, toggle, applyStored } = useAppColorMode()
const generatedAt = useBoardGeneratedAt()

useHead({
  htmlAttrs: {
    class: computed(() => (mode.value === 'dark' ? 'dark' : '')),
  },
  script: [
    {
      key: 'color-mode-init',
      innerHTML:
        "(function(){try{var m=localStorage.getItem('color-mode');if(m==='light'){document.documentElement.classList.remove('dark')}else{document.documentElement.classList.add('dark')}}catch(e){document.documentElement.classList.add('dark')}})()",
      tagPriority: 'critical',
    },
  ],
})

onMounted(() => {
  applyStored()
})
</script>

<template>
  <div class="min-h-screen bg-background text-foreground">
    <header
      class="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/90"
      style="height: var(--site-header-h)"
    >
      <div
        class="mx-auto flex h-full max-w-[90rem] items-center gap-4 px-4"
      >
        <NuxtLink
          to="/"
          class="flex shrink-0 items-center gap-2 text-base font-semibold tracking-tight text-foreground transition-colors hover:text-primary sm:text-lg"
        >
          <svg
            class="size-5 text-primary"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M3 17l6-6 4 4 8-8" />
            <path d="M14 7h7v7" />
          </svg>
          GitHub Star 趋势榜
        </NuxtLink>

        <div class="min-w-0 flex-1 overflow-x-auto">
          <LeaderboardTabs />
        </div>

        <div class="flex shrink-0 items-center gap-2 sm:gap-3">
          <span
            v-if="generatedAt"
            class="hidden text-xs text-muted-foreground md:inline"
            :title="generatedAt"
          >
            更新 {{ formatGeneratedAt(generatedAt) }}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            class="h-9 px-2 text-muted-foreground"
            :aria-label="mode === 'dark' ? '切换到亮色模式' : '切换到深色模式'"
            @click="toggle"
          >
            {{ mode === 'dark' ? '亮色' : '深色' }}
          </Button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-[90rem] px-4 py-6">
      <NuxtPage :transition="{ name: 'board-page', mode: 'out-in' }" />
    </main>

    <footer class="border-t border-border bg-card/50 py-4 text-center text-sm text-muted-foreground">
      数据来源 GitHub API · 由讯飞星辰 MaaS 提供摘要支持
    </footer>
  </div>
</template>
