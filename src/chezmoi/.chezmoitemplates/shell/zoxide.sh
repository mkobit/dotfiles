# Zoxide - smart directory jumping
# Only initialize in interactive shells: non-interactive shells (scripts, AI
# agent sessions) don't benefit from directory tracking and the chpwd hook
# will never fire, which triggers zoxide's own doctor warning spuriously.
if [[ -o interactive ]] && command -v zoxide &> /dev/null; then
    {{- if eq .shell "zsh" }}
    eval "$(zoxide init zsh --cmd cd)"
    {{- else if eq .shell "bash" }}
    eval "$(zoxide init bash --cmd cd)"
    {{- else }}
    {{- fail (printf "unsupported shell: %s" .shell) }}
    {{- end }}

else
    if [ -z "$ZOXIDE_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  zoxide not found\033[0m - install for better directory navigation: \033[1;34mhttps://github.com/ajeetdsouza/zoxide\033[0m"
        export ZOXIDE_INSTALL_HINT_SHOWN=1
    fi
fi
