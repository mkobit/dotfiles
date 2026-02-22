# Agent context for dotfiles repository

## Repository structure

- `src/` - Chezmoi templates and deployment configuration (the source of truth).
- `tools/` - Bazel rules for validation, testing, and automation.
- `config/` - Build configuration and profile management.
- `.chezmoidata/` - Modular configuration data (TOML).

## Critical Path Rules

1. **ALWAYS use `{{ .chezmoi.destDir }}` for ALL paths**
   - ✅ `export PATH="{{ .chezmoi.destDir }}/.local/bin:${PATH}"`
   - ❌ `export PATH="$HOME/.local/bin:${PATH}"`

2. **NEVER use `$HOME` or `{{ .chezmoi.homeDir }}`** in templates.
   - We install to a target directory, which may not be the user's home during testing/CI.

## Managed Environment Constraints

- **`modify_` scripts** are the ONLY safe way to customize externally managed files (like `.gitconfig`, `.zshrc` in corporate environments).
- **Never replace** system binaries or externally-installed tools.
- **Header Pattern** for `modify_` scripts:
  ```bash
  # /path/to/script.tmpl:BEGIN:section:12345678 - WARNING: managed by chezmoi, do not edit
  # Applied: {{ now | date "2006-01-02T15:04:05Z07:00" }}
  [configuration]
  # /path/to/script.tmpl:END:section:12345678
  ```

## Chezmoi Externals & Scripts

- **Externals (`.chezmoiexternals/`)**: MUST be used for all downloads (binaries, archives).
  - Define versions/checksums in `.chezmoidata/`.
  - Never use custom curl/wget scripts for installation.
- **Shared Scripts**: Use `src/scripts/` for reusable shell libraries.
  - Source with `${CHEZMOI_SOURCE_DIR:?}/scripts/lib.sh`.

## Configuration Patterns

- **Data**: All configuration data lives in `.chezmoidata/` (e.g., `src/.chezmoidata/git.toml`).
- **Templates**: Use `{{ .chezmoi.sourceDir }}` to reference source files if needed, but prefer `{{ .chezmoi.destDir }}` for target paths.
- **Hyphens**: Access keys with hyphens using `index`: `{{- with (index .zsh "oh-my-zsh") }}`.
