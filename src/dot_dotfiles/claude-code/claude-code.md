# Claude Code Configuration Guide

Claude Code CLI integration with chezmoi dotfiles management.

## Quick Reference

**Installation**: Managed via `.chezmoiexternal` → `~/.local/bin/claude`
**Configuration**: JSON files in `~/.claude/` directory
**Environment Variables**: Set via shell snippets in `~/.dotfiles/zsh/snippets/`

## Configuration Files

### User Settings
- **Location**: `~/.claude/settings.json`
- **Purpose**: Global user preferences and defaults
- **Managed by**: `~/.dotfiles/claude-code/settings.json.tmpl`

### Project Settings (Optional)
- **Location**: `~/.claude/settings.local.json`
- **Purpose**: Personal project overrides
- **Managed by**: `~/.dotfiles/claude-code/settings.local.json.tmpl`

## Environment Variables

Set via shell snippets for CLI behavior control:
- `DISABLE_AUTOUPDATER=true` - Prevent automatic updates
- `DISABLE_TELEMETRY=true` - Opt out of usage tracking
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=true` - Minimize network calls

## Documentation Links

### Core Documentation
- **Overview**: https://docs.claude.com/en/docs/claude-code/overview
- **CLI Reference**: https://docs.claude.com/en/docs/claude-code/cli-reference
- **Settings Reference**: https://docs.claude.com/en/docs/claude-code/settings

### Key Concepts
- **Configuration Precedence**: Enterprise → CLI args → Local project → Shared project → User
- **JSON Configuration**: Permissions, model settings, output style, cleanup periods
- **Agents & Tools**: MCP integration, custom tool development
- **Project Integration**: `.claude/` directory for team settings

## Feature Control

Claude Code installation and configuration controlled by `claude_code.enabled` feature flag:
- **Personal environments**: `true` (default in `.chezmoidata.toml`)
- **Work environments**: `false` (disabled in work `chezmoi.toml.tmpl`)

When disabled, no Claude Code files are installed or managed.