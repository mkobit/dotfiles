from dataclasses import dataclass, field
from typing import Dict, Any, Optional

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
    model: ModelInfo
    file: FileInfo
    cli_args: Dict[str, Any]
    template_name: str
    tool_version: str

@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    segments: Any  # Storing raw segments if needed, though they might not be serializable directly
    metadata: TranscriptionMetadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result and metadata to a dictionary for Jinja rendering."""
        return {
            "text": self.text,
            "metadata": {
                "transcription_time_seconds": self.metadata.transcription_time_seconds,
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
