"""讯飞星辰 MaaS（Astron）AI 摘要生成：队列、重试、缓存。"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from openai import OpenAI

from config import (
    SUMMARY_CONCURRENCY,
    SUMMARY_MAX_RETRIES,
    SUMMARY_TIMEOUT_S,
    XFYUN_BASE_URL,
    XFYUN_MODEL,
)

SYSTEM_PROMPT = (
    "你是一个技术文档摘要专家，请用简洁的中文概括以下GitHub项目的README内容。"
    '严格输出 JSON，格式为：{"project_positioning": "一句话定位", '
    '"core_features": ["功能1", "功能2", "功能3"], '
    '"use_cases": ["场景1", "场景2"], '
    '"tech_stack": ["技术栈1", "技术栈2"]}'
)


def build_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=XFYUN_BASE_URL)


def parse_summary(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("summary is not a JSON object")
    for key in ("project_positioning", "core_features", "use_cases", "tech_stack"):
        if key not in data:
            raise ValueError(f"missing key: {key}")
    return data


def generate_one(client: OpenAI, readme_excerpt: str) -> dict:
    response = client.chat.completions.create(
        model=XFYUN_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": readme_excerpt},
        ],

        temperature=0.3,
        max_tokens=1024,
        timeout=SUMMARY_TIMEOUT_S,
    )
    return parse_summary(response.choices[0].message.content)


def generate_with_retry(client: OpenAI, readme_excerpt: str) -> Optional[dict]:
    for attempt in range(SUMMARY_MAX_RETRIES + 1):
        try:
            return generate_one(client, readme_excerpt)
        except Exception:
            if attempt == SUMMARY_MAX_RETRIES:
                return None
    return None


def summarize_batch(
    items: list[dict],
    api_key: str,
    client_factory: Callable[[str], OpenAI] = build_client,
    *,
    save_summary: Callable[[int, dict, Optional[str]], None],
) -> dict[int, Optional[dict]]:
    """items: [{repo_id, readme_excerpt, readme_hash}]；成功后经 save_summary 写缓存。"""
    client = client_factory(api_key)
    results: dict[int, Optional[dict]] = {}

    def work(item: dict) -> tuple[int, Optional[dict], Optional[str]]:
        return (
            item["repo_id"],
            generate_with_retry(client, item["readme_excerpt"]),
            item.get("readme_hash"),
        )

    with ThreadPoolExecutor(max_workers=SUMMARY_CONCURRENCY) as pool:
        for repo_id, summary_dict, readme_hash in pool.map(work, items):
            results[repo_id] = summary_dict
            if summary_dict is not None:
                save_summary(repo_id, summary_dict, readme_hash)
    return results
