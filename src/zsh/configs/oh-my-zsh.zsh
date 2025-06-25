#!/usr/bin/env zsh
# =============================================================================
# MINIMAL OH-MY-ZSH - PERFORMANCE FOCUSED
# =============================================================================

# Check if oh-my-zsh is installed
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
    echo -e "\033[1;33m⚠️  Oh My Zsh not found!\033[0m"
    echo -e "Install for enhanced zsh experience:"
    echo -e "  \033[1;34mHomepage:\033[0m https://ohmyz.sh/"
    echo -e "  \033[1;32mInstall:\033[0m sh -c \"\$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\""
    echo ""
    # Continue without oh-my-zsh - provide basic functionality
    export PATH="$HOME/bin:$PATH"
    return 0
fi

# =============================================================================
# ESSENTIAL ENVIRONMENT
# =============================================================================
export ZSH="$HOME/.oh-my-zsh"
export PATH="$HOME/bin:$PATH"

# =============================================================================
# THEME - FASTEST OPTION
# =============================================================================
# robbyrussell is the fastest theme, perfect for tmux performance
ZSH_THEME="robbyrussell"

# =============================================================================
# MINIMAL PLUGINS - ESSENTIAL ONLY
# =============================================================================
# Only plugins that provide significant value without performance impact
plugins=(
    git                    # Essential git aliases - works great with tmux
    colored-man-pages      # Minimal overhead, useful for documentation
)

# =============================================================================
# PERFORMANCE OPTIMIZATIONS
# =============================================================================
# Disable features that slow down shell startup
DISABLE_AUTO_UPDATE="true"         # Manual updates only
DISABLE_UPDATE_PROMPT="true"       # No update prompts
COMPLETION_WAITING_DOTS="false"    # No dots while waiting
DISABLE_MAGIC_FUNCTIONS="true"     # Disable magic functions for speed

# Tmux-specific optimizations (must be set before oh-my-zsh loads)
if [[ -n "$TMUX" ]]; then
    DISABLE_AUTO_TITLE="true"       # Disable auto-title in tmux for performance
fi

# =============================================================================
# LOAD OH-MY-ZSH
# =============================================================================
source $ZSH/oh-my-zsh.sh

# =============================================================================
# POST-LOAD TMUX OPTIMIZATIONS
# =============================================================================
# Override oh-my-zsh defaults that don't work well with tmux
unsetopt CORRECT_ALL               # Only correct commands, not arguments
setopt CORRECT                     # Enable command correction
