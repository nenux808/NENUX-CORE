"""Microphone capture for NENUX Core."""

import wave
from collections import deque
from pathlib import Path

import numpy as np

from config import (
    MICROPHONE_CHANNELS,
    MICROPHONE_CHUNK_SECONDS,
    MICROPHONE_MAX_ADAPTIVE_THRESHOLD,
    MICROPHONE_MAX_UTTERANCE_SECONDS,
    MICROPHONE_NOISE_CALIBRATION_SECONDS,
    MICROPHONE_NOISE_MULTIPLIER,
    MICROPHONE_PRE_ROLL_SECONDS,
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


def adaptive_speech_threshold(
    noise_levels: list[float],
    floor: float = MICROPHONE_SPEECH_RMS_THRESHOLD,
    multiplier: float = MICROPHONE_NOISE_MULTIPLIER,
    ceiling: float = MICROPHONE_MAX_ADAPTIVE_THRESHOLD,
) -> float:
    """Derive a speech threshold from ambient RMS samples."""
    if not noise_levels:
        return floor

    baseline = float(np.median(np.asarray(noise_levels, dtype=np.float32)))
    return min(ceiling, max(floor, baseline * multiplier))


def calibrate_microphone_threshold(
    sample_rate: int = MICROPHONE_SAMPLE_RATE,
    channels: int = MICROPHONE_CHANNELS,
    chunk_seconds: float = MICROPHONE_CHUNK_SECONDS,
    calibration_seconds: float = MICROPHONE_NOISE_CALIBRATION_SECONDS,
) -> float:
    """Sample ambient audio briefly and return an adaptive speech threshold."""
    import sounddevice as sd

    frames_per_chunk = max(1, int(chunk_seconds * sample_rate))
    calibration_chunks = max(1, int(calibration_seconds / chunk_seconds))
    levels: list[float] = []

    for _ in range(calibration_chunks):
        chunk = sd.rec(
            frames_per_chunk,
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
        )
        sd.wait()
        levels.append(rms_level(np.asarray(chunk, dtype=np.int16)))

    return adaptive_speech_threshold(levels)


def record_until_silence(
    output_path: str | Path,
    sample_rate: int = MICROPHONE_SAMPLE_RATE,
    channels: int = MICROPHONE_CHANNELS,
    chunk_seconds: float = MICROPHONE_CHUNK_SECONDS,
    start_timeout: float = MICROPHONE_START_TIMEOUT_SECONDS,
    max_seconds: float = MICROPHONE_MAX_UTTERANCE_SECONDS,
    silence_seconds: float = MICROPHONE_SILENCE_SECONDS,
    speech_threshold: float = MICROPHONE_SPEECH_RMS_THRESHOLD,
    pre_roll_seconds: float = MICROPHONE_PRE_ROLL_SECONDS,
) -> tuple[Path, bool]:
    """Record until speech ends, returning (path, speech_detected)."""
    import sounddevice as sd

    path = Path(output_path)
    frames_per_chunk = max(1, int(chunk_seconds * sample_rate))
    max_chunks = max(1, int(max_seconds / chunk_seconds))
    start_chunks = max(1, int(start_timeout / chunk_seconds))
    silence_chunks_needed = max(1, int(silence_seconds / chunk_seconds))
    pre_roll_chunks = max(1, int(pre_roll_seconds / chunk_seconds))

    chunks: list[np.ndarray] = []
    pre_roll: deque[np.ndarray] = deque(maxlen=pre_roll_chunks)
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
            pre_roll.append(chunk)

            if is_speech:
                speech_started = True
                chunks.extend(list(pre_roll))
                pre_roll.clear()
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
