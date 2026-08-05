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
| Nuxt DB client | `pg` (node-postgres), no second ORM required |
| Schema migrations | Idempotent `migrate up` step at start of sync (and backfill) Actions jobs |
| Production deploy | Actions deploys Nuxt to the server over SSH after a successful sync (adapt `deploy/`); GitHub Pages removed from the product path |
| Secrets | `DATABASE_URL` and related secrets only in env / Actions Secrets |

## Architecture

```
GitHub Search / raw README / Stargazers (backfill)
        │
        ▼
GitHub Actions
  migrate → sync|backfill → (sync only) SSH deploy Nuxt
        │
        │  psycopg (DATABASE_URL read-write)
        ▼
PostgreSQL
        ▲
        │  pg (DATABASE_URL read-only role)
        │
Server: Nuxt Nitro ◄── nginx (TLS) ◄── users
```

No always-on Python API. Pipeline remains CLI in Actions.

## Network and connectivity (blocking)

GitHub-hosted Actions runners must reach Postgres on the server host/port.

**Required before go-live (pick one and document in DEPLOY.md):**

1. Expose Postgres on a reachable address with firewall allowlisting that still permits Actions egress, **or**
2. Run Actions on a self-hosted runner on the same network as Postgres, **or**
3. Another tunnel/VPN approach that gives runners a stable path to the DB

If runners cannot open a TCP connection to Postgres, sync cannot be the system of record. Do not ship assuming localhost-only Postgres.

Prefer separate DB roles when practical:

- Actions / pipeline: read-write  
- Nuxt: read-only  

## Data model

Migrations live under `db/migrations/`. Python and Nuxt share the same schema; SQL migrations are the source of truth (not a TS or Python ORM schema).

### Tables

**repos** — watch-set metadata  
`repo_id` PK, `repo_name`, `description`, `stars`, `forks`, `language`, `html_url`, `created_at`, `readme_hash`, `backfilled_365`, `updated_at`

**snapshots** — daily star/fork points (replaces `history/*.csv`)  
PK `(repo_id, date)`, `stars`, `forks`  
`repo_id` FK → `repos(repo_id)`  
Retention ≈ 400 days (delete older rows on sync)

**readmes** — README excerpts for summarization  
`repo_id` PK FK → `repos`, `hash`, `excerpt`

**summaries** — AI summary cache  
`repo_id` PK FK → `repos`, `readme_hash`, `summary` JSONB, `generated_at`

**leaderboards** — precomputed boards  
`type` PK (`total` | `daily` | `weekly` | `monthly` | `yearly`), `generated_at`, `items` JSONB  
`items` must match `LeaderboardPayload.items` (including embedded `summary` when present)

Growth is computed in the pipeline and stored in `leaderboards`. Nitro does not recompute growth over the watch set on request.

### Repo lifecycle

- Each sync **upserts** the current watch set into `repos` and writes **today’s** snapshots only for that set.
- Repos that fall out of the watch set **stop receiving new snapshots**; rows are **kept** (no physical delete) so history and FKs remain valid.

## Watch set and ranking rules

### Total board

- Fetch Top 100 repos by stars via GitHub Search
- Persist as `leaderboards.type = total`

### Watch set (union, deduped)

Effective set:

1. Search **Top 500** by stars (this already includes Top 100; do not fetch Top 100 as a separate Search pass)  
2. Newcomers: created in last 30 days with ≥ 500 stars  
3. Members of the previous four growth boards (read from `leaderboards` in DB), when present  

Total board ranking still uses the top 100 by stars from the refreshed metadata (subset of the watch set after merge).

Only watch-set repos are upserted into `repos` and receive daily `snapshots`.

### Cold start (empty DB)

- Day 1 watch set = Top 500 ∪ newcomers only (no previous board members).  
- Daily/weekly growth appear as snapshots accumulate; monthly/yearly stay thin until enough history or G3 backfill lands.  
- Acceptance explicitly allows sparse yearly (and initially sparse shorter windows) after the first sync.

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

CLI commands: `sync`, `backfill`, and `migrate` (or migrate invoked as a library call from both jobs). Remove `stage` (JSON copy into frontend).

### sync (ordered)

1. `migrate up` (idempotent)  
2. Build watch set (Top 500 ∪ newcomers ∪ previous growth-board members)  
3. Upsert `repos`; upsert today’s `snapshots`; prune snapshots older than retention  
4. Refresh READMEs for board **candidates from a first board pass** → `readmes`  
5. Generate AI summaries when README hash changed → `summaries`  
6. **Rebuild boards with summaries loaded**, then write all five `leaderboards` rows  

Step 6 must not reuse a pre-summary board payload. Final `items` must embed the latest `summaries.summary` the same way today’s second `build_boards` call does.

### backfill

1. `migrate up`  
2. Process board candidates in batches; write 365-day anchors to `snapshots`; update `repos.backfilled_365`  
3. No git commit of `data/`

### Concurrency

`sync.yml` and `backfill.yml` use separate concurrency groups today and can overlap (e.g. 00:00 vs 00:30 UTC).

Rules:

- Snapshot writes are upsert by `(repo_id, date)` (idempotent).  
- Leaderboard writes are full-row replace per `type`.  
- Prefer short transactions per repo or per board write; avoid long multi-step transactions across network calls.  
- If a conflict appears in practice, serialize by sharing one concurrency group or shifting backfill later; not required for v1 if upserts stay idempotent.

### Actions workflow changes (both `sync.yml` and `backfill.yml`)

- Add `DATABASE_URL` (and deploy secrets on sync)  
- Run migrate before pipeline command  
- Remove all `git add data` / commit / push data steps  
- **sync.yml only:** after successful sync, build frontend and SSH-deploy to the server (evolve `deploy/deploy.sh` + nginx for Node upstream, not static-only Pages)  
- Remove GitHub Pages upload/deploy steps from the product path  
- Keep failure webhook notification  
- Stop treating `data/` as source of truth (clear and untrack when implementing)

### Code shape

Replace `data_files.py` file IO with a `db.py` (psycopg) module exposing domain operations (`load_repos`, snapshot upsert, `save_leaderboard`, load previous board members, etc.). Config gains `DATABASE_URL`.

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
- Switch from `nuxt generate` / static hosting to **Node SSR** (`nuxt build` + `node .output/server/index.mjs` or equivalent)  
- `baseURL` defaults to `/` for server deploy  
- Keep sitemap via server route; no longer rely on Pages prerender-only hosting

### DB access in Nuxt

- Use **`pg`** with a small pool  
- `DATABASE_URL` only via Nuxt **`runtimeConfig`** (runtime env on the server process)—never inlined at build time into the client bundle  
- Prefer read-only DB role for the Nuxt process

### Errors

- DB down → API 5xx + friendly page error state  
- Unknown board type → 404  
- Missing leaderboard row before first sync → return payload with `items: []` and a generated_at null or omit; UI shows empty state (not a hard crash)

## Deployment and security

- Server: systemd or pm2 runs the Nitro Node server; nginx terminates TLS and reverse-proxies to that process  
- **CD path:** successful daily `sync` job builds and SSH-deploys the Nuxt app (secrets: `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_PATH`, `SSH_PRIVATE_KEY`, plus server-side `DATABASE_URL`)  
- Manual/redeploy without sync remains possible via `workflow_dispatch` or a thin deploy workflow  
- Never commit connection strings or credentials  
- Rotate any password that appeared in chat history  
- Update `docs/DEPLOY.md` and `docs/OPERATIONS.md`; retire Pages-centric instructions; document DB network prerequisites

## Testing and acceptance

- Python: unit tests for growth/watch-set logic; DB layer against test DB or heavy mocks  
- Frontend: Nitro route tests with mocked DB; existing `useLeaderboard` tests unchanged  
- Acceptance path:  
  1. Confirm Actions → Postgres connectivity  
  2. Empty DB → one `sync` → five API types respond (yearly may be sparse)  
  3. UI loads all tabs on the server deployment  
  4. Second-day sync exercises previous-board-member watch-set branch  

## Out of scope

- GH Archive / BigQuery as primary growth source  
- Migrating historical `data/` into Postgres  
- Separate FastAPI service  
- Keeping GitHub Pages as the primary production host  
- Full 10k pool tracking  
- Physical deletion of repos that leave the watch set  

## Success criteria

1. Daily Actions sync migrates schema, writes watch-set snapshots and five leaderboards to Postgres, without committing `data/`  
2. Successful sync deploys Nuxt to the server; UI and `/api/leaderboards/*` read Postgres  
3. Total board reflects Top 100; growth boards derive from the G2 watch set; final leaderboard rows include summaries when generated  
4. Runners can reach Postgres (documented network choice); no secrets in git; docs match the new deploy path  
