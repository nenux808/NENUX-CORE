import os
import unittest

import config
from core import evaluator, planner
from tools.filesystem import _safe_path, write_file
from tools.python_tool import run_python


class TestMergedSnapshotHardening(unittest.TestCase):
    def test_cross_platform_parent_traversal_is_blocked(self):
        for candidate in (
            "../main.py",
            "..\\main.py",
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config",
        ):
            with self.subTest(candidate=candidate):
                with self.assertRaises(PermissionError):
                    _safe_path(candidate)

    def test_absolute_paths_are_blocked(self):
        for candidate in ("/etc/passwd", "C:\\Windows\\System32"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(PermissionError):
                    _safe_path(candidate)

    def test_python_sandbox_reports_environment_scrubbing(self):
        write_file("sandbox_probe.py", "print('sandbox-ok')")
        result = run_python("sandbox_probe.py")

        self.assertTrue(result["success"])
        self.assertEqual(result["stdout"].strip(), "sandbox-ok")
        self.assertIn("sandbox", result)
        self.assertTrue(result["sandbox"]["environment_scrubbed"])

    def test_python_sandbox_does_not_inherit_parent_secret(self):
        os.environ["NENUX_TEST_SECRET"] = "should-not-leak"
        try:
            write_file(
                "sandbox_env_probe.py",
                "import os\n"
                "print(os.environ.get('NENUX_TEST_SECRET', 'absent'))\n",
            )
            result = run_python("sandbox_env_probe.py")
            self.assertTrue(result["success"])
            self.assertEqual(result["stdout"].strip(), "absent")
        finally:
            os.environ.pop("NENUX_TEST_SECRET", None)

    def test_python_tool_rejects_non_python_files(self):
        write_file("sandbox_notes.txt", "hello")
        result = run_python("sandbox_notes.txt")

        self.assertFalse(result["success"])
        self.assertIn(".py", result["error"])

    def test_planner_and_evaluator_have_independent_model_config(self):
        self.assertEqual(planner.PLANNER_MODEL, config.PLANNER_MODEL)
        self.assertEqual(evaluator.EVALUATOR_MODEL, config.EVALUATOR_MODEL)


if __name__ == "__main__":
    unittest.main()
