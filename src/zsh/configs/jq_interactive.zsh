#!/usr/bin/env zsh
# =============================================================================
# INTERACTIVE JQ - Real-time JSON filtering with FZF preview
# =============================================================================
#
# Function Provided:
#   ijq [file|stdin]  - Interactive jq filter with live preview
#
# Usage Examples:
#   # Interactive filtering of a JSON file
#   ijq data.json
#
#   # Interactive filtering from stdin
#   curl -s api.example.com/data | ijq
#   echo '{"name":"test","items":[1,2,3]}' | ijq
#
# Key Bindings:
#   Enter     - Output the filtered result
#   Ctrl+/    - Toggle preview window
#   Ctrl+R    - Reset/clear filter
#   Ctrl+C    - Exit without output
#
# Quick and dirty version inspired by jnv: https://github.com/ynqa/jnv
# Reference: https://gist.github.com/reegnz/b9e40993d410b75c2d866441add2cb55

# Check dependencies
if ! command -v fzf &> /dev/null || ! command -v jq &> /dev/null; then
    if [ -z "$IJQ_INSTALL_HINT_SHOWN" ]; then
        echo -e "\033[1;33m⚠️  Interactive jq requires both fzf and jq\033[0m"
        if ! command -v fzf &> /dev/null; then
            echo -e "  \033[1;34mInstall fzf:\033[0m https://github.com/junegunn/fzf#installation"
        fi
        if ! command -v jq &> /dev/null; then
            echo -e "  \033[1;34mInstall jq:\033[0m https://stedolan.github.io/jq/download/"
        fi
        export IJQ_INSTALL_HINT_SHOWN=1
    fi
    return 0
fi

# =============================================================================
# TMUX DETECTION AND CONFIGURATION
# =============================================================================
_ijq_detect_tmux() {
    [[ -n "$TMUX" ]]
}

_ijq_get_fzf_opts() {
    local is_tmux=$(_ijq_detect_tmux && echo true || echo false)
    local base_opts=""

    if [[ "$is_tmux" == "true" ]]; then
        # Tmux-optimized settings - smaller preview to preserve space
        base_opts="--height=80% --layout=reverse --border=rounded"
        echo "$base_opts --preview-window=right:50%"
    else
        # Full terminal settings
        base_opts="--height=90% --layout=reverse --border"
        echo "$base_opts --preview-window=up:60%"
    fi
}

# =============================================================================
# MAIN INTERACTIVE JQ FUNCTION
# =============================================================================
ijq() {
    local input_file
    local temp_input
    local cleanup_needed=false

    # Handle input - file argument, stdin, or error
    if [[ -z "$1" ]] || [[ "$1" == "-" ]]; then
        # Read from stdin
        if [[ -t 0 ]]; then
            echo -e "\033[1;31mError:\033[0m No input provided. Usage: ijq [file] or echo 'json' | ijq"
            return 1
        fi
        temp_input=$(mktemp)
        cleanup_needed=true
        trap "rm -f '$temp_input'" EXIT INT TERM
        cat > "$temp_input"
        input_file="$temp_input"
    else
        # Use provided file
        if [[ ! -f "$1" ]]; then
            echo -e "\033[1;31mError:\033[0m File '$1' not found"
            return 1
        fi
        input_file="$1"
    fi

    # Validate JSON input
    if ! jq empty "$input_file" 2>/dev/null; then
        echo -e "\033[1;31mError:\033[0m Invalid JSON input"
        [[ "$cleanup_needed" == true ]] && rm -f "$temp_input"
        return 1
    fi

    # Get optimal FZF options for current environment
    local fzf_opts=$(_ijq_get_fzf_opts)

    # Interactive jq with FZF
    local result
    result=$(
        echo '' | fzf \
            --disabled \
            $=fzf_opts \
            --preview-label='🔍 Interactive jq - Type your filter below' \
            --prompt='jq> ' \
            --print-query \
            --header='Enter: output | Ctrl+/: toggle preview | Ctrl+R: reset | Ctrl+C: exit' \
            --bind 'ctrl-/:change-preview-window(down|hidden|up:60%|right:50%)' \
            --bind 'ctrl-r:clear-query' \
            --preview "
                if [[ -n {q} ]]; then
                    jq --color-output -C {q} '$input_file' 2>/dev/null || echo -e '\033[1;31m❌ Invalid jq expression\033[0m\n\nTry:\n- Starting with . (dot)\n- Using quotes for strings: \"value\"\n- Basic filters: .key, .[], .key.subkey'
                else
                    echo -e '\033[1;36m💡 Start typing a jq filter...\033[0m\n\nExamples:\n  .               # Show all\n  .key            # Get specific key\n  .[]             # Array elements\n  .[] | select()  # Filter items'
                fi
            "
    )

    # Process result
    if [[ -n "$result" ]]; then
        # Extract the query (first line of result)
        local query=$(echo "$result" | head -1)
        if [[ -n "$query" ]]; then
            # Execute the final query
            jq --color-output -C "$query" "$input_file"
        else
            # No query provided, show the raw JSON with syntax highlighting
            jq --color-output -C . "$input_file"
        fi
    fi

    # Cleanup
    [[ "$cleanup_needed" == true ]] && rm -f "$temp_input"
}

# =============================================================================
# INTEGRATION WITH EXISTING FZF CONFIG
# =============================================================================
# Inherit FZF configuration if available
if [[ -n "$FZF_DEFAULT_OPTS" ]]; then
    # Use existing FZF styling for consistency
    export FZF_IJQ_OPTS="$FZF_DEFAULT_OPTS --border --layout=reverse"
fi
