import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = os.getenv("DATABASE_PATH")
if not DATABASE_PATH:
    raise ValueError("DATABASE_PATH environment variable is not set. Check your .env file.")


def init_db():
    """Initialize the SQLite database with the events table."""
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH) as con:
        con.execute("PRAGMA foreign_keys = ON")

        # Create events table
        con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                notes TEXT DEFAULT '',
                recurrence TEXT DEFAULT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        con.commit()


@contextmanager
def _conn():
    """Context manager for database connections with row factory."""
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
