# Chezmoi configuration

## Notable cross-cutting features

- **AI agent sandbox**: Docker Sandboxes (`sbx`) provides microVM-isolated execution environments for AI agent CLIs; legacy `sandboxr` bwrap implementation is documented in [src/python/sandboxr/AGENTS.md](../python/sandboxr/AGENTS.md).
- **Command approval policy** (see below): shared Claude Code and Antigravity catalog with separate Codex project rules.
- **Secrets** (`[data.secrets]` in `.chezmoi.toml.tmpl`): rendered to a private (`0600`) file sourced by shell rc fragments, never inlined into a fragment itself.

## Docker Sandboxes ownership

Dotfiles does not generate personal Docker Sandbox guest overlays, executable tools, or plugin-install kits.
Each consuming repository owns its complete tracked SBX kit and toolchain.

## Command approval policy

Shared command catalog for Claude Code and Antigravity allow and deny rules.
Codex uses its own trusted project rules when configured.
Documented here rather than inside `.chezmoidata/ai/command_policy/` itself: chezmoi parses every file under `.chezmoidata/` as a data source, so a `.md` file there breaks every template reading chezmoi data with an "unknown format" error.

- One file per domain under `.chezmoidata/ai/command_policy/*.toml` (e.g. `git.toml`, `beads.toml`); every file contributes keys to the same `[ai.command_policy.commands]` table.
- Key: a literal, complete command head, e.g. `"git commit"`, `"bd"`.
  Value: `"allow"`, `"ask"`, or `"deny"`.
- Catalog `"ask"` contributes no grant. It removes an exact previous live allow unless the per-tool source configuration explicitly ensures that entry. A configured ensure can grant a per-tool exception to catalog ask.
  Catalog `"deny"` excludes its exact matching allow, including an ensure, and renders a native denial. Explicit remove still excludes matching allows.
  Existing native denials remain when the catalog says allow or ask. To relax a preexisting denial, remove that native denial explicitly; the allow-only remove control does not remove denials.
  Broader unmanaged live allows remain and may still grant access. Omission alone does not revoke a previous live grant.
- `dot_claude/modify_settings.json` renders Claude Code `permissions.allow` and `permissions.deny` with `Bash(<command>:*)` syntax.
  `dot_gemini/antigravity-cli/modify_settings.json` renders Antigravity `permissions.allow` and `permissions.deny` with `command(<command>)` syntax. The renderer escapes the command as a regex.
  Prefix matching belongs in the renderer. The catalog stores literal command heads.
- Both tools merge computed grants, configured ensure entries, and surviving live allow entries. Explicit remove entries exclude matching allows. Native deny lists merge computed, configured, and live denials. Other native permission fields survive.
  Retired command metadata removes only exact legacy live allow entries. An overlay can disable retirement or explicitly grant the command again.
- New command = new key, in a new or existing domain file.
  An overlay adds a command by adding a key, or changes an existing one's mode by overriding the same key (e.g. `"git rebase" = "ask"`) — plain chezmoi dict merge, no add/remove/enabled machinery needed (scalars override cleanly on collision; only chezmoi list values have the wholesale-replace problem).
- The selected push is `git push --set-upstream origin HEAD`. Bare push, force push, `git reset`, and `git clean` are outside the allow catalog.
  The four workflow grants are `mise run agent:architect`, `mise run agent:work`, `mise run pr:ship`, and `mise run repo:bootstrap`. Verification uses `mise run verify`.
  These are command prefixes. They do not validate appended arguments or prove branch, remote, PR, or head identity. The shipping task must check those values before publication.
- Native file rules remain configurable through `claude_code.settings.permissions` and `gemini.permissions`.
  [Claude permissions](https://code.claude.com/docs/en/permissions#read-and-edit) supports workspace-relative gitignore paths with `Read` and `Edit`; `Edit` covers editing tools.
  [Antigravity permissions](https://antigravity.google/docs/permissions/#supported-cli-actions-and-matching-rules) supports workspace-relative `read_file(path)` and `write_file(path)`, recursive directory paths, and `permissions.deny`. A denied read also denies writes. Deny takes precedence over ask and allow.
  Do not add recursive parent rules that also include workspace files. The documented APIs do not establish an outside-only parent denial that preserves normal workspace access. Keep their normal outside-workspace prompts and the physical SBX boundary.
  Native path rules do not establish complete filesystem isolation. Parent-relative text does not prove protection against equivalent absolute paths, symlinks, or shell subprocess access. SBX mounts and validated workspace boundaries provide the outer boundary.
- Codex host settings use `on-request` approval and workspace write permissions. Existing modern selectors use `default_permissions = ":workspace"`; existing legacy selectors retain `sandbox_mode = "workspace-write"` and their other sandbox fields. New configurations use the modern scheme. Neither scheme establishes repository-only reads.
  The modifier preserves unrelated fields and named permission definitions. It returns matching base configuration bytes unchanged.
  The separate private `.codex/unattended.config.toml` profile is deployed only when `ai.workflow.enabled` is true. A disabled or missing decision ignores the target and preserves an unowned file.
  The profile uses `never` approval and full access with the base file's selector scheme. Modern profiles set `default_permissions = ":danger-full-access"` directly; this built-in cannot be an `extends` parent. Never combine a modern selector with legacy sandbox keys.
  Sources: [OpenAI configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) and [profile configuration](https://learn.chatgpt.com/docs/config-file/config-advanced).
  This is a host-side profile file. Select it only inside an independently verified guest where its presence is confirmed. The guest launcher can use supported guest-only CLI flags. Host generation does not prove that SBX received the file.

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
