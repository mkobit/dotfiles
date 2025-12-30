from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum

class ModelSize(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V3 = "large-v3"

class Device(str, Enum):
    AUTO = "auto"
    CUDA = "cuda"
    CPU = "cpu"

class ComputeType(str, Enum):
    DEFAULT = "default"
    FLOAT16 = "float16"
    INT8_FLOAT16 = "int8_float16"
    INT8 = "int8"

@dataclass(frozen=True)
class ModelInfo:
    name: str
    size: str
    device: str
    compute_type: str

@dataclass(frozen=True)
class FileInfo:
    path: str
    name: str
    size_bytes: int
    duration_seconds: Optional[float] = None

@dataclass(frozen=True)
class TranscriptionMetadata:
    transcription_time_seconds: float
    load_time_seconds: float
    model: ModelInfo
    file: FileInfo
    cli_args: Dict[str, Any]
    template_name: str
    tool_version: str

@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    segments: Any
    metadata: TranscriptionMetadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result and metadata to a dictionary for Jinja rendering."""
        return {
            "text": self.text,
            "metadata": {
                "transcription_time_seconds": self.metadata.transcription_time_seconds,
                "load_time_seconds": self.metadata.load_time_seconds,
                "model": {
                    "name": self.metadata.model.name,
                    "size": self.metadata.model.size,
                    "device": self.metadata.model.device,
                    "compute_type": self.metadata.model.compute_type,
                },
                "file": {
                    "path": self.metadata.file.path,
                    "name": self.metadata.file.name,
                    "size_bytes": self.metadata.file.size_bytes,
                    "duration_seconds": self.metadata.file.duration_seconds,
                },
                "cli_args": self.metadata.cli_args,
                "template_name": self.metadata.template_name,
                "tool_version": self.metadata.tool_version,
            }
        }
