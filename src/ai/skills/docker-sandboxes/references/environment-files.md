# Environment files

Docker environment files are experimental and require SBX `0.39.0` or later.

Tracked project files use clone mode so the agent works in a private in-VM clone and cannot change the host checkout.

Keep direct mount disabled for autonomous work.

Do not commit `secrets`, `bindings`, `registries`, local-command MCP configuration, or writable `additionalWorkspaces`.

These fields can execute host commands, change host-global credentials, or expose additional host files.

Keep host-specific settings in ignored `.sbx/local.sbxenv.yaml` and merge it only after confirmation.

Run `sbx env rm` and recreate after changing kits, workspace mounts, ports, credentials, or sandbox options because `sbx env run` does not reprovision those fields on an existing environment.

Read Docker’s [environment-file reference](https://docs.docker.com/ai/sandboxes/configuration/environment-files/) before using a field not present in the templates.
