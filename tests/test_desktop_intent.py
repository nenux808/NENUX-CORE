import unittest
from unittest.mock import patch, MagicMock

from core.desktop_intent import (
    desktop_intent_command,
    desktop_intent_plan,
    desktop_intent_tool_call,
    interpret_desktop_intent,
)


class TestDesktopIntent(unittest.TestCase):
    @patch("core.desktop_intent.chat")
    def test_garbled_close_all_tabs_is_understood(self, mock_chat):
        response = MagicMock()
        response.message.content = '{"intent":"close_all_tabs","confidence":0.93}'
        mock_chat.return_value = response

        result = interpret_desktop_intent("Can you close all chrome times?")

        self.assertEqual(result["intent"], "close_all_tabs")
        self.assertGreaterEqual(result["confidence"], 0.9)

    def test_close_all_tabs_has_canonical_command(self):
        self.assertEqual(
            desktop_intent_command("close_all_tabs"),
            "close all tabs in the current Chrome window",
        )

    def test_close_all_tabs_maps_to_whitelisted_tool(self):
        self.assertEqual(
            desktop_intent_tool_call("close_all_tabs"),
            {
                "tool": "chrome_tab_control",
                "arguments": {"action": "close_all_tabs"},
            },
        )

    def test_close_all_tabs_has_deterministic_plan(self):
        self.assertEqual(
            desktop_intent_plan("close_all_tabs"),
            ["Close all tabs in the current Chrome window using chrome_tab_control"],
        )


if __name__ == "__main__":
    unittest.main()
