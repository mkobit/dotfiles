# Jules CLI

The Jules CLI (`~/.local/bin/tools/jules` or `jules`) is a command-line tool for interacting with the Jules API to create and manage AI coding sessions.

## Usage patterns

The CLI currently supports several subcommands for managing sessions:

*   `jules session create` — Create a new session with a prompt.
*   `jules session list` — List recent sessions.
*   `jules session show` — Show session details.
*   `jules session interact` — TUI-based interactive mode (requires `fzf`).

These commands are built for both manual and programmatic use, with a `--json` flag available for most read commands.

## Feature gap: Programmatic follow-up messages

Currently, when using the `jules` CLI programmatically (e.g., from another AI agent or script), there is no way to send a follow-up message to an existing session.
The only option for sending a follow-up is `jules session interact`, which launches a TUI and requires manual interaction.

This creates a workflow gap: after creating a session, reviewing its output, and finding issues, the only programmatic option is to create a brand new session on the same branch.
This approach is wasteful and loses conversation context.

### Proposed solution

Add a new command to support sending messages programmatically:

```bash
jules session message SESSION_ID --message "Follow-up instructions here"
```

Or reading from stdin/file:

```bash
jules session message SESSION_ID --message-file /path/to/message.txt
```

### Current workaround

Until this feature is implemented, the current workaround is to create a new session on the same branch:

```bash
jules session create --prompt "Follow-up: fix the failing tests from previous attempt" --source github/owner/repo --branch <same-branch-as-previous-session>
```

### Investigation required

The Jules API reference should be checked to determine if the underlying API supports sending messages to existing sessions directly:
https://developers.google.com/jules/api/reference/rest

*   If the API supports it, this is merely a CLI wrapper gap that needs to be implemented.
*   If the API does not support it, this feature request should be escalated to the Jules API team.
