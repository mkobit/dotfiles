# Disable terminal bell/beep sounds
# This prevents audio notifications

{{- if eq .shell "zsh" }}
# ZSH-specific bell disabling
unsetopt BEEP
{{- else if eq .shell "bash" }}
# Disable readline bell (bash completion, history, etc.)
bind 'set bell-style none' 2>/dev/null || true
{{- else }}
{{- fail (printf "unsupported shell: %s" .shell) }}
{{- end }}
