---
root: true
targets: ["*"]
description: "Project Rules and Guidelines"
globs: ["**/*"]
---
# Agent context for dotfiles repository

## Project overview

Personal dotfiles repository using chezmoi for configuration management.
Maintains personal/work profiles with hybrid Bazel automation.

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

## Repository structure

- `src/` - Chezmoi templates and deployment configuration
- `tools/` - Bazel rules for validation, testing, and automation
- `config/` - Build configuration and profile management
- chezmoi files - `.chezmoi*` configuration and templates

## Commands

### Primary workflow (chezmoi)
```bash
chezmoi diff                                    # Preview changes
chezmoi apply                                   # Install/update dotfiles
chezmoi edit dot_gitconfig                      # Edit source files
```

### Development (Bazel)
```bash
bazel test //...                                # Run tests
bazel run //:format                             # Format code
bazel run //:gazelle                            # Generate/update BUILD files
bazel run //:gazelle_python_manifest.update     # Update Python import manifest
bazel test //:gazelle_python_manifest.test      # Verify manifest is current
```

## Key principles

- Use existing patterns before creating new ones
- Feature flags over profiles for granular configuration control
- Security paramount with pinned versions and no committed secrets
- Cross-platform compatibility (Linux, macOS)
- Preserve existing user configurations during installation
