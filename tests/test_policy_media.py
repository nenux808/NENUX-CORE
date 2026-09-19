import unittest

from core.policy import (
    is_full_lyrics_request,
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

    def test_yes_please_blocks_full_lyrics_followup(self):
        history = [
            {"role": "assistant", "content": "I can share the lyrics if needed."},
        ]
        self.assertTrue(is_full_lyrics_request("Yes, please.", history))

    def test_direct_full_lyrics_request_is_blocked(self):
        self.assertTrue(is_full_lyrics_request("show me the lyrics", []))

    def test_open_ended_lyrics_question_is_blocked(self):
        self.assertTrue(
            is_full_lyrics_request(
                "do you know any lyrics from Ocean Eyes by Billie Eilish?",
                [],
            )
        )


if __name__ == "__main__":
    unittest.main()
