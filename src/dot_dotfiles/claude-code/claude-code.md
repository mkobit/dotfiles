# Claude Code

Claude Code is Anthropic's official CLI tool for interacting with Claude AI for software engineering tasks.

## Official Documentation

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Getting Started Guide](https://docs.anthropic.com/en/docs/claude-code/getting-started)
- [Installation Instructions](https://docs.anthropic.com/en/docs/claude-code/installation)

## Configuration

### File Precedence
Configuration is loaded in this order (later files override earlier ones):
1. Global config: `~/.config/claude/config.toml`
2. Project config: `.claude/config.toml`
3. Project instructions: `CLAUDE.md`

### Key Configuration Files
- `CLAUDE.md` - Project context and instructions for Claude
- `.claude/config.toml` - Project-specific settings (API keys, preferences)
- `.claude/hooks/` - Custom hooks for tool execution events

## Core Features

### Hooks
Event-driven automation that triggers on tool calls and other events.
- [Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks)
- [Hook Examples](https://docs.anthropic.com/en/docs/claude-code/hooks#examples)

Common hook types:
- `user-prompt-submit-hook` - Runs before user input is sent
- `tool-call-hook` - Runs on specific tool invocations
- `session-start-hook` - Runs when starting a new session

### Agents
Specialized Claude instances for specific tasks with custom contexts and tool access.
- [Agents Documentation](https://docs.anthropic.com/en/docs/claude-code/agents)
- [Creating Custom Agents](https://docs.anthropic.com/en/docs/claude-code/agents#custom-agents)

### Context Management
- Project-level context via `CLAUDE.md`
- Session persistence and memory
- File and directory awareness

## Integration Patterns

### With chezmoi
- Use `CLAUDE.md` templates for dynamic project instructions
- Hook integration for automated file processing
- Agent-driven configuration management

### Common Workflows
- Automated testing and validation via hooks
- Custom development agents for specific project types
- Integration with build systems and CI/CD