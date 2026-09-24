"""Строит story map из docs/requirements/stories.yaml:
- story-map.excalidraw — редактируемая доска (excalidraw.com → Open);
- story-map.png — картинка для отчёта и README.

Запуск: python scripts/build_story_map.py
"""

from __future__ import annotations

import json
import random
import textwrap
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

REQ = Path(__file__).resolve().parents[1] / "docs" / "requirements"
DATA = yaml.safe_load((REQ / "stories.yaml").read_text(encoding="utf-8"))

LANES = [
    ("skeleton", "Ходячий скелет", "#ffd8a8"),
    ("mvp", "MVP — релиз 1\n(февраль 2027)", "#fff3bf"),
    ("r2", "Релиз 2", "#d0ebff"),
    ("later", "Потом", "#e9ecef"),
]
LEFT, TOP, COL_W, CARD_W, CARD_H, GAP = 190, 120, 250, 230, 96, 12
BACKBONE_H = 70
SLICE_COLOR = "#e03131"


def layout():
    acts = list(DATA["activities"])
    lanes = [ln for ln in LANES if any(s["release"] == ln[0] for s in DATA["stories"])]
    cells: dict[tuple[str, str], list[dict]] = {}
    for s in DATA["stories"]:
        cells.setdefault((s["release"], s["activity"]), []).append(s)
    lane_y, y = {}, TOP + BACKBONE_H + 30
    for key, _, _ in lanes:
        depth = max((len(cells.get((key, a), [])) for a in acts), default=1) or 1
        lane_y[key] = (y, depth * (CARD_H + GAP) + GAP)
        y += lane_y[key][1] + 16
    return acts, lanes, cells, lane_y, y


def card_text(s: dict) -> str:
    tag = "Spike" if s.get("type") == "spike" else s["epic"]
    body = textwrap.fill(s["title"], 30)
    return f"{s['id']} · {tag} · {s['points']} SP\n{body}"


def font(size: int, bold: bool = False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"),
                 ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")):
        for base in ("C:/Windows/Fonts", "/usr/share/fonts/truetype/dejavu"):
            try:
                return ImageFont.truetype(f"{base}/{name}", size)
            except OSError:
                continue
    return ImageFont.load_default()


def build_png(path: Path) -> None:
    acts, lanes, cells, lane_y, height = layout()
    width = LEFT + len(acts) * COL_W + 30
    img = Image.new("RGB", (width, height + 20), "white")
    d = ImageDraw.Draw(img)
    d.text((20, 20), "Story map проекта «Практика» · путь пользователя слева направо, приоритет сверху вниз",
           font=font(22, True), fill="#1f1f1f")
    d.text((20, 58), "Красная линия — граница MVP (релиз 1): всё выше неё нужно к февралю 2027",
           font=font(16), fill=SLICE_COLOR)
    for i, a in enumerate(acts):
        x = LEFT + i * COL_W
        d.rounded_rectangle([x, TOP, x + CARD_W, TOP + BACKBONE_H], 10, fill="#1f4e79")
        d.multiline_text((x + 12, TOP + 12), f"{a}\n" + textwrap.fill(DATA["activities"][a], 26),
                         font=font(15, True), fill="white", spacing=4)
    for key, label, color in lanes:
        y0, h = lane_y[key]
        d.rectangle([10, y0, width - 10, y0 + h], outline="#ced4da")
        d.multiline_text((20, y0 + 12), label, font=font(16, True), fill="#343a40", spacing=4)
        pts = sum(s["points"] for s in DATA["stories"] if s["release"] == key)
        d.text((20, y0 + 62), f"{pts} SP", font=font(15), fill="#495057")
        for i, a in enumerate(acts):
            for j, s in enumerate(cells.get((key, a), [])):
                x, y = LEFT + i * COL_W, y0 + GAP + j * (CARD_H + GAP)
                d.rounded_rectangle([x, y, x + CARD_W, y + CARD_H], 8, fill=color, outline="#868e96")
                d.multiline_text((x + 10, y + 8), card_text(s), font=font(14), fill="#212529", spacing=3)
    y_slice = lane_y["mvp"][0] + lane_y["mvp"][1] + 8
    d.line([10, y_slice, width - 10, y_slice], fill=SLICE_COLOR, width=4)
    img.save(path)


def build_excalidraw(path: Path) -> None:
    acts, lanes, cells, lane_y, height = layout()
    rnd = random.Random(7)
    els: list[dict] = []

    def base(kind, x, y, w, h, **kw):
        el = {"id": f"el{len(els)}", "type": kind, "x": x, "y": y, "width": w, "height": h, "angle": 0,
              "strokeColor": "#1e1e1e", "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 1,
              "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
              "roundness": {"type": 3} if kind == "rectangle" else None, "seed": rnd.randint(1, 2**31),
              "version": 1, "versionNonce": rnd.randint(1, 2**31), "isDeleted": False, "boundElements": [],
              "updated": 1, "link": None, "locked": False}
        el.update(kw)
        els.append(el)
        return el

    def text(x, y, s, size=16, container=None, color="#1e1e1e"):
        lines = s.split("\n")
        el = base("text", x, y, max(len(line) for line in lines) * size * 0.55, len(lines) * size * 1.25,
                  text=s, originalText=s, fontSize=size, fontFamily=2, textAlign="left", verticalAlign="top",
                  containerId=container["id"] if container else None, lineHeight=1.25, autoResize=True,
                  strokeColor=color)
        if container:
            container["boundElements"].append({"type": "text", "id": el["id"]})
        return el

    def box(x, y, w, h, label, bg, size=16, color="#1e1e1e"):
        rect = base("rectangle", x, y, w, h, backgroundColor=bg)
        text(x + 8, y + 8, label, size, rect, color)

    text(20, 20, "Story map проекта «Практика» (генерируется из docs/requirements/stories.yaml)", 24)
    for i, a in enumerate(acts):
        box(LEFT + i * COL_W, TOP, CARD_W, BACKBONE_H, f"{a}\n{textwrap.fill(DATA['activities'][a], 26)}",
            "#1f4e79", 16, "#ffffff")
    for key, label, color in lanes:
        y0, h = lane_y[key]
        base("rectangle", 10, y0, LEFT + len(acts) * COL_W, h, strokeColor="#adb5bd", roundness=None)
        text(20, y0 + 12, label, 18)
        for i, a in enumerate(acts):
            for j, s in enumerate(cells.get((key, a), [])):
                box(LEFT + i * COL_W, y0 + GAP + j * (CARD_H + GAP), CARD_W, CARD_H, card_text(s), color, 14)
    y_slice = lane_y["mvp"][0] + lane_y["mvp"][1] + 8
    width = LEFT + len(acts) * COL_W
    base("line", 10, y_slice, width, 0, strokeColor=SLICE_COLOR, strokeWidth=4, points=[[0, 0], [width, 0]],
         lastCommittedPoint=None, startBinding=None, endBinding=None, startArrowhead=None, endArrowhead=None)
    text(width - 260, y_slice + 8, "граница MVP (релиз 1)", 18, color=SLICE_COLOR)
    doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": els,
           "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None}, "files": {}}
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    build_png(REQ / "story-map.png")
    build_excalidraw(REQ / "story-map.excalidraw")
    print("saved story-map.png, story-map.excalidraw")
