import os
from datetime import date
from unittest.mock import MagicMock

import pytest

import db

integration = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)


def _mock_conn(*, fetchall=None, fetchone=None, rowcount=0):
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = fetchall if fetchall is not None else []
    cur.fetchone.return_value = fetchone
    cur.rowcount = rowcount
    return conn, cur


def _execute_sql_calls(cur) -> list[str]:
    return [args[0] for args, _ in cur.execute.call_args_list]


def test_upsert_snapshot_sql_uses_on_conflict():
    conn, cur = _mock_conn()

    db.upsert_snapshot(conn, 1, "2026-08-05", 10, 1)

    sql_calls = _execute_sql_calls(cur)
    assert len(sql_calls) == 1
    assert "ON CONFLICT" in sql_calls[0]
    assert "(repo_id, date)" in sql_calls[0]
    assert "EXCLUDED.stars" in sql_calls[0]
    assert "EXCLUDED.forks" in sql_calls[0]


def test_upsert_repo_preserves_null_readme_and_backfill_fields():
    conn, cur = _mock_conn()

    db.upsert_repo(conn, {
        "repo_id": 1, "repo_name": "o/r", "description": "", "stars": 10, "forks": 1,
        "language": "Python", "html_url": "https://github.com/o/r",
        "created_at": "2020-01-01T00:00:00Z",
    })

    sql = _execute_sql_calls(cur)[0]
    assert "COALESCE(EXCLUDED.readme_hash, repos.readme_hash)" in sql
    assert "COALESCE(EXCLUDED.backfilled_365, repos.backfilled_365)" in sql


@integration
def test_snapshot_upsert_idempotent():
    with db.connect() as conn:
        db.upsert_repo(conn, {
            "repo_id": 1, "repo_name": "o/r", "description": "", "stars": 10, "forks": 1,
            "language": "Python", "html_url": "https://github.com/o/r",
            "created_at": "2020-01-01T00:00:00Z",
        })
        db.upsert_snapshot(conn, 1, "2026-08-05", 10, 1)
        db.upsert_snapshot(conn, 1, "2026-08-05", 12, 2)
        hist = db.load_history(conn, 1)
        assert hist[-1] == {"date": "2026-08-05", "stars": 12, "forks": 2}
        conn.rollback()


def test_load_previous_growth_members_collects_repo_ids():
    conn, cur = _mock_conn(fetchall=[
        ("daily", [{"repo_id": 1}, {"repo_id": 2}]),
        ("weekly", [{"repo_id": 2}, {"repo_id": 3}]),
        ("monthly", [{"repo_id": 4}]),
        ("yearly", [{"repo_id": 5}]),
    ])

    members = db.load_previous_growth_members(conn)

    assert members == {1, 2, 3, 4, 5}
    sql_calls = _execute_sql_calls(cur)
    assert len(sql_calls) == 1
    assert "daily" in sql_calls[0] or "%s" in sql_calls[0]


def test_load_previous_growth_members_ignores_total_board():
    conn, cur = _mock_conn(fetchall=[
        ("daily", [{"repo_id": 10}]),
    ])

    members = db.load_previous_growth_members(conn)

    assert members == {10}
    params = cur.execute.call_args.args[1]
    growth_types = set(params[0]) if params else set()
    assert "total" not in growth_types


def test_save_leaderboard_replaces_by_type():
    conn, cur = _mock_conn()
    payload = {"type": "daily", "generated_at": "2026-08-05", "items": []}

    db.save_leaderboard(conn, "daily", payload)

    sql_calls = _execute_sql_calls(cur)
    assert len(sql_calls) == 1
    assert "ON CONFLICT" in sql_calls[0]
    assert "type" in sql_calls[0]


def test_prune_snapshots_returns_deleted_count():
    conn, cur = _mock_conn(rowcount=7)

    deleted = db.prune_snapshots(conn, 400)

    assert deleted == 7
    sql_calls = _execute_sql_calls(cur)
    assert "DELETE FROM snapshots" in sql_calls[0]


def test_load_repos_maps_rows_to_dict():
    conn, cur = _mock_conn(fetchall=[
        (
            42, "o/r", "desc", 100, 5, "Go", "https://github.com/o/r",
            "2020-01-01T00:00:00+00:00", "hash1", None, date(2026, 8, 5),
        ),
    ])

    repos = db.load_repos(conn)

    assert 42 in repos
    assert repos[42]["repo_name"] == "o/r"
    assert repos[42]["stars"] == 100


def test_load_readme_returns_none_when_missing():
    conn, cur = _mock_conn(fetchone=None)

    assert db.load_readme(conn, 99) is None


def test_load_summary_returns_none_when_missing():
    conn, cur = _mock_conn(fetchone=None)

    assert db.load_summary(conn, 99) is None
