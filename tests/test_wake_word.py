import unittest

from interface.wake_word import extract_wake_command


class TestWakePhrase(unittest.TestCase):

    def test_extracts_command_after_clara(self):
        self.assertEqual(
            extract_wake_command("Hey Clara, can you hear me?"),
            "can you hear me?",
        )

    def test_wake_phrase_is_case_insensitive(self):
        self.assertEqual(
            extract_wake_command("HEY CLARA open my files"),
            "open my files",
        )

    def test_ignores_unaddressed_transcript(self):
        self.assertIsNone(
            extract_wake_command("Can you hear me?"),
        )

    def test_allows_wake_only(self):
        self.assertEqual(
            extract_wake_command("Hey Clara"),
            "",
        )


if __name__ == "__main__":
    unittest.main()
