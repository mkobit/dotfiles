# Shell Configuration

This repository supports both Zsh (primary) and Bash environments.

## Shared Configuration

To maintain consistency across shells, common configurations are located in `src/dot_dotfiles/shared/`.
These scripts are sourced by both Zsh and Bash configurations.

### Shared Scripts Structure

Shared scripts use the `.sh` or `.sh.tmpl` extension and are prefixed with numbers for deterministic loading order:

- `000-099`: Environment variables and basic settings
- `100-199`: Tool setup (e.g., asdf)
- `200-299`: Interactive tools (fzf, zoxide)
- `300-899`: Aliases and functions
- `900-999`: Tool-specific configurations (bazelisk)

### Adding a Shared Script

1. Create a file in `src/dot_dotfiles/shared/` with the `.sh` extension.
2. Ensure the code is POSIX-compliant or handles shell differences:

```bash
if [ -n "$ZSH_VERSION" ]; then
    # Zsh specific
elif [ -n "$BASH_VERSION" ]; then
    # Bash specific
fi
```

3. Prefix the filename with a number to control loading order.

## Zsh Specifics

Zsh-specific scripts are in `src/dot_dotfiles/zsh/scripts/`.
The configuration sources shared scripts first, then Zsh scripts.

## Bash Specifics

Bash-specific snippets are in `src/dot_dotfiles/bash/snippets/`.
The configuration sources shared scripts first, then Bash snippets.
