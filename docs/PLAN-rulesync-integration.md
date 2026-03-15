# Plan: Unified AI rule authoring and cross-tool deployment

Status: Draft
Branch: `ai-rule-builder`
Created: 2026-03-10
Target tools: Claude Code, Gemini CLI, Cursor, Codex CLI

## Goals

This project serves three priorities, in order:

1. **User-level cross-tool config** — global skills, commands, rules, MCP servers, and marketplace skills deployed to all AI tools from one source of truth via chezmoi.
2. **This repo as reference implementation** — demonstrate cross-tool rule automation patterns that will be replicated to future repos.
3. **Build automation for repo-specific config** — tools to create repo-level commands, hooks, and skills (the skill-creator skill already handles this).

Every phase below is annotated with the priority it serves.

## Problem

AI tool configuration is fragmented across four concerns:
1. Always-on rules (preferences, coding standards) — duplicated per tool.
2. On-demand skills (SKILL.md) — portable via Agent Skills spec but only deployed to Claude today.
3. Slash commands — tool-specific formats (Claude = skill frontmatter, Gemini = TOML, Cursor = @mentions, Codex = N/A).
4. MCP servers and plugins — configured differently per tool, no central registry.

No way to author once and deploy everywhere.

## Cross-tool format matrix

| Concern | Claude Code | Gemini CLI | Cursor | Codex CLI |
|---------|------------|------------|--------|-----------|
| Always-on rules | `CLAUDE.md` | `GEMINI.md` | `.cursor/rules/*.mdc` | `~/.codex/AGENTS.md` (3-tier: global, repo root, cwd) |
| Skills (on-demand) | `.claude/skills/*/SKILL.md` | `.gemini/skills/*/SKILL.md` | `.cursor/skills/*/SKILL.md` | N/A |
| Portable skills | `.agents/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` | `.agents/skills/*/SKILL.md` | N/A |
| Slash commands | Skill with `disable-model-invocation: true` | `.gemini/commands/*.toml` (TOML format, separate system) | `@rule-name` / manual apply rules | N/A |
| Global skills dir | `~/.claude/skills/` | `~/.gemini/skills/` | `~/.cursor/skills/` | N/A |
| Global commands dir | N/A (merged into skills) | `~/.gemini/commands/` | N/A | N/A |
| Settings file | `settings.json` | `settings.json` | UI-based | `config.json` or `config.yaml` |
| MCP servers | `.mcp.json` (project), `~/.claude.json` (user) | MCP in `settings.json` | N/A | N/A |

Key facts:
- Skills (SKILL.md) are portable across Claude, Gemini, and Cursor via `.agents/skills/`.
- Codex CLI has no skill or command system; it reads only `AGENTS.md` for context.
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
Portable across Claude, Gemini, and Cursor via `.agents/skills/` or tool-specific paths.
Chezmoi deploys global skills to each tool's global skills dir.
For repo-specific skills: scaffold into `.agents/skills/` in any repo using skill-creator.

### Slash commands (tool-specific, not unified)

Claude: skills with `disable-model-invocation: true`.
Gemini: TOML files in `.gemini/commands/`.
Cursor: rules with manual-only application.
Codex: no command system.
These remain authored per-tool where needed.
Rulesync may generate some of these (it supports commands for Claude and simulated commands for others).

### Scaffolding

Use skill-creator (from anthropics/skills marketplace) to create skills in any directory.
Target `.agents/skills/` for cross-tool portability.
Target tool-specific dirs when needed (e.g., Gemini TOML commands).

## Current state

| Component | Status |
|-----------|--------|
| Rulesync binary | v7.6.3 in multitool + chezmoi external |
| Rulesync config | `rulesync.jsonc` targeting claudecode, geminicli, cursor, codexcli |
| Shared always-on rules | `.rulesync/rules/` (5 rules), generated to all 3 tools. Chezmoi templates migrated to static files; `agents.toml` deleted. |
| Portable skills (canonical) | 4 in `src/agents/skills/`, replicated to all 3 tool dirs via `bazel run //tools/agents:sync` |
| Upstream skills | 1 (`skill-creator`) fetched via Bazel `http_archive` from anthropics/skills |
| Claude skills (deployed) | 5 in `src/chezmoi/dot_claude/skills/` (4 portable + 1 upstream) |
| Claude commands (internal) | `claude/new/{command,agent,hook}.md`, `obsidian/{base,organize,transform}.md` |
| Gemini commands | None |
| Cursor rules | All 5 `.mdc` files in `.cursor/rules/` now rulesync-managed (repo-local only) |
| Target tools | 4 (Claude Code, Gemini CLI, Cursor, Codex CLI) |
| Codex CLI global config | `src/chezmoi/dot_codex/AGENTS.md` deployed to `~/.codex/AGENTS.md` via chezmoi |
| Codex CLI repo rules | `.codex/memories/` (4 files, rulesync-managed) |
| Validation tests | 50 (`//:validation_tests`), 65 total (`//...`) |
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

### Phase 1: Bootstrap rulesync (Priority 2)

- [x] Create `rulesync.jsonc` targeting: claude, gemini-cli, cursor
- [x] Create `.rulesync/rules/` with shared rules:
  - `00-preferences.md` (from `agents.toml`)
  - `10-technical-writing.md` (always-on portion)
  - `11-write-agent-context.md` (always-on portion)
- [x] Run `rulesync generate`, verify outputs for all three tools
- [x] Bazel integration: `//tools/rulesync:generate` genrule, `//tools/rulesync:check` drift check
- [x] Decide output integration: preferences migrated from `agents.toml` to rulesync as single source of truth; chezmoi templates to be updated in Phase 2
- [x] Commit generated outputs

### Phase 2: Portable skill deployment via chezmoi (Priority 1)

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

### Phase 3: Upstream skill-creator integration (Priority 1)

- [x] Fetch `skill-creator` from anthropics/skills via Bazel `http_archive` (pinned to commit `b0cbd3d`)
- [x] Update sync pipeline to copy full skill directories (not just SKILL.md) and discover upstream skills from Bazel runfiles
- [x] Deploy `skill-creator` to all three tool dirs via `bazel run //tools/agents:sync`
- [x] Delete superseded internal `claude-extension-builder` skill and `claude/new/skill.md` command
- [x] Keep `claude/new/{hook,agent,command}.md` (not covered by upstream skill-creator)
- [x] Add directory-level `sh_test` drift tests for upstream skills (`//src/agents/skills:upstream_drift_tests`, 3 targets)
- [x] Exclude upstream-vendored Python scripts from ruff formatting (`pyproject.toml`)
- [x] All 28 validation tests pass (`//:validation_tests`)

### Phase 4: Gemini CLI commands and Codex CLI support (Priority 2)

- [ ] Evaluate rulesync's Gemini command support (simulated commands)
- [ ] If insufficient: create bazel genrule to transform skill-like definitions into Gemini TOML commands
- [ ] Deploy global Gemini commands via chezmoi (`dot_gemini/commands/`)
- [ ] Consider which Claude slash-commands warrant Gemini TOML equivalents
- [x] Create `src/chezmoi/dot_codex/` with `AGENTS.md` for Codex CLI global context
- [x] Add `codexcli` target to rulesync — generates `.codex/memories/*.md` (4 rules) + `AGENTS.md` (discarded, repo keeps hand-coded version)
- [ ] Optionally deploy `config.yaml` with Codex CLI defaults

### Phase 5: Bazel integration (Priority 2)

- [x] `rulesync_generate` genrule: `//tools/rulesync:generate` (existed from Phase 1)
- [x] Rulesync drift tests: 19 `diff_test` targets comparing genrule outputs vs committed files (`//tools/rulesync:drift_tests`)
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

### Phase 6: Cursor rule migration (Priority 2)

- [x] Evaluate existing `.cursor/rules/*.mdc` files (5 total: 3 rulesync-managed, 2 manually authored)
- [x] Migrate portable content to rulesync rules:
  - `agents-md.mdc` -> `.rulesync/rules/01-agents-md.md` (generates outputs for all 3 tools)
  - `no-auto-commit.mdc` -> `.rulesync/rules/02-no-auto-commit.md` (generates outputs for all 3 tools)
- [x] Delete manually-authored `.cursor/rules/agents-md.mdc` and `no-auto-commit.mdc` (now rulesync-managed)
- [x] Update BUILD files: root `exports_files`, `.claude/BUILD.bazel`, `tools/rulesync/BUILD.bazel` (sources, genrule, drift pairs)
- [x] All 46 validation tests pass (6 new drift tests for the 2 rules across 3 tools)
- [ ] Deploy cursor rules to destDir if cursor is used globally (currently repo-local only)

### Phase 7: Upstream skill ingestion pipeline (Priority 1)

Replace the reverted repo-bootstrap skill with a pipeline for deterministically fetching, validating, and deploying open-source skills from marketplaces.

- [ ] **Registry format** — define a Starlark `.bzl` or JSONC file listing external skill repos with commit pins, skill names, and SHA256 hashes
- [ ] **Extend `http_archive` pattern** — support multiple external skill repos in `MODULE.bazel` (currently only `anthropic_skills`)
- [ ] **Automated validation** — run existing SKILL.md validators (`skill_frontmatter_test`, `skill_lint_test`, `skill_structure_test`) on upstream skills as part of the ingestion pipeline
- [ ] **Safety analysis layer (deterministic)** — pattern-based checks for dangerous commands (`rm -rf /`, `sudo`, credential access, exfiltration URLs, encoded payloads)
- [ ] **Safety analysis layer (probabilistic)** — LLM-based content review as opt-in Bazel test (tagged `manual`, requires API key)
- [ ] **CI enforcement** — all deterministic checks in `//:validation_tests`; LLM safety checks runnable via `--test_tag_filters=safety`
- [ ] **Sync integration** — upstream skills flow through existing `bazel run //tools/agents:sync` pipeline to all tool dirs

### Phase 8: MCP and plugin configuration (Priority 1)

Centralize MCP server and plugin configuration across tools.

- [ ] Add MCP server definitions to `chezmoidata` (server name, command, args, env, per-tool enablement)
- [ ] Generate `.mcp.json` for Claude Code via chezmoi template
- [ ] Generate MCP entries in Gemini `settings.json` via chezmoi template
- [ ] Manage Gemini extensions (version-pinned install commands in chezmoi run scripts)
- [ ] Cross-tool plugin registry: single data source mapping plugins to tool-specific config formats

## Open questions

1. **Skill deduplication**: If a skill is both a portable SKILL.md AND has content extracted to rulesync always-on rules, how to avoid redundancy?
   - Recommendation: The always-on rule contains the minimal "always apply this" subset. The full skill contains detailed instructions for when it's activated. They serve different purposes.

2. **Gemini commands vs skills**: Gemini has both. Some things are better as commands (quick shortcuts with `{{args}}`), others as skills (complex on-demand expertise). How to decide?
   - Recommendation: If it's a simple prompt template with args, Gemini TOML command. If it needs multi-step instructions, SKILL.md. Rulesync may generate both.

3. **`.agents/skills/` vs tool-specific dirs**: Deploy to the portable path or replicate to each tool's dir?
   - Recommendation: For project-level, use `.agents/skills/` (all tools discover it). For global (chezmoi-deployed), replicate to each tool's dir since there's no global `.agents/` convention.

4. **Chezmoi template vars in skills**: Skills are static SKILL.md. Some may want `destDir` or other vars.
   - Recommendation: Use `.tmpl` suffix in chezmoi source. Chezmoi renders the template, outputs a static SKILL.md.

5. **Safety analysis thresholds**: What constitutes a blocking safety finding vs a warning? How large should the dangerous-pattern library be?
   - Open: needs experimentation with real upstream skills.

6. **LLM provider for safety review**: Using Claude API adds a CI dependency and cost. Acceptable for `manual`-tagged tests?
   - Open: evaluate cost-per-review and whether a smaller model suffices.

7. **Rulesync Codex CLI support**: Does rulesync support a `codexcli` target, or do we need a custom generator for `AGENTS.md`?
   - Resolved: rulesync v7.6.3 natively supports `codexcli` target, generating `AGENTS.md` + `.codex/memories/*.md`.

8. **Registry format**: Starlark `.bzl` (native Bazel) vs JSONC (human-editable, tool-agnostic)?
   - Recommendation: Starlark for Bazel-native integration; JSONC if we want non-Bazel consumers.

9. **Skill ingestion granularity**: Fetch whole repos and cherry-pick skills, or fetch individual skill directories?
   - Recommendation: Whole repo via `http_archive` with `strip_prefix` to select specific paths, matching current `anthropic_skills` pattern.

## Non-goals (for now)

- Goose support (work uses custom version, ignore)
- Cross-tool plugin/extension adaptation (rulesync #382, blocked)
- Publishing skills to agentskills.io (keep private for now)
- Repo bootstrapping as a skill (redundant with chezmoi global config + skill-creator)
- Managing other users' local settings (these are personal by design)
