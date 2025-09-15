#!/usr/bin/env zsh
# =============================================================================
# BASELINE ZSH PERFORMANCE SETTINGS
# =============================================================================
# Core zsh optimizations focused on fundamentals only

# =============================================================================
# COMPLETION SYSTEM - Minimal, FZF-friendly, non-aggressive
# =============================================================================
# Fast completion initialization with daily cache check
autoload -Uz compinit
if [[ -n ${ZDOTDIR:-$HOME}/.zcompdump(#qN.mh+24) ]]; then
    compinit -d ${ZDOTDIR:-$HOME}/.zcompdump
else
    compinit -C -d ${ZDOTDIR:-$HOME}/.zcompdump
fi

# Completion behavior - minimal and FZF-friendly
setopt COMPLETE_IN_WORD        # Complete from both ends of word
setopt ALWAYS_TO_END           # Move cursor to end after completion
setopt AUTO_LIST               # List choices on ambiguous completion
setopt AUTO_PARAM_SLASH        # Add trailing slash to directory completions
unsetopt AUTO_MENU             # Don't auto-select first completion (show menu instead)
unsetopt MENU_COMPLETE         # Don't auto-insert first completion

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'

# =============================================================================
# VI MODE CONFIGURATION - Optimized for responsiveness
# =============================================================================
bindkey -v  # Enable vi mode

# Reduce ESC timeout for responsive mode switching (10ms)
export KEYTIMEOUT=1

# Better vi mode indicators and bindings
bindkey '^P' up-history
bindkey '^N' down-history
bindkey '^?' backward-delete-char
bindkey '^h' backward-delete-char
bindkey '^w' backward-kill-word
bindkey '^r' history-incremental-search-backward

# =============================================================================
# DIRECTORY NAVIGATION - Essential settings
# =============================================================================
setopt AUTO_CD                 # Change directory without typing cd
setopt AUTO_PUSHD              # Push directories to stack automatically
setopt PUSHD_IGNORE_DUPS       # Don't push duplicate directories
setopt PUSHD_MINUS             # Use - instead of + for directory stack

# =============================================================================
# ERROR CORRECTION - Commands only (not arguments)
# =============================================================================
setopt CORRECT                 # Correct misspelled commands
unsetopt CORRECT_ALL           # Don't correct arguments (less intrusive)

# =============================================================================
# CORE ZSH OPTIONS - Performance and usability focused
# =============================================================================
setopt PROMPT_SUBST            # Allow parameter expansion in prompts
setopt INTERACTIVE_COMMENTS    # Allow comments in interactive shell
setopt MULTIOS                 # Enable multiple redirections
setopt EXTENDED_GLOB           # Enable extended globbing patterns
setopt NULL_GLOB               # Don't error on no glob matches
setopt NO_BEEP                 # Disable beeping
setopt NO_HUP                  # Don't send HUP to background jobs on shell exit
setopt NO_CHECK_JOBS           # Don't warn about running jobs on shell exit

# Disable flow control (Ctrl-S/Ctrl-Q)
unsetopt FLOW_CONTROL
stty -ixon

# =============================================================================
# CROSS-PLATFORM OPTIMIZATIONS
# =============================================================================
case "$(uname -s)" in
    Darwin)
        # macOS specific settings
        export LSCOLORS="ExGxBxDxCxEgEdxbxgxcxd"
        # Enable colors for ls
        alias ls='ls -G'
        ;;
    Linux)
        # Linux settings (includes WSL and SteamOS)
        export LS_COLORS="di=1;34:ln=1;36:so=1;35:pi=1;33:ex=1;32:bd=1;33:cd=1;33:su=1;31:sg=1;31:tw=1;34:ow=1;34"
        # Enable colors for ls
        alias ls='ls --color=auto'

        # WSL-specific optimizations
        if [[ -n "$WSL_DISTRO_NAME" ]]; then
            # Disable problematic WSL features that can slow down zsh
            unsetopt BG_NICE
        fi
        ;;
esac

# =============================================================================
# ESSENTIAL ENVIRONMENT VARIABLES
# =============================================================================
export EDITOR="${EDITOR:-vim}"
export PAGER="${PAGER:-less}"
export LESS="-R"  # Raw color codes in less

# =============================================================================
# BASIC ALIASES - Essential navigation only
# =============================================================================
alias ..='cd ..'
alias ...='cd ../..'
