"""管道 CLI：sync（每日全流程）、backfill、migrate。"""
from __future__ import annotations

import argparse
from datetime import date

import config
import db
import migrate
from config import (
    GITHUB_TOKEN,
    HISTORY_RETENTION_DAYS,
    WATCH_TOP_N,
)

# Re-export for tests that monkeypatch main.DATABASE_URL
DATABASE_URL = config.DATABASE_URL
from github_client import GitHubClient
from growth import build_boards
from pool import build_watch_set


def sync() -> None:
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL is required")

    with db.connect() as conn:
        print("[1/4] migrate")
        applied = migrate.migrate_up(conn)
        print(f"      applied migrations: {applied}")

        client = GitHubClient(GITHUB_TOKEN)
        today = date.today()

        print("[2/4] build watch set + snapshots")
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

        print("[3/4] compute boards")
        boards = build_boards(repos, today, load_history=load_history, load_summary=load_summary)
        print("[4/4] save leaderboards")
        for name, items in boards.items():
            db.save_leaderboard(conn, name, {"type": name, "generated_at": today.isoformat(), "items": items})
        conn.commit()
        print("sync done")


def backfill() -> None:
    if not DATABASE_URL:
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
    if not DATABASE_URL:
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
