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
# Position status bar at top
# Docs: https://man.openbsd.org/tmux#status-position
set -g status-position top

# Enable dual status bars
# Docs: https://man.openbsd.org/tmux#status
set -g status 2

# Status left - Simple and reliable PREFIX indicator
# Docs: https://man.openbsd.org/tmux#status-left-length
set -g status-left-length 30
# Docs: https://man.openbsd.org/tmux#status-left
set -g status-left "#{?client_prefix,#[bg=#bf616a]#[fg=#2e3440]#[bold] PREFIX #[nobold]#[default] ,}#[bg=#88c0d0]#[fg=#2e3440]#[bold] #S #[nobold]#[default] "

# Minimal window titles inspired by tmux-powerline
# Docs: https://man.openbsd.org/tmux#window-status-format
set -g window-status-format "#[fg=#81a1c1,bg=#2e3440] #I #[fg=#d8dee9]#W #[default]"

# Docs: https://man.openbsd.org/tmux#window-status-current-format
set -g window-status-current-format "#[fg=#2e3440,bg=#88c0d0,bold] #I #W #[default]#[fg=#88c0d0,bg=#2e3440]#[default]"

# No window separator for cleaner look
# Docs: https://man.openbsd.org/tmux#window-status-separator
set -g window-status-separator ""

# Status right - Time with seconds and hostname
# Docs: https://man.openbsd.org/tmux#status-right-length
set -g status-right-length 60
# Docs: https://man.openbsd.org/tmux#status-right
set -g status-right "#[fg=#4c566a,bg=#2e3440]#[fg=#2e3440,bg=#4c566a] %H:%M:%S #[fg=#88c0d0,bg=#4c566a]#[fg=#2e3440,bg=#88c0d0,bold] #h "

# Bottom status bar - Detailed pane info with visual git status
# Docs: https://man.openbsd.org/tmux#status-format
set -g status-format[1] '#[align=left,fg=#81a1c1,bg=#2e3440] #{pane_current_path} #[fg=#a3be8c]#(cd #{pane_current_path} 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null | xargs basename 2>/dev/null | sed "s/^/git:/" || echo "")#{?#{!=:#(cd #{pane_current_path} 2>/dev/null && git status --porcelain 2>/dev/null | wc -l | tr -d " "),0},#[fg=#bf616a]*,}#[align=centre,fg=#5e81ac] #{pane_current_command}#[align=right,fg=#ebcb8b] #(df -h . 2>/dev/null | awk "NR==2{print \$4}") free #[fg=#4c566a]│#[fg=#88c0d0] load #(uptime | sed "s/.*load average: //" | cut -d"," -f1 | sed "s/^ *//") #[fg=#4c566a]│#[fg=#b48ead] #(date "+%a %b %d") #[fg=#4c566a]│#[fg=#b48ead] #(date "+%Y-%m-%d") '

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
