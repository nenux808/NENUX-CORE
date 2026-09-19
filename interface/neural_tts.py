"""Local neural text-to-speech for Clara using Kokoro."""

import numpy as np
import sounddevice as sd

from config import (
    CLARA_TTS_SAMPLE_RATE,
    CLARA_TTS_SPEED,
    CLARA_TTS_VOICE,
)


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
        message = text.strip()
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
