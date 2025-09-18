# zoxide configuration
if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init bash)"
    # Override cd with zoxide
    alias cd='z'
fi