from datetime import date, timedelta

import backfill


def test_has_365_anchor_true_when_snapshot_near_cutoff():
    today = date(2026, 8, 4)
    hist = [{"date": (today - timedelta(days=365)).isoformat(), "stars": 100, "forks": 0}]
    assert backfill.has_365_anchor(hist, today) is True
    assert backfill.has_365_anchor([], today) is False


def test_backfill_batch_writes_anchor_and_respects_limit(monkeypatch):
    today = date(2026, 8, 4)
    repos = {
        1: {"repo_id": 1, "repo_name": "a/b"},
        2: {"repo_id": 2, "repo_name": "c/d"},
        3: {"repo_id": 3, "repo_name": "e/f"},
    }
    boards = {"total": [{"repo_id": 1}, {"repo_id": 2}, {"repo_id": 3}]}
    history: dict[int, list] = {}
    snapshots: list[tuple] = []

    class FakeClient:
        def stargazer_count_at(self, repo_name, before):
            return {"a/b": 500, "c/d": 600, "e/f": 700}[repo_name]

    monkeypatch.setattr(backfill, "BACKFILL_BATCH_SIZE", 2)
    processed = backfill.backfill_batch(
        repos,
        boards,
        FakeClient(),
        today,
        load_history=lambda rid: history.get(rid, []),
        upsert_snapshot=lambda rid, when, stars, forks: snapshots.append((rid, when, stars, forks)),
    )
    assert processed == 2
    assert snapshots[0][0] == 1 and snapshots[0][2] == 500
    assert snapshots[1][0] == 2 and snapshots[1][2] == 600
    assert all(s[0] != 3 for s in snapshots)  # 超出批次未处理
    assert repos[1]["backfilled_365"] == (today - timedelta(days=365)).isoformat()
