# =============================================
# Status Bar Styling (Modern, Minimal)
# =============================================
# Status bar colors - Nord color scheme inspired
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

# Status left and right sections
set -g status-left "#[fg=#2e3440,bg=#88c0d0,bold] #S #[fg=#88c0d0,bg=#2e3440]"
set -g status-left-length 20

set -g status-right "#[fg=#4c566a,bg=#2e3440]#[fg=#e5e9f0,bg=#4c566a] %H:%M #[fg=#88c0d0,bg=#4c566a]#[fg=#2e3440,bg=#88c0d0,bold] #h "
set -g status-right-length 40

# Window status format
set -g window-status-format " #I:#W #F "
set -g window-status-current-format " #I:#W #F "
set -g window-status-separator ""