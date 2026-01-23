from dataclasses import dataclass
from enum import Enum, unique
from typing import Optional
import whenever


@unique
class ModelSize(str, Enum):
    """
    Available Whisper model sizes.
    Source: https://github.com/openai/whisper#available-models-and-languages
    """

    TINY = "tiny"
    TINY_EN = "tiny.en"
    BASE = "base"
    BASE_EN = "base.en"
    SMALL = "small"
    SMALL_EN = "small.en"
    MEDIUM = "medium"
    MEDIUM_EN = "medium.en"
    LARGE = "large"
    LARGE_V3 = "large-v3"


@unique
class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    AUTO = "auto"


@dataclass(frozen=True)
class ModelDimensions:
    n_mels: int
    n_audio_ctx: int
    n_audio_state: int
    n_audio_head: int
    n_audio_layer: int
    n_vocab: int
    n_text_ctx: int
    n_text_state: int
    n_text_head: int
    n_text_layer: int


@dataclass(frozen=True)
class ModelInfo:
    size: ModelSize
    device: Device
    load_time_seconds: float
    dims: ModelDimensions
    is_multilingual: bool


@dataclass(frozen=True)
class FileInfo:
    path: str
    size_bytes: int
    duration_seconds: Optional[float] = None


@dataclass(frozen=True)
class TranscriptionMetadata:
    model: ModelInfo
    file: FileInfo
    transcription_time_seconds: float
    timestamp: whenever.Instant
    whisper_version: str
