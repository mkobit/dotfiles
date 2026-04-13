#!/usr/bin/env zsh

# =============================================================================
# Zsh vi mode enhancements
# Must run after bindkey -v (060_zsh_defaults.zsh).
# =============================================================================

# Cursor shape: beam in insert mode, block in normal mode.
# Same visual language as terminal vim — you always know which mode you're in.
# Uses VT escape sequences supported by Ghostty, iTerm2, and most modern terminals.
function _zle_vi_mode_cursor() {
    case $KEYMAP in
        vicmd)      print -n '\e[2 q' ;;  # block
        viins|main) print -n '\e[6 q' ;;  # beam
    esac
}
zle -N zle-keymap-select _zle_vi_mode_cursor
zle -N zle-line-init      _zle_vi_mode_cursor
