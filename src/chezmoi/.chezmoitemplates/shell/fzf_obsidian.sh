{{- if eq .shell "zsh" }}
# Obsidian CLI FZF Completion for Zsh
# Provides auto-completion for Obsidian CLI commands and markdown files

# Ensure fzf is available and obsidian is installed
if command -v fzf >/dev/null 2>&1 && command -v obsidian >/dev/null 2>&1; then
    _fzf_complete_obsidian() {
        # Check if we are inside an Obsidian vault (has .obsidian directory)
        local in_vault=false
        local current_dir="$PWD"
        while [[ "$current_dir" != "/" && -n "$current_dir" ]]; do
            if [[ -d "$current_dir/.obsidian" ]]; then
                in_vault=true
                break
            fi
            current_dir=$(dirname "$current_dir")
        done

        # If in a vault, suggest markdown files
        if [[ "$in_vault" == "true" ]]; then
            _fzf_complete --prompt="Obsidian Note> " -- "$@" < <(
                if command -v fd >/dev/null 2>&1; then
                    fd -e md -t f -c never
                elif command -v fdfind >/dev/null 2>&1; then
                    fdfind -e md -t f -c never
                else
                    find . -name "*.md" -type f | sed 's|^\./||'
                fi
            )
        else
            # Default fallback - suggest directories for workspaces/vaults
            _fzf_complete --prompt="Obsidian> " -- "$@" < <(
                if command -v fd >/dev/null 2>&1; then
                    fd -t d -c never
                elif command -v fdfind >/dev/null 2>&1; then
                    fdfind -t d -c never
                else
                    find . -type d | sed 's|^\./||'
                fi
            )
        fi
    }

    # Use native fzf completion setup if available, otherwise manual fallback
    if type _fzf_setup_completion >/dev/null 2>&1; then
        _fzf_setup_completion path obsidian
    fi
fi
{{- end }}
