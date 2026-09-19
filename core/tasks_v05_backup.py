from datetime import datetime
from memory.database import get_connection


def create_task(goal: str) -> int:
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks
            (goal, status, created_at, updated_at)
            VALUES (?, 'active', ?, ?)
            """,
            (goal, now, now)
        )

        return cursor.lastrowid


def add_step(task_id: int, description: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO task_steps
            (task_id, description, status, created_at)
            VALUES (?, ?, 'pending', ?)
            """,
            (
                task_id,
                description,
                datetime.utcnow().isoformat()
            )
        )

        return cursor.lastrowid


def update_step(step_id: int, status: str):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE task_steps
            SET status = ?
            WHERE id = ?
            """,
            (status, step_id)
        )


def complete_task(task_id: int):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = 'completed',
                updated_at = ?
            WHERE id = ?
            """,
            (
                datetime.utcnow().isoformat(),
                task_id
            )
        )


def get_active_tasks():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM tasks
            WHERE status = 'active'
            ORDER BY id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]