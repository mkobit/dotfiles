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

### Configuration
- [Configuration file](https://www.chezmoi.io/reference/configuration-file/) - `chezmoi.toml` settings
