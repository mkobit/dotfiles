{{- if eq .shell "zsh" }}
unsetopt CORRECT_ALL
setopt CORRECT

bindkey -v
export KEYTIMEOUT=1

if type brew &>/dev/null; then
    export FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"
fi

autoload -Uz compinit && compinit
autoload -U +X bashcompinit && bashcompinit
{{- end }}
