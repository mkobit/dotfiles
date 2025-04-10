# Windows specific tmux configuration

# Windows clipboard operations depend on how tmux was installed
# This assumes tmux is running via a Unix-like environment on Windows (MSYS2, Cygwin, etc.)

# Terminal and color settings for Windows
set -g default-terminal "screen-256color"

# Open new windows and panes in the same directory
bind c new-window -c "#{pane_current_path}"
bind '"' split-window -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"

# Support for Windows Explorer
bind-key o run-shell "start #{pane_current_path}"