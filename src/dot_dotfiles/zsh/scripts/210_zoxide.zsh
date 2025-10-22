# Zoxide - smart directory jumping
if command -v zoxide &> /dev/null; then
    if [ -n "$ZSH_VERSION" ]; then
        eval "$(zoxide init zsh)"
    elif [ -n "$BASH_VERSION" ]; then
        eval "$(zoxide init bash)"
    else
        eval "$(zoxide init posix)"
    fi

    alias cd='z'
    alias cdi='zi'
else
    if [ -z "$ZOXIDE_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  zoxide not found\033[0m - install for better directory navigation: \033[1;34mhttps://github.com/ajeetdsouza/zoxide\033[0m"
        export ZOXIDE_INSTALL_HINT_SHOWN=1
    fi
fi
