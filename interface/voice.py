"""Voice interface boundary for NENUX Core.

This module intentionally contains no microphone, STT, or TTS dependency yet.
It defines the contract so voice can be added without coupling audio code to
the agent runtime.
"""

from dataclasses import dataclass
from typing import Protocol


class SpeechToText(Protocol):
    def listen(self) -> str:
        """Return one transcribed user utterance."""


class TextToSpeech(Protocol):
    def speak(self, text: str) -> None:
        """Speak one NENUX response."""


@dataclass
class VoiceInterface:
    stt: SpeechToText
    tts: TextToSpeech

    def receive(self) -> str:
        return self.stt.listen().strip()

    def respond(self, text: str) -> None:
        if text.strip():
            self.tts.speak(text)
