import unittest

from core.policy import (
    enforce_lyrics_output_policy,
    is_effective_lyrics_request,
    is_history_query,
    is_lyrics_context_followup,
    is_media_content_request,
    memory_only_mode,
)


class TestPolicyMediaMemory(unittest.TestCase):
    def test_media_request_is_detected(self):
        self.assertTrue(is_media_content_request("show me the lyrics to Ocean Eyes"))

    def test_lyrics_are_not_personal_history(self):
        self.assertFalse(is_history_query("do you remember any lyric from Ocean Eyes?"))

    def test_lyrics_do_not_enter_memory_only_mode(self):
        self.assertFalse(memory_only_mode("do you remember any lyric from Ocean Eyes?"))

    def test_real_prior_work_still_uses_history(self):
        self.assertTrue(is_history_query("do you remember what we did last time?"))
        self.assertTrue(memory_only_mode("do you remember what we did last time?"))

    def test_yes_please_keeps_lyrics_context(self):
        history = [
            {"role": "user", "content": "Do you know any lyric from Ocean Eyes?"},
            {"role": "assistant", "content": "I can provide a short verified lyric excerpt."},
        ]
        self.assertTrue(is_lyrics_context_followup("Yes, please.", history))

    def test_open_ended_lyrics_remain_media_not_memory(self):
        text = "do you know any lyrics from Ocean Eyes by Billie Eilish?"
        self.assertTrue(is_media_content_request(text))
        self.assertFalse(memory_only_mode(text))

    def test_long_lyric_output_is_replaced(self):
        response = '"one two three four five six seven eight nine ten eleven twelve"'
        filtered = enforce_lyrics_output_policy(
            "show me lyrics from a song",
            response,
        )
        self.assertNotEqual(filtered, response)
        self.assertIn("brief summary", filtered)

    def test_short_lyric_excerpt_can_pass(self):
        response = '"one two three four five six seven eight nine ten"'
        self.assertEqual(
            enforce_lyrics_output_policy("any lyric from a song?", response),
            response,
        )

    def test_yes_please_is_effective_lyrics_request(self):
        history = [
            {"role": "user", "content": "Do you know any lyrics from Ocean Eyes?"},
            {"role": "assistant", "content": "I can share a short verified excerpt."},
        ]
        self.assertTrue(
            is_effective_lyrics_request("Yes, please.", history)
        )

    def test_yes_please_long_lyric_output_is_filtered(self):
        history = [
            {"role": "user", "content": "Do you know any lyrics from Ocean Eyes?"},
            {"role": "assistant", "content": "I can share a short verified excerpt."},
        ]
        response = '"one two three four five six seven eight nine ten eleven twelve"'
        filtered = enforce_lyrics_output_policy(
            "Yes, please.",
            response,
            history=history,
        )
        self.assertNotEqual(filtered, response)
        self.assertIn("brief summary", filtered)


if __name__ == "__main__":
    unittest.main()
