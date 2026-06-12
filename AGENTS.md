# Agent context for dotfiles repository

This is a **personal dotfiles repository** managed by mkobit.
It is a highly customized environment optimized for specific personal workflows.
AI agents must prioritize consistency with established architectural patterns, naming conventions, and local configuration styles.
Avoid imposing standard industry "best practices" if they conflict with the existing idiomatic choices made in this repository.

## Git context

This repository uses git worktrees.
You may be operating in a worktree on a feature branch, not the main checkout.
**Always run `git status` and `git worktree list` at the start of a session** to confirm which branch and worktree you are in before making any changes.
Never assume you are on `main` or in the primary checkout directory.

## Repository structure

- `src/chezmoi/` - Chezmoi templates and deployment configuration (the source of truth; `.chezmoiroot`).
- `src/chezmoi/.chezmoidata/` - Modular configuration data (TOML).
- `src/chezmoi/.chezmoidata/ai/skills.toml` - AI skill deployment catalog (pinned upstream skills installed via chezmoi externals).
- `src/ai/skills/` - Authored AI skills (canonical sources, deployed as copies).
- `src/python/` - Local Python tools (uv workspace).

## Critical path rules

1. **ALWAYS use `{{ .chezmoi.destDir }}` for ALL paths**
   - ✅ `export PATH="{{ .chezmoi.destDir }}/.local/bin:${PATH}"`
   - ❌ `export PATH="$HOME/.local/bin:${PATH}"`

2. **NEVER use `$HOME` or `{{ .chezmoi.homeDir }}`** in templates.
   - You must never use `$HOME`.
   - You must never use `{{ .chezmoi.homeDir }}` of your own accord.
   - You must always inject and template using `{{ .chezmoi.destDir }}`, `{{ .chezmoi.sourceDir }}`, `{{ .chezmoi.workingTree }}` (for the full source git directory), and other chezmoi variables.
   - The only exception is through explicit wording from user prompting.
   - If a user asks you to use them, you must provably come to the user with the reasons why before ever making an edit.
   - We install to a target directory, which may not be the user's home during testing/CI.

## Managed environment constraints

- **`modify_` scripts** are the ONLY safe way to customize externally managed files (like `.gitconfig`, `.zshrc` in corporate environments).
- **Never replace** system binaries or externally-installed tools.
- **Header pattern** for `modify_` scripts:
  ```bash
  # /path/to/script.tmpl:BEGIN:section:12345678 - WARNING: managed by chezmoi, do not edit
  # Applied: {{ now | date "2006-01-02T15:04:05Z07:00" }}
  [configuration]
  # /path/to/script.tmpl:END:section:12345678
  ```

## Chezmoi externals & scripts

All binary downloads go through chezmoi externals — never custom curl/wget scripts.
Use the `.chezmoiexternals/` **directory** form (flat `.chezmoiexternals.toml.tmpl` files are not recognized by chezmoi).
Versions, checksums, and download metadata live in `.chezmoidata/bin/`.
Shared shell libraries live in `.chezmoitemplates/` and are sourced via `{{ .chezmoi.sourceDir }}` at script render time.

## Binary tool catalog (BOM pattern)

Each binary tool has a catalog entry in `.chezmoidata/bin/` describing how to download it (URL pattern, platform map, checksums) for each supported source (GitHub releases, vendor hosting, package managers).
The **BOM** (Bill of Materials) in `.chezmoi.toml.tmpl` declares which tools are active on a given machine and by which method — catalog entries are inert until opted into via the BOM.
A dispatch template in `.chezmoiexternals/` reads the BOM and generates the appropriate chezmoi external entries.

When adding a tool: add a catalog entry, add a BOM entry, verify the correct source type is used (GitHub releases, direct vendor download, or package manager — don't conflate them).
When a tool extracts a full directory tree rather than a single binary, it needs its own `.chezmoiexternals/` entry rather than going through the shared dispatch template.

## Data and templates

All configuration data lives in `.chezmoidata/`.
Config values set in `.chezmoi.toml.tmpl` take precedence over `.chezmoidata/` for the same key path.
Use `dig` for safe key traversal — direct map access fails in strict mode when a key is absent.
Access hyphenated keys with `index` rather than dot notation.

## Overlay compatibility

This repo is designed to be used as a base that an overlay repo rsyncs on top of.
The overlay wins all file collisions; individual data values are overridden via `[data.*]` entries in the overlay's `.chezmoi.toml.tmpl` or additional `.chezmoidata/` files.

When adding features, keep them overlay-friendly:

- Put all defaults in `.chezmoidata/` so overlays have a stable override target.
- Use generic key names — describe the concept, not the environment.
- Use `dig` for any key an overlay might omit so absence is a no-op, not a template error.
- Loop over maps (`range $k, $v := .feature.items`) for injectable content so overlays extend by adding keys, not editing base files.
- Keep all source files and data environment-neutral; machine-specific values belong in the overlay.

## Troubleshooting package installations

If an install fails due to a package being too new, check for a minimum release age setting in the relevant config (mise, uv, etc.) and use an older version that satisfies it.

## Zellij layout system

Each environment owns its layout files directly — no cross-repo injection.
Scalar config defaults live in `.chezmoidata/zellij.toml`; overlay environments override via `[data.zellij.*]`.
Docs: https://zellij.dev/documentation/creating-a-layout
