# Claude Code configuration

## Managed files

| Target | Chezmoi source | Data key |
|---|---|---|
| `~/.claude/settings.json` | `dot_claude/modify_settings.json` | `claude_code.settings` |

`~/.claude.json` is Claude Code's own runtime state (OAuth session, MCP server config, per-project trust state, startup counts, caches) — not managed by chezmoi at all.
A key that's documented as belonging in `settings.json` (like `editorMode`) goes in `claude_code.settings` even though Claude Code separately caches a copy of the active value into `~/.claude.json` on its own.

## Feature control

Controlled by `claude_code.enabled` in `.chezmoidata/`.
If disabled, no Claude Code files are installed.
