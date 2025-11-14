---
name: claude:generate-hook
description: Interactively generate a Claude hook configuration.
---

# Claude Hook Generator

This command guides an agent through creating a valid Claude hook configuration by conversing with a user.

## Instructions

1.  **Understand the Goal**: Start by asking the user what they want to achieve. For example: "What kind of automation or check would you like to set up?"

2.  **Gather Hook Details**: Based on the user's goal, guide them to provide the necessary details for the hook. You must get the following information:
    *   **Event Type**: Ask the user to choose a specific event that will trigger the hook. You can suggest common options like `PreToolUse` (before a tool runs) or `PostToolUse` (after a tool runs).
    *   **Matcher**: Determine which tool(s) the hook should apply to.
        *   Prompt the user with examples of built-in tools (`Bash`, `Edit`, `Write`, `Read`).
        *   Explain the different matcher formats: a single tool (`Bash`), a pipe-separated list (`Edit|Write`), or a wildcard (`*`).
        *   Ask if they need more advanced matchers, like those for specific `bash` commands or tool arguments.
    *   **Command**: Get the exact shell command that the hook will execute.

3.  **Determine the Output Destination**: Ask the user where they want to save the generated hook configuration. Present them with the following options:
    *   **User Settings**: Merge into the global `~/.claude/settings.json`.
    *   **Project Settings**: Merge into a project-specific `.claude/settings.local.json`.
    *   **New File**: Save to a new file in the current directory.

4.  **Generate and Present the Hook**:
    *   Execute the `generate-claude-hook` CLI tool with the gathered parameters.
    *   Display the resulting JSON to the user for their review and confirmation.

5.  **Provide the Final Command**: Based on the user's choice of destination, provide the correct, copy-pasteable command to save the hook.

    *   **For Merging into an Existing File:**
        ```bash
        # Make a backup first!
        cp <FILE_PATH> <FILE_PATH>.bak

        # Generate and merge the hook
        generate-claude-hook --event <EVENT> --matcher "<MATCHER>" --command "<COMMAND>" | \\
          jq -s '.[0] * .[1]' <FILE_PATH> - > <FILE_PATH>.tmp && \\
          mv <FILE_PATH>.tmp <FILE_PATH>
        ```
        *(Replace `<FILE_PATH>` with the user's chosen file, e.g., `~/.claude/settings.json`)*

    *   **For Saving to a New File:**
        ```bash
        generate-claude-hook --event <EVENT> --matcher "<MATCHER>" --command "<COMMAND>" > new_hook.json
        ```
