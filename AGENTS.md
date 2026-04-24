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
  - Define versions/checksums in `.chezmoidata/bin/`.
  - Never use custom curl/wget scripts for installation.
- **Shared scripts**: Use `src/scripts/` for reusable shell libraries.
  - Source with `${CHEZMOI_SOURCE_DIR:?}/scripts/lib.sh`.

## Data schema: `.chezmoidata/bin/` (static binaries)

Each tool in `bin/` describes a GitHub release download managed by the `external/release` named template.

Required keys:
- `version` — release version (e.g. `"0.26.1"`)
- `installation_method` — `"chezmoi_external"` (flat string); work config can override
- `repo` — GitHub `owner/name` (e.g. `"sharkdp/bat"`)
- `external_type` — `"archive-file"` (single file from archive) or `"file"` (standalone binary)
- `executable` — must be `true` for binaries
- `checksum_type` — `"sha256"` or `"none"`
- `tag_format` — format string for the git tag (e.g. `"v{version}"`)
- `filename_format` — format string for the release asset (e.g. `"bat-v{version}-{target}.tar.gz"`)
- `url_format` — download URL template with `{base}`, `{repo}`, `{tag}`, `{filename}` tokens
- `platforms` — map of `os_arch` to target triple (e.g. `darwin_arm64 = "aarch64-apple-darwin"`)

Optional keys:
- `path_format` — path inside archive to extract (required for `archive-file`)
- `checksums` — map of `os_arch` to SHA-256 hash (required when `checksum_type = "sha256"`)
- `fallback_url_format` — secondary download URL emitted as chezmoi `urls` field
- `strip_components` — tar strip depth
- `include` — list of globs to extract from archive
- `readonly` — deploy as read-only

The `{base}` token resolves to `github_releases.base_url` from data (default `https://github.com`).
Work config can inject an Artifactory mirror URL to override this on Stripe machines.

## Data schema: `.chezmoidata/packages/` (package-managed tools)

Each tool in `packages/` describes something installed via a system package manager (brew, snap, apt).
Templates iterate `.packages` to generate a Brewfile (darwin) or snap install script (linux).

Required keys:
- `installation_method` — flat string (`"homebrew"`) or per-OS map (`darwin = "homebrew"`, `linux = "snap"`)

Package metadata (nested under `package.<manager>`):
- `package.homebrew.name` — brew formula/cask name
- `package.homebrew.type` — `"formula"` or `"cask"` (MECE, no booleans)
- `package.snap.name` — snap package name
- `package.snap.confinement` — `"strict"` or `"classic"` (MECE, no booleans)

Only tools that actually use package managers belong here.
Tools using `chezmoi_external` should NOT have `package.*` metadata — work config can inject overrides if needed.

## Configuration patterns

- **Data**: All configuration data lives in `.chezmoidata/` (e.g., `src/.chezmoidata/git.toml`).
- **Templates**: Use `{{ .chezmoi.sourceDir }}` to reference source files if needed, but prefer `{{ .chezmoi.destDir }}` for target paths.
- **Hyphens**: Access keys with hyphens using `index`: `{{- with (index .zsh "oh-my-zsh") }}`.

## Data merge hierarchy

`--config [data.*]` beats `.chezmoidata/` unconditionally; `.chezmoidata/` files deep-merge (sibling keys coexist, last alpha file wins on conflicts).
All tool entries in `.chezmoidata/` must declare an explicit `installation_method` key.
Use `dig` for safe access when the key may be absent or may be a per-OS map.
Work-imposed locks in the generated config always win — personal cannot override them.

## Troubleshooting Package Installations
When resolving package installation failures (e.g. `npm`, `pnpm`, `bun`, `uv`), check if the failure is due to the minimum release age configuration (e.g. `min-release-age`, `minimumReleaseAge`, `exclude-newer`). If so, the package might be too new and you should use an older version.

## AI Shell Limitations
Do not execute `mise lock` in Jules, as it will permanently and irrevocably destroy the shell session.
