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

# Enable focus events for better integration with vim and other programs
# Docs: https://man.openbsd.org/tmux#focus-events
set-option -g focus-events on
