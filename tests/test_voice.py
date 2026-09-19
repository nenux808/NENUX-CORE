import unittest

from interface.voice import VoiceInterface
from interface.speech_to_text import FasterWhisperSTT


class FakeSTT:
    def __init__(self, text: str):
        self.text = text

    def listen(self) -> str:
        return self.text


class FakeTTS:
    def __init__(self):
        self.spoken = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)


class TestVoiceInterface(unittest.TestCase):

    def test_receive_returns_trimmed_transcript(self):
        voice = VoiceInterface(
            stt=FakeSTT("  hello core  "),
            tts=FakeTTS(),
        )
        self.assertEqual(voice.receive(), "hello core")

    def test_respond_speaks_non_empty_reply(self):
        tts = FakeTTS()
        voice = VoiceInterface(stt=FakeSTT("hello"), tts=tts)
        voice.respond("NENUX online")
        self.assertEqual(tts.spoken, ["NENUX online"])

    def test_respond_ignores_empty_reply(self):
        tts = FakeTTS()
        voice = VoiceInterface(stt=FakeSTT("hello"), tts=tts)
        voice.respond("   ")
        self.assertEqual(tts.spoken, [])


class FakeSegment:
    def __init__(self, text: str):
        self.text = text


class FakeWhisperModel:
    def __init__(self, segments=None):
        self.segments = segments or [
            FakeSegment(" Hello "),
            FakeSegment(" from NENUX "),
        ]

    def transcribe(self, path: str, vad_filter: bool, initial_prompt, **kwargs):
        self.path = path
        self.vad_filter = vad_filter
        self.initial_prompt = initial_prompt
        self.kwargs = kwargs
        return (self.segments, object())


class TestFasterWhisperSTT(unittest.TestCase):

    def test_transcribe_file_joins_segments(self):
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
            fake_model = FakeWhisperModel()
            stt = FasterWhisperSTT(model=fake_model)
            transcript = stt.transcribe_file(Path(audio.name))

            self.assertEqual(transcript, "Hello from NENUX")
            self.assertTrue(fake_model.vad_filter)
            self.assertIsNone(fake_model.initial_prompt)
            self.assertIn("Clara", fake_model.kwargs["hotwords"])
            self.assertIn("NENUX", fake_model.kwargs["hotwords"])
            self.assertFalse(fake_model.kwargs["condition_on_previous_text"])

    def test_keeps_low_confidence_metadata_out_of_custom_filtering(self):
        import tempfile

        segment = FakeSegment("real speech")
        segment.no_speech_prob = 0.9
        segment.avg_logprob = -1.5

        with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
            stt = FasterWhisperSTT(model=FakeWhisperModel([segment]))
            self.assertEqual(stt.transcribe_file(audio.name), "real speech")

    def test_rejects_known_prompt_hallucination(self):
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav") as audio:
            fake_model = FakeWhisperModel(
                [FakeSegment("This is a conversation with Clara, the voice interface for NENUX Core.")]
            )
            stt = FasterWhisperSTT(model=fake_model)
            self.assertEqual(stt.transcribe_file(audio.name), "")

    def test_transcribe_file_requires_existing_audio(self):
        stt = FasterWhisperSTT(model=FakeWhisperModel())
        with self.assertRaises(FileNotFoundError):
            stt.transcribe_file("missing-audio.wav")


if __name__ == "__main__":
    unittest.main()
