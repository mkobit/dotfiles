# =============================================
# Session Persistence Helpers (No Plugins)
# =============================================
# Helper key bindings for session management

# Create a new named session and prompt for a window name
bind-key N command-prompt -p "New session name:,First window name:" \
  "new-session -s '%1' -n '%2'"

# Rename current session with improved visibility
bind-key R command-prompt -I "#S" -p "Rename session:" \
  "rename-session '%%'"

# Switch to most recently used session
bind-key L switch-client -l