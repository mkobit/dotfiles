# Cross-tool AI configuration

This repo manages AI tool configuration (rules, skills, commands) for Claude Code, Gemini CLI, Cursor, and Codex CLI from a single source of truth.
Configuration is authored once and deployed to all tools via two layers plus chezmoi for global deployment.

## Layer 1: Always-on rules (rulesync)

Shared rules live in `.rulesync/rules/` as markdown files.
Rulesync generates tool-specific outputs for each target.

| Source | Generated outputs |
|--------|-------------------|
| `.rulesync/rules/*.md` | `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/*.mdc`, `.codex/memories/*.md` |

Configuration: `rulesync.jsonc` (targets: `claudecode`, `geminicli`, `cursor`, `codexcli`).

Regenerate all outputs:

```bash
bazel run //tools/rulesync:generate
```

Check for drift between generated and committed files:

```bash
bazel test //tools/rulesync:drift_tests
```

## Layer 2: Portable skills

Skills follow the [Agent Skills spec](https://agentskills.io) using `SKILL.md` files.
The canonical source is `src/agents/skills/` — one copy of each portable skill.

The sync pipeline copies skills to each tool's chezmoi directory:

- `src/chezmoi/dot_claude/skills/`
- `src/chezmoi/dot_gemini/skills/`
- `src/chezmoi/dot_cursor/skills/`

Upstream skills (e.g., `skill-creator` from anthropics/skills) are fetched via Bazel `http_archive` and included in the sync.

Sync skills to all tool directories:

```bash
bazel run //tools/agents:sync
```

Check for skill drift:

```bash
bazel test //src/agents/skills:drift_tests
```

## Layer 3: Chezmoi global deployment

Chezmoi deploys configuration from `src/chezmoi/` to `~` (destDir).

| Source directory | Deployed to | Contents |
|-----------------|-------------|----------|
| `dot_claude/` | `~/.claude/` | `CLAUDE.md`, skills (5) |
| `dot_gemini/` | `~/.gemini/` | `GEMINI.md`, skills (5) |
| `dot_cursor/` | `~/.cursor/` | rules (5 `.mdc`), skills (5) |
| `dot_codex/` | `~/.codex/` | `AGENTS.md` |

Preview changes before applying:

```bash
chezmoi diff
```

Apply changes:

```bash
chezmoi apply
```

## Common commands

| Task | Command |
|------|---------|
| Regenerate rulesync outputs | `bazel run //tools/rulesync:generate` |
| Sync portable skills | `bazel run //tools/agents:sync` |
| Validate all skills | `bazel run //tools/agents:validate` |
| Run all validation tests | `bazel test //:validation_tests` |
| Run all tests | `bazel test //...` |
| Preview chezmoi changes | `chezmoi diff` |
| Apply chezmoi changes | `chezmoi apply` |
| Check managed files | `chezmoi managed --include=files` |
