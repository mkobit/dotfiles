import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import click
import frontmatter
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from tools.agentskills.models import AssociatedFile, PluginSkill, SkillIR


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


def _scan_associated_files(skill_dir: Path) -> list[AssociatedFile]:
    """Walk skill_dir and return all non-SKILL.md files as AssociatedFile entries."""
    result: list[AssociatedFile] = []
    for p in sorted(skill_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name == "SKILL.md":
            continue
        rel = p.relative_to(skill_dir)
        result.append(
            AssociatedFile(
                path=str(rel),
                executable=os.access(p, os.X_OK),
            )
        )
    return result


def _project_agentskills(
    metadata: dict[str, Any], body: str, assoc: list[AssociatedFile]
) -> SkillIR:
    """Validate via AgentSkill (extra='forbid'), then project to SkillIR."""
    validated = AgentSkill.model_validate(metadata)
    return SkillIR(
        source_format="agentskills.io",
        name=validated.name,
        description=validated.description,
        body=body,
        associated_files=assoc,
    )


def _project_plugin(
    metadata: dict[str, Any], body: str, assoc: list[AssociatedFile]
) -> SkillIR:
    """Parse via PluginSkill (extra='ignore'), project known fields to SkillIR, rest to extra."""
    known_keys = {
        "name",
        "description",
        "argument-hint",
        "allowed-tools",
        "model",
        "effort",
        "context",
        "agent",
        "disable-model-invocation",
        "user-invocable",
        "paths",
        "shell",
    }
    # PluginSkill uses populate_by_name=True with alias support; pass metadata directly
    validated = PluginSkill.model_validate(metadata)

    if not validated.name:
        click.echo("Error: claude-plugin skill is missing a 'name'", err=True)
        sys.exit(1)
    if not validated.description:
        click.echo("Error: claude-plugin skill is missing a 'description'", err=True)
        sys.exit(1)

    # Collect extra fields: anything not recognised by PluginSkill
    extra: dict[str, Any] = {k: v for k, v in metadata.items() if k not in known_keys}

    return SkillIR(
        source_format="claude-plugin",
        name=validated.name,
        description=validated.description,
        body=body,
        **{
            "allowed-tools": validated.allowed_tools,
            "argument-hint": validated.argument_hint,
        },
        model=validated.model,
        effort=validated.effort,
        context=validated.context,
        agent=validated.agent,
        **{
            "user-invocable": validated.user_invocable,
            "disable-model-invocation": validated.disable_model_invocation,
        },
        paths=validated.paths,
        shell=validated.shell,
        extra=extra,
        associated_files=assoc,
    )


@click.command(
    help="Extracts and validates YAML frontmatter from a skill directory to IR JSON."
)
@click.argument(
    "skill_dir", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.argument("output_json", type=click.Path(path_type=Path))
@click.option(
    "--source-format",
    default="agentskills.io",
    type=click.Choice(["agentskills.io", "claude-plugin", "skill-collection"]),
    help="Source format of the skill",
)
def main(skill_dir: Path, output_json: Path, source_format: str) -> None:
    """Read SKILL.md from skill_dir, parse frontmatter, emit SkillIR JSON."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        click.echo(f"Error: No SKILL.md found in {skill_dir}", err=True)
        sys.exit(1)

    try:
        post = frontmatter.load(skill_md)
        metadata: dict[str, Any] = post.metadata
        body: str = post.content

        assoc = _scan_associated_files(skill_dir)

        try:
            if source_format == "agentskills.io":
                ir = _project_agentskills(metadata, body, assoc)
            elif source_format in ("claude-plugin", "skill-collection"):
                ir = _project_plugin(metadata, body, assoc)
            else:
                click.echo(f"Error: Unknown source format: {source_format}", err=True)
                sys.exit(1)
        except ValidationError as e:
            click.echo(
                f"Validation Error: {skill_md} contains invalid frontmatter.\n{e}",
                err=True,
            )
            sys.exit(1)

        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(ir.model_dump(mode="json", by_alias=True), f, indent=2)

        logging.debug(f"Successfully processed {skill_md} to {output_json}")
    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error processing {skill_md}: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
