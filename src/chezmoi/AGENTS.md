# Chezmoi configuration

## Notable cross-cutting features

- **AI agent sandbox**: Docker Sandboxes (`sbx`) provides microVM-isolated execution environments for AI agent CLIs; legacy `sandboxr` bwrap implementation is documented in [src/python/sandboxr/AGENTS.md](../python/sandboxr/AGENTS.md).
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
