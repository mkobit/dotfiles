# Chezmoi Scripts

This directory contains `run_once_` scripts executed by `chezmoi apply`.

## Conventions

### Sourcing Shared Libraries

Scripts in this directory should source shared shell libraries (like `logging.sh`) from `.chezmoitemplates`.

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
