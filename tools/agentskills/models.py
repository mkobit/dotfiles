"""
Canonical Pydantic models for the AI skills/plugin ecosystem.

The agentskills.io SKILL.md schema (our internal format) lives in
process_skill.py as AgentSkill and uses extra="forbid" for strict validation.
The PluginSkill model here uses extra="ignore" to accept all upstream fields
without failing on unknown extensions from external plugin authors.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Plugin SKILL.md frontmatter (Claude plugin superset of agentskills.io)
# ---------------------------------------------------------------------------


class PluginSkill(BaseModel):
    """
    SKILL.md frontmatter for a Claude plugin skill.

    Superset of the agentskills.io AgentSkill schema. Uses extra="ignore"
    rather than extra="forbid" because external plugin authors may add
    fields we don't know about. The canonical strict schema for our own
    skills remains AgentSkill in process_skill.py.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    description: str | None = None
    argument_hint: str | None = Field(None, alias="argument-hint")
    allowed_tools: str | list[str] | None = Field(None, alias="allowed-tools")
    model: str | None = None
    effort: Literal["low", "medium", "high", "max"] | None = None
    context: Literal["fork"] | None = None
    agent: str | None = Field(None, description="Subagent type when context=fork.")
    disable_model_invocation: bool | None = Field(
        None, alias="disable-model-invocation"
    )
    user_invocable: bool | None = Field(None, alias="user-invocable")
    paths: str | None = Field(
        None, description="Glob patterns limiting skill activation scope."
    )
    shell: Literal["bash", "powershell"] | None = None


# ---------------------------------------------------------------------------
# Intermediate representation (IR) types
# All source formats normalize into these canonical atoms.
# ---------------------------------------------------------------------------


class AssociatedFile(BaseModel):
    """A non-primary file in a skill/agent directory (reference docs, scripts, templates, etc.)."""

    model_config = ConfigDict(extra="ignore")

    path: str  # relative to the skill/agent directory root
    executable: bool = False


class SkillIR(BaseModel):
    """Canonical IR for a skill atom. All source formats normalize into this."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    schema_version: str = "1"
    atom_type: Literal["skill"] = "skill"
    source_format: str = Field(
        ...,
        description="agentskills.io | claude-plugin | gemini-extension | skill-collection | claude-agents",
    )
    name: str
    description: str
    body: str
    allowed_tools: str | list[str] | None = Field(None, alias="allowed-tools")
    argument_hint: str | None = Field(None, alias="argument-hint")
    model: str | None = None
    effort: Literal["low", "medium", "high", "max"] | None = None
    context: Literal["fork"] | None = None
    agent: str | None = None
    user_invocable: bool | None = Field(None, alias="user-invocable")
    disable_model_invocation: bool | None = Field(
        None, alias="disable-model-invocation"
    )
    paths: str | None = None
    shell: Literal["bash", "powershell"] | None = None
    extra: dict[str, Any] = {}
    associated_files: list[AssociatedFile] = []


class AgentIR(BaseModel):
    """Canonical IR for an agent atom."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    schema_version: str = "1"
    atom_type: Literal["agent"] = "agent"
    source_format: str
    name: str
    description: str
    body: str
    model: str | None = None
    effort: Literal["low", "medium", "high", "max"] | None = None
    tools: list[str] | None = None
    disallowed_tools: list[str] | None = Field(None, alias="disallowed-tools")
    max_turns: int | None = Field(None, alias="max-turns")
    isolation: Literal["worktree"] | None = None
    extra: dict[str, Any] = {}
    associated_files: list[AssociatedFile] = []
