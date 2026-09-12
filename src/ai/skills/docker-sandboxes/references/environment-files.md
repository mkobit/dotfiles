# Environment files

Docker environment files are experimental and require SBX `0.42.1` or later.

Read Docker’s [environment-file reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/) for file lookup and merge semantics.

SBX directory lookup resolves only `sbxenv.yaml`.
Pass a hidden `.sbxenv.yaml` explicitly when retaining that legacy filename.

Tracked project files use clone mode so the agent works in a private in-VM clone and cannot change the host checkout.

Keep direct mount disabled for autonomous work.

Do not commit `secrets`, `bindings`, `registries`, local-command MCP configuration, or writable `additionalWorkspaces`.

These fields can execute host commands, change host-global credentials, or expose additional host files.

Keep host-specific settings in ignored `.sbx/local.sbxenv.yaml` and merge it only when the session authorization covers that host-side action.

Use the project file first and `~/.local/share/sbx/personal/personal.sbxenv.yaml` second for every `sbx env` command.
Passing any explicit path skips the default `~/.sbxenv.yaml` user file.
Nested mappings merge by key, lists concatenate, and later scalar values replace earlier values.

Run `sbx env rm` and recreate after changing kits, workspace mounts, ports, credentials, or sandbox options because `sbx env run` does not reprovision those fields on an existing environment.

Resolve toolchain or package updates in-place inside an existing sandbox using `sbx exec <name> -- <command>`, or tear down the environment with `sbx env rm` for a clean rebuild.

Read Docker’s [kit customization reference](https://docs.docker.com/ai/sandboxes/configuration/customize/kits/) before adding or changing a kit.
