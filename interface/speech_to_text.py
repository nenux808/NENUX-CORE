"""faster-whisper speech-to-text adapter for NENUX Core."""

from pathlib import Path
from typing import Any

from config import STT_COMPUTE_TYPE, STT_DEVICE, STT_MODEL


class FasterWhisperSTT:
    """Transcribe audio files locally with a lazily loaded Whisper model."""

    def __init__(
        self,
        model_size: str = STT_MODEL,
        device: str = STT_DEVICE,
        compute_type: str = STT_COMPUTE_TYPE,
        model: Any = None,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = model

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
        )

        return " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()
