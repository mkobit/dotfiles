# Ghostty configuration

## Configuration structure

- **Split Files**: Uses `config-file` to include multiple configs (`fonts.conf`, `themes.conf`).
- **Processing**: Keys after a `config-file` do NOT override the included file (processed at end).

## Chezmoi integration

- **Platform-specific**: Templates handle font/size differences for macOS vs Linux.
  ```toml
  {{- if eq .chezmoi.os "darwin" }}
  font-family = "SF Mono"
  {{- else }}
  font-family = "DejaVu Sans Mono"
  {{- end }}
  ```
- **Profiles**: Profile-specific settings (e.g., window titles) are rendered based on `.git.personal.enabled`.
