"""Критерии приёмки ЗС 5–6 как код."""

import csv
import sys
from datetime import date
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "planning"))
import planning as pl  # noqa: E402


def test_wbs_three_levels_unique_ids_and_dictionary():
    ids = [c["id"] for c in pl.leaves()]
    assert len(ids) == len(set(ids))
    assert all(i.count(".") == 2 for i in ids), "все листья — 3-й уровень"
    assert len(pl.WBS["dictionary"]) == 5
    assert set(pl.WBS["dictionary"]) <= set(ids)


def test_three_increments_with_milestones_and_done_criteria():
    incs = pl.TEAM["increments"]
    ms = {m["id"] for m in pl.TEAM["milestones"]}
    assert len(incs) == 3
    for inc in incs:
        assert inc["milestone"] in ms and inc["done"] and inc["goal"]


def test_external_dependencies_have_owner_and_date():
    deps = pl.TEAM["dependencies"]
    owners = {t["id"] for t in pl.TEAM["team"]}
    assert len(deps) >= 3
    for d in deps:
        assert d["owner"] in owners, d["id"]
        assert date.fromisoformat(d["confirm_by"]), d["id"]


def test_capacity_is_below_full_scope_at_10_hours():
    # главный вывод ЛЗ 5: при 10 ч/нед команда не успевает весь скоуп
    assert pl.capacity(10).total < pl.wbs_total()
    assert pl.required_hours_per_week() > 15


def test_notebook_is_reproducible_and_executed():
    nb = nbformat.read(ROOT / "analytics" / "monte_carlo.ipynb", as_version=4)
    src = "\n".join(c.source for c in nb.cells if c.cell_type == "code")
    assert "SEED = 2026" in src and "RUNS = 10_000" in src
    assert all(c.get("execution_count") for c in nb.cells if c.cell_type == "code"), "notebook выполнен"
    outputs = "\n".join(o.get("text", "") for c in nb.cells for o in c.get("outputs", []))
    for p in ("P50", "P70", "P85", "P95"):
        assert p in outputs


def test_planning_poker_has_ten_stories():
    rows = list(csv.DictReader(open(ROOT / "analytics" / "planning_poker.csv", encoding="utf-8")))
    assert len(rows) == 10
