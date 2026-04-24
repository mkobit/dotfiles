{{- $chezmoiSourceDir := .chezmoi.sourceDir -}}
{{- $chezmoiTargetDir := .chezmoi.destDir -}}
{{- with .eza -}}
{{- $installation := dig "installation_method" "none" . -}}
{{- if ne $installation "none" -}}
# eza completions and aliases
if command -v eza >/dev/null 2>&1; then
    # Add eza completions to FPATH if they exist
    {{- if eq $.shell "zsh" }}
    if [[ -f "{{ $chezmoiTargetDir }}/.dotfiles/external/eza-completions/zsh/_eza" ]]; then
        export FPATH="{{ $chezmoiTargetDir }}/.dotfiles/external/eza-completions/zsh:$FPATH"
    fi
    {{- end }}

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