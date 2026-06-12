{{- $chezmoiSourceDir := .chezmoi.sourceDir -}}
{{- $chezmoiTargetDir := .chezmoi.destDir -}}
{{- if ne (dig "local" "bin" "eza" "installation_method" "none" $) "none" -}}
# eza completions and aliases
if command -v eza >/dev/null 2>&1; then
    # eza aliases - modern ls replacement
    alias ls='eza'
    alias ll='eza --long'
    alias la='eza --long --all'
    alias l='eza --long --all'
    alias tree='eza --tree'
    alias lt='eza --tree'

    {{- if eq $.shell "zsh" }}
    if (( ${+_comps[eza]} )); then
        compdef ls=eza
        compdef ll=eza
        compdef la=eza
        compdef l=eza
        compdef tree=eza
        compdef lt=eza
    fi
    {{- else if eq $.shell "bash" }}
    complete -F _eza -o bashdefault -o default ls
    complete -F _eza -o bashdefault -o default ll
    complete -F _eza -o bashdefault -o default la
    complete -F _eza -o bashdefault -o default l
    complete -F _eza -o bashdefault -o default tree
    complete -F _eza -o bashdefault -o default lt
    {{- end }}
fi
{{- end }}
