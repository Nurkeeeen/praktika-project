from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import create_app

FUTURE = (date.today() + timedelta(days=30)).isoformat()


@pytest.fixture()
def client(tmp_path):
    path = tmp_path / "test.db"
    db.create_database(path).close()
    return TestClient(create_app(path))


def new_vacancy(client, **kw):
    body = {"employer_id": 1, "title": "Стажёр Python", "kind": "internship", "city": "Алматы",
            "work_format": "hybrid", "skills_required": "Python;SQL;Git", "deadline": FUTURE, **kw}
    r = client.post("/vacancies", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def new_student(client, **kw):
    body = {"full_name": "Тест Студент", "email": "test.student@example.org", "group_name": "ИС-231",
            "program": "Информационные системы", "course_year": 4, "skills": "Python;SQL",
            "consent_pd": True, **kw}
    r = client.post("/students", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_seed_loaded(client):
    stats = client.get("/stats").json()
    assert stats["students"] == 40
    assert stats["applications"] == 36
    assert stats["tracked_share"] == 1.0


def test_student_requires_pd_consent(client):
    r = client.post("/students", json={"full_name": "Без Согласия", "email": "no@example.org",
                                       "group_name": "ИС-231", "program": "ИС", "course_year": 3,
                                       "consent_pd": False})
    assert r.status_code == 422


def test_duplicate_student_email_conflicts(client):
    new_student(client)
    r = client.post("/students", json={"full_name": "Другой", "email": "test.student@example.org",
                                       "group_name": "ИС-231", "program": "ИС", "course_year": 3,
                                       "consent_pd": True})
    assert r.status_code == 409


def test_application_lifecycle_and_history(client):
    st, vac = new_student(client), new_vacancy(client)
    app_ = client.post("/applications", json={"student_id": st["id"], "vacancy_id": vac["id"]}).json()
    assert app_["status"] == "submitted"
    for status in ("forwarded", "interview", "accepted"):
        r = client.patch(f"/applications/{app_['id']}/status", json={"status": status, "changed_by": "methodist"})
        assert r.status_code == 200, r.text
    history = client.get(f"/applications/{app_['id']}/history").json()
    assert [h["to_status"] for h in history] == ["submitted", "forwarded", "interview", "accepted"]


def test_invalid_transition_rejected(client):
    st, vac = new_student(client), new_vacancy(client)
    app_ = client.post("/applications", json={"student_id": st["id"], "vacancy_id": vac["id"]}).json()
    r = client.patch(f"/applications/{app_['id']}/status", json={"status": "accepted", "changed_by": "methodist"})
    assert r.status_code == 409


def test_duplicate_application_rejected(client):
    st, vac = new_student(client), new_vacancy(client)
    body = {"student_id": st["id"], "vacancy_id": vac["id"]}
    assert client.post("/applications", json=body).status_code == 201
    assert client.post("/applications", json=body).status_code == 409


def test_closed_vacancy_rejects_application(client):
    st = new_student(client)
    vac = new_vacancy(client, deadline=(date.today() - timedelta(days=1)).isoformat())
    r = client.post("/applications", json={"student_id": st["id"], "vacancy_id": vac["id"]})
    assert r.status_code == 409


def test_matches_ranked_by_skills(client):
    st = new_student(client, skills="Python;SQL;Git")
    vac = new_vacancy(client)
    matches = client.get(f"/students/{st['id']}/matches").json()
    assert matches[0]["id"] == vac["id"]
    assert matches[0]["match"] == 1.0


def test_overdue_reports(client):
    overdue = client.get("/reports/overdue", params={"today": "2027-12-31"}).json()
    assert all(r["submitted_at"] is None for r in overdue)
    assert client.get("/reports/overdue", params={"today": "2000-01-01"}).json() == []
