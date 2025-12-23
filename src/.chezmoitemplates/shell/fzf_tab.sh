{{- if eq .shell "bash" }}
# FZF Tab Completion for Bash
# https://github.com/lincheney/fzf-tab-completion

FZF_TAB_COMPLETION_DIR="{{ .chezmoi.destDir }}/.dotfiles/external/fzf-tab-completion"

if [[ -f "$FZF_TAB_COMPLETION_DIR/bash/fzf-bash-completion.sh" ]]; then
    source "$FZF_TAB_COMPLETION_DIR/bash/fzf-bash-completion.sh"

    # Bind Tab to fzf completion
    bind -x '"\t": fzf_bash_completion'

    # Ensure cycling is enabled in FZF default options if not already present
    if [[ "$FZF_DEFAULT_OPTS" != *"--cycle"* ]]; then
        export FZF_DEFAULT_OPTS="$FZF_DEFAULT_OPTS --cycle"
    fi
else
    # Only warn if interactive
    if [[ $- == *i* ]]; then
        # Try to use shared logging script if available
        CHEZMOI_SOURCE_DIR="{{ .chezmoi.sourceDir }}"
        LOGGING_SCRIPT="$CHEZMOI_SOURCE_DIR/scripts/logging.sh"
        if [[ -f "$LOGGING_SCRIPT" ]]; then
            source "$LOGGING_SCRIPT"
            log_warn "fzf-tab-completion not found at $FZF_TAB_COMPLETION_DIR"
        else
            echo "fzf-tab-completion not found at $FZF_TAB_COMPLETION_DIR"
        fi
    fi
fi
{{- else if eq .shell "zsh" }}
# FZF Tab Completion for Zsh
# https://github.com/Aloxaf/fzf-tab

FZF_TAB_DIR="{{ .chezmoi.destDir }}/.dotfiles/external/fzf-tab"

if [[ -f "$FZF_TAB_DIR/fzf-tab.plugin.zsh" ]]; then
    # Load the plugin
    source "$FZF_TAB_DIR/fzf-tab.plugin.zsh"

    # Configuration
    # Use fzf default opts to ensure consistent look and feel
    zstyle ':fzf-tab:*' use-fzf-default-opts yes

    # Ensure cycling is enabled in FZF default options if not already present
    if [[ "$FZF_DEFAULT_OPTS" != *"--cycle"* ]]; then
        export FZF_DEFAULT_OPTS="$FZF_DEFAULT_OPTS --cycle"
    fi

    # Switch group using < and >
    zstyle ':fzf-tab:*' switch-group '<' '>'

    # Preview directory content when completing cd
    # Use eza if available (preferred), otherwise fall back to ls
    if command -v eza >/dev/null 2>&1; then
        zstyle ':fzf-tab:complete:cd:*' fzf-preview 'eza -1 --color=always $realpath'
    else
        # Handle macOS vs Linux ls differences for color
        if ls --color >/dev/null 2>&1; then
             zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls -1 --color=always $realpath'
        else
             zstyle ':fzf-tab:complete:cd:*' fzf-preview 'ls -1 -G $realpath'
        fi
    fi

    # Force zsh not to show completion menu, which allows fzf-tab to capture the unambiguous prefix
    zstyle ':completion:*' menu no
else
    # Only warn if interactive
    if [[ -o interactive ]]; then
        # Try to use shared logging script if available
        CHEZMOI_SOURCE_DIR="{{ .chezmoi.sourceDir }}"
        LOGGING_SCRIPT="$CHEZMOI_SOURCE_DIR/scripts/logging.sh"
        if [[ -f "$LOGGING_SCRIPT" ]]; then
            source "$LOGGING_SCRIPT"
            log_warn "fzf-tab not found at $FZF_TAB_DIR"
        else
            echo "fzf-tab not found at $FZF_TAB_DIR"
        fi
    fi
fi
{{- end }}
