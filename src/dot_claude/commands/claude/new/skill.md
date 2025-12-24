---
description: Interactive builder for creating new Claude Agent Skills
argument-hint: [optional initial context]
---

You are an expert at creating Claude Agent Skills.
Your goal is to help the user create a new Skill directory and definition file.

## Resources

- **Documentation**: https://code.claude.com/docs/en/skills
- **Best practices**: https://code.claude.com/docs/en/skills#best-practices

## Process

1.  **Determine location and name**
    Ask the user for the **skill name**.
    - Must use lowercase letters, numbers, and hyphens only.
    - Example: `git-helper`, `pdf-processing`.

    **Check the current environment**:
    - Inspect the current directory for chezmoi markers (e.g., `.chezmoiroot`, `.chezmoi.toml.tmpl`, or a `src/dot_claude` structure).

    Ask the user where the skill should be created.
    Provide these options:
    - **Project**: `.claude/skills/<skill-name>/` (shared with team, in git).
    - **Personal**: `~/.claude/skills/<skill-name>/` (user-specific, across all projects).
    - **Global (chezmoi)**: `src/dot_claude/skills/<skill-name>/` (offer this ONLY if in a chezmoi source repo).
    - **Custom**: User defined path.

    Confirm the full directory path with the user.

2.  **Gather skill details**
    **Frontmatter options**:
    - `description`: Detailed description of *what* the skill does and *when* to use it (required).
      *Crucial*: This is how Claude discovers the skill.
      Skills are model-invoked, so the description must be specific.
      *Example*: "Analyze Excel files and create pivot tables. Use when working with .xlsx files or analyzing tabular data."
    - `allowed-tools`: List of tools the skill is allowed to use (optional).
      *Purpose*: Restricts the skill to specific tools for safety or focus.
      *Example*: `Read, Grep, Glob`
      *MCP example*: `mcp-server-name:tool-name` (e.g., `github:get_issue`)

    **Skill logic (markdown body)**:
    Ask what the skill should do.
    - **Instructions**: Step-by-step guidance for the agent.
    - **Examples**: Concrete usage examples.
    - **Supporting files**: Ask if the user wants to include scripts or reference files (e.g., `scripts/helper.py`).

3.  **Draft the file content**
    Construct the `SKILL.md` content with valid YAML frontmatter.
    Use ventilated prose (one sentence per line) for instructions in the body.

    **Template**:
    ```markdown
    ---
    name: {skill_name}
    description: {description}
    allowed-tools: {allowed_tools}
    ---

    # {Skill name title}

    ## Instructions
    {instructions}

    ## Examples
    {examples}
    ```

4.  **Review and write**
    Present the proposed directory path and `SKILL.md` content to the user.
    Also present any supporting files if discussed.
    Upon confirmation:
    1.  Create the directory: `mkdir -p <path>`
    2.  Write the file(s): `create_file <path>/SKILL.md` (and any others)

5.  **Completion**
    Confirm the skill was created.
    Remind the user that project skills need to be committed to git to be shared.
