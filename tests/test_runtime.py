import unittest

from core.policy import (
    is_history_query,
    requires_fresh_verification,
    memory_only_mode,
    should_store_task_memory,
)

from tools.filesystem import _safe_path


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


if __name__ == "__main__":
    unittest.main()
