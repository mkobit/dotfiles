# =============================================================================
# HISTORY CONFIGURATION - Large, shared, optimized for tmux
# =============================================================================
export HISTFILE=~/.zsh_history
export HISTSIZE=100000
export SAVEHIST=100000

# History behavior - optimized for cross-session sharing (tmux-friendly)
setopt EXTENDED_HISTORY        # Save timestamp and duration with each command
setopt INC_APPEND_HISTORY      # Write to history immediately, not on shell exit
setopt SHARE_HISTORY           # Share history between all sessions (important for tmux)
setopt HIST_EXPIRE_DUPS_FIRST  # Expire duplicate entries first when trimming
setopt HIST_IGNORE_DUPS        # Don't record duplicate consecutive entries
setopt HIST_IGNORE_ALL_DUPS    # Delete old entry if new entry is duplicate
setopt HIST_FIND_NO_DUPS       # Don't display duplicates when searching
setopt HIST_IGNORE_SPACE       # Don't record entries starting with space
setopt HIST_SAVE_NO_DUPS       # Don't write duplicate entries to history file
setopt HIST_REDUCE_BLANKS      # Remove superfluous blanks before recording
setopt HIST_VERIFY             # Show command with history expansion before running
