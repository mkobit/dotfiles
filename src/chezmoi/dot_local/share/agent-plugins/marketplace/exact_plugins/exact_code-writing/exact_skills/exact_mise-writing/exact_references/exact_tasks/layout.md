# Task layout

Keep a few short tasks together while the core configuration is easy to scan.
When tasks form groups such as `check`, `db`, or `docker`, move each group of short tasks to `.mise/conf.d/<group>.toml`.
The fragment name does not set the task name, so put the group in the TOML key.
For example, in `.mise/conf.d/check.toml`:

```toml
[tasks."check:format"]
description = "Check formatting"
run = "cargo fmt --check"
```

Use a file task when the command body grows past about ten lines or needs branches, loops, or cleanup.
Use a shebang to select the interpreter and commit the executable bit on POSIX systems.
Add `#MISE` metadata as needed for descriptions, dependencies, aliases, or the working directory.
For example, in `.mise/tasks/check/api.sh`:

```bash
#!/usr/bin/env bash
#MISE description="Check the API"
set -euo pipefail

if [[ -f api/Cargo.toml ]]; then
  cargo test --manifest-path api/Cargo.toml "$@"
else
  printf '%s\n' 'Missing api/Cargo.toml' >&2
  exit 1
fi
```

File task paths below `.mise/tasks/` use colons in place of directory separators.
For example, `check/api.sh` is normally `check:api`, `check/api/unit.sh` is `check:api:unit`, and `check/_default` is `check`.
Avoid names that differ only by an extension.

Use default discovery for this layout.
`task_config.includes` replaces the default task directories for its config root.
A bundle under `.mise/conf.d/<bundle>/` has a separate task root.

Remove the old command when moving a task to a new source.
A same-name TOML task with a command can override a file task.
Use `mise tasks info <task>` to check which definition mise selected.

See [TOML tasks](https://mise.jdx.dev/tasks/toml-tasks.html), [file tasks](https://mise.jdx.dev/tasks/file-tasks.html), and [task discovery and precedence](https://mise.jdx.dev/tasks/task-discovery.html).
