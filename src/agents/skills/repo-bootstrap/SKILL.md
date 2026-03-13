---
name: repo-bootstrap
description: Scaffolds AI tool configuration into any directory with sensible defaults for Claude, Gemini, and Cursor based on repo type.
---

# Repo bootstrap

Scaffold AI tool configuration into a directory.
This skill generates settings files, context documents, and directory structures for Claude Code, Gemini CLI, and Cursor.

## Workflow

When invoked, follow these steps interactively.

### Step 1: Gather inputs

Ask the user two questions before generating any files.

**Which tools to configure:**
- Claude
- Gemini
- Cursor
- All (default)

**Repo type** (affects permissions and defaults):
- Python
- TypeScript
- Bazel
- Monorepo
- Generic (default)

### Step 2: Generate shared files

Always generate these files regardless of tool selection.

**`AGENTS.md`** — minimal repo context document:
```markdown
# Project name

Brief description of the project.

## Build

Commands to build, test, and lint the project.

## Architecture

Key directories and their purposes.
```

**`.gitignore` additions** — append these lines if not already present:
```
# AI tool local settings
.claude/settings.local.json
.claude/todos/
```

**`.agents/skills/`** — create the directory for portable skills.

### Step 3: Generate tool-specific files

Generate files only for the tools the user selected.

#### Claude

**`.claude/settings.json`** — permissions based on repo type:

Python:
```json
{
  "permissions": {
    "allow": [
      "Bash(python *)",
      "Bash(pip *)",
      "Bash(pytest *)",
      "Bash(ruff *)"
    ]
  }
}
```

TypeScript:
```json
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(bun *)",
      "Bash(tsc *)"
    ]
  }
}
```

Bazel:
```json
{
  "permissions": {
    "allow": [
      "Bash(bazel build:*)",
      "Bash(bazel test:*)",
      "Bash(bazel query:*)"
    ]
  }
}
```

Monorepo:
```json
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(make *)"
    ]
  }
}
```

Generic:
```json
{
  "permissions": {
    "allow": []
  }
}
```

**`.claude/CLAUDE.md`** — placeholder context file:
```markdown
# Project instructions

Add project-specific instructions for Claude here.
```

#### Gemini

**`.gemini/settings.json`** — tool controls:
```json
{
  "tools": {
    "allowed": true
  }
}
```

**`.gemini/GEMINI.md`** — placeholder context file using TOON format:
```markdown
Please also reference the following rules as needed. The list below is provided in TOON format, and `@` stands for the project root directory.

rules[0]:
```

#### Cursor

**`.cursor/rules/`** — create the directory for cursor rules.

### Step 4: Report

After generating files, print a summary listing every file created.
Note any files that were skipped because they already existed.
Do not overwrite existing files unless the user explicitly confirms.

## Important guidelines

Use the tool's native file writing capabilities to create files.
Do not use shell commands to write files.
Do not overwrite existing files without user confirmation.
Create parent directories as needed.
Keep generated content minimal following the write-agent-context principle: less context improves agent performance.
