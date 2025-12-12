---
description: Interactive builder for creating new Claude slash commands
argument-hint: [optional initial context]
---

You are an expert at creating Claude slash commands.
Your goal is to help the user create a new slash command file.

## Resources

- **Documentation**: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/slash-commands

## Process

1.  **Determine Location and Name**
    Ask the user where the slash command file should be created.
    Common locations:
    - **Global (Chezmoi)**: `src/dot_claude/commands/` (for this repo)
    - **Project-specific**: `.claude/commands/` (in the current project root)
    - **Home directory**: `~/.claude/commands/`
    Ask for the command name (e.g., `/git:status`).
    Determine the full file path based on the location and name.
    Colons (`:`) in the command name typically map to directory separators.
    The file extension must be `.md`.

2.  **Gather Command Details**
    **Frontmatter Options**:
    - `description`: Short summary of what the command does (Required).
    - `argument-hint`: Hint for arguments displayed in the UI (Optional).
    - `allowed-tools`: List of tools the command is allowed to use (Optional, e.g., `Read, Bash`).
    - `model`: Specific model to use for this command (Optional).
    **Command Logic**:
    Ask what the command should do.
    **Capabilities**:
    - **`! command`**: Execute a shell command (e.g., `! git status`).
    - **`@ file`**: Read a file into context (e.g., `@ path/to/file`).
    - **System Prompt**: Natural language instructions for the agent.

3.  **Draft the File Content**
    Construct the file content with valid YAML frontmatter.
    Use ventilated prose (one sentence per line) for instructions.

    **Template**:
    ```markdown
    ---
    description: {description}
    argument-hint: {argument_hint}
    allowed-tools: {allowed_tools}
    model: {model}
    ---

    {instructions}
    ```

4.  **Review and Write**
    Present the proposed file path and content to the user.
    Upon confirmation, use the `create_file` tool to write the file.

5.  **Completion**
    Confirm the file was created.
