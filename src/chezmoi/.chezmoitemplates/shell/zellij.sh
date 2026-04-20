{{- $zellij := index . "zellij" | default (dict "enabled" false) -}}
{{- if $zellij.enabled }}
# Zellij aliases and fzf completion
alias zj="zellij"
alias za="zellij attach"

# Custom fzf completion for zellij sessions triggered by **<TAB>
# fzf's bash/zsh completion scripts automatically detect and use these functions
# when the user types 'zellij attach **<TAB>' or 'za **<TAB>'

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

_fzf_complete_za() {
    _fzf_complete --reverse --prompt="Zellij Session> " -- "$@" < <(
        command zellij list-sessions -n 2>/dev/null | sed -E 's/\x1B\[[0-9;]*[a-zA-Z]//g' | awk '{print $1}'
    )
}

_fzf_complete_zj() {
    _fzf_complete_zellij "$@"
}
{{- end }}
