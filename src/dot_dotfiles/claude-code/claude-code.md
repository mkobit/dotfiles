# Claude Code configuration guide

Claude Code CLI integration with chezmoi dotfiles management.

## Quick reference

**Installation**: Managed via `.chezmoiexternal.toml.tmpl` → `~/.local/bin/claude`
**Configuration**: JSON files in `~/.claude/` directory
**Environment variables**: Set via `settings.json` env section. This is supported by Claude code.

## Configuration files

### User settings
- **Location**: `~/.claude/settings.json`
- **Purpose**: Global user preferences and defaults
- **Managed by**: `src/dot_claude/settings.json.tmpl`

### Project settings (optional)
- **Location**: `~/.claude/settings.local.json`
- **Purpose**: Personal project overrides
- **Managed by**: User (not templated)

## Configuration structure

Settings are defined in `.chezmoidata.toml` under `[claude_code.settings]` and rendered to JSON using chezmoi's `toPrettyJson` function.

## Feature control

Claude Code installation controlled by `claude_code.enabled` feature flag in `chezmoi` data.

When disabled, no Claude Code files are installed.

## Documentation links

- [Overview](https://docs.claude.com/en/docs/claude-code/overview)
- [CLI reference](https://docs.claude.com/en/docs/claude-code/cli-reference)
- [Settings reference](https://docs.claude.com/en/docs/claude-code/settings)
- [Sub-agents](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [Hooks](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [MCP (model context protocol)](https://docs.claude.com/en/docs/claude-code/mcp)
