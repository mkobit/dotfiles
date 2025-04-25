# =============================================
# Window Title Settings
# =============================================
# Automatically set window titles
# Docs: https://man.openbsd.org/tmux#set-titles
set -g set-titles on
set -g set-titles-string '#H:#S.#I.#P #W #T' # hostname:session.window.pane window_name title

# Enable automatic window renaming
# Docs: https://man.openbsd.org/tmux#automatic-rename
set -w -g automatic-rename on
set -w -g allow-rename on