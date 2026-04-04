import json
import logging
import sys
from pathlib import Path
from typing import Any

import click
import yaml  # type: ignore

from tools.agentskills.models import SkillIR


def _build_frontmatter(ir: SkillIR) -> dict[str, Any]:
    """Build a frontmatter dict from a SkillIR."""
    fm: dict[str, Any] = {}

    fm["name"] = ir.name
    fm["description"] = ir.description

    if ir.allowed_tools is not None:
        fm["allowed-tools"] = ir.allowed_tools
    if ir.argument_hint is not None:
        fm["argument-hint"] = ir.argument_hint
    if ir.model is not None:
        fm["model"] = ir.model
    if ir.effort is not None:
        fm["effort"] = ir.effort
    if ir.context is not None:
        fm["context"] = ir.context
    if ir.agent is not None:
        fm["agent"] = ir.agent
    if ir.user_invocable is not None:
        fm["user-invocable"] = ir.user_invocable
    if ir.disable_model_invocation is not None:
        fm["disable-model-invocation"] = ir.disable_model_invocation
    if ir.paths is not None:
        fm["paths"] = ir.paths
    if ir.shell is not None:
        fm["shell"] = ir.shell

    # Merge extra fields
    fm.update(ir.extra)

    return fm


@click.command(help="Transform a SkillIR JSON to tool-specific markdown.")
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
    help="Scope of the skill",
)
def main(input_json: Path, output_md: Path, tool: str, scope: str) -> None:
    """Read a SkillIR JSON file, apply transformations, and write as Markdown."""
    try:
        with open(input_json, encoding="utf-8") as f:
            data = json.load(f)

        try:
            ir = SkillIR.model_validate(data)
        except Exception as e:
            click.echo(f"Failed to validate SkillIR from {input_json}: {e}", err=True)
            sys.exit(1)

        fm = _build_frontmatter(ir)

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
