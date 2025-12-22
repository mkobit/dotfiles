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

# Configure bell notifications - COMPLETELY DISABLED
# See: https://man.openbsd.org/tmux#visual-bell
set-option -g visual-bell off  # No visual bell messages

# See: https://man.openbsd.org/tmux#bell-action
set-option -g bell-action none  # Completely ignore all bells

