{{- with .bazelisk -}}
{{- if ne .installation "disabled" -}}
# Bazelisk shell configuration

if command -v bazelisk >/dev/null 2>&1; then
    if [ -n "$BASH_VERSION" ]; then
        eval "$(bazelisk completion bash)"
    elif [ -n "$ZSH_VERSION" ]; then
        # Autocompletion removed due to slow startup times in zsh
        :
    fi
fi
{{- end -}}
{{- end }}
