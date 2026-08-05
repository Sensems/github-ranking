# On-demand Summary + Card Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh card fields (open issues, last commit, etc.), stop sync-time AI summaries, and generate/persist summaries only via a Nitro button API.

**Architecture:** Pipeline sync stores `open_issues`/`pushed_at` and builds leaderboard items with `has_summary` (no embedded summary JSON). Nuxt `RepoCard` shows description + a button; `POST/GET /api/repos/:repo_id/summary` loads or generates via 讯飞 and writes `summaries`. Do not run a local sync during implementation—wait for next Actions run for field backfill; UI tolerates missing fields.

**Tech Stack:** Python/psycopg pipeline, Nuxt 3 Nitro + `pg`, OpenAI-compatible 讯飞 client (`openai` package already in pipeline; Nitro uses `fetch` or lightweight OpenAI SDK—prefer native `fetch` to avoid new frontend deps).

## Global Constraints

- Do **not** run `python scripts/main.py sync` or other GitHub backfills during this work; wait for tomorrow’s Actions.
- UI must show `—` when `open_issues` / `pushed_at` are missing on old leaderboard JSON.
- Never expose `XFYUN_*` or `DATABASE_URL` to the client bundle.
- Keep cards (not tables). Total board: no growth row. Growth boards: one matching window only.
- Sync must succeed without `XFYUN_*`.
- Commit only when the user explicitly asks (skip commit steps unless instructed).

## File map

| Path | Responsibility |
|------|----------------|
| `db/migrations/002_repo_open_issues_pushed_at.sql` | Add columns |
| `scripts/pool.py` | Map GitHub fields into repo records |
| `scripts/db.py` | Persist/load new columns |
| `scripts/growth.py` | Board items: new fields + `has_summary`, no `summary` body |
| `scripts/main.py` | Strip README/AI sync steps; single board build |
| `tests/test_pool.py`, `tests/test_growth.py`, `tests/test_main.py` | Pipeline tests |
| `frontend/nuxt.config.ts` | Runtime XFYUN config |
| `frontend/app/types/leaderboard.ts` | Item shape |
| `frontend/app/server/utils/summary.ts` | Parse + call 讯飞 |
| `frontend/app/server/api/repos/[repoId]/summary.get.ts` | Return cached summary |
| `frontend/app/server/api/repos/[repoId]/summary.post.ts` | Generate or return cache |
| `frontend/app/components/RepoCard.vue` (+ spec) | New fields + button UX |
| `docs/DEPLOY.md` / `docs/OPERATIONS.md` | XFYUN moves to Nuxt runtime; optional on Actions |

---

### Task 1: Migration + pool/db mapping for open_issues / pushed_at

**Files:**
- Create: `db/migrations/002_repo_open_issues_pushed_at.sql`
- Modify: `scripts/pool.py` (`to_repo_record`)
- Modify: `scripts/db.py` (`upsert_repo`, `load_repos`)
- Test: `tests/test_pool.py`

**Interfaces:**
- Consumes: GitHub raw repo dict with `open_issues_count`, `pushed_at`
- Produces: repo records with `open_issues: int`, `pushed_at: str | None` (ISO)

- [ ] **Step 1: Write failing test for field mapping**

```python
def test_to_repo_record_maps_open_issues_and_pushed_at():
    raw = raw_repo(1, "a/b", 100)
    raw["open_issues_count"] = 12
    raw["pushed_at"] = "2026-07-14T19:25:58Z"
    rec = pool.to_repo_record(raw)
    assert rec["open_issues"] == 12
    assert rec["pushed_at"] == "2026-07-14T19:25:58Z"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `pytest tests/test_pool.py::test_to_repo_record_maps_open_issues_and_pushed_at -v`

- [ ] **Step 3: Add migration + implement mapping + db upsert/load**

Migration file:

```sql
ALTER TABLE repos ADD COLUMN IF NOT EXISTS open_issues INT NOT NULL DEFAULT 0;
ALTER TABLE repos ADD COLUMN IF NOT EXISTS pushed_at TIMESTAMPTZ;
```

In `to_repo_record` add:

```python
"open_issues": int(raw.get("open_issues_count") or 0),
"pushed_at": raw.get("pushed_at"),
```

Extend `upsert_repo` INSERT/UPDATE columns `open_issues`, `pushed_at` from `repo.get("open_issues", 0)` and `repo.get("pushed_at")`. Extend `load_repos` SELECT and dict keys similarly (`pushed_at` via `_iso`).

- [ ] **Step 4: Run pool tests**

Run: `pytest tests/test_pool.py -q`  
Expected: PASS

---

### Task 2: Board items — has_summary, open_issues, pushed_at; drop embedded summary

**Files:**
- Modify: `scripts/growth.py` (`board_item`)
- Test: `tests/test_growth.py`

**Interfaces:**
- Consumes: `load_summary(repo_id) -> dict | None` (truthy ⇒ has cache)
- Produces: board item keys: `open_issues`, `pushed_at`, `has_summary: bool`; **no** `summary` key

- [ ] **Step 1: Write failing test**

```python
def test_board_item_exposes_meta_not_summary_body():
    repo = {
        "repo_id": 1, "repo_name": "a/b", "description": "d", "language": "Go",
        "stars": 10, "forks": 2, "html_url": "https://github.com/a/b",
        "created_at": "2020-01-01T00:00:00Z",
        "open_issues": 3, "pushed_at": "2026-07-14T19:25:58Z",
    }
    growth = {"daily": 1, "weekly": 2, "monthly": 3, "yearly": 4}

    def load_summary(rid):
        return {"summary": {"project_positioning": "x"}, "readme_hash": "h"}

    item = growth.board_item(repo, growth, 1, load_summary)
    assert item["open_issues"] == 3
    assert item["pushed_at"] == "2026-07-14T19:25:58Z"
    assert item["has_summary"] is True
    assert "summary" not in item
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/test_growth.py::test_board_item_exposes_meta_not_summary_body -v`

- [ ] **Step 3: Implement `board_item`**

```python
def board_item(repo, growth, rank, load_summary):
    cached = load_summary(repo["repo_id"])
    return {
        "rank": rank,
        "repo_id": repo["repo_id"],
        "repo_name": repo["repo_name"],
        "description": repo["description"],
        "language": repo["language"],
        "stars": repo["stars"],
        "forks": repo["forks"],
        "html_url": repo["html_url"],
        "open_issues": int(repo.get("open_issues") or 0),
        "pushed_at": repo.get("pushed_at"),
        "growth": growth,
        "has_summary": cached is not None,
    }
```

Update any existing growth tests that assert `summary` on items.

- [ ] **Step 4: Run growth tests**

Run: `pytest tests/test_growth.py -q`  
Expected: PASS

---

### Task 3: Slim sync — no README refresh / AI batch

**Files:**
- Modify: `scripts/main.py` (`sync`)
- Modify: `tests/test_main.py`
- Optional keep: `pending_summaries` / `refresh_readmes` as unused helpers **or** delete if tests only cover them for sync — prefer delete dead sync path and remove/adapt tests that require AI during sync

**Interfaces:**
- Produces: `sync()` steps: migrate → watch/snapshots → build_boards once → save_leaderboards → commit (no XFYUN)

- [ ] **Step 1: Adjust failing/outdated sync tests**

Rewrite `test_main` sync integration to assert:
- boards saved
- `summarize_batch` is **not** called even if `XFYUN_API_KEY` set
- no dependency on README refresh for success

Remove or rewrite `test_pending_summaries_*` if those helpers are deleted; if helpers remain for Nitro parity in Python, keep unit tests but ensure sync does not call them.

- [ ] **Step 2: Run sync-related tests — expect FAIL on old expectations**

Run: `pytest tests/test_main.py -q`

- [ ] **Step 3: Implement slim `sync`**

Replace steps 3–6 with:

```python
print("[3/4] compute boards")
boards = build_boards(repos, today, load_history=load_history, load_summary=load_summary)
print("[4/4] save leaderboards")
for name, items in boards.items():
    db.save_leaderboard(conn, name, {"type": name, "generated_at": today.isoformat(), "items": items})
conn.commit()
print("sync done")
```

Delete `refresh_readmes` / `pending_summaries` / `candidate_ids` if unused; update imports (`XFYUN_API_KEY`, `SUMMARY_BATCH_SIZE`, `README_TRUNCATE_CHARS` as needed).

- [ ] **Step 4: Run main + full pytest**

Run: `pytest tests/test_main.py tests/test_growth.py tests/test_pool.py -q`  
Expected: PASS

- [ ] **Step 5: Docs touch**

In `docs/DEPLOY.md` / `docs/OPERATIONS.md`: Actions sync no longer requires `XFYUN_*` for success; Nuxt server needs `XFYUN_*` for on-demand summary. Do not claim local sync was run.

---

### Task 4: Nitro summary utils + GET/POST routes

**Files:**
- Modify: `frontend/nuxt.config.ts` — add private runtimeConfig keys
- Create: `frontend/app/server/utils/summary.ts`
- Create: `frontend/app/server/api/repos/[repoId]/summary.get.ts`
- Create: `frontend/app/server/api/repos/[repoId]/summary.post.ts`
- Test: `frontend/app/server/api/repos/summary.spec.ts` (vitest, mock `getPool` / fetch)

**Interfaces:**
- `parseSummaryContent(content: string): Summary` — same keys as Python
- `generateSummary(readme: string, cfg): Promise<Summary>`
- GET → `{ repo_id, summary }` or 404
- POST → if cache return it; else fetch readme (DB or raw.githubusercontent.com), call model, upsert `summaries` + optionally `readmes`, return `{ repo_id, summary }`

- [ ] **Step 1: Add runtimeConfig**

```ts
runtimeConfig: {
  databaseUrl: process.env.NUXT_DATABASE_URL || process.env.DATABASE_URL || '',
  xfyunApiKey: process.env.NUXT_XFYUN_API_KEY || process.env.XFYUN_API_KEY || '',
  xfyunBaseUrl: process.env.NUXT_XFYUN_BASE_URL || process.env.XFYUN_BASE_URL || 'https://spark-api-open.xf-yun.com/agent/v1/',
  xfyunModel: process.env.NUXT_XFYUN_MODEL || process.env.XFYUN_MODEL || 'spark-x',
  public: { siteUrl: process.env.SITE_URL || 'https://github-trend.example.com' },
},
```

- [ ] **Step 2: Write failing vitest for parseSummaryContent**

```ts
import { describe, it, expect } from 'vitest'
import { parseSummaryContent } from '../../utils/summary'

describe('parseSummaryContent', () => {
  it('parses fenced json', () => {
    const s = parseSummaryContent('```json\n{"project_positioning":"p","core_features":["a"],"use_cases":["u"],"tech_stack":["t"]}\n```')
    expect(s.project_positioning).toBe('p')
  })
})
```

- [ ] **Step 3: Implement `summary.ts` + routes**

`summary.ts` responsibilities:
- `SYSTEM_PROMPT` identical intent to `scripts/summary.py`
- `parseSummaryContent`
- `callXfyunChat(readme, { apiKey, baseUrl, model })` via `fetch(`${baseUrl.replace(/\/?$/, '/')}chat/completions`)` **or** append path carefully to match existing working base URL (`.../agent/v1/` + `chat/completions`)
- DB helpers inline in routes using `getPool()`: select repo, select summary, select/insert readme, upsert summary

GET handler:

```ts
// 404 if no summaries row
```

POST handler:

```ts
// 404 if repo missing
// if summary exists → return
// 503 if !xfyunApiKey
// ensure readme excerpt (DB or fetch raw README.md variants)
// generate → save → return
// 502 on model/parse failure
```

- [ ] **Step 4: Run vitest for summary**

Run: `cd frontend && npm test -- summary`  
Expected: PASS (adjust script/path to match project)

---

### Task 5: Frontend types + RepoCard UX

**Files:**
- Modify: `frontend/app/types/leaderboard.ts`
- Modify: `frontend/app/components/RepoCard.vue`
- Modify: `frontend/app/components/RepoCard.spec.ts`
- Modify: `frontend/app/composables/useLeaderboard.ts` — stop searching `summary` text (use description only)

**Interfaces:**
- `LeaderboardItem`: add optional `open_issues?: number`, `pushed_at?: string | null`, `has_summary?: boolean`; remove required `summary` (client-only state after fetch)

- [ ] **Step 1: Update types**

```ts
export interface LeaderboardItem {
  rank: number
  repo_id: number
  repo_name: string
  description: string
  language: string | null
  stars: number
  forks: number
  html_url: string
  open_issues?: number
  pushed_at?: string | null
  growth: Growth
  has_summary?: boolean
}
```

- [ ] **Step 2: Failing RepoCard tests**

Assert:
- Renders stars/forks/language/open issues/description/last commit placeholders
- Total board: no growth labels
- Daily board: only 「今日」growth
- Does not show `project_positioning` until after mock generate
- Button text 「生成概况」 when `has_summary` false; 「查看概况」 when true

- [ ] **Step 3: Implement RepoCard**

Layout sketch:
- Header: `#rank` + name link + language chip; stars prominent
- Meta row: Forks · Open Issues · Last Commit (`pushed_at` formatted or `—`)
- Growth row: only if `boardType !== 'total'` — single window
- Description row: text + button
- Expanded panel: positioning + features after GET/POST success
- `loading` / `error` local refs

```ts
async function onSummaryClick() {
  if (expanded.value && summary.value) { expanded.value = false; return }
  if (summary.value) { expanded.value = true; return }
  loading.value = true
  try {
    const path = item.has_summary
      ? `/api/repos/${item.repo_id}/summary` // GET
      : `/api/repos/${item.repo_id}/summary` // POST
    summary.value = item.has_summary
      ? await $fetch(path)
      : await $fetch(path, { method: 'POST' })
    expanded.value = true
    hasSummaryLocal.value = true
  } catch (e) { error.value = '概况生成失败，请重试' }
  finally { loading.value = false }
}
```

Use `$fetch` GET vs POST as above; response shape `{ repo_id, summary }`.

- [ ] **Step 4: Run frontend tests**

Run: `cd frontend && npm test`  
Expected: PASS

---

### Task 6: Smoke checklist (no live sync)

**Files:** none required

- [ ] **Step 1: Unit/integration already green**

Run: `pytest -q` and `cd frontend && npm test`

- [ ] **Step 2: Manual UI check (optional if `npm run dev` available)**

- Old leaderboard JSON: open issues / last commit show `—`
- No AI text on load
- Button present; do **not** require successful 讯飞 call in CI
- Confirm no `python scripts/main.py sync` was run

- [ ] **Step 3: Note for operator**

Tomorrow’s Actions: migrate `002` applies, new fields fill, boards rewrite without embedded summaries. Deploy Nuxt with `XFYUN_*` for button.

---

## Spec coverage self-check

| Spec requirement | Task |
|------------------|------|
| Card fields + growth rules | 5 |
| No default AI; button generate/view | 4, 5 |
| Persist to `summaries` | 4 |
| Sync batch AI off | 3 |
| `open_issues` / `pushed_at` columns + sync mapping | 1, 2 |
| Nitro XFYUN env | 4 |
| No local sync / tolerate missing fields | Global + 5 + 6 |
| Docs Actions vs Nuxt XFYUN | 3 |

## Placeholder scan

None intentional. Commit steps omitted unless user requests commits.
