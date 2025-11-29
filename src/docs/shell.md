# Shell Configuration

This repository supports both Zsh (primary) and Bash environments.

## Shared Configuration

Common shell logic is maintained in `src/.chezmoitemplates/shell/` and included in shell-specific scripts using chezmoi templates.

### Shared Templates

Templates in `src/.chezmoitemplates/shell/` contain the core logic. These scripts are designed to be POSIX-compliant or handle shell differences using version checks (e.g., `$ZSH_VERSION`, `$BASH_VERSION`).

### Usage

To use a shared template in a shell configuration:
1. Create a script in the shell's specific directory (e.g., `src/dot_dotfiles/zsh/scripts/` or `src/dot_dotfiles/bash/snippets/`).
2. Use the `.tmpl` extension.
3. Include the shared template: `{{ include "shell/template_name.sh" . }}`.

## Zsh Specifics

Zsh-specific scripts are in `src/dot_dotfiles/zsh/scripts/`.
They are sourced in lexicographical order (numeric prefix recommended).

## Bash Specifics

Bash-specific snippets are in `src/dot_dotfiles/bash/snippets/`.
They are sourced in lexicographical order.
