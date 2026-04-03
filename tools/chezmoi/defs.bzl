"""Public deployment tag constants for chezmoi-managed AI tool targets.

These constants are referenced by Bazel macros (tools/agentskills/) and
chezmoi templates (src/chezmoi/) to coordinate installation and removal.
Keeping them here rather than in tools/agentskills/ makes the deployment
semantics explicit: these tags have no build meaning, only deployment meaning.

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

# --- Lifecycle tags ---

# Applied to targets that should be deleted from their deployment destination
# on the next chezmoi apply. Combine with an install-type tag in the intersect query.
CHEZMOI_TOMBSTONE = "tombstone"

# Applied to test fixture targets that exist in the build graph but must never
# be installed by chezmoi.
CHEZMOI_SKIP_INSTALL = "skip-install"

# --- Install-type tags: Claude ---

# ~/.claude/commands/<install_name>/
CHEZMOI_CLAUDE_COMMANDS = "claude:commands"

# ~/.claude/skills/<install_name>/  (single transformed skill)
CHEZMOI_CLAUDE_SKILL = "claude:skill"

# ~/.claude/skills/<install_name>/  (multi-skill namespace tree from a collection)
CHEZMOI_CLAUDE_SKILL_GROUP = "claude:collection"

# ~/.claude/agents/  (flat .md sub-agent files)
CHEZMOI_CLAUDE_AGENTS = "claude:agents"

# --- Install-type tags: Gemini ---

# ~/.gemini/skills/<install_name>/
CHEZMOI_GEMINI_SKILL = "gemini:skill"
