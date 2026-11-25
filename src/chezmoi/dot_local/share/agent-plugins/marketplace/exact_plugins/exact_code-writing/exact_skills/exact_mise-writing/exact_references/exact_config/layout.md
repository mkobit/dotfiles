# Configuration layout

Start with `.mise/config.toml`.
Add the other paths only when the project needs them.

```text
project/
├── .mise/
│   ├── config.toml
│   ├── config.ci.toml
│   ├── conf.d/
│   │   └── check.toml
│   └── tasks/
│       └── check/
│           └── api.sh
└── mise.local.toml
```

Keep shared `[tools]`, `[env]`, `[vars]`, and `[settings]` in `.mise/config.toml` until a section needs its own file.
Use topic names for fragments, such as `env.toml` or `hooks.toml`.
Use hyphens in fragment names because mise can interpret dots as environment suffixes.
Use `.mise/conf.d/<bundle>/mise.toml` only when a bundle needs its own files and task scope.
Mise does not search recursively for arbitrary configuration files inside a bundle.

For these base files in one project directory, precedence increases from flat fragments in alphabetical order, to folder fragments in alphabetical order, to `.mise/config.toml`, to root `mise.toml`.
Select a shared profile such as `.mise/config.ci.toml` with `MISE_ENV=ci` or `mise -E ci`.
Use root `mise.local.toml` for ignored machine overrides.
When profiles, local files, or parent directories overlap, use `mise config ls` with the same profile and working directory as the real command to see what loads.
See [configuration discovery](https://mise.jdx.dev/configuration.html#which-files-count) and [environment precedence](https://mise.jdx.dev/configuration/environments.html#file-names-and-precedence).

Before a migration, check CI, automation, and editor integrations for explicit paths to `mise.toml`.
Remove the old root file after the move if no integration requires it.
Use an explicit file path when a command such as `mise use --path .mise/config.toml` must write to the core file.
Check relative paths, the selected lockfile, and task working directories after the move.
Check feature support in the oldest mise version the project supports.
Set top-level `min_version` to the required version when the project adopts a feature that needs it.
See the [configuration reference](https://mise.jdx.dev/configuration/reference.html).
