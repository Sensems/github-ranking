"""管道 CLI：sync（每日全流程）、stage（榜单 JSON 进前端）、backfill（Task 21 追加）。"""
from __future__ import annotations

import argparse
import shutil
from datetime import date

from config import (
    DATA_DIR,
    GITHUB_TOKEN,
    POOL_SIZE,
    README_TRUNCATE_CHARS,
    REPO_ROOT,
    SUMMARY_BATCH_SIZE,
    XFYUN_API_KEY,
)
from data_files import (
    append_history,
    load_readme,
    load_repos,
    load_summary,
    save_leaderboard,
    save_readme,
    save_repos,
)
from github_client import GitHubClient
from growth import build_boards
from pool import fetch_newcomers, fetch_pool, merge_pool
from snapshot import prune_all

FRONTEND_DATA_DIR = REPO_ROOT / "frontend" / "app" / "data" / "leaderboards"


def candidate_ids(boards: dict[str, list[dict]]) -> set[int]:
    ids: set[int] = set()
    for items in boards.values():
        for item in items:
            ids.add(item["repo_id"])
    return ids


def pending_summaries(repos: dict[int, dict], boards: dict[str, list[dict]]) -> list[dict]:
    pending: list[dict] = []
    for repo_id in candidate_ids(boards):
        repo = repos[repo_id]
        cached = load_summary(repo_id)
        if cached is not None and cached.get("readme_hash") == repo.get("readme_hash"):
            continue
        readme = load_readme(repo_id)
        if readme is None:
            continue
        pending.append({
            "repo_id": repo_id,
            "readme_excerpt": readme["excerpt"],
            "readme_hash": repo.get("readme_hash"),
        })
    return pending[:SUMMARY_BATCH_SIZE]


def refresh_readmes(client: GitHubClient, repos: dict[int, dict], boards: dict[str, list[dict]]) -> None:
    for repo_id in candidate_ids(boards):
        repo = repos[repo_id]
        content = client.fetch_readme(repo["repo_name"], README_TRUNCATE_CHARS)
        new_hash = client.readme_hash(content)
        if content is not None:
            save_readme(repo_id, new_hash, content)
        repo["readme_hash"] = new_hash


def sync() -> None:
    client = GitHubClient(GITHUB_TOKEN)
    today = date.today()

    print("[1/6] fetch pool")
    repos = merge_pool(load_repos(), fetch_pool(client, POOL_SIZE), fetch_newcomers(client))
    print(f"      pool size: {len(repos)}")

    print("[2/6] write snapshots")
    for repo in repos.values():
        append_history(repo["repo_id"], today.isoformat(), repo["stars"], repo["forks"])
    pruned = prune_all(repos)
    print(f"      snapshots written, pruned rows: {pruned}")

    print("[3/6] compute boards")
    boards = build_boards(repos, today)

    print("[4/6] refresh README for top-100 candidates")
    refresh_readmes(client, repos, boards)
    save_repos(repos)

    print("[5/6] generate AI summaries")
    pending = pending_summaries(repos, boards)
    if pending and XFYUN_API_KEY:
        from summary import summarize_batch
        results = summarize_batch(pending, XFYUN_API_KEY)
        ok = sum(1 for v in results.values() if v is not None)
        print(f"      summarized: {ok} of {len(pending)}")
    else:
        print(f"      skipped ({len(pending)} pending; XFYUN_API_KEY {'set' if XFYUN_API_KEY else 'not set'})")

    print("[6/6] save leaderboards")
    for name, items in build_boards(repos, today).items():
        save_leaderboard(name, {"type": name, "generated_at": today.isoformat(), "items": items})
    print("sync done")


def stage() -> None:
    src = DATA_DIR / "leaderboards"
    dst = FRONTEND_DATA_DIR
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*.json"):
        shutil.copy(f, dst / f.name)
    print(f"staged {len(list(src.glob('*.json')))} leaderboard files to {dst}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Star Trend pipeline")
    parser.add_argument("command", choices=["sync", "stage"])
    args = parser.parse_args()
    if args.command == "sync":
        sync()
    elif args.command == "stage":
        stage()


if __name__ == "__main__":
    main()
