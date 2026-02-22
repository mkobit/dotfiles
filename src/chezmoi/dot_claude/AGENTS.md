# Claude Code configuration

## Configuration Files

- **User settings**: `~/.claude/settings.json` (managed by `src/dot_claude/settings.json.tmpl`).
- **Project settings**: `~/.claude/settings.local.json` (personal overrides).

## Configuration Structure

- **Source**: `src/.chezmoidata/claude_code.toml` under `[claude_code.settings]`.
- **Render**: Uses `toPrettyJson` in the template.

## Feature Control

- Controlled by `claude_code.enabled` in `.chezmoidata/`.
- If disabled, no Claude Code files are installed.
