# =============================================
# Copy mode (Vim-style)
# =============================================

# Setup 'v' to begin selection like Vim
# Docs: https://man.openbsd.org/tmux#copy-mode-vi
bind-key -T copy-mode-vi 'v' send-keys -X begin-selection

# OS-specific clipboard integration
# Use pbcopy on macOS, otherwise OSC 52 fallback (copy-selection-and-cancel)
{{ if eq .chezmoi.os "darwin" -}}
# macOS clipboard integration
# Docs: https://man.openbsd.org/tmux#copy-pipe-and-cancel
bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'pbcopy'
bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'pbcopy'
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel 'pbcopy'
{{ else if (and (eq .chezmoi.os "linux") (contains "microsoft" (lower .chezmoi.kernel.osrelease))) -}}
# WSL clipboard integration
# Uses clip.exe to copy to Windows clipboard
bind-key -T copy-mode-vi 'y' send-keys -X copy-pipe-and-cancel 'clip.exe'
bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel 'clip.exe'
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel 'clip.exe'
{{ else -}}
# Linux clipboard integration
# Uses native OSC 52 capability (set-clipboard on) to copy to host terminal clipboard
# This works in SSH and containers without extra tools like xclip
bind-key -T copy-mode-vi 'y' send-keys -X copy-selection-and-cancel
bind-key -T copy-mode-vi Enter send-keys -X copy-selection-and-cancel
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-selection-and-cancel
{{ end -}}

# Additional copy mode bindings
# Docs: https://man.openbsd.org/tmux#select-line
bind-key -T copy-mode-vi 'V' send-keys -X select-line
# Docs: https://man.openbsd.org/tmux#rectangle-toggle
bind-key -T copy-mode-vi 'r' send-keys -X rectangle-toggle
