# Postgres + Nuxt Nitro Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace file-backed `data/` and GitHub Pages with PostgreSQL persistence, Actions writers, and a server-hosted Nuxt Nitro read API/UI.

**Architecture:** Python sync/backfill in GitHub Actions writes a small watch set and five precomputed leaderboards to Postgres; Nuxt on the existing server reads via `pg` and Nitro routes; successful sync SSH-deploys the Node SSR app. No historical `data/` migration.

**Tech Stack:** Python 3.12, psycopg3, pytest, Nuxt 3, Nitro, `pg`, GitHub Actions, nginx + Node on server, PostgreSQL.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-05-postgres-nitro-architecture-design.md`
- Never commit `DATABASE_URL` or credentials; use env / Actions Secrets only
- Do not migrate existing `data/` JSON/CSV; empty DB start is expected
- Watch set = Search Top 500 ∪ newcomers (≥500★, 30d) ∪ previous growth-board members; total board = Top 100 by stars
- Growth windows: daily=1, weekly=7, monthly=30, yearly=365; ±3 day snapshot tolerance; participation ≥1000★ and age ≥ window
- Final leaderboard write must rebuild boards after summaries so `items[].summary` is populated
- Nuxt uses `pg` + `runtimeConfig` (runtime `DATABASE_URL`); no client-bundled secrets
- Remove Pages from product path; sync job deploys Nuxt over SSH after success
- Actions runners must reach Postgres (document network choice in DEPLOY.md)

---

## File structure

| Path | Responsibility |
|---|---|
| `db/migrations/001_init.sql` | Schema: repos, snapshots, readmes, summaries, leaderboards + FKs |
| `scripts/migrate.py` | Idempotent migrate up (schema_migrations + apply SQL files) |
| `scripts/db.py` | psycopg domain IO (replaces `data_files.py`) |
| `scripts/config.py` | `DATABASE_URL`, `WATCH_TOP_N=500`, drop file `DATA_DIR` as source of truth |
| `scripts/pool.py` | `build_watch_set(...)` |
| `scripts/growth.py` | Keep growth math; history via `db.load_history` |
| `scripts/main.py` | sync/backfill/migrate CLI; remove `stage` |
| `scripts/data_files.py` | Delete after callers moved (or thin shim removed in same task) |
| `tests/test_migrate.py`, `tests/test_db.py`, `tests/test_pool.py`, `tests/test_main.py` | Pipeline tests |
| `frontend/package.json` | Add `pg`; ensure build script for SSR |
| `frontend/nuxt.config.ts` | `runtimeConfig.databaseUrl`; SSR defaults |
| `frontend/server/utils/db.ts` | Server-only pg pool |
| `frontend/server/api/health.get.ts` | Health check |
| `frontend/server/api/leaderboards/[type].get.ts` | Board API |
| `frontend/app/pages/*.vue` | `useFetch` instead of JSON import |
| `frontend/tests` or colocated API tests | Mocked DB route tests |
| `.github/workflows/sync.yml` | migrate → sync → build → SSH deploy; no data commit; no Pages |
| `.github/workflows/backfill.yml` | migrate → backfill; no data commit |
| `deploy/deploy.sh`, `deploy/nginx.conf.example` | Node upstream deploy |
| `docs/DEPLOY.md`, `docs/OPERATIONS.md`, `README.md` | New topology |
| `data/` | Clear/untrack in final cleanup task (not migrated) |

---

### Task 1: Schema migration runner

**Files:**
- Create: `db/migrations/001_init.sql`
- Create: `scripts/migrate.py`
- Modify: `scripts/config.py`
- Modify: `requirements.txt` (add `psycopg[binary]>=3.2`)
- Modify: `scripts/main.py` (add `migrate` command)
- Test: `tests/test_migrate.py`

**Interfaces:**
- Consumes: `DATABASE_URL` from env via `config.DATABASE_URL`
- Produces: `migrate.migrate_up(conn) -> int` (number of newly applied migrations); CLI `python scripts/main.py migrate`

- [ ] **Step 1: Add dependency and config**

In `requirements.txt` add:

```
psycopg[binary]==3.2.4
```

In `scripts/config.py` add:

```python
DATABASE_URL = os.environ.get("DATABASE_URL", "")
WATCH_TOP_N = 500
TOTAL_BOARD_SIZE = 100
# Keep LEADERBOARD_SIZE = 100 for growth boards
# Change POOL_SIZE usages later; leave POOL_SIZE = WATCH_TOP_N or replace call sites
```

Set `POOL_SIZE = WATCH_TOP_N` (500) so existing `fetch_pool(client, POOL_SIZE)` matches the spec buffer.

- [ ] **Step 2: Write failing test for migrate_up**

```python
# tests/test_migrate.py
from unittest.mock import MagicMock
import migrate


def test_migrate_up_applies_pending_and_records():
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    # first fetchone: schema_migrations missing -> create path handled in SQL executes
    # simplify: stub execute + fetchall for applied versions empty, then one file applied
    cur.fetchall.return_value = []  # no applied versions
    applied = migrate.migrate_up(conn, migrations_dir=migrate.DEFAULT_MIGRATIONS_DIR)
    assert applied >= 1
    conn.commit.assert_called()
```

Adapt the mock to whatever concrete control flow you implement; the assertion is: pending SQL files run once and version rows inserted.

- [ ] **Step 3: Run test — expect FAIL**

Run: `python -m pytest tests/test_migrate.py -v`  
Expected: FAIL (module/import missing)

- [ ] **Step 4: Implement `001_init.sql` and `migrate.py`**

`db/migrations/001_init.sql`:

```sql
CREATE TABLE IF NOT EXISTS repos (
  repo_id BIGINT PRIMARY KEY,
  repo_name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  stars INT NOT NULL,
  forks INT NOT NULL,
  language TEXT,
  html_url TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  readme_hash TEXT,
  backfilled_365 DATE,
  updated_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
  repo_id BIGINT NOT NULL REFERENCES repos(repo_id),
  date DATE NOT NULL,
  stars INT NOT NULL,
  forks INT NOT NULL,
  PRIMARY KEY (repo_id, date)
);

CREATE TABLE IF NOT EXISTS readmes (
  repo_id BIGINT PRIMARY KEY REFERENCES repos(repo_id),
  hash TEXT NOT NULL,
  excerpt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
  repo_id BIGINT PRIMARY KEY REFERENCES repos(repo_id),
  readme_hash TEXT,
  summary JSONB NOT NULL,
  generated_at DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS leaderboards (
  type TEXT PRIMARY KEY,
  generated_at DATE,
  items JSONB NOT NULL DEFAULT '[]'::jsonb
);
```

`scripts/migrate.py`: maintain `schema_migrations(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ)`; apply `db/migrations/*.sql` in sorted order inside a transaction per file; no-op if already applied.

Wire `main.py` choices to include `migrate`.

- [ ] **Step 5: Run tests — expect PASS**

Run: `python -m pytest tests/test_migrate.py -v`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt scripts/config.py scripts/migrate.py scripts/main.py db/migrations/001_init.sql tests/test_migrate.py
git commit -m "feat(db): add Postgres schema migrations"
```

---

### Task 2: `db.py` persistence layer

**Files:**
- Create: `scripts/db.py`
- Create: `tests/test_db.py`
- Modify: callers later; this task only delivers `db.py` + tests (mock connection)

**Interfaces:**
- Consumes: `config.DATABASE_URL`, `HISTORY_RETENTION_DAYS`
- Produces:
  - `connect() -> psycopg.Connection`
  - `upsert_repo(conn, repo: dict) -> None`
  - `load_repos(conn) -> dict[int, dict]`
  - `upsert_snapshot(conn, repo_id: int, when: str, stars: int, forks: int) -> None`
  - `load_history(conn, repo_id: int) -> list[dict]`  # `{date, stars, forks}`
  - `prune_snapshots(conn, retention_days: int) -> int`
  - `save_readme` / `load_readme` / `save_summary` / `load_summary`
  - `save_leaderboard(conn, name: str, payload: dict) -> None`
  - `load_leaderboard(conn, name: str) -> dict | None`
  - `load_previous_growth_members(conn) -> set[int]`  # repo_ids from daily/weekly/monthly/yearly items

- [ ] **Step 1: Write failing tests for snapshot upsert idempotency and previous members**

```python
# tests/test_db.py — use a real DATABASE_URL if set; otherwise skip integration
# Plus pure unit tests with MagicMock verifying UPSERT SQL contains ON CONFLICT
import os
import pytest
import db

pytestmark = pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")


def test_snapshot_upsert_idempotent():
    with db.connect() as conn:
        db.upsert_repo(conn, {
            "repo_id": 1, "repo_name": "o/r", "description": "", "stars": 10, "forks": 1,
            "language": "Python", "html_url": "https://github.com/o/r",
            "created_at": "2020-01-01T00:00:00Z",
        })
        db.upsert_snapshot(conn, 1, "2026-08-05", 10, 1)
        db.upsert_snapshot(conn, 1, "2026-08-05", 12, 2)
        hist = db.load_history(conn, 1)
        assert hist[-1] == {"date": "2026-08-05", "stars": 12, "forks": 2}
        conn.rollback()
```

Also add a non-skipped mock test that `upsert_snapshot` executes SQL containing `ON CONFLICT`.

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/test_db.py -v`

- [ ] **Step 3: Implement `scripts/db.py`**

Use `psycopg.connect(DATABASE_URL)`; `upsert_snapshot` = `INSERT ... ON CONFLICT (repo_id, date) DO UPDATE SET stars=EXCLUDED.stars, forks=EXCLUDED.forks`; `save_leaderboard` replaces row by `type`; `load_previous_growth_members` parses `items` JSON for types in `daily/weekly/monthly/yearly`.

- [ ] **Step 4: Run tests — expect PASS** (mock tests always; integration if URL set)

- [ ] **Step 5: Commit**

```bash
git add scripts/db.py tests/test_db.py
git commit -m "feat(db): add psycopg persistence helpers"
```

---

### Task 3: Watch set builder (G2)

**Files:**
- Modify: `scripts/pool.py`
- Modify: `tests/test_pool.py`

**Interfaces:**
- Consumes: `GitHubClient.top_repos_by_stars`, `fetch_newcomers`, `db.load_previous_growth_members` results passed in
- Produces: `build_watch_set(client, previous_ids: set[int], limit: int = WATCH_TOP_N) -> dict[int, dict]`

- [ ] **Step 1: Write failing test**

```python
def test_build_watch_set_unions_top_newcomers_and_previous(monkeypatch):
    class FakeClient:
        def top_repos_by_stars(self, limit):
            return [{"id": 1, "full_name": "a/a", "description": "", "stargazers_count": 5000,
                     "forks_count": 1, "language": "Go", "html_url": "https://x", "created_at": "2020-01-01T00:00:00Z"}]
        def search(self, query, per_page=100, page=1):
            return {"items": []}

    # monkeypatch fetch_newcomers to return {2: {...}}
    # previous_ids = {3}
    # need repo 3 merged from previous — if not in fresh fetch, build_watch_set must still include stub from load_repos OR require previous repos already in `existing`
```

Spec detail to implement: previous board members come from DB `repos` rows already stored; `build_watch_set` should:

```python
def build_watch_set(client, existing: dict[int, dict], previous_ids: set[int], limit: int = WATCH_TOP_N) -> dict[int, dict]:
    fresh = fetch_pool(client, limit)
    newcomers = fetch_newcomers(client)
    merged = merge_pool(existing, fresh, newcomers)
    # ensure previous_ids present: keep existing entries; if missing, leave absent (cannot snapshot without metadata)
    return {rid: merged[rid] for rid in set(merged) | (previous_ids & set(merged)) }  # actually return full merged; previous only forces retention of existing rows still in `existing`
```

Clearer rule for implementer:

1. `merged = merge_pool(existing, fetch_pool(client, WATCH_TOP_N), fetch_newcomers(client))`
2. For each `rid in previous_ids`, if `rid in existing` and `rid not in merged`, add `existing[rid]` into merged (retain last known metadata until next Search hit)
3. Return `merged`

- [ ] **Step 2: Run FAIL, implement, PASS**

Run: `python -m pytest tests/test_pool.py -v`

- [ ] **Step 3: Commit**

```bash
git add scripts/pool.py tests/test_pool.py scripts/config.py
git commit -m "feat(pool): build G2 watch set (top500 + newcomers + previous)"
```

---

### Task 4: Rewire growth + sync/backfill to Postgres

**Files:**
- Modify: `scripts/growth.py` (use `db.load_history` / `db.load_summary` with conn or thin wrappers)
- Modify: `scripts/main.py`
- Modify: `scripts/backfill.py`
- Modify: `scripts/summary.py` (save via db)
- Modify: `tests/test_growth.py`, `tests/test_main.py`, `tests/test_backfill.py`, `tests/test_summary.py`, `tests/test_snapshot.py`
- Delete or stop importing: `scripts/data_files.py`, `scripts/snapshot.py` if prune moves into `db.prune_snapshots`

**Interfaces:**
- Consumes: Task 2 `db.*`, Task 3 `build_watch_set`
- Produces: CLI `sync` / `backfill` writing only Postgres; no `stage`

- [ ] **Step 1: Update growth to accept history loader**

Prefer keeping pure functions testable:

```python
def build_boards(repos, today, *, load_history, load_summary, total_size=TOTAL_BOARD_SIZE, board_size=LEADERBOARD_SIZE):
    ...
```

Default loaders close over a connection in `main.sync`.

Total board: sort all watch-set repos by stars, take `TOTAL_BOARD_SIZE` (100).  
Growth boards: unchanged eligibility/windows, size `LEADERBOARD_SIZE`.

- [ ] **Step 2: Rewrite `sync()` order per spec**

```python
def sync() -> None:
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL is required")
    migrate.migrate_up(...)  # or rely on Actions calling migrate separately; call both for safety
    with db.connect() as conn:
        client = GitHubClient(GITHUB_TOKEN)
        today = date.today()
        existing = db.load_repos(conn)
        previous = db.load_previous_growth_members(conn)
        repos = build_watch_set(client, existing, previous, WATCH_TOP_N)
        for repo in repos.values():
            db.upsert_repo(conn, repo)
            db.upsert_snapshot(conn, repo["repo_id"], today.isoformat(), repo["stars"], repo["forks"])
        db.prune_snapshots(conn, HISTORY_RETENTION_DAYS)
        boards = build_boards(repos, today, load_history=..., load_summary=...)
        refresh_readmes(...)  # save via db
        pending = pending_summaries(...)
        if pending and XFYUN_API_KEY:
            summarize_batch(...)  # must call db.save_summary
        boards = build_boards(repos, today, load_history=..., load_summary=...)  # rebuild with summaries
        for name, items in boards.items():
            db.save_leaderboard(conn, name, {"type": name, "generated_at": today.isoformat(), "items": items})
        conn.commit()
```

Remove `stage` command from argparse.

- [ ] **Step 3: Update backfill to use db upsert_snapshot / load_history**

- [ ] **Step 4: Fix tests** — replace filesystem fixtures with mocks or `DATABASE_URL` integration; ensure `test_main` no longer expects `stage` or `data/` writes

- [ ] **Step 5: Run full pytest**

Run: `python -m pytest -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/main.py scripts/growth.py scripts/backfill.py scripts/summary.py scripts/snapshot.py scripts/data_files.py tests
git commit -m "feat(pipeline): sync and backfill write Postgres watch set"
```

---

### Task 5: Nitro DB utils + API routes

**Files:**
- Modify: `frontend/package.json` (dependency `pg`)
- Modify: `frontend/nuxt.config.ts`
- Create: `frontend/server/utils/db.ts`
- Create: `frontend/server/api/health.get.ts`
- Create: `frontend/server/api/leaderboards/[type].get.ts`
- Create: `frontend/server/api/leaderboards/[type].spec.ts` (or vitest server test)

**Interfaces:**
- Consumes: `runtimeConfig.databaseUrl` from `process.env.DATABASE_URL`
- Produces: `GET /api/health`, `GET /api/leaderboards/:type` → `LeaderboardPayload`

- [ ] **Step 1: Config + pool**

```ts
// nuxt.config.ts
runtimeConfig: {
  databaseUrl: process.env.DATABASE_URL || '',
  public: { siteUrl: process.env.SITE_URL || 'https://github-trend.example.com' },
},
```

```ts
// server/utils/db.ts
import pg from 'pg'

let pool: pg.Pool | null = null
export function getPool() {
  const url = useRuntimeConfig().databaseUrl
  if (!url) throw createError({ statusCode: 500, statusMessage: 'DATABASE_URL not configured' })
  if (!pool) pool = new pg.Pool({ connectionString: url, max: 5 })
  return pool
}
```

- [ ] **Step 2: Implement routes**

`leaderboards/[type].get.ts`: validate type ∈ five boards; `SELECT generated_at, items FROM leaderboards WHERE type=$1`; if no row return `{ type, generated_at: null, items: [] }`; if DB error → 500.

`health.get.ts`: `SELECT 1` → `{ ok: true }`.

- [ ] **Step 3: Add vitest with mocked `getPool`**

Assert unknown type → 404; missing row → empty items.

- [ ] **Step 4: `npm test` in frontend — PASS**

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/nuxt.config.ts frontend/server
git commit -m "feat(frontend): Nitro health and leaderboard read APIs"
```

---

### Task 6: Pages switch to `useFetch` + SSR build

**Files:**
- Modify: `frontend/app/pages/index.vue`, `daily.vue`, `weekly.vue`, `monthly.vue`, `yearly.vue`
- Modify: `frontend/package.json` scripts (`build` for SSR; stop relying on `generate` for prod)
- Remove: `frontend/app/data/leaderboards/*.json` (if present)

**Interfaces:**
- Consumes: `/api/leaderboards/:type`
- Produces: SSR pages with empty-state friendly UI (already exists)

- [ ] **Step 1: Update each page**

```vue
<script setup lang="ts">
import { useLeaderboard } from '~/composables/useLeaderboard'
import type { LeaderboardPayload } from '~/types/leaderboard'

const { data, error } = await useFetch<LeaderboardPayload>('/api/leaderboards/total')
const payload = computed(() => data.value ?? { type: 'total', generated_at: '', items: [] })
const { query, language, sortBy, languages, sorted } = useLeaderboard(payload.value.items, 'total')
// Prefer watch/computed so items stay reactive when data arrives — use computed items:
const items = computed(() => payload.value.items)
// refactor useLeaderboard usage: pass items computed or keep pattern consistent across pages
</script>
```

Implementer: if `useLeaderboard` expects a plain array, call it inside `computed` pattern or change composable to accept `Ref`/`ComputedRef` — smallest change: 

```ts
const items = computed(() => data.value?.items ?? [])
const board = computed(() => useLeaderboard(items.value, 'total'))
```

Better: update `useLeaderboard` to take `MaybeRefOrGetter<LeaderboardItem[]>` only if needed; otherwise pass `items.value` after await (SSR await resolves before setup continues — current `await useFetch` is enough):

```ts
const { data } = await useFetch<LeaderboardPayload>('/api/leaderboards/total')
const payload = data.value ?? { type: 'total', generated_at: '', items: [] }
const { query, language, sortBy, languages, sorted } = useLeaderboard(payload.items, 'total')
```

Show error state if `error` is set.

- [ ] **Step 2: Ensure `nuxt build` produces `.output/server`**

Run: `cd frontend && npm run build`  
Expected: server entry exists

- [ ] **Step 3: Commit**

```bash
git add frontend/app/pages frontend/package.json frontend/app/data
git commit -m "feat(frontend): load leaderboards from Nitro API"
```

---

### Task 7: Actions workflows + deploy scripts

**Files:**
- Modify: `.github/workflows/sync.yml`
- Modify: `.github/workflows/backfill.yml`
- Modify: `deploy/deploy.sh`
- Modify: `deploy/nginx.conf.example`

**Interfaces:**
- Consumes: secrets `DATABASE_URL`, `GH_TOKEN`, `XFYUN_*`, `DEPLOY_*`, `SSH_PRIVATE_KEY`, `NOTIFY_WEBHOOK`
- Produces: DB updated + Nuxt process bundle on server

- [ ] **Step 1: Rewrite sync.yml core steps**

Order:

1. checkout, setup Python, pip install  
2. `python scripts/main.py migrate` with `DATABASE_URL`  
3. `python scripts/main.py sync` with tokens + `DATABASE_URL`  
4. setup Node, `npm ci`, `npm run build` in frontend with `DATABASE_URL` **not required at build** (runtime only on server)  
5. SSH deploy via `bash deploy/deploy.sh`  
6. failure webhook  
7. **Remove** data git commit and Pages actions  

- [ ] **Step 2: Rewrite backfill.yml**

migrate → backfill with `DATABASE_URL`; remove data commit.

- [ ] **Step 3: Update `deploy/deploy.sh`**

Rsync `frontend/.output/` (full Nitro output, not only `public/`) to `DEPLOY_PATH`; remote `systemctl restart github-ranking` or `pm2 restart github-ranking` (document the unit name in DEPLOY.md; script may accept `DEPLOY_RESTART_CMD`).

- [ ] **Step 4: nginx example**

Proxy `pass` to `127.0.0.1:3000` (or chosen port); remove pure-static root assumption.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/sync.yml .github/workflows/backfill.yml deploy
git commit -m "ci: write Postgres and SSH-deploy Nuxt SSR"
```

---

### Task 8: Docs, cleanup `data/`, README

**Files:**
- Modify: `docs/DEPLOY.md`, `docs/OPERATIONS.md`, `docs/ACCEPTANCE.md`, `README.md`
- Modify: `.gitignore` if needed
- Delete/untrack: `data/**` pipeline artifacts (keep folder out of git)

- [ ] **Step 1: Rewrite DEPLOY.md**

Must include: network prerequisites for Actions→Postgres; secrets list; systemd/pm2 unit example; nginx; first migrate+sync; empty yearly expected.

- [ ] **Step 2: OPERATIONS.md** — sync/backfill on DB; no data commit recovery

- [ ] **Step 3: README directory structure + local commands**

```bash
export DATABASE_URL=postgresql://...
python scripts/main.py migrate
python scripts/main.py sync
cd frontend && DATABASE_URL=... npm run dev
```

- [ ] **Step 4: Remove tracked `data/` artifacts from git** (after confirming empty-DB policy); add `data/` to `.gitignore` except maybe `.gitkeep` if desired

- [ ] **Step 5: Commit**

```bash
git add docs README.md .gitignore data
git commit -m "docs: Postgres + Nitro deploy path; drop file-backed data"
```

---

### Task 9: End-to-end verification checklist

**Files:** none (manual / Actions)

- [ ] **Step 1: Connectivity** — from an Actions `workflow_dispatch` debug step or local: `psycopg.connect(DATABASE_URL)` succeeds

- [ ] **Step 2: migrate + sync** against empty DB — five `leaderboards` rows exist; `snapshots` count > 0

- [ ] **Step 3: curl** `https://<host>/api/health` and `/api/leaderboards/total`

- [ ] **Step 4: Open UI** — five tabs render; empty growth boards OK on day 1

- [ ] **Step 5: Confirm** no `data/` commit in Actions logs; Pages deploy absent

---

## Spec coverage self-review

| Spec requirement | Task |
|---|---|
| SQL migrations source of truth | Task 1 |
| Tables + FKs + retention prune | Tasks 1–2, 4 |
| Watch set Top500 ∪ newcomers ∪ previous | Task 3 |
| Total Top100 / growth rules | Task 4 |
| Rebuild boards after summaries | Task 4 step 2 |
| Cold start behavior | Tasks 3–4, 8 docs |
| backfill G3 to snapshots | Task 4 |
| Remove stage / data commits | Tasks 4, 7, 8 |
| Nitro API + health | Task 5 |
| Pages useFetch + SSR | Task 6 |
| Actions migrate/sync/deploy SSH | Task 7 |
| Network/docs/secrets | Tasks 7–8 |
| No data migration | Task 8 |
| Acceptance path | Task 9 |

## Placeholder scan

No TBD/TODO left in task steps; dual-path migrate (CLI + sync internal call) allowed for safety.

## Type consistency

- Board types: `total|daily|weekly|monthly|yearly` everywhere  
- History row: `{date: str, stars: int, forks: int}`  
- `LeaderboardPayload` unchanged in `frontend/app/types/leaderboard.ts`
