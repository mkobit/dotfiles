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

On the managed OpenShell 0.1.9 Gateway, a launch with the local image tag booted the stock Ubuntu image.
A launch with an exported root filesystem was rejected because the Gateway disables caller driver configuration.
Identify how the Gateway can select an approved shared image, then confirm that a fresh guest can find the installed tools and configuration in an unrelated checkout.
Then test one noninteractive prompt with each of agy, Codex, and Claude Code to establish which credential flows the dispatcher can use.
Use those results to decide what project configuration is necessary.
