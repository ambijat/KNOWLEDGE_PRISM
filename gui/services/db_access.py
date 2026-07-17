"""Read-only SQLite access for the Knowledge Prism operational GUI."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "db" / "knowledge_prism.db"


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def rows(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connect() as con:
        return [dict(row) for row in con.execute(query, params).fetchall()]


def scalar(query: str, params: tuple[Any, ...] = (), default: Any = 0) -> Any:
    with connect() as con:
        row = con.execute(query, params).fetchone()
    if row is None:
        return default
    return row[0]


def table_count(table: str) -> int:
    return int(scalar(f"SELECT COUNT(*) FROM {table}"))


def safe_columns(table: str) -> list[str]:
    with connect() as con:
        return [row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()]
