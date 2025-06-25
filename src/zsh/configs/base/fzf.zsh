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
# Exploring FZF Options:
#   man fzf              # Complete manual with all options
#   fzf --help           # Quick help summary
#   fzf --man            # Manual page (alternative to man fzf)
#
# Popular Additional Options (add to FZF_DEFAULT_OPTS if desired):
#   --cycle              # Enable circular navigation (✅ enabled below)
#   --preview-window     # Configure preview window (right:50%:hidden)
#   --bind 'ctrl-/:toggle-preview'  # Toggle preview with Ctrl+/
#   --color              # Custom color themes
#   --ansi               # Enable ANSI color processing
#   --multi              # Enable multi-selection
#
# Alternative: Use FZF_DEFAULT_OPTS_FILE for complex configurations
#   export FZF_DEFAULT_OPTS_FILE=~/.config/fzf/config

if command -v fzf &> /dev/null; then
    if [ -n "$ZSH_VERSION" ]; then
        source <(fzf --zsh)
    elif [ -n "$BASH_VERSION" ]; then
        eval "$(fzf --bash)"
    fi

    if [ -z "$FZF_DEFAULT_OPTS" ]; then
        export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border --inline-info --cycle"
    fi
else
    if [ -z "$FZF_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  fzf not found\033[0m - install for enhanced history search and fuzzy finding:"
        echo -e "  \033[1;34mMore info:\033[0m https://github.com/junegunn/fzf#installation"
        export FZF_INSTALL_HINT_SHOWN=1
    fi
fi
