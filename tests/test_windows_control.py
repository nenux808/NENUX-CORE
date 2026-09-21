import unittest
from unittest.mock import patch, MagicMock

from tools.windows_control import (
    _resolve_profile_selector,
    open_chrome_url,
    open_youtube_search,
)


class TestWindowsChromeControl(unittest.TestCase):
    def test_profile_selector_accepts_ordinal(self):
        profiles = [
            {"directory": "Default", "name": "A", "email": ""},
            {"directory": "Profile 1", "name": "B", "email": ""},
        ]
        self.assertEqual(
            _resolve_profile_selector("first", profiles),
            "Default",
        )
        self.assertEqual(
            _resolve_profile_selector("second", profiles),
            "Profile 1",
        )

    def test_profile_selector_accepts_visible_name(self):
        profiles = [
            {
                "directory": "Profile 2",
                "name": "Personal",
                "email": "person@example.com",
            }
        ]
        self.assertEqual(
            _resolve_profile_selector("Personal", profiles),
            "Profile 2",
        )
        self.assertEqual(
            _resolve_profile_selector("person@example.com", profiles),
            "Profile 2",
        )

    @patch("tools.windows_control._find_chrome_executable")
    @patch("tools.windows_control.list_chrome_profiles")
    def test_multiple_profiles_require_selection(
        self,
        mock_profiles,
        mock_chrome,
    ):
        mock_chrome.return_value = MagicMock()
        mock_profiles.return_value = {
            "success": True,
            "saved_default": None,
            "profiles": [
                {"directory": "Default", "name": "Personal", "email": ""},
                {"directory": "Profile 1", "name": "Work", "email": ""},
            ],
        }

        result = open_chrome_url("https://www.youtube.com/watch?v=test")

        self.assertTrue(result["success"])
        self.assertFalse(result["opened"])
        self.assertTrue(result["needs_profile_selection"])

    @patch("tools.windows_control.subprocess.Popen")
    @patch("tools.windows_control._find_chrome_executable")
    @patch("tools.windows_control.list_chrome_profiles")
    def test_visible_profile_name_launches_selected_profile(
        self,
        mock_profiles,
        mock_chrome,
        mock_popen,
    ):
        mock_chrome.return_value = MagicMock(__str__=lambda self: "chrome.exe")
        mock_profiles.return_value = {
            "success": True,
            "saved_default": None,
            "profiles": [
                {"directory": "Profile 2", "name": "Personal", "email": ""},
            ],
        }

        result = open_chrome_url(
            "https://www.youtube.com/watch?v=test",
            profile_directory="Personal",
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["opened"])
        self.assertEqual(result["profile_directory"], "Profile 2")
        mock_popen.assert_called_once()

    @patch("tools.windows_control.open_chrome_url")
    def test_youtube_search_builds_results_url(self, mock_open):
        mock_open.return_value = {
            "success": True,
            "opened": True,
            "profile_directory": "Default",
            "url": "https://www.youtube.com/results?search_query=weekends+playlist",
        }

        result = open_youtube_search("weekends playlist")

        self.assertTrue(result["success"])
        self.assertTrue(result["opened"])
        self.assertEqual(result["query"], "weekends playlist")
        self.assertEqual(result["target"], "youtube_search")
        mock_open.assert_called_once_with(
            "https://www.youtube.com/results?search_query=weekends+playlist",
            profile_directory=None,
        )


if __name__ == "__main__":
    unittest.main()
