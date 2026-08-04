from datetime import date

import pytest

import data_files as df
import growth


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    yield


def history(*rows):
    return [{"date": d, "stars": s, "forks": 0} for d, s in rows]


def test_nearest_snapshot_respects_tolerance():
    h = history(("2026-07-28", 100), ("2026-08-01", 120))
    row = growth.nearest_snapshot(h, date(2026, 8, 3))  # 相差 2 天，在容差内
    assert row["stars"] == 120
    assert growth.nearest_snapshot(h, date(2026, 6, 1)) is None


def test_compute_growth_returns_none_without_history():
    g = growth.compute_growth(200, [], date(2026, 8, 4))
    assert g == {"daily": None, "weekly": None, "monthly": None, "yearly": None}


def test_compute_growth_daily_and_weekly():
    h = history(("2026-08-03", 100), ("2026-07-28", 90), ("2026-07-01", 50))
    g = growth.compute_growth(120, h, date(2026, 8, 4))
    assert g["daily"] == 20
    assert g["weekly"] == 30
    assert g["monthly"] is None  # 30 天前无快照


def test_eligible_filters_by_stars_and_age():
    young = {"stars": 2000, "created_at": "2026-07-20T00:00:00Z"}
    low = {"stars": 500, "created_at": "2020-01-01T00:00:00Z"}
    old = {"stars": 2000, "created_at": "2020-01-01T00:00:00Z"}
    today = date(2026, 8, 4)
    assert not growth.eligible(young, 30, today)
    assert not growth.eligible(low, 30, today)
    assert growth.eligible(old, 30, today)


def test_build_boards_sorts_filters_and_ranks():
    df.append_history(1, "2026-08-03", 1990, 5)
    df.append_history(1, "2026-08-04", 2000, 5)
    df.append_history(2, "2026-08-03", 1400, 9)
    df.append_history(2, "2026-08-04", 1500, 9)
    repos = {
        1: {"repo_id": 1, "repo_name": "a/b", "stars": 2000, "forks": 5, "language": "Python",
            "description": "x", "html_url": "https://github.com/a/b", "created_at": "2020-01-01T00:00:00Z"},
        2: {"repo_id": 2, "repo_name": "c/d", "stars": 1500, "forks": 9, "language": "Go",
            "description": "y", "html_url": "https://github.com/c/d", "created_at": "2020-01-01T00:00:00Z"},
    }
    boards = growth.build_boards(repos, date(2026, 8, 4))
    assert [i["repo_name"] for i in boards["daily"]] == ["c/d", "a/b"]
    assert boards["daily"][0]["growth"]["daily"] == 100
    assert boards["daily"][0]["rank"] == 1
    assert [i["repo_name"] for i in boards["total"]] == ["a/b", "c/d"]
    assert len(boards["weekly"]) == 0  # 7 天前无快照
