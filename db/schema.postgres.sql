-- Схема БД проекта «Практика» для PostgreSQL 16+ (продакшн).
-- Логическая модель совпадает с schema.sql (SQLite, MVP).

CREATE TABLE IF NOT EXISTS curators (
    id          BIGSERIAL PRIMARY KEY,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    department  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id            BIGSERIAL PRIMARY KEY,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    phone         TEXT,
    group_name    TEXT NOT NULL,
    program       TEXT NOT NULL,
    course_year   SMALLINT NOT NULL CHECK (course_year BETWEEN 1 AND 5),
    gpa           NUMERIC(3, 2) CHECK (gpa BETWEEN 0 AND 4),
    skills        TEXT NOT NULL DEFAULT '',
    languages     TEXT NOT NULL DEFAULT '',
    curator_id    BIGINT REFERENCES curators(id),
    consent_pd    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS employers (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    industry        TEXT NOT NULL,
    city            TEXT NOT NULL,
    contact_name    TEXT,
    contact_email   TEXT,
    is_partner      BOOLEAN NOT NULL DEFAULT TRUE,
    agreement_until DATE
);

CREATE TABLE IF NOT EXISTS vacancies (
    id               BIGSERIAL PRIMARY KEY,
    employer_id      BIGINT NOT NULL REFERENCES employers(id),
    title            TEXT NOT NULL,
    kind             TEXT NOT NULL CHECK (kind IN ('internship', 'job')),
    city             TEXT NOT NULL,
    work_format      TEXT NOT NULL CHECK (work_format IN ('office', 'remote', 'hybrid')),
    skills_required  TEXT NOT NULL DEFAULT '',
    slots            INTEGER NOT NULL DEFAULT 1 CHECK (slots > 0),
    salary_from      INTEGER,
    salary_to        INTEGER,
    deadline         DATE NOT NULL,
    status           TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    source           TEXT NOT NULL DEFAULT 'partner',
    source_url       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS applications (
    id            BIGSERIAL PRIMARY KEY,
    student_id    BIGINT NOT NULL REFERENCES students(id),
    vacancy_id    BIGINT NOT NULL REFERENCES vacancies(id),
    status        TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN
                  ('submitted', 'forwarded', 'interview', 'accepted', 'rejected', 'withdrawn')),
    submitted_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    comment       TEXT,
    UNIQUE (student_id, vacancy_id)
);

CREATE TABLE IF NOT EXISTS application_status_history (
    id              BIGSERIAL PRIMARY KEY,
    application_id  BIGINT NOT NULL REFERENCES applications(id),
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    changed_by      TEXT NOT NULL,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    comment         TEXT
);

CREATE TABLE IF NOT EXISTS practice_reports (
    id              BIGSERIAL PRIMARY KEY,
    application_id  BIGINT NOT NULL UNIQUE REFERENCES applications(id),
    due_date        DATE NOT NULL,
    submitted_at    TIMESTAMPTZ,
    grade           SMALLINT CHECK (grade BETWEEN 0 AND 100)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_status ON vacancies(status, deadline);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_history_app ON application_status_history(application_id);
