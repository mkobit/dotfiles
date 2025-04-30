# =============================================
# Universal settings
# =============================================

# Set Ctrl-a as the default prefix and unbind C-b
# Docs: https://man.openbsd.org/tmux#prefix
unbind-key C-b
set-option -g prefix C-a

# Allow sending prefix key (Ctrl-a) to applications running inside tmux by pressing it twice
# Docs: https://man.openbsd.org/tmux#send-prefix
bind-key C-a send-prefix

# Make sure special keys work consistently across different terminal types
# Docs: https://man.openbsd.org/tmux#xterm-keys
set-option -g xterm-keys on

# Better handling of escape sequences for function and other special keys
# Check for extended keys feature (tmux 3.2+)
# Docs: https://man.openbsd.org/tmux#extended-keys
if-shell "tmux -V | awk '{split($2,a,\".\")} a[1] > 3 || (a[1] == 3 && a[2] >= 2)'" {
    set-option -s extended-keys on
    set-option -a -s terminal-features 'xterm*:extkeys'
}

# Reload configuration (changed to a more exotic key combination since it's used less frequently)
# Docs: https://man.openbsd.org/tmux#source-file
bind-key M-r source-file ${HOME}/.tmux.conf \; display-message "Reloaded ~/.tmux.conf"
