# Agent context for dotfiles repository

## Git context

This repository uses git worktrees.
You may be operating in a worktree on a feature branch, not the main checkout.
**Always run `git status` and `git worktree list` at the start of a session** to confirm which branch and worktree you are in before making any changes.
Never assume you are on `main` or in the primary checkout directory.

## Repository structure

- `src/` - Chezmoi templates and deployment configuration (the source of truth).
- `config/` - Build configuration and profile management.
- `.chezmoidata/` - Modular configuration data (TOML).
- `src/chezmoi/dot_local/share/ai/` - AI tool plugin registry and marketplace.

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

- **Externals (`.chezmoiexternals/`)**: MUST be used for all downloads (binaries, archives).
  - Define versions/checksums in `.chezmoidata/`.
  - Never use custom curl/wget scripts for installation.
- **Shared scripts**: Use `src/scripts/` for reusable shell libraries.
  - Source with `${CHEZMOI_SOURCE_DIR:?}/scripts/lib.sh`.

## Configuration patterns

- **Data**: All configuration data lives in `.chezmoidata/` (e.g., `src/.chezmoidata/git.toml`).
- **Templates**: Use `{{ .chezmoi.sourceDir }}` to reference source files if needed, but prefer `{{ .chezmoi.destDir }}` for target paths.
- **Hyphens**: Access keys with hyphens using `index`: `{{- with (index .zsh "oh-my-zsh") }}`.

## Troubleshooting Package Installations
When resolving package installation failures (e.g. `npm`, `pnpm`, `bun`, `uv`), check if the failure is due to the minimum release age configuration (e.g. `min-release-age`, `minimumReleaseAge`, `exclude-newer`). If so, the package might be too new and you should use an older version.
