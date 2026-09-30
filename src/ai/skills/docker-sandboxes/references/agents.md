# Agents

Choose the harness the repository tracks and validates.

Codex, Claude, and AGY environment templates all include the repository `./kit` and direct-mounted workspaces.

Use AGY only through a repository `.sbx/sbxenv.agy.yaml` environment.

Before creating an AGY environment, inspect `sbx settings get kit.allowedSources`.

The AGY contrib kit needs the narrow `github.com/docker/` source prefix.

Require confirmation before changing that setting when the session authorization does not already cover it.

The setting replaces the complete allowlist, so preserve existing approved entries while adding the required prefix.

If SBX cannot resolve `agent: antigravity`, stop and report the preflight output rather than falling back to a host launcher.

The first AGY run can require a user-completed Google OAuth flow through Docker’s credential proxy.

Keep commits, signing, and pushes on the host.
