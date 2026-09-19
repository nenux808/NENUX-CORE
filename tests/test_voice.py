import unittest

from interface.voice import VoiceInterface


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
