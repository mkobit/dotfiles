---
name: mise-writing
description: Write, change, review, or troubleshoot mise project configuration and tasks. Use for mise.toml, the .mise directory, task layout and execution, tool versions and lockfiles, environment overlays, hooks, and monorepo tasks.
---

# Mise writing

Check the repository's mise version, configuration files, and task names before making changes.
Use the existing layout for small edits.
For new layouts and requested migrations, prefer `.mise/config.toml` for shared settings, `.mise/conf.d/<group>.toml` for groups of short tasks, and `.mise/tasks/<group>/<task>` for tasks that need scripts.
Split tasks when distinct groups emerge or task definitions make the core configuration hard to scan.
Keep existing task names and arguments during a move unless the user requests a change.

Read only the references for the work:

- [Task layout](references/tasks/layout.md) for TOML tasks, file tasks, names, and discovery.
- [Task execution](references/tasks/execution.md) for arguments, dependencies, caching, and monorepos.
- [Configuration layout](references/config/layout.md) for fragments, precedence, environment overlays, and migration.
- [Project configuration](references/config/project.md) for tools, environment variables, settings, hooks, and watchers.

After a layout change, run `mise config ls` and `mise tasks` from the project root with the supported mise version.
Check for the expected files and task names.
For tool or environment changes, use `mise ls`, `mise env`, or `mise doctor` as applicable.
