# =============================================
# Enhanced Functionality & Convenience
# =============================================
# Synchronize panes (send command to all panes in window)
bind-key y setw synchronize-panes \; display "Sync panes: #{?pane_synchronized,ON,OFF}"

# Toggle status bar visibility with prefix+b
bind-key b set status

# Jump between sessions with prefix+J/K
bind-key J switch-client -n
bind-key K switch-client -p

# Quickly jump to specific windows with Alt+[number]
set -g repeat-time 500
bind-key -n M-1 select-window -t 1
bind-key -n M-2 select-window -t 2
bind-key -n M-3 select-window -t 3
bind-key -n M-4 select-window -t 4
bind-key -n M-5 select-window -t 5
bind-key -n M-6 select-window -t 6
bind-key -n M-7 select-window -t 7
bind-key -n M-8 select-window -t 8
bind-key -n M-9 select-window -t 9
