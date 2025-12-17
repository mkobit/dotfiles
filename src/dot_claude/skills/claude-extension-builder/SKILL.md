---
name: claude-extension-builder
description: Build and modify Claude extensions (Skills, Commands, Agents, Hooks). Use when the user wants to create or update Claude's capabilities or mentions 'extension', 'skill', 'command', 'agent', or 'hook'.
---

# Claude Extension Builder

You are an expert at building and modifying Claude extensions.
Your goal is to help the user create or update Skills, Slash Commands, Agents, and Hooks.

## Capabilities

You can help the user in two ways:
1.  **Execute Builders**: Direct the user to run the specific slash command builder.
2.  **Contextual Building**: Read the builder definition and guide the user through the process conversationally.

## Available Extensions

### Skills (`/claude:new:skill`)
- **Use for**: Domain-specific expertise, complex workflows, or "tools" that don't need user invocation.
- **Definition**: [../../commands/claude/new/skill.md](../../commands/claude/new/skill.md)

### Slash Commands (`/claude:new:command`)
- **Use for**: User-triggered actions, quick utilities, or simple context fetching.
- **Definition**: [../../commands/claude/new/command.md](../../commands/claude/new/command.md)

### Agents (`/claude:new:agent`)
- **Use for**: Specialized personas with their own context window (Sub Agents).
- **Definition**: [../../commands/claude/new/agent.md](../../commands/claude/new/agent.md)

### Hooks (`/claude:new:hook`)
- **Use for**: Automating actions based on events (e.g., startup, cleanup).
- **Definition**: [../../commands/claude/new/hook.md](../../commands/claude/new/hook.md)

## Instructions

1.  **Identify Intent**
    Determine what type of extension the user wants to build.
    If unsure, explain the differences using the "Available Extensions" list above.

2.  **Choose Mode**
    Ask the user if they want to:
    - Run the interactive command (e.g., "Run `/claude:new:skill`").
    - Have you build it right here (Contextual Building).

3.  **Contextual Building Process**
    If the user chooses Contextual Building:
    1.  **Read the Definition**: Read the linked definition file for the chosen extension type.
    2.  **Follow the Process**: Strictly follow the "Process" section from that file.
    3.  **Create/Modify**: Use your file creation tools to save the result.
    *Note*: Ensure you identify the correct location (Global/Chezmoi vs Local/Project) as described in the definition file.

## Troubleshooting Paths

If the relative links above do not work (e.g., due to a non-standard deployment), look for the definitions in:
- `~/.claude/commands/claude/new/`
- `src/dot_claude/commands/claude/new/` (if working in the dotfiles repo)
