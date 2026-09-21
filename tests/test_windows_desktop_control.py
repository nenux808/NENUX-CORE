import unittest
from unittest.mock import patch

from tools.windows_desktop_control import (
    chrome_tab_control,
    media_control,
    open_gmail,
    open_file_explorer,
    youtube_media_control,
)


class TestWindowsDesktopControl(unittest.TestCase):
    @patch("tools.windows_desktop_control._press_key")
    def test_pause_uses_media_key(self, mock_press):
        result = media_control("pause")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "pause")
        mock_press.assert_called_once()

    @patch("tools.windows_desktop_control._press_key")
    def test_volume_up_uses_media_key(self, mock_press):
        result = media_control("volume_up")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "volume_up")
        mock_press.assert_called_once()

    @patch("tools.windows_desktop_control._press_chord")
    @patch("tools.windows_desktop_control.focus_chrome")
    def test_close_tab_focuses_chrome_then_uses_shortcut(
        self,
        mock_focus,
        mock_chord,
    ):
        mock_focus.return_value = {
            "success": True,
            "title": "YouTube - Google Chrome",
        }

        result = chrome_tab_control("close_tab")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "close_tab")
        mock_focus.assert_called_once()
        mock_chord.assert_called_once()

    @patch("tools.windows_desktop_control.open_chrome_url")
    @patch("tools.windows_desktop_control.set_default_chrome_profile")
    @patch("tools.windows_desktop_control.list_chrome_profiles")
    def test_gmail_uses_first_profile_when_no_default(
        self,
        mock_profiles,
        mock_set_default,
        mock_open,
    ):
        mock_profiles.return_value = {
            "success": True,
            "saved_default": None,
            "profiles": [
                {"directory": "Default", "name": "Personal", "email": ""},
                {"directory": "Profile 1", "name": "Work", "email": ""},
            ],
        }
        mock_open.return_value = {
            "success": True,
            "opened": True,
            "profile_directory": "Default",
        }

        result = open_gmail()

        self.assertTrue(result["success"])
        self.assertTrue(result["opened"])
        mock_set_default.assert_called_once_with("Default")
        mock_open.assert_called_once_with(
            "https://mail.google.com/",
            profile_directory="Default",
        )

    @patch("tools.windows_desktop_control._press_key")
    @patch("tools.windows_desktop_control._focus_window")
    @patch("tools.windows_desktop_control._visible_chrome_windows")
    def test_youtube_resume_targets_youtube_window(
        self,
        mock_windows,
        mock_focus,
        mock_press,
    ):
        mock_windows.return_value = [
            (100, "Music Video - YouTube - Google Chrome"),
        ]
        mock_focus.return_value = True

        result = youtube_media_control("resume")

        self.assertTrue(result["success"])
        self.assertEqual(result["target"], "youtube")
        self.assertFalse(result["verified_playback_state"])
        mock_focus.assert_called_once_with(100)
        mock_press.assert_called_once()

    @patch("tools.windows_desktop_control._visible_chrome_windows")
    def test_youtube_resume_fails_without_visible_youtube(self, mock_windows):
        mock_windows.return_value = [(100, "Gmail - Google Chrome")]

        result = youtube_media_control("resume")

        self.assertFalse(result["success"])
        self.assertIn("YouTube", result["error"])

    @patch("tools.windows_desktop_control._press_key")
    def test_unmute_uses_mute_toggle_key(self, mock_press):
        result = media_control("unmute")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "unmute")
        mock_press.assert_called_once()

    @patch("tools.windows_desktop_control._press_chord")
    @patch("tools.windows_desktop_control.focus_chrome")
    def test_close_all_tabs_uses_window_close_shortcut(
        self,
        mock_focus,
        mock_chord,
    ):
        mock_focus.return_value = {
            "success": True,
            "title": "Chrome",
        }

        result = chrome_tab_control("close_all_tabs")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "close_all_tabs")
        mock_focus.assert_called_once()
        mock_chord.assert_called_once()

    @patch("tools.windows_desktop_control.subprocess.Popen")
    def test_open_file_explorer_launches_explorer(self, mock_popen):
        result = open_file_explorer()

        self.assertTrue(result["success"])
        self.assertTrue(result["opened"])
        self.assertEqual(result["application"], "File Explorer")
        mock_popen.assert_called_once_with(
            ["explorer.exe"],
            close_fds=True,
        )


if __name__ == "__main__":
    unittest.main()
