import jinja2
from typing import Dict, Any

def render_template(template_path: str, data: Dict[str, Any]) -> str:
    """Renders a Jinja2 template with the provided data."""
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()

        env = jinja2.Environment(
            loader=jinja2.BaseLoader(),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        template = env.from_string(template_content)
        return template.render(**data)
    except Exception as e:
        raise RuntimeError(f"Failed to render template {template_path}: {e}")
