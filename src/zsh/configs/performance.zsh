#!/usr/bin/env zsh
# =============================================================================
# TMUX-OPTIMIZED ZSH PERFORMANCE SETTINGS
# =============================================================================
# Settings that oh-my-zsh doesn't handle or that need tmux-specific optimization

# =============================================================================
# TMUX-CRITICAL HISTORY SETTINGS
# =============================================================================
# Large history with immediate cross-session sharing (essential for tmux)
export HISTSIZE=100000
export SAVEHIST=100000

# CRITICAL: These ensure history is shared across all tmux panes/windows immediately
setopt INC_APPEND_HISTORY      # Write to history immediately, not on shell exit
setopt SHARE_HISTORY           # Share history between all sessions (tmux essential)
setopt HIST_VERIFY             # Show command with history expansion before running

# Advanced history deduplication (oh-my-zsh doesn't set these)
setopt HIST_EXPIRE_DUPS_FIRST  # Expire duplicate entries first when trimming
setopt HIST_IGNORE_ALL_DUPS    # Delete old entry if new entry is duplicate
setopt HIST_FIND_NO_DUPS       # Don't display duplicates when searching
setopt HIST_SAVE_NO_DUPS       # Don't write duplicate entries to history file

# =============================================================================
# VI MODE - TMUX OPTIMIZED
# =============================================================================
bindkey -v  # Enable vi mode

# CRITICAL: Fast ESC timeout for vi mode in tmux (oh-my-zsh default is too slow)
export KEYTIMEOUT=1

# Tmux-friendly vi mode bindings (avoid conflicts with tmux prefix)
bindkey '^P' up-history                    # Ctrl-P: previous command
bindkey '^N' down-history                  # Ctrl-N: next command
bindkey '^?' backward-delete-char          # Backspace in vi mode
bindkey '^h' backward-delete-char          # Ctrl-H: backspace
bindkey '^w' backward-kill-word            # Ctrl-W: delete word (tmux-safe)
# Note: Ctrl-R handled by fzf for fuzzy history search

# =============================================================================
# TMUX PERFORMANCE OPTIMIZATIONS
# =============================================================================
# Disable flow control (essential for tmux - Ctrl-S/Ctrl-Q conflicts)
unsetopt FLOW_CONTROL
stty -ixon

# Speed up job control for tmux environments
setopt NO_HUP                  # Don't send HUP to background jobs on shell exit
setopt NO_CHECK_JOBS           # Don't warn about running jobs on shell exit
setopt NO_BEEP                 # Disable beeping (annoying in tmux)

# =============================================================================
# COMPLETION OPTIMIZATIONS (oh-my-zsh doesn't optimize these)
# =============================================================================
# FZF-friendly completion behavior
unsetopt AUTO_MENU             # Don't auto-select first completion (better for fzf)
unsetopt MENU_COMPLETE         # Don't auto-insert first completion
setopt AUTO_LIST               # List choices on ambiguous completion

# =============================================================================
# TERMINAL OPTIMIZATIONS FOR NESTED ENVIRONMENTS
# =============================================================================
# Detect if we're in tmux and optimize accordingly
if [[ -n "$TMUX" ]]; then
    # In tmux - optimize for performance over features
    export TERM="screen-256color"

    # Disable some oh-my-zsh features that slow down tmux
    DISABLE_AUTO_TITLE="true"

    # Faster prompt updates in tmux
    setopt PROMPT_SUBST
else
    # Not in tmux - can afford slightly more features
    case "$TERM_PROGRAM" in
        "iTerm.app")
            # iTerm2 optimizations
            export ITERM_ENABLE_SHELL_INTEGRATION_WITH_TMUX=YES
            ;;
        "vscode")
            # VS Code terminal optimizations
            export TERM="xterm-256color"
            ;;
    esac
fi

# =============================================================================
# CROSS-PLATFORM TMUX CONSIDERATIONS
# =============================================================================
case "$(uname -s)" in
    Darwin)
        # macOS + tmux optimizations
        # Fix clipboard integration in tmux
        if [[ -n "$TMUX" ]] && command -v pbcopy >/dev/null 2>&1; then
            alias pbcopy='tmux save-buffer -'
            alias pbpaste='tmux show-buffer'
        fi
        ;;
    Linux)
        # Linux + tmux optimizations (WSL, SteamOS)
        if [[ -n "$WSL_DISTRO_NAME" && -n "$TMUX" ]]; then
            # WSL + tmux: disable problematic features
            unsetopt BG_NICE
            export LIBGL_ALWAYS_INDIRECT=1
        fi
        ;;
esac

# =============================================================================
# ESSENTIAL NAVIGATION (tmux workflow focused)
# =============================================================================
# Quick directory navigation (complement to zoxide)
setopt AUTO_CD                 # Change directory without typing cd
setopt AUTO_PUSHD              # Push directories to stack automatically
setopt PUSHD_IGNORE_DUPS       # Don't push duplicate directories
