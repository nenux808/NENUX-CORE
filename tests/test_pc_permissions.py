import unittest

from core.permissions import get_permission_level


class TestPcControlPermissions(unittest.TestCase):
    def test_chrome_url_launch_is_trusted(self):
        self.assertEqual(get_permission_level("open_chrome_url"), "safe")

    def test_desktop_controls_are_trusted(self):
        for tool in (
            "media_control",
            "open_chrome",
            "focus_chrome",
            "chrome_tab_control",
            "open_gmail",
            "open_vscode",
        ):
            self.assertEqual(get_permission_level(tool), "safe")

    def test_python_execution_still_requires_review(self):
        self.assertEqual(get_permission_level("run_python"), "review")


if __name__ == "__main__":
    unittest.main()
