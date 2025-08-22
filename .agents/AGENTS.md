# Agent context for dotfiles repository

## Project overview

Personal dotfiles repository using Bazel for cross-platform configuration management. Configurations in `src/` with personal/work profiles and guarded installation.

## Repository structure

- `src/` - Tool configurations (git, zsh, tmux, vim, hammerspoon, jq)
- `rules/` - Custom Bazel rules for configuration management
- `toolchains/` - Bazel toolchain definitions  
- `config/` - Build configuration and profile management
- `docs/` - Documentation and security practices

## Features

- Profile-based configurations (personal/work)
- Bazel-managed reproducible builds
- Guarded installation prevents overwriting existing configs
- Cross-platform support (Linux, macOS, Windows)
- Security-first approach with pinned dependencies

## Commands

### Build
```bash
bazel build //... --//config:profile=personal  # Personal profile
bazel build //... --//config:profile=work      # Work profile
bazel run //:format                             # Format code
bazel run //:lsp_setup                          # Generate IDE config
```

### Test
```bash
bazel test //...                                # All tests
bazel test //src/git:test                       # Package tests
```

### Install
```bash
bazel run //config:install_all                  # All configs
bazel run //src/git:install_config_home         # Specific tool
```

## Agent guidelines

### Code style
- Follow existing Bazel patterns
- Use guarded installation for safe config injection
- Maintain personal/work profile separation
- Keep configurations modular and testable
- Tag installation targets `manual`

### Security
- Never commit secrets
- Pin all dependencies to specific versions (GitHub Actions to commit SHAs)
- Dependabot handles automatic security updates
- Use guarded installation to prevent corruption

### File organization
- New tools follow `src/{tool}/` pattern
- Include Bazel BUILD files
- Add rules in `rules/{tool}/` if needed
- Document configuration options

### Testing
- Include tests for new configurations
- Use existing test patterns
- Ensure cross-platform compatibility
- Test both personal and work profiles

## Build system

### Package structure
- Self-contained packages under `src/{tool}/`
- `BUILD.bazel` files define installation/verification/test targets
- Installation targets tagged `manual`
- Tests co-located with source files

### Target types
- Installation: `sh_binary` with install scripts or custom rules
- Verification: Echo paths without side effects
- Test: Validate configuration logic
- Build: Generate files from templates

### Queries
```bash
bazel build //...                               # All buildable targets
bazel build //src/git:all                       # Specific package
bazel query "deps(//src/tmux:all)" --output label  # Dependencies
```

## Common tasks

- Add new tool: Create `src/{tool}/`, BUILD file, rule in `rules/`
- Modify configs: Edit `src/{tool}/configs/`
- Add profile settings: Use profile flags in BUILD files
- Security updates: Review and update pinned dependencies

## Exploration workflow

Before changes:
1. Query dependencies: `bazel query "deps(//target)" --output label`
2. Inspect build outputs: Run `bazel build` and examine files
3. Find patterns: `grep -r` for similar implementations
4. Read all relevant files before suggesting changes

## Guarded installation

Safe injection into existing config files without overwriting user content.

```bash
# Install git config to ~/.gitconfig
bazel run //src/git:install_config_home
```

Works by:
- Wrapping content with guard comments (`# START/END DOTFILES MANAGED SECTION`)
- Only updating managed sections on subsequent runs
- Preserving existing user content before/after guards
- Using atomic operations with temporary files

## Key principles

- Guarded installation prevents overwriting user configs
- Personal/work profiles with different settings
- Installation targets tagged `manual` prevent accidents
- Tests co-located for maintainability
- Bazel for reproducible builds and dependencies
- Security paramount with pinned versions