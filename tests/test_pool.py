import pool


def raw_repo(rid, name, stars):
    return {
        "id": rid,
        "full_name": name,
        "description": "desc",
        "stargazers_count": stars,
        "forks_count": 3,
        "language": "Python",
        "html_url": f"https://github.com/{name}",
        "created_at": "2020-01-01T00:00:00Z",
    }


def test_to_repo_record_maps_fields():
    rec = pool.to_repo_record(raw_repo(1, "a/b", 100))
    assert rec["repo_id"] == 1
    assert rec["repo_name"] == "a/b"
    assert rec["stars"] == 100
    assert rec["forks"] == 3


def test_merge_pool_keeps_existing_and_applies_fresh():
    existing = {1: {"repo_name": "a/b", "stars": 10}}
    fresh = {1: {"repo_name": "a/b", "stars": 20}, 2: {"repo_name": "c/d", "stars": 30}}
    newcomers = {3: {"repo_name": "e/f", "stars": 5}}
    merged = pool.merge_pool(existing, fresh, newcomers)
    assert merged[1]["stars"] == 20
    assert 2 in merged and 3 in merged


def test_fetch_newcomers_queries_recent_created():
    captured = {}

    class FakeClient:
        def search(self, query, per_page=100, page=1, *, sort=None, order=None):
            captured["query"] = query
            captured["sort"] = sort
            captured["order"] = order
            return {"items": [raw_repo(9, "new/proj", 600)]}

    result = pool.fetch_newcomers(FakeClient())
    assert "created:>=" in captured["query"]
    assert "stars:>=500" in captured["query"]
    assert "sort:" not in captured["query"]
    assert captured["sort"] == "stars"
    assert captured["order"] == "desc"
    assert result[9]["repo_name"] == "new/proj"


def test_build_watch_set_unions_top_newcomers_and_previous(monkeypatch):
    class FakeClient:
        def top_repos_by_stars(self, limit):
            assert limit == 500
            return [raw_repo(1, "a/a", 5000)]

        def search(self, query, per_page=100, page=1, **kwargs):
            return {"items": []}

        def get_repo_by_id(self, repo_id):
            assert repo_id == 3
            return raw_repo(3, "c/c", 1500)

    newcomer = pool.to_repo_record(raw_repo(2, "b/b", 800))
    monkeypatch.setattr(pool, "fetch_newcomers", lambda client: {2: newcomer})

    existing = {
        3: {"repo_id": 3, "repo_name": "c/c", "description": "old board", "stars": 1200,
            "forks": 1, "language": "Go", "html_url": "https://github.com/c/c",
            "created_at": "2019-01-01T00:00:00Z"},
    }
    result = pool.build_watch_set(FakeClient(), existing, previous_ids={3})

    assert result[1]["repo_name"] == "a/a"
    assert result[2]["repo_name"] == "b/b"
    assert result[3]["repo_name"] == "c/c"
    assert result[3]["stars"] == 1500  # refreshed from GitHub, not stale 1200


def test_build_watch_set_refreshes_previous_only_stars(monkeypatch):
    """Previous board members absent from Top-N/newcomers must not keep stale DB stars."""
    class FakeClient:
        def top_repos_by_stars(self, limit):
            return [raw_repo(1, "a/a", 5000)]

        def search(self, query, per_page=100, page=1, **kwargs):
            return {"items": []}

        def get_repo_by_id(self, repo_id):
            assert repo_id == 7
            return raw_repo(7, "prev/only", 9999)

    monkeypatch.setattr(pool, "fetch_newcomers", lambda client: {})
    existing = {
        7: {"repo_id": 7, "repo_name": "prev/only", "description": "stale", "stars": 100,
            "forks": 0, "language": "Rust", "html_url": "https://github.com/prev/only",
            "created_at": "2021-01-01T00:00:00Z", "readme_hash": "keep-me",
            "backfilled_365": "2025-06-01"},
    }
    result = pool.build_watch_set(FakeClient(), existing, previous_ids={7})
    assert result[7]["stars"] == 9999
    assert result[7]["readme_hash"] == "keep-me"
    assert result[7]["backfilled_365"] == "2025-06-01"


def test_build_watch_set_skips_previous_without_existing_metadata():
    class FakeClient:
        def top_repos_by_stars(self, limit):
            return [raw_repo(1, "a/a", 5000)]

        def search(self, query, per_page=100, page=1, **kwargs):
            return {"items": []}

        def get_repo_by_id(self, repo_id):
            raise AssertionError("should not fetch previous without existing row")

    result = pool.build_watch_set(FakeClient(), existing={}, previous_ids={99})
    assert 99 not in result
    assert 1 in result


def test_build_watch_set_excludes_historical_non_members():
    """Repos that fell out of Top500/newcomers/previous must not remain in G2."""
    class FakeClient:
        def top_repos_by_stars(self, limit):
            return [raw_repo(1, "a/a", 5000)]

        def search(self, query, per_page=100, page=1, **kwargs):
            return {"items": []}

        def get_repo_by_id(self, repo_id):
            raise AssertionError(f"unexpected get_repo_by_id({repo_id})")

    existing = {
        1: {"repo_id": 1, "repo_name": "a/a", "stars": 4000, "readme_hash": "keep",
            "backfilled_365": "2025-01-01", "description": "", "forks": 1,
            "language": "Python", "html_url": "https://github.com/a/a",
            "created_at": "2020-01-01T00:00:00Z"},
        99: {"repo_id": 99, "repo_name": "old/x", "stars": 10, "readme_hash": "x",
             "backfilled_365": None, "description": "", "forks": 0,
             "language": "Go", "html_url": "https://github.com/old/x",
             "created_at": "2018-01-01T00:00:00Z"},
    }
    result = pool.build_watch_set(FakeClient(), existing, previous_ids=set())
    assert 99 not in result
    assert 1 in result
    assert result[1]["stars"] == 5000
    assert result[1]["readme_hash"] == "keep"
    assert result[1]["backfilled_365"] == "2025-01-01"
