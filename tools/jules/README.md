# Jules CLI

The Jules CLI (`~/.local/bin/tools/jules` or `jules`) is a command-line tool for interacting with the Jules API to create and manage AI coding sessions.

## Usage patterns

The CLI currently supports several subcommands for managing sessions:

*   `jules session create` — Create a new session with a prompt.
*   `jules session list` — List recent sessions.
*   `jules session show` — Show session details.
*   `jules session message` — Send a follow-up message to an existing session.
*   `jules session interact` — TUI-based interactive mode (requires `fzf`).

These commands are built for both manual and programmatic use, with a `--json` flag available for most read commands.

### Sending messages programmatically

You can send a follow-up message to an existing session programmatically without entering the interactive TUI:

```bash
jules session message SESSION_ID --message "Follow-up instructions here"
```

Or reading from `stdin` via pipe or redirection:

```bash
echo "Please refactor this" | jules session message SESSION_ID
jules session message SESSION_ID < /path/to/message.txt
```

You can also explicitly pass `-m -` to read from `stdin`. If no message is provided and stdin is piped, it will automatically read from `stdin`.

### Investigation

For more information about what features the Jules API supports, refer to the [Jules API reference](https://developers.google.com/jules/api/reference/rest).
