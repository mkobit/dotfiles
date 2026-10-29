# CLI selection and automation

These notes cover Docker Sandboxes CLI v0.50.1 automation.
See the [v0.50.1 release notes](https://github.com/docker/sbx-releases/releases/tag/v0.50.1).

## Select a command

| Need | Command |
| --- | --- |
| Discover sandboxes | `sbx ls --format json` (`list` is an alias) |
| Inspect command usage | `sbx help <command>` or `sbx <command> --help` |
| Run a command with tracked configuration | `sbx env exec .sbx/sbxenv.yaml -- <command>` |
| Run in an existing named sandbox | `sbx exec <sandbox> <command>` |
| Inspect allocated ports | `sbx ports <sandbox> --format json` |
| Diagnose a failure | `sbx diagnose --format json` |
| Plan configuration changes | `sbx env plan .sbx/sbxenv.yaml` |

The installed CLI has no `sbx env list` or `sbx env ls`; use root `sbx ls`.
`exec` starts a stopped sandbox; `env exec` requires an existing environment and runs no host lifecycle commands.
Detached exec is unsupported even though help lists `-d`.
`sbx run --detach` starts the sandbox and prints its ID without opening an agent session.
`sbx env run --detach` creates or starts the configured sandbox without attaching.
Use `sbx exec` or `sbx env exec` to run the coding agent in that sandbox.
Keep creation and session lifecycle actions separate from command execution.

## Environment paths

Use explicit tracked paths and `--` before the guest command.
A path can be a directory containing `sbxenv.yaml` or a named environment file.
Multiple paths deep-merge in order; lists such as `ports` concatenate.
An explicit path skips the hidden home base layer.
Use the same `--name` override for each command that addresses an environment.
Specify `--name <name>` to run parallel sandboxes from one template without name conflicts.

## Machine output

Use `--format json` or `--format yaml` for machine reads instead of terminal tables.
`--format`, `--json`, and `-q` are mutually exclusive on commands that use the shared output flags.
`sbx ls --format json` returns a direct array with snake_case fields, not a `sandboxes` wrapper.
Use that array shape only for `sbx ls`; other commands have their own output schemas.
Keep result output from stdout, errors, warnings, and progress from stderr, and preserve each command's exit code.

## Prompts and flags

Confirmation requires terminal input, so piping an answer does not confirm an operation.
Use `--force` or `-f` only for an operation that is already authorized and only when that command supports the flag.
`sbx env plan` has no `--force` flag and applies no changes.
In v0.48.0, `sbx env create` and `sbx env run` use `--force` or `-f` instead of `--auto-approve` or `-y`.
`sbx run` and `sbx env run` use `--detach` or `-d` instead of `--detached`.
A command's `--force` flag does not grant platform escalation or expand task authority.
Lack of terminal input alone does not justify broader host command grants.

If a command starts sign-in or reports an expired session, use [Authentication](authentication.md).
Keep runtime errors distinct from platform restrictions when diagnosing a failed command.

## Environment and kit lifecycle

Running sandboxes reuse guest setup until the container starts or the daemon restarts.
Keep and reuse a matching environment for related checks instead of recreating it each time.
`sbx kit add` can recreate a container, and its startup commands run when the kit is added and on later starts.
Keep `sbx kit add` outside automatic grants.
Existing Codex sandboxes need a planned, explicitly authorized recreation to receive the built-in Codex MCP gateway fix.
Never remove or recreate a sandbox only because a check fails.

Managed Codex and Claude Desktop SSH targets on macOS and Windows use separate sandboxes with no host workspace mounted.
