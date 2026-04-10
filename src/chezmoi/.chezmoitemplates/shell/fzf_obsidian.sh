{{- if eq .shell "zsh" }}
# Obsidian CLI Completion for Zsh
# Provides context-aware auto-completion for the Obsidian CLI.
# This natively integrates with fzf-tab (used in the dotfiles) for fzf-powered completion.

if command -v obsidian >/dev/null 2>&1; then
    _obsidian() {
        local in_vault=false
        local current_dir="$PWD"

        # Check if we are inside an Obsidian vault
        while [[ "$current_dir" != "/" && -n "$current_dir" ]]; do
            if [[ -d "$current_dir/.obsidian" ]]; then
                in_vault=true
                break
            fi
            current_dir=$(dirname "$current_dir")
        done

        if [[ "$in_vault" == "true" ]]; then
            _files -g "*.md"
        else
            _files
        fi
    }

    compdef _obsidian obsidian
fi
{{- end }}
