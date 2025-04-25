# =============================================
# History Management
# =============================================
# Maximum number of lines held in window history
# Docs: https://man.openbsd.org/tmux#history-limit
set -g history-limit 50000

# Set history file location using HOME variable to be cross-OS compatible
# Docs: https://man.openbsd.org/tmux#history-file
set -g history-file ${HOME}/.tmux_history