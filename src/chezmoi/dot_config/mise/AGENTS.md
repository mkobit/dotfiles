# Mise tool version manager

## Installation

- **Mechanism**: Installed via `.chezmoiexternals/` directly from GitHub releases.
- **Location**: `{{ .chezmoi.destDir }}/.local/bin/mise`.

## Configuration

- **Global Tools**: Defined in `src/chezmoi/.chezmoidata/mise.toml`.
- **Shell**: Automatically hooked into `.zshrc` / `.bashrc`.

## Updating Tool Versions

The `mise.lock` file is committed to the repository and managed via Chezmoi to enforce `--locked` installations across environments. This lockfile ensures deterministic tool resolutions and avoids relying on external APIs (like GitHub or npm) during dotfiles deployment.

When updating versions in `src/chezmoi/.chezmoidata/mise.toml`, you must also regenerate the `mise.lock` file. Because Chezmoi dynamically generates the `~/.config/mise/config.toml` based on enabled/disabled features per machine, the lockfile should contain resolutions for *all* potential tools, regardless of whether they are active on the current machine.

To update the lockfile:
1. Temporarily create a `mise.toml` with *all* tools enabled, or use a machine where all tools are configured to install.
2. Run `MISE_LOCKED=0 mise lock --global` to fetch checksums and URLs.
3. Copy `~/.config/mise/mise.lock` to `src/chezmoi/dot_config/mise/mise.lock`.

It is perfectly safe (and required) to have entries in the lockfile for tools that are not currently being installed on a specific machine. `mise` will simply ignore lockfile entries for tools that aren't declared in the active `config.toml`.
