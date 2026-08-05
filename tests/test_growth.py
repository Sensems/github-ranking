from datetime import date

import growth


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
    hist = {
        1: history(("2026-08-03", 1990), ("2026-08-04", 2000)),
        2: history(("2026-08-03", 1400), ("2026-08-04", 1500)),
    }
    summaries = {}
    repos = {
        1: {"repo_id": 1, "repo_name": "a/b", "stars": 2000, "forks": 5, "language": "Python",
            "description": "x", "html_url": "https://github.com/a/b", "created_at": "2020-01-01T00:00:00Z"},
        2: {"repo_id": 2, "repo_name": "c/d", "stars": 1500, "forks": 9, "language": "Go",
            "description": "y", "html_url": "https://github.com/c/d", "created_at": "2020-01-01T00:00:00Z"},
    }
    boards = growth.build_boards(
        repos,
        date(2026, 8, 4),
        load_history=lambda rid: hist.get(rid, []),
        load_summary=lambda rid: summaries.get(rid),
    )
    assert [i["repo_name"] for i in boards["daily"]] == ["c/d", "a/b"]
    assert boards["daily"][0]["growth"]["daily"] == 100
    assert boards["daily"][0]["rank"] == 1
    assert [i["repo_name"] for i in boards["total"]] == ["a/b", "c/d"]
    assert len(boards["weekly"]) == 0  # 7 天前无快照


def test_board_item_exposes_meta_not_summary_body():
    repo = {
        "repo_id": 1, "repo_name": "a/b", "description": "d", "language": "Go",
        "stars": 10, "forks": 2, "html_url": "https://github.com/a/b",
        "created_at": "2020-01-01T00:00:00Z",
        "open_issues": 3, "pushed_at": "2026-07-14T19:25:58Z",
    }
    growth_data = {"daily": 1, "weekly": 2, "monthly": 3, "yearly": 4}

    def load_summary(rid):
        return {"summary": {"project_positioning": "x"}, "readme_hash": "h"}

    item = growth.board_item(repo, growth_data, 1, load_summary)
    assert item["open_issues"] == 3
    assert item["pushed_at"] == "2026-07-14T19:25:58Z"
    assert item["has_summary"] is True
    assert "summary" not in item


def test_build_boards_total_uses_total_size():
    repos = {
        i: {
            "repo_id": i,
            "repo_name": f"o/r{i}",
            "stars": 1000 + i,
            "forks": 1,
            "language": "Python",
            "description": "",
            "html_url": f"https://github.com/o/r{i}",
            "created_at": "2020-01-01T00:00:00Z",
        }
        for i in range(1, 6)
    }
    boards = growth.build_boards(
        repos,
        date(2026, 8, 4),
        load_history=lambda _rid: [],
        load_summary=lambda _rid: None,
        total_size=2,
        board_size=10,
    )
    assert len(boards["total"]) == 2
    assert [i["repo_name"] for i in boards["total"]] == ["o/r5", "o/r4"]
