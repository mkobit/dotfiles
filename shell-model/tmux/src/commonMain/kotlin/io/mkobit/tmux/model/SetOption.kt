package io.mkobit.tmux.model

import io.mkobit.tmux.model.SetOption.Modifier

/**
 * set-option [-aFgopqsuUw] [-t target-pane] option value
 * (alias: set)
 * Set a pane option with -p, a window option with -w, a
 * server option with -s, otherwise a session option.  If
 * the option is not a user option, -w or -s may be
 * unnecessary - will infer the type from the option name,
 * assuming -w for pane options.  If -g is given, the global
 * session or window option is set.
 *
 * -F expands formats in the option value.  The -u flag
 * unsets an option, so a session inherits the option from
 * the global options (or with -g, restores a global option
 * to the default).  -U unsets an option (like -u) but if
 * the option is a pane option also unsets the option on any
 * panes in the window.  value depends on the option and may
 * be a number, a string, or a flag (on, off, or omitted to
 * toggle).
 *
 * The -o flag prevents setting an option that is already
 * set and the -q flag suppresses errors about unknown or
 * ambiguous options.
 *
 * With -a, and if the option expects a string or a style,
 * value is appended to the existing setting.  For example:
 *
 * set -g status-left "foo"
 * set -ag status-left "bar"
 *
 * Will result in ‘foobar’.  And:
 *
 * set -g status-style "bg=red"
 * set -ag status-style "fg=blue"
 *
 * Will result in a red background and blue foreground.
 * Without -a, the result would be the default background
 * and a blue foreground.
 *
 * See [man page](https://man7.org/linux/man-pages/man1/tmux.1.html#OPTIONS) for complete
 * documentation.
 */
data class SetOption(val modifiers: Set<Modifier>, val option: Option, val value: OptionValue) : Command {
  companion object {
  }

  sealed interface Modifier {
    data object Global : Modifier
    data object Server : Modifier
    data object Window : Modifier
    data object Pane : Modifier
    data object SetIfUnset : Modifier
    data object ExpandFormat : Modifier
    data object SuppressError : Modifier
    data object Append : Modifier
  }
}

fun SetOption.Modifier.toModValue(): String = when(this) {
  SetOption.Modifier.Append -> "-a"
  SetOption.Modifier.ExpandFormat -> "-F"
  SetOption.Modifier.Global -> "-g"
  SetOption.Modifier.Pane -> "-p"
  SetOption.Modifier.Server -> "-s"
  SetOption.Modifier.SetIfUnset -> "-o"
  SetOption.Modifier.SuppressError -> "-q"
  SetOption.Modifier.Window -> "-w"
}

fun SetOption.withGlobal(): SetOption = SetOption(
  modifiers + Modifier.Global,
  option,
  value
)

fun SetOption.toGlobal(): SetOption = SetOption(
  setOf(Modifier.Global),
  option,
  value
)
