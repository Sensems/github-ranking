## Learned User Preferences

- Prefers Chinese for product and architecture discussion; often answers design choices with short A/B/C picks or brief directives.
- For the database migration: keep daily sync on GitHub Actions, run the read API on the existing server with Postgres, and implement the API as Nuxt Nitro server routes (not a separate Python API).
- Do not migrate existing `data/` JSON/CSV history into Postgres; start from an empty database and re-accumulate via sync.
- Growth ranking uses local daily snapshots (Approach A) on a reduced watch set—not a ~10k full pool and not GH Archive/BigQuery as the primary source.
- Total board tracks Top 100 by stars; daily/weekly/monthly/yearly growth boards use the G2 watch set (Top 500 ∪ newcomers ∪ previous growth-board members).

## Learned Workspace Facts

- github-ranking is a GitHub star trend leaderboard: Python pipeline under `scripts/`, Nuxt frontend under `frontend/`, historically file-backed under `data/` and published as a static site.
- Target persistence is PostgreSQL (`github-ranking`, `public` schema); store only `DATABASE_URL` (and related secrets) in environment or Actions secrets—never commit connection strings or credentials.
- Target runtime split: Actions sync writes Postgres then SSH-deploys Nuxt SSR; Nitro on the existing server serves read-only APIs and the app against that database (GitHub Pages removed from the product path).
- Shared schema lives in idempotent SQL under `db/migrations/`; the Python pipeline uses psycopg (`db.py`); `stage` and file-backed `data/` are no longer the source of truth.
- Nuxt reads Postgres via `pg` with runtime config (`NUXT_DATABASE_URL` / `DATABASE_URL`); deploy rsyncs `.output/` contents so the process entry is `server/index.mjs`.
- Only the G2 watch set receives daily snapshots; five precomputed `leaderboards` rows are served by Nitro without recomputing growth on request.
