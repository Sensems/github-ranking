# shadcn-vue Frontend Design System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shadcn-vue design system (light graphite + teal) first, then restyle the Nuxt leaderboard UI into a dense data desk without changing APIs or ranking logic.

**Architecture:** Migrate `frontend/` onto current shadcn-vue + Tailwind CSS variables; commit phase-1 primitives under `app/components/ui/`; swap business components and page chrome to consume those primitives. Data flow stays Nitro → `useLeaderboard` → filters → `RepoCard`.

**Tech Stack:** Nuxt 3, shadcn-vue, `shadcn-nuxt`, Tailwind CSS (v4 path required by current shadcn-vue docs), Reka UI, class-variance-authority, `clsx` + `tailwind-merge`, Vitest + Vue Test Utils.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-06-shadcn-vue-frontend-design.md`
- Product posture: dense data desk; no marketing hero
- Keep dual-column `RepoCard` grid (`md:grid-cols-2`)
- Light theme only (no dark / system mode)
- Palette: graphite surfaces + primary teal `#0F766E`; growth + `#15803D` / − `#B91C1C`
- Design system first: foundation → `ui/*` → page swap
- Keep tabs + flex-wrap filters; no Toolbar reorganization
- Header title「GitHub Star 趋势榜」; remove rocket emoji
- Do not change leaderboard APIs, summary contract, sync, or Postgres schema
- Existing Chinese empty/error copy must stay verbatim
- `frontend/npm test` must pass after UI swaps

---

## File structure

| Path | Responsibility |
|---|---|
| `frontend/components.json` | shadcn-vue CLI config (aliases, cssVariables, paths) |
| `frontend/nuxt.config.ts` | `shadcn-nuxt` module + Tailwind v4 wiring; drop old v3-only assumptions |
| `frontend/package.json` | Dependencies for shadcn-vue / Tailwind v4 / utils |
| `frontend/app/assets/css/main.css` | Tailwind import + CSS variables (light graphite/teal) |
| `frontend/app/lib/utils.ts` | `cn()` helper |
| `frontend/app/components/ui/*` | Phase-1 primitives (button, input, select, badge, card, tabs, separator, skeleton, alert) |
| `frontend/app/plugins/ssr-width.ts` | Optional VueUse `provideSSRWidth` for hydration-safe primitives |
| `frontend/app/app.vue` | Token-based header/main/footer + Separator |
| `frontend/app/components/LeaderboardTabs.vue` | Route tabs using shadcn Tabs visuals / API |
| `frontend/app/components/SearchBox.vue` | shadcn Input |
| `frontend/app/components/LanguageFilter.vue` | shadcn Select |
| `frontend/app/components/SortSelect.vue` | shadcn Select |
| `frontend/app/components/RepoCard.vue` | Card + Badge + Button; growth color utilities |
| `frontend/app/components/RepoCard.spec.ts` | Adjust selectors only if DOM shape changes; keep assertion meaning |
| `frontend/app/pages/{index,daily,weekly,monthly,yearly}.vue` | Token classes + Alert empty/error; layout unchanged |
| `frontend/vitest.config.ts` | Keep `~` / `@` → `app/` aliases |

---

### Task 1: Foundation — Tailwind v4 + shadcn-vue init + theme tokens

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/nuxt.config.ts`
- Modify: `frontend/app/assets/css/main.css`
- Create: `frontend/components.json`
- Create: `frontend/app/lib/utils.ts`
- Create (if CLI does not): `frontend/app/plugins/ssr-width.ts`
- Test: smoke via `npx nuxi prepare` + `npm run build` (no UI swap yet)

**Interfaces:**
- Consumes: existing Nuxt `srcDir: 'app/'`
- Produces: CSS vars `--background`, `--foreground`, `--card`, `--primary`, `--muted`, `--muted-foreground`, `--border`, `--ring`, `--destructive`, `--radius`; `cn()` at `~/lib/utils`; `components.json` pointing UI to `app/components/ui`

- [ ] **Step 1: Add TypeScript + switch Tailwind to the shadcn-vue Nuxt path**

Working directory: `frontend/`.

Install toolchain deps (exact versions resolve at install time; pin what the CLI installs afterward):

```bash
npm install -D typescript @types/node
npx nuxi@latest module add shadcn-nuxt
```

Follow [shadcn-vue Nuxt install](https://www.shadcn-vue.com/docs/installation/nuxt): prefer `@tailwindcss/vite` path. Remove reliance on Tailwind v3 `@tailwind base/components/utilities` directives.

Update `nuxt.config.ts` to include both Tailwind Vite plugin and `shadcn-nuxt` (keep existing `runtimeConfig` / `nitro` / `app.head` blocks):

```ts
import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  srcDir: 'app/',
  modules: ['shadcn-nuxt'],
  shadcn: {
    prefix: '',
    componentDir: '@/components/ui',
  },
  css: ['~/assets/css/main.css'],
  vite: {
    plugins: [tailwindcss()],
  },
  // ...keep existing app / runtimeConfig / nitro
})
```

If `@nuxtjs/tailwindcss` remains in `package.json` after the switch, remove it from `modules` and uninstall it so only one Tailwind pipeline runs:

```bash
npm uninstall @nuxtjs/tailwindcss
```

- [ ] **Step 2: Run shadcn-vue init**

```bash
npx nuxi prepare
npx shadcn-vue@latest init
```

CLI choices:
- Style: default
- Base color: **Neutral** (then override primary in CSS to teal)
- CSS variables: **yes**
- Ensure aliases resolve under `app/` (`@/components`, `@/lib/utils`, `@/components/ui`)

Confirm `components.json` exists and `tailwind.cssVariables` is `true`.

- [ ] **Step 3: Write light graphite + teal tokens in `app/assets/css/main.css`**

Replace file contents with Tailwind v4 import + shadcn theme layer. Use these HSL channels (shadcn format: space-separated, no `hsl()` wrapper):

```css
@import "tailwindcss";

@theme inline {
  --color-background: hsl(var(--background));
  --color-foreground: hsl(var(--foreground));
  --color-card: hsl(var(--card));
  --color-card-foreground: hsl(var(--card-foreground));
  --color-primary: hsl(var(--primary));
  --color-primary-foreground: hsl(var(--primary-foreground));
  --color-muted: hsl(var(--muted));
  --color-muted-foreground: hsl(var(--muted-foreground));
  --color-border: hsl(var(--border));
  --color-input: hsl(var(--input));
  --color-ring: hsl(var(--ring));
  --color-destructive: hsl(var(--destructive));
  --color-accent: hsl(var(--accent));
  --color-accent-foreground: hsl(var(--accent-foreground));
  --color-secondary: hsl(var(--secondary));
  --color-secondary-foreground: hsl(var(--secondary-foreground));
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
}

:root {
  /* #F8FAFC */
  --background: 210 40% 98%;
  /* #0F172A */
  --foreground: 222 47% 11%;
  /* #FFFFFF */
  --card: 0 0% 100%;
  --card-foreground: 222 47% 11%;
  /* #0F766E teal */
  --primary: 175 77% 26%;
  --primary-foreground: 0 0% 100%;
  /* slate muted surface */
  --secondary: 210 40% 96%;
  --secondary-foreground: 222 47% 11%;
  --muted: 210 40% 96%;
  /* #64748B */
  --muted-foreground: 215 16% 47%;
  --accent: 210 40% 96%;
  --accent-foreground: 222 47% 11%;
  --destructive: 0 72% 51%;
  /* #E2E8F0 */
  --border: 214 32% 91%;
  --input: 214 32% 91%;
  --ring: 175 77% 26%;
  --radius: 0.5rem;
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}

/* Semantic growth (not first-class shadcn tokens) */
@utility text-growth-positive {
  color: #15803d;
}
@utility text-growth-negative {
  color: #b91c1c;
}
```

If the CLI already wrote a different `@theme` / `:root` block, merge: keep CLI structure, overwrite `:root` values to the table above. Do **not** add a `.dark` block.

Ensure `app/lib/utils.ts` exists:

```ts
import type { ClassValue } from 'clsx'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

Optional hydration helper `app/plugins/ssr-width.ts`:

```ts
import { provideSSRWidth } from '@vueuse/core'

export default defineNuxtPlugin((nuxtApp) => {
  provideSSRWidth(1024, nuxtApp.vueApp)
})
```

- [ ] **Step 4: Verify foundation builds**

```bash
npx nuxi prepare
npm run build
```

Expected: build succeeds. Pages may still use old gray utility classes; that is OK for this task.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/nuxt.config.ts frontend/components.json frontend/app/assets/css/main.css frontend/app/lib/utils.ts frontend/app/plugins/ssr-width.ts
git commit -m "$(cat <<'EOF'
chore(frontend): init shadcn-vue with light graphite/teal tokens

EOF
)"
```

---

### Task 2: Install phase-1 UI primitives

**Files:**
- Create: `frontend/app/components/ui/button/**`
- Create: `frontend/app/components/ui/input/**`
- Create: `frontend/app/components/ui/select/**`
- Create: `frontend/app/components/ui/badge/**`
- Create: `frontend/app/components/ui/card/**`
- Create: `frontend/app/components/ui/tabs/**`
- Create: `frontend/app/components/ui/separator/**`
- Create: `frontend/app/components/ui/skeleton/**`
- Create: `frontend/app/components/ui/alert/**`
- Modify: `frontend/package.json` / lockfile (CLI may add reka-ui, cva, lucide-vue-next, etc.)

**Interfaces:**
- Consumes: Task 1 `components.json`, `cn`, CSS vars
- Produces: auto-imported components `Button`, `Input`, `Select*` family, `Badge`, `Card*`, `Tabs*`, `Separator`, `Skeleton`, `Alert*` (exact export names as generated by CLI)

- [ ] **Step 1: Add components via CLI**

```bash
cd frontend
npx shadcn-vue@latest add button input select badge card tabs separator skeleton alert
```

Accept dependency installs. Do **not** add dialog/dropdown/sheet.

- [ ] **Step 2: Smoke-check one primitive in a temporary render**

In `app.vue` temporarily add `<Button variant="outline">ping</Button>` under the header, run:

```bash
npm run dev
```

Confirm teal/outline styles load. Remove the temporary Button before committing.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/ui frontend/package.json frontend/package-lock.json frontend/app/lib
git commit -m "$(cat <<'EOF'
chore(frontend): add phase-1 shadcn-vue UI primitives

EOF
)"
```

---

### Task 3: App chrome (`app.vue`) on tokens

**Files:**
- Modify: `frontend/app/app.vue`
- Test: visual / build smoke (`npm run build`)

**Interfaces:**
- Consumes: `Separator` from ui; CSS tokens
- Produces: light data-desk shell (header / main / footer) without emoji

- [ ] **Step 1: Replace `app.vue` template**

```vue
<template>
  <div class="min-h-screen bg-background text-foreground">
    <header class="border-b border-border bg-card">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <NuxtLink to="/" class="text-xl font-semibold tracking-tight text-foreground">
          GitHub Star 趋势榜
        </NuxtLink>
      </div>
    </header>
    <Separator />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <NuxtPage />
    </main>
    <footer class="border-t border-border bg-card py-4 text-center text-sm text-muted-foreground">
      数据来源 GitHub API · 由讯飞星辰 MaaS 提供摘要支持
    </footer>
  </div>
</template>
```

If `Separator` under the header feels redundant with `border-b`, keep **either** header `border-b` **or** `Separator`, not both heavy rules — prefer header `border-b` and drop the extra `Separator` if the chrome looks double-lined.

- [ ] **Step 2: Build smoke**

```bash
npm run build
```

Expected: success; header text has no 🚀.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/app.vue
git commit -m "$(cat <<'EOF'
style(frontend): restyle app chrome with design tokens

EOF
)"
```

---

### Task 4: `LeaderboardTabs` → route-aware Tabs

**Files:**
- Modify: `frontend/app/components/LeaderboardTabs.vue`
- Test: manual route click smoke; optional mount test if added

**Interfaces:**
- Consumes: `Tabs`, `TabsList`, `TabsTrigger` (names as generated); `useRoute`, `navigateTo`
- Produces: same five routes `/`, `/daily`, `/weekly`, `/monthly`, `/yearly` with labels 总榜 / 日增速 / 周增速 / 月增速 / 年增速

- [ ] **Step 1: Rewrite component to sync Tabs value with route**

```vue
<script setup lang="ts">
const tabs = [
  { to: '/', label: '总榜' },
  { to: '/daily', label: '日增速' },
  { to: '/weekly', label: '周增速' },
  { to: '/monthly', label: '月增速' },
  { to: '/yearly', label: '年增速' },
] as const

const route = useRoute()
const current = computed(() => route.path)

async function onTabChange(value: string | number) {
  const path = String(value)
  if (path !== route.path) await navigateTo(path)
}
</script>

<template>
  <Tabs :model-value="current" class="mb-6" @update:model-value="onTabChange">
    <TabsList class="flex h-auto w-full flex-wrap justify-start gap-1">
      <TabsTrigger
        v-for="tab in tabs"
        :key="tab.to"
        :value="tab.to"
      >
        {{ tab.label }}
      </TabsTrigger>
    </TabsList>
  </Tabs>
</template>
```

If generated Tabs API uses `TabsTrigger` without working as uncontrolled route tabs, fall back to `TabsList` visual classes + `NuxtLink` with `cn(...)` active styles using `bg-background text-foreground shadow` for active — still no custom blue/gray utilities.

- [ ] **Step 2: Manual smoke**

```bash
npm run dev
```

Click each tab; URL and active style must match. Primary/teal active state from tokens.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/components/LeaderboardTabs.vue
git commit -m "$(cat <<'EOF'
refactor(frontend): restyle leaderboard tabs with shadcn Tabs

EOF
)"
```

---

### Task 5: Filter controls — SearchBox / LanguageFilter / SortSelect

**Files:**
- Modify: `frontend/app/components/SearchBox.vue`
- Modify: `frontend/app/components/LanguageFilter.vue`
- Modify: `frontend/app/components/SortSelect.vue`
- Test: interactive smoke on any board page; existing `useLeaderboard` unit tests unchanged

**Interfaces:**
- Consumes: `Input`; `Select`, `SelectTrigger`, `SelectValue`, `SelectContent`, `SelectItem` (exact names from CLI)
- Produces: same v-model contracts:
  - `SearchBox`: `modelValue: string` / `update:modelValue`
  - `LanguageFilter`: `modelValue: string`, `options: string[]`
  - `SortSelect`: `modelValue: string` with values `stars` | `growth` | `forks`

- [ ] **Step 1: Rewrite `SearchBox.vue`**

```vue
<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <Input
    :model-value="modelValue"
    type="search"
    placeholder="搜索项目/关键词"
    class="w-full md:w-64"
    @update:model-value="$emit('update:modelValue', String($event))"
  />
</template>
```

If generated `Input` is not v-model compatible, bind `:model-value` + `@input` to the native event the CLI component emits — keep the public v-model API identical for parents.

- [ ] **Step 2: Rewrite `LanguageFilter.vue`**

```vue
<script setup lang="ts">
const props = defineProps<{ modelValue: string; options: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <Select
    :model-value="modelValue || 'all'"
    @update:model-value="(v) => emit('update:modelValue', v === 'all' ? '' : String(v))"
  >
    <SelectTrigger class="w-[10rem]">
      <SelectValue placeholder="全部语言" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="all">全部语言</SelectItem>
      <SelectItem v-for="lang in options" :key="lang" :value="lang">
        {{ lang }}
      </SelectItem>
    </SelectContent>
  </Select>
</template>
```

Map empty string ↔ sentinel `all` because SelectItem values must be non-empty.

- [ ] **Step 3: Rewrite `SortSelect.vue`**

```vue
<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ (e: 'update:modelValue', value: string): void }>()
</script>

<template>
  <Select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', String($event))"
  >
    <SelectTrigger class="w-[10rem]">
      <SelectValue placeholder="排序" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="stars">按 Star 数</SelectItem>
      <SelectItem value="growth">按增速</SelectItem>
      <SelectItem value="forks">按 Fork 数</SelectItem>
    </SelectContent>
  </Select>
</template>
```

- [ ] **Step 4: Smoke filters**

On `/` and `/daily`, type search, pick language, change sort; list must update as before.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/components/SearchBox.vue frontend/app/components/LanguageFilter.vue frontend/app/components/SortSelect.vue
git commit -m "$(cat <<'EOF'
refactor(frontend): restyle filter controls with shadcn Input/Select

EOF
)"
```

---

### Task 6: `RepoCard` → Card / Badge / Button + growth utilities

**Files:**
- Modify: `frontend/app/components/RepoCard.vue`
- Modify: `frontend/app/components/RepoCard.spec.ts` (only if selectors break)
- Test: `frontend/app/components/RepoCard.spec.ts`

**Interfaces:**
- Consumes: `Card`, `CardHeader`, `CardContent`, `CardFooter` (use only what fits; may be single `Card` + inner divs); `Badge`; `Button`; `text-growth-positive` / `text-growth-negative`
- Produces: unchanged props `{ item: LeaderboardItem; boardType: BoardType }`; same summary fetch behavior; summary control remains a real `<button>` so `wrapper.get('button')` still works

- [ ] **Step 1: Run existing tests (baseline)**

```bash
npm test -- app/components/RepoCard.spec.ts
```

Expected: PASS on current code before edits (or note failures unrelated to this task).

- [ ] **Step 2: Restyle template with ui primitives**

Keep `<script setup>` logic identical. Replace outer `<article class="rounded-xl ...">` with:

```vue
<template>
  <Card class="transition hover:-translate-y-0.5 hover:shadow-md">
    <CardContent class="space-y-3 p-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <Badge variant="secondary" class="mr-2">#{{ item.rank }}</Badge>
          <a
            :href="item.html_url"
            target="_blank"
            rel="noopener"
            class="font-semibold text-foreground hover:text-primary"
          >
            {{ item.repo_name }}
          </a>
          <Badge variant="outline" class="ml-2">{{ display(item.language) }}</Badge>
        </div>
        <div class="shrink-0 text-lg font-bold">★ {{ fmt(item.stars) }}</div>
      </div>

      <div class="flex flex-wrap gap-x-3 gap-y-1 text-sm text-muted-foreground">
        <span>Forks {{ fmt(item.forks) }}</span>
        <span>Open Issues {{ display(item.open_issues) }}</span>
        <span>Last Commit {{ fmtDate(item.pushed_at) }}</span>
      </div>

      <div v-if="growthKey" class="text-sm text-muted-foreground">
        {{ growthLabels[growthKey] }}：
        <span
          class="font-medium"
          :class="(item.growth[growthKey] ?? 0) >= 0 ? 'text-growth-positive' : 'text-growth-negative'"
        >
          {{ fmtSigned(item.growth[growthKey]) }}
        </span>
      </div>

      <p class="text-sm text-muted-foreground">{{ display(item.description) }}</p>

      <div class="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant="link"
          class="h-auto px-0"
          :disabled="loading"
          @click="onSummaryClick"
        >
          {{ loading ? '加载中…' : hasSummaryLocal ? '查看概况' : '生成概况' }}
        </Button>
        <Button as-child variant="link" class="h-auto px-0">
          <a :href="item.html_url" target="_blank" rel="noopener">查看仓库 →</a>
        </Button>
      </div>

      <p v-if="error" class="text-sm text-destructive">{{ error }}</p>

      <div
        v-if="expanded && summary"
        class="rounded-lg bg-muted p-3 text-sm leading-relaxed text-foreground"
      >
        <p class="font-medium">{{ summary.project_positioning }}</p>
        <p v-if="summary.core_features.length" class="mt-1">功能：{{ summary.core_features.join('、') }}</p>
        <p v-if="summary.use_cases.length" class="mt-1">场景：{{ summary.use_cases.join('、') }}</p>
        <p v-if="summary.tech_stack.length" class="mt-1">技术栈：{{ summary.tech_stack.join('、') }}</p>
      </div>
    </CardContent>
  </Card>
</template>
```

If `Button` `as-child` is unavailable in the generated component, keep repo link as plain `<a class="text-sm font-medium text-primary hover:underline">`.

Critical: summary control must render a native `<button>` (default `Button` root). Prefer `variant="link"` over nesting that removes the button element.

- [ ] **Step 3: Fix tests only if needed**

```bash
npm test -- app/components/RepoCard.spec.ts
```

If `wrapper.get('button')` fails because multiple buttons exist, change those two tests to:

```ts
await wrapper.get('button').trigger('click')
// →
const summaryBtn = wrapper.findAll('button').find((b) => /概况|加载中/.test(b.text()))
expect(summaryBtn).toBeTruthy()
await summaryBtn!.trigger('click')
```

Do not weaken assertions about fetch URLs or summary text.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/components/RepoCard.vue frontend/app/components/RepoCard.spec.ts
git commit -m "$(cat <<'EOF'
refactor(frontend): restyle RepoCard with shadcn Card/Badge/Button

EOF
)"
```

---

### Task 7: Pages — token typography + Alert empty/error; full suite

**Files:**
- Modify: `frontend/app/pages/index.vue`
- Modify: `frontend/app/pages/daily.vue`
- Modify: `frontend/app/pages/weekly.vue`
- Modify: `frontend/app/pages/monthly.vue`
- Modify: `frontend/app/pages/yearly.vue`
- Test: `frontend` `npm test`; build smoke

**Interfaces:**
- Consumes: `Alert`, `AlertTitle`, `AlertDescription` (or dashed `Card` if Alert title/desc unused); existing page data hooks unchanged
- Produces: same page structure; copy unchanged for:
  - `加载失败，请稍后重试。`
  - `该榜单暂无数据（历史数据积累中），请明天再来看看。`

- [ ] **Step 1: Update one page pattern (`daily.vue`), then mirror**

Replace error/empty blocks and heading classes. Example for error + empty:

```vue
<div v-if="error">
  <Alert variant="destructive">
    <AlertDescription>加载失败，请稍后重试。</AlertDescription>
  </Alert>
</div>
...
<div v-else-if="!sorted.length">
  <Alert>
    <AlertDescription>该榜单暂无数据（历史数据积累中），请明天再来看看。</AlertDescription>
  </Alert>
</div>
```

Heading / meta:

```vue
<h1 class="text-lg font-semibold text-foreground">日增速榜</h1>
<span v-if="payload.generated_at" class="text-xs text-muted-foreground">
  数据更新于 {{ payload.generated_at }}
</span>
```

Keep:

```vue
<div class="mb-4 flex flex-wrap items-center gap-2">...</div>
<div v-if="sorted.length" class="grid gap-4 md:grid-cols-2">...</div>
```

Apply the same pattern to `index` / `weekly` / `monthly` / `yearly` (titles and `board-type` / fetch paths stay as today).

Skeleton: install already done in Task 2; do **not** rewrite `await useFetch` to show skeletons unless trivial — optional skip.

- [ ] **Step 2: Full verification**

```bash
npm test
npm run build
```

Expected: all tests PASS; production build succeeds.

- [ ] **Step 3: Acceptance checklist (manual)**

- [ ] Five boards share teal/graphite look
- [ ] Search / language / sort / summary behave as before
- [ ] Light only; no hero; dual-column cards
- [ ] No rocket emoji in header

- [ ] **Step 4: Commit**

```bash
git add frontend/app/pages
git commit -m "$(cat <<'EOF'
style(frontend): apply design tokens and Alert states on board pages

EOF
)"
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|---|---|
| shadcn-vue design system first | 1–2 |
| Light graphite + teal `#0F766E` tokens | 1 |
| Phase-1 primitives inventory | 2 |
| `app.vue` chrome; remove emoji | 3 |
| Tabs route navigation | 4 |
| Search / language / sort → Input/Select | 5 |
| RepoCard Card/Badge/Button; growth colors | 6 |
| Pages keep grid + filters; Alert empty/error | 7 |
| No API/sync/schema/dark/table/toolbar | Global Constraints / non-goals |
| `npm test` passes | 6–7 |

No placeholders left. Growth utilities use exact hex from spec. Select empty-language sentinel documented as `all`.
