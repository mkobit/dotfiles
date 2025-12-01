# Shell Configuration

This repository supports both Zsh (primary) and Bash environments.

## Shared Configuration

Common shell logic is maintained in `src/.chezmoitemplates/shell/` and included in shell-specific scripts using chezmoi templates.

### Shared Templates

Templates in `src/.chezmoitemplates/shell/` contain the core logic. These scripts are designated to avoid duplication while allowing for shell-specific rendering.

### Usage

To use a shared template in a shell configuration:
1. Create a script in the shell's specific directory (e.g., `src/dot_dotfiles/zsh/scripts/` or `src/dot_dotfiles/bash/snippets/`).
2. Use the `.tmpl` extension.
3. Include the shared template, passing the shell context and preserving the global context:
   ```
   {{ template "shell/template_name.sh" (merge (dict "shell" "zsh") .) }}
   ```

### Template Logic

Templates in `src/.chezmoitemplates/shell/` should use the `.shell` variable to conditionally render content and fail on unsupported shells:
```bash
{{- if eq .shell "zsh" }}
# Zsh specific code
{{- else if eq .shell "bash" }}
# Bash specific code
{{- else }}
{{- fail (printf "unsupported shell: %s" .shell) }}
{{- end }}
```

## Zsh Specifics

Zsh-specific scripts are in `src/dot_dotfiles/zsh/scripts/`.
They are sourced in lexicographical order (numeric prefix recommended).

## Bash Specifics

Bash-specific snippets are in `src/dot_dotfiles/bash/snippets/`.
They are sourced in lexicographical order.
