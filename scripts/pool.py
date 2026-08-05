"""候选池维护：Top-N 迭代搜索 + 新晋仓库补充 + G2 watch set。"""
from __future__ import annotations

from datetime import date, timedelta

from config import NEWCOMER_DAYS, NEWCOMER_MIN_STARS, POOL_SIZE, WATCH_TOP_N
from github_client import GitHubClient


def to_repo_record(raw: dict) -> dict:
    return {
        "repo_id": raw["id"],
        "repo_name": raw["full_name"],
        "description": raw.get("description") or "",
        "stars": raw["stargazers_count"],
        "forks": raw["forks_count"],
        "language": raw.get("language"),
        "html_url": raw["html_url"],
        "created_at": raw["created_at"],
    }


def fetch_pool(client: GitHubClient, limit: int = POOL_SIZE) -> dict[int, dict]:
    return {r["id"]: to_repo_record(r) for r in client.top_repos_by_stars(limit)}


def fetch_newcomers(client: GitHubClient) -> dict[int, dict]:
    since = (date.today() - timedelta(days=NEWCOMER_DAYS)).isoformat()
    query = f"stars:>={NEWCOMER_MIN_STARS} created:>={since} sort:stars desc"
    return {r["id"]: to_repo_record(r) for r in client.search(query).get("items", [])}


def merge_pool(existing: dict[int, dict], fresh: dict[int, dict], newcomers: dict[int, dict]) -> dict[int, dict]:
    merged = dict(existing)
    merged.update(fresh)
    merged.update(newcomers)
    return merged


def _preserve_db_fields(repo: dict, existing_row: dict | None) -> dict:
    """Keep DB-only fields when fresh GitHub metadata overwrites a repo."""
    if existing_row is None:
        return repo
    if repo.get("readme_hash") is None:
        repo["readme_hash"] = existing_row.get("readme_hash")
    if repo.get("backfilled_365") is None:
        repo["backfilled_365"] = existing_row.get("backfilled_365")
    return repo


def build_watch_set(
    client: GitHubClient,
    existing: dict[int, dict],
    previous_ids: set[int],
    limit: int = WATCH_TOP_N,
) -> dict[int, dict]:
    """True G2: Top-N ∪ newcomers ∪ previous growth members (with metadata).

    Does not retain historical repos that fell out of those three sources.
    Previous-only members (not in Top-N/newcomers) are refreshed via GitHub
    so snapshot stars are current, not stale DB metadata.
    """
    top = fetch_pool(client, limit)
    newcomers = fetch_newcomers(client)
    previous_only = {rid for rid in previous_ids if rid in existing} - set(top) - set(newcomers)
    g2_ids = set(top) | set(newcomers) | previous_only

    merged: dict[int, dict] = {}
    for rid in g2_ids:
        if rid in newcomers:
            merged[rid] = dict(newcomers[rid])
        elif rid in top:
            merged[rid] = dict(top[rid])
        else:
            # previous-only: refresh live stars/metadata before snapshotting
            merged[rid] = to_repo_record(client.get_repo_by_id(rid))
        _preserve_db_fields(merged[rid], existing.get(rid))
    return merged
