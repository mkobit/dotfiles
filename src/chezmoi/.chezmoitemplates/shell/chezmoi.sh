{{ completion .shell }}

alias cz='chezmoi'

{{- if eq $.shell "zsh" }}
compdef cz=chezmoi
{{- else if eq $.shell "bash" }}
complete -F _chezmoi -o bashdefault -o default cz
{{- end }}
