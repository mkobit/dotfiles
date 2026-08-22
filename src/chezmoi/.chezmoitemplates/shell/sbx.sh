{{- if ne (dig "local" "bin" "sbx" "installation_method" "none" $) "none" }}
# Docker Sandboxes (sbx) completions
if command -v sbx >/dev/null 2>&1; then
    {{- if eq $.shell "zsh" }}
    if type compdef &>/dev/null; then
        eval "$(sbx completion zsh)"
    fi
    {{- else if eq $.shell "bash" }}
    eval "$(sbx completion bash)"
    {{- end }}
fi
{{- end }}
