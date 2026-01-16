from dataclasses import dataclass
from enum import Enum, unique
from typing import Optional

@unique
class ModelSize(str, Enum):
    TINY = "tiny"
    TINY_EN = "tiny.en"
    BASE = "base"
    BASE_EN = "base.en"
    SMALL = "small"
    SMALL_EN = "small.en"
    MEDIUM = "medium"
    MEDIUM_EN = "medium.en"
    LARGE = "large"
    LARGE_V1 = "large-v1"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"
    DISTIL_LARGE_V2 = "distil-large-v2"
    DISTIL_MEDIUM_EN = "distil-medium.en"
    DISTIL_SMALL_EN = "distil-small.en"

@unique
class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"
    AUTO = "auto"

@unique
class ComputeType(str, Enum):
    INT8 = "int8"
    INT8_FLOAT16 = "int8_float16"
    INT16 = "int16"
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    AUTO = "auto"

@dataclass(frozen=True)
class ModelInfo:
    size: ModelSize
    device: Device
    compute_type: ComputeType
    load_time_seconds: float

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
    timestamp: str
