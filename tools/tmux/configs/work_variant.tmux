# Work variant specific tmux settings

# Set workspace indicators in status bar
set -g status-left "#[fg=#2e3440,bg=#88c0d0,bold] WORK #[fg=#88c0d0,bg=#2e3440]"

# Automatically set terminal title to include workspace indicator
set -g set-titles-string '[WORK] #H:#S.#I.#P #W'

# Work-specific color scheme (blue accents)
set -g window-status-current-style "fg=#2e3440,bg=#5e81ac,bold"
set -g pane-active-border-style "fg=#5e81ac"