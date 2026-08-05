from unittest.mock import MagicMock

import pytest

import config
import main
import migrate


def _mock_conn(*, applied_versions: list[tuple[str]] | None = None):
    """Build a connection mock with a shared cursor for migrate_up."""
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = applied_versions if applied_versions is not None else []
    return conn, cur


def _execute_sql_calls(cur) -> list[str]:
    return [args[0] for args, _ in cur.execute.call_args_list]


def test_migrate_up_applies_pending_and_records():
    conn, cur = _mock_conn(applied_versions=[])

    applied = migrate.migrate_up(conn, migrations_dir=migrate.DEFAULT_MIGRATIONS_DIR)

    assert applied == 1
    sql_calls = _execute_sql_calls(cur)
    assert any("CREATE TABLE IF NOT EXISTS repos" in sql for sql in sql_calls)
    insert_calls = [
        call for call in cur.execute.call_args_list
        if call.args[0].startswith("INSERT INTO schema_migrations")
    ]
    assert len(insert_calls) == 1
    assert insert_calls[0].args[1] == ("001_init",)
    assert conn.commit.call_count == 2  # schema table bootstrap + one migration


def test_migrate_up_skips_already_applied():
    conn, cur = _mock_conn(applied_versions=[("001_init",)])

    applied = migrate.migrate_up(conn, migrations_dir=migrate.DEFAULT_MIGRATIONS_DIR)

    assert applied == 0
    sql_calls = _execute_sql_calls(cur)
    assert not any("CREATE TABLE IF NOT EXISTS repos" in sql for sql in sql_calls)
    assert not any(sql.startswith("INSERT INTO schema_migrations") for sql in sql_calls)
    assert conn.commit.call_count == 1  # bootstrap only, no migration commit


def test_migrate_cmd_connects_and_applies(monkeypatch, capsys):
    import db

    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://test/db")

    mock_conn = MagicMock()
    cm = MagicMock()
    cm.__enter__.return_value = mock_conn
    cm.__exit__.return_value = False
    monkeypatch.setattr(db, "connect", lambda: cm)

    mock_migrate_up = MagicMock(return_value=1)
    monkeypatch.setattr(migrate, "migrate_up", mock_migrate_up)

    main.migrate_cmd()

    mock_migrate_up.assert_called_once_with(mock_conn)
    assert capsys.readouterr().out.strip() == "Applied 1 migration(s)"


def test_migrate_cmd_exits_without_database_url(monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", "")

    with pytest.raises(SystemExit, match="DATABASE_URL is not set"):
        main.migrate_cmd()
