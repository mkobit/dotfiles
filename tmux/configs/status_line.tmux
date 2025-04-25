# =============================================
# Status Line Configuration
# =============================================
# Update status bar every 2 seconds (more responsive)
# Docs: https://man.openbsd.org/tmux#status-interval
set -g status-interval 2

# Window list component is left-justified
# Docs: https://man.openbsd.org/tmux#status-justify
set -g status-justify left

# Use vi-style status line navigation
# Docs: https://man.openbsd.org/tmux#status-keys
set -g status-keys vi

# Position status bar at the top of the window
# Docs: https://man.openbsd.org/tmux#status-position
set -g status-position top