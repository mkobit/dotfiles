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
  - Use the directory form `.chezmoiexternals/<name>.toml.tmpl` — flat `.chezmoiexternals.toml.tmpl` files are NOT recognized by chezmoi.
  - Define versions/checksums in `.chezmoidata/bin/`.
  - Never use custom curl/wget scripts for installation.
- **Shared scripts**: Source shared shell libraries from `.chezmoitemplates/` via `{{ .chezmoi.sourceDir }}`.

## Data schema: `.chezmoidata/bin/` (static binaries)

Each tool lives in `.chezmoidata/bin/<name>.toml` under `[bin.<name>]`.
The **BOM** (Bill of Materials) in `.chezmoi.toml.tmpl` controls which tools are downloaded on each machine:

```toml
[data.local.bin.<name>]
installation_method = "github_releases"  # or "direct_release", "homebrew", "apt", "none"
```

The template `dot_local/bin/.chezmoiexternals/bins.toml.tmpl` iterates `.bin`, reads each tool's `installation_method` from `local.bin`, and dispatches to the appropriate entry template.

### `github_releases` sub-table

For tools published as GitHub release assets.

Required keys:
- `repo` — GitHub `owner/name`
- `external_type` — `"archive-file"`, `"archive"`, or `"file"`
- `checksum_type` — `"sha256"`
- `tag_format` — git tag format string (e.g. `"v{version}"`)
- `filename_format` — release asset name (e.g. `"bat-v{version}-{target}.tar.gz"`)
- `url_format` — URL with `{base}`, `{repo}`, `{tag}`, `{filename}` tokens
- `platforms` — map of `os_arch` to target triple

Optional:
- `path_format` — path inside archive to extract (required for `archive-file`)
- `checksums` — map of `os_arch` to SHA-256 hash
- `strip_components` — tar strip depth (camelCase `stripComponents` in rendered TOML)
- `executable` — `true` for standalone binaries

The `{base}` token resolves to `github_releases.base_url` from data (default `https://github.com`).
Work config can inject an Artifactory mirror URL to override this.

Tools with `external_type = "archive"` (multi-file tree extraction, e.g. nvim) are NOT handled by `bins.toml.tmpl` — they require their own file in a parent `.chezmoiexternals/` directory.

### `direct_release` sub-table

For vendor-hosted static binaries not published on GitHub (e.g. chafa on hpjansson.org).
Same keys as `github_releases` except `repo`, `tag_format`, and `{base}`/`{repo}`/`{tag}` tokens are omitted — `url_format` is a full URL pattern using only `{filename}`.

### Package manager sub-tables

Tools may also declare `homebrew`, `apt` sub-tables for package-manager fallback on platforms without a static binary.
`dot_Brewfile.tmpl` and install scripts read `installation_method` from the BOM to decide which tools to include.

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

## Zellij layout system

Personal layouts live in `src/chezmoi/dot_config/zellij/layouts/`.
Each environment (overlay, personal machine, remote) owns its own layout files directly — no cross-repo injection for layouts.
Config scalar defaults (`scrollback_lines_to_serialize`, `show_startup_tips`) live in `.chezmoidata/zellij.toml`; overlay environments may override via `[data.zellij.config]`.
Docs: https://zellij.dev/documentation/creating-a-layout
