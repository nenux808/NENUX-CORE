import unittest
from unittest.mock import patch

import main


class TestClaraConversation(unittest.TestCase):
    @patch("main.call_model")
    def test_voice_history_does_not_override_clara_identity(self, mock_call_model):
        mock_call_model.return_value = "I'm Clara, doing great!"

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I'm NENUX Core."},
        ]

        reply = main.run_conversation(
            "how are you?",
            history,
            interface_name="Clara",
        )

        self.assertEqual(reply, "I'm Clara, doing great!")
        messages = mock_call_model.call_args.args[0]
        self.assertFalse(
            any(
                message.get("role") == "assistant"
                and "NENUX Core" in message.get("content", "")
                for message in messages
            )
        )


if __name__ == "__main__":
    unittest.main()
