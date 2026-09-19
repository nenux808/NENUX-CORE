import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

from clara import resolve_voice_command
from interface.microphone import adaptive_speech_threshold, chunk_contains_speech, rms_level


class TestVoiceActivityHelpers(unittest.TestCase):
    def test_rms_level_detects_silence(self):
        audio = np.zeros((1600, 1), dtype=np.int16)
        self.assertEqual(rms_level(audio), 0.0)

    def test_rms_level_detects_signal(self):
        audio = np.full((1600, 1), 2000, dtype=np.int16)
        self.assertGreater(rms_level(audio), 0.01)

    def test_adaptive_threshold_respects_floor(self):
        self.assertEqual(
            adaptive_speech_threshold([0.0002, 0.0003, 0.0004], floor=0.002),
            0.002,
        )

    def test_adaptive_threshold_tracks_room_noise(self):
        threshold = adaptive_speech_threshold(
            [0.002, 0.0022, 0.0024],
            floor=0.001,
            multiplier=1.8,
            ceiling=0.008,
        )
        self.assertGreater(threshold, 0.003)
        self.assertLessEqual(threshold, 0.008)

    def test_two_stage_gate_rejects_noise_even_when_loud(self):
        fake_module = types.SimpleNamespace(
            Vad=lambda mode: types.SimpleNamespace(
                is_speech=lambda frame, sample_rate: False
            )
        )
        audio = np.full((1600, 1), 3000, dtype=np.int16)

        with patch.dict(sys.modules, {"webrtcvad": fake_module}):
            self.assertFalse(
                chunk_contains_speech(
                    audio,
                    speech_threshold=0.002,
                    sample_rate=16000,
                )
            )

    def test_two_stage_gate_accepts_speech_like_frames(self):
        fake_module = types.SimpleNamespace(
            Vad=lambda mode: types.SimpleNamespace(
                is_speech=lambda frame, sample_rate: True
            )
        )
        audio = np.full((1600, 1), 3000, dtype=np.int16)

        with patch.dict(sys.modules, {"webrtcvad": fake_module}):
            self.assertTrue(
                chunk_contains_speech(
                    audio,
                    speech_threshold=0.002,
                    sample_rate=16000,
                )
            )


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
