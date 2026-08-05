# PostgreSQL + Nuxt Nitro Architecture Design

Date: 2026-08-05  
Status: Approved for implementation planning

## Goal

Replace file-backed `data/` persistence and GitHub Pages static hosting with:

- PostgreSQL as the system of record
- GitHub Actions for daily sync/backfill (writes DB)
- Nuxt Nitro on the existing server for read-only APIs and SSR UI

Do **not** migrate existing `data/` JSON/CSV. Start from an empty database and re-accumulate via sync.

## Decisions

| Topic | Choice |
|---|---|
| Database | PostgreSQL (`github-ranking`, `public`) |
| Frontend data access | Nuxt Nitro read-only API (not a separate Python API) |
| Hosting | Nuxt + API on the existing server near Postgres |
| Sync location | GitHub Actions (unchanged) |
| Growth method | Local daily snapshots (Approach A); not GH Archive as primary |
| Pool scope | No 10k full pool |
| Total board | Track/search Top 100 by stars |
| Growth boards | G2 small watch set + snapshots; G3 backfill for 365d anchors on board candidates |
| Secrets | `DATABASE_URL` and related secrets only in env / Actions Secrets |

## Architecture

```
GitHub Search / raw README / Stargazers (backfill)
        │
        ▼
GitHub Actions: python scripts/main.py sync|backfill
        │  (psycopg, DATABASE_URL)
        ▼
PostgreSQL
        │
        ▼
Server: Nuxt (Nitro) ──nginx──► users
        read-only pg / Drizzle
```

No always-on Python API. Pipeline remains CLI in Actions.

## Data model

Migrations live under `db/migrations/`. Python and Nuxt share the same schema; neither owns a divergent ORM model as source of truth.

### Tables

**repos** — watch-set metadata  
`repo_id` PK, `repo_name`, `description`, `stars`, `forks`, `language`, `html_url`, `created_at`, `readme_hash`, `backfilled_365`, `updated_at`

**snapshots** — daily star/fork points (replaces `history/*.csv`)  
PK `(repo_id, date)`, `stars`, `forks`  
Retention ≈ 400 days

**readmes** — README excerpts for summarization  
`repo_id` PK, `hash`, `excerpt`

**summaries** — AI summary cache  
`repo_id` PK, `readme_hash`, `summary` JSONB, `generated_at`

**leaderboards** — precomputed boards  
`type` PK (`total` | `daily` | `weekly` | `monthly` | `yearly`), `generated_at`, `items` JSONB

Growth is computed in the pipeline and stored in `leaderboards`. Nitro does not recompute growth over the full watch set on request.

## Watch set and ranking rules

### Total board

- Fetch Top 100 repos by stars via GitHub Search
- Persist as `leaderboards.type = total`

### Watch set (union, deduped)

1. Current total Top 100  
2. Members of the previous four growth boards (read from DB)  
3. Newcomers: created in last 30 days with ≥ 500 stars  
4. Search Top 500 buffer  

Only watch-set repos are upserted into `repos` and receive daily `snapshots`.

### Growth boards (daily / weekly / monthly / yearly)

Windows unchanged: 1 / 7 / 30 / 365 days.  
Growth = current stars − nearest snapshot within ±3 days of target date.  
Eligibility unchanged unless later revised: ≥ 1000 stars and repo age ≥ window days.  
Sort by window growth descending; keep Top 100 each.

### README and summaries

Refresh only for repos currently on any of the five boards (not the entire watch set).

### Backfill (G3)

Batch job for board candidates missing a ~365-day snapshot anchor, using Stargazers API (`star+json`), writing into `snapshots`.

## Pipeline (Actions)

CLI commands remain: `sync`, `backfill`. `stage` (copy JSON into frontend) is removed or no-oped.

### sync

1. Build watch set (Top 500 + newcomers + previous board members + Top 100)  
2. Upsert `repos`; append/upsert today’s `snapshots`; prune old snapshots  
3. `build_boards` → five boards  
4. Refresh READMEs for board candidates → `readmes`  
5. Generate AI summaries when README hash changed → `summaries`  
6. Write `leaderboards`

### backfill

Process board candidates in batches; write 365-day anchors to `snapshots`; update `repos.backfilled_365`.

### Actions workflow changes

- Add `DATABASE_URL` secret  
- Run migrations when needed (explicit step or documented manual step)  
- Remove commit-of-`data/` step  
- Remove GitHub Pages build/deploy steps from the daily product path  
- Keep failure webhook notification  
- Stop treating `data/` as source of truth (may clear and untrack)

### Code shape

Replace `data_files.py` file IO with a `db.py` (psycopg) module exposing the same domain operations (`load_repos`, `append_history` → snapshot upsert, `save_leaderboard`, etc.). Config gains `DATABASE_URL`.

## Nitro API and frontend

### Routes

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/leaderboards/:type` | Return `LeaderboardPayload` from `leaderboards` |
| GET | `/api/health` | DB connectivity check |

Payload shape stays aligned with `frontend/app/types/leaderboard.ts`.

### Frontend

- Remove static imports of `app/data/leaderboards/*.json`  
- Pages use `useFetch('/api/leaderboards/...')` (SSR, same origin)  
- Keep `useLeaderboard` client filter/sort  
- `baseURL` defaults to `/` for server deploy (not GitHub Pages project path)

### DB access in Nuxt

Use `pg` or Drizzle with a small pool. Connection only via `DATABASE_URL`. Prefer a DB role with read-only privileges for the Nuxt process when practical; Actions uses a read-write role.

### Errors

- DB down → API 5xx + friendly page error state  
- Unknown board type → 404  
- Missing row after fresh install → empty items or 404; document expected empty state before first sync

## Deployment and security

- Server runs `nuxt build` output under Node (systemd/pm2)  
- nginx terminates TLS and reverse-proxies to Node  
- Adapt `deploy/` for artifact sync + process restart  
- Never commit connection strings or credentials  
- Rotate any password that appeared in chat history  
- Update `docs/DEPLOY.md` and `docs/OPERATIONS.md`; retire Pages-centric instructions

## Testing and acceptance

- Python: unit tests for growth/watch-set logic; DB layer against test DB or heavy mocks  
- Frontend: Nitro route tests with mocked DB; existing `useLeaderboard` tests unchanged  
- Acceptance path: empty DB → one Actions/manual `sync` → five API board types return data → UI loads all tabs

## Out of scope

- GH Archive / BigQuery as primary growth source  
- Migrating historical `data/` into Postgres  
- Separate FastAPI service  
- Keeping GitHub Pages as the primary production host  
- Full 10k pool tracking

## Success criteria

1. Daily Actions sync writes watch-set snapshots and five leaderboards to Postgres without committing `data/`  
2. Server Nuxt serves UI and `/api/leaderboards/*` from Postgres  
3. Total board reflects Top 100; growth boards derive from the G2 watch set  
4. No secrets in git; docs match the new deploy path  
