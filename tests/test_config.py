from config import normalize_database_url


def test_normalize_strips_prisma_schema_public():
    raw = "postgresql://user:pass@host:25432/github-ranking?schema=public"
    assert normalize_database_url(raw) == "postgresql://user:pass@host:25432/github-ranking"


def test_normalize_maps_non_public_schema_to_search_path():
    raw = "postgresql://user:pass@host:5432/db?schema=analytics"
    out = normalize_database_url(raw)
    assert "schema=" not in out
    assert "options=" in out
    assert "search_path" in out
    assert "analytics" in out


def test_normalize_keeps_plain_url():
    raw = "postgresql://user:pass@host:5432/db"
    assert normalize_database_url(raw) == raw
