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

The [host launcher](../openshell-bootstrap.md#5-run-the-chezmoi-skills-pilot) passed in two fresh guests with the existing image and ChatGPT login.
The final run passed 111 contract checks and 99 unit tests and returned signed commit `dd2fd1266478590342f4fb83d04e7bcbf80bd75d` in a Git bundle.
The host signer checked the authorized parent and tree before signing, and the launcher verified the signature and commit after transfer.
The OpenShell VM supplied isolation because Codex could not start its inner bubblewrap sandbox.
The guest used anonymous, read-only GitHub access.
Both runs removed their guest, provider, and profile.

The shared image rebuilt from launcher commit `094fb450` under a separate local tag.
A fresh guest started from that image and reported the installed agy, Codex, Claude, and mise versions.

The agy trial used a placeholder in a file-backed login and a temporary Gateway provider with the host access token.
The policy allowed only the agy binary to call the Google model endpoint.
After the host token expired, `agy models` renewed it and advanced its expiry.
A fresh guest used the renewed token through a new provider, received HTTP 429 `RESOURCE_EXHAUSTED`, and removed its temporary resources.
The OAuth endpoint and refresh token stayed outside the guest.

The [Routine Flow](https://github.com/mkobit/routine-flow/tree/54bc045b5b997d637bf9521c207eb692a6e0ee46) image added Xvfb, xauth, fonts, and Electron system libraries.
The guest used the project's pinned mise tools, Bun lockfile, and Obsidian 1.15.1.
The installer needed more space than the guest `/tmp` provided, so the checkout and caches moved to `/var/tmp`.
Xvfb needed a trial-only change for an identity reset that the VM rejects, and Chromium needed guest-local write access to `/dev/shm`.
The native Playwright run reached Obsidian and stopped after the first test because the guest denied a process-group signal during teardown.
In a disposable checkout, a graceful CDP close made that test pass and left no Obsidian or Chromium processes.
The trial did not verify cleanup after a forced shutdown or the full suite with the teardown change.

On WSL, `openshell sandbox create --editor cursor` started the Cursor wrapper and produced no Remote SSH connection in the Cursor logs.
The wrapper passed a second `--remote` option.
A temporary Windows Cursor profile reached a fresh guest through Windows OpenSSH and a WSL OpenShell proxy command.
Cursor's SSH server upload failed, including on a writable guest disk with free space.
With `remote.SSH.localServerDownload` set to `off`, the guest downloaded the exact Cursor server archive from `downloads.cursor.com` through a `GET` rule for `/usr/bin/curl`.
Cursor installed the server in a writable guest path, started forwarding, and completed a remote command.
The trial removed its guests and temporary SSH settings.

## Next tasks

1. Verify an agy model response after the quota resets, then record the launch path with the same guest lifecycle and a placeholder OAuth file.
   Keep credential renewal outside the guest.
   Use the [reference Antigravity policy](https://github.com/fredrikp999/openshell-configs/blob/f97c4090dff8dff176c0eea4035620a881f58b5e/policies/antigravity.yaml) to group rules by endpoint and explain their purpose.
   Use the guest's actual binary path and the requests observed in our probes to select rules.
2. Verify Routine Flow teardown on both success and failure, then run its full suite in a fresh guest.
   Keep its normal mise and test commands usable from developer checkouts and CI.
   Use the second repo's results before choosing a shared project config format.
