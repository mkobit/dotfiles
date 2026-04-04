import json
import logging
import sys
from pathlib import Path
from typing import Any

import click
import frontmatter
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tools.agentskills.models import AgentIR


class _AgentFrontmatter(BaseModel):
    """Permissive parser for agent .md frontmatter. Unknown fields go to extra."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    model: str | None = None
    effort: str | None = None
    tools: list[str] | None = Field(None, alias="tools")
    allowed_tools: list[str] | None = Field(None, alias="allowed-tools")
    disallowed_tools: list[str] | None = Field(None, alias="disallowedTools")
    max_turns: int | None = Field(None, alias="maxTurns")
    isolation: str | None = None


_KNOWN_AGENT_KEYS = {
    "name",
    "description",
    "model",
    "effort",
    "tools",
    "allowed-tools",
    "disallowedTools",
    "maxTurns",
    "isolation",
}


@click.command(help="Process an agent .md file to AgentIR JSON.")
@click.argument(
    "agent_md_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument("output_json", type=click.Path(path_type=Path))
@click.option(
    "--source-format",
    default="claude-agents",
    type=click.Choice(["claude-plugin", "claude-agents"]),
    help="Source format of the agent",
)
def main(agent_md_file: Path, output_json: Path, source_format: str) -> None:
    """Read an agent .md file, parse frontmatter, emit AgentIR JSON."""
    try:
        post = frontmatter.load(agent_md_file)
        metadata: dict[str, Any] = post.metadata
        body: str = post.content

        try:
            parsed = _AgentFrontmatter.model_validate(metadata)
        except ValidationError as e:
            click.echo(
                f"Validation Error: {agent_md_file} contains invalid frontmatter.\n{e}",
                err=True,
            )
            sys.exit(1)

        # Collect extra: any key not in the known set
        extra: dict[str, Any] = {
            k: v for k, v in metadata.items() if k not in _KNOWN_AGENT_KEYS
        }

        # Resolve tools: prefer "tools", fall back to "allowed-tools"
        tools = parsed.tools or parsed.allowed_tools

        # Derive name from filename stem if not present in frontmatter
        name = parsed.name or agent_md_file.stem

        ir = AgentIR(
            source_format=source_format,
            name=name,
            description=parsed.description or "",
            body=body,
            model=parsed.model,
            effort=parsed.effort,
            tools=tools,
            **{"disallowedTools": parsed.disallowed_tools},
            **{"maxTurns": parsed.max_turns},
            isolation=parsed.isolation,
            extra=extra,
        )

        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(ir.model_dump(mode="json", by_alias=True), f, indent=2)

        logging.debug(f"Successfully processed {agent_md_file} to {output_json}")
    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error processing {agent_md_file}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
