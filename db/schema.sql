-- Схема БД проекта «Практика» (SQLite, MVP).
-- Для продакшна та же модель в schema.postgres.sql (см. docs/adr/0003-database.md).

PRAGMA foreign_keys = ON;

-- Кураторы практики от университета
CREATE TABLE IF NOT EXISTS curators (
    id          INTEGER PRIMARY KEY,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    department  TEXT NOT NULL
);

-- База студентов
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT,
    group_name    TEXT NOT NULL,
    program       TEXT NOT NULL,                -- образовательная программа
    course_year   INTEGER NOT NULL CHECK (course_year BETWEEN 1 AND 5),
    gpa           REAL CHECK (gpa BETWEEN 0 AND 4),
    skills        TEXT NOT NULL DEFAULT '',     -- навыки через ';'
    languages     TEXT NOT NULL DEFAULT '',     -- kk;ru;en
    curator_id    INTEGER REFERENCES curators(id),
    consent_pd    INTEGER NOT NULL DEFAULT 0 CHECK (consent_pd IN (0, 1)),  -- согласие на обработку ПДн
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Работодатели (партнёры карьерного центра)
CREATE TABLE IF NOT EXISTS employers (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    industry        TEXT NOT NULL,
    city            TEXT NOT NULL,
    contact_name    TEXT,
    contact_email   TEXT,
    is_partner      INTEGER NOT NULL DEFAULT 1 CHECK (is_partner IN (0, 1)),
    agreement_until TEXT                         -- срок договора о практике (YYYY-MM-DD)
);

-- База вакансий и мест практики
CREATE TABLE IF NOT EXISTS vacancies (
    id               INTEGER PRIMARY KEY,
    employer_id      INTEGER NOT NULL REFERENCES employers(id),
    title            TEXT NOT NULL,
    kind             TEXT NOT NULL CHECK (kind IN ('internship', 'job')),
    city             TEXT NOT NULL,
    work_format      TEXT NOT NULL CHECK (work_format IN ('office', 'remote', 'hybrid')),
    skills_required  TEXT NOT NULL DEFAULT '',   -- навыки через ';'
    slots            INTEGER NOT NULL DEFAULT 1 CHECK (slots > 0),
    salary_from      INTEGER,
    salary_to        INTEGER,
    deadline         TEXT NOT NULL,              -- приём заявок до (YYYY-MM-DD)
    status           TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    source           TEXT NOT NULL DEFAULT 'partner',  -- partner | hh.kz | telegram | ...
    source_url       TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Заявки студентов на вакансии
CREATE TABLE IF NOT EXISTS applications (
    id            INTEGER PRIMARY KEY,
    student_id    INTEGER NOT NULL REFERENCES students(id),
    vacancy_id    INTEGER NOT NULL REFERENCES vacancies(id),
    status        TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN
                  ('submitted', 'forwarded', 'interview', 'accepted', 'rejected', 'withdrawn')),
    submitted_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    comment       TEXT,
    UNIQUE (student_id, vacancy_id)
);

-- История статусов: даёт метрику «доля заявок с прослеживаемым статусом»
CREATE TABLE IF NOT EXISTS application_status_history (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER NOT NULL REFERENCES applications(id),
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    changed_by      TEXT NOT NULL,
    changed_at      TEXT NOT NULL DEFAULT (datetime('now')),
    comment         TEXT
);

-- Отчёты о практике и их сроки
CREATE TABLE IF NOT EXISTS practice_reports (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER NOT NULL UNIQUE REFERENCES applications(id),
    due_date        TEXT NOT NULL,
    submitted_at    TEXT,
    grade           INTEGER CHECK (grade BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_status ON vacancies(status, deadline);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_history_app ON application_status_history(application_id);
