# Set EDITOR to nvim if available, otherwise vim
if command -v nvim >/dev/null 2>&1; then
    export EDITOR=nvim
    alias vim=nvim
elif command -v vim >/dev/null 2>&1; then
    export EDITOR=vim
fi

# Set VISUAL to a GUI editor if available, otherwise fallback to EDITOR
if command -v cursor >/dev/null 2>&1; then
    export VISUAL=cursor
elif command -v code >/dev/null 2>&1; then
    export VISUAL=code
elif command -v idea >/dev/null 2>&1; then
    export VISUAL=idea
else
    export VISUAL="$EDITOR"
fi
