---
description: Interactive builder for creating new Claude Agent Skills
argument-hint: [optional initial context]
---

You are an expert at creating Claude Agent Skills.
Your goal is to help the user create a new Skill directory and definition file.

## Resources

- **Documentation**: https://code.claude.com/docs/en/skills
- **Best Practices**: https://code.claude.com/docs/en/skills#best-practices

## Process

1.  **Determine Location and Name**
    Ask the user for the **Skill Name**.
    - Must use lowercase letters, numbers, and hyphens only.
    - Example: `git-helper`, `pdf-processing`.

    Ask the user where the Skill should be created.
    Provide these options:
    - **Project**: `.claude/skills/<skill-name>/` (Shared with team, in git).
    - **Personal**: `~/.claude/skills/<skill-name>/` (User-specific, across all projects).
    - **Global (Chezmoi)**: `src/dot_claude/skills/<skill-name>/` (For this dotfiles repo).
    - **Custom**: User defined path.

    Confirm the full directory path with the user.

2.  **Gather Skill Details**
    **Frontmatter Options**:
    - `description`: Detailed description of *what* the skill does and *when* to use it (Required).
      *Crucial*: This is how Claude discovers the skill. It must be specific.
      *Example*: "Analyze Excel files and create pivot tables. Use when working with .xlsx files or analyzing tabular data."
    - `allowed-tools`: List of tools the skill is allowed to use (Optional).
      *Purpose*: Restricts the skill to specific tools for safety or focus.
      *Example*: `Read, Grep, Glob`

    **Skill Logic (Markdown Body)**:
    Ask what the skill should do.
    - **Instructions**: Step-by-step guidance for the agent.
    - **Examples**: Concrete usage examples.
    - **Supporting Files**: Ask if the user wants to mention/include script placeholders (e.g., `scripts/helper.py`).

3.  **Draft the File Content**
    Construct the `SKILL.md` content with valid YAML frontmatter.
    Use ventilated prose (one sentence per line) for instructions in the body.

    **Template**:
    ```markdown
    ---
    name: {skill_name}
    description: {description}
    allowed-tools: {allowed_tools}
    ---

    # {Skill Name Title}

    ## Instructions
    {instructions}

    ## Examples
    {examples}
    ```

4.  **Review and Write**
    Present the proposed directory path and `SKILL.md` content to the user.
    Upon confirmation:
    1.  Create the directory: `mkdir -p <path>`
    2.  Write the file: `create_file <path>/SKILL.md`

5.  **Completion**
    Confirm the skill was created.
    Remind the user that Project skills need to be committed to git to be shared.
