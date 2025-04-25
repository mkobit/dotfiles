# =============================================
# Window and Pane Options
# =============================================
# Use vim keybindings in copy mode
# Docs: https://man.openbsd.org/tmux#mode-keys
set -w -g mode-keys vi

# Window indexing starts at 1 (easier to reach on keyboard)
# Docs: https://man.openbsd.org/tmux#base-index
set -g base-index 1

# Pane indexing starts at 1 (for consistency with windows)
# Docs: https://man.openbsd.org/tmux#pane-base-index
set -w -g pane-base-index 1

# Renumber windows when any is closed (maintains sequential ordering)
# Docs: https://man.openbsd.org/tmux#renumber-windows
set -g renumber-windows on