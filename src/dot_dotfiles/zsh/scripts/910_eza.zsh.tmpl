{{- $chezmoiSourceDir := .chezmoi.sourceDir -}}
{{- $chezmoiTargetDir := .chezmoi.destDir -}}
{{- with .eza -}}
{{- $installation := index .installation $.chezmoi.os -}}
{{- if and $installation (ne $installation "disabled") -}}
# eza completions and aliases
if command -v eza >/dev/null 2>&1; then
    # Add eza completions to FPATH if they exist
    if [[ -f "{{ $chezmoiTargetDir }}/.dotfiles/external/eza-completions/zsh/_eza" ]]; then
        export FPATH="{{ $chezmoiTargetDir }}/.dotfiles/external/eza-completions/zsh:$FPATH"
    fi

    # eza aliases - modern ls replacement
    alias ls='eza'
    alias ll='eza --long'
    alias la='eza --long --all'
    alias l='eza --long --all'
    alias tree='eza --tree'
    alias lt='eza --tree'
fi
{{- end -}}
{{- end }}