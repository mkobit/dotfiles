import json
import sys
import tomllib
from pathlib import Path

import click


@click.command()
@click.argument("command_toml", type=click.Path(exists=True, path_type=Path))
@click.argument("context_json", type=click.Path(exists=True, path_type=Path))
@click.argument("output_md", type=click.Path(path_type=Path))
def main(command_toml: Path, context_json: Path, output_md: Path) -> None:
    """Transform a Gemini extension TOML command + context JSON into a Claude command markdown file.

    The output is a self-contained Claude command: YAML frontmatter with the
    description, the extension context (from the contextFileName) as a preamble,
    and the command prompt as the body.
    """
    try:
        with open(command_toml, "rb") as f:
            cmd = tomllib.load(f)

        with open(context_json, encoding="utf-8") as f:
            ctx_data = json.load(f)

        description = cmd.get("description", "")
        prompt = cmd.get("prompt", "")
        context_body = ctx_data.get("body", "")

        lines: list[str] = []
        lines.append("---")
        lines.append(f"description: {json.dumps(description)}")
        lines.append("---")
        lines.append("")

        if context_body:
            lines.append("# Extension context")
            lines.append("")
            lines.append(context_body.rstrip())
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append(prompt.strip())
        lines.append("")

        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text("\n".join(lines), encoding="utf-8")

    except Exception as e:
        click.echo(f"Error processing {command_toml}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
