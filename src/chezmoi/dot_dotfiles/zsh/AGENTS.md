# Zsh configuration

## Shared templates

- **Location**: `src/.chezmoitemplates/shell/`.
- **Usage**: Include in shell-specific scripts (Zsh/Bash) with context:
  ```toml
  {{ template "shell/template_name.sh" (merge (dict "shell" "zsh") .) }}
  ```
- **Logic**: Use `.shell` variable for conditionals (`eq .shell "zsh"`).

## Font automation

- **MesloLGS NF**: Automatically downloaded via `.chezmoiexternals/` to `{{ .chezmoi.destDir }}/.dotfiles/external/fonts/`.
