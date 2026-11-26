# OpenShell repository files

Use the runbook to build an image, start a sandbox, and deliver a reviewed commit from the host.
Docker and OpenShell read the files here from the checkout.
Chezmoi applies the separate source tree under `src/chezmoi/`.
Use the installed OpenShell skills for CLI, policy, and troubleshooting guidance. [Runbook](../../docs/openshell-bootstrap.md) · [Local skill](../chezmoi/dot_local/share/agent-plugins/marketplace/exact_plugins/exact_mkobit-dotfiles/exact_skills/exact_openshell-sandboxes/SKILL.md)

## Files in this repository

- `images/shared/` contains the Dockerfile and guest chezmoi configuration for the shared image. [Dockerfile](images/shared/Dockerfile) · [Guest configuration](images/shared/sandbox-chezmoi.toml)
- `policies/` groups policies by repository. The normal dotfiles launch uses the read-only policy.
  Use the push policy only for an explicitly approved guest push.
  The chezmoi-skills pilot uses its own policy. [Read-only policy](policies/dotfiles/github-read-only.yaml) · [Read-only launch](../../docs/openshell-bootstrap.md#4-start-normal-work-without-github-credentials) · [Push policy](policies/dotfiles/github-push.yaml) · [Pilot policy](policies/chezmoi-skills/task.yaml) · [Sandbox policies](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/policies/overview)
- `provider-profiles/` contains the Codex endpoint and credential slot definitions. [Codex provider profile](provider-profiles/codex-dispatch.json) · [Provider profiles](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/providers/profiles)
- `pilots/chezmoi-skills/` contains the pilot launcher and guest setup script. [Pilot launcher](pilots/chezmoi-skills/run.py) · [Pilot setup](pilots/chezmoi-skills/setup.sh)
- `tools/` contains the host signer, which checks the approved commit before it signs it with a host key. [Signer](tools/sign-commit.py) · [Review and signing](../../docs/openshell-bootstrap.md#6-review-and-sign-a-guest-commit)

Keep project-specific image recipes, setup commands, and network requirements in the project that uses them.
Chezmoi installs the WSL MicroVM Gateway configuration and systemd unit from its source tree.
The host approval catalog controls which OpenShell CLI commands coding agents can run without approval. [Gateway configuration](../chezmoi/dot_config/private_openshell/microvm-gateway.toml.tmpl) · [Systemd unit](../chezmoi/dot_config/systemd/user/openshell-microvm.service.tmpl) · [Host command policy](../chezmoi/.chezmoidata/ai/command_policy/openshell.toml)

## Gateway resources

Track reusable build files, policies, provider profiles, and launch instructions in Git.
Create providers, sandbox templates, and services on the Gateway.
Keep live Gateway state, tokens, and rotating credential values outside Git.

- **Sandbox template.** Store the image, resource limits, and non-secret environment settings on a named Gateway template when tasks reuse them. Select the policy and attach providers when you create each sandbox. [Runbook example](../../docs/openshell-bootstrap.md#optional-templates-and-services) · [Sandbox templates](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/templates)
- **Service.** Expose a loopback port on a running sandbox when its workload needs a Gateway URL. [Runbook example](../../docs/openshell-bootstrap.md#optional-templates-and-services) · [Sandbox services](https://docs.nvidia.com/openshell/v0.1.9/how-it-works/sandboxes/overview#expose-long-running-services)
- **Provider.** Use the provider profile to create a provider on the Gateway with its runtime credentials. [Codex provider profile](provider-profiles/codex-dispatch.json)
