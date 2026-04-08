# Decision: chezmoi-native AI skill deployment (2026-04-06)

Supersedes: `docs/DESIGN-upstream-skills.md` § "What's next — UV-powered upstream skill assembly"

## Context

Over the past several months we built a UV-based pipeline for deploying upstream AI skills and extensions across Claude Code, Cursor, and Gemini CLI.
The pipeline grew to include:

- Module extension repo rules (`extensions.bzl`) fetching and scanning upstream archives at build time
- IR models (`SkillIR`, `AgentIR`) and transform scripts producing tool-specific Markdown
- Packaging macros (`claude_skill_group`, `gemini_skill_group`, `cursor_skill_group`, `gemini_extension_group`, …) producing tagged tars
- A tag taxonomy (`tool:*`, `claude:commands`, `gemini:extension`, …) and `uv cquery` queries in chezmoi templates to discover deployable tars

## What we learned

**The pipeline fought each tool's native install model.**
The final example: Gemini CLI requires a `.gemini-extension-install.json` metadata file in every installed extension directory.
`gemini extension install` writes it; dropping a tar archive does not.
This was not a one-off — every tool has install-time conventions that evolve independently and are not reflected in the archive format.

**Complexity outran the problem.**
The actual need is: fetch pinned versions of upstream repos and place files in the right locations.
UV is strong at hermetic fetching.
It is not the right layer for "call the tool's install CLI with the right arguments."

**The IR transform pipeline has genuine value — but not in dotfiles.**
The idea of a common IR that can emit skill formats for any tool (Claude, Gemini, Cursor, Codex) is sound.
It belongs in a dedicated project, informed by this work and gaps in tools like rulesync, not embedded in a personal dotfiles repo.

## Decision

1. **Remove UV from the dotfiles repo entirely.**
   `tools/agentskills/`, `tools/chezmoi/`, `tools/lint/`, `tools/python/`, and the `MODULE.uv` build graph are deleted.
   The repo becomes chezmoi-only.

2. **AI skills and extensions are managed via chezmoi primitives.**
   - Version pins live in `.chezmoidata/` (TOML).
   - Versioned archives are fetched via `.chezmoiexternals/` entries with `sha256` and `exact = true`.
   - Install-time logic (calling `gemini extension install`, writing metadata, etc.) lives in `run_onchange_` scripts.

3. **Scripts that need real logic are typed, not raw shell.**
   Use Python via `uv` (with lock file) or TypeScript via `bun` (with lock file) for any script that parses JSON, calls multiple CLIs, or has conditional paths.
   Reserve shell for trivial one-liners.

4. **The IR transform pipeline is a future standalone project.**
   It will be built separately, tested independently, and consumed here as a binary via `.chezmoiexternals/` if and when it matures.

## New deployment shape (per skill source)

```
.chezmoidata/ai-skills.toml          ← version pins, sha256, strip_prefix
.chezmoiexternals/claude-skills.toml.tmpl   ← archive entries for ~/.claude/skills/
.chezmoiexternals/gemini-skills.toml.tmpl   ← archive entries for ~/.gemini/skills/
.chezmoiexternals/cursor-skills.toml.tmpl   ← archive entries for ~/.cursor/rules/
run_onchange_gemini-extensions.py.tmpl      ← calls `gemini extension install` per extension
```

## What we keep

- The Gemini extension format research (deploy to `~/.gemini/extensions/<name>/`, `.gemini-extension-install.json` required).
- The tag taxonomy design — useful documentation if the standalone IR project materialises.
- The upstream repo + version pin inventory in `MODULE.uv` — migrates to `.chezmoidata/`.
