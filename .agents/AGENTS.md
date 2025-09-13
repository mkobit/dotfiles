# Agent context for dotfiles repository

## Project overview

Personal dotfiles repository transitioning from Bazel to chezmoi for configuration management. Maintains personal/work profiles and guarded installation concepts.

**🚧 Active Projects**: See [.agents/scratch_zone/](.agents/scratch_zone/) for current development status and tasks.

## Repository structure

- `src/` - Tool configurations (git, zsh, tmux, vim, hammerspoon, jq)
- `rules/` - Bazel rules (maintained for testing/automation)
- `config/` - Build configuration and profile management
- chezmoi files - `.chezmoi*` configuration and templates

## Commands

### Primary workflow (chezmoi)
```bash
chezmoi apply                                   # Install/update dotfiles
chezmoi diff                                    # Preview changes
chezmoi edit dot_gitconfig                      # Edit source files
```

### Development (Bazel)
```bash
bazel test //...                                # Run tests
bazel run //:format                             # Format code
```

## Key principles

- Personal/work profiles with different settings  
- Security paramount with pinned versions and no committed secrets
- Tests validate configurations before deployment
- Cross-platform compatibility (Linux, macOS, Windows)
- Preserve existing user configurations during installation

## Bazel to chezmoi transition

**Current state**: Mixed Bazel/chezmoi architecture during migration period.

### Migration goals
- **chezmoi**: Primary tool for file installation and management
- **Bazel**: Retained for verification, testing, and automation tasks
- **Hybrid approach**: Leverage strengths of both tools

### Responsibilities

#### chezmoi handles:
- Dotfile installation and management (`chezmoi apply`)
- Template processing and variable substitution
- Cross-platform file management
- User-specific configuration deployment

#### Bazel retains:
- **Verification**: Validate configurations before deployment
- **Testing**: Unit tests for configuration logic
- **Automation**: Generate chezmoi files (versions, SHAs, external dependencies)
- **Build reproducibility**: Pinned dependencies and deterministic builds

### Implementation strategy
1. Keep existing Bazel infrastructure for testing/verification
2. Gradually migrate installation logic to chezmoi templates
3. Future: Use Bazel to generate dynamic chezmoi files (versions, SHAs, external dependencies)
4. Maintain dual-path support during transition
5. Preserve security practices (pinned versions, safe installation concepts)

### Future state
- `chezmoi apply` as primary deployment command
- `bazel test //...` for validation
- Simplified user workflow with maintained build system benefits

## chezmoi documentation

This repository uses chezmoi for dotfiles management. Key documentation links:

### Special files
- [Template format](https://www.chezmoi.io/reference/special-files/chezmoi-format-tmpl/) - `.tmpl` files with Go templating
- [Data files](https://www.chezmoi.io/reference/special-files/chezmoidata-format/) - `.chezmoidata.*` for template variables
- [External files](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/) - `.chezmoiexternal.*` for downloaded files
- [Ignore patterns](https://www.chezmoi.io/reference/special-files/chezmoiignore/) - `.chezmoiignore` for exclusions
- [Remove files](https://www.chezmoi.io/reference/special-files/chezmoiremove/) - `.chezmoiremove` for cleanup
- [Root directory](https://www.chezmoi.io/reference/special-files/chezmoiroot/) - `.chezmoiroot` for source location
- [Version requirements](https://www.chezmoi.io/reference/special-files/chezmoiversion/) - `.chezmoiversion` for version constraints

### Special directories
- [Data directory](https://www.chezmoi.io/reference/special-directories/chezmoidata/) - `.chezmoidata/` for template data files
- [Externals directory](https://www.chezmoi.io/reference/special-directories/chezmoiexternals/) - `.chezmoiexternals/` for external file configs  
- [Scripts directory](https://www.chezmoi.io/reference/special-directories/chezmoiscripts/) - `.chezmoiscripts/` for run scripts
- [Templates directory](https://www.chezmoi.io/reference/special-directories/chezmoitemplates/) - `.chezmoitemplates/` for reusable templates

### Configuration
- [Configuration file](https://www.chezmoi.io/reference/configuration-file/) - `.chezmoi.toml` settings

## chezmoi script patterns

### Shared utility libraries

For reusable code across multiple scripts, use the `scripts/` directory pattern:

```bash
# Structure
src/
├── scripts/
│   └── utils.sh              # Shared utilities (logging, helpers)
└── .chezmoiscripts/
    └── run_once_example.sh.tmpl

# Usage in scripts
#!/bin/bash
# utils.sh hash: {{ include "scripts/utils.sh" | sha256sum }}
source "${CHEZMOI_SOURCE_DIR:?}/scripts/utils.sh"

log_info "Using shared logging utilities..."
```

**Key principles:**
- Use `${CHEZMOI_SOURCE_DIR:?}` for robust sourcing with error handling
- Include hash comments for dependency tracking (script re-runs when utilities change)  
- Keep utilities in `scripts/` directory (not managed as dotfiles)
- Follow community pattern from [chezmoi/discussions/3506](https://github.com/twpayne/chezmoi/discussions/3506)

**Utility functions available:**
- `log_info()`, `log_success()`, `log_warn()`, `log_error()` - Colored logging
- `check_command()` - Test if command is available
