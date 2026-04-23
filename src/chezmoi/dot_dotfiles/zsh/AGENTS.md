# Zsh configuration

## Shared templates

- **Location**: `src/.chezmoitemplates/shell/`.
- **Usage**: Include in shell-specific scripts (Zsh/Bash) with context:
  ```toml
  {{- $ctx := merge (dict "shell" "zsh") . -}}
  {{ template "shell/template_name.sh" $ctx }}
  ```
- **Logic**: Use `.shell` variable for conditionals (`eq .shell "zsh"`).

## Font automation

- Fonts specified in `.chezmoidata/fonts.toml` are automatically downloaded via `.chezmoiexternals/` to `{{ .chezmoi.destDir }}/.local/share/fonts/`.
