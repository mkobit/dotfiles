#!/usr/bin/env zsh
# =============================================================================
# OH-MY-ZSH LOADER
# =============================================================================
# This script sources oh-my-zsh and any custom configurations.
# oh-my-zsh is installed and managed by chezmoi.

# Source custom configurations for oh-my-zsh
source {{ .chezmoi.homeDir }}/.dotfiles/zsh/snippets/oh-my-zsh-custom.zsh

# Set the ZSH environment variable to the chezmoi-managed location
export ZSH="$HOME/.oh-my-zsh"

# Load oh-my-zsh
if [[ -f "$ZSH/oh-my-zsh.sh" ]]; then
    source "$ZSH/oh-my-zsh.sh"
else
    echo -e "\033[1;33m⚠️  oh-my-zsh.sh not found at $ZSH/oh-my-zsh.sh\033[0m"
fi
