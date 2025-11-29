{{- $shell := .shell -}}
{{- with .bazelisk -}}
{{- if ne .installation "disabled" -}}
# Bazelisk shell configuration

if command -v bazelisk >/dev/null 2>&1; then
    {{- if eq $shell "bash" }}
    eval "$(bazelisk completion bash)"
    {{- else if eq $shell "zsh" }}
    # Autocompletion removed due to slow startup times in zsh
    :
    {{- end }}
fi
{{- end -}}
{{- end }}
