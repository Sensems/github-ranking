# Table Leaderboard + Dual Theme Implementation Plan

> **For agentic workers:** Execute on current branch (no worktree). TDD where tests exist.

**Goal:** Horizontal row/table leaderboard with sticky toolbar + column headers, dark neon-green default + light companion theme.

**Architecture:** Dual CSS tokens (`.dark` / `:root`); `useColorMode` + sticky shell in `app.vue`; `RepoRow` replaces `RepoCard` grid; `LeaderboardView` owns sticky toolbar/headers.

**Tech Stack:** Nuxt 3, Vue 3, Tailwind v4, shadcn-vue, Vitest, `@vueuse/core` color mode if suitable.

## Global Constraints

- Brand stays「GitHub Star 趋势榜」
- Default theme: dark; persist in localStorage
- No sync/DB/API ranking changes
- Narrow: horizontal scroll, no card layout

## Tasks

- [x] Task 1: Dual-theme tokens in `main.css` + `useColorMode` + `app.vue` shell
- [x] Task 2: Restyle `LeaderboardTabs` for header; `useBoardGeneratedAt` for header timestamp
- [x] Task 3: `RepoRow` (TDD from `RepoCard.spec`) + growth bar
- [x] Task 4: `LeaderboardView` table layout + sticky chrome; board meta eyebrows
- [x] Task 5: Update specs; run `npm test`; removed `RepoCard`
