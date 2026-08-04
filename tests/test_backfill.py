from datetime import date, timedelta

import pytest

import backfill
import data_files as df


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    yield


def test_has_365_anchor_true_when_snapshot_near_cutoff():
    today = date(2026, 8, 4)
    df.append_history(1, (today - timedelta(days=365)).isoformat(), 100, 0)
    assert backfill.has_365_anchor(df.load_history(1), today) is True
    assert backfill.has_365_anchor([], today) is False


def test_backfill_batch_writes_anchor_and_respects_limit(monkeypatch):
    today = date(2026, 8, 4)
    repos = {
        1: {"repo_id": 1, "repo_name": "a/b"},
        2: {"repo_id": 2, "repo_name": "c/d"},
        3: {"repo_id": 3, "repo_name": "e/f"},
    }
    boards = {"total": [{"repo_id": 1}, {"repo_id": 2}, {"repo_id": 3}]}

    class FakeClient:
        def stargazer_count_at(self, repo_name, before):
            return {"a/b": 500, "c/d": 600, "e/f": 700}[repo_name]

    monkeypatch.setattr(backfill, "BACKFILL_BATCH_SIZE", 2)
    processed = backfill.backfill_batch(repos, boards, FakeClient(), today)
    assert processed == 2
    hist = df.load_history(1)
    assert hist and hist[0]["stars"] == 500
    assert df.load_history(3) == []  # 超出批次未处理
