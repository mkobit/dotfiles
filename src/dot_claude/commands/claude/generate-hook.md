---
name: claude:generate-hook
description: Interactively generate a Claude hook configuration.
---

# Claude Hook Generator

This command guides you through the process of creating a valid Claude hook configuration.

## Instructions

1.  **Engage the User**: Start a conversation to determine the necessary details for the hook. You must get the following information:
    *   **Event Type**: The specific event that will trigger the hook (e.g., `PreToolUse`, `PostToolUse`).
    *   **Matcher**: The tool(s) the hook should apply to (e.g., `Bash`, `Edit|Write`, `*`).
    *   **Command**: The shell command that the hook will execute.

2.  **Generate the Hook JSON**: Once you have all the required information, use the `generate-claude-hook` CLI tool to create the JSON configuration. The command will look like this:

    ```bash
    generate-claude-hook --event <EVENT_TYPE> --matcher "<MATCHER>" --command "<COMMAND>"
    ```

3.  **Present the JSON**: Display the generated JSON to the user for their review.

4.  **Provide Merging Instructions**: Provide the user with the following `jq` command to merge the generated JSON into their settings file. You must explain what the command does and how to adapt it.

    **Example `jq` command:**

    ```bash
    # Make a backup first!
    cp ~/.claude/settings.json ~/.claude/settings.json.bak

    # Merge the new hook into the settings file
    generate-claude-hook --event <EVENT_TYPE> --matcher "<MATCHER>" --command "<COMMAND>" | \\
      jq -s '.[0] * .[1]' ~/.claude/settings.json - > ~/.claude/settings.json.tmp && \\
      mv ~/.claude/settings.json.tmp ~/.claude/settings.json
    ```

    **Explanation to provide:**
    *   "This command pipeline first generates the hook JSON."
    *   "It then uses `jq` with the `-s` (slurp) flag to read both the existing `settings.json` and the new hook JSON into a single array."
    *   "The `'.[0] * .[1]` filter performs a deep merge of the two JSON objects."
    *   "The result is written to a temporary file, and if successful, it replaces the original `settings.json`. This is a safe way to update the file."
    *   "You can replace `~/.claude/settings.json` with the path to any other settings file you wish to modify, such as a project-specific `.claude/settings.local.json`."
