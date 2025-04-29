# =============================================
# Window Configuration
# =============================================
# Window indexing starts at 1 (not 0)
set -g base-index 1
set-window-option -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Enable titles
set -g set-titles on
set -g set-titles-string "#I:#W - #{host_short}"

# Window navigation
bind -r C-h previous-window
bind -r C-l next-window

# Create new windows in same directory
bind c new-window -c "#{pane_current_path}"

# Window splitting keeps current path
bind v split-window -h -c "#{pane_current_path}"
bind s split-window -v -c "#{pane_current_path}"

# Make window switching repeatable
bind -r n next-window
bind -r p previous-window

# Easy renaming and reset to auto naming
bind r command-prompt -I "#{window_name}" "rename-window '%%'"
bind R set-window-option automatic-rename on \; display-message "Auto rename restored"

# Reorder windows
bind < swap-window -t -1
bind > swap-window -t +1