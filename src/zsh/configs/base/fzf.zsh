# FZF - Enhanced fuzzy finding and history search
if command -v fzf &> /dev/null; then
    if [ -n "$ZSH_VERSION" ]; then
        source <(fzf --zsh)
    elif [ -n "$BASH_VERSION" ]; then
        eval "$(fzf --bash)"
    fi

    if [ -z "$FZF_DEFAULT_OPTS" ]; then
        export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border --inline-info"
    fi
else
    if [ -z "$FZF_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  fzf not found\033[0m - install for enhanced history search and fuzzy finding:"
        echo -e "  \033[1;34mMore info:\033[0m https://github.com/junegunn/fzf#installation"
        export FZF_INSTALL_HINT_SHOWN=1
    fi
fi
