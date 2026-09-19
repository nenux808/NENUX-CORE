import unittest
from unittest.mock import patch

import main


class TestClaraConversation(unittest.TestCase):
    @patch("main.call_model")
    def test_voice_session_preserves_clara_turns(self, mock_call_model):
        mock_call_model.return_value = "Yep, I remember that."

        history = [
            {"role": "user", "content": "My favorite test number is 42."},
            {"role": "assistant", "content": "Got it, 42."},
        ]

        reply = main.run_conversation(
            "what number did I just tell you?",
            history,
            interface_name="Clara",
        )

        self.assertEqual(reply, "Yep, I remember that.")
        messages = mock_call_model.call_args.args[0]
        self.assertIn(history[0], messages)
        self.assertIn(history[1], messages)
        self.assertIn("You are Clara", messages[0]["content"])


if __name__ == "__main__":
    unittest.main()
