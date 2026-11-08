# =============================================================================
# MULTIPLEXER-AWARE ZSH PERFORMANCE SETTINGS
# =============================================================================
# Settings that oh-my-zsh doesn't handle or that need multiplexer-specific optimization

# =============================================================================
# TMUX-CRITICAL HISTORY SETTINGS
# =============================================================================
# Large history with immediate cross-session sharing (essential for tmux)
export HISTSIZE=100000
export SAVEHIST=100000

# CRITICAL: These ensure history is shared across all tmux panes/windows immediately
# INC_APPEND_HISTORY writes to history immediately, not on shell exit
# SHARE_HISTORY shares history between all sessions (tmux essential)
# HIST_VERIFY shows command with history expansion before running
# Advanced history deduplication (oh-my-zsh doesn't set these)
# HIST_EXPIRE_DUPS_FIRST expires duplicate entries first when trimming
# HIST_IGNORE_ALL_DUPS deletes old entry if new entry is duplicate
# HIST_FIND_NO_DUPS hides duplicates when searching
# HIST_SAVE_NO_DUPS does not write duplicate entries to history file
{{- if eq .shell "zsh" }}
setopt INC_APPEND_HISTORY
setopt SHARE_HISTORY
setopt HIST_VERIFY
setopt HIST_EXPIRE_DUPS_FIRST
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS
{{- end }}

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
{{- if eq .shell "zsh" }}
unsetopt FLOW_CONTROL
{{- end }}
[[ -t 0 ]] && stty -ixon

# Speed up job control for tmux environments
# NO_HUP does not send HUP to background jobs on shell exit
# NO_CHECK_JOBS does not warn about running jobs on shell exit
# NO_BEEP disables beeping (annoying in tmux)
{{- if eq .shell "zsh" }}
setopt NO_HUP
setopt NO_CHECK_JOBS
setopt NO_BEEP
{{- end }}

# =============================================================================
# COMPLETION OPTIMIZATIONS (oh-my-zsh doesn't optimize these)
# =============================================================================
# FZF-friendly completion behavior
# AUTO_MENU off: do not auto-select first completion (better for fzf)
# MENU_COMPLETE off: do not auto-insert first completion
# AUTO_LIST lists choices on ambiguous completion
{{- if eq .shell "zsh" }}
unsetopt AUTO_MENU
unsetopt MENU_COMPLETE
setopt AUTO_LIST
{{- end }}

# =============================================================================
# TERMINAL OPTIMIZATIONS FOR NESTED ENVIRONMENTS
# =============================================================================
# Detect which multiplexer (if any) we are inside and set TERM appropriately.
# tmux needs tmux-256color for full feature support (italics, true color, etc.).
# zellij manages its own TERM (xterm-256color); do not override it.
if [[ -n "$TMUX" ]]; then
    export TERM="tmux-256color"
    DISABLE_AUTO_TITLE="true"
    {{- if eq .shell "zsh" }}
    setopt PROMPT_SUBST
    {{- end }}
elif [[ -n "$ZELLIJ" ]]; then
    # zellij sets xterm-256color; leave TERM alone and just suppress auto-title
    DISABLE_AUTO_TITLE="true"
    {{- if eq .shell "zsh" }}
    setopt PROMPT_SUBST
    {{- end }}
else
    case "$TERM_PROGRAM" in
        "iTerm.app")
            export ITERM_ENABLE_SHELL_INTEGRATION_WITH_TMUX=YES
            ;;
        "vscode")
            export TERM="xterm-256color"
            ;;
    esac
fi

# =============================================================================
# CROSS-PLATFORM TMUX CONSIDERATIONS
# =============================================================================
case "$(uname -s)" in
    Darwin)
        # macOS + multiplexer optimizations
        # Fix clipboard integration in multiplexers
        if [[ -n "$TMUX" ]] && command -v pbcopy >/dev/null 2>&1; then
            alias pbcopy='tmux save-buffer -'
            alias pbpaste='tmux show-buffer'
        elif [[ -n "$ZELLIJ" ]] && command -v pbcopy >/dev/null 2>&1; then
            # Zellij handles clipboard natively via OSC52 when configured,
            # or we just use normal pbcopy/pbpaste
            :
        fi
        ;;
    Linux)
        # Linux + multiplexer optimizations (WSL, SteamOS)
        if [[ -n "$WSL_DISTRO_NAME" && ( -n "$TMUX" || -n "$ZELLIJ" ) ]]; then
            # WSL + multiplexer: disable problematic features
            {{- if eq .shell "zsh" }}
            unsetopt BG_NICE
            {{- end }}
            export LIBGL_ALWAYS_INDIRECT=1
        fi
        ;;
esac

# =============================================================================
# ESSENTIAL NAVIGATION (tmux workflow focused)
# =============================================================================
# Quick directory navigation (complement to zoxide)
# AUTO_CD changes directory without typing cd
# AUTO_PUSHD pushes directories to stack automatically
# PUSHD_IGNORE_DUPS does not push duplicate directories
{{- if eq .shell "zsh" }}
setopt AUTO_CD
setopt AUTO_PUSHD
setopt PUSHD_IGNORE_DUPS
{{- else if eq .shell "bash" }}
shopt -s autocd
{{- end }}
