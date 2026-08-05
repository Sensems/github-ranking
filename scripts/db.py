"""PostgreSQL persistence helpers for the github-ranking pipeline."""
from __future__ import annotations

import json
from datetime import date
from typing import TYPE_CHECKING

from config import DATABASE_URL, HISTORY_RETENTION_DAYS

if TYPE_CHECKING:
    import psycopg

GROWTH_BOARD_TYPES = ("daily", "weekly", "monthly", "yearly")


def connect() -> "psycopg.Connection":
    import psycopg

    return psycopg.connect(DATABASE_URL)


def _iso(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def upsert_repo(conn, repo: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO repos (
                repo_id, repo_name, description, stars, forks, language,
                html_url, created_at, readme_hash, backfilled_365, updated_at
            ) VALUES (
                %(repo_id)s, %(repo_name)s, %(description)s, %(stars)s, %(forks)s,
                %(language)s, %(html_url)s, %(created_at)s, %(readme_hash)s,
                %(backfilled_365)s, %(updated_at)s
            )
            ON CONFLICT (repo_id) DO UPDATE SET
                repo_name = EXCLUDED.repo_name,
                description = EXCLUDED.description,
                stars = EXCLUDED.stars,
                forks = EXCLUDED.forks,
                language = EXCLUDED.language,
                html_url = EXCLUDED.html_url,
                created_at = EXCLUDED.created_at,
                readme_hash = EXCLUDED.readme_hash,
                backfilled_365 = EXCLUDED.backfilled_365,
                updated_at = EXCLUDED.updated_at
            """,
            {
                "repo_id": repo["repo_id"],
                "repo_name": repo["repo_name"],
                "description": repo.get("description", ""),
                "stars": repo["stars"],
                "forks": repo["forks"],
                "language": repo.get("language"),
                "html_url": repo["html_url"],
                "created_at": repo["created_at"],
                "readme_hash": repo.get("readme_hash"),
                "backfilled_365": repo.get("backfilled_365"),
                "updated_at": date.today(),
            },
        )


def load_repos(conn) -> dict[int, dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT repo_id, repo_name, description, stars, forks, language,
                   html_url, created_at, readme_hash, backfilled_365, updated_at
            FROM repos
            """
        )
        repos: dict[int, dict] = {}
        for row in cur.fetchall():
            repo_id = row[0]
            repos[repo_id] = {
                "repo_id": repo_id,
                "repo_name": row[1],
                "description": row[2],
                "stars": row[3],
                "forks": row[4],
                "language": row[5],
                "html_url": row[6],
                "created_at": _iso(row[7]),
                "readme_hash": row[8],
                "backfilled_365": _iso(row[9]),
                "updated_at": _iso(row[10]),
            }
        return repos


def upsert_snapshot(conn, repo_id: int, when: str, stars: int, forks: int) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO snapshots (repo_id, date, stars, forks)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (repo_id, date) DO UPDATE SET
                stars = EXCLUDED.stars,
                forks = EXCLUDED.forks
            """,
            (repo_id, when, stars, forks),
        )


def load_history(conn, repo_id: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT date, stars, forks
            FROM snapshots
            WHERE repo_id = %s
            ORDER BY date
            """,
            (repo_id,),
        )
        return [
            {"date": _iso(row[0]), "stars": row[1], "forks": row[2]}
            for row in cur.fetchall()
        ]


def prune_snapshots(conn, retention_days: int = HISTORY_RETENTION_DAYS) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM snapshots WHERE date < CURRENT_DATE - %s::integer",
            (retention_days,),
        )
        return cur.rowcount


def save_readme(conn, repo_id: int, hash_value: str, excerpt: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO readmes (repo_id, hash, excerpt)
            VALUES (%s, %s, %s)
            ON CONFLICT (repo_id) DO UPDATE SET
                hash = EXCLUDED.hash,
                excerpt = EXCLUDED.excerpt
            """,
            (repo_id, hash_value, excerpt),
        )


def load_readme(conn, repo_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT hash, excerpt FROM readmes WHERE repo_id = %s",
            (repo_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {"hash": row[0], "excerpt": row[1]}


def save_summary(
    conn,
    repo_id: int,
    summary: dict,
    readme_hash: str | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO summaries (repo_id, readme_hash, summary, generated_at)
            VALUES (%s, %s, %s::jsonb, %s)
            ON CONFLICT (repo_id) DO UPDATE SET
                readme_hash = EXCLUDED.readme_hash,
                summary = EXCLUDED.summary,
                generated_at = EXCLUDED.generated_at
            """,
            (repo_id, readme_hash, json.dumps(summary), date.today()),
        )


def load_summary(conn, repo_id: int) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT readme_hash, summary, generated_at
            FROM summaries
            WHERE repo_id = %s
            """,
            (repo_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "readme_hash": row[0],
            "summary": row[1],
            "generated_at": _iso(row[2]),
        }


def save_leaderboard(conn, name: str, payload: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO leaderboards (type, generated_at, items)
            VALUES (%s, %s, %s::jsonb)
            ON CONFLICT (type) DO UPDATE SET
                generated_at = EXCLUDED.generated_at,
                items = EXCLUDED.items
            """,
            (
                name,
                payload.get("generated_at"),
                json.dumps(payload.get("items", [])),
            ),
        )


def load_leaderboard(conn, name: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT generated_at, items FROM leaderboards WHERE type = %s",
            (name,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "type": name,
            "generated_at": _iso(row[0]),
            "items": row[1],
        }


def load_previous_growth_members(conn) -> set[int]:
    ids: set[int] = set()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT type, items
            FROM leaderboards
            WHERE type = ANY(%s)
            """,
            (list(GROWTH_BOARD_TYPES),),
        )
        for _board_type, items in cur.fetchall():
            for item in items or []:
                ids.add(int(item["repo_id"]))
    return ids
