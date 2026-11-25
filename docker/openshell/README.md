# OpenShell repository files

Use the runbook to build an image, start a sandbox, and deliver a reviewed commit from the host.
Use the installed OpenShell skills for CLI, policy, and troubleshooting guidance. [Runbook](../../docs/openshell-bootstrap.md) · [Local skill](../../src/chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_openshell-sandboxes/SKILL.md)

## Files in this repository

- **Image.** The Dockerfile builds the shared guest environment from the guest chezmoi configuration. [Dockerfile](Dockerfile) · [Guest configuration](sandbox-chezmoi.toml)
- **Policies.** The normal dotfiles launch removes the push rule from `github-push.yaml` to permit read-only Git access. The chezmoi-skills pilot uses its own policy. [Read-only launch](../../docs/openshell-bootstrap.md#4-start-normal-work-without-github-credentials) · [Push policy](github-push.yaml) · [Pilot policy](chezmoi-skills-policy.yaml) · [Sandbox policies](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/policies/overview)
- **Host command approvals.** The host approval catalog controls which OpenShell CLI commands coding agents can run on the host without approval. [Host command policy](../../src/chezmoi/.chezmoidata/ai/command_policy/openshell.toml)
- **Sandbox.** The runbook uses native `openshell sandbox` commands. The chezmoi-skills pilot also has a launcher and a setup script. [Pilot launcher](run-chezmoi-skills.py) · [Pilot setup](chezmoi-skills-setup.sh)
- **Signer.** The host signer checks the approved commit before it signs it with a host key. [Signer](sign-commit.py) · [Review and signing](../../docs/openshell-bootstrap.md#6-review-and-sign-a-guest-commit)
- **Gateway.** Chezmoi installs the WSL MicroVM Gateway configuration and its systemd unit. [Gateway configuration](../../src/chezmoi/dot_config/openshell/microvm-gateway.toml.tmpl) · [Systemd unit](../../src/chezmoi/dot_config/systemd/user/openshell-microvm.service.tmpl)

## Objects to add as needed

This repository has no standalone template, service, or provider profile definitions.
The pilot launcher builds its provider profile when it runs.

- **Template.** Save a reusable image, resource limits, and non-secret environment settings. Select the policy and providers when you start each sandbox. [Sandbox templates](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/templates)
- **Service.** Expose a port when you need access to a process inside a sandbox. Keep the port and access settings with the project that uses them. [Sandbox services](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/overview#expose-long-running-services)
- **Provider profile and provider.** Keep reusable profile definitions with the workload. Create each provider on the Gateway with its runtime credential. Keep credentials and live sandbox state outside Git. [Provider profiles](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/providers/profiles)
