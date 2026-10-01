"""Собирает сайт-портфолио проекта в _site/ (публикуется на GitHub Pages workflow'ом pages.yml).

Источники — те же файлы, что и у лабораторных: отчёты docs/labs/*.docx, финмодель finance/tco_model.py,
бэклог и НФТ docs/requirements/*.yaml, ADR docs/adr/*.md, демо-базы db/seed/*.csv.
Шаблон страницы — site/ (index.html, style.css, app.js, model.js).

Запуск: python scripts/build_site.py  →  открыть _site/index.html или `python -m http.server -d _site`
"""

from __future__ import annotations

import csv
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import docx
import markdown
import yaml
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "finance"))
import tco_model as m  # noqa: E402

SRC, OUT = ROOT / "site", ROOT / "_site"
LABS = [
    ("lz1", 1, "ЛЗ1_Реверс-инжиниринг_рынка_труда.docx"),
    ("lz2", 2, "ЛЗ2_Модель_поставки_и_рабочее_пространство.docx"),
    ("lz3", 3, "ЛЗ3_Бизнес-кейс_устав_финмодель.docx"),
    ("lz4", 4, "ЛЗ4_Требования_story_map_НФТ.docx"),
]
BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
EMBED = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"


# ---------------------------------------------------------------- .docx → HTML
def _para_html(p: Paragraph, doc, assets: Path, prefix: str, counter: list[int]) -> tuple[str, str]:
    """Возвращает (вид, html): вид — h2/h3/h4/li/p/img/title."""
    for blip in p._p.iter(BLIP):
        part = doc.part.related_parts[blip.get(EMBED)]
        counter[0] += 1
        name = f"{prefix}-{counter[0]}{Path(part.partname).suffix}"
        (assets / name).write_bytes(part.blob)
        return "img", f'<figure><img src="assets/{name}" alt="" loading="lazy"></figure>'
    text = html.escape(p.text.strip())
    if not text:
        return "skip", ""
    style = p.style.name if p.style is not None else ""
    numbered = p._p.pPr is not None and p._p.pPr.numPr is not None
    bold = all(r.bold for r in p.runs if r.text.strip())
    if style == "Heading 1":
        return "h2", f"<h3>{text}</h3>"
    if style == "Heading 2":
        return "h3", f"<h4>{text}</h4>"
    if style.startswith("List") or numbered:
        return ("ol" if "Number" in style else "ul"), f"<li>{text}</li>"
    if bold and len(text) < 140:
        return "h4", f"<h5>{text}</h5>"
    if all(r.italic for r in p.runs if r.text.strip()):
        return "p", f'<p class="note">{text}</p>'
    return "p", f"<p>{text}</p>"


def _table_html(t: Table) -> str:
    rows = []
    for i, row in enumerate(t.rows):
        tag = "th" if i == 0 else "td"
        cells, seen = [], set()
        for c in row.cells:
            if id(c._tc) in seen:  # объединённые ячейки python-docx отдаёт повторно
                continue
            seen.add(id(c._tc))
            val = "<br>".join(html.escape(par.text) for par in c.paragraphs if par.text.strip())
            cells.append(f"<{tag}>{val}</{tag}>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return '<div class="table-wrap"><table>' + "".join(rows) + "</table></div>"


def docx_to_html(path: Path, assets: Path, prefix: str) -> tuple[str, str]:
    """Возвращает (заголовок документа, html тела без заголовка)."""
    d = docx.Document(path)
    out, title, open_list, counter = [], "", None, [0]
    for el in d.element.body.iterchildren():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "p":
            kind, frag = _para_html(Paragraph(el, d), d, assets, prefix, counter)
            if kind == "skip":
                continue
            if not title and kind in ("p", "h4", "h2"):
                title = Paragraph(el, d).text.strip()
                continue
        elif tag == "tbl":
            kind, frag = "table", _table_html(Table(el, d))
        else:
            continue
        if kind in ("ul", "ol"):
            if open_list != kind:
                if open_list:
                    out.append(f"</{open_list}>")
                out.append(f"<{kind}>")
                open_list = kind
        elif open_list:
            out.append(f"</{open_list}>")
            open_list = None
        out.append(frag)
    if open_list:
        out.append(f"</{open_list}>")
    return title, "\n".join(out)


# ---------------------------------------------------------------- данные
def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def md_html(path: Path) -> str:
    return markdown.markdown(path.read_text(encoding="utf-8"), extensions=["tables"])


def checklist() -> list[dict]:
    rows = []
    for line in (ROOT / "docs" / "portfolio-checklist.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.match(r"^\d", cells[0]):
            status = "done" if cells[3].startswith("✅") else "progress" if "🟡" in cells[3] else "todo"
            note = re.sub(r"[✅🟡⬜]\s*", "", cells[3]).strip(" ;")
            rows.append({"week": cells[0], "artifact": cells[1], "status": status, "note": note})
    return rows


def finance() -> dict:
    opts = m.options()
    support = m.P["support_h_month"] * 12 * m.RATE_DEV
    out = []
    for i, o in enumerate(opts):
        own = i >= 2  # В2, В3, В3-С — своя разработка, поддержка 4 ч/мес по A10
        out.append({"name": o.name, "costs": o.costs, "benefits": o.benefits,
                    "support": [0, support, support, support] if own else [0, 0, 0, 0],
                    "tco": o.tco, "roi": o.roi, "npv": o.npv, "payback": o.payback_years})
    return {
        "options": out,
        "discount_rate": m.P["discount_rate"],
        "rate_edu": m.RATE_EDU, "rate_dev": m.RATE_DEV,
        "annual_benefit": m.annual_benefit(), "saved_hours": m.saved_hours(),
        "methodist_before": m.P["methodist_h_before"], "methodist_after": m.P["methodist_h_after"],
        "active_weeks": m.P["active_weeks"],
        "other_hours": m.saved_hours() - (m.P["methodist_h_before"] - m.P["methodist_h_after"]) * m.P["active_weeks"],
        "support_base": m.P["support_h_month"],
        "licenses": m.licenses_proprietary(),
        "sources": m.SOURCES, "assumptions": m.ASSUMPTIONS,
        "scenarios": [{"name": n, "ck": ck, "bk": bk} for n, ck, bk in m.SCENARIOS],
    }


def git_sha() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:7]
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    assets, files = OUT / "assets", OUT / "files"
    assets.mkdir()
    files.mkdir()

    labs = []
    for key, week, fname in LABS:
        src = ROOT / "docs" / "labs" / fname
        title, body = docx_to_html(src, assets, key)
        shutil.copy(src, files / fname)
        labs.append({"id": key, "week": week, "title": title, "html": body, "file": f"files/{fname}"})

    downloads = [{"name": lab["title"], "file": lab["file"], "kind": "Word"} for lab in labs]
    for src, kind, label in [
        (ROOT / "finance" / "tco_model.xlsx", "Excel", "Финансовая модель TCO/ROI (формулы)"),
        (ROOT / "docs" / "requirements" / "story-map.excalidraw", "Excalidraw", "Story map — редактируемая доска"),
        (ROOT / "docs" / "requirements" / "story-map.png", "PNG", "Story map — картинка"),
        (ROOT / "docs" / "requirements" / "stakeholder-matrix.png", "PNG", "Матрица стейкхолдеров"),
    ]:
        shutil.copy(src, files / src.name)
        downloads.append({"name": label, "file": f"files/{src.name}", "kind": kind})
    shutil.copy(ROOT / "docs" / "requirements" / "story-map.png", assets / "story-map.png")

    req = ROOT / "docs" / "requirements"
    backlog = yaml.safe_load((req / "stories.yaml").read_text(encoding="utf-8"))
    seed = ROOT / "db" / "seed"
    data = {
        "meta": {
            "repo": os.environ.get("GITHUB_REPOSITORY", "Nurkeeeen/praktika-project"),
            "built": date.today().isoformat(), "sha": git_sha(),
            "team": [{"name": "Бекмағанбет Әлібек", "role": "PM, коммуникация с заказчиком, разработка"},
                     {"name": "Зият Нүркен", "role": "Аналитика и требования, тестирование и CI"}],
        },
        "checklist": checklist(),
        "projectCard": md_html(ROOT / "docs" / "project-card.md"),
        "labs": labs,
        "downloads": downloads,
        "lz1": {"vacancies": read_csv(ROOT / "db" / "market" / "hh_pm_vacancies_2026-09-10.csv"),
                "requirements": read_csv(ROOT / "db" / "market" / "pm_requirements_frequency.csv")},
        "finance": finance(),
        "backlog": backlog,
        "nfr": yaml.safe_load((req / "nfr.yaml").read_text(encoding="utf-8")),
        "adr": [{"id": p.stem[:4], "html": md_html(p)} for p in sorted((ROOT / "docs" / "adr").glob("0*.md"))
                if not p.stem.startswith("0000")],
        "db": {name: read_csv(seed / f"{name}.csv")
               for name in ("students", "employers", "vacancies", "applications", "curators", "practice_reports")},
    }
    (OUT / "data.js").write_text("window.SITE_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
                                 encoding="utf-8")
    print(f"Сайт собран: {OUT / 'index.html'}  ({len(labs)} лабораторных, {len(downloads)} файлов)")


if __name__ == "__main__":
    main()
