"""GitHub REST API 薄封装。"""
from __future__ import annotations

import hashlib
from typing import Optional

import requests

SEARCH_URL = "https://api.github.com/search/repositories"
REPO_BY_ID_URL = "https://api.github.com/repositories/{repo_id}"


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

    def get_repo_by_id(self, repo_id: int) -> dict:
        """Fetch current repository metadata (including stargazers_count) by numeric id."""
        resp = self.session.get(
            REPO_BY_ID_URL.format(repo_id=repo_id),
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
