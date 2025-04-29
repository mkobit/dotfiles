# =============================================
# Session Management
# =============================================
# Create a new session with prefix+S with naming prompt
bind-key S command-prompt -p "New session name:" "new-session -s '%%'"

# Rename current session with prefix+$
bind-key '$' command-prompt -I "#S" "rename-session '%%'"

# Kill current session with prefix+X
bind-key X confirm-before -p "Kill session #S? (y/n)" "kill-session"

# List sessions with prefix+s and make it more visual
bind-key s choose-tree -Zs

# Session navigation with prefix+( and prefix+)
bind-key ( switch-client -p
bind-key ) switch-client -n

# Group sessions for easier management
bind-key g command-prompt -p "Group with session:" "link-window -s %% -a"

# We're preserving the default window switching with prefix+0-9
# This allows quick navigation between windows within a session