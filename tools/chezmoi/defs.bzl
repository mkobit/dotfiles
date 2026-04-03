"""Deployment tag constants for chezmoi-managed AI tool targets.

These constants are referenced by Bazel macros (tools/agentskills/) and
chezmoi templates (src/chezmoi/) to coordinate installation and removal.
Keeping them here rather than in tools/agentskills/ makes the deployment
semantics explicit: these tags have no build meaning, only deployment meaning.

Usage in macros:
    load("//tools/chezmoi:defs.bzl", "ChezmoidTags")
    tags = ["tool:claude", ChezmoidTags.claude_skill]

# Tag taxonomy

Every deployable target carries two orthogonal tag sets:

  tool tags     — which AI tool owns this artifact
                  tool:claude, tool:claude-agents, tool:gemini, tool:cursor

  install-type tags — what kind of artifact this is and where it deploys
                  claude:commands   → ~/.claude/commands/<install_name>/
                  claude:skill      → ~/.claude/skills/<install_name>/  (single skill)
                  claude:collection → ~/.claude/skills/<install_name>/  (multi-skill namespace tree)
                  claude:agents     → ~/.claude/agents/  (flat .md files)
                  gemini:skill      → ~/.gemini/skills/<install_name>/

  lifecycle tags — deployment state
                  skip-install     → exists in build graph, never deployed
                  tombstone        → was deployed, must now be removed

# Tag design note

No install-type tag is a substring of another.  Bazel attr() uses regex
substring matching, so tags that share a prefix would produce false matches.
The names were chosen to be mutually non-overlapping on purpose.

# Usage in chezmoi templates

Install (per type — no string parsing needed):
  attr(tags, "claude:commands",   //...) except attr(tags, "skip-install", //...) except attr(tags, "tombstone", //...)
  attr(tags, "claude:skill",      //...) except ...
  attr(tags, "claude:collection", //...) except ...
  attr(tags, "claude:agents",     //...) except ...

Remove:
  attr(tags, "claude:commands",   //...) intersect attr(tags, "tombstone", //...)
  attr(tags, "claude:skill",      //...) intersect attr(tags, "tombstone", //...)
  attr(tags, "claude:collection", //...) intersect attr(tags, "tombstone", //...)
  attr(tags, "claude:agents",     //...) intersect attr(tags, "tombstone", //...)
"""

ChezmoidTags = struct(
    # Lifecycle: was deployed, must now be removed on next chezmoi apply.
    # Add to a target via tags = [ChezmoidTags.tombstone] and it will be
    # picked up by the intersect removal query in .chezmoiremove.tmpl.
    tombstone = "tombstone",

    # Lifecycle: exists in the build graph but must never be installed.
    # Use for test fixture targets.
    skip_install = "skip-install",

    # Install-type: Claude slash commands → ~/.claude/commands/<install_name>/
    claude_commands = "claude:commands",

    # Install-type: single transformed skill → ~/.claude/skills/<install_name>/
    claude_skill = "claude:skill",

    # Install-type: multi-skill namespace tree → ~/.claude/skills/<install_name>/
    claude_collection = "claude:collection",

    # Install-type: flat .md sub-agent files → ~/.claude/agents/
    claude_agents = "claude:agents",

    # Install-type: Gemini skill → ~/.gemini/skills/<install_name>/
    gemini_skill = "gemini:skill",
)
