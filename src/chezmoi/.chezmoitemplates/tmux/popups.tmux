# =============================================
# Popups
# =============================================

# Improved popups in tmux >= 3.2
if-shell -b '[ "$(echo "$(tmux -V | cut -d" " -f2) >= 3.2" | bc)" = 1 ]' {
  # Display popup with available sessions to switch to
  bind-key C-j display-popup -E "tmux list-sessions | sed -E 's/:.*$//' | grep -v \"^$(tmux display-message -p '#S')$\" | fzf --reverse | xargs tmux switch-client -t"

  # Show a clock in a popup
  bind-key C-t display-popup -E "date; sleep 1"
}
