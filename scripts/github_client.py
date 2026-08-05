"""GitHub REST API 薄封装。"""
from __future__ import annotations

import hashlib
import time
from typing import Optional

import requests

SEARCH_URL = "https://api.github.com/search/repositories"
REPO_BY_ID_URL = "https://api.github.com/repositories/{repo_id}"
# Search API returns at most 1000 results (10 pages × 100) per query window.
SEARCH_MAX_PAGES = 10
SEARCH_PER_PAGE = 100


class GitHubClient:
    def __init__(
        self,
        token: str = "",
        session: Optional[requests.Session] = None,
        *,
        search_retry_wait_s: float = 60.0,
        search_max_retries: int = 3,
    ) -> None:
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.session = session or requests.Session()
        self.search_retry_wait_s = search_retry_wait_s
        self.search_max_retries = search_max_retries

    def search(
        self,
        query: str,
        per_page: int = SEARCH_PER_PAGE,
        page: int = 1,
        *,
        sort: Optional[str] = None,
        order: Optional[str] = None,
    ) -> dict:
        params: dict = {"q": query, "per_page": per_page, "page": page}
        if sort is not None:
            params["sort"] = sort
        if order is not None:
            params["order"] = order
        last_exc: Optional[requests.HTTPError] = None
        for attempt in range(self.search_max_retries + 1):
            resp = self.session.get(
                SEARCH_URL,
                params=params,
                headers=self.headers,
            )
            if resp.status_code != 403 or attempt >= self.search_max_retries:
                resp.raise_for_status()
                return resp.json()
            last_exc = requests.HTTPError(
                f"{resp.status_code} Client Error: {resp.reason} for url: {resp.url}",
                response=resp,
            )
            # Secondary rate limit — wait then retry.
            time.sleep(self.search_retry_wait_s)
        raise last_exc  # pragma: no cover

    def get_repo_by_id(self, repo_id: int) -> dict:
        """Fetch current repository metadata (including stargazers_count) by numeric id."""
        resp = self.session.get(
            REPO_BY_ID_URL.format(repo_id=repo_id),
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    def top_repos_by_stars(self, limit: int) -> list[dict]:
        """收集 Top-N（按 stars 降序）。

        先对同一 query 翻页（最多 1000 条），不足再以 stars:<floor 下探窗口。
        sort/order 是 Search API 独立参数，不能写进 q。
        """
        results: list[dict] = []
        seen: set[int] = set()
        upper: Optional[int] = None
        while len(results) < limit:
            query = "stars:>0" if upper is None else f"stars:<{upper}"
            window_min: Optional[int] = None
            got_new = False
            for page in range(1, SEARCH_MAX_PAGES + 1):
                if len(results) >= limit:
                    break
                items = self.search(
                    query, per_page=SEARCH_PER_PAGE, page=page, sort="stars", order="desc"
                ).get("items", [])
                if not items:
                    break
                new = [r for r in items if r["id"] not in seen]
                if not new:
                    break
                for r in new:
                    seen.add(r["id"])
                results.extend(new)
                got_new = True
                page_min = min(r["stargazers_count"] for r in new)
                window_min = page_min if window_min is None else min(window_min, page_min)
                if len(items) < SEARCH_PER_PAGE:
                    break
            if not got_new or window_min is None:
                break
            if len(results) >= limit:
                break
            # Next search window below the lowest star count seen so far.
            upper = window_min
        return results[:limit]

    def fetch_readme(self, repo_name: str, truncate_chars: int = 30_000) -> Optional[str]:
        """经 raw.githubusercontent.com 抓取 README（不计 API 配额）。"""
        for filename in ("README.md", "readme.md", "Readme.md"):
            url = f"https://raw.githubusercontent.com/{repo_name}/HEAD/{filename}"
            resp = self.session.get(url)
            if resp.status_code == 200:
                return resp.text[:truncate_chars]
            if resp.status_code != 404:
                resp.raise_for_status()
        return None

    def readme_hash(self, content: Optional[str]) -> Optional[str]:
        if content is None:
            return None
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def stargazer_count_at(self, repo_name: str, before: str) -> int:
        """近似统计 before 时点之前（含）的 stargazers 数。
        列表按 starring 时间正序返回；只统计当前仍在 star 的用户（unstar 不计入）。"""
        headers = {**self.headers, "Accept": "application/vnd.github.star+json"}
        url = f"https://api.github.com/repos/{repo_name}/stargazers"
        count = 0
        page = 1
        while True:
            resp = self.session.get(url, params={"per_page": 100, "page": page}, headers=headers)
            resp.raise_for_status()
            items = resp.json()
            if not items:
                return count
            for item in items:
                if item.get("starred_at", "9999-12-31T00:00:00Z") <= before:
                    count += 1
                else:
                    return count
            page += 1
