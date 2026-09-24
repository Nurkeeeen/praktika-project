# Как мы работаем

Соглашения зафиксированы в ЛЗ 2 (рабочее пространство проекта).

## Задачи

- Типы: `Epic`, `Story`, `Task`, `Bug`, `Spike`, `ADR` — шаблоны в `.github/ISSUE_TEMPLATE/`.
- Название: `[ЗС-N] Краткое описание`, где N — номер лабораторного занятия.
- Поля доски GitHub Projects: Приоритет (High/Medium/Low), Итерация (неделя ЗС), Оценка (Story Points), Роль-исполнитель.
- Статусы доски: `Backlog → Ready → In Progress → In Review → Done`. Тестирование входит в In Review.

## Ветки

- `main` защищена: только через pull request, 1 одобрение, зелёный CI.
- Рабочие ветки: `type/зсN-краткое-описание`, например `feature/зс4-story-map`, `fix/зс9-баг-статусов`,
  `docs/зс3-бизнес-кейс`.

## Pull request

1. В описании — ссылка на задачу (`Closes #12`).
2. `ruff check .` и `pytest` проходят локально.
3. Если меняется архитектура или процесс — новый ADR в `docs/adr/` по шаблону `0000-template.md`.
4. Если менялись допущения финмодели — пересобрать `python finance/generate_xlsx.py` и
   `python scripts/build_lz3_docs.py`.
5. Если менялись `docs/requirements/*.yaml` — пересобрать `python scripts/build_lz4_docs.py` (story map
   пересобирается вместе с документом); изменение после тега `baseline-v1` — только через Change Request.

## Данные

Реальные персональные данные студентов в репозиторий не коммитим. Для демо — только `scripts/generate_demo_data.py`.
