---
name: openshell-sandboxes
description: >-
  Use when inspecting, launching, or debugging NVIDIA OpenShell sandboxes or configuring sandbox policies with the `openshell` CLI.
  Keep command approvals in central policy; never forward personal host GPG/SSH keys or raw tokens into a sandbox.
---

# OpenShell sandboxes

Use the [OpenShell runbook](https://github.com/mkobit/dotfiles/blob/main/docs/openshell-bootstrap.md) for Gateway setup, guest work, signing, and GitHub push.
The central command policy controls host command approvals.

Run `openshell` and `openshell-doctor` on the host.
Run repository tools directly inside the guest.
Use an isolated guest clone in a writable directory approved by its policy.
Keep host worktrees, private keys, agent sockets, and raw tokens outside the guest.

Use the runbook's host signer for guest commits.
Attach the GitHub push provider only when the task authorizes a push.
