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

        self.assertEqual(
            voice.receive(),
            "hello core",
        )

    def test_respond_speaks_non_empty_reply(self):
        tts = FakeTTS()
        voice = VoiceInterface(
            stt=FakeSTT("hello"),
            tts=tts,
        )

        voice.respond("NENUX online")

        self.assertEqual(
            tts.spoken,
            ["NENUX online"],
        )

    def test_respond_ignores_empty_reply(self):
        tts = FakeTTS()
        voice = VoiceInterface(
            stt=FakeSTT("hello"),
            tts=tts,
        )

        voice.respond("   ")

        self.assertEqual(
            tts.spoken,
            [],
        )


if __name__ == "__main__":
    unittest.main()


class FakeSegment:
    def __init__(self, text: str):
        self.text = text


class FakeWhisperModel:
    def transcribe(self, path: str, vad_filter: bool, initial_prompt: str, **kwargs):
        self.path = path
        self.vad_filter = vad_filter
        self.initial_prompt = initial_prompt
        self.kwargs = kwargs
        return (
            [
                FakeSegment(" Hello "),
                FakeSegment(" from NENUX "),
            ],
            object(),
        )


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
            self.assertIn("Clara", fake_model.initial_prompt)
            self.assertFalse(fake_model.kwargs["condition_on_previous_text"])
            self.assertIn("no_speech_threshold", fake_model.kwargs)

    def test_transcribe_file_requires_existing_audio(self):
        stt = FasterWhisperSTT(model=FakeWhisperModel())

        with self.assertRaises(FileNotFoundError):
            stt.transcribe_file("missing-audio.wav")
