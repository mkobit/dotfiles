"""
Canonical Pydantic models for the AI skills/plugin ecosystem.

These types cover three external formats:

  1. Claude plugin manifest  (.claude-plugin/plugin.json)
  2. Claude plugin marketplace  (.claude-plugin/marketplace.json)
  3. Claude plugin SKILL.md frontmatter  (superset of agentskills.io)

The agentskills.io SKILL.md schema (our internal format) lives in
process_skill.py as AgentSkill and uses extra="forbid" for strict validation.
The PluginSkill model here uses extra="ignore" to accept all upstream fields
without failing on unknown extensions from external plugin authors.

All models use extra="ignore" unless noted, since we are consumers
of externally-authored files we do not fully control.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------


class AuthorInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    email: str | None = None
    url: str | None = None


# ---------------------------------------------------------------------------
# Plugin source types (discriminated union on "source" key)
# Used in marketplace.json plugin entries.
# ---------------------------------------------------------------------------


class GitHubSource(BaseModel):
    """Plugin sourced from a GitHub repository."""

    model_config = ConfigDict(extra="ignore")

    source: Literal["github"]
    repo: str = Field(..., description="'owner/repo' on GitHub.")
    ref: str | None = Field(None, description="Branch, tag, or commit-ish.")
    sha: str | None = Field(
        None, description="40-character git commit SHA for pinning."
    )


class GitUrlSource(BaseModel):
    """Plugin sourced from an arbitrary Git remote."""

    model_config = ConfigDict(extra="ignore")

    source: Literal["url"]
    url: str
    ref: str | None = None
    sha: str | None = None


class GitSubdirSource(BaseModel):
    """Plugin sourced from a subdirectory of a Git repo (sparse clone)."""

    model_config = ConfigDict(extra="ignore")

    source: Literal["git-subdir"]
    url: str
    path: str = Field(..., description="Subdirectory path within the repo.")
    ref: str | None = None
    sha: str | None = None


class NpmSource(BaseModel):
    """Plugin sourced from an npm package."""

    model_config = ConfigDict(extra="ignore")

    source: Literal["npm"]
    package: str
    version: str | None = None
    registry: str | None = Field(
        None, description="Custom registry URL for private packages."
    )


PluginSourceObject = Annotated[
    GitHubSource | GitUrlSource | GitSubdirSource | NpmSource,
    Field(discriminator="source"),
]

# A plugin source is either a relative path string or one of the typed objects.
PluginSource = str | PluginSourceObject


# ---------------------------------------------------------------------------
# Plugin manifest  (.claude-plugin/plugin.json or .cursor-plugin/plugin.json)
# ---------------------------------------------------------------------------


class PluginManifest(BaseModel):
    """
    Parsed representation of plugin.json.

    The name field is the canonical plugin identifier used for namespacing
    skills, commands, and agents (e.g. /plugin-name:skill-name).
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str
    version: str | None = None
    description: str | None = None
    author: AuthorInfo | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = []

    # Component path overrides (each can be a string path or list of paths).
    # When absent, Claude Code uses convention-based directory discovery.
    commands: str | list[str] | None = None
    agents: str | list[str] | None = None
    skills: str | list[str] | None = None
    hooks: str | list[str] | dict[str, Any] | None = None
    mcp_servers: str | list[Any] | dict[str, Any] | None = Field(
        None, alias="mcpServers"
    )
    lsp_servers: str | list[Any] | dict[str, Any] | None = Field(
        None, alias="lspServers"
    )
    user_config: dict[str, Any] | None = Field(None, alias="userConfig")
    channels: list[Any] | None = None


# ---------------------------------------------------------------------------
# Marketplace file  (.claude-plugin/marketplace.json)
# ---------------------------------------------------------------------------


class MarketplaceMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    description: str | None = None
    version: str | None = None
    plugin_root: str | None = Field(
        None,
        alias="pluginRoot",
        description="Base directory prepended to relative plugin source paths.",
    )


class MarketplaceEntry(BaseModel):
    """A single plugin listed in a marketplace.json."""

    model_config = ConfigDict(extra="ignore")

    name: str
    source: PluginSource
    description: str | None = None
    version: str | None = None
    author: AuthorInfo | None = None
    homepage: str | None = None
    repository: str | None = None
    license: str | None = None
    keywords: list[str] = []
    category: str | None = None
    tags: list[str] = []
    strict: bool = Field(
        True,
        description=(
            "When True, plugin.json is the authority for component definitions. "
            "When False, the marketplace entry defines everything."
        ),
    )
    # Component overrides (same semantics as PluginManifest)
    commands: str | list[str] | None = None
    agents: str | list[str] | None = None
    hooks: str | list[str] | dict[str, Any] | None = None
    mcp_servers: str | list[Any] | dict[str, Any] | None = Field(
        None, alias="mcpServers"
    )
    lsp_servers: str | list[Any] | dict[str, Any] | None = Field(
        None, alias="lspServers"
    )


class MarketplaceFile(BaseModel):
    """
    Parsed representation of marketplace.json.

    A marketplace is a flat catalog — it lists plugins but cannot reference
    other marketplaces (not recursive).
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    owner: AuthorInfo
    plugins: list[MarketplaceEntry]
    metadata: MarketplaceMetadata | None = None


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
    hooks: dict[str, Any] | None = None
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
    disallowed_tools: list[str] | None = Field(None, alias="disallowedTools")
    max_turns: int | None = Field(None, alias="maxTurns")
    isolation: Literal["worktree"] | None = None
    extra: dict[str, Any] = {}
    associated_files: list[AssociatedFile] = []


class CommandIR(BaseModel):
    """Canonical IR for a slash command atom."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    schema_version: str = "1"
    atom_type: Literal["command"] = "command"
    source_format: str
    name: str
    description: str | None = None
    body: str
    argument_hint: str | None = Field(None, alias="argument-hint")
    allowed_tools: str | list[str] | None = Field(None, alias="allowed-tools")
    extra: dict[str, Any] = {}
    associated_files: list[AssociatedFile] = []
