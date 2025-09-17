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
# POST-LOAD OPTIMIZATIONS
# =============================================================================
# Override oh-my-zsh defaults that don't work well with tmux
unsetopt CORRECT_ALL               # Only correct commands, not arguments
setopt CORRECT                     # Enable command correction

# CRITICAL: Set vi mode AFTER oh-my-zsh loads (oh-my-zsh resets to emacs mode)
bindkey -v                         # Enable vi mode (must be after oh-my-zsh)
export KEYTIMEOUT=1                # Fast ESC timeout for vi mode
