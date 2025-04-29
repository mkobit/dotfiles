# =============================================
# Window Title Settings
# =============================================
# Automatically set window titles with simpler contextual information
# Docs: https://man.openbsd.org/tmux#set-titles
set -g set-titles on
set -g set-titles-string '#H:#S.#I.#P | #{pane_current_path} | #{pane_current_command}'

# Enable automatic window renaming
# Docs: https://man.openbsd.org/tmux#automatic-rename
set -w -g automatic-rename on
set -w -g allow-rename on

# Show window activity indicators in the status line
setw -g monitor-activity on
set -g visual-activity off  # Don't show messages, just the indicator