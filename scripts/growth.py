"""增速计算与 5 个榜单生成。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, Optional

from config import LEADERBOARD_SIZE, PARTICIPATION_MIN_STARS, TOLERANCE_DAYS, TOTAL_BOARD_SIZE, WINDOWS


def parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def nearest_snapshot(history: list[dict], target: date) -> Optional[dict]:
    best: Optional[dict] = None
    best_delta: Optional[int] = None
    for row in history:
        delta = abs(parse_date(row["date"]) - target).days
        if delta <= TOLERANCE_DAYS and (best_delta is None or delta < best_delta):
            best = row
            best_delta = delta
    return best


def compute_growth(stars: int, history: list[dict], today: date) -> dict[str, Optional[int]]:
    growth: dict[str, Optional[int]] = {}
    for name, days in WINDOWS.items():
        target = today - timedelta(days=days)
        row = nearest_snapshot(history, target)
        growth[name] = None if row is None else stars - row["stars"]
    return growth


def eligible(repo: dict, window_days: int, today: date) -> bool:
    if repo["stars"] < PARTICIPATION_MIN_STARS:
        return False
    age = (today - parse_date(repo["created_at"])).days
    return age >= window_days


def board_item(repo: dict, growth: dict, rank: int, load_summary: Callable[[int], Optional[dict]]) -> dict:
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


def build_boards(
    repos: dict[int, dict],
    today: date,
    *,
    load_history: Callable[[int], list[dict]],
    load_summary: Callable[[int], Optional[dict]],
    total_size: int = TOTAL_BOARD_SIZE,
    board_size: int = LEADERBOARD_SIZE,
) -> dict[str, list[dict]]:
    boards: dict[str, list[dict]] = {name: [] for name in ["total", *WINDOWS.keys()]}
    for repo in repos.values():
        hist = load_history(repo["repo_id"])
        g = compute_growth(repo["stars"], hist, today)
        boards["total"].append(board_item(repo, g, 0, load_summary))
        for name, days in WINDOWS.items():
            if g[name] is not None and eligible(repo, days, today):
                boards[name].append(board_item(repo, g, 0, load_summary))
    for name in boards:
        if name == "total":
            boards[name].sort(key=lambda it: it["stars"], reverse=True)
            boards[name] = boards[name][:total_size]
        else:
            boards[name].sort(key=lambda it: it["growth"][name], reverse=True)
            boards[name] = boards[name][:board_size]
        for i, item in enumerate(boards[name], start=1):
            item["rank"] = i
    return boards
