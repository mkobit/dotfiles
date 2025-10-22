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
# Note: vi mode and KEYTIMEOUT are now set in oh-my-zsh.zsh after oh-my-zsh loads
# This ensures oh-my-zsh doesn't override our vi mode preference

# =============================================================================
# TODO: HOLISTIC KEYBINDING STRATEGY
# =============================================================================
# Need to design a unified keybinding strategy that works seamlessly across:
# macOS -> iTerm2 -> tmux -> zsh -> vim workflow
#
# CURRENT KEYBINDINGS TO EVALUATE:
# - bindkey '^P' up-history                    # Ctrl-P: previous command
# - bindkey '^N' down-history                  # Ctrl-N: next command
# - bindkey '^?' backward-delete-char          # Backspace in vi mode
# - bindkey '^h' backward-delete-char          # Ctrl-H: backspace
# - bindkey '^w' backward-kill-word            # Ctrl-W: delete word
# - Ctrl-R (FZF history search) - ESTABLISHED
# - Ctrl-T (FZF file search) - ESTABLISHED
# - Alt-C (FZF directory search) - ESTABLISHED
#
# ENVIRONMENTS TO SUPPORT:
# Primary: macOS + iTerm2 + tmux + zsh + vim
# Secondary: Linux + terminal + tmux + zsh + vim
# Tertiary: WSL + Windows Terminal + tmux + zsh + vim
# Edge case: VS Code integrated terminal
#
# KEY BINDING LAYER ANALYSIS:
#
# 1. SYSTEM LAYER (OS intercepts first)
#    macOS: Cmd+anything goes to system
#    Linux: Alt+F4, Super+anything goes to system
#    Windows: Win+anything, Alt+F4 goes to system
#
# 2. TERMINAL EMULATOR LAYER (app intercepts next)
#    iTerm2: Cmd+D (split), Cmd+T/W (tab), Cmd+1-9 (tab switch)
#    iTerm2: Alt+Cmd+Arrow (pane nav), Cmd+; (autocomplete)
#    Terminal.app: Similar Cmd+* patterns
#    VS Code: Ctrl+` (toggle terminal), Ctrl+Shift+` (new terminal)
#
# 3. TMUX LAYER (if running)
#    Default prefix: Ctrl-B
#    Common custom: Ctrl-A
#    Safe area: Anything not using the prefix
#    Copy mode: Prefix+[ enters vi-style navigation
#
# 4. SHELL LAYER (zsh vi mode)
#    ESC: Enter vi command mode
#    Insert mode: Need emacs-style bindings for efficiency
#    Command mode: Full vi bindings available
#
# 5. EDITOR LAYER (vim/nvim)
#    All vim bindings when in editor
#    Terminal vim vs. GUI vim considerations
#
# DESIGN PRINCIPLES:
#
# 1. CONSISTENCY: Same key does same thing across contexts where possible
# 2. NON-INTERFERENCE: Don't break existing muscle memory
# 3. DISCOVERABILITY: Logical patterns that are easy to remember
# 4. ESCAPE HATCHES: Always a way to get out of any mode
# 5. PERFORMANCE: Minimal latency, no key sequence delays
#
# PROPOSED UNIFIED STRATEGY:
#
# TIER 1 - ESSENTIAL (implement first):
# - Keep existing FZF bindings (Ctrl-R, Ctrl-T, Alt-C) - WORKING
# - Standard history navigation (up/down arrows) - DEFAULT
# - Basic editing (backspace, delete) - DEFAULT
#
# TIER 2 - ENHANCED NAVIGATION (implement after testing):
# - Word movement: Need to find conflict-free keys
# - Line movement: Need to find conflict-free keys
# - Quick editing: Kill word, kill line, etc.
#
# TIER 3 - ADVANCED (nice to have):
# - Vim-style text objects in command line
# - Integration with tmux copy mode
# - Context-aware bindings (different in/out of tmux)
#
# TESTING METHODOLOGY:
#
# 1. Map current iTerm2 keybindings (Preferences > Keys)
# 2. Test each proposed binding in: bare terminal -> tmux -> zsh -> vim
# 3. Verify no conflicts with common workflows
# 4. Test across all supported environments
# 5. Document any environment-specific configuration needed
#
# IMPLEMENTATION PHASES:
#
# Phase 1: Audit current conflicts and remove problematic bindings
# Phase 2: Establish core safe bindings that work everywhere
# Phase 3: Add enhanced bindings with proper conflict detection
# Phase 4: Create environment-specific optimizations
#
# DECISION CRITERIA:
#
# - If a key conflicts in ANY supported environment, don't use it
# - Prefer Ctrl over Alt (less likely to conflict with terminal emulators)
# - Prefer function keys over modified keys (but less ergonomic)
# - Consider user-configurable bindings for advanced users
# - Always provide escape hatches and alternatives
#
# Once this analysis is complete, implement the safest subset first,
# then gradually add more advanced features with proper testing.

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
