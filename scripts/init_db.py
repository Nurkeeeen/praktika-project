"""Создаёт SQLite-базу из db/schema.sql и загружает демо-данные из db/seed/.

Запуск: python scripts/init_db.py [путь_к_базе]   (по умолчанию data/praktika.db)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db  # noqa: E402


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else db.db_path()
    conn = db.create_database(path, seed=False)
    counts = db.load_seed(conn)
    conn.close()
    print(f"База создана: {path}")
    for table, n in counts.items():
        print(f"  {table}: {n}")


if __name__ == "__main__":
    main()
