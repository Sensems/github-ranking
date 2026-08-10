# Mobile Responsive Board Design

**Date:** 2026-08-10  
**Status:** Approved (Approach C — adapt same row/table)

## Goal

Make「GitHub Star 趋势榜」usable on phones without a second card-grid layout. Narrow screens reflow the existing row/table board into stacked rows; desktop (`md+`) keeps the current dense subgrid table.

## Out of scope

- New `RepoCard` / card-grid shell
- Dialog / sheet / bottom-sheet filter UI
- Changing board data, API, or sort defaults
- Separate mobile-only components (prefer CSS + light markup hooks on existing components)

## Breakpoint

| Range | Layout |
|-------|--------|
| `< md` (Tailwind default, &lt;768px) | Stacked board rows; hide column header; chrome compacted |
| `md+` | Unchanged desktop subgrid table (`min-width` + sticky colhead) |

## Board rows (mobile)

Same `RepoRow` / `board-row-card` chrome (border, top-3 accents, 概况 panel).

Stack order:

1. **Rank + repo** — rank and name on one line; description `line-clamp-2` below
2. **Meta strip** — language · stars · forks · open issues · last push; growth boards insert the window growth (signed + bar) after stars
3. **Actions** — 概况 + 查看仓库, full-width-friendly, min touch height ~40–44px

Sticky column header (`.board-colhead`) is `display: none` below `md`. Parent `.board-table` drops `min-width` and becomes a single-column list (no forced horizontal page scroll).

概况 panel stays `col-span-full` / full-width under the row; summary internal `sm:grid-cols-3` already stacks on narrow screens.

## Chrome

- **Header:** Keep brand + theme toggle; tabs stay horizontally scrollable (`overflow-x-auto`, `nowrap`) so they do not wrap and inflate `--site-header-h`. Optional: slightly smaller brand type already present via `sm:text-lg`.
- **Toolbar:** Keep sticky under header; search full width; language/sort share a second wrap row; result count on its own wrap line. Avoid changing filter semantics.
- **Back-to-top:** Keep fixed bottom-right; nudge inset for safe area if cheap (`env(safe-area-inset-*)`).

## CSS strategy

1. Add stable cell hooks on header + `RepoRow` (`board-cell-rank`, `board-cell-repo`, `board-cell-lang`, `board-cell-stars`, `board-cell-forks`, `board-cell-issues`, `board-cell-pushed`, `board-cell-growth`, `board-cell-actions`).
2. In `main.css`, under `@media (max-width: 767px)` (or Tailwind `@variant` / max-md block):
   - Reset `.board-table--total|growth` to one column, `min-width: 0`
   - Hide `.board-colhead`
   - Replace row subgrid with an explicit stacked grid / flex for `.board-row-card`
   - Group metric cells into a meta row (flex wrap + muted separators or gaps)
3. Desktop rules remain the source of truth above `md`; do not regress subgrid alignment.

## Accessibility / UX

- No layout that relies on hover-only actions
- Touch targets for primary actions ≥ ~40px height on mobile
- Preserve existing `prefers-reduced-motion` behavior
- Viewport meta already set in `nuxt.config.ts` — no change required

## Testing

- Extend `RepoRow` / board tests only if markup hooks or visible structure assertions break; prefer asserting cell classes exist and content still renders.
- Manual: Chrome/Firefox device mode ~375px and ~768px — no horizontal page scroll; desktop table unchanged at 1280px.

## Success criteria

- Phone width: board scannable without horizontal page scroll
- Same components and dual-theme tokens
- Desktop table visually unchanged
