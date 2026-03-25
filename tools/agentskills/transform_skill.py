import json
import sys
from pathlib import Path
from typing import Any

import click
import yaml  # type: ignore

from tools.agentskills.process_skill import AgentSkill


def transform_frontmatter(skill: AgentSkill, tool: str, scope: str) -> dict[str, Any]:
    """Apply tool-specific and scope-specific transformations to the frontmatter."""

    # Dump using the Pydantic model for validation/consistency
    transformed: dict[str, Any] = skill.model_dump(
        mode="json", by_alias=True, exclude_none=True
    )

    # Generic scope addition
    if "metadata" not in transformed or not isinstance(transformed["metadata"], dict):
        transformed["metadata"] = {}

    transformed["metadata"]["scope"] = scope
    transformed["metadata"]["target_tool"] = tool

    # Tool-specific logic (placeholder for future adaptations like extensions/slash commands)
    if tool == "claude":
        # Example: Claude might require a different capability name
        pass
    elif tool == "gemini":
        # Example: Gemini might require different formatting
        pass

    return transformed


@click.command(help="Transform agentskills.io .md.json to tool-specific markdown.")
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
    """Read a processed .md.json file, apply transformations, and write as Markdown."""
    try:
        with open(input_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse using the same Pydantic model used during generation
        metadata_dict = data.get("metadata", {})
        try:
            skill = AgentSkill.model_validate(metadata_dict)
        except Exception as e:
            click.echo(f"Failed to validate metadata against AgentSkill: {e}", err=True)
            sys.exit(1)

        body = data.get("body", "")

        # Transform the metadata
        transformed_metadata = transform_frontmatter(skill, tool, scope)

        # Generate the output markdown
        # PyYAML dumps with some defaults we want to override for frontmatter
        yaml_str = yaml.dump(
            transformed_metadata, default_flow_style=False, sort_keys=True
        )

        output_content = f"---\n{yaml_str}---\n\n{body}"

        output_md.parent.mkdir(parents=True, exist_ok=True)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write(output_content)

        click.echo(
            f"Successfully transformed {input_json} to {output_md} for {tool} ({scope} scope)"
        )

    except Exception as e:
        click.echo(f"Error transforming {input_json}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
