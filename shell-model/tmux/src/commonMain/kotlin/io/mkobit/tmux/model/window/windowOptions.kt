package io.mkobit.tmux.model.window

//        aggressive-resize [on | off]
//               Aggressively resize the chosen window.  This means that
//               will resize the window to the size of the smallest or
//               largest session (see the window-size option) for which it
//               is the current window, rather than the session to which
//               it is attached.  The window may resize when the current
//               window is changed on another session; this option is good
//               for full-screen programs which support SIGWINCH and poor
//               for interactive programs such as shells.
//
//       automatic-rename [on | off]
//               Control automatic window renaming.  When this setting is
//               enabled, will rename the window automatically using the
//               format specified by automatic-rename-format.  This flag
//               is automatically disabled for an individual window when a
//               name is specified at creation with new-window or
//               new-session, or later with rename-window, or with a
//               terminal escape sequence.  It may be switched off
//               globally with:
//
//                     set-option -wg automatic-rename off
//
//       automatic-rename-format format
//               The format (see “FORMATS”) used when the automatic-rename
//               option is enabled.
//
//       clock-mode-colour colour
//               Set clock colour.
//
//       clock-mode-style [12 | 24]
//               Set clock hour format.
//
//       fill-character character
//               Set the character used to fill areas of the terminal
//               unused by a window.
//
//       main-pane-height height
//       main-pane-width width
//               Set the width or height of the main (left or top) pane in
//               the main-horizontal or main-vertical layouts.  If
//               suffixed by ‘%’, this is a percentage of the window size.
//
//       copy-mode-match-style style
//               Set the style of search matches in copy mode.  For how to
//               specify style, see the “STYLES” section.
//
//       copy-mode-mark-style style
//               Set the style of the line containing the mark in copy
//               mode.  For how to specify style, see the “STYLES”
//               section.
//
//       copy-mode-current-match-style style
//               Set the style of the current search match in copy mode.
//               For how to specify style, see the “STYLES” section.
//
//       mode-keys [vi | emacs]
//               Use vi or emacs-style key bindings in copy mode.  The
//               default is emacs, unless VISUAL or EDITOR contains ‘vi’.
//
//       mode-style style
//               Set window modes style.  For how to specify style, see
//               the “STYLES” section.
//
//       monitor-activity [on | off]
//               Monitor for activity in the window.  Windows with
//               activity are highlighted in the status line.
//
//       monitor-bell [on | off]
//               Monitor for a bell in the window.  Windows with a bell
//               are highlighted in the status line.
//
//       monitor-silence [interval]
//               Monitor for silence (no activity) in the window within
//               interval seconds.  Windows that have been silent for the
//               interval are highlighted in the status line.  An interval
//               of zero disables the monitoring.
//
//       other-pane-height height
//               Set the height of the other panes (not the main pane) in
//               the main-horizontal layout.  If this option is set to 0
//               (the default), it will have no effect.  If both the
//               main-pane-height and other-pane-height options are set,
//               the main pane will grow taller to make the other panes
//               the specified height, but will never shrink to do so.  If
//               suffixed by ‘%’, this is a percentage of the window size.
//
//       other-pane-width width
//               Like other-pane-height, but set the width of other panes
//               in the main-vertical layout.
//
//       pane-active-border-style style
//               Set the pane border style for the currently active pane.
//               For how to specify style, see the “STYLES” section.
//               Attributes are ignored.
//
//       pane-base-index index
//               Like base-index, but set the starting index for pane
//               numbers.
//
//       pane-border-format format
//               Set the text shown in pane border status lines.
//
//       pane-border-indicators [off | colour | arrows | both]
//               Indicate active pane by colouring only half of the border
//               in windows with exactly two panes, by displaying arrow
//               markers, by drawing both or neither.
//
//       pane-border-lines type
//               Set the type of characters used for drawing pane borders.
//               type may be one of:
//
//               single  single lines using ACS or UTF-8 characters
//
//               double  double lines using UTF-8 characters
//
//               heavy   heavy lines using UTF-8 characters
//
//               simple  simple ASCII characters
//
//               number  the pane number
//
//               ‘double’ and ‘heavy’ will fall back to standard ACS line
//               drawing when UTF-8 is not supported.
//
//       pane-border-status [off | top | bottom]
//               Turn pane border status lines off or set their position.
//
//       pane-border-style style
//               Set the pane border style for panes aside from the active
//               pane.  For how to specify style, see the “STYLES”
//               section.  Attributes are ignored.
//
//       popup-style style
//               Set the popup style.  See the “STYLES” section on how to
//               specify style.  Attributes are ignored.
//
//       popup-border-style style
//               Set the popup border style.  See the “STYLES” section on
//               how to specify style.  Attributes are ignored.
//
//       popup-border-lines type
//               Set the type of characters used for drawing popup
//               borders.  type may be one of:
//
//               single  single lines using ACS or UTF-8 characters
//                       (default)
//
//               rounded
//                       variation of single with rounded corners using
//                       UTF-8 characters
//
//               double  double lines using UTF-8 characters
//
//               heavy   heavy lines using UTF-8 characters
//
//               simple  simple ASCII characters
//
//               padded  simple ASCII space character
//
//               none    no border
//
//               ‘double’ and ‘heavy’ will fall back to standard ACS line
//               drawing when UTF-8 is not supported.
//
//       window-status-activity-style style
//               Set status line style for windows with an activity alert.
//               For how to specify style, see the “STYLES” section.
//
//       window-status-bell-style style
//               Set status line style for windows with a bell alert.  For
//               how to specify style, see the “STYLES” section.
//
//       window-status-current-format string
//               Like window-status-format, but is the format used when
//               the window is the current window.
//
//       window-status-current-style style
//               Set status line style for the currently active window.
//               For how to specify style, see the “STYLES” section.
//
//       window-status-format string
//               Set the format in which the window is displayed in the
//               status line window list.  See the “FORMATS” and “STYLES”
//               sections.
//
//       window-status-last-style style
//               Set status line style for the last active window.  For
//               how to specify style, see the “STYLES” section.
//
//       window-status-separator string
//               Sets the separator drawn between windows in the status
//               line.  The default is a single space character.
//
//       window-status-style style
//               Set status line style for a single window.  For how to
//               specify style, see the “STYLES” section.
//
//       window-size largest | smallest | manual | latest
//               Configure how determines the window size.  If set to
//               largest, the size of the largest attached session is
//               used; if smallest, the size of the smallest.  If manual,
//               the size of a new window is set from the default-size
//               option and windows are resized automatically.  With
//               latest, uses the size of the client that had the most
//               recent activity.  See also the resize-window command and
//               the aggressive-resize option.
//
//       wrap-search [on | off]
//               If this option is set, searches will wrap around the end
//               of the pane contents.  The default is on.
