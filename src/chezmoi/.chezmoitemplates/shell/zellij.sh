{{- $zellij := index . "zellij" | default (dict) -}}
{{- if eq (dig "installation_method" "" $zellij) "chezmoi_external" }}
# Zellij aliases and fzf completion
alias zj="zellij"
alias zja="zellij attach"

# Initialize zellij completions
if command -v zellij >/dev/null 2>&1; then
    eval "$(zellij setup --generate-completion {{ .shell }})"
fi

# Custom fzf completion for zellij sessions triggered by **<TAB>
# fzf's bash/zsh completion scripts automatically detect and use these functions
# when the user types 'zellij attach **<TAB>' or 'zja **<TAB>'

_fzf_complete_zellij() {
    local args
    args=("$@")

    # Only trigger fzf session picker for 'attach' or 'a' subcommand
    if [[ " ${args[*]} " =~ " attach " || " ${args[*]} " =~ " a " ]]; then
        _fzf_complete --reverse --prompt="Zellij Session> " -- "$@" < <(
            command zellij list-sessions -n 2>/dev/null | sed -E 's/\x1B\[[0-9;]*[a-zA-Z]//g' | awk '{print $1}'
        )
    else
        # Fall back to default file/dir completion provided by fzf for other subcommands
        _fzf_path_completion "$@"
    fi
}

_fzf_complete_zja() {
    _fzf_complete --reverse --prompt="Zellij Session> " -- "$@" < <(
        command zellij list-sessions -n 2>/dev/null | sed -E 's/\x1B\[[0-9;]*[a-zA-Z]//g' | awk '{print $1}'
    )
}

_fzf_complete_zj() {
    _fzf_complete_zellij "$@"
}
{{- end }}
