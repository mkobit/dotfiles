# =============================================
# Activity and bell notifications
# =============================================

# Configure activity monitoring - COMPLETELY DISABLED
# Disabling monitor-activity prevents beeps/visuals when activity occurs in other windows
# See: https://man.openbsd.org/tmux#monitor-activity
set-window-option -g monitor-activity off

# See: https://man.openbsd.org/tmux#visual-activity
set-option -g visual-activity off  # No messages for activity

# See: https://man.openbsd.org/tmux#activity-action
set-option -g activity-action none  # Ignore all activity

# Configure bell notifications - COMPLETELY DISABLED
# See: https://man.openbsd.org/tmux#monitor-bell
set-window-option -g monitor-bell off

# See: https://man.openbsd.org/tmux#visual-bell
set-option -g visual-bell off  # No visual bell messages

# See: https://man.openbsd.org/tmux#bell-action
set-option -g bell-action none  # Completely ignore all bells
