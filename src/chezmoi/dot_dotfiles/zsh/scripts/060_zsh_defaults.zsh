#!/usr/bin/env zsh

# =============================================================================
# GENERAL ZSH OPTIMIZATIONS AND SETTINGS
# =============================================================================

# Command correction
unsetopt CORRECT_ALL               # Only correct commands, not arguments
setopt CORRECT                     # Enable command correction

# Vi mode bindings
bindkey -v                         # Enable vi mode
export KEYTIMEOUT=1                # Fast ESC timeout for vi mode

# Enable bash completion compatibility
autoload -U +X bashcompinit && bashcompinit
