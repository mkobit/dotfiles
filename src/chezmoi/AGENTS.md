# Chezmoi configuration

## Notable cross-cutting features

- **AI agent sandbox**: Docker Sandboxes (`sbx`) provides microVM-isolated execution environments for AI agent CLIs; legacy `sandboxr` bwrap implementation is documented in [src/python/sandboxr/AGENTS.md](../python/sandboxr/AGENTS.md).
- **Command approval policy** (see below): shared Claude Code and Antigravity catalog; SBX integrations for Codex and Cursor are separate units.
- **Secrets** (`[data.secrets]` in `.chezmoi.toml.tmpl`): rendered to a private (`0600`) file sourced by shell rc fragments, never inlined into a fragment itself.

## Docker Sandboxes ownership

Dotfiles does not generate personal Docker Sandbox guest overlays, executable tools, or plugin-install kits.
Each consuming repository owns its complete tracked SBX kit and toolchain.

## Command approval policy

Shared command catalog for Claude Code and Antigravity allow, prompt, and deny rules.
The SBX policy selects Claude Code, Antigravity, Codex, and Cursor; this unit implements the first two renderers.
Pi approval support is excluded.
Codex and Cursor integration remain separate units.
Documented here rather than inside `.chezmoidata/ai/command_policy/` itself: chezmoi parses every file under `.chezmoidata/` as a data source, so a `.md` file there breaks every template reading chezmoi data with an "unknown format" error.

- One file per domain under `.chezmoidata/ai/command_policy/*.toml` (e.g. `git.toml`, `beads.toml`); every file contributes keys to the same `[ai.command_policy.commands]` table.
- Key: a literal, complete command head, e.g. `"git commit"`, `"bd"`.
  Value: `"allow"`, `"ask"`, `"prompt"`, or `"deny"`.
- `"ask"` (or simply omitting the command) renders nowhere in either tool.
  Absence from a tool's allow/deny rules is what falls back to its normal per-use prompt.
  Most entries should be omitted rather than explicitly written as `"ask"`.
- `"prompt"` renders an explicit native `permissions.ask` rule.
  Use it when an execution head must require approval even with a broader live allow.
- Rendered by `dot_claude/modify_settings.json` → Claude Code's `permissions.allow`/`.ask`/`.deny`, `Bash(<command>:*)` syntax.
  Rendered by `dot_gemini/antigravity-cli/modify_settings.json` → Antigravity's `permissions.allow`/`.ask`/`.deny`, literal `command(<command>)` token syntax.
  Exact retired grants retain their old syntax for migration.
  Prefix/wildcard matching is entirely a renderer concern — the schema only ever stores complete, literal commands.
- Both tools merge computed command grants, configured ensure entries, and surviving live allow entries.
  Configured remove entries exclude matching allow entries.
  Both renderers retain live and configured asks and denials.
  Native precedence is deny, then ask, then allow; a broad live allow does not override an explicit ask.
  Force or bypass modes can disable confirmation; rendered settings alone do not prove runtime enforcement.
  Retired command metadata removes only matching legacy live allow entries unless an overlay disables retirement or explicitly re-grants the command.
- SBX grants allow all later arguments: removal prefixes also permit bulk and force flags.
  Use named removal and `--skip-host-commands` for pilot environment operations unless setup explicitly requires host commands.
  No broad `sbx` grant is generated.
- New command = new key, in a new or existing domain file.
  An overlay adds a command by adding a key, or changes an existing one's mode by overriding the same key (e.g. `"git rebase" = "ask"`) — plain chezmoi dict merge, no add/remove/enabled machinery needed (scalars override cleanly on collision; only chezmoi list values have the wholesale-replace problem).
- Why `git push`/`reset`/`clean` are excluded: see the rationale comment block in `git.toml`.
  Reflog-recoverability and remote-write/leak risk are the deciding factors, not "is it a local command."

## Script conventions

### Sourcing shared libraries

Scripts in `.chezmoiscripts/` source shared shell libraries (e.g. `logging.sh`) from `.chezmoitemplates/` via `{{ .chezmoi.sourceDir }}`, not `.chezmoi.destDir` — `.chezmoitemplates/` files are never deployed, so only the source path resolves them.
Use the absolute path, not a relative one (e.g. `../../.chezmoitemplates`) — the script's execution cwd varies.

```bash
CHEZMOI_SOURCE_DIR="{{ .chezmoi.sourceDir }}"
source "${CHEZMOI_SOURCE_DIR}/.chezmoitemplates/shell/logging.sh"
```

### Referencing the repository root

`{{ .chezmoi.workingTree }}` evaluates to the git repository root — use it for project files (e.g. Python source) that live outside the chezmoi source directory.
