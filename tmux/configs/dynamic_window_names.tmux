# =============================================
# Dynamic Window Naming
# =============================================
# Show active process name or directory basename in window title
set -g automatic-rename-format '#{?#{==:#{pane_current_command},bash},#{b:pane_current_path},#{pane_current_command}}'

# Better window list display with numbers for quick navigation
bind-key w choose-tree -Zw