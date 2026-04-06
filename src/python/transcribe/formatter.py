from typing import List, Any, Optional
import os
from jinja2 import Template, Environment, FileSystemLoader
from src.python.transcribe.utils import format_timestamp


class Formatter:
    DEFAULT_TEMPLATE = "{% for seg in segments %}{{ seg.text }}\n{% endfor %}"

    @staticmethod
    def format_segments(
        segments: List[Any],
        info: Any,
        template_file: Optional[str] = None,
        template_string: Optional[str] = None,
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
        elif template_string:
            template = Template(template_string)
            return str(template.render(context))
        else:
            template = Template(Formatter.DEFAULT_TEMPLATE)
            return str(template.render(context))
