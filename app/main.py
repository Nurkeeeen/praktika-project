"""REST API «Практика»: база студентов, база вакансий, заявки и сроки отчётов.

Запуск: uvicorn app.main:app --reload  →  http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from app import db
from app.domain import STATUS_LABELS, can_transition, match_score

Status = Literal["submitted", "forwarded", "interview", "accepted", "rejected", "withdrawn"]


class StudentIn(BaseModel):
    full_name: str = Field(min_length=3)
    email: EmailStr
    phone: str | None = None
    group_name: str
    program: str
    course_year: int = Field(ge=1, le=5)
    gpa: float | None = Field(default=None, ge=0, le=4)
    skills: str = ""
    languages: str = "kk;ru"
    curator_id: int | None = None
    consent_pd: bool = Field(description="Согласие на обработку персональных данных — обязательно")


class VacancyIn(BaseModel):
    employer_id: int
    title: str = Field(min_length=3)
    kind: Literal["internship", "job"]
    city: str
    work_format: Literal["office", "remote", "hybrid"]
    skills_required: str = ""
    slots: int = Field(default=1, gt=0)
    salary_from: int | None = None
    salary_to: int | None = None
    deadline: date
    source: str = "partner"
    source_url: str | None = None


class ApplicationIn(BaseModel):
    student_id: int
    vacancy_id: int
    comment: str | None = None


class StatusChange(BaseModel):
    status: Status
    changed_by: str = Field(min_length=2)
    comment: str | None = None


def create_app(db_path: str | Path | None = None) -> FastAPI:
    api = FastAPI(title="Практика API", version="0.1.0",
                  description="Приём и маршрутизация заявок студентов на практику и вакансий партнёров.")
    path = db_path or db.db_path()
    if str(path) != ":memory:" and not Path(path).exists():
        db.create_database(path).close()  # первый запуск — база с демо-данными
    api.state.conn = db.connect(path)

    def get_conn(request: Request) -> sqlite3.Connection:
        return request.app.state.conn

    def one(conn: sqlite3.Connection, sql: str, *args) -> dict:
        row = conn.execute(sql, args).fetchone()
        if row is None:
            raise HTTPException(404, "Не найдено")
        return dict(row)

    @api.get("/health")
    def health():
        return {"status": "ok"}

    # ---------- Студенты ----------
    @api.get("/students")
    def list_students(program: str | None = None, q: str | None = None,
                      conn: sqlite3.Connection = Depends(get_conn)):
        sql, args = "SELECT * FROM students WHERE 1=1", []
        if program:
            sql += " AND program = ?"
            args.append(program)
        if q:
            sql += " AND (full_name LIKE ? OR skills LIKE ?)"
            args += [f"%{q}%", f"%{q}%"]
        return [dict(r) for r in conn.execute(sql + " ORDER BY id", args)]

    @api.get("/students/{student_id}")
    def get_student(student_id: int, conn: sqlite3.Connection = Depends(get_conn)):
        return one(conn, "SELECT * FROM students WHERE id = ?", student_id)

    @api.post("/students", status_code=201)
    def create_student(s: StudentIn, conn: sqlite3.Connection = Depends(get_conn)):
        if not s.consent_pd:
            raise HTTPException(422, "Без согласия на обработку персональных данных запись не создаётся")
        try:
            cur = conn.execute(
                "INSERT INTO students (full_name, email, phone, group_name, program, course_year, gpa, skills,"
                " languages, curator_id, consent_pd) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                (s.full_name, s.email, s.phone, s.group_name, s.program, s.course_year, s.gpa, s.skills,
                 s.languages, s.curator_id))
        except sqlite3.IntegrityError as e:
            raise HTTPException(409, f"Конфликт данных: {e}") from e
        conn.commit()
        return get_student(cur.lastrowid, conn)

    @api.get("/students/{student_id}/matches")
    def student_matches(student_id: int, min_score: float = Query(0.5, ge=0, le=1),
                        conn: sqlite3.Connection = Depends(get_conn)):
        """Открытые вакансии, отсортированные по совпадению навыков."""
        st = get_student(student_id, conn)
        rows = conn.execute(
            "SELECT v.*, e.name AS employer FROM vacancies v JOIN employers e ON e.id = v.employer_id "
            "WHERE v.status = 'open' AND v.deadline >= ?", (date.today().isoformat(),))
        out = []
        for r in rows:
            score = match_score(st["skills"], r["skills_required"])
            if score >= min_score:
                out.append({**dict(r), "match": round(score, 2)})
        return sorted(out, key=lambda v: -v["match"])

    # ---------- Работодатели и вакансии ----------
    @api.get("/employers")
    def list_employers(conn: sqlite3.Connection = Depends(get_conn)):
        return [dict(r) for r in conn.execute("SELECT * FROM employers ORDER BY name")]

    @api.get("/vacancies")
    def list_vacancies(kind: str | None = None, city: str | None = None, skill: str | None = None,
                       open_only: bool = True, conn: sqlite3.Connection = Depends(get_conn)):
        sql = ("SELECT v.*, e.name AS employer FROM vacancies v JOIN employers e ON e.id = v.employer_id "
               "WHERE 1=1")
        args: list = []
        if open_only:
            sql += " AND v.status = 'open'"
        if kind:
            sql += " AND v.kind = ?"
            args.append(kind)
        if city:
            sql += " AND v.city = ?"
            args.append(city)
        if skill:
            sql += " AND v.skills_required LIKE ?"
            args.append(f"%{skill}%")
        return [dict(r) for r in conn.execute(sql + " ORDER BY v.deadline", args)]

    @api.get("/vacancies/{vacancy_id}")
    def get_vacancy(vacancy_id: int, conn: sqlite3.Connection = Depends(get_conn)):
        return one(conn, "SELECT * FROM vacancies WHERE id = ?", vacancy_id)

    @api.post("/vacancies", status_code=201)
    def create_vacancy(v: VacancyIn, conn: sqlite3.Connection = Depends(get_conn)):
        one(conn, "SELECT id FROM employers WHERE id = ?", v.employer_id)
        cur = conn.execute(
            "INSERT INTO vacancies (employer_id, title, kind, city, work_format, skills_required, slots,"
            " salary_from, salary_to, deadline, source, source_url) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (v.employer_id, v.title, v.kind, v.city, v.work_format, v.skills_required, v.slots, v.salary_from,
             v.salary_to, v.deadline.isoformat(), v.source, v.source_url))
        conn.commit()
        return get_vacancy(cur.lastrowid, conn)

    # ---------- Заявки ----------
    @api.post("/applications", status_code=201)
    def create_application(a: ApplicationIn, conn: sqlite3.Connection = Depends(get_conn)):
        get_student(a.student_id, conn)
        vac = get_vacancy(a.vacancy_id, conn)
        if vac["status"] != "open" or vac["deadline"] < date.today().isoformat():
            raise HTTPException(409, "Приём заявок на эту вакансию закрыт")
        try:
            cur = conn.execute("INSERT INTO applications (student_id, vacancy_id, comment) VALUES (?,?,?)",
                               (a.student_id, a.vacancy_id, a.comment))
        except sqlite3.IntegrityError as e:
            raise HTTPException(409, "Студент уже подал заявку на эту вакансию") from e
        conn.execute("INSERT INTO application_status_history (application_id, from_status, to_status, changed_by)"
                     " VALUES (?, NULL, 'submitted', 'student')", (cur.lastrowid,))
        conn.commit()
        return get_application(cur.lastrowid, conn)

    @api.get("/applications/{app_id}")
    def get_application(app_id: int, conn: sqlite3.Connection = Depends(get_conn)):
        row = one(conn, "SELECT * FROM applications WHERE id = ?", app_id)
        return {**row, "status_label": STATUS_LABELS[row["status"]]}

    @api.patch("/applications/{app_id}/status")
    def change_status(app_id: int, body: StatusChange, conn: sqlite3.Connection = Depends(get_conn)):
        current = get_application(app_id, conn)["status"]
        if not can_transition(current, body.status):
            raise HTTPException(409, f"Переход {current} → {body.status} не допускается")
        conn.execute("UPDATE applications SET status = ?, updated_at = datetime('now') WHERE id = ?",
                     (body.status, app_id))
        conn.execute("INSERT INTO application_status_history (application_id, from_status, to_status, changed_by,"
                     " comment) VALUES (?,?,?,?,?)", (app_id, current, body.status, body.changed_by, body.comment))
        conn.commit()
        return get_application(app_id, conn)

    @api.get("/applications/{app_id}/history")
    def application_history(app_id: int, conn: sqlite3.Connection = Depends(get_conn)):
        get_application(app_id, conn)
        return [dict(r) for r in conn.execute(
            "SELECT * FROM application_status_history WHERE application_id = ? ORDER BY changed_at, id", (app_id,))]

    # ---------- Отчёты и метрики ----------
    @api.get("/reports/overdue")
    def overdue_reports(today: date | None = None, conn: sqlite3.Connection = Depends(get_conn)):
        """Отчёты о практике, срок которых прошёл, а отчёт не сдан."""
        d = (today or date.today()).isoformat()
        return [dict(r) for r in conn.execute(
            "SELECT r.*, s.full_name AS student, s.email, c.full_name AS curator, v.title AS vacancy "
            "FROM practice_reports r JOIN applications a ON a.id = r.application_id "
            "JOIN students s ON s.id = a.student_id JOIN vacancies v ON v.id = a.vacancy_id "
            "LEFT JOIN curators c ON c.id = s.curator_id "
            "WHERE r.submitted_at IS NULL AND r.due_date < ? ORDER BY r.due_date", (d,))]

    @api.get("/stats")
    def stats(conn: sqlite3.Connection = Depends(get_conn)):
        """Метрики из бизнес-кейса: статусы заявок и доля заявок с прослеживаемой историей."""
        by_status = {r["status"]: r["n"] for r in conn.execute(
            "SELECT status, COUNT(*) AS n FROM applications GROUP BY status")}
        total = sum(by_status.values())
        tracked = conn.execute(
            "SELECT COUNT(DISTINCT application_id) FROM application_status_history").fetchone()[0]
        return {
            "students": conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
            "open_vacancies": conn.execute("SELECT COUNT(*) FROM vacancies WHERE status='open'").fetchone()[0],
            "applications": total,
            "by_status": by_status,
            "tracked_share": round(tracked / total, 3) if total else None,
        }

    return api


app = create_app()
