# Retire sandboxr

## Context

The August decision kept `sandboxr` on Bubblewrap.
That setup supported host signing-agent forwarding on Linux.
At the time, Docker Sandboxes (SBX) had no equivalent forwarding path, and the repository had yet to adopt it for this work.
See the [August decision record](https://github.com/mkobit/dotfiles/blob/94fead1df7000d1aeb46b97a86e7aa3e416855f2/docs/decisions/2026-08-12-sandboxr-sandbox-backend.md).

The repository now maintains an SBX environment that runs tasks in a microVM with a private Git clone.
The pilot design uses a dedicated GPG signing subkey and keeps the primary private key outside the guest.
That design addresses the signing requirement without host-agent forwarding.
The pilot record distinguishes guest checks from the pending proof of a complete run with the user's signing subkey.
See the [SBX environment guide](../../.sbx/README.md) and [pilot design](../designs/sbx-agy-pilot.md).

## Decision

Remove `sandboxr` and use SBX as the repository's maintained sandbox path for agent tasks.
Remove the Python package, tests, deployment entries, and settings specific to the old runner.
CI discovers the remaining packages and tests through the workspace and test directories.
See [PR #1140](https://github.com/mkobit/dotfiles/pull/1140).

## Alternative considered

Keeping the Bubblewrap runner would preserve a local option for Linux users who need host signing-agent forwarding.
It would also require continued maintenance of a second set of sandbox policies, tool integrations, and tests.
The repository already has an SBX environment and a documented signing design, so it can retire the second path while tracking pilot verification separately.

## Consequences

Workflows that call `sandboxr` must move to SBX or use a separately maintained runner.
This source change stops future managed installs of the package.
The base chezmoi init template selects uninstall for the old uv tool.
Run `chezmoi init` to refresh an existing base configuration, then run `chezmoi apply` to remove the tool.
Overlays that replace the init template must select uninstall in their own configuration.

Revisit the decision if a required workflow cannot use SBX and needs a maintained Linux runner with host signing-agent forwarding.
