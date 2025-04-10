# Personal variant specific tmux settings

# Set workspace indicators in status bar
set -g status-left "#[fg=#2e3440,bg=#a3be8c,bold] PERSONAL #[fg=#a3be8c,bg=#2e3440]"

# Automatically set terminal title to include workspace indicator
set -g set-titles-string '[PERSONAL] #H:#S.#I.#P #W'

# Personal-specific color scheme (green accents)
set -g window-status-current-style "fg=#2e3440,bg=#a3be8c,bold"
set -g pane-active-border-style "fg=#a3be8c"