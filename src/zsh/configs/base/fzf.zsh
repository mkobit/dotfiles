# FZF - Enhanced fuzzy finding and history search
#
# Key Bindings Provided:
#   Ctrl+R  - Fuzzy search command history
#   Ctrl+T  - Fuzzy find files/directories (inserts at cursor)
#   Alt+C   - Fuzzy find and cd to directory
#   Tab     - Enhanced tab completion for files, processes, etc.
#
# Usage Examples:
#   # History search - type partial command parts in any order
#   <Ctrl+R> then type: "git co" (matches "git commit", "git checkout", etc.)
#
#   # File finder - insert file path at cursor
#   vim <Ctrl+T>  (fuzzy find and select file to edit)
#
#   # Directory navigation
#   <Alt+C>  (browse and cd to any subdirectory)
#
#   # Advanced piping patterns
#   ps aux | fzf | awk '{print $2}' | xargs kill  # Kill processes
#   git branch | fzf | xargs git checkout         # Switch git branches
#   find . -type f | fzf --preview 'cat {}'       # Browse with preview

if command -v fzf &> /dev/null; then
    if [ -n "$ZSH_VERSION" ]; then
        source <(fzf --zsh)
    elif [ -n "$BASH_VERSION" ]; then
        eval "$(fzf --bash)"
    fi

    if [ -z "$FZF_DEFAULT_OPTS" ]; then
        export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border --inline-info"
    fi
else
    if [ -z "$FZF_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  fzf not found\033[0m - install for enhanced history search and fuzzy finding:"
        echo -e "  \033[1;34mMore info:\033[0m https://github.com/junegunn/fzf#installation"
        export FZF_INSTALL_HINT_SHOWN=1
    fi
fi
