# Agent context for dotfiles repository

## Project overview

Personal dotfiles repository using chezmoi for configuration management. Maintains personal/work profiles with hybrid Bazel automation.

**🚧 Active Projects**: See [.agents/scratch_zone/](.agents/scratch_zone/) for current development status and tasks.

## Repository structure

- `src/` - Chezmoi templates and deployment configuration
- `build/` - Bazel rules for validation, testing, and automation
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

### Core concepts
- [Source state attributes](https://www.chezmoi.io/reference/source-state-attributes/) - File prefixes/suffixes (dot_, create_, encrypted_, executable_, etc.)
- [Application order](https://www.chezmoi.io/reference/application-order/) - Deterministic processing: before scripts → directories → files → after scripts (alphabetical)
- [Target types](https://www.chezmoi.io/reference/target-types/) - Files, directories, symlinks, scripts with type-specific attributes
- [Template functions](https://www.chezmoi.io/reference/templates/functions/) - Sprig functions + chezmoi-specific (includeTemplate, lookPath, output, etc.)
- [Template variables](https://www.chezmoi.io/reference/templates/variables/) - Complete variable reference

**Key template variables**:
- `{{ .chezmoi.sourceFile }}` - Current template source file path (e.g., `modify_dot_gitconfig.tmpl`)  
- `{{ .chezmoi.sourceDir }}` - Source directory path (e.g., `/Users/user/.local/share/chezmoi/src`)
- `{{ .chezmoi.homeDir }}` - User home directory path (e.g., `/Users/user`)
- `{{ .chezmoi.hostname }}` - Machine hostname
- `{{ .chezmoi.username }}` - Current user
- `{{ .chezmoi.os }}` - Operating system (darwin, linux, windows)
- `{{ .chezmoi.arch }}` - Architecture (amd64, arm64)

**Note**: Raw markdown documentation is also available at [chezmoi source docs](https://github.com/twpayne/chezmoi/tree/master/assets/chezmoi.io) for more concise reference when working with agents.

## chezmoi script patterns

### Shared utility libraries

For reusable code across multiple scripts, use the `scripts/` directory pattern:

```bash
# Structure
src/
├── scripts/
│   └── logging.sh            # Shared logging utilities
└── .chezmoiscripts/
    └── run_once_example.sh.tmpl

# Usage in scripts
#!/bin/bash
# logging.sh hash: {{ include "scripts/logging.sh" | sha256sum }}
source "${CHEZMOI_SOURCE_DIR:?}/scripts/logging.sh"

log_info "Using shared logging utilities..."
```

**Key principles:**
- Use `${CHEZMOI_SOURCE_DIR:?}` for robust sourcing with error handling
- Include hash comments for dependency tracking (script re-runs when utilities change)  
- Keep utilities in `scripts/` directory (not managed as dotfiles)
- Follow community pattern from [chezmoi/discussions/3506](https://github.com/twpayne/chezmoi/discussions/3506)

See `src/scripts/logging.sh` for available functions.

## Chezmoi modify script essentials

**Key insight**: `modify_` scripts work on ANY file via stdin/stdout - perfect for adding sections to corporate-managed files.

**Critical components**:
1. **SHA256 hash in header/footer** - enables change detection and re-execution  
2. **Replacement logic with sed** - removes old sections before adding new ones
3. **Matching header/footer** - defines exact boundaries for replacement
4. **ISO8601 timestamp** - shows when section was last applied

**Header pattern**:
```bash
# /path/to/script.tmpl:BEGIN:section:12345678 - WARNING: managed by chezmoi, do not edit
# Applied: 2025-01-15T10:30:45Z07:00
[configuration]
# /path/to/script.tmpl:END:section:12345678
```

**BSD sed compatibility**: Use literal filenames in sed patterns, not template variables (they expand incorrectly).
