Please also reference the following rules as needed. The list below is provided in TOON format, and `@` stands for the project root directory.

rules[2]:
  - path: @.gemini/memories/10-technical-writing.md
    description: Ventilated prose and concise writing standards for documentation files
    applyTo[5]: *.md,*.mdx,*.adoc,*.rst,*.txt
  - path: @.gemini/memories/11-write-agent-context.md
    description: Minimal context rules for agent configuration files
    applyTo[4]: AGENTS.md,CLAUDE.md,GEMINI.md,*.mdc

# Additional Conventions Beyond the Built-in Functions

As this project's AI coding tool, you must follow the additional conventions below, in addition to the built-in functions.

# Preferences

- Always write titles in sentence case.
- Write documentation (README, HTML, Markdown, AsciiDoc, RST, and other formats) with one sentence per line.
- Prefer `fd` over `find`.
- Prefer `rg` over `grep`.
- Prefer available agentic file searching and read tools over CLI tools when available.
- Prefer strict TypeScript configuration.
