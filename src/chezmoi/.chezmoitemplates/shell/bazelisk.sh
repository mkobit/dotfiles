{{- $shell := .shell -}}
{{- with .bazelisk -}}
{{- if ne .installation "disabled" -}}
# Bazelisk shell configuration

if command -v bazelisk >/dev/null 2>&1; then
    {{- if or (eq $shell "bash") (eq $shell "zsh") }}
    # Autocompletion removed due to slow startup times
    :
    {{- else }}
    {{- fail (printf "unsupported shell: %s" $shell) }}
    {{- end }}
fi
{{- end -}}
{{- end }}
