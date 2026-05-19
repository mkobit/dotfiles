# Mise tool version manager

## Installation

- **Mechanism**: Installed via `.chezmoiexternals/` directly from GitHub releases.
- **Location**: `{{ .chezmoi.destDir }}/.local/bin/mise`.

## Configuration

- **Global tools**: Defined in `src/chezmoi/.chezmoidata/mise.toml` under `[mise.global_tools]`.
- **Settings**: Also in `src/chezmoi/.chezmoidata/mise.toml` under `[mise.settings]`.
- **Shell**: Automatically hooked into `.zshrc` / `.bashrc`.

## Lockfile

`mise.lock` in this directory is the global lockfile managed by chezmoi.
It pins checksums for all global tools across all platforms.
Locking is **enforced during deployment** via `MISE_LOCKED=1` in the `run_after_onchange_06_trust-install-global-mise-tools.sh.tmpl` script.
However, the deployed `config.toml` defaults to `locked = false` to ensure that local projects are not forced to use lockfiles by default.

### Updating tools and relocking

Follow these steps exactly when updating any mise-managed tool version.
Do not substitute alternative commands — especially in Jules, where `mise lock` destroys the shell session permanently and irrevocably.

1. Update the version in `src/chezmoi/.chezmoidata/bin/mise.toml` under `[mise.global_tools.<tool>]`.
2. Apply the config to the home directory:
   ```
   chezmoi apply ~/.config/mise/config.toml
   ```
3. Regenerate the lockfile:
   ```
   MISE_LOCKED=0 mise -C ~ lock --global
   ```
   The `-C ~` flag is required — running from the dotfiles repo root causes global-only tools (e.g. `uv`) to be excluded because the local `.mise.toml` claims them.
4. Copy the lockfile back to the chezmoi source:
   ```
   chezmoi add ~/.config/mise/mise.lock
   ```
