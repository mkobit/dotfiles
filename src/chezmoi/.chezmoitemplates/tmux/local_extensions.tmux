# =============================================
# Local extensions
# =============================================

# Source local extensions if they exist
if-shell "test -f ~/.tmux.conf.local" "source-file ~/.tmux.conf.local"
if-shell "test -f ~/.tmux.local.conf" "source-file ~/.tmux.local.conf"
