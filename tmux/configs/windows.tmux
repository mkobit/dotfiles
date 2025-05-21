# =============================================
# Windows
# =============================================

# Window indexing starts at 1 (not 0)
set-option -g base-index 1

# Automatically renumber windows when one is closed
set-option -g renumber-windows on

# Enable titles for terminal windows
set-option -g set-titles on
set-option -g set-titles-string "#I:#W - #{host_short}"

# Create new windows in same directory
unbind-key c
bind-key c new-window -c "#{pane_current_path}"

# Window splitting keeps current path
bind-key v split-window -h -c "#{pane_current_path}"
bind-key s split-window -v -c "#{pane_current_path}"

# Window navigation
# Docs: https://man.openbsd.org/tmux#previous-window
bind-key -r C-h previous-window
# Docs: https://man.openbsd.org/tmux#next-window
bind-key -r C-l next-window

# Easier window rearrangement
# Docs: https://man.openbsd.org/tmux#swap-window
bind-key -n C-S-Left swap-window -t -1\; select-window -t -1
bind-key -n C-S-Right swap-window -t +1\; select-window -t +1

# Enable automatic window renaming by default
# Docs: https://man.openbsd.org/tmux#automatic-rename
set-window-option -g automatic-rename on
# Allow external programs to rename windows (required for automatic renaming)
# Docs: https://man.openbsd.org/tmux#allow-rename
set-window-option -g allow-rename on

# Format for automatic window naming:
# - Use compact symbols to indicate type (📁=dir, 🔧=command, etc.)
# - Keep names short but meaningful
# - Limit length to prevent overly long titles
set-window-option -g automatic-rename-format '\
#{window_index}#{?#{e|>:#{window_panes},1}, (#{pane_index}/#{window_panes}),}: \
#{?window_zoomed_flag,🔍,}#{?pane_marked,🚩,}#{?pane_synchronized,🔄,} \
#(git -C "#{pane_current_path}" rev-parse --is-inside-work-tree >/dev/null 2>&1 && echo "🐙 ")#{?pane_ssh,🌐,#{?#{m:((n)?vim|nano|ed),#{b:pane_current_command}},📝,#{?#{m:(less|man),#{b:pane_current_command}},📖,#{?#{m:(htop|top),#{b:pane_current_command}},📊,#{?#{m:(bash|zsh|sh|fish),#{b:pane_current_command}},⌨️,🚀}}}}} \
#{b:pane_current_path}#{?#{m:(bash|zsh|sh|fish),#{b:pane_current_command}},, | #{b:pane_current_command}}'

# Disable automatic renaming when a window is manually renamed
# This ensures custom names are preserved
bind-key , command-prompt -p "(rename-window '#W')" "rename-window '%%'; set-window-option automatic-rename off"
