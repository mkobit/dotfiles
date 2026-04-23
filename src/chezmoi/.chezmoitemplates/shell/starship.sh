{{- $prompt := default "starship" .zsh.prompt -}}
{{- if eq $prompt "starship" }}
# Initialize Starship
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init {{ .shell }})"
else
    echo -e "\033[1;33m⚠️  starship not found in PATH\033[0m"
fi
{{- end }}
