import json

import pytest

import data_files as df


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    yield


def test_append_history_idempotent_for_same_day():
    df.append_history(1, "2026-08-04", 100, 10)
    df.append_history(1, "2026-08-04", 120, 11)
    rows = df.load_history(1)
    assert len(rows) == 1
    assert rows[0] == {"date": "2026-08-04", "stars": 120, "forks": 11}


def test_prune_history_drops_rows_older_than_retention():
    df.append_history(1, "2025-01-01", 10, 1)
    df.append_history(1, "2026-08-04", 100, 10)
    df.prune_history(1, retention_days=30)
    rows = df.load_history(1)
    assert [r["date"] for r in rows] == ["2026-08-04"]


def test_repos_roundtrip_preserves_int_keys():
    df.save_repos({42: {"repo_name": "owner/repo", "stars": 5}})
    repos = df.load_repos()
    assert 42 in repos
    assert repos[42]["repo_name"] == "owner/repo"


def test_readme_and_summary_roundtrip():
    df.save_readme(7, "abc123", "hello world")
    assert df.load_readme(7) == {"hash": "abc123", "excerpt": "hello world"}
    df.save_summary(7, {"project_positioning": "x"}, "abc123")
    assert df.load_summary(7)["summary"]["project_positioning"] == "x"


def test_save_leaderboard_writes_json(tmp_path):
    path = tmp_path / "leaderboards" / "daily.json"
    df.save_leaderboard("daily", {"type": "daily", "items": []})
    assert json.loads(path.read_text(encoding="utf-8"))["type"] == "daily"
