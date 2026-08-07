## Learned User Preferences

- Prefers Chinese for product and architecture discussion; often answers design choices with short A/B/C picks or brief directives.
- For the database migration: keep daily sync on GitHub Actions, run the read API on the existing server with Postgres, and implement the API as Nuxt Nitro server routes (not a separate Python API).
- Do not migrate existing `data/` JSON/CSV history into Postgres; start from an empty database and re-accumulate via sync.
- Growth ranking uses local daily snapshots (Approach A) on a reduced watch set—not a ~10k full pool and not GH Archive/BigQuery as the primary source.
- Total board tracks Top 100 by stars; daily/weekly/monthly/yearly growth boards use the G2 watch set (Top 500 ∪ newcomers ∪ previous growth-board members).
- Keep the RepoCard grid (not a table-first layout); total board shows screenshot-style fields, while growth boards additionally show the matching window’s star growth.
- Repo AI summaries are on-demand only: no default/batch summary in daily sync; each card has a generate button that calls the API and persists to the database.
- Frontend redesign direction: dense “数据台” console with shadcn-vue—light theme only, graphite neutrals + teal primary `#0F766E`, high information density—not a marketing/landing hero layout and not dark mode.
- Prefer design-system-first UI rollout: land shadcn-vue `ui/*` primitives before restyling business components; phase-1 set is button, input, select, badge, card, tabs, separator, skeleton, alert (no dialog/dropdown/sheet yet).

## Learned Workspace Facts

- github-ranking is a GitHub star trend leaderboard: Python pipeline under `scripts/`, Nuxt frontend under `frontend/`, historically file-backed under `data/` and published as a static site.
- Target persistence is PostgreSQL (`github-ranking`, `public` schema); store only `DATABASE_URL` (and related secrets) in environment or Actions secrets—never commit connection strings or credentials.
- Target runtime split: Actions sync/backfill write Postgres only; Nuxt SSR is deployed manually on the existing server (no Actions SSH deploy, no GitHub Pages).
- Shared schema lives in idempotent SQL under `db/migrations/`; the Python pipeline uses psycopg (`db.py`); `stage` and file-backed `data/` are no longer the source of truth.
- Nuxt reads Postgres via `pg` with runtime config (`NUXT_DATABASE_URL` / `DATABASE_URL`); deploy rsyncs `.output/` contents so the process entry is `server/index.mjs`.
- Only the G2 watch set receives daily snapshots; five precomputed `leaderboards` rows are served by Nitro without recomputing growth on request.
- Sync persists `open_issues` / `pushed_at` from GitHub and no longer batch-refreshes README or AI summaries; missing card fields may show as "—" until Actions fills them.
- Board items expose `has_summary` (and related card fields) without embedding summary text by default; on-demand Chinese summaries are served through Nitro GET/POST routes and written to the database.
- Frontend UI stack is Nuxt 3 + Tailwind v4 + shadcn-vue; primitives live under `frontend/app/components/ui/`, and light graphite/teal theme tokens live in `frontend/app/assets/css/main.css`.
