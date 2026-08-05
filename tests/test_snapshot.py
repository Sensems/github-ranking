"""Snapshot prune lives in db.prune_snapshots (file-backed snapshot.py removed)."""

from unittest.mock import MagicMock

import db


def test_prune_snapshots_deletes_old_rows():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cur.rowcount = 3

    assert db.prune_snapshots(conn, retention_days=30) == 3
    sql = cur.execute.call_args.args[0]
    assert "DELETE FROM snapshots" in sql
