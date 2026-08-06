# shadcn-vue Frontend Design System Redesign

Date: 2026-08-06  
Status: Approved for implementation planning

## Goal

Refactor the Nuxt frontend visual layer into a **dense data-desk** UI using **shadcn-vue** (Vue equivalent of shadcn/ui). Build the design system first, then restyle existing pages and business components. Do not change leaderboard APIs, sync logic, or ranking rules.

## Decisions

| Topic | Choice |
|---|---|
| Product posture | Data desk (high information density); not marketing / hero-led |
| List presentation | Keep dual-column `RepoCard` grid |
| Color mode | Light only |
| Palette | Neutral graphite surfaces + single teal accent |
| Primary accent | Teal `#0F766E` |
| Approach | Design system first (foundation → ui primitives → page swap) |
| Component library | shadcn-vue (copy-in `components/ui`), not React shadcn/ui |
| Layout chrome | Keep tabs + flex-wrap filters; no Toolbar reorganization |
| Brand mark | Keep title「GitHub Star 趋势榜」; remove rocket emoji from header |

## Design tokens (light)

| Role | Hex | Notes |
|---|---|---|
| Background | `#F8FAFC` | Page canvas |
| Surface | `#FFFFFF` | Cards, header, footer |
| Foreground | `#0F172A` | Primary text |
| Muted text | `#64748B` | Secondary / meta |
| Border | `#E2E8F0` | Dividers, card edges |
| Primary | `#0F766E` | Active tab, links, primary actions |
| Growth positive | `#15803D` | Star deltas ≥ 0 |
| Growth negative | `#B91C1C` | Star deltas < 0 |

Map these into shadcn CSS variables (`--background`, `--foreground`, `--primary`, `--muted`, `--border`, etc.) in `app/assets/css/main.css`. Semantic growth colors may stay as utility classes if not first-class shadcn tokens.

## Architecture

```
frontend/
  components.json          # shadcn-vue config
  app/
    assets/css/main.css    # Tailwind + CSS variables (light theme)
    components/
      ui/                  # shadcn primitives (Button, Input, …)
      RepoCard.vue         # business; consumes ui/*
      LeaderboardTabs.vue
      SearchBox.vue
      LanguageFilter.vue
      SortSelect.vue
    pages/*.vue            # structure unchanged; empty/error use Alert/Card
    app.vue                # token-based chrome + Separator
```

Data flow stays: Nitro `/api/leaderboards/[type]` → `useLeaderboard` → filters → `RepoCard`. On-demand summary button → existing summary API unchanged.

## UI primitive inventory (phase 1)

Install and commit only what the product uses:

- Button
- Input
- Select
- Badge
- Card
- Tabs
- Separator
- Skeleton
- Alert

Out of scope for phase 1: Dialog, Dropdown Menu, Sheet, dark mode, charts.

## Business component mapping

| Existing | Target |
|---|---|
| `LeaderboardTabs` | shadcn Tabs styling; navigation remains route-based (`NuxtLink` / `navigateTo`) |
| `SearchBox` | Input `type="search"` |
| `LanguageFilter` | Select |
| `SortSelect` | Select |
| `RepoCard` shell | Card; rank/language Badge; summary/repo actions Button |
| Empty / error states | Alert or dashed Card; keep existing Chinese copy |
| Optional loading | Skeleton (no fetch-logic rewrite required) |

Pages (`index`, `daily`, `weekly`, `monthly`, `yearly`) keep:

- LeaderboardTabs
- Title + `generated_at`
- Search + language + sort row (`flex-wrap`)
- `md:grid-cols-2` card grid

## Rollout order

1. Add shadcn-vue deps, `components.json`, and light CSS variable theme.
2. Generate/commit phase-1 `app/components/ui/*`.
3. Update `app.vue` and `main.css` to consume tokens.
4. Replace Tabs → filter trio → `RepoCard` → empty/error states on all five pages.
5. Run existing Vitest suite; adjust selectors only if needed; do not change business assertion meaning.

## Acceptance

- All five boards share one visual system; controls look like shadcn components.
- Search / language / sort / summary behaviors match current product.
- Light theme only; no marketing hero; dual-column cards retained.
- `npm test` in `frontend/` passes.

## Non-goals

- Dark mode or system theme switching
- Table / list ranking layout
- Toolbar redesign (deferred)
- API, Postgres schema, sync/backfill, or historical `data/` migration
- Changing on-demand summary contract
