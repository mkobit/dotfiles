# Plan: Unified AI rule authoring and cross-tool deployment

Status: Draft
Branch: `ai-rule-builder`
Created: 2026-03-10
Target tools: Claude Code, Gemini CLI, Cursor

## Problem

AI tool configuration is fragmented across three concerns:
1. Always-on rules (preferences, coding standards) - duplicated per tool.
2. On-demand skills (SKILL.md) - portable via Agent Skills spec but only deployed to Claude today.
3. Slash commands - tool-specific formats (Claude = skill frontmatter, Gemini = TOML, Cursor = @mentions).

No way to author once and deploy everywhere.
No way to quickly scaffold skills into arbitrary repos/directories.

## Cross-tool format matrix

| Concern | Claude Code | Gemini CLI | Cursor |
|---------|------------|------------|--------|
| Always-on rules | `CLAUDE.md` | `GEMINI.md` | `.cursor/rules/*.mdc` |
| Skills (on-demand) | `.claude/skills/*/SKILL.md` | `.gemini/skills/*/SKILL.md` | `.cursor/skills/*/SKILL.md` |
| Portable skills | `.agents/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` |
| Slash commands | Skill with `disable-model-invocation: true` | `.gemini/commands/*.toml` (TOML format, separate system) | `@rule-name` / manual apply rules |
| Global skills dir | `~/.claude/skills/` | `~/.gemini/skills/` | `~/.cursor/skills/` |
| Global commands dir | N/A (merged into skills) | `~/.gemini/commands/` | N/A |

Key facts:
- Skills (SKILL.md) are portable across all three tools via `.agents/skills/`.
- Slash commands are NOT portable. Gemini uses TOML, Claude uses skill frontmatter, Cursor uses rule metadata.
- Always-on rules have different formats per tool. Rulesync handles this transformation.

## Architecture: Two layers + scaffolding

### Layer 1: Always-on rules (rulesync)

Author shared rules as markdown in `.rulesync/rules/`.
Rulesync generates tool-specific outputs: CLAUDE.md, GEMINI.md, `.cursor/rules/*.mdc`, etc.
Chezmoi deploys global outputs to destDir.
Repo-local outputs committed directly.

### Layer 2: Portable skills (Agent Skills spec)

Skills as SKILL.md directories.
Portable across all three tools via `.agents/skills/` or tool-specific paths.
Chezmoi deploys global skills to each tool's global skills dir.
For repo-specific skills: scaffold into `.agents/skills/` in any repo.

### Slash commands (tool-specific, not unified)

Claude: skills with `disable-model-invocation: true`.
Gemini: TOML files in `.gemini/commands/`.
Cursor: rules with manual-only application.
These remain authored per-tool where needed.
Rulesync may generate some of these (it supports commands for Claude and simulated commands for others).

### Scaffolding

Use skill-creator (from anthropics/skills marketplace) or a thin wrapper to create skills in any directory.
Target `.agents/skills/` for cross-tool portability.
Target tool-specific dirs when needed (e.g., Gemini TOML commands).

## Current state

| Component | Status |
|-----------|--------|
| Rulesync binary | v7.6.3 in multitool + chezmoi external |
| Rulesync config | `rulesync.jsonc` targeting claudecode, geminicli, cursor |
| Shared always-on rules | `.rulesync/rules/` (3 rules), generated to all 3 tools. Chezmoi templates migrated to static files; `agents.toml` deleted. |
| Portable skills (canonical) | 4 in `src/agents/skills/`, replicated to all 3 tool dirs via `bazel run //tools/agents:sync` |
| Claude skills (internal) | 5 in `src/chezmoi/dot_claude/skills/` (4 portable + 1 Claude-only) |
| Claude commands (internal) | `claude/new/{skill,command,agent,hook}.md`, `obsidian/{base,organize,transform}.md` |
| Gemini commands | None |
| Cursor rules | 2 `.mdc` files in `.cursor/rules/` (repo-local only) |
| Anthropic skill marketplace | Not configured |
| Gemini extensions | conductor v0.3.1 via install script |

## Skill audit and migration plan

| Current skill | Portable? | Action |
|--------------|-----------|--------|
| `technical-writing` | Yes | Keep as SKILL.md. Extract always-on portion to rulesync rules. Deploy globally via chezmoi to all three tools' skill dirs. |
| `write-agent-context` | Yes | Same as above. |
| `typescript-expert` | Yes | Keep as SKILL.md. Deploy globally. |
| `pr-reviewer` | Yes | Keep as SKILL.md. Deploy globally. |
| `claude-extension-builder` | Partially | **Replaced** by upstream `skill-creator` (fetched via Bazel `http_archive`, deployed to all tools). Deleted. |

| Current command | Portable? | Action |
|----------------|-----------|--------|
| `claude/new/skill.md` | No (Claude-specific) | **Replaced** by upstream `skill-creator`. Deleted. |
| `claude/new/command.md` | No | Keep for Claude. Consider Gemini TOML equivalent. |
| `claude/new/agent.md` | No | Claude-specific concept. Keep. |
| `claude/new/hook.md` | No | Claude-specific. Keep. |
| `obsidian/*` | Partially | These are task-oriented commands. Could become portable skills in `.agents/skills/`. |

## Phases

### Phase 1: Bootstrap rulesync

- [x] Create `rulesync.jsonc` targeting: claude, gemini-cli, cursor
- [x] Create `.rulesync/rules/` with shared rules:
  - `00-preferences.md` (from `agents.toml`)
  - `10-technical-writing.md` (always-on portion)
  - `11-write-agent-context.md` (always-on portion)
- [x] Run `rulesync generate`, verify outputs for all three tools
- [x] Bazel integration: `//tools/rulesync:generate` genrule, `//tools/rulesync:check` drift check
- [x] Decide output integration: preferences migrated from `agents.toml` to rulesync as single source of truth; chezmoi templates to be updated in Phase 2
- [x] Commit generated outputs

### Phase 2: Portable skill deployment via chezmoi

- [x] Migrate chezmoi templates from `agents.toml` to static files matching rulesync output
  - Replaced `dot_claude/CLAUDE.md.tmpl` → `dot_claude/CLAUDE.md` (static)
  - Replaced `dot_gemini/GEMINI.md.tmpl` → `dot_gemini/GEMINI.md` (static)
  - Deleted `src/chezmoi/.chezmoidata/agents.toml`
- [x] Deploy portable skills to all three global dirs:
  - `dot_claude/skills/` (existing, unchanged)
  - `dot_gemini/skills/` (new: 4 portable skills)
  - `dot_cursor/skills/` (new: 4 portable skills)
  - `claude-extension-builder` kept Claude-only (references Claude-specific commands)
- [x] Verified `.chezmoiignore` allows new paths (no SKILL.md patterns blocked)
- [x] Filesystem-driven skill sync pipeline (no Bazel config to edit):
  - Canonical source: `src/agents/skills/` (single copy of each portable skill)
  - Sync: `bazel run //tools/agents:sync` — discovers skills and tools from filesystem, copies to chezmoi dirs
  - Drift check: `bazel run //tools/agents:check` — verifies committed copies match canonical source
  - Adding a new skill: create `src/agents/skills/<name>/SKILL.md`, run `sync`
  - Adding a new tool: create `src/chezmoi/dot_<tool>/skills/` directory, run `sync`
- [ ] Verify skill discovery works in all three tools

### Phase 3: Upstream skill-creator integration

- [x] Fetch `skill-creator` from anthropics/skills via Bazel `http_archive` (pinned to commit `b0cbd3d`)
- [x] Update sync pipeline to copy full skill directories (not just SKILL.md) and discover upstream skills from Bazel runfiles
- [x] Deploy `skill-creator` to all three tool dirs via `bazel run //tools/agents:sync`
- [x] Delete superseded internal `claude-extension-builder` skill and `claude/new/skill.md` command
- [x] Keep `claude/new/{hook,agent,command}.md` (not covered by upstream skill-creator)
- [x] Add directory-level `sh_test` drift tests for upstream skills (`//src/agents/skills:upstream_drift_tests`, 3 targets)
- [x] Exclude upstream-vendored Python scripts from ruff formatting (`pyproject.toml`)
- [x] All 28 validation tests pass (`//:validation_tests`)

### Phase 4: Gemini CLI command generation

- [ ] Evaluate rulesync's Gemini command support (simulated commands)
- [ ] If insufficient: create bazel genrule to transform skill-like definitions into Gemini TOML commands
- [ ] Deploy global Gemini commands via chezmoi (`dot_gemini/commands/`)
- [ ] Consider which Claude slash-commands warrant Gemini TOML equivalents

### Phase 5: Bazel integration

- [x] `rulesync_generate` genrule: `//tools/rulesync:generate` (existed from Phase 1)
- [x] Rulesync drift tests: 9 `diff_test` targets comparing genrule outputs vs committed files (`//tools/rulesync:drift_tests`)
- [x] Skills drift tests: 12 `diff_test` targets auto-generated via `skills_drift_tests` macro (`//src/agents/skills:drift_tests`)
- [x] All suites added to `//:validation_tests` (40 total tests)
- [x] `skill_validate` test: SKILL.md validation framework
  - Fixed non-compliant skill names to match directory names (kebab-case)
  - Pydantic models: `ValidationContext`, `ValidationResult`, `SkillValidationReport`
  - YAML frontmatter parser (`frontmatter.py`)
  - Spec validators aligned with agentskills.io (9 rules)
  - Lint validators for project conventions (1 rule)
  - Structure validators for folder layout (2 rules)
  - Composable Bazel macros: `skill_frontmatter_test`, `skill_lint_test`, `skill_structure_test`, `skill_validation_tests`
  - 12 per-skill test targets (4 skills x 3 types) in `//src/agents/skills:skill_validation`
  - Interactive CLI: `bazel run //tools/agents:validate`
  - Unit tests: `//tools/agents/skills_cli:test_validate`

### Phase 6: Cursor rule migration

- [ ] Evaluate existing `.cursor/rules/*.mdc` files
- [ ] Migrate portable content to rulesync rules (generates `.cursor/rules/` output)
- [ ] Keep cursor-specific rules (like `agents-md.mdc`) as-is
- [ ] Deploy cursor rules to destDir if cursor is used globally (currently repo-local only)

## Open questions

1. **Skill deduplication**: If a skill is both a portable SKILL.md AND has content extracted to rulesync always-on rules, how to avoid redundancy?
   - Recommendation: The always-on rule contains the minimal "always apply this" subset. The full skill contains detailed instructions for when it's activated. They serve different purposes.

2. **Gemini commands vs skills**: Gemini has both. Some things are better as commands (quick shortcuts with `{{args}}`), others as skills (complex on-demand expertise). How to decide?
   - Recommendation: If it's a simple prompt template with args, Gemini TOML command. If it needs multi-step instructions, SKILL.md. Rulesync may generate both.

3. **`.agents/skills/` vs tool-specific dirs**: Deploy to the portable path or replicate to each tool's dir?
   - Recommendation: For project-level, use `.agents/skills/` (all tools discover it). For global (chezmoi-deployed), replicate to each tool's dir since there's no global `.agents/` convention.

4. **Chezmoi template vars in skills**: Skills are static SKILL.md. Some may want `destDir` or other vars.
   - Recommendation: Use `.tmpl` suffix in chezmoi source. Chezmoi renders the template, outputs a static SKILL.md.

## Settings, permissions, and repo bootstrapping

### Settings hierarchy per tool

| Aspect | Claude Code | Gemini CLI | Cursor |
|--------|------------|------------|--------|
| Global settings | `~/.claude/settings.json` | `~/.gemini/settings.json` | User Settings UI |
| Project settings (committed) | `.claude/settings.json` | `.gemini/settings.json` | `.cursor/rules/*.mdc` |
| Local overrides (gitignored) | `.claude/settings.local.json` | CLI args / env vars | User-level settings |
| Permissions model | allow/ask/deny rules | `tools.allowed`/`tools.exclude` | N/A |
| Hooks | `hooks` in settings.json | N/A (extensions) | N/A |
| Sandbox | `sandbox` in settings.json | `tools.sandbox` (docker/podman) | N/A |
| MCP servers | `.mcp.json` (project), `~/.claude.json` (user) | MCP in settings.json | N/A |

### Current settings in this repo

**Project-level (`.claude/settings.json`, committed):**
- Bazel permissions (build/test/query/run allowed)
- WebFetch domains (github.com, docs.anthropic.com, jules.google)
- PostToolUse hooks: format on write/edit, bazel validate

**Global (deployed via chezmoi from `claude_code.toml`):**
- `cleanupPeriodDays`, `outputStyle`, `statusLine` command
- Permission defaults: tools=allow, files=allow
- Env: telemetry/autoupdater disabled

**Local (`.claude/settings.local.json`, gitignored):**
- Personal overrides, not managed by this system

### What "bootstrapping a new repo" means

When starting a new project or adding AI tool support to an existing repo, you need:

| File | Purpose | Portable? |
|------|---------|-----------|
| `.agents/skills/` | Shared skills | Yes (all tools) |
| `AGENTS.md` | Repo context for all tools | Yes (Claude, Gemini, Cursor all read it) |
| `.claude/settings.json` | Permissions, hooks, MCP | Claude only |
| `.claude/CLAUDE.md` | Claude-specific instructions | Claude only |
| `.gemini/settings.json` | Tool controls, sandbox | Gemini only |
| `.gemini/GEMINI.md` | Gemini-specific instructions | Gemini only |
| `.gemini/commands/*.toml` | Gemini slash commands | Gemini only |
| `.cursor/rules/*.mdc` | Cursor rules | Cursor only |
| `.gitignore` additions | Ignore local settings | Universal |

### Repo bootstrap skill

A portable skill that scaffolds AI tool config into any directory.
This is the "create new repo config" counterpart to skill-creator's "create new skill" capability.

**Inputs:**
- Which tools to configure (claude, gemini, cursor, all)
- Repo type (e.g., python, typescript, monorepo) - affects default permissions and rules
- Whether to include example skills, hooks, commands

**Outputs:**
- Tool-specific settings files with sensible defaults
- `AGENTS.md` with repo structure documentation
- `.gitignore` additions for local override files
- Optionally: starter skills in `.agents/skills/`

This skill should itself live in `.agents/skills/repo-bootstrap/SKILL.md` so it's available from any tool.

### Managing local settings

Local settings (`.claude/settings.local.json`, Gemini env overrides) are:
- Never committed to repos
- Never managed by chezmoi (they're per-machine preferences)
- Created manually or by the repo-bootstrap skill

However, we can provide **templates** for common local settings patterns:
- "I want to auto-approve all tools in this repo" (Claude: `defaultMode: bypassPermissions`, Gemini: `--yolo`)
- "I want to restrict to read-only" (Claude: `defaultMode: plan`, Gemini: `defaultApprovalMode: plan`)
- "I need these additional directories" (Claude: `additionalDirectories`, Gemini: `context.includeDirectories`)

These templates could be:
1. Documented in `AGENTS.md` as copy-paste snippets
2. A skill that generates the local settings file interactively
3. A Gemini TOML command that applies a preset

### Permission patterns for common repo types

Reusable permission templates for `.claude/settings.json`:

**Python repo:**
```json
{
  "permissions": {
    "allow": ["Bash(python *)", "Bash(pip *)", "Bash(pytest *)", "Bash(ruff *)"]
  }
}
```

**TypeScript repo:**
```json
{
  "permissions": {
    "allow": ["Bash(npm *)", "Bash(npx *)", "Bash(bun *)", "Bash(tsc *)"]
  }
}
```

**Bazel repo (like this one):**
```json
{
  "permissions": {
    "allow": ["Bash(bazel build:*)", "Bash(bazel test:*)", "Bash(bazel query:*)"]
  }
}
```

These patterns inform the repo-bootstrap skill's output.

### Phase 7: Repo bootstrap and settings management

- [ ] Create `.agents/skills/repo-bootstrap/SKILL.md` - portable skill for initializing AI tool config in any directory
- [ ] Define permission template library (python, typescript, bazel, etc.) as reference files in the skill
- [ ] Create Gemini TOML command equivalent for repo bootstrapping
- [ ] Document local settings patterns (what goes in settings.local.json, when to use it, common presets)
- [ ] Consider: should chezmoi deploy a "default project settings" template somewhere accessible?

## Non-goals (for now)

- Goose support (work uses custom version, ignore)
- Cross-tool plugin/extension adaptation (rulesync #382, blocked)
- Publishing skills to agentskills.io (keep private for now)
- Gemini extension -> Claude MCP adaptation (future phase)
- Managing other users' local settings (these are personal by design)
