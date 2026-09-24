"""Подключение к SQLite и загрузка схемы/демо-данных."""

from __future__ import annotations

import csv
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"
SEED_DIR = ROOT / "db" / "seed"
DEFAULT_DB = ROOT / "data" / "praktika.db"

# Порядок важен из-за внешних ключей
SEED_TABLES = ["curators", "students", "employers", "vacancies", "applications",
               "application_status_history", "practice_reports"]


def db_path() -> Path:
    return Path(os.environ.get("PRAKTIKA_DB", DEFAULT_DB))


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))


def load_seed(conn: sqlite3.Connection, seed_dir: Path = SEED_DIR) -> dict[str, int]:
    counts = {}
    for table in SEED_TABLES:
        with open(seed_dir / f"{table}.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            counts[table] = 0
            continue
        cols = list(rows[0])
        conn.executemany(
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
            [[r[c] if r[c] != "" else None for c in cols] for r in rows],
        )
        counts[table] = len(rows)
    conn.commit()
    return counts


def create_database(path: Path | str, seed: bool = True) -> sqlite3.Connection:
    path = Path(path)
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
    conn = connect(path)
    init_schema(conn)
    if seed:
        load_seed(conn)
    return conn
