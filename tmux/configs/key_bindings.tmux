# =============================================
# Key Bindings
# =============================================
# Set Ctrl-a as the default prefix and unbind C-b
# Docs: https://man.openbsd.org/tmux#prefix
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# Make sure special keys work consistently across different terminal types
set -g xterm-keys on

# Better handling of escape sequences for function and other special keys
# Check for extended keys feature (tmux 3.2+)
if-shell "tmux -V | awk '{split($2,a,\".\")} a[1] > 3 || (a[1] == 3 && a[2] >= 2)'" {
    set -s extended-keys on
    set -as terminal-features 'xterm*:extkeys'
}

# Reload configuration (changed to a more exotic key combination since it's used less frequently)
# Docs: https://man.openbsd.org/tmux#source-file
bind M-r source-file ${HOME}/.tmux.conf \; display "Reloaded ~/.tmux.conf"

# Window management
unbind-key c
bind-key c new-window -c "#{pane_current_path}"

# Split panes using | and - (more intuitive than % and ")
unbind '"'
unbind %
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Quick window navigation
bind-key a last-window

# Window renaming - more accessible than default (prefix + ,)
# Using 'A' (capital a) for renAme instead of 'R' to avoid conflicts
bind-key A command-prompt -I "#W" "rename-window '%%'"
bind-key C-a send-prefix  # Preserve the send-prefix functionality

# Vim-like pane navigation
unbind-key j
bind-key j select-pane -D
unbind-key k
bind-key k select-pane -U
unbind-key h
bind-key h select-pane -L
unbind-key l
bind-key l select-pane -R

# Alt+Arrow keys for pane navigation without prefix
bind -n M-Left select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up select-pane -U
bind -n M-Down select-pane -D

# Shift+Arrow for window navigation without prefix
bind -n S-Left previous-window
bind -n S-Right next-window

# Easier window rearrangement (requires tmux >= 3.0)
bind-key -n C-S-Left swap-window -t -1\; select-window -t -1
bind-key -n C-S-Right swap-window -t +1\; select-window -t +1

# Vim-style resizing
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5
