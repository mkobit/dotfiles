# =============================================
# Session Color Coding
# =============================================
# Apply different colors to different session indices for easy visual distinction
# These get run on session creation to set specific colors per session

# Define session colors
set -g @session-color-0 "#88c0d0"  # Blue
set -g @session-color-1 "#ebcb8b"  # Yellow
set -g @session-color-2 "#a3be8c"  # Green
set -g @session-color-3 "#b48ead"  # Purple
set -g @session-color-default "#81a1c1"  # Light Blue

# Set color for current session based on index
set-hook -g session-created 'run-shell "tmux set -g @current-session-color #{?#{e|:|##{session_id}|0},#{@session-color-0},#{?#{e|:|##{session_id}|1},#{@session-color-1},#{?#{e|:|##{session_id}|2},#{@session-color-2},#{?#{e|:|##{session_id}|3},#{@session-color-3},#{@session-color-default}}}}}"'

# Update current session variable on client attached
set-hook -g client-attached 'run-shell "tmux set -g @current-session-color #{?#{e|:|##{session_id}|0},#{@session-color-0},#{?#{e|:|##{session_id}|1},#{@session-color-1},#{?#{e|:|##{session_id}|2},#{@session-color-2},#{?#{e|:|##{session_id}|3},#{@session-color-3},#{@session-color-default}}}}}"'