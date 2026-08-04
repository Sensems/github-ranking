"""data/ 目录下 JSON/CSV 文件的读写与滚动裁剪。"""
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from config import DATA_DIR, HISTORY_RETENTION_DAYS


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def repos_path() -> Path:
    return DATA_DIR / "repos.json"


def load_repos() -> dict[int, dict]:
    data = load_json(repos_path(), {"repos": {}})
    return {int(k): v for k, v in data.get("repos", {}).items()}


def save_repos(repos: dict[int, dict]) -> None:
    payload = {
        "updated_at": date.today().isoformat(),
        "repos": {str(k): v for k, v in repos.items()},
    }
    save_json(repos_path(), payload)


def history_path(repo_id: int) -> Path:
    return DATA_DIR / "history" / f"{repo_id}.csv"


def load_history(repo_id: int) -> list[dict]:
    path = history_path(repo_id)
    rows: list[dict] = []
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append({"date": row["date"], "stars": int(row["stars"]), "forks": int(row["forks"])})
    return rows


def append_history(repo_id: int, when: str, stars: int, forks: int) -> None:
    """幂等追加：同一天重复写入只保留最后一次。"""
    rows = [r for r in load_history(repo_id) if r["date"] != when]
    rows.append({"date": when, "stars": stars, "forks": forks})
    rows.sort(key=lambda r: r["date"])
    path = history_path(repo_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("date,stars,forks\n")
        for r in rows:
            f.write(f"{r['date']},{r['stars']},{r['forks']}\n")


def prune_history(repo_id: int, retention_days: int = HISTORY_RETENTION_DAYS) -> None:
    rows = load_history(repo_id)
    cutoff = date.today().toordinal() - retention_days
    keep = [r for r in rows if date.fromisoformat(r["date"]).toordinal() >= cutoff]
    if len(keep) < len(rows):
        path = history_path(repo_id)
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write("date,stars,forks\n")
            for r in keep:
                f.write(f"{r['date']},{r['stars']},{r['forks']}\n")


def readme_path(repo_id: int) -> Path:
    return DATA_DIR / "readmes" / f"{repo_id}.json"


def load_readme(repo_id: int) -> dict | None:
    return load_json(readme_path(repo_id))


def save_readme(repo_id: int, hash_value: str, excerpt: str) -> None:
    save_json(readme_path(repo_id), {"hash": hash_value, "excerpt": excerpt})


def summary_path(repo_id: int) -> Path:
    return DATA_DIR / "summaries" / f"{repo_id}.json"


def load_summary(repo_id: int) -> dict | None:
    return load_json(summary_path(repo_id))


def save_summary(repo_id: int, summary: dict, readme_hash: str | None) -> None:
    save_json(summary_path(repo_id), {
        "generated_at": date.today().isoformat(),
        "readme_hash": readme_hash,
        "summary": summary,
    })


def save_leaderboard(name: str, payload: dict) -> None:
    save_json(DATA_DIR / "leaderboards" / f"{name}.json", payload)
