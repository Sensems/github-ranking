from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

import config
import db
import main
import migrate
import summary as summary_mod


def test_candidate_ids_union_of_all_boards():
    boards = {
        "total": [{"repo_id": 1}],
        "daily": [{"repo_id": 2}],
        "weekly": [{"repo_id": 2}],
        "monthly": [{"repo_id": 3}],
        "yearly": [],
    }
    assert main.candidate_ids(boards) == {1, 2, 3}


def test_cli_choices_exclude_stage(monkeypatch):
    import argparse

    captured = {}

    class FakeParser:
        """Plain stub — do not subclass ArgumentParser (monkeypatch recursion hang)."""

        def __init__(self, *args, **kwargs):
            pass

        def add_argument(self, *args, **kwargs):
            if args and args[0] == "command":
                captured["choices"] = kwargs.get("choices")

        def parse_args(self, args=None, namespace=None):
            return argparse.Namespace(command="sync")

    monkeypatch.setattr(argparse, "ArgumentParser", FakeParser)
    monkeypatch.setattr(main, "sync", lambda: None)
    main.main()
    assert captured["choices"] == ["sync", "backfill", "migrate"]
    assert "stage" not in captured["choices"]


def test_pending_summaries_only_when_missing_or_hash_changed():
    store = {
        "readmes": {
            1: {"hash": "old-hash", "excerpt": "excerpt-1"},
            2: {"hash": "new-hash", "excerpt": "excerpt-2"},
        },
        "summaries": {
            2: {"readme_hash": "new-hash", "summary": {"project_positioning": "ok"}},
        },
    }
    conn = object()

    def load_readme(c, rid):
        assert c is conn
        return store["readmes"].get(rid)

    def load_summary(c, rid):
        assert c is conn
        return store["summaries"].get(rid)

    repos = {
        1: {"repo_id": 1, "readme_hash": "old-hash"},
        2: {"repo_id": 2, "readme_hash": "new-hash"},
    }
    boards = {"total": [{"repo_id": 1}, {"repo_id": 2}]}
    pending = main.pending_summaries(
        repos,
        boards,
        conn,
        load_readme=load_readme,
        load_summary=load_summary,
    )
    assert [p["repo_id"] for p in pending] == [1]
    assert pending[0]["readme_excerpt"] == "excerpt-1"


def test_sync_end_to_end_with_fakes(monkeypatch):
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://test/db")
    monkeypatch.setattr(main, "XFYUN_API_KEY", "fake")
    monkeypatch.setattr(main, "DATABASE_URL", "postgresql://test/db")

    store = {
        "repos": {},
        "history": {},
        "readmes": {},
        "summaries": {},
        "leaderboards": {},
        "previous": set(),
    }
    conn = MagicMock()

    def load_repos(c):
        return {k: dict(v) for k, v in store["repos"].items()}

    def load_previous(c):
        return set(store["previous"])

    def upsert_repo(c, repo):
        store["repos"][repo["repo_id"]] = dict(repo)

    def upsert_snapshot(c, rid, when, stars, forks):
        rows = [r for r in store["history"].get(rid, []) if r["date"] != when]
        rows.append({"date": when, "stars": stars, "forks": forks})
        rows.sort(key=lambda r: r["date"])
        store["history"][rid] = rows

    def load_history(c, rid):
        return list(store["history"].get(rid, []))

    def prune_snapshots(c, retention_days=400):
        return 0

    def save_readme(c, rid, hash_value, excerpt):
        store["readmes"][rid] = {"hash": hash_value, "excerpt": excerpt}

    def load_readme(c, rid):
        return store["readmes"].get(rid)

    def save_summary(c, rid, summary, readme_hash):
        store["summaries"][rid] = {
            "readme_hash": readme_hash,
            "summary": summary,
            "generated_at": date.today().isoformat(),
        }

    def load_summary(c, rid):
        return store["summaries"].get(rid)

    def save_leaderboard(c, name, payload):
        store["leaderboards"][name] = payload

    monkeypatch.setattr(db, "connect", lambda: MagicMock(
        __enter__=lambda s: conn,
        __exit__=lambda *a: False,
    ))
    # context manager protocol for `with db.connect() as conn`
    cm = MagicMock()
    cm.__enter__.return_value = conn
    cm.__exit__.return_value = False
    monkeypatch.setattr(db, "connect", lambda: cm)

    monkeypatch.setattr(db, "load_repos", load_repos)
    monkeypatch.setattr(db, "load_previous_growth_members", load_previous)
    monkeypatch.setattr(db, "upsert_repo", upsert_repo)
    monkeypatch.setattr(db, "upsert_snapshot", upsert_snapshot)
    monkeypatch.setattr(db, "load_history", load_history)
    monkeypatch.setattr(db, "prune_snapshots", prune_snapshots)
    monkeypatch.setattr(db, "save_readme", save_readme)
    monkeypatch.setattr(db, "load_readme", load_readme)
    monkeypatch.setattr(db, "save_summary", save_summary)
    monkeypatch.setattr(db, "load_summary", load_summary)
    monkeypatch.setattr(db, "save_leaderboard", save_leaderboard)
    monkeypatch.setattr(migrate, "migrate_up", MagicMock(return_value=0))

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

        def get_repo_by_id(self, repo_id):
            raise AssertionError(f"unexpected get_repo_by_id({repo_id})")

        def fetch_readme(self, repo_name, truncate_chars=30_000):
            return "readme content"

        def readme_hash(self, content):
            return "hash-1" if content else None

    monkeypatch.setattr(main, "GitHubClient", FakeClient)

    today = date.today()
    for days in (1, 7, 30, 365):
        when = (today - timedelta(days=days)).isoformat()
        upsert_snapshot(conn, 1, when, 1000, 5)
        upsert_snapshot(conn, 2, when, 1400, 5)

    def fake_summarize(items, api_key, client_factory=None, save_summary=None):
        out = {}
        for it in items:
            summary = {"project_positioning": "p"}
            out[it["repo_id"]] = summary
            if save_summary is not None:
                save_summary(it["repo_id"], summary, it.get("readme_hash"))
        return out

    monkeypatch.setattr(summary_mod, "summarize_batch", fake_summarize)

    main.sync()

    boards = store["leaderboards"]["daily"]
    assert len(boards["items"]) == 2
    assert boards["items"][0]["repo_name"] == "a/b"
    assert boards["items"][0]["growth"]["daily"] == 1000
    assert store["repos"][1]["readme_hash"] == "hash-1"
    assert boards["items"][0]["summary"] == {"project_positioning": "p"}
    conn.commit.assert_called()
    migrate.migrate_up.assert_called_once_with(conn)


def test_sync_requires_database_url(monkeypatch):
    monkeypatch.setattr(main, "DATABASE_URL", "")
    with pytest.raises(SystemExit, match="DATABASE_URL"):
        main.sync()


def test_sync_does_not_snapshot_fallen_out_repos(monkeypatch):
    """Historical repos outside Top500∪newcomers∪previous must not get today's snapshot."""
    monkeypatch.setattr(main, "DATABASE_URL", "postgresql://test/db")
    monkeypatch.setattr(main, "XFYUN_API_KEY", "")

    store = {
        "repos": {
            99: {
                "repo_id": 99, "repo_name": "old/fallen", "description": "", "stars": 50,
                "forks": 0, "language": "Go", "html_url": "https://github.com/old/fallen",
                "created_at": "2018-01-01T00:00:00Z", "readme_hash": "keep-me",
                "backfilled_365": "2025-01-01",
            },
            1: {
                "repo_id": 1, "repo_name": "a/b", "description": "", "stars": 100,
                "forks": 0, "language": "Python", "html_url": "https://github.com/a/b",
                "created_at": "2020-01-01T00:00:00Z", "readme_hash": "h",
                "backfilled_365": None,
            },
        },
        "history": {},
        "readmes": {},
        "summaries": {},
        "leaderboards": {},
        "previous": set(),
        "snapshotted": [],
    }
    conn = MagicMock()
    cm = MagicMock()
    cm.__enter__.return_value = conn
    cm.__exit__.return_value = False
    monkeypatch.setattr(db, "connect", lambda: cm)
    monkeypatch.setattr(db, "load_repos", lambda c: {k: dict(v) for k, v in store["repos"].items()})
    monkeypatch.setattr(db, "load_previous_growth_members", lambda c: set(store["previous"]))
    monkeypatch.setattr(db, "upsert_repo", lambda c, repo: store["repos"].__setitem__(repo["repo_id"], dict(repo)))
    monkeypatch.setattr(
        db,
        "upsert_snapshot",
        lambda c, rid, when, stars, forks: store["snapshotted"].append(rid),
    )
    monkeypatch.setattr(db, "load_history", lambda c, rid: [])
    monkeypatch.setattr(db, "prune_snapshots", lambda c, retention_days=400: 0)
    monkeypatch.setattr(db, "save_readme", lambda *a, **k: None)
    monkeypatch.setattr(db, "load_readme", lambda c, rid: None)
    monkeypatch.setattr(db, "load_summary", lambda c, rid: None)
    monkeypatch.setattr(db, "save_leaderboard", lambda *a, **k: None)
    monkeypatch.setattr(migrate, "migrate_up", MagicMock(return_value=0))

    class FakeClient:
        def __init__(self, token=""):
            pass

        def top_repos_by_stars(self, limit):
            return [{
                "id": 1, "full_name": "a/b", "description": "d", "stargazers_count": 2000,
                "forks_count": 1, "language": "Python", "html_url": "https://github.com/a/b",
                "created_at": "2020-01-01T00:00:00Z",
            }]

        def search(self, query, per_page=100, page=1):
            return {"items": []}

        def get_repo_by_id(self, repo_id):
            raise AssertionError(f"unexpected get_repo_by_id({repo_id})")

        def fetch_readme(self, repo_name, truncate_chars=30_000):
            return None

        def readme_hash(self, content):
            return None

    monkeypatch.setattr(main, "GitHubClient", FakeClient)
    main.sync()
    assert 99 not in store["snapshotted"]
    assert 1 in store["snapshotted"]


def test_backfill_skips_historical_non_g2_repos(monkeypatch):
    """Fallen-out repos must not enter backfill_batch via boards from full load_repos."""
    monkeypatch.setattr(main, "DATABASE_URL", "postgresql://test/db")
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://test/db")

    store = {
        "repos": {
            99: {
                "repo_id": 99, "repo_name": "old/fallen", "description": "", "stars": 9000,
                "forks": 0, "language": "Go", "html_url": "https://github.com/old/fallen",
                "created_at": "2018-01-01T00:00:00Z", "readme_hash": None,
                "backfilled_365": None,
            },
            1: {
                "repo_id": 1, "repo_name": "a/b", "description": "", "stars": 2000,
                "forks": 0, "language": "Python", "html_url": "https://github.com/a/b",
                "created_at": "2020-01-01T00:00:00Z", "readme_hash": None,
                "backfilled_365": None,
            },
        },
        "history": {},
        "previous": set(),
        "snapshotted": [],
        "stargazer_queries": [],
    }
    conn = MagicMock()
    cm = MagicMock()
    cm.__enter__.return_value = conn
    cm.__exit__.return_value = False
    monkeypatch.setattr(db, "connect", lambda: cm)
    monkeypatch.setattr(db, "load_repos", lambda c: {k: dict(v) for k, v in store["repos"].items()})
    monkeypatch.setattr(db, "load_previous_growth_members", lambda c: set(store["previous"]))
    monkeypatch.setattr(db, "load_history", lambda c, rid: list(store["history"].get(rid, [])))
    monkeypatch.setattr(db, "load_summary", lambda c, rid: None)
    monkeypatch.setattr(
        db,
        "upsert_snapshot",
        lambda c, rid, when, stars, forks: store["snapshotted"].append(rid),
    )
    monkeypatch.setattr(db, "upsert_repo", lambda c, repo: store["repos"].__setitem__(repo["repo_id"], dict(repo)))
    monkeypatch.setattr(migrate, "migrate_up", MagicMock(return_value=0))

    class FakeClient:
        def __init__(self, token=""):
            pass

        def top_repos_by_stars(self, limit):
            return [{
                "id": 1, "full_name": "a/b", "description": "d", "stargazers_count": 2000,
                "forks_count": 1, "language": "Python", "html_url": "https://github.com/a/b",
                "created_at": "2020-01-01T00:00:00Z",
            }]

        def search(self, query, per_page=100, page=1):
            return {"items": []}

        def get_repo_by_id(self, repo_id):
            raise AssertionError(f"unexpected get_repo_by_id({repo_id})")

        def stargazer_count_at(self, repo_name, before):
            store["stargazer_queries"].append(repo_name)
            return 100

    monkeypatch.setattr(main, "GitHubClient", FakeClient)
    main.backfill()

    assert "old/fallen" not in store["stargazer_queries"]
    assert 99 not in store["snapshotted"]
    assert "a/b" in store["stargazer_queries"]
    assert 1 in store["snapshotted"]
