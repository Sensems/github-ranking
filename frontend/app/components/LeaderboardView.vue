<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useLeaderboard, type SortBy } from '~/composables/useLeaderboard'
import { useBoardGeneratedAt } from '~/composables/useBoardGeneratedAt'
import type { BoardType, LeaderboardPayload } from '~/types/leaderboard'
import { BOARD_META } from '~/utils/boardMeta'

const props = defineProps<{
  boardType: BoardType
  payload: LeaderboardPayload
  error?: unknown
}>()

const PAGE_SIZE = 24
const route = useRoute()
const router = useRouter()
const boardGeneratedAt = useBoardGeneratedAt()

const {
  query,
  language,
  sortBy,
  languages,
  sorted,
  totalCount,
  resultCount,
  hasActiveFilters,
  clearFilters,
} = useLeaderboard(props.payload.items, props.boardType)

const meta = computed(() => BOARD_META[props.boardType])
const visibleCount = ref(PAGE_SIZE)
const showBackTop = ref(false)
const isGrowthBoard = computed(() => props.boardType !== 'total')

const visibleItems = computed(() => sorted.value.slice(0, visibleCount.value))
const canLoadMore = computed(() => visibleCount.value < sorted.value.length)
const isDataEmpty = computed(() => !props.error && totalCount.value === 0)
const isFilterEmpty = computed(
  () => !props.error && totalCount.value > 0 && resultCount.value === 0,
)
const sortIsNonDefault = computed(() => {
  const defaultSort: SortBy = props.boardType === 'total' ? 'stars' : 'growth'
  return sortBy.value !== defaultSort
})

const maxGrowth = computed(() => {
  if (!isGrowthBoard.value) return 0
  const key = props.boardType as Exclude<BoardType, 'total'>
  let max = 0
  for (const item of visibleItems.value) {
    const g = item.growth[key]
    if (g != null && Math.abs(g) > max) max = Math.abs(g)
  }
  return max
})

const topBadge = computed(() => {
  const n = totalCount.value || props.payload.items.length
  return n > 0 ? `TOP ${Math.min(n, 100)}` : 'TOP 100'
})

function parseSort(raw: unknown): SortBy | null {
  if (raw === 'stars' || raw === 'growth' || raw === 'forks') return raw
  return null
}

function syncFromRoute() {
  const q = typeof route.query.q === 'string' ? route.query.q : ''
  const lang = typeof route.query.lang === 'string' ? route.query.lang : ''
  const sort = parseSort(route.query.sort)
  query.value = q
  language.value = lang
  if (sort) sortBy.value = sort
}

function syncToRoute() {
  const next: Record<string, string | undefined> = {
    q: query.value.trim() || undefined,
    lang: language.value || undefined,
    sort: sortBy.value || undefined,
  }
  const defaultSort: SortBy = props.boardType === 'total' ? 'stars' : 'growth'
  if (next.sort === defaultSort) next.sort = undefined

  const current = {
    q: typeof route.query.q === 'string' ? route.query.q : undefined,
    lang: typeof route.query.lang === 'string' ? route.query.lang : undefined,
    sort: typeof route.query.sort === 'string' ? route.query.sort : undefined,
  }
  if (current.q === next.q && current.lang === next.lang && current.sort === next.sort) return

  router.replace({ query: { ...route.query, ...next } })
}

watch(
  () => props.payload.generated_at,
  (value) => {
    boardGeneratedAt.value = value ?? null
  },
  { immediate: true },
)

watch([query, language, sortBy], () => {
  visibleCount.value = PAGE_SIZE
  syncToRoute()
})

watch(
  () => route.fullPath,
  () => syncFromRoute(),
)

function onScroll() {
  showBackTop.value = window.scrollY > window.innerHeight
}

function loadMore() {
  visibleCount.value = Math.min(visibleCount.value + PAGE_SIZE, sorted.value.length)
}

function backToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onClearFilters() {
  clearFilters()
}

onMounted(() => {
  syncFromRoute()
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  boardGeneratedAt.value = null
})
</script>

<template>
  <div class="board-page">
    <div class="mb-5">
      <p class="text-xs font-semibold tracking-wider text-primary uppercase">
        {{ meta.eyebrow }}
      </p>
      <div class="mt-1 flex flex-wrap items-center gap-2">
        <h1 class="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
          {{ meta.title }}
        </h1>
        <span
          class="rounded border border-border px-2 py-0.5 text-xs font-medium text-muted-foreground"
        >
          {{ topBadge }}
        </span>
      </div>
      <p class="mt-2 max-w-3xl text-sm text-muted-foreground">{{ meta.description }}</p>
    </div>

    <Alert v-if="error" variant="destructive" class="mb-4">
      <AlertDescription>加载失败，请稍后重试。</AlertDescription>
    </Alert>

    <template v-else-if="isDataEmpty">
      <Alert>
        <AlertDescription>{{ meta.emptyHint }}</AlertDescription>
      </Alert>
    </template>

    <template v-else>
      <div
        class="board-toolbar sticky z-30 -mx-4 mb-0 flex flex-wrap items-center gap-2 bg-background/95 px-4 py-2 backdrop-blur supports-[backdrop-filter]:bg-background/90"
        style="top: var(--site-header-h)"
      >
        <SearchBox v-model="query" />
        <LanguageFilter v-model="language" :options="languages" />
        <SortSelect v-model="sortBy" :board-type="boardType" />
        <div class="flex min-h-8 flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span aria-live="polite">
            显示 {{ resultCount }} / {{ totalCount }} 项
            <template v-if="sortIsNonDefault"> · 排名为原榜名次</template>
          </span>
          <Button
            v-if="hasActiveFilters"
            type="button"
            variant="ghost"
            size="sm"
            class="h-8 px-2 text-xs"
            @click="onClearFilters"
          >
            清除筛选
          </Button>
        </div>
      </div>

      <Alert v-if="isFilterEmpty" class="mt-4">
        <AlertDescription>
          没有匹配的项目。试试其他关键词，或
          <button type="button" class="text-primary underline" @click="onClearFilters">
            清除筛选
          </button>
          。
        </AlertDescription>
      </Alert>

      <div v-else class="mt-0">
        <div
          class="board-table"
          :class="isGrowthBoard ? 'board-table--growth' : 'board-table--total'"
        >
          <div
            class="board-cols board-colhead sticky z-20 rounded-md bg-muted/80 py-3.5 text-sm font-semibold tracking-wide text-muted-foreground uppercase backdrop-blur"
            style="top: calc(var(--site-header-h) + var(--toolbar-h))"
          >
            <div>排名</div>
            <div>仓库</div>
            <div>主语言</div>
            <div>Star 总数</div>
            <div>Fork</div>
            <div>未关闭 Issue</div>
            <div>最近提交</div>
            <div v-if="isGrowthBoard">{{ meta.growthCol }}</div>
            <div class="text-right">操作</div>
          </div>

          <RepoRow
            v-for="(item, index) in visibleItems"
            :key="item.repo_id"
            :item="item"
            :board-type="boardType"
            :max-growth="maxGrowth"
            :style="{ '--stagger': index }"
          />
        </div>

        <div v-if="canLoadMore" class="mt-6 flex justify-center">
          <Button type="button" variant="outline" class="h-11 min-w-40" @click="loadMore">
            加载更多（还有 {{ sorted.length - visibleCount }} 项）
          </Button>
        </div>
      </div>
    </template>

    <ClientOnly>
      <Teleport to="body">
        <Button
          v-if="showBackTop"
          type="button"
          variant="secondary"
          class="fixed bottom-20 right-6 z-50 h-11 shadow-sm"
          @click="backToTop"
        >
          回到顶部
        </Button>
      </Teleport>
    </ClientOnly>
  </div>
</template>
