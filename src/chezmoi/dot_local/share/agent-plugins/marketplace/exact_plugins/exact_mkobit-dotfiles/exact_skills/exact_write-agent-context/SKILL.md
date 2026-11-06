---
name: write-agent-context
description: Enforces minimal, progressively-disclosed context in agent configuration files like AGENTS.md, CLAUDE.md, GEMINI.md, SKILL.md, and *.mdc to improve task success rates and reduce inference costs. Use when writing or modifying agent context files or skills.
metadata:
  purpose: "Provides context regarding the research at https://arxiv.org/abs/2602.11988 and https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models"
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
The same restraint applies to skills (`SKILL.md`), not just `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`.

Split long context into a tree of files loaded on demand, and reference sub-files instead of inlining everything into one dense file.
Prefer brief, judgment-guided steering over rigid blanket rules for nuanced matters; reserve absolute rules for genuinely critical or safety-relevant invariants.
