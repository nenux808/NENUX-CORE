import unittest
from unittest.mock import patch

from tools.windows_desktop_control import (
    chrome_tab_control,
    media_control,
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


if __name__ == "__main__":
    unittest.main()
