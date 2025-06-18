# =============================================
# Pane settings and key bindings
# =============================================

# Set vi-style key bindings for copy mode
# Docs: https://man.openbsd.org/tmux#mode-keys
set-window-option -g mode-keys vi

# Pane indexing starts at 1 (for consistency with windows)
# Docs: https://man.openbsd.org/tmux#pane-base-index
set-window-option -g pane-base-index 1

# Pane indicators - display pane numbers for 2 seconds
# Docs: https://man.openbsd.org/tmux#display-panes-time
set-option -g display-panes-time 2000

# Split panes using | and - (and remove unintuitive bindings of % and ")
# Docs: https://man.openbsd.org/tmux#split-window
unbind '"'
unbind %
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Vim-like pane navigation
# Docs: https://man.openbsd.org/tmux#select-pane
unbind-key j
bind-key j select-pane -D
unbind-key k
bind-key k select-pane -U
unbind-key h
bind-key h select-pane -L
unbind-key l
bind-key l select-pane -R

# Option/Alt+Arrow keys for pane navigation without prefix
# Docs: https://man.openbsd.org/tmux#select-pane
bind-key -n M-Left select-pane -L
bind-key -n M-Right select-pane -R
bind-key -n M-Up select-pane -U
bind-key -n M-Down select-pane -D

# Vim-style resizing
# Docs: https://man.openbsd.org/tmux#resize-pane
bind-key -r H resize-pane -L 5
bind-key -r J resize-pane -D 5
bind-key -r K resize-pane -U 5
bind-key -r L resize-pane -R 5
