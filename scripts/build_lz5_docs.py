"""Собирает ЛЗ 5 (WBS, словарь, план релизов, зависимости, топология и RACI, capacity) в .docx и .md.

Данные — docs/planning/wbs.yaml и team.yaml, расчёты — docs/planning/planning.py.
Запуск: python scripts/build_lz5_docs.py
"""

from __future__ import annotations

import sys
import textwrap
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "planning"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(PLAN))
import planning as pl  # noqa: E402
from build_story_map import font  # noqa: E402
from docgen import Doc  # noqa: E402

DOCX_OUT = ROOT / "docs" / "labs" / "ЛЗ5_WBS_релизы_зависимости.docx"
MD_OUT = ROOT / "docs" / "lz5-planning.md"
TEAM, WBS = pl.TEAM, pl.WBS
OWNER = {t["id"]: t["name"] for t in TEAM["team"]}
STATUS = {"done": "сделано", "in_progress": "в работе", "todo": "впереди"}
INC = {1: "Инкремент 1", 2: "Инкремент 2", 3: "Инкремент 3", "ongoing": "весь семестр", "done": "—"}
# палитра графиков (эталонная палитра dataviz: синий, оранжевый; серый — для «нужно»)
BLUE, ORANGE, GREY, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#898781", "#0b0b0b", "#52514e", "#e1e0d9"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#c3c2b7",
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})


def d(s: str) -> date:
    return date.fromisoformat(s)


# ---------------------------------------------------------------- диаграммы
def draw_wbs(path: Path) -> None:
    cols = WBS["items"]
    col_w, box_w, gap, top = 270, 250, 10, 150
    width = len(cols) * col_w + 40
    leaf_h = 74
    height = top + 70 + max(len(c["children"]) for c in cols) * (leaf_h + gap) + 90
    img = Image.new("RGB", (width, height), "white")
    g = ImageDraw.Draw(img)
    fill = {"done": "#e9ecef", "in_progress": "#fff3bf", "todo": "#ffffff"}
    total = pl.wbs_total()
    root_w = 520
    rx = (width - root_w) // 2
    g.rounded_rectangle([rx, 20, rx + root_w, 80], 10, fill="#1f4e79")
    g.text((rx + 16, 30), WBS["project"], font=font(20, True), fill="white")
    g.text((rx + 16, 56), f"осталось {total:.0f} ч работы", font=font(14), fill="#dbe7f3")
    g.line([width // 2, 80, width // 2, 110], fill="#868e96", width=2)
    g.line([20 + col_w // 2 - 10, 110, 20 + (len(cols) - 1) * col_w + col_w // 2 - 10, 110], fill="#868e96", width=2)
    for i, item in enumerate(cols):
        x = 20 + i * col_w
        cx = x + box_w // 2
        g.line([cx, 110, cx, top - 10], fill="#868e96", width=2)
        hrs = sum(c["hours"] for c in item["children"])
        g.rounded_rectangle([x, top - 10, x + box_w, top + 50], 8, fill="#d0ebff", outline="#4dabf7")
        g.text((x + 10, top - 2), f"{item['id']} {item['name']}", font=font(14, True), fill="#0b4a80")
        g.text((x + 10, top + 24), f"{hrs:.0f} ч", font=font(13), fill="#0b4a80")
        for j, c in enumerate(item["children"]):
            y = top + 70 + j * (leaf_h + gap)
            g.line([x + 8, top + 50, x + 8, y + leaf_h // 2], fill="#ced4da", width=2)
            g.line([x + 8, y + leaf_h // 2, x + 18, y + leaf_h // 2], fill="#ced4da", width=2)
            g.rounded_rectangle([x + 18, y, x + box_w, y + leaf_h], 7, fill=fill[c["status"]], outline="#adb5bd")
            name = textwrap.fill(c["name"], 30)
            g.multiline_text((x + 26, y + 6), f"{c['id']}  {name}", font=font(12), fill="#212529", spacing=2)
            g.text((x + box_w - 8, y + leaf_h - 18), f"{c['hours']:.0f} ч", font=font(12, True), fill="#495057",
                   anchor="ra")
    ly = height - 40
    for k, (st, lbl) in enumerate([("done", "сделано"), ("in_progress", "в работе"), ("todo", "впереди")]):
        lx = 20 + k * 160
        g.rectangle([lx, ly, lx + 18, ly + 18], fill=fill[st], outline="#adb5bd")
        g.text((lx + 26, ly), lbl, font=font(14), fill="#495057")
    img.save(path)


def draw_releases(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 3.6), dpi=150)
    colors = [BLUE, ORANGE, "#1baf7a"]
    for i, inc in enumerate(TEAM["increments"]):
        a, b = inc["weeks"]
        start, end = pl.week_start(a), pl.week_start(b + 1)
        y = len(TEAM["increments"]) - i
        ax.barh(y, (end - start).days, left=start, height=0.5, color=colors[i])
        ax.text(start, y + 0.34, f"Инкремент {inc['id']}: {inc['name']} · нед. {a}–{b}", ha="left", va="bottom",
                color=INK, fontsize=9.5, fontweight="bold")
        if inc["id"] == 3:
            w0 = date(2027, 1, 18)
            ax.barh(y, 14, left=w0, height=0.5, color=colors[i], alpha=0.45)
            ax.text(w0 + (date(2027, 2, 1) - w0) / 2, y + 0.34, "каникулы", ha="center", va="bottom", fontsize=8.5,
                    color=INK)
    ax.axvspan(d("2026-12-21"), d("2027-01-17"), color=GRID, alpha=0.6, lw=0)
    ax.text(d("2027-01-03"), 0.35, "сессия", ha="center", fontsize=8.5, color=MUTED)
    for m in TEAM["milestones"]:
        md_ = d(m["date"])
        ax.plot([md_], [0.35], marker="D", color=INK, markersize=7, clip_on=False)
        ax.axvline(md_, color=MUTED, lw=0.8, ls=":", ymin=0.08)
        ax.text(md_, 3.55, f"{m['id']}\n{md_:%d.%m}", ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.set_yticks([])
    ax.set_ylim(0, 4.4)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.set_xlim(d("2026-10-05"), d("2027-02-08"))
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def draw_dependencies(path: Path) -> None:
    deps = TEAM["dependencies"]
    parties = list(dict.fromkeys(x["party"] for x in deps))
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
    color = {"решение заказчика": BLUE, "внешняя служба": ORANGE, "поставщик": "#1baf7a", "интеграция": "#4a3aa7"}
    used = set()
    for x in deps:
        y = len(parties) - parties.index(x["party"])
        lbl = x["type"] if x["type"] not in used else None
        used.add(x["type"])
        ax.scatter([d(x["confirm_by"])], [y], s=70, color=color[x["type"]], edgecolor="white", linewidth=2,
                   zorder=3, label=lbl)
        same = [z["id"] for z in deps if z["party"] == x["party"] and z["confirm_by"] == x["confirm_by"]]
        if same[0] == x["id"]:
            ax.annotate(", ".join(same), (d(x["confirm_by"]), y), xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=8.5, color=INK)
    for m in TEAM["milestones"]:
        ax.axvline(d(m["date"]), color=MUTED, lw=0.9, ls="--")
        ax.text(d(m["date"]), len(parties) + 0.75, m["id"], ha="center", fontsize=9, color=INK, fontweight="bold")
    ax.set_yticks(range(len(parties), 0, -1), parties)
    ax.set_ylim(0.4, len(parties) + 1.1)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax.set_xlim(d("2026-10-05"), d("2027-02-08"))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), frameon=False, fontsize=8.5, ncol=4)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def draw_capacity(path: Path) -> None:
    base, rec = pl.coverage(10, False), pl.coverage(15, True)
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=150)
    labels = [f"Инкремент {r['inc']}\n{r['name']}" for r in base]
    xs = range(len(labels))
    w = 0.26
    series = [([r["need"] for r in base], "нужно (полный скоуп)", GREY, -w),
              ([r["capacity"] for r in base], "есть при 10 ч/нед", BLUE, 0),
              ([r["capacity"] for r in rec], "есть при 15 ч/нед", ORANGE, w)]
    for vals, lbl, c, off in series:
        bars = ax.bar([x + off for x in xs], vals, width=w - 0.03, color=c, label=lbl)
        for b, v in zip(bars, vals, strict=True):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(list(xs), labels)
    ax.set_ylabel("часы команды")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(max(v) for v, *_ in series) * 1.15)
    ax.legend(frameon=False, fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def mermaid() -> str:
    deps = TEAM["dependencies"]
    pid = {p_: f"P{i}" for i, p_ in enumerate(dict.fromkeys(x["party"] for x in deps), 1)}
    lines = ["flowchart LR"]
    lines.append('  subgraph EXT["Стейкхолдеры и поставщики"]')
    for p_, i in pid.items():
        lines.append(f'    {i}["{p_}"]')
    lines.append("  end")
    lines.append('  subgraph WP["Пакеты работ"]')
    wp = {c["id"]: c["name"] for c in pl.leaves()}
    for wid in dict.fromkeys(x["needed_for"] for x in deps):
        lines.append(f'    W{wid.replace(".", "_")}["{wid} {wp[wid]}"]')
    lines.append("  end")
    lines.append('  subgraph MS["Вехи"]')
    for m in TEAM["milestones"]:
        lines.append(f'    {m["id"]}(["{m["id"]} {m["name"]} · {d(m["date"]):%d.%m.%Y}"])')
    lines.append("  end")
    for x in deps:
        lines.append(f'  {pid[x["party"]]} -- "{x["id"]} до {d(x["confirm_by"]):%d.%m}" --> W{x["needed_for"].replace(".", "_")}')
    for wid, ms in dict.fromkeys((x["needed_for"], x["blocks"]) for x in deps):
        lines.append(f'  W{wid.replace(".", "_")} --> {ms}')
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- документ
D = Doc()
D.title("ЛЗ 5. WBS, план релизов и карта зависимостей проекта «Практика»")
D.sub("Управление IT-проектами · Неделя 5 · 4 курс бакалавриата · осень 2026")
total = pl.wbs_total()
cap = pl.capacity()
D.p("Артефакты ЗС 5: WBS до 3-го уровня и словарь на 5 пакетов (часть 1), план релизов из 3 инкрементов с "
    "вехами (часть 2), карта зависимостей (часть 3), топология команд и RACI (часть 4), расчёт capacity "
    "(часть 5). Исходные данные лежат в репозитории в docs/planning/ (YAML), расчёты — в planning.py, "
    "так что любую цифру можно пересчитать.")
D.note(f"Главный вывод: при 10 часах в неделю на человека команда успевает {cap.total / total:.0%} "
       f"оставшейся работы ({cap.total:.0f} из {total:.0f} ч). Чтобы успеть всё, нужно около "
       f"{pl.required_hours_per_week():.0f} ч в неделю на каждого. Решение — в части 5.")

# 1
D.h1("Часть 1. WBS")
D.p("WBS построена по результатам (что сдаём), а не по действиям, и соблюдает правило 100 %: всё, что команда "
    "делает в проекте, включая лабораторные артефакты, лежит ровно в одном пакете 3-го уровня. Часы — оставшаяся "
    "работа с 12.10.2026; сделанное в ЛЗ 1–4 и прототип имеют 0 ч. Оценки — предварительные, их проверим "
    "покером планирования в ЗС 6.")
draw_wbs(PLAN / "wbs.png")
D.image(PLAN / "wbs.png", "Рис. 1. WBS проекта до 3-го уровня (часы — оставшаяся работа)")
D.table(["Код", "Пакет работ", "Часы", "Статус", "Инкремент", "Ответственный", "Истории"],
        [[c["id"], c["name"], f"{c['hours']:.0f}", STATUS[c["status"]], INC[c["inc"]], OWNER[c["owner"]],
          ", ".join(c.get("stories", []))] for c in pl.leaves()])
D.p(f"Итого {total:.0f} ч: продукт {total - pl.hours_by('inc').get('ongoing', 0):.0f} ч, управление и "
    f"документы, идущие весь семестр, — {pl.hours_by('inc').get('ongoing', 0):.0f} ч. Для сравнения: в "
    "бизнес-кейсе ЛЗ 3 (допущение A7) заложено 600 ч — это оценка подрядчика «с нуля». У нас уже есть "
    "прототип API, поэтому снизу вверх получается меньше. A7 обновим через Change Request, на рекомендацию "
    "бизнес-кейса это не влияет: вариант В3-С остаётся лучшим.")
D.h2("Словарь WBS: 5 ключевых пакетов")
leaf = {c["id"]: c for c in pl.leaves()}
for wid, e in WBS["dictionary"].items():
    c = leaf[wid]
    D.table(["Поле", f"{wid} {c['name']}"], [
        ["Описание", e["description"]], ["Результат", e["deliverables"]], ["Критерии приёмки", e["acceptance"]],
        ["Оценка", f"{c['hours']:.0f} ч · {INC[c['inc']]}"], ["Ответственный", OWNER[c["owner"]]],
        ["Зависит от", "; ".join(e["depends_on"])], ["Риск", e["risks"]],
    ])

# 2
D.h1("Часть 2. План релизов на семестр")
D.p("Модель поставки — Hybrid (ADR-001): снаружи вехи по неделям курса, внутри инкремента — итерации с демо "
    "методисту. Инкременты нарезаны по story map из ЛЗ 4: сначала тонкий сквозной сценарий, потом всё, без чего "
    "нельзя пустить реальных пользователей, потом перенос данных и передача системы.")
draw_releases(PLAN / "releases.png")
D.image(PLAN / "releases.png", "Рис. 2. План релизов: инкременты, вехи M1–M4, сессия и каникулы")
ms = {m["id"]: m for m in TEAM["milestones"]}
for inc in TEAM["increments"]:
    a, b = inc["weeks"]
    m = ms[inc["milestone"]]
    D.h2(f"Инкремент {inc['id']}. {inc['name']} — недели {a}–{b}")
    D.p(f"Цель: {inc['goal']}")
    D.p(f"Содержание: истории {', '.join(inc['stories'])}; пакеты WBS: "
        + ", ".join(c["id"] for c in pl.leaves() if c["inc"] == inc["id"]) + ".")
    D.p(f"Веха {m['id']} «{m['name']}» — {d(m['date']):%d.%m.%Y}. Критерии готовности вехи:")
    D.bullets(inc["done"])
D.p("Веха M4 «Запуск пилота» — 01.02.2027, после каникул. Решение принимает спонсор по чек-листу go / no-go "
    "из бизнес-кейса: замер методиста подтвердил эффект, ИТ-отдел принял поддержку, UAT подписан.")

# 3
D.h1("Часть 3. Карта зависимостей")
deps = TEAM["dependencies"]
D.p(f"{len(deps)} зависимостей от людей и организаций вне команды. У каждой есть владелец с нашей стороны (кто "
    "добивается ответа) и дата, к которой нужно подтверждение, иначе сдвигается веха. Структурная схема в "
    "формате Mermaid лежит в docs/planning/dependencies.mmd (GitHub рисует её прямо в браузере). Ниже — те же "
    "зависимости на шкале времени.")
draw_dependencies(PLAN / "dependencies.png")
D.image(PLAN / "dependencies.png", "Рис. 3. Когда каждая зависимость должна быть подтверждена (пунктир — вехи)")
D.table(["ID", "От кого", "Тип", "Что нужно", "Для пакета", "Владелец", "Подтвердить до", "Блокирует"],
        [[x["id"], x["party"], x["type"], x["what"], x["needed_for"], OWNER[x["owner"]],
          f"{d(x['confirm_by']):%d.%m.%Y}", x["blocks"]] for x in deps])
D.p("Решения, ожидающие заказчика: D2 (замер — первое условие go / no-go), D3 (время на демо и UAT), D4 "
    "(образец таблицы), D7 (бюджет эксплуатации). Критическая цепочка: D1 → 1.6.3 → M4. Если ИТ-отдел не "
    "возьмёт поддержку до 16.10, запуск по бизнес-кейсу не делаем, а инкремент 3 превращается в передачу "
    "документации.")

# 4
D.h1("Часть 4. Топология команд и роли")
D.table(["Команда (Team Topologies)", "Кто", "Режим взаимодействия с нами"], [
    ["Stream-aligned — поток «практика студента»", "Наша команда: Бекмағанбет Әлібек, Зият Нұркен",
     "Владеет продуктом целиком: от требований до запуска"],
    ["Platform", "ИТ-отдел университета: сервер, почта, резервные копии, вход",
     "X-as-a-Service: берём готовые сервисы по запросу (D1, D8, D9)"],
    ["Enabling", "Преподаватель курса, служба ИБ на этапе модели угроз",
     "Facilitating: учат и проверяют, но работу не делают за нас"],
    ["Complicated-subsystem", "Нет", "Интеграция с ИС успеваемости вынесена из скоупа (устав)"],
])
D.p("Почему так: команда из двух человек не потянет свою инфраструктуру — когнитивная нагрузка уйдёт в "
    "серверы вместо продукта. Поэтому стек простой (ADR-002), а всё, что ИТ-отдел умеет делать как сервис, "
    "берём у него.")
D.h2("Роли и зоны ответственности")
D.table(["Участник", "Роль", "Отвечает за"], [
    ["Бекмағанбет Әлібек", "PM, бэкенд", "План и вехи, коммуникация со спонсором и методистом, API, кабинеты студента и методиста, импорт/экспорт"],
    ["Зият Нұркен", "Аналитик, QA, DevOps", "Бэклог и НФТ, макеты, уведомления, кабинет куратора, CI/CD, тестирование и UAT, развёртывание, обучение"],
])
D.h2("RACI на ключевые артефакты")
D.p("R — делает, A — отвечает за результат (ровно один на строку), C — консультирует, I — информируется.")
raci = [
    ("Бэклог и приоритеты", "C", "R", "A", "I", "", ""),
    ("WBS, план релизов, capacity", "A/R", "C", "C", "I", "", "I"),
    ("Нефункциональные требования", "C", "A/R", "C", "", "C", ""),
    ("API и интерфейсы", "A/R", "R", "C", "", "", ""),
    ("CI/CD и окружения", "I", "A/R", "", "", "C", ""),
    ("Протокол UAT", "C", "R", "A", "I", "", ""),
    ("Развёртывание и runbook", "A", "R", "I", "", "C", ""),
    ("Перенос данных (акт сверки)", "C", "R", "A", "", "", ""),
    ("Статус-отчёт спонсору", "A/R", "C", "I", "I", "", ""),
    ("Go / no-go запуска", "R", "C", "C", "A", "C", ""),
    ("Сдача лабораторных", "A/R", "R", "", "", "", "I"),
]
D.table(["Артефакт", "Әлібек (PM)", "Нұркен (BA/QA)", "Методист", "Спонсор", "ИТ-отдел", "Преподаватель"],
        [list(r) for r in raci])

# 5
D.h1("Часть 5. Capacity команды на семестр")
c = TEAM["capacity"]
D.p("Считаем реальные часы, а не «по 40 часов в неделю». Формула: человек × часы в неделю × доля недели × "
    "фокус-фактор × (1 − резерв).")
D.bullets([
    f"[C1] {c['hours_per_week']} ч в неделю на человека: лекция и лабораторная плюс самостоятельная работа по курсу. "
    "У обоих ещё 5–6 предметов, проект — не единственная нагрузка.",
    f"[C2] Фокус-фактор {c['focus_factor']}: встречи, переключения, ревью съедают около 30 % времени.",
    f"[C3] Резерв {c['reserve']:.0%} на болезни и непредвиденное.",
    "[C4] Неделя 8 — рубежный контроль и выходной 26.10 за День Республики (0,48 недели); неделя 14 — второй "
    "рубежный контроль (0,6); неделя 15 — защита, сессия и 16.12 День Независимости (0,4).",
    f"[C5] Сессия — проектом не занимаемся; {c['winter']['label']} — по {c['winter']['hours_per_week']} ч в неделю, "
    "если команда согласна.",
])
D.table(["Неделя", *[lbl for lbl, _ in cap.weeks], "Итого"],
        [["Часы команды", *[f"{h:.0f}" for _, h in cap.weeks], f"{cap.total:.0f}"]])
D.h2("Хватает ли часов")
rows = []
for hpw, cuts in pl.SCENARIOS:
    cp = pl.capacity(hpw).total
    need = total - (sum(h for _, h, _ in pl.SCOPE_CUTS) if cuts else 0)
    rows.append([f"{hpw} ч/нед" + (" + CR-001" if cuts else ""), f"{cp:.0f}", f"{need:.0f}", f"{cp / need:.0%}"])
D.table(["Сценарий", "Capacity, ч", "Нужно, ч", "Покрытие"], rows)
draw_capacity(PLAN / "capacity.png")
D.image(PLAN / "capacity.png", "Рис. 4. Часы по инкрементам: сколько нужно и сколько есть")
D.p(f"При 10 ч в неделю команда закрывает {cap.total / total:.0%} работы. Больше всего не хватает в "
    "инкрементах 1 и 2: на них же приходятся лабораторные и рубежный контроль. Чтобы успеть весь скоуп, "
    f"каждому нужно около {pl.required_hours_per_week():.0f} ч в неделю — нереально для 4 курса с другими "
    "предметами.")
D.h2("Решение: три шага вместо «будем стараться»")
D.numbered([
    "Каждый участник выделяет 15 ч в неделю — договорённость фиксируем в протоколе команды.",
    f"Change Request CR-001 убирает из семестра {sum(h for _, h, _ in pl.SCOPE_CUTS)} ч: "
    + "; ".join(f"{wid} — {why}" for wid, _, why in pl.SCOPE_CUTS) + ".",
    f"Оставшиеся ~{total - sum(h for _, h, _ in pl.SCOPE_CUTS) - pl.capacity(15).total:.0f} ч закрываем третьим "
    "участником (курс допускает команды по 3–4 человека) или вторым Change Request. Решение — до конца недели 6.",
])
D.p("Если ничего из этого не сделать, к M3 не будут готовы перенос данных и передача ИТ-отделу, а значит, "
    "не выполнится go / no-go запуска в феврале. Это отдельный риск в реестре ЗС 7.")

D.h1("Раскрытие использования AI")
D.p("По правилам курса: структура WBS, оценки часов, расчёт capacity и диаграммы подготовлены с помощью "
    "AI-ассистента Claude (Anthropic). Часы и допущения C1–C5 — предложения, которые команда пересматривает; "
    "даты зависимостей нужно согласовать с владельцами. Ответственность за содержание несёт команда.")

if __name__ == "__main__":
    (PLAN / "dependencies.mmd").write_text(mermaid(), encoding="utf-8")
    D.render_docx(DOCX_OUT)
    D.render_md(MD_OUT)
    print(f"saved {DOCX_OUT}\nsaved {MD_OUT}")
