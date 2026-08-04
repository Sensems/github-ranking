"""GitHub REST API 薄封装。"""
from __future__ import annotations

from typing import Optional

import requests

SEARCH_URL = "https://api.github.com/search/repositories"


class GitHubClient:
    def __init__(self, token: str = "", session: Optional[requests.Session] = None) -> None:
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.session = session or requests.Session()

    def search(self, query: str, per_page: int = 100, page: int = 1) -> dict:
        resp = self.session.get(
            SEARCH_URL,
            params={"q": query, "per_page": per_page, "page": page},
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    def top_repos_by_stars(self, limit: int) -> list[dict]:
        """迭代下探收集 Top-N（按 stars 降序）。单次查询最多 1000 条。"""
        results: list[dict] = []
        seen: set[int] = set()
        upper: Optional[int] = None
        while len(results) < limit:
            query = "stars:>0 sort:stars desc" if upper is None else f"stars:<{upper} sort:stars desc"
            items = self.search(query).get("items", [])
            if not items:
                break
            new = [r for r in items if r["id"] not in seen]
            for r in new:
                seen.add(r["id"])
            if not new:
                break
            results.extend(new)
            upper = min(r["stargazers_count"] for r in new)
        return results[:limit]
