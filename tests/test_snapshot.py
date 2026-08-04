import pytest

import data_files as df
import snapshot


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    yield


def test_record_snapshot_writes_row():
    snapshot.record_snapshot(1, 100, 10, when="2026-08-04")
    assert df.load_history(1) == [{"date": "2026-08-04", "stars": 100, "forks": 10}]


def test_prune_all_counts_removed_rows():
    df.append_history(1, "2025-01-01", 1, 0)
    df.append_history(1, "2026-08-04", 100, 10)
    df.append_history(2, "2025-01-01", 1, 0)
    removed = snapshot.prune_all({1: {}, 2: {}}, retention_days=30)
    assert removed == 2
