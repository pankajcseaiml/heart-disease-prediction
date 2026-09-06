"""Database initialization and schema validation script."""

import sys
from pathlib import Path

# Ensure root is in path
root = Path(__file__).resolve().parent.parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from backend.app.db.models import get_prediction_count, init_tables
from backend.app.db.session import get_connection, get_db_path


def init_database() -> None:
    db_path = get_db_path()
    print(f"[*] Initializing database schema at: {db_path}")
    conn = get_connection()
    try:
        init_tables(conn)
        count = get_prediction_count(conn)
        print(f"[+] Database initialized successfully. Current record count: {count}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
