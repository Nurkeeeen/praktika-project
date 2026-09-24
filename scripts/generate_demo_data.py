"""Генерирует синтетические демо-данные в db/seed/*.csv.

Все люди, e-mail, телефоны и компании-партнёры ВЫМЫШЛЕНЫ (закон РК о персональных
данных: реальные ПДн студентов в репозиторий не кладём). Генерация детерминирована
(seed=42), поэтому повторный запуск даёт те же файлы.

Запуск: python scripts/generate_demo_data.py
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parents[1] / "db" / "seed"
rnd = random.Random(42)

FIRST = ["Әлібек", "Нұрлан", "Айгерім", "Дана", "Ерлан", "Мадина", "Арман", "Жансая", "Тимур", "Аружан",
         "Данияр", "Камила", "Санжар", "Әсел", "Ильяс", "Томирис", "Алихан", "Диана", "Бауыржан", "Айым"]
LAST = ["Сейтқали", "Жұмабай", "Оспан", "Тлеу", "Қасым", "Ахмет", "Бекқожа", "Нұржан", "Смағұл", "Ержан",
        "Мұқан", "Сәрсен", "Кенже", "Әбіл", "Төлеу"]
PROGRAMS = {"ИС": "Информационные системы", "DS": "Data Science"}
SKILLS = ["Python", "SQL", "Git", "Excel", "Power BI", "Jira", "JavaScript", "Java", "Linux", "Docker",
          "Figma", "английский B1", "Pandas", "REST API", "тестирование", "Agile/Scrum", "1С", "C#"]
CITIES = ["Алматы", "Астана", "Шымкент", "Караганда"]

EMPLOYERS = [
    ("ТОО «Демо Софт» (демо)", "Разработка ПО", "Алматы"),
    ("АО «Демо Банк» (демо)", "Финансы", "Алматы"),
    ("ТОО «Демо Телеком» (демо)", "Телеком", "Астана"),
    ("ТОО «Демо Логистика» (демо)", "Логистика", "Караганда"),
    ("ТОО «Демо Ритейл» (демо)", "Ретейл", "Алматы"),
    ("ГУ «Демо Цифровой центр» (демо)", "Госсектор", "Астана"),
    ("ТОО «Демо Аналитика» (демо)", "Консалтинг / BI", "Алматы"),
    ("ТОО «Демо Агро» (демо)", "Агро", "Шымкент"),
    ("ТОО «Демо EdTech» (демо)", "Образование", "Астана"),
    ("ТОО «Демо GameDev» (демо)", "Игры", "Алматы"),
]

VACANCY_TEMPLATES = [
    ("Стажёр Python-разработчик", "internship", "Python;Git;SQL;REST API"),
    ("Стажёр аналитик данных", "internship", "SQL;Excel;Power BI;Pandas"),
    ("Стажёр QA-инженер", "internship", "тестирование;Jira;SQL"),
    ("Стажёр бизнес-аналитик", "internship", "Excel;SQL;Jira;Agile/Scrum"),
    ("Junior Data Scientist", "job", "Python;Pandas;SQL;английский B1"),
    ("Стажёр Frontend-разработчик", "internship", "JavaScript;Git;Figma"),
    ("Стажёр DevOps", "internship", "Linux;Docker;Git"),
    ("Помощник проектного менеджера", "internship", "Jira;Excel;Agile/Scrum;английский B1"),
    ("Junior Java-разработчик", "job", "Java;SQL;Git"),
    ("Стажёр 1С-программист", "internship", "1С;SQL"),
    ("Junior .NET-разработчик", "job", "C#;SQL;Git"),
]

TODAY = date(2026, 9, 24)


def write(name: str, header: list[str], rows: list[list]) -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    with open(SEED_DIR / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} строк")


def main() -> None:
    curators = [
        [1, "Куратор Демо Первый", "curator1@example.org", "Кафедра информационных систем"],
        [2, "Куратор Демо Второй", "curator2@example.org", "Кафедра информационных систем"],
        [3, "Куратор Демо Третий", "curator3@example.org", "Кафедра Data Science"],
        [4, "Куратор Демо Четвёртый", "curator4@example.org", "Кафедра Data Science"],
    ]
    write("curators.csv", ["id", "full_name", "email", "department"], curators)

    students = []
    for i in range(1, 41):
        code = rnd.choice(list(PROGRAMS))
        year = rnd.choice([3, 4])
        students.append([
            i,
            f"{rnd.choice(LAST)} {rnd.choice(FIRST)}",
            f"student{i:03d}@example.org",
            f"+7 700 000 {i:04d}",
            f"{code}-{26 - year}{rnd.randint(1, 3)}",
            PROGRAMS[code],
            year,
            round(rnd.uniform(2.3, 4.0), 2),
            ";".join(sorted(rnd.sample(SKILLS, rnd.randint(3, 6)))),
            ";".join(["kk", "ru"] + (["en"] if rnd.random() < 0.5 else [])),
            (1 if code == "ИС" else 3) + rnd.randint(0, 1),
            1,
        ])
    write("students.csv", ["id", "full_name", "email", "phone", "group_name", "program", "course_year", "gpa",
                           "skills", "languages", "curator_id", "consent_pd"], students)

    employers = []
    for i, (nm, ind, city) in enumerate(EMPLOYERS, start=1):
        employers.append([i, nm, ind, city, f"HR Демо {i}", f"hr{i}@example.com", 1,
                          (TODAY + timedelta(days=rnd.randint(90, 720))).isoformat()])
    write("employers.csv", ["id", "name", "industry", "city", "contact_name", "contact_email", "is_partner",
                            "agreement_until"], employers)

    vacancies = []
    for i in range(1, 25):
        emp = rnd.choice(employers)
        title, kind, skills = rnd.choice(VACANCY_TEMPLATES)
        deadline = TODAY + timedelta(days=rnd.randint(-20, 80))
        salary = (None, None) if kind == "internship" and rnd.random() < 0.6 else \
            (rnd.choice([150, 200, 250, 300]) * 1000, rnd.choice([350, 400, 500]) * 1000)
        vacancies.append([
            i, emp[0], title, kind, emp[3], rnd.choice(["office", "remote", "hybrid"]), skills,
            rnd.randint(1, 4), salary[0], salary[1], deadline.isoformat(),
            "open" if deadline >= TODAY else "closed", "partner", None,
        ])
    write("vacancies.csv", ["id", "employer_id", "title", "kind", "city", "work_format", "skills_required",
                            "slots", "salary_from", "salary_to", "deadline", "status", "source", "source_url"],
          vacancies)

    # Заявки и история статусов: каждая заявка проходит допустимую цепочку переходов
    paths = [["submitted"], ["submitted", "forwarded"], ["submitted", "forwarded", "interview"],
             ["submitted", "forwarded", "interview", "accepted"], ["submitted", "forwarded", "rejected"],
             ["submitted", "withdrawn"]]
    weights = [3, 3, 2, 3, 2, 1]
    applications, history, reports = [], [], []
    pairs = set()
    app_id = hist_id = rep_id = 0
    while app_id < 36:
        st, vac = rnd.choice(students), rnd.choice(vacancies)
        if (st[0], vac[0]) in pairs:
            continue
        pairs.add((st[0], vac[0]))
        app_id += 1
        path = rnd.choices(paths, weights)[0]
        t = date.fromisoformat(vac[10]) - timedelta(days=rnd.randint(5, 25))
        submitted = t
        prev = None
        for step in path:
            hist_id += 1
            who = "student" if step in ("submitted", "withdrawn") else "methodist"
            history.append([hist_id, app_id, prev, step, who, f"{t.isoformat()} 10:00:00", None])
            prev = step
            t += timedelta(days=rnd.randint(1, 6))
        applications.append([app_id, st[0], vac[0], path[-1], f"{submitted.isoformat()} 10:00:00",
                             history[-1][5], None])
        if path[-1] == "accepted":
            rep_id += 1
            due = TODAY + timedelta(days=rnd.randint(-10, 60))
            done = due < TODAY and rnd.random() < 0.5
            reports.append([rep_id, app_id, due.isoformat(),
                             f"{(due - timedelta(days=1)).isoformat()} 18:00:00" if done else None,
                             rnd.randint(70, 98) if done else None])
    write("applications.csv", ["id", "student_id", "vacancy_id", "status", "submitted_at", "updated_at", "comment"],
          applications)
    write("application_status_history.csv", ["id", "application_id", "from_status", "to_status", "changed_by",
                                             "changed_at", "comment"], history)
    write("practice_reports.csv", ["id", "application_id", "due_date", "submitted_at", "grade"], reports)


if __name__ == "__main__":
    main()
