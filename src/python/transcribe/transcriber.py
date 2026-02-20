from typing import Iterable, Tuple, Optional, Any
from faster_whisper import WhisperModel

class Transcriber:
    def __init__(self, model_size: str = "base", device: str = "auto", compute_type: str = "default"):
        """
        Initialize the Transcriber with a specific model size and device.

        Args:
            model_size: Size of the Whisper model (tiny, base, small, medium, large-v3).
            device: Device to use (cpu, cuda, auto).
            compute_type: Type of computation (float16, int8_float16, int8, default).
        """
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Tuple[Iterable[Any], Any]:
        """
        Transcribe an audio file.

        Args:
            audio_path: Path to the audio file.
            language: Language code (optional).

        Returns:
            A tuple containing a generator of segments and info object.
        """
        return self.model.transcribe(audio_path, language=language, beam_size=5)  # type: ignore
