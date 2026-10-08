"""Расчёты ЗС 5: трудоёмкость WBS, capacity команды по неделям, покрытие инкрементов, сценарии.

Источники — wbs.yaml и team.yaml рядом. Запуск: python docs/planning/planning.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
WBS = yaml.safe_load((HERE / "wbs.yaml").read_text(encoding="utf-8"))
TEAM = yaml.safe_load((HERE / "team.yaml").read_text(encoding="utf-8"))
WEEK1 = date(2026, 9, 7)

# Сокращение скоупа, которое предлагаем через Change Request CR-001 (часы, которые уходят из семестра)
SCOPE_CUTS = [
    ("1.3.1", 10, "PostgreSQL — после пилота; на пилоте остаётся SQLite (нагрузка 30–40 заявок/нед, ADR-003 пересмотреть)"),
    ("1.4.3", 8, "Кабинет куратора (S11) — в релиз 2; до этого кураторы получают список просрочек письмом"),
    ("1.5.1", 6, "Вместо SSO — вход по одноразовой ссылке на почту вуза (спайк S19 решает окончательно)"),
    ("1.2.3", 6, "Макеты — эскизы от руки и сразу HTML, без отдельного прототипа"),
]


def week_start(k: int) -> date:
    return WEEK1 + timedelta(weeks=k - 1)


def leaves() -> list[dict]:
    return [c for item in WBS["items"] for c in item["children"]]


def wbs_total() -> float:
    return sum(c["hours"] for c in leaves())


def hours_by(key: str) -> dict:
    out: dict = {}
    for c in leaves():
        out[c[key]] = out.get(c[key], 0) + c["hours"]
    return out


@dataclass
class Capacity:
    weeks: list[tuple[str, float]]   # (метка недели, чистые часы команды)

    @property
    def total(self) -> float:
        return sum(h for _, h in self.weeks)


def capacity(hours_per_week: float | None = None) -> Capacity:
    c = TEAM["capacity"]
    hpw = c["hours_per_week"] if hours_per_week is None else hours_per_week
    people = len(TEAM["team"])
    net = c["focus_factor"] * (1 - c["reserve"])
    weeks = []
    for k in range(c["planning_start_week"], c["last_week"] + 1):
        f = c["week_factors"].get(k, 1.0)
        weeks.append((f"нед. {k}", people * hpw * f * net))
    w = c["winter"]
    winter_h = w["hours_per_week"] * hpw / c["hours_per_week"]  # каникулы масштабируем вместе со сценарием
    for i in range(w["weeks"]):
        weeks.append((f"янв. {i + 1}", people * winter_h * net))
    return Capacity(weeks)


def increment_weeks(inc: dict) -> list[str]:
    a, b = inc["weeks"]
    labels = [f"нед. {k}" for k in range(a, b + 1)]
    if inc["id"] == 3:
        labels += [f"янв. {i + 1}" for i in range(TEAM["capacity"]["winter"]["weeks"])]
    return labels


def coverage(hours_per_week: float | None = None, cuts: bool = False) -> list[dict]:
    """Покрытие каждого инкремента: ongoing-работы делятся по неделям поровну."""
    cap = capacity(hours_per_week)
    cut = {wid: h for wid, h, _ in SCOPE_CUTS} if cuts else {}
    by_inc: dict = {}
    for c in leaves():
        by_inc[c["inc"]] = by_inc.get(c["inc"], 0) + c["hours"] - cut.get(c["id"], 0)
    ongoing = by_inc.get("ongoing", 0)
    semester_weeks = [lbl for lbl, _ in cap.weeks if lbl.startswith("нед.")]
    per_week_overhead = ongoing / len(semester_weeks)
    rows = []
    for inc in TEAM["increments"]:
        labels = increment_weeks(inc)
        cap_h = sum(h for lbl, h in cap.weeks if lbl in labels)
        overhead = per_week_overhead * sum(1 for lbl in labels if lbl.startswith("нед."))
        need = by_inc.get(inc["id"], 0) + overhead
        rows.append({"inc": inc["id"], "name": inc["name"], "capacity": cap_h, "need": need,
                     "features": by_inc.get(inc["id"], 0), "overhead": overhead, "coverage": cap_h / need})
    return rows


def required_hours_per_week(cuts: bool = False) -> float:
    """Сколько часов в неделю на человека нужно, чтобы capacity = вся работа."""
    need = wbs_total() - (sum(h for _, h, _ in SCOPE_CUTS) if cuts else 0)
    return need / capacity(1).total


SCENARIOS = [(8, False), (10, False), (15, False), (15, True), (20, False)]


if __name__ == "__main__":
    print(f"WBS: {wbs_total():.0f} ч; по инкрементам {hours_by('inc')}")
    cap = capacity()
    print(f"Capacity (база): {cap.total:.0f} ч")
    for lbl, h in cap.weeks:
        print(f"  {lbl}: {h:.1f}")
    for hpw, cuts in SCENARIOS:
        c = capacity(hpw).total
        need = wbs_total() - (sum(h for _, h, _ in SCOPE_CUTS) if cuts else 0)
        print(f"{hpw} ч/нед{' + CR-001' if cuts else ''}: capacity {c:.0f} / нужно {need:.0f} = {c / need:.0%}")
    print(f"нужно ч/нед на человека: {required_hours_per_week():.1f}; с CR-001: {required_hours_per_week(True):.1f}")
    for r in coverage(15, True):
        print(r)
