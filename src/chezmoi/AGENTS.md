# Chezmoi Configuration

This directory contains the Chezmoi source state for dotfiles management.

## Directory Structure

- `.chezmoidata/`: TOML data files loaded into the template context.
- `.chezmoiexternals/`: External dependencies (archives, git repos) managed by Chezmoi.
- `.chezmoiscripts/`: Scripts executed by `chezmoi apply` (e.g., `run_once_` scripts).
- `.chezmoitemplates/`: Shared template fragments.
- `dot_*/`: Files that will be deployed to the user's home directory (e.g., `dot_config` -> `~/.config`).

## Notable cross-cutting features

- **AI agent sandbox** (`sandboxr`, see [src/python/sandboxr/AGENTS.md](../python/sandboxr/AGENTS.md)): autonomous agent CLI runs are wrapped by `sandboxr` reading `.chezmoidata/ai/sandbox.toml`, rendered to `~/.config/ai-policy/sandbox.toml` plus per-tool fragments under `dot_config/ai-policy/`.
- **Command approval policy** (see below): global command-approval allowlist for attended (HITL) agent sessions, rendered into each tool's native permission syntax.
- **Secrets** (`[data.secrets]` in `.chezmoi.toml.tmpl`): rendered to a private (`0600`) file sourced by shell rc fragments, never inlined into a fragment itself.

## Command approval policy

Global, tool-neutral allowlist of shell commands that AI coding agents auto-approve without prompting the human.
Defined once, rendered into each tool's native permission syntax.
Documented here rather than inside `.chezmoidata/ai/command_policy/` itself: chezmoi parses every file under `.chezmoidata/` as a data source, so a `.md` file there breaks every template reading chezmoi data with an "unknown format" error.

- One file per domain under `.chezmoidata/ai/command_policy/*.toml` (e.g. `git.toml`, `beads.toml`); every file contributes keys to the same `[ai.command_policy.commands]` table.
- Key: a literal, complete command head, e.g. `"git commit"`, `"bd"`.
  Value: `"allow"`, `"ask"`, or `"deny"`.
- `"ask"` (or simply omitting the command) renders nowhere in either tool.
  Absence from a tool's allow/deny rules is what falls back to its normal per-use prompt.
  Most entries should be omitted rather than explicitly written as `"ask"`.
- Rendered by `dot_claude/modify_settings.json` → Claude Code's `permissions.allow`/`.deny`, `Bash(<command>:*)` syntax.
  Rendered by `dot_gemini/antigravity-cli/modify_settings.json` → Antigravity's `permissions.allow`/`.deny`, `command(<command>)` syntax (each whitespace token matched as an anchored regex).
  The `deny` key name there is inferred from Antigravity's documented "Deny > Ask > Allow" precedence, not yet live-tested.
  Prefix/wildcard matching is entirely a renderer concern — the schema only ever stores complete, literal commands.
- Both tools' `permissions.allow`/`.deny` are fully replaced by chezmoi on every apply, including any grant agy's own in-CLI "always allow" flow wrote into the live file.
  Chezmoi owns these fields; add a command to the catalog rather than relying on a tool's own approval UI to persist it.
- New command = new key, in a new or existing domain file.
  An overlay adds a command by adding a key, or changes an existing one's mode by overriding the same key (e.g. `"git rebase" = "ask"`) — plain chezmoi dict merge, no add/remove/enabled machinery needed (scalars override cleanly on collision; only chezmoi list values have the wholesale-replace problem).
- Why `git push`/`reset`/`clean` are excluded: see the rationale comment block in `git.toml`.
  Reflog-recoverability and remote-write/leak risk are the deciding factors, not "is it a local command."

## Script Conventions

### Sourcing Shared Libraries

Scripts in `.chezmoiscripts/` should source shared shell libraries (like `logging.sh`) from `.chezmoitemplates` using the absolute path provided by `{{ .chezmoi.sourceDir }}`.

**Pattern:**

```bash
# Source logging library from chezmoi source
CHEZMOI_SOURCE_DIR="{{ .chezmoi.sourceDir }}"
source "${CHEZMOI_SOURCE_DIR}/.chezmoitemplates/shell/logging.sh"
```

**Why:**
- `{{ .chezmoi.sourceDir }}` resolves to the absolute path of the source directory.
- This allows scripts to use shared utilities without them being deployed to the destination machine.
- Avoid using relative paths (e.g., `../../.chezmoitemplates`) as the execution context might vary.

### Referencing repository root

The `{{ .chezmoi.workingTree }}` attribute evaluates to the absolute path of the git repository root.
This is useful for referencing project files (like Python source code) that live outside of the chezmoi source directory.

### Referencing destination directory

When referring to the destination home directory in scripts (e.g., for `PATH` manipulation), always use `{{ .chezmoi.destDir }}` instead of `{{ .chezmoi.homeDir }}` or hardcoded paths like `$HOME`.
