# Generic fallback tmux configuration

# Default clipboard operations without system integration
bind-key -T copy-mode-vi 'y' send-keys -X copy-selection
bind-key -T copy-mode-vi Enter send-keys -X copy-selection
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-selection

# Open new windows and panes in the same directory
bind c new-window -c "#{pane_current_path}"
bind '"' split-window -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"