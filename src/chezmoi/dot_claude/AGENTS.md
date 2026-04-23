# Claude Code configuration

## Why two config files

Claude Code splits configuration across two files for no obvious reason:

- `~/.claude/settings.json` — deployment config: permissions, env vars, sandbox, MCP servers, hooks.
- `~/.claude.json` — UI preferences AND mutable runtime state: editor mode, startup counts, seen-tips history, feature flags.

These are managed separately because Claude Code itself writes to `~/.claude.json` constantly.
Injecting only preferences while leaving runtime state alone requires a modify script.

## Managed files

| Target | Chezmoi source | Data key |
|---|---|---|
| `~/.claude/settings.json` | `dot_claude/modify_settings.json.tmpl` | `claude_code.settings` |
| `~/.claude.json` | `modify_dot_claude.json.tmpl` | `claude_code.preferences` |

Both sources live in `src/.chezmoidata/claude_code.toml`.

## Feature control

Controlled by `claude_code.enabled` in `.chezmoidata/`.
If disabled, no Claude Code files are installed.
