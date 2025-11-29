{{ if eq .asdf.installation "external-sources" -}}
# asdf version manager
if [[ -f "{{ .chezmoi.destDir }}/.dotfiles/asdf/asdf.sh" ]]; then
    source "{{ .chezmoi.destDir }}/.dotfiles/asdf/asdf.sh"
fi
{{- end }}
