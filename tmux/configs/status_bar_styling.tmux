# =============================================
# Status bar styling
# =============================================

set -g automatic-rename-format '#{?#{||:#{==:#{pane_current_command},bash},#{==:#{pane_current_command},zsh}},#{b:pane_current_path},#{=15:pane_current_command}}'

# Make sure automatic renaming is enabled by default
set -w -g automatic-rename on
set -w -g allow-rename on

set -g status-style "bg=#2e3440,fg=#d8dee9"

# Default window title colors
set -g window-status-style "fg=#81a1c1,bg=#2e3440"

# Active window title colors
set -g window-status-current-style "fg=#2e3440,bg=#88c0d0,bold"

# Pane border colors
set -g pane-border-style "fg=#4c566a"
set -g pane-active-border-style "fg=#88c0d0"

# Message text colors
set -g message-style "fg=#eceff4,bg=#3b4252,bold"

# Status left section - simple but informative
set -g status-left-length 30
set -g status-left "#{?client_prefix,#[fg=#2e3440]#[bg=#bf616a]#[bold],#[fg=#2e3440]#[bg=#88c0d0]#[bold]} #S #[fg=#88c0d0]#[bg=#2e3440]"

# Enhanced window status formats with clearer numbering for easier window switching
# Make window numbers more prominent for quick navigation with prefix+number
set -g window-status-format " #[fg=#81a1c1,bold]#I#[fg=#81a1c1,nobold]:#[fg=#d8dee9]#{window_name}#{?#{m:*ssh*,#{pane_current_command}}, [SSH],}#{?window_zoomed_flag, 🔍,} "
set -g window-status-current-format " #[fg=#2e3440,bg=#88c0d0,bold]#I#[fg=#2e3440]:#[fg=#2e3440,bold]#{window_name}#{?#{m:*ssh*,#{pane_current_command}}, [SSH],}#{?window_zoomed_flag, 🔍,} "

# Status right section with system info
set -g status-right-length 50
set -g status-right "#[fg=#4c566a,bg=#2e3440]#[fg=#e5e9f0,bg=#4c566a] %H:%M #{?window_zoomed_flag,Z ,}#[fg=#88c0d0,bg=#4c566a]#[fg=#2e3440,bg=#88c0d0,bold] #h "

# Simple window status formats with SSH highlighting
set -g window-status-format " #I:#W #{?#{m:*ssh*,#{pane_current_command}},#[fg=#bf616a]SSH#[fg=#81a1c1],}#{?window_zoomed_flag, 🔍,} "
set -g window-status-current-format " #I:#W #{?#{m:*ssh*,#{pane_current_command}},#[fg=#bf616a]SSH,}#{?window_zoomed_flag, 🔍,} "
set -g window-status-separator ""

# When explicitly renaming a window, disable automatic renaming
set-hook -g after-rename-window 'set-window-option automatic-rename off'
