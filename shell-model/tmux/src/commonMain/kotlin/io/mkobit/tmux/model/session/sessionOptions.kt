package io.mkobit.tmux.model.session

//       activity-action [any | none | current | other]
//               Set action on window activity when monitor-activity is
//               on.  any means activity in any window linked to a session
//               causes a bell or message (depending on visual-activity)
//               in the current window of that session, none means all
//               activity is ignored (equivalent to monitor-activity being
//               off), current means only activity in windows other than
//               the current window are ignored and other means activity
//               in the current window is ignored but not those in other
//               windows.
//
//       assume-paste-time milliseconds
//               If keys are entered faster than one in milliseconds, they
//               are assumed to have been pasted rather than typed and key
//               bindings are not processed.  The default is one
//               millisecond and zero disables.
//
//       base-index index
//               Set the base index from which an unused index should be
//               searched when a new window is created.  The default is
//               zero.
//
//       bell-action [any | none | current | other]
//               Set action on a bell in a window when monitor-bell is on.
//               The values are the same as those for activity-action.
//
//       default-command shell-command
//               Set the command used for new windows (if not specified
//               when the window is created) to shell-command, which may
//               be any sh(1) command.  The default is an empty string,
//               which instructs to create a login shell using the value
//               of the default-shell option.
//
//       default-shell path
//               Specify the default shell.  This is used as the login
//               shell for new windows when the default-command option is
//               set to empty, and must be the full path of the
//               executable.  When started tries to set a default value
//               from the first suitable of the SHELL environment
//               variable, the shell returned by getpwuid(3), or /bin/sh.
//               This option should be configured when is used as a login
//               shell.
//
//       default-size XxY
//               Set the default size of new windows when the window-size
//               option is set to manual or when a session is created with
//               new-session -d.  The value is the width and height
//               separated by an ‘x’ character.  The default is 80x24.
//
//       destroy-unattached [on | off]
//               If enabled and the session is no longer attached to any
//               clients, it is destroyed.
//
//       detach-on-destroy [off | on | no-detached | previous | next]
//               If on (the default), the client is detached when the
//               session it is attached to is destroyed.  If off, the
//               client is switched to the most recently active of the
//               remaining sessions.  If no-detached, the client is
//               detached only if there are no detached sessions; if
//               detached sessions exist, the client is switched to the
//               most recently active.  If previous or next, the client is
//               switched to the previous or next session in alphabetical
//               order.
//
//       display-panes-active-colour colour
//               Set the colour used by the display-panes command to show
//               the indicator for the active pane.
//
//       display-panes-colour colour
//               Set the colour used by the display-panes command to show
//               the indicators for inactive panes.
//
//       display-panes-time time
//               Set the time in milliseconds for which the indicators
//               shown by the display-panes command appear.
//
//       display-time time
//               Set the amount of time for which status line messages and
//               other on-screen indicators are displayed.  If set to 0,
//               messages and indicators are displayed until a key is
//               pressed.  time is in milliseconds.
//
//       history-limit lines
//               Set the maximum number of lines held in window history.
//               This setting applies only to new windows - existing
//               window histories are not resized and retain the limit at
//               the point they were created.
//
//       key-table key-table
//               Set the default key table to key-table instead of root.
//
//       lock-after-time number
//               Lock the session (like the lock-session command) after
//               number seconds of inactivity.  The default is not to lock
//               (set to 0).
//
//       lock-command shell-command
//               Command to run when locking each client.  The default is
//               to run lock(1) with -np.
//
//       menu-style style
//               Set the menu style.  See the “STYLES” section on how to
//               specify style.  Attributes are ignored.
//
//       menu-selected-style style
//               Set the selected menu item style.  See the “STYLES”
//               section on how to specify style.  Attributes are ignored.
//
//       menu-border-style style
//               Set the menu border style.  See the “STYLES” section on
//               how to specify style.  Attributes are ignored.
//
//       menu-border-lines type
//               Set the type of characters used for drawing menu borders.
//               See popup-border-lines for possible values for
//               border-lines.
//
//       message-command-style style
//               Set status line message command style.  This is used for
//               the command prompt with vi(1) keys when in command mode.
//               For how to specify style, see the “STYLES” section.
//
//       message-line [0 | 1 | 2 | 3 | 4]
//               Set line on which status line messages and the command
//               prompt are shown.
//
//       message-style style
//               Set status line message style.  This is used for messages
//               and for the command prompt.  For how to specify style,
//               see the “STYLES” section.
//
//       mouse [on | off]
//               If on, captures the mouse and allows mouse events to be
//               bound as key bindings.  See the “MOUSE SUPPORT” section
//               for details.
//
//       prefix key
//               Set the key accepted as a prefix key.  In addition to the
//               standard keys described under “KEY BINDINGS”, prefix can
//               be set to the special key ‘None’ to set no prefix.
//
//       prefix2 key
//               Set a secondary key accepted as a prefix key.  Like
//               prefix, prefix2 can be set to ‘None’.
//
//       renumber-windows [on | off]
//               If on, when a window is closed in a session,
//               automatically renumber the other windows in numerical
//               order.  This respects the base-index option if it has
//               been set.  If off, do not renumber the windows.
//
//       repeat-time time
//               Allow multiple commands to be entered without pressing
//               the prefix-key again in the specified time milliseconds
//               (the default is 500).  Whether a key repeats may be set
//               when it is bound using the -r flag to bind-key.  Repeat
//               is enabled for the default keys bound to the resize-pane
//               command.
//
//       set-titles [on | off]
//               Attempt to set the client terminal title using the tsl
//               and fsl terminfo(5) entries if they exist.  automatically
//               sets these to the \e]0;...\007 sequence if the terminal
//               appears to be xterm(1).  This option is off by default.
//
//       set-titles-string string
//               String used to set the client terminal title if
//               set-titles is on.  Formats are expanded, see the
//               “FORMATS” section.
//
//       silence-action [any | none | current | other]
//               Set action on window silence when monitor-silence is on.
//               The values are the same as those for activity-action.
//
//       status [off | on | 2 | 3 | 4 | 5]
//               Show or hide the status line or specify its size.  Using
//               on gives a status line one row in height; 2, 3, 4 or 5
//               more rows.
//
//       status-format[] format
//               Specify the format to be used for each line of the status
//               line.  The default builds the top status line from the
//               various individual status options below.
//
//       status-interval interval
//               Update the status line every interval seconds.  By
//               default, updates will occur every 15 seconds.  A setting
//               of zero disables redrawing at interval.
//
//       status-justify [left | centre | right | absolute-centre]
//               Set the position of the window list in the status line:
//               left, centre or right.  centre puts the window list in
//               the relative centre of the available free space;
//               absolute-centre uses the centre of the entire horizontal
//               space.
//
//       status-keys [vi | emacs]
//               Use vi or emacs-style key bindings in the status line,
//               for example at the command prompt.  The default is emacs,
//               unless the VISUAL or EDITOR environment variables are set
//               and contain the string ‘vi’.
//
//       status-left string
//               Display string (by default the session name) to the left
//               of the status line.  string will be passed through
//               strftime(3).  Also see the “FORMATS” and “STYLES”
//               sections.
//
//               For details on how the names and titles can be set see
//               the “NAMES AND TITLES” section.
//
//               Examples are:
//
//                     #(sysctl vm.loadavg)
//                     #[fg=yellow,bold]#(apm -l)%%#[default] [#S]
//
//               The default is ‘[#S] ’.
//
//       status-left-length length
//               Set the maximum length of the left component of the
//               status line.  The default is 10.
//
//       status-left-style style
//               Set the style of the left part of the status line.  For
//               how to specify style, see the “STYLES” section.
//
//       status-position [top | bottom]
//               Set the position of the status line.
//
//       status-right string
//               Display string to the right of the status line.  By
//               default, the current pane title in double quotes, the
//               date and the time are shown.  As with status-left, string
//               will be passed to strftime(3) and character pairs are
//               replaced.
//
//       status-right-length length
//               Set the maximum length of the right component of the
//               status line.  The default is 40.
//
//       status-right-style style
//               Set the style of the right part of the status line.  For
//               how to specify style, see the “STYLES” section.
//
//       status-style style
//               Set status line style.  For how to specify style, see the
//               “STYLES” section.
//
//       update-environment[] variable
//               Set list of environment variables to be copied into the
//               session environment when a new session is created or an
//               existing session is attached.  Any variables that do not
//               exist in the source environment are set to be removed
//               from the session environment (as if -r was given to the
//               set-environment command).
//
//       visual-activity [on | off | both]
//               If on, display a message instead of sending a bell when
//               activity occurs in a window for which the
//               monitor-activity window option is enabled.  If set to
//               both, a bell and a message are produced.
//
//       visual-bell [on | off | both]
//               If on, a message is shown on a bell in a window for which
//               the monitor-bell window option is enabled instead of it
//               being passed through to the terminal (which normally
//               makes a sound).  If set to both, a bell and a message are
//               produced.  Also see the bell-action option.
//
//       visual-silence [on | off | both]
//               If monitor-silence is enabled, prints a message after the
//               interval has expired on a given window instead of sending
//               a bell.  If set to both, a bell and a message are
//               produced.
//
//       word-separators string
//               Sets the session's conception of what characters are
//               considered word separators, for the purposes of the next
//               and previous word commands in copy mode.
