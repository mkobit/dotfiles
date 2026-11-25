# OpenShell setup

See the [OpenShell runbook](../openshell-bootstrap.md) for the managed Gateway, sandbox setup, and host-backed guest signing.

## Shared guest environment

Reuse the chezmoi-managed plugins, skills, terminal setup, and CLI tools across projects such as chezmoi-skills, storagemaxxing, and the Obsidian plugin repositories.
The dispatcher should supply this environment when it starts a guest.
Each project should need to declare only its own requirements, such as build tools, setup commands, or additional network access.
The same project should be usable from a developer checkout with its normal tools.

Start with the existing [chezmoi-built guest image](../../docker/openshell/Dockerfile) as the place to assemble the shared setup.
Keep the build in this repository for the first trial.
Revisit separate repositories if the shared environment needs its own release or ownership.

The dispatcher should select the guest image and supply one effective OpenShell policy for the task.
Gateway providers supply credentials at launch.
The host signs commits with its existing key, and GitHub push remains a separate authorization.

## Next check

The managed OpenShell 0.1.9 Gateway loaded the shared image from a local image tag.
The launch output showed the stock Ubuntu bootstrap image, and the Gateway journal identified the separate shared image.
An explicit guest `PATH` that includes `/sandbox/.local/bin` let the guest run `agy --version`, `codex --version`, and `claude --version`.
The same checks passed from a fresh `chezmoi-skills` checkout with a read-only Git network policy and no providers.
The guest had the shared Git configuration.
Codex reported that it could not create aliases under `/sandbox/.codex/tmp` with that policy.
Give each agent writable runtime state when testing unattended prompts.
Then test one noninteractive prompt with each of agy, Codex, and Claude Code to establish which credential flows the dispatcher can use.
Use those results to decide what project configuration is necessary.
