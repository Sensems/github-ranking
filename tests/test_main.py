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


def test_sync_end_to_end_with_fakes(monkeypatch, tmp_path):
    from datetime import date, timedelta

    import summary as summary_mod
    import data_files as df
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    monkeypatch.setattr(main, "XFYUN_API_KEY", "fake")

    def raw_repo(rid, name, stars):
        return {
            "id": rid, "full_name": name, "description": "d", "stargazers_count": stars,
            "forks_count": 1, "language": "Python", "html_url": f"https://github.com/{name}",
            "created_at": "2020-01-01T00:00:00Z",
        }

    class FakeClient:
        def __init__(self, token=""):
            pass

        def top_repos_by_stars(self, limit):
            return [raw_repo(1, "a/b", 2000), raw_repo(2, "c/d", 1500)]

        def search(self, query, per_page=100, page=1):
            return {"items": []}

        def fetch_readme(self, repo_name, truncate_chars=30_000):
            return "readme content"

        def readme_hash(self, content):
            return "hash-1" if content else None

    monkeypatch.setattr(main, "GitHubClient", FakeClient)

    today = date.today()
    for days in (1, 7, 30, 365):
        when = (today - timedelta(days=days)).isoformat()
        df.append_history(1, when, 1000, 5)
        df.append_history(2, when, 1400, 5)

    def fake_summarize(items, api_key):
        return {it["repo_id"]: {"project_positioning": "p"} for it in items}

    monkeypatch.setattr(summary_mod, "summarize_batch", fake_summarize)

    main.sync()

    boards = df.load_json(df.DATA_DIR / "leaderboards" / "daily.json")
    assert len(boards["items"]) == 2
    assert boards["items"][0]["repo_name"] == "a/b"
    assert boards["items"][0]["growth"]["daily"] == 1000
    repos = df.load_repos()
    assert repos[1]["readme_hash"] == "hash-1"
