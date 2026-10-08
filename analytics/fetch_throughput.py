"""Выгружает историю закрытых задач открытого репозитория GitHub в CSV (данные для ЗС 6).

Берём только issues (без pull request), закрытые как выполненные (state_reason = completed):
дубли и «не будем делать» в throughput не входят. Снимок сохраняется в analytics/data/,
поэтому notebook воспроизводим без сети.

Запуск: python analytics/fetch_throughput.py owner/repo 2025-10-06 2026-10-05
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "data"


def fetch(repo: str, since: str, until: str) -> list[dict]:
    rows, page = [], 1
    while True:
        url = (f"https://api.github.com/repos/{repo}/issues?state=closed&since={since}T00:00:00Z"
               f"&per_page=100&page={page}&sort=updated&direction=desc")
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                   "User-Agent": "praktika-course-lab"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        if not data:
            break
        for i in data:
            closed = (i.get("closed_at") or "")[:10]
            if "pull_request" in i or i.get("state_reason") != "completed" or not (since <= closed < until):
                continue
            rows.append({"number": i["number"], "created": i["created_at"][:10], "closed": closed,
                         "title": i["title"]})
        page += 1
        time.sleep(1)
    return sorted(rows, key=lambda r: r["closed"])


def main() -> None:
    repo, since, until = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = fetch(repo, since, until)
    path = OUT_DIR / f"closed_issues_{repo.replace('/', '__')}.csv"
    OUT_DIR.mkdir(exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["number", "created", "closed", "title"])
        w.writeheader()
        w.writerows(rows)
    print(f"{repo}: {len(rows)} закрытых задач → {path}")


if __name__ == "__main__":
    main()
