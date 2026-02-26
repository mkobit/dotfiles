# Chezmoi Configuration

This directory contains the Chezmoi source state for dotfiles management.

## Directory Structure

- `.chezmoidata/`: TOML data files loaded into the template context.
- `.chezmoiexternals/`: External dependencies (archives, git repos) managed by Chezmoi.
- `.chezmoiscripts/`: Scripts executed by `chezmoi apply` (e.g., `run_once_` scripts).
- `.chezmoitemplates/`: Shared template fragments.
- `dot_*/`: Files that will be deployed to the user's home directory (e.g., `dot_config` -> `~/.config`).

## Script Conventions

### Sourcing Shared Libraries

Scripts in `.chezmoiscripts/` should source shared shell libraries (like `logging.sh`) from `.chezmoitemplates` using the absolute path provided by `{{ .chezmoi.sourceDir }}`.

**Pattern:**

```bash
# Source logging library from chezmoi source
CHEZMOI_SOURCE_DIR="{{ .chezmoi.sourceDir }}"
source "${CHEZMOI_SOURCE_DIR}/.chezmoitemplates/shell/logging.sh"
```

**Why:**
- `{{ .chezmoi.sourceDir }}` resolves to the absolute path of the source directory.
- This allows scripts to use shared utilities without them being deployed to the destination machine.
- Avoid using relative paths (e.g., `../../.chezmoitemplates`) as the execution context might vary.

### Referencing Destination Directory

When referring to the destination home directory in scripts (e.g., for `PATH` manipulation), always use `{{ .chezmoi.destDir }}` instead of `{{ .chezmoi.homeDir }}` or hardcoded paths like `$HOME`.
