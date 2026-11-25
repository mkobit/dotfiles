# OpenShell rollout plan

## 1. Deliver changes from the host

Use a guest with read-only GitHub access for repository work.
Start from a reviewed commit in a private, writable guest checkout.
Give the guest its project tools and approved model access, with writable paths for the checkout, caches, and agent state.
Keep host worktrees, private signing keys, SSH agent sockets, and GitHub write credentials outside the guest.

Return the guest changes in a Git bundle.
The host checks that the bundle can be fetched, that the changes start from the requested base, and that the changed files are within the task scope.
The host reviews the diff and check results, signs the delivery commits, and pushes the authorized feature branch for review.
Use host delivery as the default before expanding the rollout to more agents and projects.

The chezmoi-skills pilot proved transfer of an empty signed commit from a read-only guest.
Its host signer checked the expected parent and tree before signing, and the launcher verified the signature and commit after transfer.
The pilot passed 111 contract checks and 99 unit tests and removed the temporary guest, provider, and profile.
The dotfiles trial delivered a real code change from a disposable guest through host review, signing, and a draft pull request.
[Host signer (#1171)](https://github.com/mkobit/dotfiles/pull/1171), [Codex pilot (#1177)](https://github.com/mkobit/dotfiles/pull/1177), [Host delivery trial (#1183)](https://github.com/mkobit/dotfiles/pull/1183)

For Beads work, claim one approved issue on the host and start a fresh guest with the repository and issue labels.
Keep the guest until the host verifies its result.
Record the pull request on the issue from the host.

See the [OpenShell runbook](../openshell-bootstrap.md) for host and guest setup.

## 2. Reuse the shared guest environment

Use the [chezmoi-built guest image](../../docker/openshell/Dockerfile) for the shared plugins, skills, terminal setup, and CLI tools.
Keep the image build in this repository until the shared environment needs its own release or ownership.
Keep the chezmoi components selectable for host and guest builds.
Reuse the image when its inputs are unchanged.
If a task changes a chezmoi input or image build file, build a trial image from the task revision and test it in a fresh guest.
Use the trial image only for that task until review is complete.

Select the guest image and base policy for each task.
Gateway providers supply credentials at launch.
Each project declares its tools, setup commands, and additional network access.
Use the project's mise configuration and locked dependencies where available.
Use a project image for system packages and other system dependencies.
Keep the project setup and test commands usable from developer checkouts, CI, and OpenShell.
Use the results from a second project before choosing a shared project configuration format.
[Shared environment (#1174)](https://github.com/mkobit/dotfiles/pull/1174), [Project checkout verification (#1175)](https://github.com/mkobit/dotfiles/pull/1175)

## 3. Complete the remaining trials

- **Antigravity CLI.** Verify a model response after the quota resets.
  Keep OAuth renewal on the host and use a placeholder login file in the guest.
  Limit network access to the requests needed by the guest binary.
  [Dispatch trials (#1176)](https://github.com/mkobit/dotfiles/pull/1176), [Quota and renewal results (#1177)](https://github.com/mkobit/dotfiles/pull/1177)
- **Routine Flow.** Verify Obsidian and Chromium teardown on success and failure, then run the full suite in a fresh guest.
  Keep Xvfb, the system libraries, and the pinned Obsidian build in the project image.
  [Routine Flow trial (#1177)](https://github.com/mkobit/dotfiles/pull/1177)
- **Cursor.** Verify on-demand inspection of a retained guest on WSL.
  The Windows Remote SSH trial worked when the guest downloaded the exact Cursor server archive.
  Verify the normal launch path before making it the default.
  [Cursor trial (#1177)](https://github.com/mkobit/dotfiles/pull/1177)
