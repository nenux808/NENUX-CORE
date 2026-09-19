import unittest

from interface.neural_tts import sanitize_for_speech


class TestSpeechSanitizer(unittest.TestCase):
    def test_removes_emoji_from_spoken_text(self):
        self.assertEqual(
            sanitize_for_speech("I'm doing great! 😊"),
            "I'm doing great!",
        )

    def test_removes_multiple_emoji(self):
        self.assertEqual(
            sanitize_for_speech("That worked 😂😂 nice!"),
            "That worked nice!",
        )

    def test_removes_raw_urls_from_spoken_text(self):
        self.assertEqual(
            sanitize_for_speech("Check https://www.spacex.com/updates for updates."),
            "Check for updates.",
        )

    def test_keeps_markdown_link_label_but_not_url(self):
        self.assertEqual(
            sanitize_for_speech("See [SpaceX updates](https://www.spacex.com/updates) for details."),
            "See SpaceX updates for details.",
        )

    def test_preserves_normal_punctuation(self):
        self.assertEqual(
            sanitize_for_speech("Hey, I'm Clara. How are you?"),
            "Hey, I'm Clara. How are you?",
        )


if __name__ == "__main__":
    unittest.main()
