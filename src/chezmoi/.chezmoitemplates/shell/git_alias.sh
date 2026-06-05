# Git alias
alias g='git'

{{- if eq $.shell "zsh" }}
compdef g=git
{{- else if eq $.shell "bash" }}
complete -F _git -o bashdefault -o default g
{{- end }}

# Prevent prompt tools (Starship, claude-statusline, etc.) from acquiring the
# advisory index.lock during read-only operations like `git status`.
# Safe with fsmonitor active — change tracking is handled by the daemon,
# so the stat cache write-back that optional locks normally perform is redundant.
export GIT_OPTIONAL_LOCKS=0
