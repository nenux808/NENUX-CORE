"""Microphone capture for NENUX Core."""

import wave
from pathlib import Path

import numpy as np

from config import (
    MICROPHONE_CHANNELS,
    MICROPHONE_CHUNK_SECONDS,
    MICROPHONE_MAX_UTTERANCE_SECONDS,
    MICROPHONE_RECORD_SECONDS,
    MICROPHONE_SAMPLE_RATE,
    MICROPHONE_SILENCE_SECONDS,
    MICROPHONE_SPEECH_RMS_THRESHOLD,
    MICROPHONE_START_TIMEOUT_SECONDS,
)


def _write_wav(path: Path, audio: np.ndarray, sample_rate: int, channels: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio.astype(np.int16, copy=False).tobytes())

    return path


def record_wav(
    output_path: str | Path,
    seconds: float = MICROPHONE_RECORD_SECONDS,
    sample_rate: int = MICROPHONE_SAMPLE_RATE,
    channels: int = MICROPHONE_CHANNELS,
) -> Path:
    """Record a fixed-duration PCM WAV file."""
    import sounddevice as sd

    path = Path(output_path)
    frames = int(seconds * sample_rate)
    audio = sd.rec(
        frames,
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
    )
    sd.wait()
    return _write_wav(path, audio, sample_rate, channels)


def rms_level(audio: np.ndarray) -> float:
    """Return normalized RMS amplitude for int16 microphone audio."""
    if audio.size == 0:
        return 0.0

    samples = audio.astype(np.float32) / 32768.0
    return float(np.sqrt(np.mean(np.square(samples))))


def record_until_silence(
    output_path: str | Path,
    sample_rate: int = MICROPHONE_SAMPLE_RATE,
    channels: int = MICROPHONE_CHANNELS,
    chunk_seconds: float = MICROPHONE_CHUNK_SECONDS,
    start_timeout: float = MICROPHONE_START_TIMEOUT_SECONDS,
    max_seconds: float = MICROPHONE_MAX_UTTERANCE_SECONDS,
    silence_seconds: float = MICROPHONE_SILENCE_SECONDS,
    speech_threshold: float = MICROPHONE_SPEECH_RMS_THRESHOLD,
) -> tuple[Path, bool]:
    """Record until speech ends, returning (path, speech_detected).

    This is a lightweight local energy-based voice activity gate. It waits for
    speech, captures the full utterance, and stops after sustained silence.
    """
    import sounddevice as sd

    path = Path(output_path)
    frames_per_chunk = max(1, int(chunk_seconds * sample_rate))
    max_chunks = max(1, int(max_seconds / chunk_seconds))
    start_chunks = max(1, int(start_timeout / chunk_seconds))
    silence_chunks_needed = max(1, int(silence_seconds / chunk_seconds))

    chunks: list[np.ndarray] = []
    speech_started = False
    silent_chunks = 0

    for index in range(max_chunks):
        chunk = sd.rec(
            frames_per_chunk,
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
        )
        sd.wait()
        chunk = np.asarray(chunk, dtype=np.int16)

        level = rms_level(chunk)
        is_speech = level >= speech_threshold

        if not speech_started:
            if is_speech:
                speech_started = True
                chunks.append(chunk)
            elif index + 1 >= start_chunks:
                empty = np.zeros((0, channels), dtype=np.int16)
                return _write_wav(path, empty, sample_rate, channels), False
            continue

        chunks.append(chunk)

        if is_speech:
            silent_chunks = 0
        else:
            silent_chunks += 1
            if silent_chunks >= silence_chunks_needed:
                break

    if not chunks:
        empty = np.zeros((0, channels), dtype=np.int16)
        return _write_wav(path, empty, sample_rate, channels), False

    audio = np.concatenate(chunks, axis=0)
    return _write_wav(path, audio, sample_rate, channels), True
