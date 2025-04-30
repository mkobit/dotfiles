# =============================================
# Status line configuration
# =============================================

# Update status bar every 2 seconds (more responsive)
# Docs: https://man.openbsd.org/tmux#status-interval
set-option -g status-interval 2

# Window list component is left-justified
# Docs: https://man.openbsd.org/tmux#status-justify
set-option -g status-justify left

# Use vi-style status line navigation
# Docs: https://man.openbsd.org/tmux#status-keys
set-option -g status-keys vi

# Position status bar at the top of the window
# Docs: https://man.openbsd.org/tmux#status-position
set-option -g status-position top

# Time (in ms) for which status line messages are displayed
# Docs: https://man.openbsd.org/tmux#display-time
set-option -g display-time 4000
