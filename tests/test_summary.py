import pytest

import summary


def test_parse_summary_strips_code_fence():
    content = '```json\n{"project_positioning": "x", "core_features": ["a"], "use_cases": ["b"], "tech_stack": ["c"]}\n```'
    data = summary.parse_summary(content)
    assert data["project_positioning"] == "x"


def test_parse_summary_rejects_missing_keys():
    with pytest.raises(ValueError):
        summary.parse_summary('{"project_positioning": "x"}')


class FailingClient:
    class Completions:
        @staticmethod
        def create(**kwargs):
            raise RuntimeError("api down")

    chat = type("Chat", (), {"completions": Completions()})()


def test_generate_with_retry_returns_none_after_failures():
    assert summary.generate_with_retry(FailingClient(), "readme") is None


class OkClient:
    class Completions:
        @staticmethod
        def create(**kwargs):
            content = '{"project_positioning": "p", "core_features": ["f"], "use_cases": ["u"], "tech_stack": ["t"]}'
            message = type("M", (), {"content": content})()
            choice = type("C", (), {"message": message})()
            return type("R", (), {"choices": [choice]})()

    chat = type("Chat", (), {"completions": Completions()})()


def test_summarize_batch_writes_cache():
    saved = {}

    def save_summary(repo_id, summary_dict, readme_hash):
        saved[repo_id] = {"summary": summary_dict, "readme_hash": readme_hash}

    items = [
        {"repo_id": 1, "readme_excerpt": "readme-1", "readme_hash": "h1"},
        {"repo_id": 2, "readme_excerpt": "readme-2", "readme_hash": "h2"},
    ]
    results = summary.summarize_batch(
        items,
        "fake-key",
        client_factory=lambda api_key: OkClient(),
        save_summary=save_summary,
    )
    assert results[1]["project_positioning"] == "p"
    assert saved[1]["summary"]["project_positioning"] == "p"
    assert saved[2]["summary"] is not None
