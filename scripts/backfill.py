"""365 天历史回溯：对进入榜单 Top 100 的仓库补算一年前 star 数。"""
from __future__ import annotations

from datetime import date, timedelta

from config import BACKFILL_BATCH_SIZE
from data_files import append_history, load_history
from github_client import GitHubClient
from growth import nearest_snapshot


def has_365_anchor(history: list[dict], today: date) -> bool:
    target = today - timedelta(days=365)
    return nearest_snapshot(history, target) is not None


def backfill_batch(
    repos: dict[int, dict],
    boards: dict[str, list[dict]],
    client: GitHubClient,
    today: date,
) -> int:
    candidates = sorted({item["repo_id"] for items in boards.values() for item in items})
    processed = 0
    for repo_id in candidates:
        if processed >= BACKFILL_BATCH_SIZE:
            break
        repo = repos[repo_id]
        if has_365_anchor(load_history(repo_id), today):
            continue
        before = (today - timedelta(days=365)).isoformat()
        stars_365 = client.stargazer_count_at(repo["repo_name"], before)
        append_history(repo_id, before, stars_365, 0)
        repo["backfilled_365"] = before
        processed += 1
    return processed
