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
Keep shared chezmoi components reusable as they change so host and guest builds can select the components they need.

For a typical project, use its existing mise configuration to install project tools.
For projects that need system packages, use a project image built with the shared guest environment.
An Obsidian test image can add Xvfb, the required system libraries, and a pinned Obsidian build.
Keep the test command in the project so the same command can run in CI and in OpenShell.

Reuse the shared image when its inputs are unchanged.
When a task changes a chezmoi input or image build file, build a trial image from the task revision and test it in a fresh guest.
Use that image only for the task until the change has passed review.

The dispatcher should select the guest image and supply one effective OpenShell policy for the task.
Gateway providers supply credentials at launch.
The host signs commits with its existing key, and GitHub push remains a separate authorization.
Keep GitHub access read-only by default and give the guest writable checkout, cache, and agent state paths.
For on-demand inspection, prefer Cursor and test `openshell sandbox create --editor cursor` with a retained guest.

## Verified behavior

The managed OpenShell 0.1.9 Gateway loaded the shared image from a local image tag.
The launch output showed the stock Ubuntu bootstrap image, and the Gateway journal identified the separate shared image.
An explicit guest `PATH` that includes `/sandbox/.local/bin` let the guest run `agy --version`, `codex --version`, and `claude --version`.
The same checks passed from a fresh `chezmoi-skills` checkout with a read-only Git network policy and no providers.
The guest had the shared Git configuration.
Codex reported that it could not create aliases under `/sandbox/.codex/tmp` with that policy.
A separate `chezmoi-skills` guest installed the tools with mise and installed dependencies from the frozen Bun lockfile.
Its 111 contract checks and 99 unit tests passed.

Codex returned a response with the existing ChatGPT login through a temporary Gateway provider.
agy used a placeholder in its usual OAuth file and reached the Google model endpoint with the existing Google login.
Google returned the expected weekly quota error.
Both probes supplied current access tokens to the Gateway and put placeholders in the guests.
Automatic renewal and unattended signed task delivery still need tests.

## Next tasks

1. Add a host-side launch command for one `chezmoi-skills` task.
   Use the existing Codex login, start a fresh guest, run the repo checks, sign one commit with the existing host signer, return the verified commit, and delete the guest.
   Use read-only GitHub access and keep SBX available.
2. Add the agy launch path with the same guest lifecycle and a placeholder OAuth file.
   Keep credential renewal outside the guest.
   Verify access after quota reset and test how a subsequent launch obtains a fresh token.
   Use the [reference Antigravity policy](https://github.com/fredrikp999/openshell-configs/blob/f97c4090dff8dff176c0eea4035620a881f58b5e/policies/antigravity.yaml) to group rules by endpoint and explain their purpose.
   Use the guest's actual binary path and the requests observed in our probes to select rules.
3. Try the launcher on an Obsidian plugin repo before choosing a project config format.
   Keep shared images, provider bindings, and signing in the launcher.
   Reuse each repo's mise and test commands, and record which additional inputs the Obsidian image needs.
   Test rebuilding the shared setup from a task revision and opening a retained guest in Cursor.
