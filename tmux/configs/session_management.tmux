# =============================================
# Session Management
# =============================================
# Create a new session with prefix+S
bind-key S command-prompt "new-session -s %%"

# Kill current session with prefix+X
bind-key X confirm-before -p "Kill session #S? (y/n)" "kill-session"

# List sessions with prefix+s and make it more visual
bind-key s choose-tree -Zs