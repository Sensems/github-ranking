# RepoRank-Style Table Leaderboard + Dual Theme

Date: 2026-08-07  
Status: Approved for implementation planning

## Goal

Restyle the Nuxt leaderboard into a dense, mockup-aligned **horizontal row/table** console with **sticky search toolbar and sticky column headers**, plus **dark (default) neon-green** and **companion light** themes. Do not change sync pipelines, Postgres schema, or ranking rules. Keep brand title「GitHub Star 趋势榜」(not RepoRank).

This supersedes the prior frontend preference for light-only teal + RepoCard grid for list presentation and color mode.

## Decisions

| Topic | Choice |
|---|---|
| List presentation | Horizontal row/table (Approach A); not RepoCard grid |
| Narrow screens | Same table with horizontal scroll; no second card layout |
| Color mode | Dual theme; default dark; toggle + `localStorage` |
| Palette | Dark neon green accent (mockup); light companion with darker green for contrast |
| Brand | Keep「GitHub Star 趋势榜」; trend-line icon OK; no RepoRank rename |
| Sticky chrome | Site header → toolbar (search + language + sort) → column headers |
| Implementation | New `RepoRow` (replace grid `RepoCard`); CSS sticky stacking; token dual theme |
| Out of scope | Data Table library; sync/DB changes; brand rename; mobile card variant |

## Information architecture

Top to bottom:

1. **Site header (sticky, `top: 0`)**  
   Left: brand + small trend icon. Center: board nav (总排名 / 日增速 / 周增速 / 月增速 / 年增速) with neon underline active state. Right: updated-at + theme toggle.

2. **Page header (not sticky)**  
   Eyebrow (`OVERALL` / `GROWTH · DAILY` / …) → Chinese title → `TOP N` badge → description.

3. **Toolbar (sticky under header)**  
   Search + language + sort + result count; clear-filters when active.

4. **Column headers (sticky under toolbar)**  
   - Total: 排名 | 仓库 | 主语言 | STAR 总数 | FORK | 未关闭 ISSUE | 最近提交 | 操作  
   - Growth boards: same + window growth column (今日/本周/本月/今年增速)

5. **Rows**  
   One repo per row; growth boards show signed `+N` and a small green magnitude bar; actions: 生成/查看概况, 查看仓库 →. Expanded summary renders inline below the row.

## Visual & theme tokens

### Dark (default)

| Role | Approx hex | Notes |
|---|---|---|
| Background | `#0D1117` | Page canvas |
| Surface / row | `#161B22` | Row / elevated panels |
| Foreground | `#FFFFFF` | Primary text |
| Muted text | `#8B949E` | Secondary / meta |
| Border | `#30363D` | Hairline separators |
| Primary / accent | `#39D353` | Nav active, rank, growth, outline CTAs |
| Star accent | `#E3B341` | Star icon only |

### Light (companion)

| Role | Approx hex | Notes |
|---|---|---|
| Background | `#F6F8FA` | Page canvas |
| Surface / row | `#FFFFFF` | Rows |
| Foreground | `#1F2328` | Primary text |
| Muted text | `#636C76` | Secondary |
| Border | `#D0D7DE` | Dividers |
| Primary / accent | `#0F9F55` | Darker green for WCAG contrast |

Implementation: map into shadcn CSS variables in `frontend/app/assets/css/main.css` (`:root` light, `.dark` dark). Toggle sets `class="dark"` on `html`; preference in `localStorage`; first visit defaults to dark.

Motion: keep restrained fade/stagger; honor `prefers-reduced-motion`.

## Components

| Unit | Responsibility |
|---|---|
| `app.vue` | Shell: sticky site header (brand, `LeaderboardTabs`, updated-at, theme toggle), main, footer |
| Color-mode composable | Read/write `localStorage`; toggle `html.dark`; default dark on first visit |
| `LeaderboardTabs` | Header link nav with underline active; rendered inside site header (removed from page body) |
| Board updated-at | `LeaderboardView` provides `generated_at` upward (provide/inject or shared ref); header displays「更新 …」 |
| `LeaderboardView` | Page header + sticky toolbar + sticky col headers + row list; reuse filter/sort/pagination |
| `RepoRow` | Replaces `RepoCard` grid cell; columns + growth bar + actions + inline summary |
| `SearchBox` / `LanguageFilter` / `SortSelect` | Unchanged behavior; sit in sticky toolbar |
| `main.css` | Dual-theme tokens; sticky offset CSS variables |

Data flow unchanged: Nitro `/api/leaderboards/[type]` → `useLeaderboard` → filters/sort → rows. Summary GET/POST APIs unchanged. Growth boards continue default-sort by window growth.

## Sticky mechanics

Use CSS `position: sticky` with stacked offsets:

- Site header: `top: 0`
- Toolbar: `top: var(--site-header-h)`
- Column headers: `top: calc(var(--site-header-h) + var(--toolbar-h))`

Horizontal scroll container shares one `min-width` for header row and body rows so columns stay aligned while scrolling.

## Empty / error states

Keep existing Alert patterns:

- Load failure
- Empty board (`emptyHint`)
- Filter no-match + clear-filters control

No new dialogs/sheets.

## Testing

- Rename/adapt `RepoCard.spec.ts` → `RepoRow.spec.ts` (columns, growth bar visibility, summary actions)
- Update board-page / LeaderboardView assertions for table structure and sticky regions as needed
- Theme toggle: preference persistence smoke coverage if inexpensive; otherwise manual check

## Non-goals

- Migrating sync or Postgres schema
- Introducing TanStack Table (or similar)
- Separate mobile card layout
- Renaming product to RepoRank
- Changing ranking rules or board payload shape (beyond existing fields already returned)
