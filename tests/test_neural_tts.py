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

    def test_removes_markdown_bold_markers(self):
        self.assertEqual(
            sanitize_for_speech("The codename is **Atlas**."),
            "The codename is Atlas.",
        )

    def test_removes_markdown_italic_markers(self):
        self.assertEqual(
            sanitize_for_speech("This is *important*."),
            "This is important.",
        )

    def test_removes_inline_code_markers(self):
        self.assertEqual(
            sanitize_for_speech("Run `python clara.py` now."),
            "Run python clara.py now.",
        )

    def test_removes_heading_marker(self):
        self.assertEqual(
            sanitize_for_speech("## Result\nAtlas"),
            "Result\nAtlas",
        )


if __name__ == "__main__":
    unittest.main()
