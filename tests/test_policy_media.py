import unittest

from core.policy import is_history_query, is_media_content_request, memory_only_mode


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


if __name__ == "__main__":
    unittest.main()
