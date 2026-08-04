import main


def test_candidate_ids_union_of_all_boards():
    boards = {
        "total": [{"repo_id": 1}],
        "daily": [{"repo_id": 2}],
        "weekly": [{"repo_id": 2}],
        "monthly": [{"repo_id": 3}],
        "yearly": [],
    }
    assert main.candidate_ids(boards) == {1, 2, 3}


def test_pending_summaries_only_when_missing_or_hash_changed(tmp_path, monkeypatch):
    import data_files as df
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    df.save_readme(1, "old-hash", "excerpt-1")
    df.save_readme(2, "new-hash", "excerpt-2")
    df.save_summary(2, {"project_positioning": "ok"}, "new-hash")
    repos = {
        1: {"repo_id": 1, "readme_hash": "old-hash"},
        2: {"repo_id": 2, "readme_hash": "new-hash"},
    }
    boards = {"total": [{"repo_id": 1}, {"repo_id": 2}]}
    pending = main.pending_summaries(repos, boards)
    assert [p["repo_id"] for p in pending] == [1]  # 1 缺摘要；2 已有且 hash 匹配
    assert pending[0]["readme_excerpt"] == "excerpt-1"
