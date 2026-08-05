"""全局配置：常量与密钥入口。所有脚本只从这里读取配置。"""
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def normalize_database_url(url: str) -> str:
    """Strip Prisma-only query params (e.g. schema=public) that psycopg rejects."""
    if not url or "?" not in url:
        return url
    parsed = urlparse(url)
    if not parsed.query:
        return url
    kept: list[tuple[str, str]] = []
    schema: str | None = None
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key == "schema":
            schema = value or None
            continue
        kept.append((key, value))
    # public is the Postgres default; non-public schemas map to search_path.
    if schema and schema != "public":
        if not any(k == "options" and "search_path" in v for k, v in kept):
            kept.append(("options", f"-csearch_path={schema}"))
    return urlunparse(parsed._replace(query=urlencode(kept)))


# Database
DATABASE_URL = normalize_database_url(os.environ.get("DATABASE_URL", ""))

# GitHub
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
WATCH_TOP_N = 500
POOL_SIZE = WATCH_TOP_N
TOTAL_BOARD_SIZE = 100
NEWCOMER_MIN_STARS = 500
NEWCOMER_DAYS = 30

# 榜单
PARTICIPATION_MIN_STARS = 1_000
LEADERBOARD_SIZE = 100
TOLERANCE_DAYS = 3
WINDOWS = {"daily": 1, "weekly": 7, "monthly": 30, "yearly": 365}

# 历史
HISTORY_RETENTION_DAYS = 400

# README / AI 摘要
README_TRUNCATE_CHARS = 30_000
XFYUN_API_KEY = os.environ.get("XFYUN_API_KEY", "")
XFYUN_BASE_URL = os.environ.get("XFYUN_BASE_URL", "https://maas-token-api.cn-huabei-1.xf-yun.com/v2")
XFYUN_MODEL = os.environ.get("XFYUN_MODEL", "xsparkx2")
SUMMARY_CONCURRENCY = 3
SUMMARY_TIMEOUT_S = 60
SUMMARY_MAX_RETRIES = 2
SUMMARY_BATCH_SIZE = 100

# 回溯
BACKFILL_BATCH_SIZE = 300
