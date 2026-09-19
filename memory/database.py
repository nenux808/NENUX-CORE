import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "nenux_memory.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              role TEXT NOT NULL,
              content TEXT NOT NULL,
              created_at TEXT NOT NULL
            );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS task_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT NOT NULL,
            arguments TEXT,
            result TEXT,
            approved INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS task_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'running',
            started_at TEXT NOT NULL,
            finished_at TEXT,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        );
        """)


def remember(key, value):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO memories (key, value, created_at)
            VALUES (?, ?, ?)
            """,
            (
                key,
                json.dumps(value, ensure_ascii=False),
                datetime.utcnow().isoformat()
            )
        )


def recall(key):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT value
            FROM memories
            WHERE key = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (key,)
        ).fetchone()

    if not row:
        return None

    return json.loads(row["value"])


def log_action(tool, arguments, result, approved):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO action_logs
            (tool, arguments, result, approved, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                tool,
                json.dumps(arguments, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                int(approved),
                datetime.utcnow().isoformat()
            )
        )

def save_message(role: str, content: str):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (role, content, created_at)
            VALUES (?, ?, ?)
            """,
            (
                role,
                content,
                datetime.utcnow().isoformat()
            )
        )


def get_recent_messages(limit: int = 12):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM conversations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    rows = list(reversed(rows))

    return [
        {
            "role": row["role"],
            "content": row["content"]
        }
        for row in rows
    ]


def get_task_steps(task_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, description, status
            FROM task_steps
            WHERE task_id = ?
            ORDER BY id ASC
            """,
            (task_id,)
        ).fetchall()

    return [dict(row) for row in rows]

def start_task_attempt(task_id: int) -> tuple[int, int]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(MAX(attempt_number), 0) AS max_attempt
            FROM task_attempts
            WHERE task_id = ?
            """,
            (task_id,)
        ).fetchone()

        attempt_number = int(row["max_attempt"]) + 1

        cursor = conn.execute(
            """
            INSERT INTO task_attempts
            (task_id, attempt_number, status, started_at)
            VALUES (?, ?, 'running', ?)
            """,
            (
                task_id,
                attempt_number,
                datetime.utcnow().isoformat()
            )
        )

        return cursor.lastrowid, attempt_number


def finish_task_attempt(
    attempt_id: int,
    status: str
):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE task_attempts
            SET status = ?,
                finished_at = ?
            WHERE id = ?
            """,
            (
                status,
                datetime.utcnow().isoformat(),
                attempt_id
            )
        )


def get_task_attempts(task_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM task_attempts
            WHERE task_id = ?
            ORDER BY attempt_number ASC
            """,
            (task_id,)
        ).fetchall()

    return [dict(row) for row in rows]
