# Environment files

Docker environment files are experimental; [SKILL.md](../SKILL.md) records the last-tested SBX version.

Read Docker’s [environment-file reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/) for file lookup and merge semantics.

When the installed SBX version differs from that tested baseline, or a release changes environment-file, kit, or agent behavior, inspect the installed command help and the applicable [Docker kit customization reference](https://docs.docker.com/ai/sandboxes/customize/kits/) and release documentation before updating this workflow.
Then revalidate the affected schema, merge, kit, or native agent behavior using the supported validation and planning commands (currently `sbx kit validate` and `sbx env plan`) and a disposable clone-mode sandbox within the existing authorization.
Verify only the affected behavior, including the selected agent, plugin activation, injected tools, skill discovery, or project PATH precedence as applicable.
Update the affected templates, tests, references, and last-tested version only after that evidence is available.

SBX directory lookup resolves only `sbxenv.yaml`.
Pass a hidden `.sbxenv.yaml` explicitly when retaining that legacy filename.

Tracked project files use clone mode so the agent works in a private in-VM clone and cannot change the host checkout.

Keep direct mount disabled for autonomous work.

Do not commit `secrets`, `bindings`, `registries`, local-command MCP configuration, or writable `additionalWorkspaces`.

These fields can execute host commands, change host-global credentials, or expose additional host files.

Keep host-specific settings in ignored `.sbx/local.sbxenv.yaml` and merge it only when the session authorization covers that host-side action.

Use the project file first and the selected personal overlay second for every `sbx env` command; see [repository setup](repository-setup.md) for the agent-specific overlay path.
Passing any explicit path skips the default `~/.sbxenv.yaml` user file.
Nested mappings merge by key, lists concatenate, and later scalar values replace earlier values.

Run `sbx env rm` and recreate after changing kits, workspace mounts, ports, credentials, or sandbox options because `sbx env run` does not reprovision those fields on an existing environment.

Resolve toolchain or package updates in-place inside an existing sandbox using `sbx exec <name> -- <command>`, or tear down the environment with `sbx env rm` for a clean rebuild.

Read Docker’s [kit customization reference](https://docs.docker.com/ai/sandboxes/configuration/customize/kits/) before adding or changing a kit.
