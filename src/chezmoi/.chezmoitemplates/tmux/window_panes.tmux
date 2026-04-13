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
unbind-key '"'
unbind-key %
bind-key | split-window -h -c "#{pane_current_path}"
bind-key - split-window -v -c "#{pane_current_path}"

# Smart editor/tmux pane switching (Seamless Navigation)
# Docs: https://man.openbsd.org/tmux#bind-key
# Docs: https://man.openbsd.org/tmux#if-shell
# This allows using Ctrl+h/j/k/l to switch panes seamlessly, passing keys to editor if active.
is_editor="#{||:#{m:*vim*,#{pane_current_command}},#{m:*nvim*,#{pane_current_command}}}"
bind-key -n 'C-h' if-shell -F "$is_editor" 'send-keys C-h'  'select-pane -L'
bind-key -n 'C-j' if-shell -F "$is_editor" 'send-keys C-j'  'select-pane -D'
bind-key -n 'C-k' if-shell -F "$is_editor" 'send-keys C-k'  'select-pane -U'
bind-key -n 'C-l' if-shell -F "$is_editor" 'send-keys C-l'  'select-pane -R'

bind-key -T copy-mode-vi 'C-h' select-pane -L
bind-key -T copy-mode-vi 'C-j' select-pane -D
bind-key -T copy-mode-vi 'C-k' select-pane -U
bind-key -T copy-mode-vi 'C-l' select-pane -R

# Note: Do NOT enable Option/Alt+Arrow keys (M-Left/Right/Up/Down) for pane navigation.
# These bindings conflict with standard shell word-wise navigation (Option+Left/Right).

# Vim-style resizing
# Docs: https://man.openbsd.org/tmux#resize-pane
bind-key -r H resize-pane -L 5
bind-key -r J resize-pane -D 5
bind-key -r K resize-pane -U 5
bind-key -r L resize-pane -R 5

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
