"""Критерии приёмки ЗС 4 как код: бэклог и НФТ не должны деградировать при правках."""

import re
from pathlib import Path

import yaml

REQ = Path(__file__).resolve().parents[1] / "docs" / "requirements"
BACKLOG = yaml.safe_load((REQ / "stories.yaml").read_text(encoding="utf-8"))
NFR = yaml.safe_load((REQ / "nfr.yaml").read_text(encoding="utf-8"))
FIBONACCI = {1, 2, 3, 5, 8, 13}


def test_backlog_size_matches_assignment():
    assert 15 <= len(BACKLOG["stories"]) <= 20


def test_stories_are_complete():
    ids = [s["id"] for s in BACKLOG["stories"]]
    assert len(ids) == len(set(ids))
    for s in BACKLOG["stories"]:
        assert s["epic"] in BACKLOG["epics"], s["id"]
        assert s["activity"] in BACKLOG["activities"], s["id"]
        assert s["release"] in {"skeleton", "mvp", "r2", "later"}, s["id"]
        assert s["points"] in FIBONACCI, s["id"]
        assert s.get("type") == "spike" or s["story"].startswith("Как "), s["id"]
        for ac in s["acceptance"]:
            assert re.search(r"Given .+When .+Then ", ac), f"{s['id']}: {ac}"


def test_walking_skeleton_covers_request_to_status():
    skeleton = {s["activity"] for s in BACKLOG["stories"] if s["release"] == "skeleton"}
    assert {"A1", "A2", "A3"} <= skeleton


def test_nfr_are_measurable():
    assert len(NFR) >= 12
    for r in NFR:
        assert re.search(r"\d", r["metric"]), f"{r['id']}: в метрике нет числового порога"
        assert r["verify"].strip(), r["id"]
