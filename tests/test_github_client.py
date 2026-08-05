import requests

import github_client as gc


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.reason = "OK" if status_code == 200 else "Error"
        self.url = "https://api.github.com/search/repositories"

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error", response=self)
        return None


def make_session(batches):
    """batches: list of items lists; each search call returns the next batch."""
    calls = []

    class FakeSession:
        def get(self, url, params=None, headers=None):
            calls.append(params)
            batch = batches[min(len(calls) - 1, len(batches) - 1)]
            return FakeResponse({"items": batch})

    return FakeSession()


def repo(i, stars):
    return {"id": i, "full_name": f"owner/repo{i}", "stargazers_count": stars,
            "forks_count": 1, "description": "", "language": "Python",
            "html_url": f"https://github.com/owner/repo{i}", "created_at": "2020-01-01T00:00:00Z"}


def test_top_repos_uses_sort_and_order_query_params():
    """GitHub Search sorts via sort=/order=, not qualifiers inside q."""
    calls = []

    class FakeSession:
        def get(self, url, params=None, headers=None):
            calls.append(params)
            return FakeResponse({"items": [repo(1, 999)]})

    client = gc.GitHubClient(session=FakeSession(), search_max_retries=0)
    client.top_repos_by_stars(1)
    assert calls, "expected a search request"
    params = calls[0]
    assert params["q"] == "stars:>0"
    assert params["page"] == 1
    assert "sort:" not in params["q"]
    assert params["sort"] == "stars"
    assert params["order"] == "desc"


def test_top_repos_paginates_before_lowering_star_window():
    calls = []

    class FakeSession:
        def get(self, url, params=None, headers=None):
            calls.append(dict(params or {}))
            page = params["page"]
            # 100 items per page so pagination continues within the same q.
            start = (page - 1) * 100
            batch = [repo(start + i + 1, 10_000 - start - i) for i in range(100)]
            return FakeResponse({"items": batch})

    client = gc.GitHubClient(session=FakeSession(), search_max_retries=0)
    result = client.top_repos_by_stars(250)
    assert len(result) == 250
    assert [c["page"] for c in calls] == [1, 2, 3]
    assert all(c["q"] == "stars:>0" for c in calls)


def test_top_repos_collects_limit_and_dedupes():
    first = [repo(i, 1000 - i) for i in range(1, 1001)]
    second = [repo(i, 500 - i) for i in range(1001, 2001)]
    client = gc.GitHubClient(session=make_session([first, second]), search_max_retries=0)
    result = client.top_repos_by_stars(2000)
    assert len(result) == 2000
    assert len({r["id"] for r in result}) == 2000
    assert result[0]["stargazers_count"] == 999


def test_top_repos_stops_when_empty():
    client = gc.GitHubClient(session=make_session([[repo(1, 5)]]), search_max_retries=0)
    result = client.top_repos_by_stars(100)
    assert len(result) == 1


def test_search_raises_on_http_error():
    def boom(self, url, params=None, headers=None):
        raise requests.HTTPError("403 rate limit")

    client = gc.GitHubClient(session=type("S", (), {"get": boom})())
    try:
        client.search("stars:>0")
    except requests.HTTPError:
        return
    raise AssertionError("expected HTTPError")


def test_get_repo_by_id_fetches_repository_endpoint():
    captured = {}

    class FakeSession:
        def get(self, url, params=None, headers=None):
            captured["url"] = url
            return FakeResponse(repo(42, 1234))

    client = gc.GitHubClient(session=FakeSession())
    result = client.get_repo_by_id(42)
    assert "repositories/42" in captured["url"]
    assert result["id"] == 42
    assert result["stargazers_count"] == 1234


def test_fetch_readme_falls_back_to_lowercase():
    calls = []

    class FakeSession:
        def get(self, url):
            calls.append(url)
            if "README.md" in url:
                return type("R", (), {"status_code": 404})()
            return type("R", (), {"status_code": 200, "text": "readme-body"})()

    client = gc.GitHubClient(session=FakeSession())
    assert client.fetch_readme("owner/repo") == "readme-body"
    assert len(calls) == 2


def test_readme_hash_is_sha256():
    client = gc.GitHubClient()
    assert client.readme_hash("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert client.readme_hash(None) is None


def test_stargazer_count_at_counts_only_before_cutoff():
    page1 = [
        {"starred_at": "2025-01-01T00:00:00Z"},
        {"starred_at": "2025-03-01T00:00:00Z"},
    ]
    page2 = [
        {"starred_at": "2026-01-01T00:00:00Z"},
    ]

    class FakeSession:
        def get(self, url, params=None, headers=None):
            return type(
                "R",
                (),
                {
                    "json": staticmethod(lambda: page1 if params["page"] == 1 else page2),
                    "raise_for_status": staticmethod(lambda: None),
                },
            )()

    client = gc.GitHubClient(session=FakeSession())
    assert client.stargazer_count_at("owner/repo", "2025-06-01T00:00:00Z") == 2
    assert client.stargazer_count_at("owner/repo", "2024-06-01T00:00:00Z") == 0
