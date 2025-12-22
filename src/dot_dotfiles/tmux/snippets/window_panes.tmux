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

# Note: Do NOT enable Option/Alt+Arrow keys (M-Left/Right/Up/Down) for pane navigation.
# These bindings conflict with standard shell word-wise navigation (Option+Left/Right).

# Vim-style resizing
# Docs: https://man.openbsd.org/tmux#resize-pane
bind-key -r H resize-pane -L 5
bind-key -r J resize-pane -D 5
bind-key -r K resize-pane -U 5
bind-key -r L resize-pane -R 5

# Smart vim/nvim-aware navigation - handles both vim and neovim
is_vim="ps -o state= -o comm= -t '#{pane_tty}' | grep -iqE '^[^TXZ ]+ +(\\S+\\/)?g?n?(view|vim|nvim)(diff)?$'"

# Enhanced pane display with longer timeout and better colors
set-option -g display-panes-time 4000
set-option -g display-panes-active-colour "#88c0d0"
set-option -g display-panes-colour "#4c566a"

# Additional non-conflicting session shortcuts using function keys
bind-key F1 switch-client -t 1
bind-key F2 switch-client -t 2
bind-key F3 switch-client -t 3
bind-key F4 switch-client -t 4
bind-key F5 switch-client -t 5
