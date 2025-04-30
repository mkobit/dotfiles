# =============================================
# Windows
# =============================================

# Window indexing starts at 1 (not 0)
# Docs: https://man.openbsd.org/tmux#base-index
set-option -g base-index 1

# Automatically renumber windows when one is closed
# Docs: https://man.openbsd.org/tmux#renumber-windows
set-option -g renumber-windows on

# Enable titles for terminal windows
# Docs: https://man.openbsd.org/tmux#set-titles
set-option -g set-titles on
set-option -g set-titles-string "#I:#W - #{host_short}"

# Window navigation
# Docs: https://man.openbsd.org/tmux#previous-window
bind-key -r C-h previous-window
# Docs: https://man.openbsd.org/tmux#next-window
bind-key -r C-l next-window

# Create new windows in same directory
# Docs: https://man.openbsd.org/tmux#new-window
unbind-key c
bind-key c new-window -c "#{pane_current_path}"

# Window splitting keeps current path
# Docs: https://man.openbsd.org/tmux#split-window
bind-key v split-window -h -c "#{pane_current_path}"
bind-key s split-window -v -c "#{pane_current_path}"

# Make window switching repeatable
# Docs: https://man.openbsd.org/tmux#next-window
bind-key -r n next-window
# Docs: https://man.openbsd.org/tmux#previous-window
bind-key -r p previous-window

# Easy renaming and reset to auto naming
# Docs: https://man.openbsd.org/tmux#command-prompt
bind-key r command-prompt -I "#{window_name}" "rename-window '%%'"
# Docs: https://man.openbsd.org/tmux#automatic-rename
bind-key R set-window-option automatic-rename on \; display-message "Auto rename restored"

# Shift+Arrow for window navigation without prefix
# Docs: https://man.openbsd.org/tmux#previous-window
bind-key -n S-Left previous-window
# Docs: https://man.openbsd.org/tmux#next-window
bind-key -n S-Right next-window

# Easier window rearrangement (requires tmux >= 3.0)
# Docs: https://man.openbsd.org/tmux#swap-window
bind-key -n C-S-Left swap-window -t -1\; select-window -t -1
bind-key -n C-S-Right swap-window -t +1\; select-window -t +1
