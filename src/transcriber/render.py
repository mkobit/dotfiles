from pathlib import Path
from typing import Any
from jinja2 import Template

DEFAULT_TEMPLATE = """---
model:
  size: {{ metadata.model.size.value }}
  device: {{ metadata.model.device.value }}
  load_time_seconds: {{ metadata.model.load_time_seconds }}
  is_multilingual: {{ metadata.model.is_multilingual }}
  dims:
    n_mels: {{ metadata.model.dims.n_mels }}
    n_vocab: {{ metadata.model.dims.n_vocab }}
    n_audio_layer: {{ metadata.model.dims.n_audio_layer }}
file:
  path: {{ metadata.file.path }}
  size_bytes: {{ metadata.file.size_bytes }}
  duration_seconds: {{ metadata.file.duration_seconds }}
transcription:
  time_seconds: {{ metadata.transcription_time_seconds }}
  timestamp: {{ metadata.timestamp.format_common_iso() }}
  whisper_version: {{ metadata.whisper_version }}
---

{{ text }}
"""


def render_template(template_path: Path | None, data: dict[str, Any]) -> str:
    """Renders the transcription output using Jinja2.

    Args:
        template_path: Path to a Jinja2 template file. If None, uses the default template.
        data: Context dictionary for the template.

    Returns:
        Rendered string.
    """
    if template_path:
        content = template_path.read_text(encoding="utf-8")
        template = Template(content)
    else:
        template = Template(DEFAULT_TEMPLATE)

    return str(template.render(**data))
