import pytest

import data_files as df
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


def test_summarize_batch_writes_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(df, "DATA_DIR", tmp_path)
    items = [{"repo_id": 1, "readme_excerpt": "readme-1"}, {"repo_id": 2, "readme_excerpt": "readme-2"}]
    results = summary.summarize_batch(items, "fake-key", client_factory=lambda api_key: OkClient())
    assert results[1]["project_positioning"] == "p"
    assert df.load_summary(1)["summary"]["project_positioning"] == "p"
    assert df.load_summary(2)["summary"] is not None
