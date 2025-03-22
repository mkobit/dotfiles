# tmux configuration file
# {{generated_notice}}

# Set default terminal
set -g default-terminal "screen-256color"

# Set prefix
set -g prefix C-a
unbind C-b
bind C-a send-prefix

# Reload config
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Split panes
bind | split-window -h
bind - split-window -v

# Move between panes
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Resize panes
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Mouse mode
setw -g mouse on

# Set window notifications
setw -g monitor-activity on
set -g visual-activity on

# Start window numbering at 1
set -g base-index 1
setw -g pane-base-index 1

# Status bar
set -g status-style fg=white,bg=black
setw -g window-status-style fg=cyan,bg=black
setw -g window-status-current-style fg=white,bold,bg=red

# Platform-specific settings
{{platform_specific_settings}}

# Include local configuration
if-shell "[ -f ~/.tmux.conf.local ]" "source ~/.tmux.conf.local"