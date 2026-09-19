"""Local neural text-to-speech for Clara using Kokoro."""

import re
import unicodedata

import numpy as np
import sounddevice as sd

from config import (
    CLARA_TTS_SAMPLE_RATE,
    CLARA_TTS_SPEED,
    CLARA_TTS_VOICE,
)


def sanitize_for_speech(text: str) -> str:
    """Remove visual-only symbols that should not be spoken aloud."""
    # URLs are useful on screen but terrible spoken output. Remove them before
    # synthesis while leaving the visible Clara response unchanged.
    cleaned = re.sub(r"https?://[^\\s)\\]}>]+", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"www\\.[^\\s)\\]}>]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\\[[^\\]]+\\]\\([^\\s)]+\\)", lambda m: m.group(0).split("](")[0][1:], cleaned)

    cleaned = "".join(
        char
        for char in text
        if not unicodedata.category(char).startswith(("So", "Sk"))
    )
    cleaned = re.sub(r"\s+([,.!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class KokoroTTS:
    """Generate and play Clara speech locally with Kokoro-82M."""

    def __init__(
        self,
        voice: str = CLARA_TTS_VOICE,
        speed: float = CLARA_TTS_SPEED,
    ):
        self.voice = voice
        self.speed = speed
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            from kokoro import KPipeline
            self._pipeline = KPipeline(lang_code="a")
        return self._pipeline

    def speak(self, text: str) -> None:
        message = sanitize_for_speech(text)
        if not message:
            return

        chunks = []
        generator = self._get_pipeline()(
            message,
            voice=self.voice,
            speed=self.speed,
        )

        for _, _, audio in generator:
            chunks.append(np.asarray(audio, dtype=np.float32))

        if not chunks:
            return

        waveform = np.concatenate(chunks)
        sd.play(waveform, samplerate=CLARA_TTS_SAMPLE_RATE)
        sd.wait()
