import unittest

from core.permissions import get_permission_level


class TestPcControlPermissions(unittest.TestCase):
    def test_chrome_url_launch_is_trusted(self):
        self.assertEqual(get_permission_level("open_chrome_url"), "safe")

    def test_python_execution_still_requires_review(self):
        self.assertEqual(get_permission_level("run_python"), "review")


if __name__ == "__main__":
    unittest.main()
