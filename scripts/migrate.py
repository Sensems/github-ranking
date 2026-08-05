"""Apply SQL migrations from db/migrations/."""
from __future__ import annotations

from pathlib import Path

from config import REPO_ROOT

DEFAULT_MIGRATIONS_DIR = REPO_ROOT / "db" / "migrations"

_SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  version TEXT PRIMARY KEY,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
"""


def _ensure_schema_migrations_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(_SCHEMA_MIGRATIONS_DDL)


def _applied_versions(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def migrate_up(conn, migrations_dir: Path = DEFAULT_MIGRATIONS_DIR) -> int:
    """Apply pending *.sql files in sorted order; return count of newly applied."""
    _ensure_schema_migrations_table(conn)
    conn.commit()

    applied = _applied_versions(conn)
    count = 0

    for path in sorted(Path(migrations_dir).glob("*.sql")):
        version = path.stem
        if version in applied:
            continue

        sql = path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,),
            )
        conn.commit()
        count += 1

    return count
