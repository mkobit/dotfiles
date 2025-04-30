# =============================================
# Activity and bell notifications
# =============================================

# Configure activity monitoring with visual indicators but no messages
# This highlights the window name until you view it
# See: https://man.openbsd.org/tmux#monitor-activity
set-window-option -g monitor-activity on

# See: https://man.openbsd.org/tmux#visual-activity
set-option -g visual-activity off  # No messages for activity

# See: https://man.openbsd.org/tmux#activity-action
set-option -g activity-action other  # Only mark windows that aren't current

# Configure bell notifications with visual indicators but no messages
# See: https://man.openbsd.org/tmux#visual-bell
set-option -g visual-bell off  # No messages for bell alerts

# See: https://man.openbsd.org/tmux#bell-action
set-option -g bell-action any  # Mark any window that triggers a bell

# Status bar indicators - highlight activity in windows with color
# Window title formats with activity highlighting
set-window-option -g window-status-activity-style "fg=#bf616a,bg=#2e3440,bold"
