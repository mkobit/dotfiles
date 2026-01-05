{{ if eq .mise.installation "external-sources" -}}
# mise version manager
if command -v mise >/dev/null 2>&1; then
  eval "$(mise activate {{ .shell }})"
fi
{{- end }}
