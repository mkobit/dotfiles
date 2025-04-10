# Linux specific tmux configuration

# Use xclip for clipboard operations (must be installed)
bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'

# Open new windows and panes in the same directory
bind c new-window -c "#{pane_current_path}"
bind '"' split-window -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"

# Support for xdg-open command
bind-key o run-shell "xdg-open #{pane_current_path}"