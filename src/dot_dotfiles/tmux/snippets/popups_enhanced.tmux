# =============================================
# Enhanced Popups
# =============================================

# Check tmux version for popup support
if-shell -b '[ "$(echo "$(tmux -V | cut -d" " -f2) >= 3.2" | bc)" = 1 ]' {

    # System information popup (using C-i)
    bind-key C-i display-popup -E -w 60% -h 70% "
        echo '=== System Information ==='
        echo
        echo 'CPU Usage:'
        if [[ \"\$OSTYPE\" == \"darwin\"* ]]; then
            top -l 1 -n 0 | grep 'CPU usage' | awk '{print \$3}' | sed 's/%//' || echo 'N/A'
        else
            top -bn1 | grep 'Cpu(s)' | awk '{print \$2}' | sed 's/%us,//' || echo 'N/A'
        fi
        echo
        echo 'Memory Usage:'
        if [[ \"\$OSTYPE\" == \"darwin\"* ]]; then
            vm_stat | head -5
        else
            free -h 2>/dev/null || echo 'N/A'
        fi
        echo
        echo 'Disk Usage:'
        df -h . | tail -1
        echo
        echo 'Load Average:'
        uptime | grep -oE 'load average[s:][: ].*' || echo 'N/A'
        echo
        echo 'Press any key to close...'
        read -n 1
    "

    # Git status popup for current directory (using C-g)
    bind-key C-g display-popup -E -w 80% -h 70% "
        cd '#{pane_current_path}'
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            echo '=== Git Status for #{pane_current_path} ==='
            echo
            git status --short --branch
            echo
            echo '=== Recent Commits ==='
            git log --oneline -10 --graph --color=always 2>/dev/null || git log --oneline -10
            echo
            echo '=== Branches ==='
            git branch -a --color=always 2>/dev/null || git branch -a
        else
            echo 'Not a git repository: #{pane_current_path}'
        fi
        echo
        echo 'Press any key to close...'
        read -n 1
    "

    # File browser popup (using C-f)
    bind-key C-f display-popup -E -w 90% -h 80% "
        if command -v ranger >/dev/null 2>&1; then
            cd '#{pane_current_path}' && ranger
        elif command -v lf >/dev/null 2>&1; then
            cd '#{pane_current_path}' && lf
        elif command -v fzf >/dev/null 2>&1; then
            cd '#{pane_current_path}'
            file=\$(find . -type f | head -500 | fzf --prompt='Open file: ' --preview 'head -50 {}' --height=80%)
            [[ -n \"\$file\" ]] && tmux send-keys -t '#{pane_id}' \"\$EDITOR \$file\" Enter
        else
            echo 'File Browser - #{pane_current_path}'
            echo '=================================='
            cd '#{pane_current_path}'
            ls -la | head -30
            echo
            read -p 'Enter filename to open: ' file
            [[ -n \"\$file\" && -f \"\$file\" ]] && tmux send-keys -t '#{pane_id}' \"\$EDITOR \$file\" Enter
        fi
    "

    # Quick command runner popup (using C-q)
    bind-key C-q display-popup -E -w 70% -h 40% "
        echo 'Quick Command Runner'
        echo '==================='
        echo 'Enter command to run in current directory: #{pane_current_path}'
        echo
        cd '#{pane_current_path}'
        read -p '$ ' cmd
        if [[ -n \"\$cmd\" ]]; then
            echo
            echo 'Executing: '\$cmd
            echo '========================'
            eval \$cmd
            echo
            echo 'Command finished. Press any key to close...'
            read -n 1
        fi
    "

} {
    # Fallback for older tmux versions
    bind-key C-f display-message "Enhanced popups require tmux 3.2+. Current version: $(tmux -V)"
}
