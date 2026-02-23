# Claude Code configuration

## Configuration files

- **User settings**: `~/.claude/settings.json` (managed by `src/dot_claude/settings.json.tmpl`).
- **Project settings**: `~/.claude/settings.local.json` (personal overrides).

## Configuration structure

- **Source**: `src/.chezmoidata/claude_code.toml` under `[claude_code.settings]`.
- **Render**: Uses `toPrettyJson` in the template.

## Feature control

- Controlled by `claude_code.enabled` in `.chezmoidata/`.
- If disabled, no Claude Code files are installed.
