# =============================================
# Advanced Features (No Plugins Required)
# =============================================

# Configure activity monitoring with visual indicators but no messages
# This highlights the window name until you view it
setw -g monitor-activity on
set -g visual-activity off  # No messages for activity
set -g activity-action other  # Only mark windows that aren't current

# Bell notifications
set -g visual-bell off
set -g bell-action any

# Status bar indicators - highlight activity in windows with color
# Window title formats with activity highlighting
setw -g window-status-activity-style "fg=#bf616a,bg=#2e3440,bold"

# Show bell events in status line
set -ag status-right "#[fg=#b48ead,bg=#2e3440]#{?window_bell_flag, Bell ,}"

# Improved popups in tmux >= 3.2
if-shell -b '[ "$(echo "$(tmux -V | cut -d" " -f2) >= 3.2" | bc)" = 1 ]' {
  # Display popup with available sessions to switch to
  bind-key C-j display-popup -E "tmux list-sessions | sed -E 's/:.*$//' | grep -v \"^$(tmux display-message -p '#S')$\" | fzf --reverse | xargs tmux switch-client -t"

  # Show a clock in a popup
  bind-key C-t display-popup -E "date; sleep 1"
}

# Automatically renumber windows when one is closed
set -g renumber-windows on

# Set a larger history limit
set -g history-limit 50000

# Activity indication settings (window titles change color until viewed)
setw -g monitor-activity on
set -g visual-activity off
set -g activity-action other

# Pane indicators - display pane numbers for 2 seconds
set -g display-panes-time 2000