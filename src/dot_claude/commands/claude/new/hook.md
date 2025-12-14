---
description: Interactive builder for creating new Claude Code Hooks
argument-hint: [optional initial context]
---

You are an expert at creating Claude Code Hooks.
Your goal is to help the user create a valid hook configuration and any necessary scripts.

## Resources

- **Documentation**: https://code.claude.com/docs/en/hooks
- **Reference**: https://code.claude.com/docs/en/hooks-guide

## Process

1.  **Context and Diagnostics**
    First, determine the user's environment to suggest the best location.
    Run the following diagnostic checks (silently or with minimal output):
    - **Chezmoi Source**: Check if `src/.chezmoidata/claude_code.toml` exists.
    - **Project**: Check if `.claude/` directory exists.
    - **User Home**: Check if `~/.claude/settings.json` exists.

    Ask the user where they want to configure this hook:
    - **Global (Chezmoi)**: Create a JSON fragment in `src/dot_claude/hooks/` for later merging. (Best if in dotfiles repo).
    - **Project**: Append to `.claude/settings.json` (or create a fragment).
    - **User**: Append to `~/.claude/settings.json`.

2.  **Gather Hook Details**
    **Event**:
    Ask which event to hook into. Common options:
    - `PreToolUse`: Run before a tool is used (can block/modify).
    - `PostToolUse`: Run after a tool completes (logging, formatting).
    - `SessionStart`: Run when a session begins.
    - `UserPromptSubmit`: Run when user submits input.

    **Matcher**:
    Ask for the tool matcher (required for Tool events).
    - `*`: Matches all tools.
    - `Bash`, `Edit`, `Write`, `Glob`, `Grep`: Specific tools.
    - Regex is supported (e.g., `Edit|Write`).

    **Command Type**:
    Ask if this is a simple **Inline Command** or a **Script**.

    *Option A: Inline Command*
    - Ask for the command string.
    - Example: `echo "Starting session" >> /tmp/log.txt`

    *Option B: Script (Recommended for complex logic)*
    - Ask for the script name (e.g., `format-code.sh`, `validate.py`).
    - Ask for the language (Bash, Python, etc.).
    - Ask for the script logic/content.
    - **Important**: Explain that `$CLAUDE_PROJECT_DIR` is available in the hook environment.
    - **Create the script**:
        - Determine script path based on context (e.g., `src/dot_claude/hooks/` or `.claude/hooks/`).
        - Create the file.
        - Make it executable: `chmod +x <script_path>`.

3.  **Generate Configuration**
    Construct the JSON configuration object.

    **Structure**:
    ```json
    {
      "hooks": {
        "<EventName>": [
          {
            "matcher": "<Matcher>",
            "hooks": [
              {
                "type": "command",
                "command": "<Command or Script Path>"
              }
            ]
          }
        ]
      }
    }
    ```

    *Note on Script Paths*:
    - If using a script in the project, use absolute paths or `$CLAUDE_PROJECT_DIR/.claude/hooks/myscript.sh`.
    - If using a global script, ensure the path is resolved correctly (e.g., `~/.claude/hooks/myscript.sh`).

4.  **Finalize**
    **If Chezmoi**:
    - Save the JSON object to a file, e.g., `src/dot_claude/hooks/<hook-name>.json`.
    - Tell the user they can now combine this with their main configuration templates.

    **If Project/User**:
    - Offer to apply the changes to `settings.json` directly (using `jq` or Python to merge).
    - Or print the JSON block for them to copy-paste.

    **Verification**:
    - Remind the user to run `/hooks` to verify the configuration is active.
