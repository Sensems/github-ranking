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
        def search(self, query, per_page=100, page=1):
            captured["query"] = query
            return {"items": [raw_repo(9, "new/proj", 600)]}

    result = pool.fetch_newcomers(FakeClient())
    assert "created:>=" in captured["query"]
    assert "stars:>=500" in captured["query"]
    assert result[9]["repo_name"] == "new/proj"
