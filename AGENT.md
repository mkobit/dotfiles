# Agent Context for Dotfiles Repository

## Project Overview

This is a personal dotfiles repository managed with Bazel for cross-platform configuration management. The repository contains configurations for various development tools organized under a structured Bazel build system.

## Repository Structure

- **`src/`** - All tool configurations organized by tool type
  - `git/` - Git configurations with personal/work profiles
  - `zsh/` - Zsh shell configurations and performance optimizations
  - `tmux/` - Tmux terminal multiplexer configurations
  - `vim/` - Vim editor configurations
  - `hammerspoon/` - macOS automation tool configurations
  - `jq/` - JSON processing tool configurations

- **`rules/`** - Custom Bazel rules for configuration management
- **`toolchains/`** - Bazel toolchain definitions
- **`config/`** - Build configuration and profile management
- **`docs/`** - Documentation including security practices

## Key Features

- **Profile-based configurations**: Separate personal and work profiles
- **Bazel-managed builds**: Reproducible configuration deployment
- **Guarded installation**: Safe injection into existing configuration files
- **Cross-platform support**: Linux, macOS, and Windows compatibility
- **Security-first approach**: Pinned dependencies and automated security updates

## Development Workflow

### Building
```bash
# Build specific profile
bazel build //... --//config:profile=personal
bazel build //... --//config:profile=work

# Format code
bazel run //:format

# Generate IDE configuration  
bazel run //:lsp_setup
```

### Testing
```bash
# Run all tests
bazel test //...

# Run quality checks
bazel test //:quality_checks
```

### Installation
```bash
# Install all configurations
bazel run //config:install_all

# Install specific tool configuration
bazel run //src/git:install_config_home
bazel run //src/zsh:install_config_home
```

## Agent Guidelines

### Code Style
- Follow existing Bazel patterns and conventions
- Use guarded installation patterns for safe configuration injection
- Maintain separation between personal and work profiles
- Keep configurations modular and testable

### Security Considerations
- Never commit secrets or sensitive information
- Follow the security practices outlined in `docs/SECURITY.adoc`
- Pin all dependencies to specific versions
- Use guarded installation to prevent configuration corruption

### File Organization
- New tool configurations should follow the `src/{tool}/` pattern
- Include appropriate Bazel BUILD files
- Add corresponding rules in `rules/{tool}/` if needed
- Document configuration options and usage

### Testing
- Always include tests for new configurations
- Use the existing test patterns in the codebase
- Ensure cross-platform compatibility when possible
- Test both personal and work profile builds

## Build System Architecture

### Package Structure
- Each tool has a self-contained package under `src/{tool}/`
- `BUILD.bazel` files define installation, verification, and test targets
- Installation targets are tagged `manual` to prevent accidental execution
- Tests are co-located with source files for better organization

### Target Types
- **Installation targets**: Use `sh_binary` with `//rules:install_dotfile.sh` or custom rules
- **Verification targets**: Echo intended paths without side effects
- **Test targets**: Validate configuration logic and scripts
- **Build targets**: Generate files from templates or compile code

### Workflow Commands
```bash
# Build all buildable targets
bazel build //...

# Build specific package
bazel build //src/git:all

# Test specific package
bazel test //src/git:test

# Query dependencies
bazel query "deps(//src/tmux:all)" --output label
```

## Common Tasks

- **Adding a new tool configuration**: Create directory in `src/`, add BUILD file, create rule in `rules/`
- **Modifying existing configurations**: Edit files in `src/{tool}/configs/`
- **Adding profile-specific settings**: Use profile flags in BUILD files
- **Security updates**: Review and update pinned dependencies

## Exploration Guidelines

Before making changes, always:

1. **Examine dependencies**: Use `bazel query "deps(//target)" --output label`
2. **Understand build outputs**: Run `bazel build` and inspect generated files
3. **Check existing implementations**: Use `grep -r` to find similar patterns
4. **Read ALL relevant files** before suggesting changes

## Important Notes

- All configurations use guarded installation to prevent overwriting existing user configurations
- The repository supports both personal and work profiles with different settings
- Installation targets are tagged `manual` to prevent accidental execution
- Tests are co-located with configurations for better maintainability
- Bazel is used for reproducible builds and dependency management
- Security is a primary concern with all actions and dependencies pinned to specific versions