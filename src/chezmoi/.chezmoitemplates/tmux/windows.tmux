# =============================================
# Windows
# =============================================

# Window indexing starts at 1 (not 0)
set-option -g base-index 1

# Automatically renumber windows when one is closed
set-option -g renumber-windows on

# Enable titles for terminal windows
set-option -g set-titles on
set-option -g set-titles-string "#I:#W - #{host_short}"

# Create new windows in same directory
unbind-key c
bind-key c new-window -c "#{pane_current_path}"

# Window splitting keeps current path
bind-key v split-window -h -c "#{pane_current_path}"
bind-key s split-window -v -c "#{pane_current_path}"

# Window navigation
# Docs: https://man.openbsd.org/tmux#previous-window
bind-key -r C-h previous-window
# Docs: https://man.openbsd.org/tmux#next-window
bind-key -r C-l next-window

# Easier window rearrangement
# Docs: https://man.openbsd.org/tmux#swap-window
bind-key -n C-S-Left swap-window -t -1\; select-window -t -1
bind-key -n C-S-Right swap-window -t +1\; select-window -t +1

# Window naming managed by tmux-powerline theme
# Docs: https://man.openbsd.org/tmux#automatic-rename
set-window-option -g automatic-rename on
# Allow external programs to rename windows (required for tmux-powerline)
# Docs: https://man.openbsd.org/tmux#allow-rename
set-window-option -g allow-rename on

# Disable automatic renaming when a window is manually renamed
# This ensures custom names are preserved
bind-key , command-prompt -p "(rename-window '#W')" "rename-window '%%'; set-window-option automatic-rename off"


# Quick window switching with Meta (Alt) + Number (without prefix)
# This allows instantly jumping to a specific window
# Docs: https://man.openbsd.org/tmux#select-window
bind-key -n M-1 select-window -t 1
bind-key -n M-2 select-window -t 2
bind-key -n M-3 select-window -t 3
bind-key -n M-4 select-window -t 4
bind-key -n M-5 select-window -t 5
bind-key -n M-6 select-window -t 6
bind-key -n M-7 select-window -t 7
bind-key -n M-8 select-window -t 8
bind-key -n M-9 select-window -t 9
