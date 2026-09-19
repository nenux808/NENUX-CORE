import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.policy import (
    is_history_query,
    requires_fresh_verification,
    memory_only_mode,
    should_store_task_memory,
)

from tools.filesystem import _safe_path
from config import CORE_VERSION, CHAT_MODEL, EMBED_MODEL
from memory import database


class TestPolicy(unittest.TestCase):

    def test_history_query(self):
        self.assertTrue(
            is_history_query(
                "Have we previously tested multiplication?"
            )
        )

    def test_fresh_verification(self):
        self.assertTrue(
            requires_fresh_verification(
                "Run it again and verify now."
            )
        )

    def test_memory_only(self):
        self.assertTrue(
            memory_only_mode(
                "Have we done this before?"
            )
        )

    def test_not_memory_only_when_rerun_requested(self):
        self.assertFalse(
            memory_only_mode(
                "Have we done this before? Run it again."
            )
        )

    def test_memory_lookup_not_re_stored(self):
        self.assertFalse(
            should_store_task_memory(
                "Have we previously done multiplication?"
            )
        )


class TestWorkspaceSecurity(unittest.TestCase):

    def test_workspace_path_allowed(self):
        path = _safe_path(
            "safe_test.py"
        )

        self.assertIn(
            "workspace",
            str(path).lower()
        )

    def test_parent_escape_blocked(self):
        with self.assertRaises(
            PermissionError
        ):
            _safe_path(
                "..\\main.py"
            )


class TestRuntimeSmoke(unittest.TestCase):

    def test_main_imports(self):
        import main

        self.assertTrue(
            callable(main.main)
        )

    def test_central_config_is_available(self):
        self.assertEqual(
            CORE_VERSION,
            "0.11-dev"
        )
        self.assertTrue(CHAT_MODEL)
        self.assertTrue(EMBED_MODEL)


class TestDatabaseMemory(unittest.TestCase):

    def test_key_value_memory_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test_memory.db"

            with patch.object(
                database,
                "DB_PATH",
                test_db
            ):
                database.init_database()
                database.remember(
                    "runtime_test",
                    {"value": 42}
                )

                self.assertEqual(
                    database.recall("runtime_test"),
                    {"value": 42}
                )

    def test_database_initializes_expected_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_db = Path(temp_dir) / "test_schema.db"

            with patch.object(
                database,
                "DB_PATH",
                test_db
            ):
                database.init_database()

                with sqlite3.connect(test_db) as conn:
                    rows = conn.execute(
                        """
                        SELECT name
                        FROM sqlite_master
                        WHERE type = 'table'
                        """
                    ).fetchall()

            tables = {
                row[0]
                for row in rows
            }

            self.assertTrue(
                {
                    "conversations",
                    "memories",
                    "tasks",
                    "task_steps",
                    "action_logs",
                    "task_attempts",
                }.issubset(tables)
            )

if __name__ == "__main__":
    unittest.main()
