# macOS specific tmux configuration

# Enable macOS clipboard integration
set-option -g default-command "reattach-to-user-namespace -l zsh"

# Use pbcopy/pbpaste for clipboard operations
bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'pbcopy'
bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'pbcopy'
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel 'pbcopy'

# Open new windows and panes in the same directory
bind c new-window -c "#{pane_current_path}"
bind '"' split-window -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"

# Support for macOS open command
bind-key o run-shell "open #{pane_current_path}"