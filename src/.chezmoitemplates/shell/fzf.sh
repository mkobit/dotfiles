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
# See the fzf wiki for more: https://github.com/junegunn/fzf/wiki

# Check if we have our Bazel-managed fzf first, then fall back to system fzf
if [ -x "$BUILD_WORKSPACE_DIRECTORY/bazel-bin/src/tools/fzf_install" ]; then
    export PATH="$BUILD_WORKSPACE_DIRECTORY/bazel-bin/src/tools:$PATH"
    FZF_BINARY="$BUILD_WORKSPACE_DIRECTORY/bazel-bin/src/tools/fzf_install"
elif command -v fzf &> /dev/null; then
    FZF_BINARY="fzf"
else
    FZF_BINARY=""
fi

if [ -n "$FZF_BINARY" ]; then
    {{- if eq .shell "zsh" }}
    source <($FZF_BINARY --zsh)
    {{- else if eq .shell "bash" }}
    eval "$($FZF_BINARY --bash)"
    {{- end }}

    if [ -z "$FZF_DEFAULT_OPTS" ]; then
        export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border --inline-info --cycle"
    fi

    # Configure Ctrl+T (file/directory finder)
    if [ -z "$FZF_CTRL_T_OPTS" ]; then
        FZF_CTRL_T_OPTS="--walker-skip .git,node_modules,target,bazel-bin,bazel-out,bazel-testlogs"
        FZF_CTRL_T_OPTS="$FZF_CTRL_T_OPTS --bind 'ctrl-/:change-preview-window(down|hidden|)'"

        # Add preview with bat if available, fallback to cat
        if command -v bat &> /dev/null; then
            FZF_CTRL_T_OPTS="$FZF_CTRL_T_OPTS --preview 'bat -n --color=always {}'"
        else
            FZF_CTRL_T_OPTS="$FZF_CTRL_T_OPTS --preview 'cat {}'"
        fi

        export FZF_CTRL_T_OPTS
    fi

    # Configure Alt+C (directory navigation)
    if [ -z "$FZF_ALT_C_OPTS" ]; then
        FZF_ALT_C_OPTS="--walker-skip .git,node_modules,target,bazel-bin,bazel-out,bazel-testlogs"

        # Add preview with tree if available, fallback to ls
        if command -v tree &> /dev/null; then
            FZF_ALT_C_OPTS="$FZF_ALT_C_OPTS --preview 'tree -C {} | head -50'"
        else
            FZF_ALT_C_OPTS="$FZF_ALT_C_OPTS --preview 'ls -la {}'"
        fi

        export FZF_ALT_C_OPTS
    fi
else
    if [ -z "$FZF_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  fzf not found\033[0m - install for enhanced history search and fuzzy finding:"
        echo -e "  \033[1;34mMore info:\033[0m https://github.com/junegunn/fzf#installation"
        export FZF_INSTALL_HINT_SHOWN=1
    fi
fi
