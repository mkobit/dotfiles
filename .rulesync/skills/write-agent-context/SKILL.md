---
name: write-agent-context
description: Enforces minimal context in agent configuration files like AGENTS.md, CLAUDE.md, GEMINI.md, and *.mdc to improve task success rates and reduce inference costs. Use when writing or modifying agent context files.
targets: ["*"]
metadata:
  purpose: "Provides context regarding the research at https://arxiv.org/abs/2602.11988"
---

# Write agent context

A widespread practice in software development is to tailor coding agents to repositories using context files.
Recent research indicates that providing excessive repository context tends to reduce task success rates.
It also increases inference cost by over 20%.
Both LLM-generated and developer-provided context files encourage broader exploration, such as more thorough testing and file traversal.
While coding agents tend to respect their instructions, unnecessary requirements make tasks harder.

Therefore, human-written context files must describe only minimal requirements.
Do not include generic documentation, tutorials, or non-critical context.
Restrict these files to repository-specific constraints and critical architecture maps.
Ensure all documentation formats are written with one sentence per line to improve diff readability.
Documentation titles and headers must use sentence case.
