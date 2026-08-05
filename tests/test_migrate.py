from unittest.mock import MagicMock

import migrate


def test_migrate_up_applies_pending_and_records():
    conn = MagicMock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = []
    applied = migrate.migrate_up(conn, migrations_dir=migrate.DEFAULT_MIGRATIONS_DIR)
    assert applied >= 1
    conn.commit.assert_called()
