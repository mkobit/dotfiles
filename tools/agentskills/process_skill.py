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

    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="The unique name of the skill")
    description: str = Field(
        ..., description="A short description of what the skill does"
    )
    version: str | None = Field(None, description="The version of the skill")
    author: str | None = Field(None, description="The author of the skill")
    repository: str | None = Field(
        None, description="A link to the skill's source repository"
    )
    license: str | None = Field(None, description="The license of the skill")
    tags: list[str] | None = Field(default_factory=list, description="Categorical tags")


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
            "metadata": validated_skill.model_dump(mode="json"),
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
