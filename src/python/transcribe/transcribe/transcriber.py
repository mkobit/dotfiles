from collections.abc import Iterable
from typing import Any

from faster_whisper import WhisperModel


class Transcriber:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "default",
    ) -> None:
        """Initialize the Transcriber with a specific model size and device."""
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: str | None = None) -> tuple[Iterable[Any], Any]:
        """Transcribe an audio file."""
        return self.model.transcribe(audio_path, language=language, beam_size=5)
