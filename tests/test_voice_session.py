import unittest

from interface.session import append_session_turn


class TestVoiceSession(unittest.TestCase):
    def test_appends_user_and_assistant_turn(self):
        history = append_session_turn([], "hello", "Hi there.", max_messages=10)
        self.assertEqual(
            history,
            [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "Hi there."},
            ],
        )

    def test_caps_session_history(self):
        history = [
            {"role": "user", "content": "one"},
            {"role": "assistant", "content": "1"},
            {"role": "user", "content": "two"},
            {"role": "assistant", "content": "2"},
        ]
        updated = append_session_turn(
            history,
            "three",
            "3",
            max_messages=4,
        )
        self.assertEqual(
            updated,
            [
                {"role": "user", "content": "two"},
                {"role": "assistant", "content": "2"},
                {"role": "user", "content": "three"},
                {"role": "assistant", "content": "3"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
