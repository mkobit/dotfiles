# =============================================
# Copy mode (Vim-style)
# =============================================

# Setup 'v' to begin selection like Vim
# Docs: https://man.openbsd.org/tmux#copy-mode-vi
bind-key -T copy-mode-vi 'v' send-keys -X begin-selection

# OS-specific clipboard integration
# Use pbcopy on macOS, xclip on Linux if available, otherwise OSC 52 fallback
if-shell "uname | grep -q Darwin" {
  # macOS clipboard integration
  # Docs: https://man.openbsd.org/tmux#copy-pipe-and-cancel
  bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'pbcopy'
  bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'pbcopy'
} {
  # Linux clipboard integration (e.g., WSL, servers)
  # Check if xclip is available for local X11 sessions
  if-shell "command -v xclip" {
      bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
      bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'xclip -in -selection clipboard'
  } {
      # Fallback to internal clipboard (OSC 52) for WSL/SSH without X11
      # Relies on 'set -s set-clipboard on' in terminal_settings.tmux
      bind-key -T copy-mode-vi 'y' send-keys -X copy-selection-and-cancel
      bind-key -T copy-mode-vi Enter send-keys -X copy-selection-and-cancel
  }
}

# Additional copy mode bindings
# Docs: https://man.openbsd.org/tmux#select-line
bind-key -T copy-mode-vi 'V' send-keys -X select-line
# Docs: https://man.openbsd.org/tmux#rectangle-toggle
bind-key -T copy-mode-vi 'r' send-keys -X rectangle-toggle
