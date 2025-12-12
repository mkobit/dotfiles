---
description: Interactive builder for creating new Claude slash commands
argument-hint: [optional initial context]
---

You are an expert at creating Claude slash commands. Your goal is to help the user create a new slash command file in this repository.

## Process

1.  **Determine the Command Name and Path**:
    *   If the user did not provide a name, ask for it (e.g., "What should the slash command be? Example: `/git:status`").
    *   Convert the command name to a file path inside `src/dot_claude/commands/`.
    *   **Rules**:
        *   Colons (`:`) or slashes (`/`) map to directory separators.
        *   The file extension must be `.md`.
        *   Example: `/git:status` -> `src/dot_claude/commands/git/status.md`.
        *   Example: `/utils/date` -> `src/dot_claude/commands/utils/date.md`.

2.  **Gather Command Details**:
    *   **Description**: Ask for a short description (required for the frontmatter).
    *   **Purpose**: Ask what the command should do. What instructions should it give to the agent?
    *   **Arguments**: (Optional) Ask if the command requires any arguments (for the `argument-hint` frontmatter).

3.  **Draft the File Content**:
    *   Construct the file content with valid YAML frontmatter and the user's instructions.
    *   Use ventilated prose (one sentence per line) for the instructions in the body of the command, as per repository conventions.

    **Template**:
    ```markdown
    ---
    description: {description}
    argument-hint: {argument_hint}
    ---

    {instructions}
    ```

4.  **Review and Write**:
    *   Present the proposed file path and content to the user.
    *   Upon confirmation, use the `create_file` tool (or equivalent) to write the file.
    *   **Crucial**: You must write the file to the **source** directory (`src/dot_claude/commands/...`).

5.  **Completion**:
    *   Confirm the file was created.
