{{- if ne (dig "local" "bin" "openshell" "installation_method" "none" $) "none" }}
# NVIDIA OpenShell (openshell) completions
if command -v openshell >/dev/null 2>&1; then
    {{- if eq $.shell "zsh" }}
    if type compdef &>/dev/null; then
        eval "$(openshell completions zsh)"
    fi
    {{- else if eq $.shell "bash" }}
    eval "$(openshell completions bash)"
    {{- end }}
fi
{{- end }}
