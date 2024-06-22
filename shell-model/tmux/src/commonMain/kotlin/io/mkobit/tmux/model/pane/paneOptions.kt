package io.mkobit.tmux.model.pane

//        allow-passthrough [on | off | all]
//               Allow programs in the pane to bypass using a terminal
//               escape sequence (\ePtmux;...\e\\).  If set to on,
//               passthrough sequences will be allowed only if the pane is
//               visible.  If set to all, they will be allowed even if the
//               pane is invisible.
//
//       allow-rename [on | off]
//               Allow programs in the pane to change the window name
//               using a terminal escape sequence (\ek...\e\\).
//
//       alternate-screen [on | off]
//               This option configures whether programs running inside
//               the pane may use the terminal alternate screen feature,
//               which allows the smcup and rmcup terminfo(5)
//               capabilities.  The alternate screen feature preserves the
//               contents of the window when an interactive application
//               starts and restores it on exit, so that any output
//               visible before the application starts reappears unchanged
//               after it exits.
//
//       cursor-colour colour
//               Set the colour of the cursor.
//
//       pane-colours[] colour
//               The default colour palette.  Each entry in the array
//               defines the colour uses when the colour with that index
//               is requested.  The index may be from zero to 255.
//
//       cursor-style style
//               Set the style of the cursor.  Available styles are:
//               default, blinking-block, block, blinking-underline,
//               underline, blinking-bar, bar.
//
//       remain-on-exit [on | off | failed]
//               A pane with this flag set is not destroyed when the
//               program running in it exits.  If set to failed, then only
//               when the program exit status is not zero.  The pane may
//               be reactivated with the respawn-pane command.
//
//       remain-on-exit-format string
//               Set the text shown at the bottom of exited panes when
//               remain-on-exit is enabled.
//
//       scroll-on-clear [on | off]
//               When the entire screen is cleared and this option is on,
//               scroll the contents of the screen into history before
//               clearing it.
//
//       synchronize-panes [on | off]
//               Duplicate input to all other panes in the same window
//               where this option is also on (only for panes that are not
//               in any mode).
//
//       window-active-style style
//               Set the pane style when it is the active pane.  For how
//               to specify style, see the “STYLES” section.
//
//       window-style style
//               Set the pane style.  For how to specify style, see the
//               “STYLES” section.
