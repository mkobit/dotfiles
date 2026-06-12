{{- if eq .shell "zsh" }}
unsetopt CORRECT_ALL
setopt CORRECT

bindkey -v
export KEYTIMEOUT=1

# Ensure FPATH includes Homebrew's site-functions directory BEFORE calling compinit.
# If this is done after compinit, brew-installed completions (like _eza) will not
# be discovered, causing `compdef: unknown command or service` errors when registering aliases.
if type brew &>/dev/null; then
    export FPATH="$(brew --prefix)/share/zsh/site-functions:${FPATH}"
fi

autoload -Uz compinit && compinit
autoload -U +X bashcompinit && bashcompinit
{{- end }}
