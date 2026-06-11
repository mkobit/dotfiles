{{ if eq .mise.installation_method "chezmoi_external" -}}
# mise version manager
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate {{ .shell }})"
fi
{{- end }}
