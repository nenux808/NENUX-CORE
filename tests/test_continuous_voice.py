import unittest

import numpy as np

from clara import resolve_voice_command
from interface.microphone import rms_level


class TestVoiceActivityHelpers(unittest.TestCase):
    def test_rms_level_detects_silence(self):
        audio = np.zeros((1600, 1), dtype=np.int16)
        self.assertEqual(rms_level(audio), 0.0)

    def test_rms_level_detects_signal(self):
        audio = np.full((1600, 1), 2000, dtype=np.int16)
        self.assertGreater(rms_level(audio), 0.01)


class TestContinuousVoiceRouting(unittest.TestCase):
    def test_requires_wake_phrase_before_session_is_active(self):
        command, active = resolve_voice_command("my favorite number is 42", False)
        self.assertIsNone(command)
        self.assertFalse(active)

    def test_wake_phrase_activates_session(self):
        command, active = resolve_voice_command("Hey Clara, my favorite number is 42", False)
        self.assertEqual(command, "my favorite number is 42")
        self.assertTrue(active)

    def test_active_session_accepts_follow_up_without_wake_phrase(self):
        command, active = resolve_voice_command("what number did I just tell you?", True)
        self.assertEqual(command, "what number did I just tell you?")
        self.assertTrue(active)


if __name__ == "__main__":
    unittest.main()
