#!/usr/bin/env zsh

unsetopt CORRECT_ALL
setopt CORRECT

bindkey -v
export KEYTIMEOUT=1

autoload -U +X bashcompinit && bashcompinit
