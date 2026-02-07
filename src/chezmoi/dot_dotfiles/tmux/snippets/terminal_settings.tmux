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

# =============================================
# Advanced Terminal Capabilities
# =============================================
# Allow pass-through of escape sequences (e.g. for images)
# Docs: https://man.openbsd.org/tmux#allow-passthrough
set -g allow-passthrough on

# Enable external clipboard (OSC 52)
# Docs: https://man.openbsd.org/tmux#set-clipboard
set -s set-clipboard on

# Explicitly define Ms capability for OSC 52 clipboard access
# This ensures tmux can copy to the system clipboard via the terminal
# Docs: https://github.com/sunaku/home/blob/master/.tmux.conf.erb
set-option -ga terminal-overrides ',xterm*:Ms=\E]52;c;%p2%s\007'
set-option -ga terminal-overrides ',xterm-kitty:Ms=\E]52;c;!\007\E]52;c;%p2%s\007'
set-option -ga terminal-overrides ',screen*:Ms=\E]52;c;%p2%s\007'
