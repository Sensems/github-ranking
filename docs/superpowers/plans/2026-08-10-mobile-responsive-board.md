# Mobile Responsive Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adapt the existing leaderboard row/table for `<md` viewports without a second card-grid layout.

**Architecture:** Add stable `board-cell-*` class hooks on column headers and `RepoRow`; reflow via CSS in `main.css` under max-width 767px; keep desktop subgrid rules intact above `md`. Light chrome tweaks in `app.vue` / `LeaderboardTabs` / toolbar wrappers only as needed.

**Tech Stack:** Nuxt 3, Vue 3 SFCs, Tailwind v4, existing CSS in `frontend/app/assets/css/main.css`, Vitest.

## Global Constraints

- Adapt the same row/table board for mobile — not a second card-grid layout
- Product name remains「GitHub Star 趋势榜」
- Preserve dual theme, sticky toolbar (desktop also sticky colhead), top-3 accents, borderless 概况
- No new dialog/sheet primitives
- Touch-friendly action buttons on mobile; `prefers-reduced-motion` unchanged

---

## File map

| File | Responsibility |
|------|----------------|
| `frontend/app/components/RepoRow.vue` | Add `board-cell-*` classes; minor mobile-friendly action sizing classes |
| `frontend/app/components/LeaderboardView.vue` | Add matching header cell classes; hide colhead via CSS (class already `board-colhead`) |
| `frontend/app/assets/css/main.css` | Mobile reflow rules; safe-area nudge for back-to-top optional |
| `frontend/app/app.vue` | Tabs nowrap + overflow; optional safe-area / compact header |
| `frontend/app/components/LeaderboardTabs.vue` | `flex-nowrap` so header height stays stable |
| `frontend/app/components/RepoRow.spec.ts` | Assert cell hooks if useful |

---

### Task 1: Cell hooks on RepoRow + column header

- [x] Add `board-cell-rank|repo|lang|stars|forks|issues|pushed|growth|actions` to `RepoRow.vue` cells
- [x] Mirror the same classes on `LeaderboardView.vue` `.board-colhead` children
- [x] Run `RepoRow` unit tests; fix any class-based failures

### Task 2: Mobile CSS reflow

- [x] In `main.css`, add `@media (max-width: 767px)` block:
  - `.board-table--total|growth`: single column, `min-width: 0`
  - `.board-colhead { display: none }`
  - `.board-row-card`: stacked grid (rank+repo / meta / actions)
  - Meta cells as flex wrap strip; hide empty visual noise only if needed
- [x] Verify desktop rules outside the media query are untouched

### Task 3: Chrome polish

- [x] `LeaderboardTabs`: `flex-nowrap` + ensure parent scroll works
- [x] Toolbar/search already wrap — ensure SearchBox full width on small screens (already `w-full md:w-52`)
- [x] Back-to-top: add safe-area-aware positioning classes if easy

### Task 4: Verify

- [x] Run frontend unit tests for affected components
- [x] Spot-check mentally against 375 / 768 / 1280 behavior from the spec
