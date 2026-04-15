import os
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

from transcribe.utils import format_timestamp


class Formatter:
    DEFAULT_TEMPLATE = "{% for seg in segments %}{{ seg.text }}\n{% endfor %}"

    @staticmethod
    def format_segments(
        segments: list[Any],
        info: Any,
        template_file: str | None = None,
        template_string: str | None = None,
    ) -> str:
        """Format transcription segments using Jinja2 templates."""
        context = {
            "segments": segments,
            "info": info,
            "format_timestamp": format_timestamp,
        }

        if template_file:
            env = Environment(
                loader=FileSystemLoader(os.path.dirname(os.path.abspath(template_file)))
            )
            template = env.get_template(os.path.basename(template_file))
            return str(template.render(context))
        if template_string:
            template = Template(template_string)
            return str(template.render(context))
        template = Template(Formatter.DEFAULT_TEMPLATE)
        return str(template.render(context))
