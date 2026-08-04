"""候选池维护：Top-N 迭代搜索 + 新晋仓库补充 + 合并。"""
from __future__ import annotations

from datetime import date, timedelta

from config import NEWCOMER_DAYS, NEWCOMER_MIN_STARS, POOL_SIZE
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
