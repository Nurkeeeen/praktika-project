"""Бизнес-правила: жизненный цикл заявки и подбор вакансий под студента."""

from __future__ import annotations

# Допустимые переходы статусов заявки. Финальные статусы переходов не имеют.
TRANSITIONS: dict[str, set[str]] = {
    "submitted": {"forwarded", "rejected", "withdrawn"},
    "forwarded": {"interview", "rejected", "withdrawn"},
    "interview": {"accepted", "rejected", "withdrawn"},
    "accepted": set(),
    "rejected": set(),
    "withdrawn": set(),
}

STATUS_LABELS = {
    "submitted": "Подана",
    "forwarded": "Передана работодателю",
    "interview": "Собеседование",
    "accepted": "Принят(а) на практику",
    "rejected": "Отказ",
    "withdrawn": "Отозвана студентом",
}


def can_transition(current: str, new: str) -> bool:
    return new in TRANSITIONS.get(current, set())


def parse_skills(value: str | None) -> set[str]:
    return {s.strip().lower() for s in (value or "").split(";") if s.strip()}


def match_score(student_skills: str, vacancy_skills: str) -> float:
    """Доля требуемых навыков вакансии, которые есть у студента (0..1)."""
    need = parse_skills(vacancy_skills)
    if not need:
        return 0.0
    return len(need & parse_skills(student_skills)) / len(need)
