import json
import sys
from pathlib import Path
from typing import Any

import click
import frontmatter
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AgentSkill(BaseModel):
    """
    Pydantic model representing the expected frontmatter properties
    for an agentskills.io skill file.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
        description="The unique name of the skill. Lowercase letters, numbers, and hyphens only.",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="A short description of what the skill does and when to use it.",
    )
    license: str | None = Field(
        None, description="License name or reference to a bundled license file."
    )
    compatibility: str | None = Field(
        None,
        max_length=500,
        description="Indicates environment requirements.",
    )
    metadata: dict[str, Any] | None = Field(
        default_factory=dict,
        description="Arbitrary key-value mapping for additional metadata.",
    )
    allowed_tools: str | None = Field(
        None,
        alias="allowed-tools",
        description="Space-delimited list of pre-approved tools the skill may use.",
    )


@click.command(
    help="Extracts and validates YAML frontmatter from a Markdown file to JSON."
)
@click.argument("input_md", type=click.Path(exists=True, path_type=Path))
@click.argument("output_json", type=click.Path(path_type=Path))
def main(input_md: Path, output_json: Path) -> None:
    """Extracts frontmatter and body from a markdown file, validates it, and saves to JSON."""
    try:
        post = frontmatter.load(input_md)
        metadata = post.metadata
        body = post.content

        # Validate the extracted frontmatter against the AgentSkill schema
        try:
            validated_skill = AgentSkill.model_validate(metadata)
        except ValidationError as e:
            click.echo(
                f"Validation Error: {input_md} contains invalid frontmatter.\n{e}",
                err=True,
            )
            sys.exit(1)

        # Output the validated frontmatter along with the markdown body
        output_data: dict[str, Any] = {
            "metadata": validated_skill.model_dump(mode="json", by_alias=True),
            "body": body,
        }

        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)

        click.echo(f"Successfully processed {input_md} to {output_json}")

    except Exception as e:
        click.echo(f"Error processing {input_md}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
