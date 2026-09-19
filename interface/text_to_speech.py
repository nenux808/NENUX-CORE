"""Offline text-to-speech adapter for Clara."""

import pyttsx3


class Pyttsx3TTS:
    """Speak NENUX responses using the host operating system voices."""

    def __init__(self, rate: int = 185, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
        return self._engine

    def speak(self, text: str) -> None:
        message = text.strip()
        if not message:
            return

        engine = self._get_engine()
        engine.say(message)
        engine.runAndWait()
