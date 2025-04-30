# =============================================
# Copy mode (Vim-style)
# =============================================

# Setup 'v' to begin selection like Vim
# Docs: https://man.openbsd.org/tmux#copy-mode-vi
bind-key -T copy-mode-vi 'v' send-keys -X begin-selection

# OS-specific clipboard integration
# Use pbcopy on macOS and xclip on Linux
if-shell "uname | grep -q Darwin" {
  # macOS clipboard integration
  # Docs: https://man.openbsd.org/tmux#copy-pipe-and-cancel
  bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'pbcopy'
  bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'pbcopy'
} {
  # Linux clipboard integration (requires xclip)
  # Docs: https://man.openbsd.org/tmux#copy-pipe-and-cancel
  bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
  bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
}

# Additional copy mode bindings
# Docs: https://man.openbsd.org/tmux#select-line
bind-key -T copy-mode-vi 'V' send-keys -X select-line
# Docs: https://man.openbsd.org/tmux#rectangle-toggle
bind-key -T copy-mode-vi 'r' send-keys -X rectangle-toggle
