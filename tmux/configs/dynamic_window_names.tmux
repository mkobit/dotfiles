# =============================================
# Dynamic Window Naming
# =============================================
# Show directory basename for shell windows, and truncated command for other windows
# User-set names will take precedence (they disable automatic renaming)
set -g automatic-rename-format '#{?#{||:#{==:#{pane_current_command},bash},#{==:#{pane_current_command},zsh}},#{b:pane_current_path},#{=15:pane_current_command}}'

# Make sure automatic renaming is enabled by default
set -w -g automatic-rename on
set -w -g allow-rename on

# When explicitly renaming a window, disable automatic renaming
set-hook -g after-rename-window 'set-window-option -t "#{window_id}" automatic-rename off'

# Simple toggle for automatic renaming
bind-key C-n set-window-option automatic-rename \; display-message "Auto rename: #{?automatic-rename,on,off}"