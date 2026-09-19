"""faster-whisper speech-to-text adapter for NENUX Core."""

from pathlib import Path
from typing import Any

from config import (
    STT_COMPUTE_TYPE,
    STT_DEVICE,
    STT_INITIAL_PROMPT,
    STT_MODEL,
    STT_SEGMENT_MAX_NO_SPEECH_PROB,
    STT_SEGMENT_MIN_AVG_LOGPROB,
)


KNOWN_HALLUCINATIONS = {
    "this is a conversation with nenux core",
    "this is a conversation with clara the voice interface for nenux core",
    "hey clara clara",
}


def _normalize_transcript(text: str) -> str:
    return " ".join(
        text.lower()
        .replace(".", " ")
        .replace(",", " ")
        .replace("!", " ")
        .replace("?", " ")
        .split()
    )


def _segment_is_confident(segment: Any) -> bool:
    """Reject segments Whisper itself marks as probable silence/low confidence."""
    no_speech_prob = getattr(segment, "no_speech_prob", 0.0)
    avg_logprob = getattr(segment, "avg_logprob", 0.0)

    return (
        no_speech_prob <= STT_SEGMENT_MAX_NO_SPEECH_PROB
        and avg_logprob >= STT_SEGMENT_MIN_AVG_LOGPROB
    )


class FasterWhisperSTT:
    """Transcribe audio files locally with a lazily loaded Whisper model."""

    def __init__(
        self,
        model_size: str = STT_MODEL,
        device: str = STT_DEVICE,
        compute_type: str = STT_COMPUTE_TYPE,
        model: Any = None,
        initial_prompt: str = STT_INITIAL_PROMPT,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = model
        self.initial_prompt = initial_prompt

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )

        return self._model

    def transcribe_file(self, audio_path: str | Path) -> str:
        path = Path(audio_path)

        if not path.is_file():
            raise FileNotFoundError(f"Audio file not found: {path}")

        segments, _ = self._get_model().transcribe(
            str(path),
            vad_filter=True,
            initial_prompt=self.initial_prompt or None,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip() and _segment_is_confident(segment)
        ).strip()

        if _normalize_transcript(transcript) in KNOWN_HALLUCINATIONS:
            return ""

        return transcript
