"""管道 CLI：sync（每日全流程）、backfill、migrate。"""
from __future__ import annotations

import argparse
from datetime import date
from typing import Callable

import config
import db
import migrate
from config import (
    GITHUB_TOKEN,
    HISTORY_RETENTION_DAYS,
    README_TRUNCATE_CHARS,
    SUMMARY_BATCH_SIZE,
    WATCH_TOP_N,
    XFYUN_API_KEY,
)

# Re-export for tests that monkeypatch main.DATABASE_URL
DATABASE_URL = config.DATABASE_URL
from github_client import GitHubClient
from growth import build_boards
from pool import build_watch_set


def candidate_ids(boards: dict[str, list[dict]]) -> set[int]:
    ids: set[int] = set()
    for items in boards.values():
        for item in items:
            ids.add(item["repo_id"])
    return ids


def pending_summaries(
    repos: dict[int, dict],
    boards: dict[str, list[dict]],
    conn,
    *,
    load_readme: Callable = db.load_readme,
    load_summary: Callable = db.load_summary,
) -> list[dict]:
    pending: list[dict] = []
    for repo_id in candidate_ids(boards):
        repo = repos[repo_id]
        cached = load_summary(conn, repo_id)
        if cached is not None and cached.get("readme_hash") == repo.get("readme_hash"):
            continue
        readme = load_readme(conn, repo_id)
        if readme is None:
            continue
        pending.append({
            "repo_id": repo_id,
            "readme_excerpt": readme["excerpt"],
            "readme_hash": repo.get("readme_hash"),
        })
    return pending[:SUMMARY_BATCH_SIZE]


def refresh_readmes(
    client: GitHubClient,
    repos: dict[int, dict],
    boards: dict[str, list[dict]],
    conn,
) -> None:
    for repo_id in candidate_ids(boards):
        repo = repos[repo_id]
        content = client.fetch_readme(repo["repo_name"], README_TRUNCATE_CHARS)
        new_hash = client.readme_hash(content)
        if content is not None:
            db.save_readme(conn, repo_id, new_hash, content)
        repo["readme_hash"] = new_hash
        db.upsert_repo(conn, repo)


def sync() -> None:
    if not (DATABASE_URL or config.DATABASE_URL):
        raise SystemExit("DATABASE_URL is required")

    with db.connect() as conn:
        print("[1/6] migrate")
        applied = migrate.migrate_up(conn)
        print(f"      applied migrations: {applied}")

        client = GitHubClient(GITHUB_TOKEN)
        today = date.today()

        print("[2/6] build watch set + snapshots")
        existing = db.load_repos(conn)
        previous = db.load_previous_growth_members(conn)
        repos = build_watch_set(client, existing, previous, WATCH_TOP_N)
        print(f"      watch set size: {len(repos)}")

        for repo in repos.values():
            db.upsert_repo(conn, repo)
            db.upsert_snapshot(
                conn,
                repo["repo_id"],
                today.isoformat(),
                repo["stars"],
                repo["forks"],
            )
        pruned = db.prune_snapshots(conn, HISTORY_RETENTION_DAYS)
        print(f"      snapshots written, pruned rows: {pruned}")

        load_history = lambda rid: db.load_history(conn, rid)
        load_summary = lambda rid: db.load_summary(conn, rid)

        print("[3/6] compute boards (first pass)")
        boards = build_boards(
            repos,
            today,
            load_history=load_history,
            load_summary=load_summary,
        )

        print("[4/6] refresh README for board candidates")
        refresh_readmes(client, repos, boards, conn)

        print("[5/6] generate AI summaries")
        pending = pending_summaries(repos, boards, conn)
        if pending and XFYUN_API_KEY:
            from summary import summarize_batch

            results = summarize_batch(
                pending,
                XFYUN_API_KEY,
                save_summary=lambda rid, s, rh: db.save_summary(conn, rid, s, rh),
            )
            ok = sum(1 for v in results.values() if v is not None)
            print(f"      summarized: {ok} of {len(pending)}")
        else:
            print(
                f"      skipped ({len(pending)} pending; "
                f"XFYUN_API_KEY {'set' if XFYUN_API_KEY else 'not set'})"
            )

        print("[6/6] rebuild boards with summaries + save")
        boards = build_boards(
            repos,
            today,
            load_history=load_history,
            load_summary=load_summary,
        )
        for name, items in boards.items():
            db.save_leaderboard(
                conn,
                name,
                {"type": name, "generated_at": today.isoformat(), "items": items},
            )
        conn.commit()
        print("sync done")


def backfill() -> None:
    if not (DATABASE_URL or config.DATABASE_URL):
        raise SystemExit("DATABASE_URL is required")

    from backfill import backfill_batch

    with db.connect() as conn:
        migrate.migrate_up(conn)
        client = GitHubClient(GITHUB_TOKEN)
        today = date.today()
        existing = db.load_repos(conn)
        previous = db.load_previous_growth_members(conn)
        # Same G2 watch set as sync — fallen-out repos are not backfill candidates.
        repos = build_watch_set(client, existing, previous, WATCH_TOP_N)
        load_history = lambda rid: db.load_history(conn, rid)
        load_summary = lambda rid: db.load_summary(conn, rid)
        boards = build_boards(
            repos,
            today,
            load_history=load_history,
            load_summary=load_summary,
        )
        processed = backfill_batch(
            repos,
            boards,
            client,
            today,
            load_history=load_history,
            upsert_snapshot=lambda rid, when, stars, forks: db.upsert_snapshot(
                conn, rid, when, stars, forks
            ),
        )
        if processed:
            for repo in repos.values():
                if repo.get("backfilled_365"):
                    db.upsert_repo(conn, repo)
        conn.commit()
        print(f"backfill processed: {processed}")


def migrate_cmd() -> None:
    if not config.DATABASE_URL:
        raise SystemExit("DATABASE_URL is not set")

    with db.connect() as conn:
        applied = migrate.migrate_up(conn)
    print(f"Applied {applied} migration(s)")


def main() -> None:
    parser = argparse.ArgumentParser(description="GitHub Star Trend pipeline")
    parser.add_argument("command", choices=["sync", "backfill", "migrate"])
    args = parser.parse_args()
    if args.command == "sync":
        sync()
    elif args.command == "backfill":
        backfill()
    elif args.command == "migrate":
        migrate_cmd()


if __name__ == "__main__":
    main()
