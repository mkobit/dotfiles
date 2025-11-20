# =============================================
# Enhanced Status Bar with Smart Window Names
# =============================================

# Base colors and styling
# Docs: https://man.openbsd.org/tmux#status-style
set -g status-style "bg=#2e3440,fg=#d8dee9"

# Window status styling
# Docs: https://man.openbsd.org/tmux#window-status-style
set -g window-status-style "fg=#81a1c1,bg=#2e3440"
# Docs: https://man.openbsd.org/tmux#window-status-current-style
set -g window-status-current-style "fg=#2e3440,bg=#88c0d0,bold"

# Pane border colors
# Docs: https://man.openbsd.org/tmux#pane-border-style
set -g pane-border-style "fg=#4c566a"
# Docs: https://man.openbsd.org/tmux#pane-active-border-style
set -g pane-active-border-style "fg=#88c0d0"

# Message styling
# Docs: https://man.openbsd.org/tmux#message-style
set -g message-style "fg=#eceff4,bg=#3b4252,bold"
# Docs: https://man.openbsd.org/tmux#message-command-style
set -g message-command-style "fg=#eceff4,bg=#5e81ac"

# === STATUS BAR CONFIGURATION ===
# Status bar configured by tmux-powerline plugin.
# See: src/docs/tmux.md

# === WINDOW NAMING BEHAVIOR ===
# Focused window naming like tmux-powerline
# Docs: https://man.openbsd.org/tmux#allow-rename
set-window-option -g allow-rename off
# Docs: https://man.openbsd.org/tmux#automatic-rename
set-window-option -g automatic-rename on
# Docs: https://man.openbsd.org/tmux#automatic-rename-format
set-window-option -g automatic-rename-format "#{?#{==:#{pane_current_command},zsh},#{b:pane_current_path},#{pane_current_command}}"

# === BEHAVIOR SETTINGS ===
# Update status bar every 5 seconds for seconds display
# Docs: https://man.openbsd.org/tmux#status-interval
set-option -g status-interval 5

# Window list positioning (left-justified)
# Docs: https://man.openbsd.org/tmux#status-justify
set-option -g status-justify left

# Use vi-style status line navigation
# Docs: https://man.openbsd.org/tmux#status-keys
set-option -g status-keys vi

# Message display time (3 seconds)
# Docs: https://man.openbsd.org/tmux#display-time
set-option -g display-time 3000

# === ACTIVITY AND BELL STYLING ===
# Enhanced activity styling
# Docs: https://man.openbsd.org/tmux#window-status-activity-style
set-window-option -g window-status-activity-style "fg=#ebcb8b,bg=#2e3440,bold"

# Enhanced bell styling with blink
# Docs: https://man.openbsd.org/tmux#window-status-bell-style
set-window-option -g window-status-bell-style "fg=#bf616a,bg=#2e3440,bold,blink"

# Monitor activity but reduce visual noise
# Docs: https://man.openbsd.org/tmux#monitor-activity
set-window-option -g monitor-activity on
# Docs: https://man.openbsd.org/tmux#visual-activity
set-option -g visual-activity off
# Docs: https://man.openbsd.org/tmux#visual-bell
set-option -g visual-bell off

# === ADDITIONAL STYLING ===
# Copy mode styling
# Docs: https://man.openbsd.org/tmux#mode-style
set-window-option -g mode-style "fg=#2e3440,bg=#88c0d0"

# Clock mode styling
# Docs: https://man.openbsd.org/tmux#clock-mode-colour
set-window-option -g clock-mode-colour "#88c0d0"
# Docs: https://man.openbsd.org/tmux#clock-mode-style
set-window-option -g clock-mode-style 24
