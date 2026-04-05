# Agent context: agentskills Bazel rules

## Purpose

Bazel rules for ingesting, transforming, and deploying AI skills from external upstreams to tool-specific formats (Claude, Gemini, Cursor) via chezmoi.
Think of it as a transpiler: upstream source → validated IR → tool-specific archive → chezmoi installs.

## Supported upstream formats

- **agentskills.io (SKILL.md)** — canonical format; full validation + transformation pipeline via `process_skill.py` / `transform_skill.py`
- **Gemini extensions** — `gemini-extension.json` + TOML commands → Claude slash commands + skill via `claude_from_gemini_extension()`
- **Skill collections** (`skill_collection_repo`) — raw directories with `SKILL.md`; packaged as-is, NO validation pipeline; only use when files are already Claude-compatible
- **Sub-agent collections** (`claude_agents_repo`) — flat `.md` agent files by division → `~/.claude/agents/`

## Evaluating a new upstream source

Before adding via `skill_collection`, verify:
- SKILL.md files are the authoritative source (not auto-generated from templates)
- No preamble that calls upstream-specific binaries, writes to state dirs, or does network I/O at invocation time
- Skills are general purpose, not the upstream's own infrastructure
- No installer/uninstaller scripts that modify managed paths (`~/.claude/`, etc.)
- Deployment model is compatible with pinned, chezmoi-managed installation (not self-upgrading git clones)

Sources that fail multiple criteria should be ingested selectively as local `src/ai/skills/` entries rewritten to agentskills.io format, not passed through as a collection.

## Deployment tags (see tools/chezmoi/defs.bzl for full reference)

`claude:skill`, `claude:collection`, `claude:commands`, `claude:agents`, `gemini:skill`, `skip-install`, `tombstone`

## Upstream source history

### compound-engineering (EveryInc/compound-engineering-plugin) — added 2026-04-04

Claude plugin format (`claude_plugin_repo`).
50+ general-purpose skills (ce-plan, ce-review, ce-work, git-*, agent-native-architecture, etc.) deployed to `~/.claude/skills/compound-engineering/`.
Skills are already Claude-native with clean frontmatter — no transformation needed.
Agents (review personas, design, research, workflow) are not currently deployed; the nested `agents/<category>/` structure doesn't map cleanly to our flat `claude_subagent_group` rule.

### gstack — tombstoned 2026-04-04

`github.com/garrytan/gstack` — tombstoned after evaluation.
Problems: every skill has an identical ~40-line preamble with telemetry, update checks (outbound network), session tracking, and gstack binary calls (all `|| true`, but still context noise).
SKILL.md files are auto-generated from `.tmpl` sources.
Several skills are gstack infrastructure (freeze, unfreeze, learn, guard, canary), not general purpose.
`bin/` includes an uninstall script that removes `~/.claude/skills/gstack` and a telemetry sync daemon — both incompatible with chezmoi-managed deployment.

**Potential future**: cherry-pick `review`, `health`, `qa`, `investigate`, `design-review`, `ship` as local skills rewritten to agentskills.io format without the preamble.
