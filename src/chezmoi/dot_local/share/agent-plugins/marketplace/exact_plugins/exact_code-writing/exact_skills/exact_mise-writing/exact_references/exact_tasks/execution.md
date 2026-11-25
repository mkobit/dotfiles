# Task execution

Use `mise run <task> --help` to check the public argument interface.
Use the same argument names, defaults, and exit behavior when moving a task between TOML and a file.
Use the `usage` field in a TOML task or `#USAGE` in a file task when the task needs named arguments, validation, or help.
See [task arguments](https://mise.jdx.dev/tasks/task-arguments.html) and [running tasks](https://mise.jdx.dev/tasks/running-tasks.html).

Use `depends` for work that must finish before the task starts.
Sibling dependencies can run in parallel.
Declare a dependency chain when order matters.
Use `depends_post` for cleanup after a task that starts, and `wait_for` for order between tasks that are already scheduled.
Check the graph with `mise tasks deps <task>`.
See [dependencies and execution order](https://mise.jdx.dev/tasks/architecture.html).

Use `sources` and `outputs` when a task produces local files and mise can safely skip work while they are current.
Include all inputs that affect the result.
Check the repository's mise version before adding a task cache, and check [cache keys and environment inputs](https://mise.jdx.dev/tasks/caching.html) for that version.
See [task properties](https://mise.jdx.dev/tasks/task-configuration.html) for working directories, ordering, and skip rules.

In an existing mise monorepo, put shared tasks at the root and project tasks in the associated project configuration.
Use explicit references such as `//services/api:check` for cross-project dependencies.
If the project needs monorepo discovery, check version support for `monorepo_root` and `config_roots`, then verify the task names from the root and a subproject.
See [monorepo tasks](https://mise.jdx.dev/tasks/monorepo.html).
