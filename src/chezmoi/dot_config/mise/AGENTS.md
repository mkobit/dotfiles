# Mise tool version manager

## Installation

- **Mechanism**: Installed via `.chezmoiexternals/` directly from GitHub releases.
- **Location**: `{{ .chezmoi.destDir }}/.local/bin/mise`.

## Configuration

- **Global tools catalog** (versions, postinstall hooks): `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.global_tools.<tool>]`.
- **Global tools BOM** (per-machine opt-in via `installation_method`): `src/chezmoi/.chezmoi.toml.tmpl` under `[data.local.mise.global_tools.<tool>]`.
  Catalog entries are inert until a BOM entry opts in (`installation_method = "mise"`).
  Mirrors the `.local.bin.*` convention.
- **Settings**: `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.settings]`.
- **Shell**: Automatically hooked into `.zshrc` / `.bashrc`.

## Lockfile

`~/.config/mise/mise.lock` is regenerated locally by `mise lock` and is **not tracked in this repo** — `.chezmoiignore` blocks it (`**/.config/mise/mise.lock`) so per-machine drift doesn't pollute the chezmoi diff.
Locking is **enforced during deployment** via `MISE_LOCKED=1` in the `run_after_onchange_06_trust-install-global-mise-tools.sh.tmpl` script, so whatever lockfile is locally present is honored at install time.
The deployed `config.toml` defaults to `locked = false` so local projects aren't forced to use lockfiles by default.

### Updating tools and relocking

Follow these steps exactly when updating any mise-managed tool version.
Do not substitute alternative commands — especially in Jules, where `mise lock` destroys the shell session permanently and irrevocably.

1. Update the version in `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.global_tools.<tool>]` (catalog).
   New tools also require a BOM entry in `src/chezmoi/.chezmoi.toml.tmpl` under `[data.local.mise.global_tools.<tool>]` with `installation_method = "mise"`, followed by `chezmoi init` to propagate.
2. Apply the config to the home directory:
   ```
   chezmoi apply ~/.config/mise/config.toml
   ```
3. Regenerate the lockfile:
   ```
   MISE_LOCKED=0 mise -C ~ lock --global
   ```
   The `-C ~` flag is required — running from the dotfiles repo root causes global-only tools (e.g. `uv`) to be excluded because the local `.mise.toml` claims them.
