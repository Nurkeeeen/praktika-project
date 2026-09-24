"""Заносит бэклог из docs/requirements/stories.yaml в GitHub Issues (ЗС 4, п. 4).

Нужен GitHub CLI: https://cli.github.com, затем `gh auth login`.
Запуск из корня репозитория:
    python scripts/create_issues.py --dry-run   # показать, что будет создано
    python scripts/create_issues.py             # создать метки, эпики и истории

Повторный запуск безопасен: задачи с таким же названием пропускаются.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = yaml.safe_load((ROOT / "docs" / "requirements" / "stories.yaml").read_text(encoding="utf-8"))
RELEASE_LABEL = {"skeleton": "release:skeleton", "mvp": "release:mvp", "r2": "release:r2", "later": "release:later"}
PRIORITY = {"skeleton": "priority:high", "mvp": "priority:high", "r2": "priority:medium", "later": "priority:low"}
LABELS = {
    "type:epic": "3E4B9E", "type:story": "1D76DB", "type:spike": "FBCA04", "type:change-request": "B60205",
    "priority:high": "B60205", "priority:medium": "D93F0B", "priority:low": "C2E0C6",
    "release:skeleton": "F76707", "release:mvp": "FAB005", "release:r2": "4DABF7", "release:later": "ADB5BD",
    "зс-4": "EDEDED",
}


def gh(*args: str, dry: bool = False) -> str:
    if dry:
        print("gh", " ".join(a if " " not in a else repr(a) for a in args[:4]), "...")
        return ""
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout


def existing_titles() -> set[str]:
    out = gh("issue", "list", "--state", "all", "--limit", "500", "--json", "title")
    return {i["title"] for i in json.loads(out or "[]")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    dry = ap.parse_args().dry_run

    for name, color in LABELS.items():
        gh("label", "create", name, "--color", color, "--force", dry=dry)
    have = set() if dry else existing_titles()

    epic_num: dict[str, str] = {}
    for key, name in DATA["epics"].items():
        title = f"[ЗС-4] {key}: {name}"
        if title in have:
            continue
        url = gh("issue", "create", "--title", title, "--label", "type:epic,зс-4",
                 "--body", f"Эпик {key}. Истории — задачи со ссылкой «Эпик: {key}».", dry=dry)
        epic_num[key] = url.strip().rsplit("/", 1)[-1] if url else key

    for s in DATA["stories"]:
        title = f"[ЗС-4] {s['id']} {s['title']}"
        if title in have:
            continue
        kind = "type:spike" if s.get("type") == "spike" else "type:story"
        epic = epic_num.get(s["epic"], s["epic"])
        body = "\n".join([
            s["story"], "", "**Критерии приёмки**", *[f"- {a}" for a in s["acceptance"]], "",
            f"**Оценка:** {s['points']} SP · **Релиз:** {s['release']} · **Эпик:** #{epic} "
            f"({DATA['epics'][s['epic']]}) · **Шаг пути:** {DATA['activities'][s['activity']]}",
            *([f"**Уже есть в прототипе:** `{s['api']}`"] if s.get("api") else []),
        ])
        labels = ",".join([kind, PRIORITY[s["release"]], RELEASE_LABEL[s["release"]], "зс-4"])
        gh("issue", "create", "--title", title, "--label", labels, "--body", body, dry=dry)
        print("создано:", title)


if __name__ == "__main__":
    main()
