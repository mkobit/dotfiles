# WSL specific tmux configuration

# Use clip.exe for clipboard operations (for WSL integration with Windows)
bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel '/mnt/c/Windows/System32/clip.exe'
bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel '/mnt/c/Windows/System32/clip.exe'
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel '/mnt/c/Windows/System32/clip.exe'

# Open new windows and panes in the same directory
bind c new-window -c "#{pane_current_path}"
bind '"' split-window -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"

# Support for Windows Explorer integration
bind-key o run-shell "explorer.exe `wslpath -w #{pane_current_path}`"