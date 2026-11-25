# Project configuration

## Tools and lockfiles

Declare shared tool versions in `[tools]`.
Use the repository's existing backend when it supplies the tool on all required platforms.
Use an explicit backend when a tool name is ambiguous or the source matters.
If the repository tracks `mise.lock`, review changes to it with changes to tool requests.
Use `mise lock` to resolve requests without installing tools, and `mise install --locked` when CI must use the recorded resolution.
Keep application lockfiles because `mise.lock` covers tools.
See [development tools](https://mise.jdx.dev/dev-tools/) and [mise lockfiles](https://mise.jdx.dev/dev-tools/mise-lock.html).

## Environment and settings

Use `[env]` for exported variables and `[vars]` for values used in mise templates.
Use `[env]` directives `_.file` and `_.path` to load dotenv files and add paths.
Keep secrets in the project's secret store or an ignored local file.
Redaction limits output exposure and does not make a secret safe to commit.
Use `[settings]` for mise behavior that the project needs.
See [environment variables](https://mise.jdx.dev/environments/), [settings](https://mise.jdx.dev/configuration/settings.html), and [profiles and local overrides](layout.md).

## Hooks and watchers

Use a task for work that someone runs on demand.
Use `[hooks]` for lifecycle events such as directory entry or tool installation.
Directory hooks and `[[watch_files]]` require shell activation.
Use `mise watch <task>` for a continuous watch session because `[[watch_files]]` checks for changes at the shell prompt.
See [hooks](https://mise.jdx.dev/hooks.html) for supported events and execution order.
