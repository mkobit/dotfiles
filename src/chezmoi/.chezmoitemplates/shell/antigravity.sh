{{- $autoUpdate := dig "local" "bin" "agy" "auto_update" (dig "gemini" "general" "enable_auto_update" false .) . -}}
{{- if not $autoUpdate }}
# Disable the native updater: https://antigravity.google/docs/cli/troubleshooting/#resolution-3
export AGY_CLI_DISABLE_AUTO_UPDATE=true
{{- end }}
