"""НФТ, которые проверяются уже на прототипе (auto: true в docs/requirements/nfr.yaml)."""

import time
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    path = tmp_path / "nfr.db"
    db.create_database(path).close()
    return TestClient(create_app(path))


def test_nfr01_read_latency_smoke(client):
    """NFR-01 (smoke): p95 чтения списка вакансий ≤ 200 мс на 200 запросов к демо-базе."""
    timings = []
    for _ in range(200):
        t0 = time.perf_counter()
        assert client.get("/vacancies", params={"open_only": False}).status_code == 200
        timings.append(time.perf_counter() - t0)
    p95 = sorted(timings)[int(len(timings) * 0.95) - 1]
    assert p95 <= 0.2, f"p95 = {p95 * 1000:.0f} мс"


def test_nfr08_every_status_change_is_audited(client):
    """NFR-08: каждое изменение статуса оставляет запись в журнале (кто, было, стало)."""
    vac = client.post("/vacancies", json={
        "employer_id": 1, "title": "Стажёр QA", "kind": "internship", "city": "Астана", "work_format": "office",
        "deadline": (date.today() + timedelta(days=10)).isoformat()}).json()
    app_ = client.post("/applications", json={"student_id": 1, "vacancy_id": vac["id"]}).json()
    client.patch(f"/applications/{app_['id']}/status", json={"status": "forwarded", "changed_by": "methodist"})
    client.patch(f"/applications/{app_['id']}/status", json={"status": "rejected", "changed_by": "employer"})
    hist = client.get(f"/applications/{app_['id']}/history").json()
    assert [(h["from_status"], h["to_status"], h["changed_by"]) for h in hist] == [
        (None, "submitted", "student"), ("submitted", "forwarded", "methodist"), ("forwarded", "rejected", "employer")]
    assert client.get("/stats").json()["tracked_share"] == 1.0


def test_nfr10_no_profile_without_consent(client):
    """NFR-10: профиль студента не создаётся без согласия на обработку ПДн."""
    r = client.post("/students", json={"full_name": "Без Согласия", "email": "x@example.org", "group_name": "ИС-231",
                                       "program": "ИС", "course_year": 3, "consent_pd": False})
    assert r.status_code == 422
