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

## Skills

Skills are reusable tools that an agent can use to perform specific tasks. They are defined as executable scripts or binaries and can be written in any language.

- **Location**: Skills are typically located in the `.claude/skills/` directory within a project or in the global `~/.claude/skills/` directory.
- **Structure**: Each skill should be in its own subdirectory and include a `skill.yaml` file that describes the skill's inputs, outputs, and how to execute it.

For detailed information on creating and using skills, see the [official documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).

## Plugins

Plugins extend Claude Code's functionality by adding new commands, hooks, or other integrations.

- **Location**: Plugins are typically located in the `.claude/plugins/` directory.
- **Structure**: A plugin is a directory containing a `plugin.yaml` file and the necessary scripts or binaries.

For more information on developing plugins, refer to the [official plugin documentation](https://docs.claude.com/en/docs/claude-code/plugins).

## Feature control

Claude Code installation controlled by `claude_code.enabled` feature flag in `chezmoi` data.

When disabled, no Claude Code files are installed.

## Documentation links

- [Overview](https://docs.claude.com/en/docs/claude-code/overview)
- [CLI reference](https://docs.claude.com/en/docs/claude-code/cli-reference)
- [Settings reference](https://docs.claude.com/en/docs/claude-code/settings)
- [Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- [Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Sub-agents](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [Hooks](https://docs.claude.com/en/docs/claude-code/hooks-guide)
- [MCP (model context protocol)](https://docs.claude.com/en/docs/claude-code/mcp)
