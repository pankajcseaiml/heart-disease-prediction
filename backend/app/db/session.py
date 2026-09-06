"""Database connection and session management for SQLite."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "heart_disease.db"


def get_db_path() -> Path:
    db_url = os.getenv("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        raw_path = db_url.replace("sqlite:///", "")
        if os.path.isabs(raw_path):
            path = Path(raw_path)
        else:
            root = Path(__file__).resolve().parent.parent.parent.parent
            path = (root / raw_path).resolve()
    else:
        path = DEFAULT_DB_PATH

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    path = get_db_path()
    conn = sqlite3.connect(str(path), timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency and performance
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
