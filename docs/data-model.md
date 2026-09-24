# Модель данных

Схема: [db/schema.sql](../db/schema.sql) (SQLite, MVP), [db/schema.postgres.sql](../db/schema.postgres.sql) (продакшн).

```mermaid
erDiagram
    curators {
        int id PK
        text full_name
        text email UK
        text department
    }
    students {
        int id PK
        text full_name
        text email UK
        text group_name
        text program
        int course_year
        real gpa
        text skills "через ;"
        text languages "kk;ru;en"
        int curator_id FK
        int consent_pd "согласие на ПДн"
    }
    employers {
        int id PK
        text name UK
        text industry
        text city
        int is_partner
        date agreement_until
    }
    vacancies {
        int id PK
        int employer_id FK
        text title
        text kind "internship | job"
        text work_format "office | remote | hybrid"
        text skills_required
        int slots
        date deadline
        text status "open | closed"
        text source "partner | hh.kz | ..."
    }
    applications {
        int id PK
        int student_id FK
        int vacancy_id FK
        text status
        datetime submitted_at
        datetime updated_at
    }
    application_status_history {
        int id PK
        int application_id FK
        text from_status
        text to_status
        text changed_by
        datetime changed_at
    }
    practice_reports {
        int id PK
        int application_id FK
        date due_date
        datetime submitted_at
        int grade
    }
    curators ||--o{ students : "курирует"
    students ||--o{ applications : "подаёт"
    employers ||--o{ vacancies : "публикует"
    vacancies ||--o{ applications : "получает"
    applications ||--o{ application_status_history : "история"
    applications ||--o| practice_reports : "отчёт"
```

## Правила

- Один студент — одна заявка на вакансию (`UNIQUE (student_id, vacancy_id)`).
- Заявку нельзя подать после `deadline` или на закрытую вакансию.
- Переходы статусов: см. `app/domain.py` (`TRANSITIONS`). Финальные: `accepted`, `rejected`, `withdrawn`.
- Студент без согласия на обработку ПДн (`consent_pd = 0`) не создаётся.

## Наборы данных

| Файл | Что | Происхождение |
|---|---|---|
| `db/seed/*.csv` | демо-база студентов, партнёров, вакансий, заявок | синтетика, `scripts/generate_demo_data.py` |
| `db/market/hh_pm_vacancies_2026-09-10.csv` | 10 вакансий PM-ролей в Казахстане | hh.kz, выборка ЛЗ 1 |
| `db/market/pm_requirements_frequency.csv` | частотная таблица требований | ЛЗ 1, часть 2 |
