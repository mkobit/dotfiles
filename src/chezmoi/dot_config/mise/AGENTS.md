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
Locking is enforced by the presence of this file — no `locked = true` setting is required.

### Updating tools and relocking

1. Update the version in `src/chezmoi/.chezmoidata/mise.toml`.
2. Apply the config: `chezmoi apply ~/.config/mise/config.toml`
3. Regenerate the lockfile: `MISE_LOCKED=0 mise lock --global`
4. Add the updated lockfile: `chezmoi add ~/.config/mise/mise.lock`
