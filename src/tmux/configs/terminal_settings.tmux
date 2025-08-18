# =============================================
# Terminal Settings
# =============================================
# Use tmux-256color if available, otherwise screen-256color
# Docs: https://man.openbsd.org/tmux#default-terminal
if-shell "infocmp tmux-256color" {
    set -g default-terminal "tmux-256color"
    set -ga terminal-overrides ",tmux-256color:Tc"
} {
    set -g default-terminal "screen-256color"
    set -ga terminal-overrides ",screen-256color:Tc"
}

# Fix backspace and delete key issues across different terminals
# Docs: https://man.openbsd.org/tmux#assume-paste-time
set-option -g assume-paste-time 1

# Explicitly set the terminal support for special keys
# Docs: https://man.openbsd.org/tmux#terminal-overrides
set-option -g -a terminal-overrides "*:kbs=\\177"   # Fix backspace
set-option -g -a terminal-overrides "*:khome=\\033[1~"  # Fix home key
set-option -g -a terminal-overrides "*:kend=\\033[4~"   # Fix end key

# Enable focus events for better integration with vim and other programs
# Docs: https://man.openbsd.org/tmux#focus-events
set-option -g focus-events on
