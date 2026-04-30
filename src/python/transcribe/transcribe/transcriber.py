from collections.abc import Iterable
from typing import Protocol

from faster_whisper import WhisperModel

from transcribe.models import TranscriptionInfo, TranscriptionSegment


class Transcriber(Protocol):
    """Protocol for audio transcribers."""

    def transcribe(
        self, audio_path: str, language: str | None = None
    ) -> tuple[Iterable[TranscriptionSegment], TranscriptionInfo]:
        """Transcribe an audio file and return a generator of segments and info."""
        ...


class FasterWhisperTranscriber:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "default",
    ) -> None:
        """Initialize the FasterWhisperTranscriber with a specific model size and device."""
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(
        self, audio_path: str, language: str | None = None
    ) -> tuple[Iterable[TranscriptionSegment], TranscriptionInfo]:
        """Transcribe an audio file using faster-whisper."""
        segments, info = self.model.transcribe(audio_path, language=language, beam_size=5)

        # Map to abstraction models
        mapped_info = TranscriptionInfo(
            language=info.language, language_probability=info.language_probability, duration=info.duration
        )

        def segment_generator() -> Iterable[TranscriptionSegment]:
            for segment in segments:
                yield TranscriptionSegment(start=segment.start, end=segment.end, text=segment.text)

        return segment_generator(), mapped_info
