# Disable terminal bell/beep sounds
# This prevents audio notifications

if [ -n "$ZSH_VERSION" ]; then
    # ZSH-specific bell disabling
    unsetopt BEEP
elif [ -n "$BASH_VERSION" ]; then
    # Disable readline bell (bash completion, history, etc.)
    bind 'set bell-style none' 2>/dev/null || true
fi
