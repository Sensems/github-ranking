# On-demand AI Summary + Card Field Refresh

Date: 2026-08-05  
Status: approved (pending implementation)

## Goal

Keep the existing card layout, but:

1. Show screenshot-aligned repo fields (stars, forks, language, open issues, description, last commit).
2. Stop embedding / auto-showing AI summaries on the page.
3. Generate AI summaries only when the user clicks a button next to the description; persist to Postgres.
4. Turn off daily sync batch AI summarization.

## Decisions (locked)

| Topic | Choice |
|-------|--------|
| Layout | Keep cards (not table) |
| Growth display | Total board: no growth row. Growth boards: show only that board’s window growth |
| Sync AI batch | Off — summaries only via button |
| Open Issues / Last Commit | Sync from GitHub into DB (`open_issues`, `pushed_at`) and display |
| Summary runtime | Nitro API calling 讯飞 (same `XFYUN_*` env as pipeline) |
| Data refresh now | **Do not** run local sync to backfill new fields; wait for next day’s Actions sync |

## Card UI

### Always shown

- Rank, project name (link), Stars, Forks, Language, Open Issues, Description, Last Commit (`pushed_at`)

### Growth

- **Total**: omit growth row
- **Daily / weekly / monthly / yearly**: show only the matching window (今日 / 本周 / 本月 / 今年)

### Summary interaction

- Default: show GitHub `description` only; **do not** render AI summary blocks.
- Button beside description:
  - No cached summary → label「生成概况」
  - Cached summary → label「查看概况」(or toggle expand/collapse)
- Click「生成概况」:
  1. Button enters loading state
  2. `POST /api/repos/:repo_id/summary`
  3. On success: expand summary inline; keep in component state
  4. On failure: show error; allow retry
- If cache exists and user clicks「查看概况」, load/show without regenerating (unless a future「刷新」is added — out of scope).

## Data model

Migration `db/migrations/002_repo_open_issues_pushed_at.sql` (idempotent):

```sql
ALTER TABLE repos ADD COLUMN IF NOT EXISTS open_issues INT NOT NULL DEFAULT 0;
ALTER TABLE repos ADD COLUMN IF NOT EXISTS pushed_at TIMESTAMPTZ;
```

Pipeline mapping from GitHub API:

- `open_issues` ← `open_issues_count` (search/repo payloads)
- `pushed_at` ← `pushed_at`

`board_item` includes `open_issues` and `pushed_at` (ISO string or null). Leaderboard JSON **does not** embed full `summary`; may include `has_summary: boolean` for button label.

Frontend `LeaderboardItem` gains `open_issues`, `pushed_at`, `has_summary`; drops required inline `summary` (or keeps optional for post-click client state only).

## Sync pipeline changes

Remove from `scripts/main.py` sync:

- Batch `pending_summaries` / `summarize_batch`
- README refresh done solely for board AI candidates (`refresh_readmes` as currently wired for summaries)

Sync continues: migrate → watch set → snapshots → build boards → save leaderboards (no AI step).

README fetch moves to on-demand path when generating a summary (if `readmes` row missing or hash stale — v1: fetch if missing).

## Nitro API

### `POST /api/repos/:repo_id/summary`

Server-only. Steps:

1. Validate `repo_id` exists in `repos`.
2. If `summaries` row exists for repo → return cached summary (idempotent GET-like behavior on POST is OK for v1; optional query `?force=1` out of scope).
3. Else load README excerpt from `readmes`, or fetch from raw.githubusercontent.com and upsert `readmes`.
4. Call 讯飞 OpenAI-compatible chat (env: `XFYUN_API_KEY`, `XFYUN_BASE_URL`, `XFYUN_MODEL`) with the same JSON schema as `scripts/summary.py`.
5. Upsert `summaries` (`repo_id`, `readme_hash`, `summary`, `generated_at`).
6. Return `{ repo_id, summary }`.

Errors: 404 unknown repo; 503 missing AI config; 502 upstream/parse failure; 500 DB.

Runtime config / env on Nuxt server (never client-bundled):

- `NUXT_XFYUN_API_KEY` / `XFYUN_API_KEY`
- `NUXT_XFYUN_BASE_URL` / `XFYUN_BASE_URL`
- `NUXT_XFYUN_MODEL` / `XFYUN_MODEL`

Also document that Actions no longer needs XFYUN for sync success (optional secret). Deployed Nuxt process **does** need XFYUN for the button to work.

### Leaderboard read path

`GET /api/leaderboards/:type` unchanged shape except items omit `summary` and may add `has_summary`, `open_issues`, `pushed_at`. Until Actions runs tomorrow, old leaderboard JSON may lack new fields — UI must tolerate missing `open_issues` / `pushed_at` (show `—`).

## Out of scope

- Table layout / screenshot pixel clone
- Force-regenerate summary
- Running local sync or backfill before Actions
- Migrating historical AI text out of existing leaderboard JSON (next sync overwrites boards)

## Acceptance

1. Cards show new fields; total has no growth row; growth boards show one window.
2. No AI text until user action.
3. Button generates (or shows cached) summary and persists to `summaries`.
4. Sync without `XFYUN_*` still completes boards.
5. After next Actions sync: `open_issues` / `pushed_at` populated for watch-set repos.
