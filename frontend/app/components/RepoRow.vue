<script setup lang="ts">
import { computed, ref } from 'vue'
import { Button } from '~/components/ui/button'
import type { BoardType, LeaderboardItem, Summary } from '~/types/leaderboard'
import { languageColor } from '~/utils/languageColor'

const props = defineProps<{
  item: LeaderboardItem
  boardType: BoardType
  maxGrowth: number
}>()

const summary = ref<Summary | null>(null)
const expanded = ref(false)
const loading = ref(false)
const error = ref('')

const growthKey = computed(() => (props.boardType === 'total' ? null : props.boardType))

const rankLabel = computed(() => `#${String(props.item.rank).padStart(2, '0')}`)

const growthValue = computed(() => {
  if (!growthKey.value) return null
  return props.item.growth[growthKey.value]
})

const growthBarWidth = computed(() => {
  const g = growthValue.value
  if (g == null || props.maxGrowth <= 0) return 0
  return Math.min(100, Math.max(4, (Math.abs(g) / props.maxGrowth) * 100))
})

function fmt(n: number | null | undefined): string {
  if (n == null) return '—'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

function fmtSigned(n: number | null | undefined): string {
  if (n == null) return '数据积累中'
  return n >= 0 ? `+${n.toLocaleString('en-US')}` : n.toLocaleString('en-US')
}

function display(v: string | number | null | undefined): string {
  if (v == null || v === '') return '—'
  return String(v)
}

function fmtDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toISOString().slice(0, 10)
}

async function loadSummary(method: 'GET' | 'POST') {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const res =
      method === 'POST'
        ? await $fetch<{ repo_id: number; summary: Summary }>(
            `/api/repos/${props.item.repo_id}/summary`,
            { method: 'POST' },
          )
        : await $fetch<{ repo_id: number; summary: Summary }>(
            `/api/repos/${props.item.repo_id}/summary`,
          )
    summary.value = res.summary
    expanded.value = true
  } catch {
    error.value = method === 'POST' ? '概况生成失败，请重试' : '概况加载失败，请重试'
  } finally {
    loading.value = false
  }
}

async function onSummaryAction() {
  if (expanded.value && summary.value) {
    expanded.value = false
    return
  }
  if (summary.value) {
    expanded.value = true
    return
  }
  if (props.item.has_summary) {
    await loadSummary('GET')
    return
  }
  await loadSummary('POST')
}

const summaryActionLabel = computed(() => {
  if (loading.value) return '加载中…'
  if (expanded.value && summary.value) return '收起概况'
  if (props.item.has_summary || summary.value) return '查看概况'
  return '生成概况'
})

const rankAccentClass = computed(() => {
  if (props.item.rank === 1) return 'board-row-card--rank-1'
  if (props.item.rank === 2) return 'board-row-card--rank-2'
  if (props.item.rank === 3) return 'board-row-card--rank-3'
  return ''
})
</script>

<template>
  <article
    class="board-row-card board-row-cells text-sm"
    :class="rankAccentClass"
    :data-rank="item.rank"
  >
    <div class="font-semibold tabular-nums text-primary">{{ rankLabel }}</div>

    <div class="min-w-0">
      <a
        :href="item.html_url"
        target="_blank"
        rel="noopener"
        class="font-semibold text-foreground transition-colors hover:text-primary"
      >
        {{ item.repo_name }}
      </a>
      <p class="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
        {{ display(item.description) }}
      </p>
    </div>

    <div class="flex min-w-0 items-center gap-1.5 text-muted-foreground">
      <span
        class="inline-block size-2 shrink-0 rounded-full"
        :style="{ backgroundColor: languageColor(item.language) }"
        aria-hidden="true"
      />
      <span class="truncate">{{ display(item.language) }}</span>
    </div>

    <div class="flex items-center gap-1 tabular-nums text-foreground">
      <span class="text-[var(--star)]" aria-hidden="true">★</span>
      {{ fmt(item.stars) }}
    </div>

    <div class="tabular-nums text-foreground">{{ fmt(item.forks) }}</div>
    <div class="tabular-nums text-foreground">{{ display(item.open_issues) }}</div>
    <div class="tabular-nums text-muted-foreground">{{ fmtDate(item.pushed_at) }}</div>

    <div v-if="growthKey" data-testid="growth-cell" class="min-w-0">
      <div
        class="text-base font-semibold tabular-nums"
        :class="
          (growthValue ?? 0) >= 0 ? 'text-growth-positive' : 'text-growth-negative'
        "
      >
        {{ fmtSigned(growthValue) }}
      </div>
      <div
        v-if="growthValue != null"
        class="mt-1 h-1.5 w-full max-w-[6rem] overflow-hidden rounded-full bg-muted"
      >
        <div
          data-testid="growth-bar"
          class="h-full rounded-full bg-primary"
          :style="{ width: `${growthBarWidth}%` }"
        />
      </div>
    </div>

    <div class="flex flex-wrap items-center justify-end gap-2">
      <Button
        type="button"
        size="sm"
        data-testid="summary-action"
        :variant="expanded && summary ? 'default' : 'outline'"
        class="h-8"
        :class="
          expanded && summary
            ? ''
            : 'border-primary/50 text-primary hover:bg-primary/10'
        "
        :disabled="loading"
        @click="onSummaryAction"
      >
        {{ summaryActionLabel }}
      </Button>
      <Button as-child variant="outline" size="sm" class="h-8">
        <a :href="item.html_url" target="_blank" rel="noopener">查看仓库 →</a>
      </Button>
    </div>

    <Transition name="summary">
      <div
        v-if="expanded && summary"
        data-summary
        data-testid="summary-panel"
        class="col-span-full mt-3 rounded-md bg-muted/80 px-3 py-3"
      >
        <h3 class="text-sm font-semibold text-primary">项目定位</h3>
        <p class="mt-1.5 text-sm leading-relaxed text-foreground">
          {{ summary.project_positioning }}
        </p>

        <div class="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <h4 class="text-sm font-semibold text-primary">功能</h4>
            <ul v-if="summary.core_features.length" class="mt-2 space-y-1.5">
              <li
                v-for="(feature, i) in summary.core_features"
                :key="i"
                data-testid="summary-feature"
                class="flex gap-2 text-sm text-foreground"
              >
                <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                <span>{{ feature }}</span>
              </li>
            </ul>
            <p v-else class="mt-2 text-sm text-muted-foreground">—</p>
          </div>

          <div>
            <h4 class="text-sm font-semibold text-primary">场景</h4>
            <ul v-if="summary.use_cases.length" class="mt-2 space-y-1.5">
              <li
                v-for="(useCase, i) in summary.use_cases"
                :key="i"
                class="flex gap-2 text-sm text-foreground"
              >
                <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                <span>{{ useCase }}</span>
              </li>
            </ul>
            <p v-else class="mt-2 text-sm text-muted-foreground">—</p>
          </div>

          <div>
            <h4 class="text-sm font-semibold text-primary">技术栈</h4>
            <p
              v-if="summary.tech_stack.length"
              class="mt-2 text-sm leading-relaxed text-foreground"
            >
              {{ summary.tech_stack.join('、') }}
            </p>
            <p v-else class="mt-2 text-sm text-muted-foreground">—</p>
          </div>
        </div>
      </div>
    </Transition>

    <p
      v-if="error"
      data-summary
      role="alert"
      class="mt-2 text-sm text-destructive"
    >
      {{ error }}
    </p>
  </article>
</template>
