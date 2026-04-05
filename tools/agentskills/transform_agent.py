import json
import logging
import sys
from pathlib import Path
from typing import Any

import click
import yaml  # type: ignore

from tools.agentskills.models import AgentIR

# Fields that are Claude-specific and must be stripped for other targets.
_CLAUDE_ONLY_KEYS = {"disallowedTools", "maxTurns", "isolation"}


def _build_frontmatter(ir: AgentIR, tool: str) -> dict[str, Any]:
    """Build a tool-specific frontmatter dict from an AgentIR."""
    fm: dict[str, Any] = {}

    fm["name"] = ir.name
    fm["description"] = ir.description
    if ir.model is not None:
        fm["model"] = ir.model
    if ir.effort is not None:
        fm["effort"] = ir.effort
    if ir.tools is not None:
        fm["tools"] = ir.tools

    if tool == "claude":
        if ir.disallowed_tools is not None:
            fm["disallowedTools"] = ir.disallowed_tools
        if ir.max_turns is not None:
            fm["maxTurns"] = ir.max_turns
        if ir.isolation is not None:
            fm["isolation"] = ir.isolation

    for k, v in ir.extra.items():
        if tool != "claude" and k in _CLAUDE_ONLY_KEYS:
            continue
        fm[k] = v

    return fm


@click.command(help="Transform an AgentIR JSON to tool-specific markdown.")
@click.argument("input_json", type=click.Path(exists=True, path_type=Path))
@click.argument("output_md", type=click.Path(path_type=Path))
@click.option(
    "--tool",
    required=True,
    type=click.Choice(["claude", "gemini", "cursor"]),
    help="Target AI tool",
)
@click.option(
    "--scope",
    required=True,
    type=click.Choice(["user", "repo"]),
    help="Scope of the agent",
)
def main(input_json: Path, output_md: Path, tool: str, scope: str) -> None:
    """Read an AgentIR JSON file, apply tool-specific projection, and write as Markdown."""
    try:
        with open(input_json, encoding="utf-8") as f:
            data = json.load(f)

        try:
            ir = AgentIR.model_validate(data)
        except Exception as e:
            click.echo(f"Failed to validate AgentIR from {input_json}: {e}", err=True)
            sys.exit(1)

        fm = _build_frontmatter(ir, tool)

        yaml_str = yaml.dump(
            fm,
            default_flow_style=False,
            sort_keys=True,
        )

        output_content = f"---\n{yaml_str}---\n\n{ir.body}"

        output_md.parent.mkdir(parents=True, exist_ok=True)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(output_content)

        logging.debug(
            f"Successfully transformed {input_json} to {output_md} for {tool} ({scope} scope)"
        )
    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error transforming {input_json}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
