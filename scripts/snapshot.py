"""每日快照写入与滚动裁剪。"""
from __future__ import annotations

from datetime import date

from config import HISTORY_RETENTION_DAYS
from data_files import append_history, load_history, prune_history


def record_snapshot(repo_id: int, stars: int, forks: int, when: str | None = None) -> None:
    append_history(repo_id, when or date.today().isoformat(), stars, forks)


def prune_all(repos: dict[int, dict], retention_days: int = HISTORY_RETENTION_DAYS) -> int:
    removed = 0
    for repo_id in repos:
        before = len(load_history(repo_id))
        prune_history(repo_id, retention_days)
        removed += before - len(load_history(repo_id))
    return removed
