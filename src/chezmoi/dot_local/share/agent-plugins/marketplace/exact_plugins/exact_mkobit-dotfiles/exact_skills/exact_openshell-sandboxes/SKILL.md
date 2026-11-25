---
name: openshell-sandboxes
description: >-
  Use when inspecting, launching, or debugging NVIDIA OpenShell sandboxes or configuring sandbox policies with the `openshell` CLI.
---

# OpenShell sandboxes

Follow the [OpenShell runbook](https://github.com/mkobit/dotfiles/blob/main/docs/openshell-bootstrap.md) for setup, task dispatch, and host delivery.
The central command policy controls host command approvals.

Run `openshell` and `openshell-doctor` on the host.
Run repository tools directly inside the guest.
Use a separate guest clone in a writable directory.
Give the guest read-only access to Git remotes.
Use anonymous Git access for public repositories.
Keep host worktrees, private keys, agent sockets, and raw tokens outside the guest.

Return the guest result for host review.
The host controls signing, pushes, and pull requests.
