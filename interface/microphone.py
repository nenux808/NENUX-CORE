"""Microphone capture for NENUX Core."""

import wave
from pathlib import Path

from config import (
    MICROPHONE_CHANNELS,
    MICROPHONE_RECORD_SECONDS,
    MICROPHONE_SAMPLE_RATE,
)


def record_wav(
    output_path: str | Path,
    seconds: float = MICROPHONE_RECORD_SECONDS,
    sample_rate: int = MICROPHONE_SAMPLE_RATE,
    channels: int = MICROPHONE_CHANNELS,
) -> Path:
    """Record PCM audio from the default microphone into a WAV file."""
    import sounddevice as sd

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    frames = int(seconds * sample_rate)
    audio = sd.rec(
        frames,
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
    )
    sd.wait()

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.tobytes())

    return path
