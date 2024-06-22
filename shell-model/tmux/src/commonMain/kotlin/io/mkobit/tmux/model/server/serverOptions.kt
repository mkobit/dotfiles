package io.mkobit.tmux.model.server

import io.mkobit.tmux.model.SetOption
import io.mkobit.tmux.model.StringOption
import io.mkobit.tmux.model.StringOptionValue

private val serverModifier = setOf(SetOption.Modifier.Server)

//        backspace key
//               Set the key sent by for backspace.
//
//       buffer-limit number
//               Set the number of buffers; as new buffers are added to
//               the top of the stack, old ones are removed from the
//               bottom if necessary to maintain this maximum length.
//
//       command-alias[] name=value
//               This is an array of custom aliases for commands.  If an
//               unknown command matches name, it is replaced with value.
//               For example, after:
//
//                     set -s command-alias[100] zoom='resize-pane -Z'
//
//               Using:
//
//                     zoom -t:.1
//
//               Is equivalent to:
//
//                     resize-pane -Z -t:.1
//
//               Note that aliases are expanded when a command is parsed
//               rather than when it is executed, so binding an alias with
//               bind-key will bind the expanded form.
//
//       default-terminal terminal
//               Set the default terminal for new windows created in this
//               session - the default value of the TERM environment
//               variable.  For to work correctly, this must be set to
//               ‘screen’, ‘tmux’ or a derivative of them.
fun SetOption.Companion.defaultTerminal(terminal: String): SetOption =
  SetOption(serverModifier, StringOption("default-terminal"), StringOptionValue(terminal))
//
//       copy-command shell-command
//               Give the command to pipe to if the copy-pipe copy mode
//               command is used without arguments.
//
//       escape-time time
//               Set the time in milliseconds for which waits after an
//               escape is input to determine if it is part of a function
//               or meta key sequences.  The default is 500 milliseconds.
//
//       editor shell-command
//               Set the command used when runs an editor.
//
//       exit-empty [on | off]
//               If enabled (the default), the server will exit when there
//               are no active sessions.
//
//       exit-unattached [on | off]
//               If enabled, the server will exit when there are no
//               attached clients.
//
//       extended-keys [on | off | always]
//               When on or always, the escape sequence to enable extended
//               keys is sent to the terminal, if knows that it is
//               supported.  always recognises extended keys itself.  If
//               this option is on, will only forward extended keys to
//               applications when they request them; if always, will
//               always forward the keys.
//
//       focus-events [on | off]
//               When enabled, focus events are requested from the
//               terminal if supported and passed through to applications
//               running in .  Attached clients should be detached and
//               attached again after changing this option.
//
//       history-file path
//               If not empty, a file to which will write command prompt
//               history on exit and load it from on start.
//
//       message-limit number
//               Set the number of error or information messages to save
//               in the message log for each client.
//
//       prompt-history-limit number
//               Set the number of history items to save in the history
//               file for each type of command prompt.
//
//       set-clipboard [on | external | off]
//               Attempt to set the terminal clipboard content using the
//               xterm(1) escape sequence, if there is an Ms entry in the
//               terminfo(5) description (see the “TERMINFO EXTENSIONS”
//               section).
//
//               If set to on, will both accept the escape sequence to
//               create a buffer and attempt to set the terminal
//               clipboard.  If set to external, will attempt to set the
//               terminal clipboard but ignore attempts by applications to
//               set buffers.  If off, will neither accept the clipboard
//               escape sequence nor attempt to set the clipboard.
//
//               Note that this feature needs to be enabled in xterm(1) by
//               setting the resource:
//
//                     disallowedWindowOps: 20,21,SetXprop
//
//               Or changing this property from the xterm(1) interactive
//               menu when required.
//
//       terminal-features[] string
//               Set terminal features for terminal types read from
//               terminfo(5).  has a set of named terminal features.  Each
//               will apply appropriate changes to the terminfo(5) entry
//               in use.
//
//               can detect features for a few common terminals; this
//               option can be used to easily tell tmux about features
//               supported by terminals it cannot detect.  The
//               terminal-overrides option allows individual terminfo(5)
//               capabilities to be set instead, terminal-features is
//               intended for classes of functionality supported in a
//               standard way but not reported by terminfo(5).  Care must
//               be taken to configure this only with features the
//               terminal actually supports.
//
//               This is an array option where each entry is a colon-
//               separated string made up of a terminal type pattern
//               (matched using fnmatch(3)) followed by a list of terminal
//               features.  The available features are:
//
//               256     Supports 256 colours with the SGR escape
//                       sequences.
//
//               clipboard
//                       Allows setting the system clipboard.
//
//               ccolour
//                       Allows setting the cursor colour.
//
//               cstyle  Allows setting the cursor style.
//
//               extkeys
//                       Supports extended keys.
//
//               focus   Supports focus reporting.
//
//               hyperlinks
//                       Supports OSC 8 hyperlinks.
//
//               ignorefkeys
//                       Ignore function keys from terminfo(5) and use the
//                       internal set only.
//
//               margins
//                       Supports DECSLRM margins.
//
//               mouse   Supports xterm(1) mouse sequences.
//
//               osc7    Supports the OSC 7 working directory extension.
//
//               overline
//                       Supports the overline SGR attribute.
//
//               rectfill
//                       Supports the DECFRA rectangle fill escape
//                       sequence.
//
//               RGB     Supports RGB colour with the SGR escape
//                       sequences.
//
//               sixel   Supports SIXEL graphics.
//
//               strikethrough
//                       Supports the strikethrough SGR escape sequence.
//
//               sync    Supports synchronized updates.
//
//               title   Supports xterm(1) title setting.
//
//               usstyle
//                       Allows underscore style and colour to be set.
//
//       terminal-overrides[] string
//               Allow terminal descriptions read using terminfo(5) to be
//               overridden.  Each entry is a colon-separated string made
//               up of a terminal type pattern (matched using fnmatch(3))
//               and a set of name=value entries.
//
//               For example, to set the ‘clear’ terminfo(5) entry to
//               ‘\e[H\e[2J’ for all terminal types matching ‘rxvt*’:
//
//                     rxvt*:clear=\e[H\e[2J
//
//               The terminal entry value is passed through strunvis(3)
//               before interpretation.
//
//       user-keys[] key
//               Set list of user-defined key escape sequences.  Each item
//               is associated with a key named ‘User0’, ‘User1’, and so
//               on.
//
//               For example:
//
//                     set -s user-keys[0] "\e[5;30012~"
//                     bind User0 resize-pane -L 3
