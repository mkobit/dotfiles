# =============================================
# Copy Mode (Vim-style)
# =============================================
# Setup 'v' to begin selection like Vim
# Docs: https://man.openbsd.org/tmux#copy-mode-vi
bind-key -T copy-mode-vi 'v' send -X begin-selection

# OS-specific clipboard integration
# Use pbcopy on macOS and xclip on Linux
if-shell "uname | grep -q Darwin" {
  # macOS clipboard integration
  bind-key -T copy-mode-vi 'y' send -X copy-pipe-and-cancel 'pbcopy'
  bind-key -T copy-mode-vi Enter send -X copy-pipe-and-cancel 'pbcopy'
} {
  # Linux clipboard integration (requires xclip)
  bind-key -T copy-mode-vi 'y' send -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
  bind-key -T copy-mode-vi Enter send -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
}

# Additional copy mode bindings
bind-key -T copy-mode-vi 'V' send -X select-line
bind-key -T copy-mode-vi 'r' send -X rectangle-toggle