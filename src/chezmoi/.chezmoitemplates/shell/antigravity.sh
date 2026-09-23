{{- $autoUpdate := dig "local" "bin" "agy" "auto_update" (dig "gemini" "general" "enable_auto_update" false .) . -}}
{{- if not $autoUpdate }}
# Disable Antigravity CLI automatic self-updates to preserve chezmoi management
export AGY_CLI_DISABLE_AUTO_UPDATE=true
{{- end }}
