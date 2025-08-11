# Claude Code Configuration

## Project Context

This dotfiles repository uses Bazel for cross-platform configuration management with personal/work profiles. All configurations are located in `src/` and follow strict security practices.

## Build and Test Commands

### Formatting and Linting
```bash
bazel run //:format
bazel test //:format_test
```

### Building
```bash
# Personal profile (default for development)
bazel build //... --//config:profile=personal

# Work profile
bazel build //... --//config:profile=work
```

### Testing
```bash
# Run all tests
bazel test //...

# Test specific package
bazel test //src/git:test

# Quality checks
bazel test //:quality_checks

# Coverage report
bazel coverage //...
```

### Installation
```bash
# Install all configurations
bazel run //config:install_all

# Install specific configurations
bazel run //src/git:install_config_home
bazel run //src/zsh:install_config_home
bazel run //src/tmux:install_config_home
```

### IDE Setup
```bash
# Generate LSP configuration
bazel run //:lsp_setup

# Generate compile commands
bazel run //:compile_commands
```

## File Patterns

### Configuration Files
- `src/{tool}/configs/` - Tool-specific configuration files
- `src/{tool}/BUILD.bazel` - Bazel build definitions
- `rules/{tool}/` - Custom Bazel rules for each tool

### Important Files
- `MODULE.bazel` - Bazel module definition
- `config/BUILD.bazel` - Profile and installation configuration
- `docs/SECURITY.adoc` - Security practices and guidelines

## Development Guidelines

### Security Requirements
- Never commit secrets or sensitive information
- All dependencies must be pinned to specific versions
- Follow guarded installation patterns to prevent configuration corruption
- Review security documentation before making changes

### Code Style
- Follow existing Bazel patterns
- Maintain modular, testable configurations
- Use profile-based configuration separation
- Include appropriate tests for all changes
- Installation targets must be tagged `manual` to prevent accidental execution

### Exploration Before Changes
Before making any modifications:

1. **Query dependencies**: `bazel query "deps(//target)" --output label`
2. **Inspect build outputs**: Run `bazel build //target` and examine generated files
3. **Find existing patterns**: Use `grep -r "pattern" --include="*.ext" ./src/tool/`
4. **Read all relevant files** before suggesting changes

### Common Workflows
- Always run tests before committing: `bazel test //...`
- Format code before committing: `bazel run //:format`
- Test both personal and work profiles when making changes
- Use guarded installation for safe configuration deployment
- Explore existing implementations before adding new features

## Memory Context

When working on this repository, remember:
- This is a personal dotfiles repository with both personal and work configurations
- Bazel is used for reproducible builds and cross-platform support
- Security is paramount - all actions and dependencies are pinned
- Configurations use guarded installation to safely inject into existing files
- The repository structure follows `src/{tool}/` organization pattern