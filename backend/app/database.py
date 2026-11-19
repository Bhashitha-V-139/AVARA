import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    filename    TEXT NOT NULL,
    size_bytes  INTEGER NOT NULL,
    page_count  INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id  TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    citations   TEXT,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection, commit on success, roll back on error, and always close."""
    conn = sqlite3.connect(settings.sqlite_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the database file and all tables if they don't exist."""
    settings.ensure_directories()
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def insert_document(
    document_id: str,
    filename: str,
    size_bytes: int,
    page_count: int,
    status: str,
    uploaded_at: datetime,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents (document_id, filename, size_bytes, page_count, status, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, filename, size_bytes, page_count, status, uploaded_at.isoformat()),
        )


def list_documents() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
        return [dict(row) for row in rows]


def get_document(document_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
        return dict(row) if row else None


def delete_document_record(document_id: str) -> bool:
    """Delete one document row. Returns True if a row was removed."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE document_id = ?", (document_id,))
        return cursor.rowcount > 0


def create_session(session_id: str, created_at: datetime) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (session_id, created_at) VALUES (?, ?)",
            (session_id, created_at.isoformat()),
        )


def session_exists(session_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM chat_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        return row is not None


def add_message(
    session_id: str,
    role: str,
    content: str,
    created_at: datetime,
    citations_json: str | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, citations, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, content, citations_json, created_at.isoformat()),
        )


def get_recent_messages(session_id: str, limit: int) -> list[dict]:
    """Return the most recent messages, oldest first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM (
                SELECT id, role, content FROM chat_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
            """,
            (session_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def clear_session_messages(session_id: str) -> None:
    """Delete a session's messages. The session itself stays, so it can be reused."""
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))